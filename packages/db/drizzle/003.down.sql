ALTER TABLE payments DROP COLUMN mode;
ALTER TABLE native_review_items DROP COLUMN remedy_option;
DROP TABLE notification_test_log;
ALTER TABLE notifications DROP COLUMN translations;
ALTER TABLE rule_catalogue DROP COLUMN draft_patch;
DROP TABLE staff_approvals, staff_login_challenges;
ALTER TABLE staff_mfa_devices DROP COLUMN last_step;
ALTER TABLE staff_sessions DROP COLUMN binding, DROP COLUMN last_seen;
ALTER TABLE staff_users DROP COLUMN fixture_user_id, DROP COLUMN assigned_locale, DROP COLUMN disabled_at, DROP COLUMN password_hash;
