import { randomBytes } from 'node:crypto';
import { Secret } from 'otpauth';
import type { Pool, PoolClient } from 'pg';
import { transaction } from '../consumer/common';
import {
  audit,
  binding,
  clock,
  cookie,
  demand,
  device,
  headerCookie,
  mac,
  passwordMatches,
  pending,
  seal,
  session,
  string,
  throttle,
  token,
  type Context,
  type Input,
  type Staff,
} from './security';

export function response(value: unknown, status = 200, cookies: string[] = []) {
  const headers = new Headers({
    'Cache-Control': 'no-store',
    Vary: 'Origin',
    'X-Content-Type-Options': 'nosniff',
  });
  for (const line of cookies) headers.append('Set-Cookie', line);
  return Response.json(value, { status, headers });
}
export async function recoveryCodes(db: PoolClient, c: Context, s: Staff) {
  await db.query('DELETE FROM staff_recovery_codes WHERE staff_id=$1', [s.id]);
  const codes = Array.from({ length: 8 }, () =>
    randomBytes(12).toString('hex'),
  );
  for (const code of codes)
    await db.query(
      'INSERT INTO staff_recovery_codes(staff_id,code_hash) VALUES($1,$2)',
      [s.id, mac(c, 'recovery:' + s.id, code)],
    );
  return codes;
}
export async function login(pool: Pool, c: Context, r: Request, b: Input) {
  await throttle(pool, c, 'login-ip', c.ip ?? 'shared', 60);
  const email = string(b.email, 254).toLowerCase();
  await throttle(pool, c, 'login-email', email, 8);
  demand(
    typeof b.password === 'string' &&
      b.password.length > 0 &&
      b.password.length <= 512,
  );
  const password = b.password;
  return transaction(pool, async (db) => {
    const s = (
      await db.query(
        'SELECT * FROM staff_users WHERE email=$1 AND disabled_at IS NULL AND (expires_at IS NULL OR expires_at>now()) FOR UPDATE',
        [email],
      )
    ).rows[0];
    demand(
      await passwordMatches(password, s?.password_hash),
      401,
      'Sign-in failed',
    );
    const enrolled = !!(
      await db.query('SELECT id FROM staff_mfa_devices WHERE staff_id=$1', [
        s.id,
      ])
    ).rowCount;
    const seed = enrolled ? undefined : new Secret({ size: 20 }).base32;
    const challenge = token(),
      deviceId = token();
    await db.query(
      `INSERT INTO staff_login_challenges(token_hash,staff_id,binding,expires_at,enrollment_ciphertext)
      VALUES ($1,$2,$3,now()+interval '5 minutes',$4) ON CONFLICT(staff_id) DO UPDATE
      SET token_hash=excluded.token_hash,binding=excluded.binding,expires_at=excluded.expires_at,enrollment_ciphertext=excluded.enrollment_ciphertext`,
      [
        mac(c, 'challenge', challenge),
        s.id,
        binding(c, r, deviceId),
        seed ? seal(c, s.id, seed) : null,
      ],
    );
    await audit(db, c, r, s, 'login.first-factor');
    return response(
      { next: 'totp', ...(seed ? { enrollment_secret: seed } : {}) },
      200,
      [
        headerCookie(pending, challenge, 300),
        headerCookie(device, deviceId, 43200),
      ],
    );
  });
}
export async function verify(pool: Pool, c: Context, r: Request, b: Input) {
  const challenge = cookie(r, pending),
    deviceId = cookie(r, device);
  demand(challenge && deviceId, 401, 'Login required');
  await throttle(pool, c, 'verify-ip', c.ip ?? 'shared', 60);
  await throttle(pool, c, 'verify-challenge', challenge, 5);
  return transaction(pool, async (db) => {
    const s = (
      await db.query(
        `SELECT s.*,p.enrollment_ciphertext FROM staff_login_challenges p JOIN staff_users s ON s.id=p.staff_id
      WHERE p.token_hash=$1 AND p.binding=$2 AND p.expires_at>now() AND s.disabled_at IS NULL AND (s.expires_at IS NULL OR s.expires_at>now()) FOR UPDATE OF s,p`,
        [mac(c, 'challenge', challenge), binding(c, r, deviceId)],
      )
    ).rows[0];
    demand(s, 401, 'Login required');
    const factor = (
      await db.query(
        'SELECT * FROM staff_mfa_devices WHERE staff_id=$1 FOR UPDATE',
        [s.id],
      )
    ).rows[0];
    let codes: string[] | undefined;
    if (b.recovery_code && factor) {
      const result = await db.query(
        'UPDATE staff_recovery_codes SET used_at=now() WHERE staff_id=$1 AND code_hash=$2 AND used_at IS NULL RETURNING id',
        [s.id, mac(c, 'recovery:' + s.id, string(b.recovery_code))],
      );
      demand(result.rowCount, 401, 'Verification failed');
    } else {
      const encrypted = factor?.secret_ciphertext ?? s.enrollment_ciphertext;
      demand(encrypted, 401, 'Login required');
      const timestamp = Date.now();
      const delta = clock(c, s.id, encrypted).validate({
        token: string(b.code, 6),
        window: 1,
        timestamp,
      });
      demand(delta !== null, 401, 'Verification failed');
      const step = Math.floor(timestamp / 30000) + delta;
      demand(
        step > Number(factor?.last_step ?? -1),
        401,
        'Verification failed',
      );
      if (factor)
        await db.query(
          'UPDATE staff_mfa_devices SET last_step=$2 WHERE id=$1',
          [factor.id, step],
        );
      else {
        await db.query(
          "INSERT INTO staff_mfa_devices(staff_id,secret_ciphertext,key_version,last_step) VALUES($1,$2,'1',$3)",
          [s.id, encrypted, step],
        );
        codes = await recoveryCodes(db, c, s);
      }
    }
    await db.query('DELETE FROM staff_login_challenges WHERE staff_id=$1', [
      s.id,
    ]);
    const key = token();
    await db.query(
      "INSERT INTO staff_sessions(staff_id,token_hash,binding,expires_at) VALUES($1,$2,$3,now()+interval '12 hours')",
      [s.id, mac(c, 'session', key), binding(c, r, deviceId)],
    );
    await audit(db, c, r, s, codes ? 'mfa.enrolled' : 'login.verified');
    return response(
      {
        csrf: mac(c, 'csrf', key),
        ...(codes ? { recovery_codes: codes } : {}),
      },
      200,
      [headerCookie(session, key, 43200), headerCookie(pending, '', 0)],
    );
  });
}
export async function authenticate(
  db: PoolClient,
  c: Context,
  r: Request,
): Promise<Staff> {
  const key = cookie(r, session);
  demand(key, 401, 'Staff session required');
  const s = (
    await db.query(
      `UPDATE staff_sessions t SET last_seen=now() FROM staff_users u
    WHERE t.token_hash=$1 AND u.id=t.staff_id AND t.revoked_at IS NULL AND t.binding=$2 AND t.expires_at>now()
    AND t.last_seen>now()-interval '8 hours' AND u.disabled_at IS NULL AND (u.expires_at IS NULL OR u.expires_at>now())
    RETURNING u.id,u.role,u.assigned_locale,u.fixture_user_id`,
      [mac(c, 'session', key), binding(c, r, cookie(r, device))],
    )
  ).rows[0];
  demand(s, 401, 'Staff session required');
  if (r.method !== 'GET')
    demand(
      r.headers.get('x-staff-csrf') === mac(c, 'csrf', key),
      403,
      'CSRF verification failed',
    );
  return s;
}
