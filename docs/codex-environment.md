# Bhava360 cloud development

Use the existing checkout at `/workspace/bhava360_22Nov26`. The managed Linux image supplies Bash, npm, GCC/G++ and Python 3. On a minimal Debian or Ubuntu image, include `python3`, `python3-venv`, `python3-dev`, `build-essential` and `npm` during image provisioning.

## Setup phase

Allow network access only for package installation. Configure the cloud setup command as follows.

```bash
cd /workspace/bhava360_22Nov26
./scripts/codex-setup.sh
```

The script prepares Node 24 LTS, pnpm and a Python virtual environment with the pinned development requirements. It can run repeatedly. Once a root package manifest exists, it installs the workspace dependencies, using the frozen lockfile when available. The default tool directory is outside the checkout. Set `BHAVA_TOOLS_DIR` to an absolute writable directory to override it.

## Agent phase

Disable internet access after setup. Development and validation run locally, with synthetic fixtures from [AGENTS.md](../AGENTS.md). Setup requires no secrets or environment file. Swiss Ephemeris is a development dependency for future reference tests. The owner decides licensing before public launch.

Activate the installed tools in each new task shell.

```bash
cd /workspace/bhava360_22Nov26
tools_dir="${BHAVA_TOOLS_DIR:-/workspace/.bhava360-tools}"
export PATH="$tools_dir/bin:$PATH"
. "$tools_dir/venv/bin/activate"
node --version
pnpm --version
python3 -c 'import yaml, swisseph'
(cd kb/governance/validation && PYTHONDONTWRITEBYTECODE=1 python3 check.py)
```

Once the root package manifest exists, also run `pnpm test` and `pnpm build` from the checkout root. Use local or ephemeral Postgres for future database checks. The migration CLI must refuse hosted URLs. Kiran approves hosted migrations separately.
