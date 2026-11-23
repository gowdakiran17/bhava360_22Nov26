UPDATE feature_flags SET value='true' WHERE key='module.numerology';
DROP TABLE otp_rate_limits;
ALTER TABLE otp_challenges DROP COLUMN created_at;
ALTER TABLE sessions DROP COLUMN active_profile_id, DROP COLUMN locale;
ALTER TABLE profiles DROP COLUMN adult_permission, DROP COLUMN deleted_at;
