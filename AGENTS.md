# AGENTS.md

This repository is a **new from-scratch** multi-system astrology app (working name **Bhava360**; final name TBD). It is **not** the live app at bhava360.com. Do not reuse code, data, secrets, or schema from any earlier Bhava360 project.

You are implementing product work from a GitHub issue. Follow this file, then the issue. If they conflict, follow the stricter safety rule and note the conflict in the PR.

## One PR per issue

- Implement only the issue you were assigned.
- Open **exactly one** pull request for that issue.
- Do not start the next groundwork issue in the same PR, and do not file new issues from the work.
- Give complete files, not fragments. Do not deploy, publish, or apply changes to any hosted environment.

## Commands to run before opening a PR

Always run the knowledge-base validator (repo already contains it):

```bash
cd kb/governance/validation && python3 check.py
```

Once the TypeScript monorepo exists (`package.json` at the repo root, added in the setup/architecture issue):

```bash
pnpm test
pnpm build
```

Do not add GitHub Actions workflows. Quality gates are this local test suite and the production build.

Do **not** run database migrations against any hosted database (Render, Neon, Supabase, RDS, or any non-local URL). Kiran approves hosted migrations separately. Local or ephemeral Postgres in tests is allowed. A migrate CLI must refuse hosted URLs.

## Synthetic fixtures only

Use only these five people in code, tests, seeds, mockups, docs, and screenshots (IST, Lahiri ayanamsa). **Never** use real birth data, real phone numbers, or real emails.

| Name | Date | Time | Place |
|---|---|---|---|
| Asha | 12 Mar 1992 | 05:40 | Bengaluru |
| Ravi | 3 Aug 1985 | 14:10 | Mysuru |
| Meera | 21 Dec 2001 | 22:30 | Delhi |
| Kabir | 9 Jun 1978 | 07:15 | Mumbai |
| Dev | 5 Jan 1995 | 12:00 (noon; also the "time unknown" fixture) | Chennai |

Fake tester numbers only, for example `9000000001`. Fake staff emails only, for example `owner@example.test`. Place aliases such as Mysuru/Mysore and Bengaluru/Bangalore must resolve to the same gazetteer row.

## Secrets and environment

- Never commit secrets, API keys, tokens, OTP codes, or a real owner email.
- Document environment variable **names** only in `.env.example`.
- Settings UIs and logs may show secret names and present/missing — never values.
- Structured logs must not contain raw phone, email, birth datetime, OTP, card data, or key material.

## Do not edit these

- Do not edit `kb/` content (YAML entries, SCHEMA, examples, or the Python validators). Application code lives beside `kb/`, never inside it. The portal may store approval state and copy proposals in database tables that *reference* dotted KB IDs; it must not rewrite files under `kb/` and must not invent a second rule catalogue.
- Do not edit or generate legal or privacy wording (Privacy, Terms, Refunds, Disclaimer). Placeholder routes are fine; body text is a human owner upload.

## Product copy and evidence

- User-facing wording uses **may / can / tends to**. Never "will", "guaranteed", "destined", "doomed", or "your fate".
- Tones are exactly **Supportive**, **Steady**, or **Take care**. Never "Favourable", "bad", "danger", or colour-only meaning.
- **No scores, percentages, meters, or star ratings** for ordinary users. Technical points, totals, bindus, rule IDs, sources, confidence, dasha/transit chains, KP sublords, and numerology sums are **admin/tester only** and must be stripped from consumer API projections. (A later matching module may show traditional points as plain text, for example "31 of 36 traditional points" — never as a score meter.)
- No fear, urgency, countdowns, or loss warnings. No gemstones, crystals, lucky colours, paid remedies, or yantras for sale. Remedies that exist must be optional, free, and conduct-based.
- Every AI-written sentence is marked **✦ AI**; nothing else uses ✦.
- Every user-facing string is externalised in **English, Kannada, and Hindi**. A missing required-locale key must fail the test suite or production build. Staff UI may be English-only; strings the user will see still need `en` / `kn` / `hi`.

## Admin and auth

- The admin portal lives on a **separate host** (recommended production host `admin.<app-domain>`; a separate localhost port in dev). `/staff` on the public app is acceptable only in local/dev. No "Admin" link in the consumer app.
- Staff sign-in is **email + password or email magic link, plus mandatory TOTP 2FA**. Consumer phone OTP must not grant staff access.
- Dummy OTP exists only when `APP_ENV` is not `production`, and only for synthetic accounts.
- Six staff roles, one role per account: owner, admin, astrologer-reviewer, native-language reviewer, tester, support. Only the owner can set a KB rule to `approved`, grant the owner role, or complete a hard delete. No live impersonation ("become this user") in MVP.
- First owner email belongs in bootstrap env (`ADMIN_BOOTSTRAP_OWNER_EMAIL`), never in the repository.

## Services and licensing

- No paid services or paid-account sign-ups in this work. Integrations are interfaces, stubs, and env var names (AI, OTP, email, Razorpay, Swiss Ephemeris path). Prefer a Postgres-backed queue over Redis.
- `pyswisseph` may be installed in the dev/Codex environment for later golden tests. Do not add ephemeris binaries or a licence decision in application code; the Swiss Ephemeris licence is an owner decision before public launch.

## Architecture defaults (unless an issue says otherwise)

- TypeScript strict monorepo with pnpm, Next.js apps (`apps/web`, `apps/admin`, `apps/api`), PostgreSQL + Drizzle, Vitest.
- Engine packages are pure: no network, no UI, no host-local time.
- Birth instants are resolved once from IANA history and stored in UTC, with original local date/time/zone kept for display. Unknown birth time uses a noon chart and marks Lagna-dependent facts unavailable (Dev is the time-unknown fixture).
