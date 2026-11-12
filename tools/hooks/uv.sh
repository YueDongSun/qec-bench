#!/usr/bin/env bash
set -euo pipefail
if ! command -v uv >/dev/null 2>&1; then
  if [[ -x "${HOME}/.local/bin/uv" ]]; then
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not on PATH. Install uv, then run make setup." >&2
  exit 1
fi
exec uv "$@"
