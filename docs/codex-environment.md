# Bhava360 development environment

Use the repository root as the working directory for Codex cloud and local agent sessions.

## Cloud settings

Set the setup command to `bash scripts/codex-setup.sh`. Allow outbound access during setup only for package installation through apt, official Node distributions, the npm/pnpm registry and PyPI. Turn internet access off during implementation, or use the closest available outbound restriction. If a dependency is missing, rerun setup. Keep product sign-in, production scraping, live bhava360.com, hosted databases and payment, OTP and AI providers outside both phases.

Leave the environment secret store empty. If the platform requires a binding, use an empty placeholder. Document variable names only, such as `DATABASE_URL` and `ADMIN_BOOTSTRAP_OWNER_EMAIL`. Never put credential values or a real owner email in the repository or Codex memory. Setup copies a names-only `.env.example` when present and preserves an existing `.env`. Use only the synthetic fixtures in [AGENTS.md](../AGENTS.md).

## Toolchain

Start with Bash and Python 3 on Linux. On a minimal Debian or Ubuntu image, install missing prerequisites during setup with apt: `python3`, `python3-venv`, `python3-pip`, `python3-dev`, `build-essential`, `ca-certificates`, `curl` and `xz-utils`. The script creates a repository-local `.venv` and installs the development requirements from PyPI. PyYAML provides the `yaml` module and pyswisseph provides `swisseph`.

Setup uses the installed Node and pnpm when available. On Linux x64 and arm64, it can bootstrap Node 22 LTS from the official nodejs.org tarball, checking its SHA-256 against the release manifest before extraction. When pnpm is missing it installs major 10 with npm into the virtual environment. New shells can use these tools by activating the environment.

## Before each PR

From the repository root, run:

```bash
source .venv/bin/activate
export XDG_DATA_HOME="${XDG_DATA_HOME:-$VIRTUAL_ENV/share}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$VIRTUAL_ENV/cache}"
export PYTHONDONTWRITEBYTECODE=1
python3 -c "import yaml, swisseph"
(cd kb/governance/validation && python3 check.py)
```

Once issue 01 adds the root `package.json`, also run `pnpm test` and `pnpm build` from the root. These local checks replace cloud CI for now. Do not add GitHub Actions. The validators under `kb/` remain authoritative for YAML. Preserve them during setup.

If set, `DATABASE_URL` may point only to local or ephemeral Postgres. Migration commands must refuse non-local URLs. Kiran approves hosted migrations separately.
