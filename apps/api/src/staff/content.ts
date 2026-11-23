import { catalogue } from '@bhava360/i18n';
import type { PoolClient } from 'pg';
import {
  overlay,
  knowledge,
  lintCopy,
  validateRule,
  validateRemedy,
} from './kb';
import { demand, id, string, type Staff, type Input } from './security';
import type { Action } from './policy';

export function scopedLocale(s: Staff, language: unknown) {
  const locale = string(language, 2);
  demand(['en', 'kn', 'hi'].includes(locale));
  demand(
    s.role !== 'native-language reviewer' ||
      (locale !== 'en' && locale === s.assigned_locale),
    403,
    'Outside locale assignment',
  );
  return locale;
}
export async function consumeApproval(
  db: PoolClient,
  op: string,
  parameters: Input,
  approval: unknown,
) {
  demand(typeof approval === 'string', 403, 'Specific owner approval required');
  const used = await db.query(
    `UPDATE staff_approvals SET used_at=now() WHERE id=$1 AND operation=$2 AND parameters=$3::jsonb
    AND expires_at>now() AND used_at IS NULL AND EXISTS(SELECT FROM staff_users u WHERE u.id=owner_id AND u.role='owner' AND u.disabled_at IS NULL AND (u.expires_at IS NULL OR u.expires_at>now()))
    RETURNING id`,
    [id(approval), op, JSON.stringify(parameters)],
  );
  demand(used.rowCount, 403, 'Specific owner approval required');
}
export async function content(db: PoolClient, s: Staff, op: Action, b: Input) {
  if (op === 'remedies') {
    const result = [];
    const patches = new Map(
      (
        await db.query(
          "SELECT rule_key,draft_patch FROM rule_catalogue WHERE draft_patch <> '{}'::jsonb",
        )
      ).rows.map((r) => [r.rule_key, r.draft_patch]),
    );
    for (const base of knowledge().values()) {
      const rule = { ...base, ...(patches.get(base.id) ?? {}) } as typeof base;
      for (const [key, value] of Object.entries({
        main: rule.remedy,
        ...rule.options,
      })) {
        if (!value) continue;
        try {
          validateRemedy(value);
        } catch {
          continue;
        }
        result.push(
          s.role === 'native-language reviewer'
            ? {
                entry: rule.id,
                key,
                text: value.user_text[s.assigned_locale ?? ''],
              }
            : { entry: rule.id, key, remedy: value },
        );
      }
    }
    return result;
  }
  if (op === 'remedies/review') {
    const { rule: entry } = await overlay(db, b.entry);
    const key = string(b.option ?? 'main');
    const remedy = key === 'main' ? entry.remedy : entry.options?.[key];
    demand(remedy, 404, 'Unknown remedy');
    validateRemedy(remedy);
    return { reviewed: true };
  }
  if (op === 'remedies/edit') {
    const entry = await overlay(db, b.entry);
    demand(entry.state === 'draft', 409, 'Draft required');
    const key = string(b.option ?? 'main');
    const old = key === 'main' ? entry.rule.remedy : entry.rule.options?.[key];
    demand(old, 404, 'Unknown remedy');
    const locale = scopedLocale(s, b.locale),
      proposal = lintCopy(b.text);
    const revised = validateRemedy({
      ...old,
      user_text: { ...old.user_text, [locale]: proposal },
    });
    if (locale !== 'en')
      return (
        await db.query(
          "INSERT INTO native_review_items(entry_id,locale,state,proposal,remedy_option) VALUES($1,$2,'pending',$3,$4) RETURNING id,state",
          [entry.id, locale, proposal, key],
        )
      ).rows[0];
    const patch =
      key === 'main'
        ? { remedy: revised }
        : { options: { ...entry.rule.options, [key]: revised } };
    await db.query(
      'UPDATE rule_catalogue SET draft_patch=draft_patch || $2::jsonb WHERE id=$1',
      [entry.id, JSON.stringify(patch)],
    );
    return { state: 'draft' };
  }
  if (op === 'native/queue')
    return (
      await db.query(
        `SELECT id,entry_id,i18n_key,locale,state,proposal,remedy_option FROM native_review_items
    WHERE locale IN ('kn','hi') AND ($1::text IS NULL OR locale=$1) ORDER BY id`,
        [
          s.role === 'native-language reviewer'
            ? (s.assigned_locale ?? 'unassigned')
            : null,
        ],
      )
    ).rows;
  if (op === 'copy') {
    const locale = scopedLocale(s, b.locale),
      proposal = lintCopy(b.text);
    demand(Boolean(b.entry) !== Boolean(b.key));
    const entry = b.entry ? await overlay(db, b.entry) : undefined;
    if (!entry)
      demand(
        Object.hasOwn(catalogue('en'), string(b.key)),
        400,
        'Unknown UI key',
      );
    demand(!entry || entry.state === 'draft', 409, 'Draft required');
    if (entry && locale === 'en')
      await db.query(
        'UPDATE rule_catalogue SET draft_patch=draft_patch || $2::jsonb WHERE id=$1',
        [
          entry.id,
          JSON.stringify({
            user_text: { ...entry.rule.user_text, en: proposal },
          }),
        ],
      );
    return (
      await db.query(
        `INSERT INTO native_review_items(entry_id,i18n_key,locale,state,proposal)
      VALUES($1,$2,$3,$5,$4) RETURNING id,state`,
        [
          entry?.id ?? null,
          entry ? null : b.key,
          locale,
          proposal,
          locale === 'en' ? 'approved' : 'pending',
        ],
      )
    ).rows[0];
  }
  if (op === 'native/review') {
    const item = (
      await db.query(
        'SELECT * FROM native_review_items WHERE id=$1 FOR UPDATE',
        [id(b.id)],
      )
    ).rows[0];
    demand(item, 404, 'Unknown item');
    scopedLocale(s, item.locale);
    demand(
      ['kn', 'hi'].includes(item.locale) &&
        item.state === 'pending' &&
        ['approved', 'rejected'].includes(String(b.state)),
    );
    if (item.i18n_key?.startsWith('notification:') && b.state === 'approved') {
      await db.query(
        `INSERT INTO notifications(template_key,translations) VALUES($1,jsonb_build_object($2::text,$3::text))
        ON CONFLICT(template_key) DO UPDATE SET translations=notifications.translations||excluded.translations`,
        [item.i18n_key.slice(13), item.locale, lintCopy(item.proposal)],
      );
    }
    if (item.entry_id && b.state === 'approved') {
      const key = (
        await db.query('SELECT rule_key FROM rule_catalogue WHERE id=$1', [
          item.entry_id,
        ])
      ).rows[0].rule_key;
      const entry = await overlay(db, key);
      demand(entry.state === 'draft', 409, 'Draft required');
      const text = lintCopy(item.proposal);
      let patch: Input = {
        user_text: { ...entry.rule.user_text, [item.locale]: text },
      };
      if (item.remedy_option) {
        const k = item.remedy_option,
          old = k === 'main' ? entry.rule.remedy : entry.rule.options?.[k];
        demand(old, 404);
        const revised = validateRemedy({
          ...old,
          user_text: { ...old.user_text, [item.locale]: text },
        });
        patch =
          k === 'main'
            ? { remedy: revised }
            : { options: { ...entry.rule.options, [k]: revised } };
      }
      await db.query(
        'UPDATE rule_catalogue SET draft_patch=draft_patch || $2::jsonb WHERE id=$1',
        [entry.id, JSON.stringify(patch)],
      );
    }
    await db.query(
      'UPDATE native_review_items SET state=$2,reviewer_id=$3 WHERE id=$1',
      [item.id, b.state, s.id],
    );
    return { state: b.state };
  }
  if (op === 'kb' && !b.entry)
    return [...knowledge().keys()]
      .filter((k) => k.startsWith(String(b.prefix ?? '')))
      .slice(0, 200);
  const entry = await overlay(db, b.entry);
  if (op === 'kb') {
    if (s.role === 'native-language reviewer')
      return {
        entry: entry.rule.id,
        text: entry.rule.user_text?.[s.assigned_locale ?? ''] ?? null,
      };
    return { ...entry.rule, approval: entry.state };
  }
  if (op === 'kb/edit') {
    demand(entry.state === 'draft', 409, 'Draft required');
    demand(
      b.conditions &&
        typeof b.conditions === 'object' &&
        !Array.isArray(b.conditions) &&
        Array.isArray(b.sources) &&
        b.sources.length,
    );
    await db.query(
      'UPDATE rule_catalogue SET draft_patch=draft_patch || $2::jsonb WHERE id=$1',
      [
        entry.id,
        JSON.stringify({ conditions: b.conditions, sources: b.sources }),
      ],
    );
    return { state: 'draft' };
  }
  const next = string(b.state),
    current = entry.state;
  if (current === 'approved' && ['draft', 'validated'].includes(next)) {
    demand(['owner', 'admin'].includes(s.role), 403);
    if (s.role === 'admin')
      await consumeApproval(
        db,
        'kb/revert',
        { entry: b.entry, state: next },
        b.approval,
      );
  } else {
    demand(
      (
        {
          draft: ['in_review'],
          in_review: ['validated', 'draft'],
          validated: ['approved', 'draft'],
        } as Record<string, string[]>
      )[current]?.includes(next),
      409,
      'Invalid transition',
    );
    if (next === 'approved') demand(s.role === 'owner', 403);
  }
  if (next === 'approved' || next === 'validated') validateRule(entry.rule);
  const notes = next === 'draft' ? string(b.notes) : null;
  await db.query('UPDATE rule_catalogue SET state=$2 WHERE id=$1', [
    entry.id,
    next,
  ]);
  await db.query(
    'INSERT INTO kb_entry_reviews(entry_id,actor_id,from_state,to_state,notes) VALUES($1,$2,$3,$4,$5)',
    [entry.id, s.id, current, next, notes],
  );
  return { entry: b.entry, state: next };
}
