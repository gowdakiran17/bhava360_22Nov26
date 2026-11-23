import { existsSync, globSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parse } from 'yaml';
import type { PoolClient } from 'pg';
import { demand, string } from './security';

type Rule = {
  id: string;
  path: string;
  conditions?: unknown;
  sources?: unknown;
  confidence?: string;
  traditions_differ?: unknown;
  exceptions?: unknown;
  user_text: Record<string, string>;
  remedy?: Remedy;
  options?: Record<string, Remedy>;
};
type Remedy = {
  type: string;
  optional: boolean;
  cost: string;
  user_text: Record<string, string>;
};
let entries: Map<string, Rule> | undefined;
export function knowledge() {
  if (entries) return entries;
  const root = [resolve('kb'), resolve('../../kb')].find((p) =>
    existsSync(resolve(p, 'SCHEMA.yaml')),
  );
  demand(root, 503, 'KB unavailable');
  const result = new Map<string, Rule>();
  const systems = [
    'vedic',
    'jaimini',
    'kp',
    'western',
    'numerology',
    'tarot',
    'palmistry',
    'lal-kitab',
    'face-reading',
    'vastu',
    'remedies',
  ];
  for (const system of systems)
    for (const file of globSync(system + '/**/*.yaml', { cwd: root })) {
      const row = parse(
        readFileSync(resolve(root, file), 'utf8'),
      ) as Rule | null;
      if (row?.id && (row.user_text || row.remedy))
        result.set(row.id, { ...row, path: file });
    }
  return (entries = result);
}
export function lintCopy(value: unknown) {
  const copy = string(value, 3000);
  demand(
    !/(\b(must|required|guaranteed|doomed|danger|unlucky|lucky|gems?|gemstones?|stones?|ratna|paid puja|yantra[- ]for[- ]sale|scores?)\b|\d\s*%|\d+\s*\/\s*\d+|अनिवार्य|अशुभ|रत्न|ಕಡ್ಡಾಯ|ಅಶುಭ|ರತ್ನ)/iu.test(
      copy,
    ),
    422,
    'Copy failed review',
  );
  return copy;
}
export function validateRemedy(v: Remedy) {
  demand(
    v &&
      v.optional === true &&
      v.cost === 'free' &&
      [
        'conduct',
        'service',
        'charity',
        'mantra',
        'mantra-japa',
        'fasting',
        'prayer',
        'reflection',
      ].includes(v.type),
    422,
    'Only free optional practices are eligible',
  );
  for (const lang of ['en', 'kn', 'hi']) lintCopy(v.user_text?.[lang]);
  return v;
}
export async function overlay(db: PoolClient, key: unknown) {
  const rule = knowledge().get(string(key));
  demand(rule, 404, 'Unknown entry');
  await db.query(
    "INSERT INTO rule_catalogue(rule_key,source_path,state) VALUES($1,$2,'draft') ON CONFLICT(rule_key) DO NOTHING",
    [rule.id, rule.path],
  );
  const row = (
    await db.query(
      'SELECT id,state,draft_patch FROM rule_catalogue WHERE rule_key=$1 FOR UPDATE',
      [rule.id],
    )
  ).rows[0];
  return {
    rule: { ...rule, ...row.draft_patch } as Rule,
    id: row.id as string,
    state: row.state as string,
  };
}
export async function approvedCopy(
  db: Pick<PoolClient, 'query'>,
  key: string,
  locale: string,
) {
  const row = (
    await db.query(
      "SELECT draft_patch FROM rule_catalogue WHERE rule_key=$1 AND state='approved'",
      [key],
    )
  ).rows[0];
  const rule = row && knowledge().get(key);
  const text = rule && (row.draft_patch.user_text ?? rule.user_text)?.[locale];
  return typeof text === 'string' ? { text } : null;
}
export function validateRule(rule: Rule) {
  demand(
    rule.conditions && Array.isArray(rule.sources) && rule.sources.length,
    422,
    'Missing conditions or sources',
  );
  for (const lang of ['en', 'kn', 'hi']) lintCopy(rule.user_text?.[lang]);
  if (rule.remedy) validateRemedy(rule.remedy);
}
export function fixtureSQL(column: string) {
  return `${column} IN (SELECT md5('fixture:user:'||n)::uuid FROM unnest(ARRAY['Asha','Ravi','Meera','Kabir','Dev']) n)`;
}
export const fixtureProfileSQL = (p: string) =>
  `(${fixtureSQL(p + '.user_id')} AND ${p}.id=md5('fixture:profile:'||${p}.display_name||${p}.time_precision::text)::uuid)`;
