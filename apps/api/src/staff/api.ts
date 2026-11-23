import type { Pool } from 'pg';
import { transaction } from '../consumer/common';
import { login, verify, authenticate, response, recoveryCodes } from './auth';
import { operate } from './operations';
import { allowed, policy, reads, type Action } from './policy';
import {
  Failure,
  audit,
  id,
  cookie,
  demand,
  headerCookie,
  mac,
  pending,
  reason,
  session,
  throttle,
  type Context,
  type Input,
} from './security';

export async function admin(req: Request, pool: Pool, c: Context) {
  try {
    const url = new URL(req.url),
      origin = req.headers.get('origin'),
      expected = new URL(c.origin);
    demand(
      expected.origin !== new URL(c.publicOrigin).origin &&
        (req.headers.get('host') ?? url.host) === expected.host &&
        url.pathname.startsWith('/staff/'),
      403,
      'Staff origin required',
    );
    demand(
      (!origin || origin === expected.origin) &&
        (req.method === 'GET' || origin === expected.origin),
      403,
      'Origin refused',
    );
    const action = url.pathname.slice(7);
    let b: Input = Object.fromEntries(url.searchParams);
    if (req.method === 'POST') {
      demand(
        req.headers.get('content-type')?.split(';')[0] === 'application/json',
        415,
      );
      const raw = await req.text();
      demand(raw.length <= 20000, 413);
      try {
        b = JSON.parse(raw);
      } catch {
        throw new Failure(400, 'Invalid JSON');
      }
      demand(b && typeof b === 'object' && !Array.isArray(b));
      if (action === 'login') return await login(pool, c, req, b);
      if (action === 'verify') return await verify(pool, c, req, b);
    }
    demand(Object.hasOwn(policy, action), 404, 'Unknown staff route');
    const op = action as Action;
    demand(
      req.method === (reads.has(op) ? 'GET' : 'POST'),
      405,
      'Method not allowed',
    );
    demand(cookie(req, session), 401, 'Staff session required');
    return await transaction(pool, async (db) => {
      const s = await authenticate(db, c, req);
      if (!allowed(op, s.role)) {
        await audit(db, c, req, s, op + '.denied');
        return response({ error: 'Permission denied' }, 403);
      }
      if (op === 'unmask' || op === 'requests/export')
        await throttle(db, c, op, s.id, 10);
      await db.query('SAVEPOINT staff_action');
      try {
        let value: unknown;
        if (op === 'logout') {
          await db.query(
            'UPDATE staff_sessions SET revoked_at=now() WHERE token_hash=$1',
            [mac(c, 'session', cookie(req, session))],
          );
          value = { signed_out: true };
        } else if (op === 'recovery/rotate')
          value = { recovery_codes: await recoveryCodes(db, c, s) };
        else value = await operate(db, s, c, op, b);
        const target =
          typeof b.id === 'string' &&
          /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(b.id)
            ? b.id
            : s.id;
        // Audit only fields explicitly approved for this operation. Never serialize requests or responses.
        const details: Input = {};
        if (op === 'legal') details.file_sha256 = b.file_sha256;
        if (op === 'flags/request' || op === 'flags/change')
          Object.assign(details, {
            key: b.key,
            environment: b.environment,
            value: b.value,
          });
        if (op === 'kb/transition')
          Object.assign(details, { entry: b.entry, state: b.state });
        if (op === 'staff/role') details.role = b.role;
        if (op === 'approvals')
          details.approval_id = (value as { id: string }).id;
        if (
          b.approval &&
          [
            'kb/transition',
            'flags/change',
            'requests/complete',
            'payments/live',
            'notifications/broadcast',
          ].includes(op)
        )
          details.approval_id = id(b.approval);
        await audit(
          db,
          c,
          req,
          s,
          op,
          target,
          b.reason ? reason(b.reason) : 'Staff operation',
          details,
        );
        return response(
          value,
          200,
          op === 'logout'
            ? [headerCookie(session, '', 0), headerCookie(pending, '', 0)]
            : [],
        );
      } catch (error) {
        if (!(error instanceof Failure)) throw error;
        await db.query('ROLLBACK TO SAVEPOINT staff_action');
        await audit(db, c, req, s, op + '.denied');
        return response({ error: error.message }, error.status);
      }
    });
  } catch (e) {
    return e instanceof Failure
      ? response({ error: e.message }, e.status)
      : response({ error: 'Staff service unavailable' }, 503);
  }
}
