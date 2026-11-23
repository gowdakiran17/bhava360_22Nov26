import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { randomBytes } from 'node:crypto';
import { mkdtemp } from 'node:fs/promises';
import { createServer, type AddressInfo } from 'node:net';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { Pool } from 'pg';
import { TOTP } from 'otpauth';
import EmbeddedPostgres from 'embedded-postgres';
import { it, expect, beforeAll, afterAll } from 'vitest';
import { run } from '../../../../packages/db/src/local';
import { consumer } from '../consumer/api';
import { FixtureMailbox } from '../consumer/otp';
import { admin } from './api';
import { hashPassword, type Context } from './security';
import { allowed, policy, reads, roles, type Action } from './policy';
import { validateRemedy } from './kb';
import spec from '../../../../openapi/admin.json';

const ctx: Context = {
  environment: 'test',
  origin: 'https://admin.example.test',
  publicOrigin: 'https://web.example.test',
  secret: randomBytes(32).toString('hex'),
};
const password = randomBytes(24).toString('hex');
let server: EmbeddedPostgres, pool: Pool;
type Jar = { cookies: Record<string, string>; csrf: string };
const empty = (): Jar => ({ cookies: {}, csrf: '' });
const jars: Record<string, Jar> = {};
async function call(
  jar: Jar,
  route: string,
  body?: object,
  context = ctx,
  overrides: Record<string, string> = {},
) {
  const req = new Request(ctx.origin + '/staff/' + route, {
    method: body ? 'POST' : 'GET',
    headers: {
      origin: ctx.origin,
      'content-type': 'application/json',
      cookie: Object.values(jar.cookies).join('; '),
      'x-staff-csrf': jar.csrf,
      ...overrides,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const res = await admin(req, pool, context);
  for (const line of res.headers.getSetCookie()) {
    const pair = line.split(';')[0];
    jar.cookies[pair.split('=')[0]] = pair;
  }
  return res;
}
async function signIn(email: string) {
  const jar = empty();
  const first = await call(jar, 'login', { email, password });
  expect(first.status).toBe(200);
  const { enrollment_secret } = await first.json();
  expect(enrollment_secret).toBeTypeOf('string');
  expect((await call(jar, 'dashboard')).status).toBe(401);
  const code = new TOTP({ secret: enrollment_secret }).generate();
  const verified = await call(jar, 'verify', { code });
  expect(verified.status).toBe(200);
  const reply = await verified.json();
  expect(reply.recovery_codes).toHaveLength(8);
  jar.csrf = reply.csrf;
  return jar;
}
beforeAll(async () => {
  const sock = createServer();
  await new Promise<void>((r) => sock.listen(0, '127.0.0.1', r));
  const port = (sock.address() as AddressInfo).port;
  await new Promise<void>((r) => sock.close(() => r()));
  const dir = await mkdtemp(join(tmpdir(), 'staff-db-')),
    key = randomBytes(16).toString('hex');
  server = new EmbeddedPostgres({
    databaseDir: dir,
    user: 'postgres',
    password: key,
    port,
    persistent: false,
    postgresFlags: ['-c', 'listen_addresses=127.0.0.1', '-k', dir],
    autoRehydrateSymlinks: true,
    onLog: () => {},
  });
  await server.initialise();
  await server.start();
  const url = `postgres://postgres:${key}@127.0.0.1:${port}/postgres`;
  await run('up', url);
  await run('seed', url, 'test');
  pool = new Pool({ connectionString: url });
  const provision = () =>
    execFileSync(
      process.execPath,
      ['node_modules/tsx/dist/cli.mjs', 'src/bootstrap-owner.ts'],
      {
        cwd: resolve('packages/db'),
        env: {
          ...process.env,
          DATABASE_URL: url,
          ADMIN_BOOTSTRAP_OWNER_EMAIL: 'owner@example.test',
          ADMIN_BOOTSTRAP_PASSWORD: password,
        },
        stdio: 'pipe',
      },
    );
  provision();
  expect(provision).toThrow();
  await pool.query(
    "UPDATE staff_users SET password_hash=$1 WHERE role<>'owner'",
    [await hashPassword(password)],
  );
  for (const [role, email] of Object.entries({
    owner: 'owner',
    admin: 'admin',
    'astrologer-reviewer': 'reviewer',
    'native-language reviewer': 'kn-reviewer',
    tester: 'tester',
    support: 'support',
  })) {
    jars[role] = await signIn(email + '@example.test');
    expect((await call(jars[role], 'dashboard')).status).toBe(200);
  }
}, 30000);
afterAll(async () => {
  await pool?.end();
  await server?.stop();
});

it('keeps consumer OTP, consumer sessions and staff credentials separate', async () => {
  const mailbox = new FixtureMailbox(),
    settings = {
      environment: 'test',
      secret: randomBytes(32).toString('hex'),
      webOrigin: ctx.publicOrigin,
      delivery: mailbox,
    };
  const send = (path: string, body: object) =>
    consumer(
      new Request(ctx.publicOrigin + '/consumer/otp/' + path, {
        method: 'POST',
        headers: { origin: ctx.publicOrigin },
        body: JSON.stringify(body),
      }),
      pool,
      settings,
    );
  const identifier = 'asha@example.test',
    channel = 'email';
  expect((await send('request', { identifier, channel })).status).toBe(202);
  const code = mailbox.read(channel, identifier);
  const verified = await send('verify', { identifier, channel, code });
  expect(verified.status).toBe(200);
  const header = verified.headers.get('set-cookie')!.split(';')[0];
  const jar = empty();
  jar.cookies.consumer = header;
  expect((await call(jar, 'verify', { code })).status).toBe(401);
  expect((await call(jar, 'dashboard')).status).toBe(401);
  jar.cookies.consumer = header.replace(
    '__Host-bhava-consumer',
    '__Host-bhava-staff',
  );
  expect((await call(jar, 'dashboard')).status).toBe(401);
  expect((await pool.query('SELECT id FROM staff_sessions')).rowCount).toBe(6);
  expect(
    (
      await call(jars.owner, 'dashboard', undefined, ctx, {
        origin: ctx.publicOrigin,
      })
    ).status,
  ).toBe(403);
  expect(
    (
      await call(jars.owner, 'dashboard', undefined, {
        ...ctx,
        country: 'changed',
      })
    ).status,
  ).toBe(401);
  expect(
    (
      await call(jars.owner, 'recovery/rotate', {}, ctx, {
        'x-staff-csrf': 'invalid',
      })
    ).status,
  ).toBe(403);
});
it('enforces role restrictions on every protected route before processing input', async () => {
  for (const role of roles) {
    for (const op of Object.keys(policy) as Action[]) {
      expect(Object.hasOwn(spec.paths, '/staff/' + op)).toBe(true);
      if (!allowed(op, role))
        expect(
          (await call(jars[role], op, reads.has(op) ? undefined : {})).status,
          role + ' ' + op,
        ).toBe(403);
    }
    expect((await call(jars[role], 'impersonate', {})).status).toBe(404);
  }
  expect((await call(jars.tester, 'users')).status).toBe(403);
  expect((await call(jars.support, 'users')).status).toBe(200);
  const entries = await (await call(jars.owner, 'settings')).json();
  expect(entries.length).toBeGreaterThan(3);
  for (const value of entries)
    expect(Object.keys(value).sort()).toEqual(['name', 'present']);
  expect(
    (
      await call(jars['native-language reviewer'], 'copy', {
        locale: 'hi',
        key: 'footer',
        text: 'test',
      })
    ).status,
  ).toBe(403);
});
it('requires an audited reason for sensitive access and scopes inspections and exports', async () => {
  const p = (
    await pool.query(
      "SELECT * FROM profiles WHERE display_name='Dev' AND time_precision='unknown'",
    )
  ).rows[0];
  const fixture = await (
    await call(jars.tester, 'inspector', { id: p.id })
  ).json();
  expect(fixture.user_saw).toBeNull();
  expect(fixture.staff_evidence).toMatchObject({
    engine: 'not_built',
    matching_points: null,
    lagna_facts: 'withheld',
  });
  const other = (
    await pool.query(
      `INSERT INTO profiles(user_id,display_name,birth_instant,local_date,local_time,iana_zone,place_id,time_precision,relation)
    SELECT user_id,display_name,birth_instant,local_date,local_time,iana_zone,place_id,time_precision,relation FROM profiles WHERE id=$1 RETURNING id`,
      [p.id],
    )
  ).rows[0];
  expect((await call(jars.tester, 'inspector', { id: other.id })).status).toBe(
    403,
  );
  for (const action of ['inspector', 'unmask']) {
    const input = { id: other.id, field: 'birth_instant' };
    expect((await call(jars.support, action, input)).status).toBe(400);
    expect(
      (
        await call(jars.support, action, {
          ...input,
          reason: 'Verify reported profile discrepancy',
        })
      ).status,
    ).toBe(200);
    const log = await (
      await call(jars.support, 'audit?action=' + action)
    ).json();
    expect(
      log.some(
        (r: { opaque_target_id: string }) => r.opaque_target_id === other.id,
      ),
    ).toBe(true);
  }
  expect(
    (
      await pool.query(
        'SELECT id FROM inspector_access_log WHERE opaque_profile_id=$1',
        [other.id],
      )
    ).rowCount,
  ).toBe(1);
  const flags = await (
    await call(jars.owner, 'flags?environment=development')
  ).json();
  expect(
    flags.find((f: { key: string }) => f.key === 'modern_outer').value,
  ).toBe(false);
});
it('validates overlays, publishes only as owner and requires a scoped revert approval', async () => {
  const entry = 'vedic.yogas.harsha',
    params = { entry, state: 'validated' };
  const publicCopy = () =>
    consumer(
      new Request(ctx.publicOrigin + '/consumer/rule-copy?entry=' + entry),
      pool,
      {
        environment: 'test',
        webOrigin: ctx.publicOrigin,
        secret: ctx.secret,
        delivery: new FixtureMailbox(),
      },
    );
  expect((await publicCopy()).status).toBe(404);
  for (const state of ['in_review', 'validated']) {
    const res = await call(jars['astrologer-reviewer'], 'kb/transition', {
      entry,
      state,
    });
    expect(res.status, await res.text()).toBe(200);
  }
  expect(
    (await call(jars.admin, 'kb/transition', { entry, state: 'approved' }))
      .status,
  ).toBe(403);
  expect(
    (await call(jars.owner, 'kb/transition', { entry, state: 'approved' }))
      .status,
  ).toBe(200);
  expect(Object.keys(await (await publicCopy()).json())).toEqual(['text']);
  const approved = await (
    await call(jars.owner, 'approvals', {
      operation: 'kb/revert',
      parameters: params,
    })
  ).json();
  expect(
    (
      await call(jars.admin, 'kb/transition', {
        ...params,
        approval: approved.id,
      })
    ).status,
  ).toBe(200);
  expect((await publicCopy()).status).toBe(404);
  const saturn = (await (await call(jars.owner, 'remedies')).json()).find(
    (r: { entry: string }) => r.entry === 'remedies.conduct.saturn',
  );
  expect(saturn.remedy.cost).toBe('free');
  for (const patch of [
    { cost: 'paid' },
    { optional: false },
    { user_text: { en: 'You must buy a gemstone' } },
  ]) {
    expect(() => validateRemedy({ ...saturn.remedy, ...patch })).toThrow();
  }
});

it('binds owner go-aheads to exact targets, consumes them once and audits hard-delete completion', async () => {
  const params = {
    environment: 'production',
    key: 'module.tarot',
    value: true,
  };
  expect((await call(jars.admin, 'flags/change', params)).status).toBe(403);
  const grant = await (
    await call(jars.owner, 'approvals', {
      operation: 'flags/change',
      parameters: params,
    })
  ).json();
  expect(
    (
      await call(jars.admin, 'flags/change', {
        ...params,
        value: false,
        approval: grant.id,
      })
    ).status,
  ).toBe(403);
  expect(
    (await call(jars.admin, 'flags/change', { ...params, approval: grant.id }))
      .status,
  ).toBe(200);
  expect(
    (await call(jars.owner, 'flags/change', { ...params, approval: grant.id }))
      .status,
  ).toBe(403);
  const user = (
    await pool.query(
      "SELECT user_id FROM profiles WHERE display_name='Kabir' LIMIT 1",
    )
  ).rows[0];
  const intake = await (
    await call(jars.support, 'requests/intake', {
      kind: 'delete',
      user_id: user.user_id,
    })
  ).json();
  expect(
    (await call(jars.admin, 'requests/complete', { id: intake.id })).status,
  ).toBe(403);
  const approval = await (
    await call(jars.owner, 'approvals', {
      operation: 'requests/complete',
      parameters: { id: intake.id },
    })
  ).json();
  expect(
    (
      await call(jars.admin, 'requests/complete', {
        id: intake.id,
        approval: approval.id,
      })
    ).status,
  ).toBe(200);
  expect(
    (
      await pool.query('SELECT id FROM profiles WHERE user_id=$1', [
        user.user_id,
      ])
    ).rowCount,
  ).toBe(0);
  expect(
    (
      await pool.query(
        "SELECT id FROM audit_log WHERE action='requests/complete' AND opaque_target_id=$1",
        [intake.id],
      )
    ).rowCount,
  ).toBe(1);
});
it('reviews assigned locale only and runs template deliveries locally', async () => {
  const native = jars['native-language reviewer'];
  const kn = await (
    await call(native, 'notifications/edit', {
      key: 'reflection',
      locale: 'kn',
      text: 'ನಿಮ್ಮ ಆಯ್ಕೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ',
    })
  ).json();
  expect(kn.state).toBe('pending');
  const hi = await (
    await call(jars.admin, 'notifications/edit', {
      key: 'reflection',
      locale: 'hi',
      text: 'अपने विकल्पों की समीक्षा करें',
    })
  ).json();
  expect(
    (await call(native, 'native/review', { id: hi.id, state: 'approved' }))
      .status,
  ).toBe(403);
  expect(
    (await call(native, 'native/review', { id: kn.id, state: 'approved' }))
      .status,
  ).toBe(200);
  expect(
    (await call(jars.owner, 'native/review', { id: hi.id, state: 'approved' }))
      .status,
  ).toBe(200);
  const n = await (
    await call(jars.owner, 'notifications/edit', {
      key: 'reflection',
      locale: 'en',
      text: 'You can review your choices.',
    })
  ).json();
  expect(
    (await call(jars.tester, 'notifications/test', { id: n.id })).status,
  ).toBe(200);
  expect((await call(jars.support, 'notifications')).status).toBe(200);
  expect(
    (
      await call(jars.admin, 'copy', {
        key: 'Privacy',
        locale: 'en',
        text: 'example',
      })
    ).status,
  ).toBe(400);
});
it('blocks test adapters even with a fully verified staff session in production settings', async () => {
  const prod = { ...ctx, environment: 'production' };
  // A separate factor namespace simulates a fresh environment on the disposable test cluster.
  await pool.query(
    "DELETE FROM staff_mfa_devices WHERE staff_id=(SELECT id FROM staff_users WHERE role='tester')",
  );
  const jar = empty(),
    email = 'tester@example.test';
  const login = await (
    await call(jar, 'login', { email, password }, prod)
  ).json();
  const verified = await (
    await call(
      jar,
      'verify',
      { code: new TOTP({ secret: login.enrollment_secret }).generate() },
      prod,
    )
  ).json();
  jar.csrf = verified.csrf;
  expect((await call(jar, 'dashboard', undefined, prod)).status).toBe(200);
  for (const op of ['payments/test', 'fixtures/code', 'notifications/test']) {
    expect((await call(jar, op, {}, prod)).status).toBe(403);
  }
  await pool.query(
    "UPDATE staff_sessions SET last_seen=now()-interval '9 hours' WHERE staff_id=(SELECT id FROM staff_users WHERE role='tester')",
  );
  expect((await call(jar, 'dashboard', undefined, prod)).status).toBe(401);
});

it('matches the six independent permission columns for representative module actions', () => {
  const cases: Record<string, string> = {
    dashboard: 'YYYYYY',
    users: 'YY---Y',
    unmask: 'YY---Y',
    testers: 'YY----',
    fixtures: 'YYY-Y-',
    inspector: 'YYY-YY',
    kb: 'YYYYY-',
    'kb/edit': 'YYY---',
    'native/review': 'YY-Y--',
    ai: 'YYY-YY',
    copy: 'YY-Y--',
    legal: 'Y-----',
    remedies: 'YYYYY-',
    'flags/change': 'YY----',
    'flags/request': '----Y-',
    jobs: 'YY--YY',
    'jobs/retry': 'YY--Y-',
    payments: 'YY--YY',
    'payments/live': 'Y-----',
    'notifications/edit': 'YY-Y--',
    'notifications/test': 'YY--Y-',
    'notifications/broadcast': 'YY----',
    audit: 'YYYYYY',
    settings: 'YY----',
    'staff/role': 'YY----',
    'requests/intake': 'YY---Y',
    'requests/complete': 'YY----',
    approvals: 'Y-----',
  };
  for (const [op, expected] of Object.entries(cases))
    expect(
      roles.map((role) => (allowed(op as Action, role) ? 'Y' : '-')).join(''),
      op,
    ).toBe(expected);
});

it('rotates recovery credentials, consumes a code once and keeps secrets out of audit', async () => {
  const rotated = await (await call(jars.admin, 'recovery/rotate', {})).json();
  expect(rotated.recovery_codes).toHaveLength(8);
  const key = rotated.recovery_codes[0],
    jar = empty();
  expect(
    (await call(jar, 'login', { email: 'admin@example.test', password }))
      .status,
  ).toBe(200);
  expect((await call(jar, 'verify', { recovery_code: key })).status).toBe(200);
  expect(
    (await call(jar, 'login', { email: 'admin@example.test', password }))
      .status,
  ).toBe(200);
  expect((await call(jar, 'verify', { recovery_code: key })).status).toBe(401);
  const audit = JSON.stringify(
    (await pool.query('SELECT * FROM audit_log')).rows,
  );
  expect(audit).not.toContain(key);
  expect(audit).not.toContain(password);
  expect(audit).not.toContain('admin@example.test');
  expect(
    (
      await pool.query(
        'SELECT code_hash FROM staff_recovery_codes WHERE code_hash=$1',
        [key],
      )
    ).rowCount,
  ).toBe(0);
});

it('requires an owner for grants of the owner role, allows scoped lower-role grants', async () => {
  const reviewer = (
    await pool.query(
      "SELECT id FROM staff_users WHERE email='reviewer@example.test'",
    )
  ).rows[0];
  expect(
    (await call(jars.admin, 'staff/role', { id: reviewer.id, role: 'owner' }))
      .status,
  ).toBe(403);
  expect(
    (await call(jars.owner, 'staff/role', { id: reviewer.id, role: 'owner' }))
      .status,
  ).toBe(200);
  expect((await call(jars['astrologer-reviewer'], 'dashboard')).status).toBe(
    401,
  );
});

it('builds a public-field export only for the account on the request', async () => {
  const user = (
    await pool.query(
      "SELECT user_id FROM profiles WHERE display_name='Asha' LIMIT 1",
    )
  ).rows[0].user_id;
  const request = await (
    await call(jars.support, 'requests/intake', {
      kind: 'export',
      user_id: user,
    })
  ).json();
  expect(
    (await call(jars.support, 'requests/export', { id: request.id })).status,
  ).toBe(403);
  const data = await (
    await call(jars.owner, 'requests/export', { id: request.id })
  ).json();
  const expected = (
    await pool.query(
      'SELECT id FROM profiles WHERE user_id=$1 AND deleted_at IS NULL',
      [user],
    )
  ).rows
    .map((r) => r.id)
    .sort();
  expect(data.profiles.map((p: { id: string }) => p.id).sort()).toEqual(
    expected,
  );
  for (const p of data.profiles)
    expect(Object.keys(p).sort()).toEqual([
      'display_name',
      'id',
      'relation',
      'time_precision',
    ]);
});

it('exposes the allowlisted settings shape without injected values', async () => {
  const payload = await (await call(jars.owner, 'settings')).json();
  expect(payload.map((v: { name: string }) => v.name)).toEqual([
    'AI_PROVIDER',
    'GEMINI_API_KEY',
    'OPENAI_API_KEY',
    'RAZORPAY_KEY_ID',
    'RAZORPAY_KEY_SECRET',
    'RESEND_API_KEY',
    'SWEPH_PATH',
    'OTP_PROVIDER',
    'ADMIN_BOOTSTRAP_OWNER_EMAIL',
  ]);
  for (const line of payload)
    expect(line).toEqual({
      name: expect.any(String),
      present: expect.any(Boolean),
    });
});
