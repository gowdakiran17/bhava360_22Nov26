import { Pool } from 'pg';
import { isIP } from 'node:net';
import { admin } from '../../../src/staff/api';

let pool: Pool | undefined;
async function handle(req: Request) {
  const {
    ADMIN_ORIGIN,
    WEB_ORIGIN,
    DATABASE_URL,
    ADMIN_SESSION_SECRET,
    SESSION_SECRET,
    APP_ENV,
    TRUSTED_CLIENT_IP_HEADER,
    ADMIN_TRUSTED_COUNTRY_HEADER,
  } = process.env;
  if (
    !ADMIN_ORIGIN ||
    !WEB_ORIGIN ||
    !DATABASE_URL ||
    !ADMIN_SESSION_SECRET ||
    ADMIN_SESSION_SECRET.length < 32 ||
    ADMIN_SESSION_SECRET === SESSION_SECRET
  )
    return new Response(null, { status: 503 });
  pool ??= new Pool({ connectionString: DATABASE_URL });
  const ip = TRUSTED_CLIENT_IP_HEADER
    ? req.headers.get(TRUSTED_CLIENT_IP_HEADER)
    : null;
  return admin(req, pool, {
    origin: ADMIN_ORIGIN,
    publicOrigin: WEB_ORIGIN,
    secret: ADMIN_SESSION_SECRET,
    environment: APP_ENV ?? '',
    ip: ip && isIP(ip) ? ip : undefined,
    country: ADMIN_TRUSTED_COUNTRY_HEADER
      ? (req.headers.get(ADMIN_TRUSTED_COUNTRY_HEADER) ?? undefined)
      : undefined,
  });
}
export { handle as GET, handle as POST };
