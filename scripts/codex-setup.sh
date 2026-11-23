#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tools_dir="${BHAVA_TOOLS_DIR:-/workspace/.bhava360-tools}"
mkdir -p "$tools_dir"
export PATH="$tools_dir/bin:$PATH"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$tools_dir/share}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$tools_dir/cache}"
if ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) === 24 && process.release.lts ? 0 : 1)' 2>/dev/null; then
  npm install --prefix "$tools_dir" --global node@24
fi
if ! command -v pnpm >/dev/null; then
  npm install --prefix "$tools_dir" --global pnpm@11.25.0
fi
python3 -m venv "$tools_dir/venv"
. "$tools_dir/venv/bin/activate"
CC=gcc CXX=g++ LDSHARED='gcc -shared' LDCXXSHARED='g++ -shared' \
  python -m pip install --disable-pip-version-check -r requirements-dev.txt
if [[ -f pnpm-lock.yaml ]]; then
  pnpm install --frozen-lockfile
elif [[ -f package.json ]]; then
  pnpm install
fi
