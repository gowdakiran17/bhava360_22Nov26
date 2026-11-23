import { randomBytes } from 'node:crypto';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer, type AddressInfo } from 'node:net';
import { Pool } from 'pg';
import EmbeddedPostgres from 'embedded-postgres';
import { beforeAll, afterAll, it, expect } from 'vitest';
import { resolveBirth } from '@bhava360/core';
import { run } from '../../../../packages/db/src/local';
import { consumer } from './api';
import { FixtureMailbox } from './otp';

const origin = 'https://consumer.example.test';
const address = 'asha@example.test';
const mailbox = new FixtureMailbox();
const settings = {
  environment: 'test',
  secret: randomBytes(32).toString('hex'),
  webOrigin: origin,
  delivery: mailbox,
};
let server: EmbeddedPostgres;
let pool: Pool;
let cookie = '';
async function call(
  path: string,
  method = 'GET',
  body?: object,
  session = cookie,
  env = 'test',
  host = origin,
  ip = '127.0.0.1',
) {
  return consumer(
    new Request(host + '/consumer/' + path, {
      method,
      headers: { origin: host, cookie: session },
      body: body ? JSON.stringify(body) : undefined,
    }),
    pool,
    { ...settings, environment: env },
    ip,
  );
}
const send = (channel = 'email', identifier = address) =>
  call('otp/request', 'POST', { channel, identifier });
const verify = (code: string, channel = 'email', identifier = address) =>
  call('otp/verify', 'POST', { channel, identifier, code, locale: 'kn' });
async function login(channel: 'email' | 'phone', identifier: string) {
  expect((await send(channel, identifier)).status).toBe(202);
  const code = mailbox.read(channel, identifier);
  expect(code).toMatch(/^\d{6}$/);
  const response = await verify(code!, channel, identifier);
  expect(response.status).toBe(200);
  expect(await response.json()).toEqual({ authenticated: true });
  const header = response.headers.get('set-cookie')!;
  expect(header).toContain('HttpOnly; Secure; SameSite=Strict');
  return header.split(';')[0];
}
beforeAll(async () => {
  const socket = createServer();
  await new Promise<void>((r) => socket.listen(0, '127.0.0.1', r));
  const port = (socket.address() as AddressInfo).port;
  await new Promise<void>((r) => socket.close(() => r()));
  const directory = await mkdtemp(join(tmpdir(), 'bhava-auth-'));
  const password = randomBytes(24).toString('hex');
  server = new EmbeddedPostgres({
    databaseDir: directory,
    user: 'postgres',
    password,
    port,
    persistent: false,
    postgresFlags: ['-c', 'listen_addresses=127.0.0.1', '-k', directory],
    autoRehydrateSymlinks: true,
    onLog: () => {},
  });
  await server.initialise();
  await server.start();
  const url = `postgres://postgres:${password}@127.0.0.1:${port}/postgres`;
  await run('up', url);
  await run('seed', url, 'test');
  pool = new Pool({ connectionString: url });
}, 30000);
afterAll(async () => {
  await pool?.end();
  await server?.stop();
});

