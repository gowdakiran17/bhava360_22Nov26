import { sql } from 'drizzle-orm';
import { bigint, pgTable, pgEnum, uuid, text, timestamp, date, time, integer, doublePrecision, boolean, jsonb, cidr, unique, index, check, foreignKey } from 'drizzle-orm/pg-core';

export const channel = pgEnum('identity_channel', ['phone', 'email']);
export const precision = pgEnum('birth_precision', ['known', 'approximate', 'unknown']);
export const environment = pgEnum('app_environment', ['development','staging','production']);
export const approval = pgEnum('approval_state', ['draft','in_review','validated','approved']);
export const role = pgEnum('staff_role', ['owner','admin','astrologer-reviewer','native-language reviewer','tester','support']);
export const request = pgEnum('data_request_kind', ['export','delete']);

export const users = pgTable('users', {
  id: uuid().primaryKey().defaultRandom(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
  deactivated_at: timestamp({ withTimezone: true }),
  delete_by: timestamp({ withTimezone: true }),
}, t => [
  check('delete_window', sql`(${t.deactivated_at} is null and ${t.delete_by} is null) or (${t.deactivated_at} is not null and ${t.delete_by} is not null and ${t.delete_by} between ${t.deactivated_at} and ${t.deactivated_at} + interval '30 days')`),
]);

export const places = pgTable('places', {
  id: uuid().primaryKey().defaultRandom(),
  city: text().notNull().unique(),
  aliases: text().array().notNull(),
  name_kn: text().notNull(),
  name_hi: text().notNull(),
  native_review: text().notNull(),
  latitude: doublePrecision().notNull(),
  longitude: doublePrecision().notNull(),
  iana_zone: text().notNull(),
}, t => [
  check('city_coordinates', sql`${t.latitude} between -90 and 90 and ${t.longitude} between -180 and 180`), index().using('gin', t.aliases),
]);

export const identities = pgTable('identities', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  kind: channel().notNull(),
  identifier_digest: text().notNull(),
}, t => [
  index().on(t.user_id),
  unique().on(t.kind, t.identifier_digest),
]);

export const otp_challenges = pgTable('otp_challenges', {
  id: uuid().primaryKey().defaultRandom(),
  identity_id: uuid().notNull().references(() => identities.id, { onDelete: 'cascade' }),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
  code_hash: text().notNull(),
  ip_digest: text().notNull(),
  expires_at: timestamp({ withTimezone: true }).notNull(),
  attempts: integer().notNull().default(0),
  consumed_at: timestamp({ withTimezone: true }),
}, t => [
  index().on(t.identity_id),
  check('attempts_nonnegative', sql`${t.attempts} >= 0`), index().on(t.expires_at),
]);

export const sessions = pgTable('sessions', {
  locale: text().notNull().default('en'),
  active_profile_id: uuid().references(() => profiles.id, { onDelete: 'set null' }),
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  token_hash: text().notNull().unique(),
  expires_at: timestamp({ withTimezone: true }).notNull(),
  revoked_at: timestamp({ withTimezone: true }),
}, t => [
  index().on(t.user_id),
]);

export const consents = pgTable('consents', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  purpose: text().notNull(),
  version: text().notNull(),
  required: boolean().notNull(),
  granted: boolean().notNull(),
  recorded_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.user_id),
]);

export const profiles = pgTable('profiles', {
  deleted_at: timestamp({ withTimezone: true }),
  adult_permission: boolean().notNull().default(false),
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  display_name: text().notNull(),
  birth_instant: timestamp({ withTimezone: true }).notNull(),
  local_date: date().notNull(),
  local_time: time().notNull(),
  iana_zone: text().notNull(),
  place_id: uuid().notNull().references(() => places.id, { onDelete: 'restrict' }),
  time_precision: precision().notNull(),
  relation: text().notNull(),
  gender: text(),
}, t => [
  index().on(t.user_id),
  index().on(t.place_id),
  check('unknown_noon', sql`${t.time_precision} <> 'unknown' or ${t.local_time} = time '12:00'`), unique().on(t.user_id, t.id),
]);

export const computation_cache = pgTable('computation_cache', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  convention: text().notNull(),
  module: text().notNull(),
  cache_key: text().notNull().unique(),
  facts: jsonb().notNull(),
  expires_at: timestamp({ withTimezone: true }).notNull(),
}, t => [
  index().on(t.profile_id),
]);

