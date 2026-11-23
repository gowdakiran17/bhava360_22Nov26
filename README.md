# Bhava360

A strict TypeScript workspace for the consumer, staff and API shells alongside the existing [knowledge base](kb/README.md). Run commands from the checkout root.

```bash
bash scripts/codex-setup.sh
source .venv/bin/activate
export XDG_DATA_HOME="${XDG_DATA_HOME:-$VIRTUAL_ENV/share}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$VIRTUAL_ENV/cache}"
pnpm test
pnpm typecheck
pnpm check:i18n
pnpm build
(cd kb/governance/validation && PYTHONDONTWRITEBYTECODE=1 python3 check.py)
```

Use Node 22 LTS and the pnpm version in package.json. For development, run `pnpm --filter @bhava360/web dev`, `pnpm --filter @bhava360/admin dev` or `pnpm --filter @bhava360/api dev` in separate shells. Open localhost ports 3000, 3001 and 3002 respectively; the API health path is /health. After a production build use the matching start script. Hosted database migrations are forbidden. The scaffold needs no secrets or paid accounts.

Read the [architecture](docs/architecture.md), [security design](docs/security.md) and [cloud setup](docs/codex-environment.md) before extending the workspace.
