import { issueFixtureCode, FixtureMailbox } from '../consumer/otp';
import type { PoolClient } from 'pg';
import { content, consumeApproval, scopedLocale } from './content';
import { fixtureProfileSQL, fixtureSQL, knowledge, lintCopy } from './kb';
import { roles, type Action } from './policy';
import {
  demand,
  id,
  string,
  reason,
  hashPassword,
  token,
  type Staff,
  type Context,
  type Input,
} from './security';

export const settingNames = [
  'AI_PROVIDER',
  'GEMINI_API_KEY',
  'OPENAI_API_KEY',
  'RAZORPAY_KEY_ID',
  'RAZORPAY_KEY_SECRET',
  'RESEND_API_KEY',
  'SWEPH_PATH',
  'OTP_PROVIDER',
  'ADMIN_BOOTSTRAP_OWNER_EMAIL',
] as const;
const approvalOps = [
  'flags/change',
  'kb/revert',
  'requests/complete',
  'notifications/broadcast',
  'payments/live',
];
const approvers = ['owner', 'admin'];
export async function operate(
  db: PoolClient,
  s: Staff,
  c: Context,
  op: Action,
  b: Input,
) {
  const rows = async (sql: string, args: unknown[] = []) =>
    (await db.query(sql, args)).rows;
  const first = async (sql: string, args: unknown[] = []) => {
    const row = (await rows(sql, args))[0];
    demand(row, 404, 'Unknown record');
    return row;
  };
  const dev = ['test', 'development'].includes(c.environment);
  const tester = s.role === 'tester',
    native = s.role === 'native-language reviewer',
    support = s.role === 'support';
  switch (op) {
    case 'dashboard': {
      const pending = await rows(
        "SELECT locale,count(*)::int AS count FROM native_review_items WHERE state='pending' AND locale IN ('kn','hi') AND ($1::text IS NULL OR locale=$1) GROUP BY locale",
        [native ? (s.assigned_locale ?? 'none') : null],
      );
      if (native) return { native_pending: pending };
      if (tester) return { fixture_benchmark: 'not_built' };
      if (support)
        return first(
          "SELECT count(*)::int AS open_requests FROM data_requests WHERE status<>'completed'",
        );
      const counts = await rows(
        'SELECT state,count(*)::int AS count FROM rule_catalogue GROUP BY state',
      );
      const result = {
        native_pending: pending,
        kb_states: counts,
        unindexed_drafts:
          knowledge().size - counts.reduce((n, r) => n + r.count, 0),
      };
      if (s.role === 'astrologer-reviewer') return result;
      return {
        ...result,
        ...(await first(
          "SELECT (SELECT count(*)::int FROM data_requests WHERE status<>'completed') AS open_requests,(SELECT count(*)::int FROM report_jobs WHERE status='failed') AS failed_jobs",
        )),
        ai_guardrail_hits: 'not_recorded',
        fixture_benchmark: 'not_built',
        flag_drift: 'not_built',
      };
    }
    case 'users':
      return rows(
        `SELECT u.id,p.id AS profile_id,'masked' AS identity, u.deactivated_at IS NOT NULL AS deactivated
      FROM users u LEFT JOIN profiles p ON p.user_id=u.id WHERE $1::uuid IS NULL OR u.id=$1 OR p.id=$1 ORDER BY u.id,p.id LIMIT 100`,
        [b.id ? id(b.id) : null],
      );
    case 'unmask': {
      reason(b.reason);
      const field = string(b.field);
      if (field === 'birth_instant')
        return first('SELECT birth_instant FROM profiles WHERE id=$1', [
          id(b.id),
        ]);
      demand(['phone', 'email'].includes(field));
      await first('SELECT id FROM users WHERE id=$1', [id(b.id)]);
      return { field, status: 'not_retained_in_plaintext' };
    }
    case 'testers': {
      const fixture = id(b.fixture_user_id);
      await first('SELECT id FROM users WHERE id=$1 AND ' + fixtureSQL('id'), [
        fixture,
      ]);
      const email = string(b.email).toLowerCase();
      demand(/^[a-z0-9.+-]+@example\.test$/.test(email));
      if (b.disable === true) {
        await first(
          "UPDATE staff_users SET disabled_at=now() WHERE email=$1 AND role='tester' AND fixture_user_id=$2 RETURNING id",
          [email, fixture],
        );
        return { disabled: true };
      }
      const password = token();
      await db.query(
        "INSERT INTO staff_users(email,role,password_hash,fixture_user_id) VALUES($1,'tester',$2,$3)",
        [email, await hashPassword(password), fixture],
      );
      return { email, initial_password: password };
    }
    case 'fixtures/code': {
      demand(dev, 403);
      const profile = await first(
        `SELECT p.user_id,p.display_name FROM profiles p WHERE p.id=$1 AND ${fixtureProfileSQL('p')} AND deleted_at IS NULL`,
        [id(b.id)],
      );
      if (tester) demand(profile.user_id === s.fixture_user_id, 403);
      const secret = process.env.SESSION_SECRET;
      demand(
        secret && secret.length >= 32,
        503,
        'Configure shared development consumer signing key',
      );
      const code = await issueFixtureCode(
        db,
        {
          environment: c.environment,
          secret,
          webOrigin: c.publicOrigin,
          delivery: new FixtureMailbox(),
        },
        {
          channel: 'email',
          identifier: profile.display_name.toLowerCase() + '@example.test',
        },
        c.ip ?? 'local',
      );
      demand(code, 404);
      return { code, fixture_only: true };
    }
    case 'fixtures': {
      if (tester) demand(dev, 403);
      return rows(
        `SELECT p.id,p.display_name,p.time_precision FROM profiles p WHERE ${fixtureProfileSQL('p')} AND p.deleted_at IS NULL ORDER BY p.display_name`,
      );
    }
    case 'inspector': {
      const p = await first(
        `SELECT id,time_precision,${fixtureProfileSQL('p')} AS fixture FROM profiles p WHERE id=$1 AND deleted_at IS NULL`,
        [id(b.id)],
      );
      if (p.fixture) demand(!support, 403);
      if (!p.fixture) {
        demand(!tester, 403);
        await db.query(
          'INSERT INTO inspector_access_log(actor_id,opaque_profile_id,reason) VALUES($1,$2,$3)',
          [s.id, p.id, reason(b.reason)],
        );
      }
      return {
        user_saw: null,
        staff_evidence: {
          engine: 'not_built',
          rule_chains: [],
          matching_points: null,
          numerology_totals: null,
          dasha_transit: null,
          kp_sublords: null,
          check_tool_chains: [],
          lagna_facts:
            p.time_precision === 'unknown' ? 'withheld' : 'not_built',
        },
      };
    }
    case 'ai': {
      if (support) reason(b.reason);
      return rows(
        `SELECT g.id,g.model,g.provider,g.template_version AS prompt_reference,g.created_at,NULL AS prompt,NULL AS output,'not_recorded' AS guardrail_hits,
        NULL::boolean AS ai_marked FROM ai_generations g JOIN profiles p ON p.id=g.profile_id
        WHERE NOT $1 OR ${fixtureProfileSQL('p')} ORDER BY g.created_at DESC LIMIT 100`,
        [tester],
      );
    }
    case 'kb':
    case 'kb/edit':
    case 'kb/transition':
    case 'native/queue':
    case 'native/review':
    case 'copy':
    case 'remedies':
    case 'remedies/edit':
    case 'remedies/review':
      return content(db, s, op, b);
    case 'legal':
      demand(
        Object.keys(b).length === 1 &&
          /^[a-f0-9]{64}$/.test(string(b.file_sha256)),
      );
      return { status: 'human_file_hook', file_sha256: b.file_sha256 };
    case 'flags': {
      const env = string(b.environment ?? c.environment);
      if (tester) demand(env !== 'production' && dev, 403);
      return rows(
        'SELECT key,value FROM feature_flags WHERE environment=$1 ORDER BY key',
        [env === 'test' ? 'development' : env],
      );
    }
    case 'flags/request': {
      demand(
        dev && ['development', 'staging'].includes(String(b.environment)),
        403,
      );
      const flag = await first(
        'SELECT value FROM feature_flags WHERE key=$1 AND environment=$2',
        [string(b.key), b.environment],
      );
      demand(
        typeof flag.value === typeof b.value &&
          (typeof b.value === 'boolean' ||
            (typeof b.value === 'string' && /^[a-zA-Z-]{1,30}$/.test(b.value))),
      );
      return { requested: b.key, status: 'recorded' };
    }
    case 'flags/change': {
      const env = string(b.environment),
        key = string(b.key);
      const flag = await first(
        'SELECT value FROM feature_flags WHERE environment=$1 AND key=$2 FOR UPDATE',
        [env, key],
      );
      demand(
        typeof flag.value === typeof b.value &&
          (typeof b.value === 'boolean' || typeof b.value === 'string'),
      );
      if (typeof b.value === 'string') {
        const values: Record<string, string[]> = {
          'matching.default': ['Ashtakoota', 'Porutham'],
          'vedic.houses': ['whole-sign'],
          'western.houses': ['Placidus'],
        };
        demand(values[key]?.includes(b.value));
      }
      if (env === 'production')
        await consumeApproval(
          db,
          op,
          { environment: env, key, value: b.value },
          b.approval,
        );
      await db.query(
        'UPDATE feature_flags SET value=$3::jsonb WHERE environment=$1 AND key=$2',
        [env, key, JSON.stringify(b.value)],
      );
      return { key, environment: env, value: b.value };
    }
    case 'approvals': {
      const operation = string(b.operation);
      demand(
        approvalOps.includes(operation) &&
          b.parameters &&
          typeof b.parameters === 'object' &&
          !Array.isArray(b.parameters),
      );
      const parameters = b.parameters as Input;
      const fields: Record<string, string[]> = {
        'kb/revert': ['entry', 'state'],
        'flags/change': ['environment', 'key', 'value'],
        'payments/live': ['mode'],
        'notifications/broadcast': ['id'],
        'requests/complete': ['id'],
      };
      demand(
        Object.keys(parameters).sort().join() ===
          fields[operation].sort().join(),
      );
      for (const field of fields[operation]) {
        if (field === 'id') id(parameters.id);
        else if (field === 'value')
          demand(
            typeof parameters.value === 'boolean' ||
              ['whole-sign', 'Placidus', 'Ashtakoota', 'Porutham'].includes(
                String(parameters.value),
              ),
          );
        else if (field === 'entry')
          demand(knowledge().has(string(parameters.entry)));
        else if (field === 'state')
          demand(['draft', 'validated'].includes(String(parameters.state)));
        else if (field === 'environment')
          demand(parameters.environment === 'production');
        else if (field === 'mode') demand(parameters.mode === 'live');
        else if (field === 'key')
          await first('SELECT id FROM feature_flags WHERE key=$1 LIMIT 1', [
            string(parameters.key),
          ]);
      }
      return first(
        "INSERT INTO staff_approvals(owner_id,operation,parameters,expires_at) VALUES($1,$2,$3,now()+interval '1 day') RETURNING id,operation,expires_at",
        [s.id, operation, b.parameters],
      );
    }
    case 'jobs':
    case 'payments': {
      const payment = op === 'payments';
      if (payment && !dev) return { mode: 'test', items: [] };
      const table = payment ? 'payments' : 'report_jobs';
      return rows(
        `SELECT t.id,t.status FROM ${table} t JOIN report_orders o ON o.id=t.order_id JOIN profiles p ON p.id=o.profile_id
        WHERE ${payment ? "t.mode='test' AND" : ''} (NOT $1 OR ${fixtureProfileSQL('p')}) AND (NOT $2 OR p.user_id=$3) ORDER BY t.id LIMIT 100`,
        [payment || tester, payment && tester, s.fixture_user_id],
      );
    }
    case 'jobs/retry': {
      if (tester) demand(dev, 403);
      return first(
        `UPDATE report_jobs j SET status='queued',lease_until=NULL,available_at=now() FROM report_orders o JOIN profiles p ON o.profile_id=p.id
        WHERE j.order_id=o.id AND j.id=$1 AND j.status='failed' AND (CASE WHEN ${fixtureProfileSQL('p')} THEN $2 ELSE NOT $3 END) RETURNING j.id,j.status`,
        [id(b.id), dev, tester],
      );
    }
    case 'payments/test':
      demand(dev, 403);
      return { mode: 'test', capture: false, status: 'provider_not_built' };
    case 'payments/live':
      await consumeApproval(db, op, { mode: 'live' }, b.approval);
      return { capture: false, status: 'not_built' };
    case 'notifications': {
      if (support)
        return rows(
          "SELECT template_id,created_at,'test_only' AS status FROM notification_test_log ORDER BY created_at DESC LIMIT 100",
        );
      if (native) {
        const lang = scopedLocale(s, s.assigned_locale);
        return rows(
          'SELECT template_key,translations->>$1 AS text FROM notifications',
          [lang],
        );
      }
      return rows(
        'SELECT id,template_key,translations FROM notifications ORDER BY template_key',
      );
    }
    case 'notifications/edit': {
      const key = string(b.key, 80),
        locale = scopedLocale(s, b.locale),
        text = lintCopy(b.text);
      demand(/^[a-z][a-z0-9_.-]*$/.test(key));
      if (locale !== 'en')
        return first(
          "INSERT INTO native_review_items(i18n_key,locale,state,proposal) VALUES($1,$2,'pending',$3) RETURNING id,state",
          ['notification:' + key, locale, text],
        );
      return first(
        `INSERT INTO notifications(template_key,translations) VALUES($1,jsonb_build_object($2::text,$3::text))
        ON CONFLICT(template_key) DO UPDATE SET translations=notifications.translations||excluded.translations RETURNING id,translations`,
        [key, locale, text],
      );
    }
    case 'notifications/test': {
      demand(dev, 403);
      const n = await first(
        'SELECT id,translations FROM notifications WHERE id=$1',
        [id(b.id)],
      );
      for (const lang of ['en', 'kn', 'hi']) lintCopy(n.translations[lang]);
      return first(
        "INSERT INTO notification_test_log(template_id,staff_id) VALUES($1,$2) RETURNING id,'test_only' AS status",
        [n.id, s.id],
      );
    }
    case 'notifications/broadcast':
      await consumeApproval(db, op, { id: id(b.id) }, b.approval);
      return { sent: false, status: 'sender_not_built' };
    case 'audit': {
      return rows(
        `SELECT action,opaque_target_id,actor_id,role,reason,created_at FROM audit_log WHERE ($1 OR actor_id=$2)
        AND ($3::text IS NULL OR action=$3) ORDER BY created_at DESC LIMIT 100`,
        [approvers.includes(s.role), s.id, b.action ?? null],
      );
    }
    case 'settings':
      return settingNames.map((name) => ({
        name,
        present: Boolean(process.env[name]),
      }));
    case 'staff/role': {
      const role = b.role;
      demand(roles.some((r) => r === role));
      if (role === 'owner') demand(s.role === 'owner', 403);
      const locale =
        role === 'native-language reviewer' ? string(b.locale) : null;
      demand(!locale || ['kn', 'hi'].includes(locale));
      if (!b.id) {
        demand(role !== 'tester', 400, 'Use fixture-bound tester provisioning');
        const password = token();
        const email = string(b.email, 254).toLowerCase();
        demand(/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email));
        const added = await first(
          'INSERT INTO staff_users(email,role,password_hash,assigned_locale) VALUES($1,$2,$3,$4) RETURNING id',
          [email, role, await hashPassword(password), locale],
        );
        return { ...added, initial_password: password };
      }
      const target = await first(
        'SELECT id,role,password_hash,fixture_user_id FROM staff_users WHERE id=$1 FOR UPDATE',
        [id(b.id)],
      );
      if (role === 'tester')
        demand(target.fixture_user_id, 400, 'Fixture binding required');
      if (target.role === 'owner' || role === 'owner')
        demand(s.role === 'owner' && target.id !== s.id, 403);
      const password = target.password_hash ? null : token();
      await db.query(
        'UPDATE staff_users SET role=$2,assigned_locale=$3,password_hash=coalesce(password_hash,$4) WHERE id=$1',
        [
          target.id,
          role,
          locale,
          password ? await hashPassword(password) : null,
        ],
      );
      await db.query(
        'UPDATE staff_sessions SET revoked_at=now() WHERE staff_id=$1',
        [target.id],
      );
      await db.query('DELETE FROM staff_login_challenges WHERE staff_id=$1', [
        target.id,
      ]);
      return {
        id: target.id,
        role,
        ...(password ? { initial_password: password } : {}),
      };
    }
    case 'requests/list':
      return rows(
        'SELECT id,kind,status,due_at FROM data_requests ORDER BY due_at LIMIT 100',
      );
    case 'requests/intake': {
      demand(['export', 'delete'].includes(String(b.kind)));
      const user = id(b.user_id);
      await first('SELECT id FROM users WHERE id=$1 FOR UPDATE', [user]);
      if (b.kind === 'delete')
        await db.query(
          "UPDATE users SET deactivated_at=coalesce(deactivated_at,now()),delete_by=coalesce(delete_by,now()+interval '30 days') WHERE id=$1",
          [user],
        );
      return first(
        "INSERT INTO data_requests(user_id,kind,status,due_at) VALUES($1,$2,'pending',now()+interval '30 days') RETURNING id,status",
        [user, b.kind],
      );
    }
    case 'requests/export': {
      const q = await first(
        "SELECT user_id FROM data_requests WHERE id=$1 AND kind='export'",
        [id(b.id)],
      );
      return {
        profiles: await rows(
          'SELECT id,display_name,relation,time_precision FROM profiles WHERE user_id=$1 AND deleted_at IS NULL',
          [q.user_id],
        ),
        consents: await rows(
          'SELECT purpose,version,granted,recorded_at FROM consents WHERE user_id=$1',
          [q.user_id],
        ),
      };
    }
    case 'requests/complete': {
      const request = id(b.id);
      if (s.role !== 'owner')
        await consumeApproval(db, op, { id: request }, b.approval);
      const q = await first(
        "SELECT user_id FROM data_requests WHERE id=$1 AND kind='delete' AND status='pending' FOR UPDATE",
        [request],
      );
      await first(
        'DELETE FROM users WHERE id=$1 AND deactivated_at IS NOT NULL RETURNING id',
        [q.user_id],
      );
      return { completed: true };
    }
    default:
      throw new Error('Unhandled staff operation');
  }
}
