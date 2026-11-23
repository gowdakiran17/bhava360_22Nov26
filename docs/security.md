# Security and privacy boundaries

Consumer and admin bundles deploy to separate origins. Issue 03 introduces consumer OTP and host-only httpOnly sessions. Issue 04 introduces staff email authentication plus mandatory TOTP. Staff use a separately named, signed, revocable host-only cookie. Validate origin on mutations and authorize the session audience on every route. A consumer session cannot grant staff permissions.

Staff have one role each: owner, admin, astrologer-reviewer, native-language reviewer, tester or support. Restrict approval to the owner. Exclude live impersonation. Audit privileged actions using object IDs and outcomes. Consumer serializers explicitly allowlist public fields through toPublicProjection before returning, caching or exporting data. Technical evidence stays on authorized staff/tester routes.

Inject secrets only through deployment environment variables. Redact raw phone, email, birth datetime, OTP, session credentials and API keys from structured logs. Collect separate consent for palmistry images, restrict processing to that purpose, delete images by default after processing, and never derive biometric templates.

The shell endpoints contain no account data. Keep synthetic test runs local. Hosted migrations require separate owner approval when introduced.
