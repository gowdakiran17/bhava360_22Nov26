ALTER TABLE profiles ADD COLUMN deleted_at timestamptz, ADD COLUMN adult_permission boolean NOT NULL DEFAULT false;
ALTER TABLE sessions ADD COLUMN locale text NOT NULL DEFAULT 'en' CHECK (locale IN ('en','kn','hi')),
  ADD COLUMN active_profile_id uuid REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE otp_challenges ADD COLUMN created_at timestamptz NOT NULL DEFAULT now();
CREATE TABLE otp_rate_limits (
  bucket text PRIMARY KEY, window_start timestamptz NOT NULL, hits integer NOT NULL
);
CREATE INDEX otp_rate_expiry ON otp_rate_limits(window_start);
UPDATE feature_flags SET value='false' WHERE key='module.numerology';