export const readings = pgTable('readings', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  module: text().notNull(),
  period: text().notNull(),
  language: text().notNull(),
  fact_hash: text().notNull(),
  body: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.profile_id),
]);

export const ai_generations = pgTable('ai_generations', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  provider: text().notNull(),
  model: text().notNull(),
  template_version: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.profile_id),
]);

export const ask_threads = pgTable('ask_threads', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.profile_id),
]);

export const ask_messages = pgTable('ask_messages', {
  id: uuid().primaryKey().defaultRandom(),
  thread_id: uuid().notNull().references(() => ask_threads.id, { onDelete: 'cascade' }),
  speaker: text().notNull(),
  body: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.thread_id),
]);

export const matches = pgTable('matches', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  first_profile_id: uuid().notNull(),
  second_profile_id: uuid().notNull(),
  method: text().notNull(),
}, t => [
  index().on(t.user_id),
  foreignKey({ columns: [t.user_id, t.first_profile_id], foreignColumns: [profiles.user_id, profiles.id] }).onDelete('cascade'),
  foreignKey({ columns: [t.user_id, t.second_profile_id], foreignColumns: [profiles.user_id, profiles.id] }).onDelete('cascade'),
]);

export const muhurta_searches = pgTable('muhurta_searches', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  activity: text().notNull(),
  start_date: date().notNull(),
  end_date: date().notNull(),
  place_id: uuid().notNull().references(() => places.id, { onDelete: 'restrict' }),
}, t => [
  index().on(t.profile_id),
  index().on(t.place_id),
  check('search_date_range', sql`${t.end_date} >= ${t.start_date}`),
]);

export const tarot_draws = pgTable('tarot_draws', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  spread: text().notNull(),
  card_ids: text().array().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.profile_id),
]);

export const tarot_journal = pgTable('tarot_journal', {
  id: uuid().primaryKey().defaultRandom(),
  draw_id: uuid().notNull().references(() => tarot_draws.id, { onDelete: 'cascade' }),
  note: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.draw_id),
]);

export const numerology_names = pgTable('numerology_names', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  candidate_name: text().notNull(),
  system: text().notNull(),
}, t => [
  index().on(t.profile_id),
]);

export const palm_sessions = pgTable('palm_sessions', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  keep_opt_in: boolean().notNull().default(false),
  storage_pointer: text(),
  delete_at: timestamp({ withTimezone: true }),
}, t => [
  index().on(t.profile_id),
  check('opted_in_storage', sql`(${t.storage_pointer} is null and ${t.delete_at} is null) or (${t.keep_opt_in} and ${t.storage_pointer} is not null and ${t.delete_at} is not null)`),
]);

export const reports = pgTable('reports', {
  id: uuid().primaryKey().defaultRandom(),
  catalogue_key: text().notNull().unique(),
  price_minor: integer().notNull(),
  currency: text().notNull(),
}, t => [
  check('price_nonnegative', sql`${t.price_minor} >= 0`),
]);

export const report_orders = pgTable('report_orders', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  report_id: uuid().notNull().references(() => reports.id, { onDelete: 'restrict' }),
  status: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.profile_id),
  index().on(t.report_id),
]);

export const report_books = pgTable('report_books', {
  id: uuid().primaryKey().defaultRandom(),
  order_id: uuid().notNull().references(() => report_orders.id, { onDelete: 'cascade' }),
  storage_pointer: text().notNull(),
  language: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.order_id),
]);

export const payments = pgTable('payments', {
  mode: text().notNull().default('unknown'),
  id: uuid().primaryKey().defaultRandom(),
  order_id: uuid().notNull().references(() => report_orders.id, { onDelete: 'cascade' }),
  provider_ref: text().notNull().unique(),
  status: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.order_id),
]);

export const subscriptions = pgTable('subscriptions', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  provider_ref: text().notNull().unique(),
  plan: text().notNull(),
  expires_at: timestamp({ withTimezone: true }).notNull(),
}, t => [
  index().on(t.user_id),
]);

