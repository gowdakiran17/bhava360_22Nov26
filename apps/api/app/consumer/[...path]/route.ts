import { randomBytes } from 'node:crypto';
import { Pool } from 'pg';
import { consumer } from '../../../src/consumer/api';
import { FixtureMailbox } from '../../../src/consumer/otp';

const mailbox = new FixtureMailbox();
let pool: Pool | undefined;
let localSecret: string | undefined;
async function handle(request: Request) {
  const {
    WEB_ORIGIN,
    ADMIN_ORIGIN,
    DATABASE_URL,
    SESSION_SECRET,
    APP_ENV,
    TRUSTED_CLIENT_IP_HEADER,
  } = process.env;
  const local = APP_ENV === 'development' || APP_ENV === 'test';
  const secret = SESSION_SECRET ?? (local ? (localSecret ??= randomBytes(32).toString('hex')) : undefined);
  if (
    !WEB_ORIGIN ||
    WEB_ORIGIN === ADMIN_ORIGIN ||
    !DATABASE_URL ||
    !secret ||
    secret.length < 32
  ) {
    return new Response(null, { status: 503 });
  }
  pool ??= new Pool({ connectionString: DATABASE_URL });
  return consumer(
    request,
    pool,
    {
      webOrigin: WEB_ORIGIN,
      secret,
      environment: APP_ENV ?? '',
      delivery: mailbox,
    },
    TRUSTED_CLIENT_IP_HEADER
      ? (request.headers.get(TRUSTED_CLIENT_IP_HEADER) ?? undefined)
      : undefined,
  );
}
export { handle as GET, handle as POST, handle as PATCH, handle as DELETE };
