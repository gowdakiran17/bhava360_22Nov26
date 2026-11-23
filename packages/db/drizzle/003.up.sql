ALTER TABLE staff_users ADD COLUMN password_hash text, ADD COLUMN disabled_at timestamptz,
  ADD COLUMN assigned_locale text CHECK (assigned_locale IN ('kn','hi')),
  ADD COLUMN fixture_user_id uuid REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE staff_sessions ADD COLUMN binding text, ADD COLUMN last_seen timestamptz NOT NULL DEFAULT now();
ALTER TABLE staff_mfa_devices ADD COLUMN last_step bigint NOT NULL DEFAULT -1;
CREATE TABLE staff_login_challenges (
  token_hash text PRIMARY KEY, staff_id uuid NOT NULL UNIQUE REFERENCES staff_users(id) ON DELETE CASCADE,
  binding text NOT NULL, expires_at timestamptz NOT NULL, enrollment_ciphertext text
);
CREATE TABLE staff_approvals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), owner_id uuid NOT NULL REFERENCES staff_users(id),
  operation text NOT NULL, parameters jsonb NOT NULL, expires_at timestamptz NOT NULL, used_at timestamptz
);
ALTER TABLE rule_catalogue ADD COLUMN draft_patch jsonb NOT NULL DEFAULT '{}';
ALTER TABLE notifications ADD COLUMN translations jsonb NOT NULL DEFAULT '{}';
CREATE TABLE notification_test_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), template_id uuid NOT NULL REFERENCES notifications(id),
  staff_id uuid NOT NULL REFERENCES staff_users(id), created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE native_review_items ADD COLUMN remedy_option text;
ALTER TABLE payments ADD COLUMN mode text NOT NULL DEFAULT 'unknown' CHECK (mode IN ('unknown','test','live'));
