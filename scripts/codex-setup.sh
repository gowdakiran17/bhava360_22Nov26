#!/usr/bin/env bash
# Codex / local developer setup. Package install only. No secrets, no hosted DB.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
root="$PWD"
log() { printf '%s\n' "$*"; }

if ! command -v python3 >/dev/null; then
  log "Install Python 3, python3-venv, python3-pip, Python headers and build tools, then rerun."
  exit 1
fi
if [[ ! -x .venv/bin/python3 ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python3 -m pip install --upgrade pip
CC=gcc CXX=g++ LDSHARED='gcc -shared' LDCXXSHARED='g++ -shared' \
  python3 -m pip install -r requirements-dev.txt

if ! command -v node >/dev/null; then
  log "Installing Node 22 LTS from the official Linux distribution."
  case "$(uname -m)" in
    x86_64) arch=x64 ;;
    aarch64|arm64) arch=arm64 ;;
    *) log "Install Node LTS for this architecture, then rerun."; exit 1 ;;
  esac
  stage=$(mktemp -d)
  trap 'rm -rf -- "$stage"' EXIT
  base=https://nodejs.org/dist/latest-v22.x
  (
    cd "$stage"
    curl --proto '=https' --fail --silent --show-error -O "$base/SHASUMS256.txt"
    awk -v arch="$arch" '$2 ~ ("^node-v22[.][0-9]+[.][0-9]+-linux-" arch "[.]tar[.]xz$")' SHASUMS256.txt > selected.sha256
    [[ $(wc -l < selected.sha256) -eq 1 ]]
    read -r _ archive < selected.sha256
    curl --proto '=https' --fail --silent --show-error -O "$base/$archive"
    sha256sum --check selected.sha256
    mkdir -p "$root/.venv/node"
    tar -xJf "$archive" --strip-components=1 -C "$root/.venv/node"
  )
  ln -sf ../node/bin/node .venv/bin/node
  ln -sf ../node/lib/node_modules/npm/bin/npm-cli.js .venv/bin/npm
fi

export XDG_DATA_HOME="${XDG_DATA_HOME:-$VIRTUAL_ENV/share}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$VIRTUAL_ENV/cache}"
if [[ -f package.json ]] && node -e "process.exit(require('./package.json').packageManager?.startsWith('pnpm@') ? 0 : 1)"; then
  export COREPACK_HOME="$VIRTUAL_ENV/cache/corepack"
  export NODE_USE_ENV_PROXY="${NODE_USE_ENV_PROXY:-1}"
  mkdir -p "$COREPACK_HOME"
  if ! command -v corepack >/dev/null; then
    npm install --cache "$XDG_CACHE_HOME/npm" --global --prefix "$VIRTUAL_ENV" corepack@0.34
  fi
  corepack enable --install-directory "$VIRTUAL_ENV/bin" pnpm
  corepack install
  hash -r
  pnpm --version
elif ! command -v pnpm >/dev/null; then
  npm install --cache "$XDG_CACHE_HOME/npm" --global --prefix "$VIRTUAL_ENV" pnpm@10
fi

if [[ -f package.json ]]; then
  if [[ -f pnpm-lock.yaml ]]; then
    CI=true pnpm install --frozen-lockfile
  else
    CI=true pnpm install
  fi
else
  log "No package.json yet; skipping pnpm install (expected before issue 01)."
fi

if [[ -f .env.example && ! -e .env && ! -L .env ]]; then
  # Reject populated assignments without reading their values into the logs.
  if grep -Evq '^[[:space:]]*(#.*|[A-Za-z_][A-Za-z_0-9]*=)?[[:space:]]*$' .env.example; then
    log "Use only empty assignments in .env.example."
    exit 1
  fi
  cp -n .env.example .env
fi
log "Setup complete."
log "KB validator: cd kb/governance/validation && python3 check.py"
log "App tests (after issue 01): pnpm test"
log "Production build (after issue 01): pnpm build"
log "Never run migrations against a hosted database."
