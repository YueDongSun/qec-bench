#!/usr/bin/env bash
# Wrap the pre-commit pre-push hook so destination refs on stdin are checked.
# pre-commit's hook runner does not forward that stdin to hook scripts.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
hook="${root}/.git/hooks/pre-push"
if [[ ! -f "${hook}" ]]; then
  echo "pre-commit pre-push hook is missing. Run: uv run pre-commit install --hook-type pre-push" >&2
  exit 1
fi
if grep -q "deny_push_main.py" "${hook}"; then
  exit 0
fi
cat > "${hook}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
input="$(cat)"
root="$(git rev-parse --show-toplevel)"
printf '%s\n' "${input}" | python3 "${root}/tools/hooks/deny_push_main.py"
cd "${root}"
if ! command -v uv >/dev/null 2>&1 && [[ -x "${HOME}/.local/bin/uv" ]]; then
  export PATH="${HOME}/.local/bin:${PATH}"
fi
exec uv run pre-commit hook-impl --config=.pre-commit-config.yaml --hook-type=pre-push --hook-dir "${root}/.git/hooks" "$@"
EOF
chmod 0755 "${hook}"
