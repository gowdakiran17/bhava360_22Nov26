# Consumer API

Expose /consumer/* on the WEB_ORIGIN host through a same-origin reverse proxy to apps/api. Preserve Host and the browser's Origin. Mutations require Origin to match WEB_ORIGIN exactly. Route staff traffic separately. The API issues a host-only __Host-bhava-consumer cookie with Path=/, Secure, HttpOnly, SameSite=Strict and a 30-day lifetime. Use HTTPS for browser development. Only keyed token digests reach the consumer sessions table. Staff authorization must use its own session table and cookie.

Supply DATABASE_URL for local Postgres, WEB_ORIGIN and APP_ENV. Development and test use a process-local random key when SESSION_SECRET is absent; restarting then invalidates sessions and pending codes. For stable keys across workers, inject SESSION_SECRET of at least 32 characters. Other environments require an injected key. Use the documented local migration and development seed commands. For a trusted ingress that overwrites incoming client-IP headers, configure TRUSTED_CLIENT_IP_HEADER to that header's name. Only configure it if clients cannot access the backend directly or supply its value. Otherwise all clients share a conservative IP bucket. Responses are uncached and errors include a stable key and a translated message. Before login the API reads Accept-Language; after login it uses the session locale.

| Method and path under /consumer | Request and result |
|---|---|
| POST /otp/request | Send channel (phone or email) and identifier. A generic 202 acknowledges the request. Ten-digit Indian numbers normalize to +91 and emails to lowercase. |
| POST /otp/verify | Send channel, identifier, six-digit code and optional locale. Success returns authenticated and sets the cookie. |
| GET or PATCH /session | Read locale and active_profile_id. PATCH accepts locale (en, kn or hi). |
| POST /logout or /logout-all | Revoke the current session or all of the user's sessions and clear the current cookie. |
| GET /places?q=prefix | Search localized city names and aliases. Returns canonical ID, display names, city coordinates and IANA zone. |
| GET or POST /consents | Read recorded decisions or submit consent_version and booleans for adult, terms, birthDetails, ai, updates and analytics. The first three must be true. Omitted optional choices are recorded as false. |
| GET or POST /profiles | List owned active profiles or create one with display_name, local_date, local_time, time_precision, place_id, relation and optional gender. For another adult, set adult_permission. |
| GET, PATCH or DELETE /profiles/{id} | Read, update or soft-delete an owned profile. Deletion also clears active selection in other sessions. |
| POST /profiles/{id}/switch | Persist active selection for the current session. |

Known and approximate times use the gazetteer's IANA zone. Unknown time uses local noon with its own precision flag. Skipped local times return 400. Repeated local times return 409 with chooseTime; resubmit with disambiguation set to earlier or later. The historical test uses New York's November 2020 fold. Non-birth edits retain the stored UTC instant. Three live profiles are allowed on the free plan; an active Plus entitlement lifts that cap pending the owner decision.

## Fixture delivery

The phone and email port currently delivers only to an in-process fixture mailbox. Use APP_ENV=development or test and rerun the synthetic seed after upgrading an issue 02 development database. Only the five allowlisted normalized identifiers per channel bound to the corresponding seeded user IDs can receive codes. Automated tests read the mailbox directly. No route returns codes, the server logs none, and staging, production and unspecified environments return 503 from both OTP operations. Live providers and non-fixture sign-in await the provider decision.

Codes expire after ten minutes, allow five mismatches and are replaced on resend after thirty seconds. Consuming a code and creating its session share a transaction. Separate ten-minute request and verify budgets allow six requests or twenty verifications per identifier and thirty requests or sixty verifications per IP. Exceeding a budget or resending early returns 429. PostgreSQL enforces shared budgets across API instances; only digests reach limit rows. Expired challenge and session retention follows the database retention guidance.

Migration 002 turns module.numerology off across environments on both fresh installs and issue 02 upgrades. Numerology is scheduled for R2.