export const entitlements = pgTable('entitlements', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  capability: text().notNull(),
  expires_at: timestamp({ withTimezone: true }),
}, t => [
  index().on(t.user_id),
  unique().on(t.user_id, t.capability),
]);

export const notifications = pgTable('notifications', {
  translations: jsonb().notNull().default({}),
  id: uuid().primaryKey().defaultRandom(),
  template_key: text().notNull().unique(),
});

export const notification_preferences = pgTable('notification_preferences', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  channel: text().notNull(),
  enabled: boolean().notNull(),
}, t => [
  index().on(t.user_id),
  unique().on(t.user_id,t.channel),
]);

export const notification_inbox = pgTable('notification_inbox', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  notification_id: uuid().notNull().references(() => notifications.id, { onDelete: 'restrict' }),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
  read_at: timestamp({ withTimezone: true }),
}, t => [
  index().on(t.user_id),
  index().on(t.notification_id),
]);

export const check_requests = pgTable('check_requests', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  tool_type: text().notNull(),
  saved: boolean().notNull().default(false),
  inputs: jsonb(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.profile_id),
  check('explicit_save', sql`${t.saved} or ${t.inputs} is null`),
]);

export const explanations_cache = pgTable('explanations_cache', {
  id: uuid().primaryKey().defaultRandom(),
  profile_id: uuid().notNull().references(() => profiles.id, { onDelete: 'cascade' }),
  entity: text().notNull(),
  fact_hash: text().notNull(),
  language: text().notNull(),
  explanation: text().notNull(),
}, t => [
  index().on(t.profile_id),
  unique().on(t.profile_id,t.entity,t.fact_hash,t.language),
]);

export const feature_flags = pgTable('feature_flags', {
  id: uuid().primaryKey().defaultRandom(),
  environment: environment().notNull(),
  key: text().notNull(),
  value: jsonb().notNull(),
}, t => [
  unique().on(t.environment,t.key),
]);

export const rule_catalogue = pgTable('rule_catalogue', {
  draft_patch: jsonb().notNull().default({}),
  id: uuid().primaryKey().defaultRandom(),
  rule_key: text().notNull().unique(),
  source_path: text().notNull(),
  state: approval().notNull(),
}, t => [
  check('dotted_rule_key', sql`position('.' in ${t.rule_key}) > 1`),
]);

export const staff_users = pgTable('staff_users', {
  password_hash: text(),
  disabled_at: timestamp({withTimezone:true}),
  assigned_locale: text(),
  fixture_user_id: uuid().references(() => users.id, {onDelete:'set null'}),
  id: uuid().primaryKey().defaultRandom(),
  email: text().notNull().unique(),
  role: role().notNull(),
  expires_at: timestamp({ withTimezone: true }),
});

export const staff_sessions = pgTable('staff_sessions', {
  binding: text(),
  last_seen: timestamp({withTimezone:true}).notNull().defaultNow(),
  id: uuid().primaryKey().defaultRandom(),
  staff_id: uuid().notNull().references(() => staff_users.id, { onDelete: 'cascade' }),
  token_hash: text().notNull().unique(),
  expires_at: timestamp({ withTimezone: true }).notNull(),
  revoked_at: timestamp({ withTimezone: true }),
}, t => [
  index().on(t.staff_id),
]);

export const staff_mfa_devices = pgTable('staff_mfa_devices', {
  last_step: bigint({mode:'number'}).notNull().default(-1),
  id: uuid().primaryKey().defaultRandom(),
  staff_id: uuid().notNull().references(() => staff_users.id, { onDelete: 'cascade' }),
  secret_ciphertext: text().notNull(),
  key_version: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.staff_id),
]);

export const staff_recovery_codes = pgTable('staff_recovery_codes', {
  id: uuid().primaryKey().defaultRandom(),
  staff_id: uuid().notNull().references(() => staff_users.id, { onDelete: 'cascade' }),
  code_hash: text().notNull().unique(),
  used_at: timestamp({ withTimezone: true }),
}, t => [
  index().on(t.staff_id),
]);

export const kb_entry_reviews = pgTable('kb_entry_reviews', {
  id: uuid().primaryKey().defaultRandom(),
  entry_id: uuid().notNull().references(() => rule_catalogue.id, { onDelete: 'restrict' }),
  actor_id: uuid().notNull().references(() => staff_users.id, { onDelete: 'restrict' }),
  from_state: approval().notNull(),
  to_state: approval().notNull(),
  notes: text(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.entry_id),
  index().on(t.actor_id),
]);

