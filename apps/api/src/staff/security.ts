import {
  createCipheriv,
  createDecipheriv,
  createHmac,
  randomBytes,
  scrypt,
  timingSafeEqual,
} from 'node:crypto';
import { promisify } from 'node:util';
import { TOTP, Secret } from 'otpauth';
import type { Pool, PoolClient } from 'pg';

const derive = promisify(scrypt);
export class Failure extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}
export function demand(
  condition: unknown,
  status = 400,
  message = 'Invalid request',
): asserts condition {
  if (!condition) throw new Failure(status, message);
}
export function string(value: unknown, max = 300) {
  demand(
    typeof value === 'string' && value.trim().length > 0 && value.length <= max,
  );
  return value.trim();
}
export const id = (v: unknown) => {
  const s = string(v, 36);
  demand(/^[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12}$/i.test(s));
  return s;
};
export type Input = Record<string, unknown>;
export type Staff = {
  id: string;
  role: string;
  assigned_locale: string | null;
  fixture_user_id: string | null;
};
export interface Context {
  secret: string;
  origin: string;
  publicOrigin: string;
  environment: string;
  country?: string;
  ip?: string;
}
export const token = () => randomBytes(32).toString('base64url');
export const mac = (ctx: Context, label: string, value: string) =>
  createHmac('sha256', ctx.secret)
    .update(JSON.stringify([ctx.environment, ctx.origin, label, value]))
    .digest('hex');
export const cookie = (req: Request, name: string) =>
  req.headers
    .get('cookie')
    ?.split(/;\s*/)
    .find((s) => s.startsWith(name + '='))
    ?.slice(name.length + 1) ?? '';
export const headerCookie = (name: string, value: string, age: number) =>
  name +
  '=' +
  value +
  '; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=' +
  age;
export const pending = '__Host-bhava-staff-login',
  session = '__Host-bhava-staff',
  device = '__Host-bhava-staff-device';
export const binding = (c: Context, r: Request, d: string) =>
  mac(
    c,
    'device',
    JSON.stringify([d, r.headers.get('user-agent'), c.country ?? 'unknown']),
  );
export async function hashPassword(password: string) {
  const salt = randomBytes(16).toString('hex');
  return (
    salt + ':' + ((await derive(password, salt, 64)) as Buffer).toString('hex')
  );
}
export async function passwordMatches(password: string, hash: string | null) {
  const [salt, saved] = (hash ?? 'unused:').split(':');
  const actual = (await derive(password, salt, 64)) as Buffer;
  const expected = Buffer.from(saved, 'hex');
  return expected.length === actual.length && timingSafeEqual(actual, expected);
}
export function seal(c: Context, staffId: string, secret: string) {
  const iv = randomBytes(12),
    cipher = createCipheriv(
      'aes-256-gcm',
      Buffer.from(mac(c, 'key', 'totp'), 'hex'),
      iv,
    );
  cipher.setAAD(Buffer.from(staffId));
  const data = Buffer.concat([cipher.update(secret, 'utf8'), cipher.final()]);
  return [iv, data, cipher.getAuthTag()]
    .map((b) => b.toString('base64url'))
    .join('.');
}
export function clock(c: Context, staffId: string, encrypted: string) {
  const [iv, data, tag] = encrypted
    .split('.')
    .map((b) => Buffer.from(b, 'base64url'));
  const decipher = createDecipheriv(
    'aes-256-gcm',
    Buffer.from(mac(c, 'key', 'totp'), 'hex'),
    iv,
  );
  decipher.setAAD(Buffer.from(staffId));
  decipher.setAuthTag(tag);
  return new TOTP({
    secret: Secret.fromBase32(
      Buffer.concat([decipher.update(data), decipher.final()]).toString(),
    ),
  });
}
export async function throttle(
  pool: Pick<Pool, 'query'>,
  c: Context,
  scope: string,
  subject: string,
  max: number,
) {
  const { rows } = await pool.query(
    `INSERT INTO otp_rate_limits VALUES ($1,now(),1) ON CONFLICT(bucket) DO UPDATE SET
   hits=CASE WHEN otp_rate_limits.window_start<now()-interval '15 minutes' THEN 1 ELSE least(otp_rate_limits.hits+1,10000) END,
   window_start=CASE WHEN otp_rate_limits.window_start<now()-interval '15 minutes' THEN now() ELSE otp_rate_limits.window_start END RETURNING hits`,
    [mac(c, 'staff-limit:' + scope, subject)],
  );
  demand(rows[0].hits <= max, 429, 'Temporarily locked');
}
export function reason(v: unknown) {
  const s = string(v, 200);
  demand(s.length >= 4, 400, 'Enter a reason');
  return s
    .replace(/[^\s@]+@[^\s@]+/gu, '[redacted]')
    .replace(
      /(?:\+?\d[\d .():/-]{4,}\d)|(?:[A-Za-z0-9_-]{32,})/gu,
      '[redacted]',
    );
}
export async function audit(
  db: PoolClient,
  c: Context,
  r: Request,
  s: Staff,
  action: string,
  target = s.id,
  note = 'Staff operation',
  details: Input = {},
) {
  await db.query(
    `INSERT INTO audit_log(actor_id,role,action,target_type,opaque_target_id,reason,ip_digest,user_agent,new_value)
   VALUES($1,$2,$3,'staff-operation',$4,$5,$6,$7,$8)`,
    [
      s.id,
      s.role,
      action,
      target,
      note,
      mac(c, 'ip', c.ip ?? 'shared'),
      mac(c, 'agent', r.headers.get('user-agent') ?? ''),
      JSON.stringify(details),
    ],
  );
}