it('rejects production dummy delivery and verification, even with a valid test challenge', async () => {
  expect(
    (
      await call(
        'otp/request',
        'POST',
        { channel: 'email', identifier: address },
        '',
        'production',
      )
    ).status,
  ).toBe(503);
  expect((await send()).status).toBe(202);
  const code = mailbox.read('email', address)!;
  expect(
    (
      await call(
        'otp/verify',
        'POST',
        { channel: 'email', identifier: address, code },
        '',
        'production',
      )
    ).status,
  ).toBe(503);
  expect((await verify(code)).status).toBe(200);
  expect((await verify(code)).status).toBe(401);
});
it('enforces resend delay, hash rotation, expiry and five attempts', async () => {
  const email = 'ravi@example.test';
  await send('email', email);
  expect((await send('email', email)).status).toBe(429);
  const before = (
    await pool.query(
      'SELECT code_hash FROM otp_challenges ORDER BY created_at DESC LIMIT 1',
    )
  ).rows[0].code_hash;
  await pool.query(
    "UPDATE otp_challenges SET created_at=created_at-interval '31 seconds'",
  );
  expect((await send('email', email)).status).toBe(202);
  const after = (
    await pool.query(
      'SELECT code_hash FROM otp_challenges ORDER BY created_at DESC LIMIT 1',
    )
  ).rows[0].code_hash;
  expect(after).not.toEqual(before);
  const code = mailbox.read('email', email)!;
  for (let i = 0; i < 5; i++)
    expect(
      (await verify(code === '000000' ? '111111' : '000000', 'email', email))
        .status,
    ).toBe(401);
  expect((await verify(code, 'email', email)).status).toBe(401);
  await pool.query(
    "UPDATE otp_challenges SET created_at=created_at-interval '31 seconds'",
  );
  await send('email', email);
  await pool.query(
    'UPDATE otp_challenges SET expires_at=now() WHERE consumed_at IS NULL',
  );
  expect(
    (await verify(mailbox.read('email', email)!, 'email', email)).status,
  ).toBe(401);
});
it('limits both operations by identifier and by IP', async () => {
  for (const [action, maximum, ipMaximum] of [
    ['request', 6, 30],
    ['verify', 20, 60],
  ] as const) {
    await pool.query('DELETE FROM otp_rate_limits');
    const body = {
      channel: 'email',
      identifier: 'dev@example.test',
      code: '000000',
    };
    for (let i = 0; i < maximum; i++) await call('otp/' + action, 'POST', body);
    expect((await call('otp/' + action, 'POST', body)).status).toBe(429);
    await pool.query('DELETE FROM otp_rate_limits');
    for (let i = 0; i < ipMaximum; i++)
      await call('otp/' + action, 'POST', {
        ...body,
        identifier: 'dev+' + i + '@example.test',
      });
    expect((await call('otp/' + action, 'POST', body)).status).toBe(429);
  }
  await pool.query('DELETE FROM otp_rate_limits');
});
it('persists scoped sessions, profiles and consent decisions', async () => {
  cookie = await login('phone', '+919000000001');
  expect(
    (
      await call(
        'session',
        'GET',
        undefined,
        cookie,
        'test',
        'https://staff.example.test',
      )
    ).status,
  ).toBe(403);
  const existing = await (await call('profiles')).json();
  const places = async (q: string) =>
    (await (await call('places?q=' + q)).json())[0];
  expect((await places('Mysore')).id).toBe((await places('Mysuru')).id);
  expect((await places('Bangalore')).id).toBe((await places('Bengaluru')).id);
  const consent = {
    adult: true,
    terms: true,
    birthDetails: true,
    analytics: false,
    consent_version: 'fixture-v1',
  };
  expect(
    (await call('consents', 'POST', { ...consent, terms: false })).status,
  ).toBe(400);
  const records = await (await call('consents', 'POST', consent)).json();
  expect(records).toHaveLength(6);
  expect(records[0]).toMatchObject({
    version: 'fixture-v1',
    recorded_at: expect.any(String),
  });
  const asha = {
    display_name: 'Asha',
    relation: 'self',
    local_date: '1992-03-12',
    local_time: '05:40',
    time_precision: 'known',
    place_id: (await places('Bengaluru')).id,
  };
  const created = await (await call('profiles', 'POST', asha)).json();
  expect(created.birth_instant).toBe('1992-03-12T00:10:00.000Z');
  const updated = await (
    await call('profiles/' + created.id, 'PATCH', {
      time_precision: 'approximate',
    })
  ).json();
  expect(updated.birth_instant).toBe(created.birth_instant);
  expect(updated.time_precision).toBe('approximate');
  await call('profiles/' + created.id + '/switch', 'POST');
  expect(await (await call('session')).json()).toEqual({
    locale: 'kn',
    active_profile_id: created.id,
  });
  const dev = {
    display_name: 'Dev',
    relation: 'adult',
    adult_permission: true,
    local_date: '1995-01-05',
    time_precision: 'unknown',
    place_id: (await places('Chennai')).id,
  };
  expect(
    (await call('profiles', 'POST', { ...dev, adult_permission: false }))
      .status,
  ).toBe(400);
  const concurrent = await Promise.all([
    call('profiles', 'POST', dev),
    call('profiles', 'POST', dev),
  ]);
  expect(concurrent.map((r) => r.status).sort()).toEqual([200, 409]);
  expect(await concurrent.find((r) => r.ok)!.json()).toMatchObject({
    local_time: '12:00:00',
    birth_instant: '1995-01-05T06:30:00.000Z',
  });
  await call('profiles/' + created.id, 'DELETE');
  expect((await (await call('session')).json()).active_profile_id).toBeNull();
  expect((await call('profiles/' + created.id)).status).toBe(404);
  const other = await login('email', 'meera@example.test');
  expect(
    (await call('profiles/' + existing[0].id, 'DELETE', undefined, other))
      .status,
  ).toBe(404);
  await pool.query(
    "UPDATE otp_challenges SET created_at=created_at-interval '31 seconds'",
  );
  const second = await login('email', address);
  await call('logout', 'POST', {}, cookie);
  expect((await call('session')).status).toBe(401);
  expect((await call('session', 'GET', undefined, second)).status).toBe(200);
  await call('logout-all', 'POST', {}, second);
  expect((await call('session', 'GET', undefined, second)).status).toBe(401);
  expect((await call('session', 'GET', undefined, other)).status).toBe(200);
  expect(
    (
      await pool.query(
        "SELECT value FROM feature_flags WHERE key='module.numerology'",
      )
    ).rows,
  ).toEqual(Array(3).fill({ value: false }));
});
it('delivers development codes only to the exact seeded accounts', async () => {
  for (const identifier of ['kabir@example.test', 'owner@example.test']) {
    const result = await call(
      'otp/request',
      'POST',
      { channel: 'email', identifier },
      '',
      'development',
    );
    expect(result.status).toBe(202);
  }
  expect(mailbox.read('email', 'owner@example.test')).toBeUndefined();
  const result = await call(
    'otp/verify',
    'POST',
    {
      channel: 'email',
      identifier: 'kabir@example.test',
      code: mailbox.read('email', 'kabir@example.test'),
    },
    '',
    'development',
  );
  expect(result.status).toBe(200);
});
it('requires a choice for repeated wall time and rejects a skipped time', () => {
  const zone = 'America/New_York';
  expect(() => resolveBirth('2020-11-01', '01:30', zone)).toThrow('chooseTime');
  expect(resolveBirth('2020-11-01', '01:30', zone, 'earlier')).toBe(
    '2020-11-01T05:30:00Z',
  );
  expect(resolveBirth('2020-11-01', '01:30', zone, 'later')).toBe(
    '2020-11-01T06:30:00Z',
  );
  expect(() => resolveBirth('2020-03-08', '02:30', zone)).toThrow();
});