export const native_review_items = pgTable('native_review_items', {
  remedy_option: text(),
  id: uuid().primaryKey().defaultRandom(),
  entry_id: uuid().references(() => rule_catalogue.id, { onDelete: 'restrict' }),
  i18n_key: text(),
  locale: text().notNull(),
  state: text().notNull(),
  proposal: text().notNull(),
  reviewer_id: uuid().references(() => staff_users.id, { onDelete: 'restrict' }),
}, t => [
  index().on(t.entry_id),
  index().on(t.reviewer_id),
  check('one_target', sql`num_nonnulls(${t.entry_id}, ${t.i18n_key}) = 1`),
]);

export const inspector_access_log = pgTable('inspector_access_log', {
  id: uuid().primaryKey().defaultRandom(),
  actor_id: uuid().notNull().references(() => staff_users.id, { onDelete: 'restrict' }),
  opaque_profile_id: uuid().notNull(),
  reason: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.actor_id),
]);

export const staff_ip_allowlist = pgTable('staff_ip_allowlist', {
  id: uuid().primaryKey().defaultRandom(),
  staff_id: uuid().notNull().references(() => staff_users.id, { onDelete: 'cascade' }),
  network: cidr().notNull(),
}, t => [
  index().on(t.staff_id),
]);

export const audit_log = pgTable('audit_log', {
  id: uuid().primaryKey().defaultRandom(),
  actor_id: uuid().notNull(),
  role: role().notNull(),
  action: text().notNull(),
  target_type: text().notNull(),
  opaque_target_id: uuid().notNull(),
  reason: text().notNull(),
  previous_value: jsonb(),
  new_value: jsonb(),
  ip_digest: text().notNull(),
  user_agent: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.opaque_target_id,t.created_at),
]);

export const feedback = pgTable('feedback', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  category: text().notNull(),
  body: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
}, t => [
  index().on(t.user_id),
]);

export const data_requests = pgTable('data_requests', {
  id: uuid().primaryKey().defaultRandom(),
  user_id: uuid().notNull().references(() => users.id, { onDelete: 'cascade' }),
  kind: request().notNull(),
  status: text().notNull(),
  created_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
  due_at: timestamp({ withTimezone: true }).notNull(),
}, t => [
  index().on(t.user_id),
]);

export const report_jobs = pgTable('report_jobs', {
  id: uuid().primaryKey().defaultRandom(),
  order_id: uuid().notNull().references(() => report_orders.id, { onDelete: 'cascade' }),
  status: text().notNull(),
  attempts: integer().notNull().default(0),
  available_at: timestamp({ withTimezone: true }).notNull().defaultNow(),
  lease_until: timestamp({ withTimezone: true }),
}, t => [
  index().on(t.order_id),
  index().on(t.status,t.available_at),
]);

export const otp_rate_limits = pgTable('otp_rate_limits', {
  bucket: text().primaryKey(),
  window_start: timestamp({ withTimezone: true }).notNull(),
  hits: integer().notNull(),
}, t => [index('otp_rate_expiry').on(t.window_start)]);

export const staff_login_challenges = pgTable('staff_login_challenges', {
  token_hash: text().primaryKey(), staff_id: uuid().notNull().unique().references(() => staff_users.id, {onDelete:'cascade'}),
  binding: text().notNull(), expires_at: timestamp({withTimezone:true}).notNull(), enrollment_ciphertext: text()
});
export const staff_approvals = pgTable('staff_approvals', {
  id: uuid().primaryKey().defaultRandom(), owner_id: uuid().notNull().references(() => staff_users.id),
  operation: text().notNull(), parameters: jsonb().notNull(), expires_at: timestamp({withTimezone:true}).notNull(),
  used_at: timestamp({withTimezone:true})
});
export const notification_test_log = pgTable('notification_test_log', {
  id: uuid().primaryKey().defaultRandom(), template_id: uuid().notNull().references(() => notifications.id),
  staff_id: uuid().notNull().references(() => staff_users.id), created_at: timestamp({withTimezone:true}).notNull().defaultNow()
});
