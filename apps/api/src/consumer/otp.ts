import {
  createHash,
  createHmac,
  randomBytes,
  randomInt,
  randomUUID,
  timingSafeEqual,
} from 'node:crypto';
import type { OtpPort } from '../providers';
import type { Pool, PoolClient } from 'pg';
import {
  ApiError,
  invalid,
  locale,
  text,
  transaction,
  type Body,
} from './common';

export type Channel = 'phone' | 'email';

// Process-local development mailbox. Never expose this through an HTTP route.
export class FixtureMailbox implements OtpPort {
  private codes = new Map<string, string>();
  send(channel: Channel, recipient: string, code: string) {
    this.codes.set(channel + recipient, code);
  }
  read(channel: Channel, recipient: string) {
    return this.codes.get(channel + recipient);
  }
}
export interface Settings {
  environment: string;
  webOrigin: string;
  secret: string;
  delivery: OtpPort;
}
const digest = (value: string) =>
  createHash('sha256').update(value).digest('hex');
function keyed(settings: Settings, purpose: string, value: string) {
  return createHmac('sha256', settings.secret)
    .update(JSON.stringify([settings.environment, purpose, value]))
    .digest('hex');
}
export function tokenHash(settings: Settings, token: string) {
  return keyed(settings, 'consumer-session', token);
}
const names = ['asha', 'ravi', 'meera', 'kabir', 'dev'];
function recipient(body: Body) {
  const input = text(body.identifier, 254);
  if (body.channel === 'email') {
    const address = input.toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(address)) return invalid();
    return {
      channel: 'email' as const,
      address,
      fixture: names.find((n) => address === n + '@example.test'),
    };
  }
  if (body.channel !== 'phone') return invalid();
  const digits = input.replace(/[ ()-]/g, '');
  const address = /^\d{10}$/.test(digits) ? '+91' + digits : digits;
  if (!/^\+[1-9]\d{7,14}$/.test(address)) return invalid();
  return {
    channel: 'phone' as const,
    address,
    fixture: names.find((_, i) => address === '+91900000000' + (i + 1)),
  };
}

async function limit(
  pool: Pool,
  settings: Settings,
  operation: string,
  identifier: string,
  ip: string,
) {
  const verify = operation === 'verify';
  const allowed = await transaction(pool, async (db) => {
    await db.query(
      "DELETE FROM otp_rate_limits WHERE window_start < now()-interval '1 day'",
    );
    let accepted = true;
    for (const [scope, value, max] of [
      ['ip', ip, verify ? 60 : 30],
      ['identifier', identifier, verify ? 20 : 6],
    ] as const) {
      const result = await db.query(
        `INSERT INTO otp_rate_limits VALUES ($1,now(),1)
        ON CONFLICT (bucket) DO UPDATE SET
          hits=CASE WHEN otp_rate_limits.window_start <= now()-interval '10 minutes' THEN 1 ELSE least(otp_rate_limits.hits+1,1000) END,
          window_start=CASE WHEN otp_rate_limits.window_start <= now()-interval '10 minutes' THEN now() ELSE otp_rate_limits.window_start END
        RETURNING hits`,
        [keyed(settings, operation + scope, value)],
      );
      if (result.rows[0].hits > max) {
        accepted = false;
        break;
      }
    }
    return accepted;
  });
  if (!allowed) throw new ApiError(429, 'wait');
}

async function fixtureIdentity(
  db: PoolClient,
  who: ReturnType<typeof recipient>,
) {
  if (!who.fixture) return;
  const result = await db.query(
    `SELECT i.id,i.user_id FROM identities i JOIN users u ON u.id=i.user_id
    WHERE kind=$1 AND identifier_digest=$2 AND u.deactivated_at IS NULL
    AND u.id=md5('fixture:user:' || initcap($3))::uuid FOR UPDATE OF u,i`,
    [who.channel, digest(who.address), who.fixture],
  );
  return result.rows[0];
}

export async function issueFixtureCode(
  db: PoolClient,
  settings: Settings,
  body: Body,
  ip: string,
) {
  if (!['test', 'development'].includes(settings.environment))
    throw new ApiError(403, 'denied');
  const who = recipient(body);
  const code = randomInt(1_000_000).toString().padStart(6, '0');
  const identity = await fixtureIdentity(db, who);
  if (!identity) return undefined;
  const recent = await db.query(
    "SELECT id FROM otp_challenges WHERE identity_id=$1 AND created_at>now()-interval '30 seconds'",
    [identity.id],
  );
  if (recent.rowCount) throw new ApiError(429, 'wait');
  await db.query(
    'UPDATE otp_challenges SET consumed_at=now() WHERE identity_id=$1 AND consumed_at IS NULL',
    [identity.id],
  );
  const id = randomUUID();
  await db.query(
    `INSERT INTO otp_challenges(id,identity_id,code_hash,ip_digest,expires_at)
        VALUES ($1,$2,$3,$4,now()+interval '10 minutes')`,
    [id, identity.id, keyed(settings, id, code), keyed(settings, 'ip', ip)],
  );
  return code;
}
export async function otp(
  pool: Pool,
  settings: Settings,
  mode: 'request' | 'verify',
  body: Body,
  ip: string,
) {
  if (!['test', 'development'].includes(settings.environment))
    throw new ApiError(503, 'unavailable');
  const who = recipient(body);
  await limit(pool, settings, mode, who.address, ip);
  if (mode === 'request') {
    const code = await transaction(pool, (db) =>
      issueFixtureCode(db, settings, body, ip),
    );
    if (code) settings.delivery.send(who.channel, who.address, code);
    return;
  }
  const language = locale(body.locale ?? 'en');
  const code = text(body.code, 6);
  if (!/^\d{6}$/.test(code)) return invalid();
  const token = await transaction(pool, async (db) => {
    const identity = await fixtureIdentity(db, who);
    if (!identity) return;
    const result = await db.query(
      `SELECT id,code_hash FROM otp_challenges WHERE identity_id=$1
      AND consumed_at IS NULL AND expires_at>now() AND attempts<5 ORDER BY created_at DESC LIMIT 1 FOR UPDATE`,
      [identity.id],
    );
    const challenge = result.rows[0];
    if (!challenge) return;
    if (
      !timingSafeEqual(
        Buffer.from(challenge.code_hash),
        Buffer.from(keyed(settings, challenge.id, code)),
      )
    ) {
      await db.query(
        'UPDATE otp_challenges SET attempts=attempts+1 WHERE id=$1',
        [challenge.id],
      );
      return;
    }
    await db.query('UPDATE otp_challenges SET consumed_at=now() WHERE id=$1', [
      challenge.id,
    ]);
    const token = randomBytes(32).toString('base64url');
    await db.query(
      "INSERT INTO sessions(user_id,token_hash,locale,expires_at) VALUES ($1,$2,$3,now()+interval '30 days')",
      [identity.user_id, tokenHash(settings, token), language],
    );
    return token;
  });
  if (!token) throw new ApiError(401, 'invalidCode');
  return token;
}
