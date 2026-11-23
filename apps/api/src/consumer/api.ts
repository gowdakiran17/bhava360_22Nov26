import type { Pool } from 'pg';
import { isIP } from 'node:net';
import { catalogue } from '@bhava360/i18n';
import {
  ApiError,
  invalid,
  locale,
  text,
  transaction,
  type Body,
} from './common';
import { otp, tokenHash, type Settings } from './otp';
import { consents, profiles } from './profiles';

const cookie = '__Host-bhava-consumer';
const attributes = '; Path=/; HttpOnly; Secure; SameSite=Strict';
function json(
  value: unknown,
  status = 200,
  headers: Record<string, string> = {},
) {
  return Response.json(value, {
    status,
    headers: { 'cache-control': 'no-store', ...headers },
  });
}

export async function consumer(
  req: Request,
  pool: Pool,
  settings: Settings,
  peerIp?: string,
) {
  let language = req.headers.get('accept-language')?.slice(0, 2) ?? 'en';
  try {
    const url = new URL(req.url);
    if (!url.pathname.startsWith('/consumer/'))
      throw new ApiError(404, 'missing');
    const expected = new URL(settings.webOrigin);
    const origin = req.headers.get('origin');
    if (
      (req.headers.get('host') ?? url.host) !== expected.host ||
      (origin && origin !== expected.origin) ||
      (req.method !== 'GET' && origin !== expected.origin)
    )
      throw new ApiError(403, 'denied');
    let body: Body = {};
    if (['POST', 'PATCH'].includes(req.method)) {
      try {
        const raw = await req.text();
        body = raw ? JSON.parse(raw) : {};
        if (!body || typeof body !== 'object' || Array.isArray(body))
          return invalid();
      } catch {
        return invalid();
      }
    }
    const segments = url.pathname.split('/').slice(2);
    const route = segments.join('/');
    if (
      req.method === 'POST' &&
      (route === 'otp/request' || route === 'otp/verify')
    ) {
      const token = await otp(
        pool,
        settings,
        route === 'otp/request' ? 'request' : 'verify',
        body,
        peerIp && isIP(peerIp) ? peerIp : 'shared-ingress',
      );
      if (!token) return json({ accepted: true }, 202);
      return json({ authenticated: true }, 200, {
        'set-cookie': cookie + '=' + token + attributes + '; Max-Age=2592000',
      });
    }
    if (req.method === 'GET' && route === 'places') {
      const query = text(url.searchParams.get('q'));
      const result = await pool.query(
        `SELECT id,city,name_kn,name_hi,latitude,longitude,iana_zone FROM places
        WHERE EXISTS (SELECT FROM unnest(aliases || ARRAY[city,name_kn,name_hi]) name
        WHERE starts_with(lower(name),lower($1))) ORDER BY city LIMIT 20`,
        [query],
      );
      return json(result.rows);
    }
    const token = req.headers
      .get('cookie')
      ?.split(/;\s*/)
      .find((s) => s.startsWith(cookie + '='))
      ?.slice(cookie.length + 1);
    if (!token || !/^[\w-]{43}$/.test(token)) throw new ApiError(401, 'signIn');
    return await transaction(pool, async (db) => {
      const session = (
        await db.query(
          `SELECT s.id,s.user_id,s.locale,s.active_profile_id FROM users u JOIN sessions s ON u.id=s.user_id
        WHERE s.token_hash=$1 AND s.expires_at>now() AND s.revoked_at IS NULL AND u.deactivated_at IS NULL FOR UPDATE OF u,s`,
          [tokenHash(settings, token)],
        )
      ).rows[0];
      if (!session) throw new ApiError(401, 'signIn');
      language = session.locale;
      if (route === 'session' && ['GET', 'PATCH'].includes(req.method)) {
        if (req.method === 'PATCH') {
          session.locale = locale(body.locale);
          await db.query('UPDATE sessions SET locale=$1 WHERE id=$2', [
            session.locale,
            session.id,
          ]);
        }
        return json({
          locale: session.locale,
          active_profile_id: session.active_profile_id,
        });
      }
      if (req.method === 'POST' && ['logout', 'logout-all'].includes(route)) {
        if (route === 'logout-all')
          await db.query(
            'UPDATE sessions SET revoked_at=now() WHERE user_id=$1',
            [session.user_id],
          );
        else
          await db.query('UPDATE sessions SET revoked_at=now() WHERE id=$1', [
            session.id,
          ]);
        return json({}, 200, {
          'set-cookie': cookie + '=' + attributes + '; Max-Age=0',
        });
      }
      if (route === 'consents')
        return json(await consents(db, session.user_id, req.method, body));
      if (segments[0] === 'profiles') {
        const switching =
          segments.length === 3 &&
          segments[2] === 'switch' &&
          req.method === 'POST';
        if (segments.length <= 2 || switching)
          return json(
            await profiles(
              db,
              session.user_id,
              session.id,
              switching ? 'switch' : req.method,
              segments[1],
              body,
            ),
          );
      }
      throw new ApiError(404, 'missing');
    });
  } catch (error) {
    const failure =
      error instanceof ApiError ? error : new ApiError(503, 'unavailable');
    return json(
      { error: failure.key, message: catalogue(language)[failure.key] },
      failure.status,
    );
  }
}
