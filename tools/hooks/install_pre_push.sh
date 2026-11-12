#!/usr/bin/env bash
# Wrap pre-push so the destination ref on stdin is checked before pre-commit.
# pre-commit's own runner does not forward that stdin, and hook-impl needs the
# remote name and URL after "--".
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
python_bin="${root}/.venv/bin/python"
if [[ ! -x "${python_bin}" ]]; then
  echo "missing ${python_bin}. Run uv sync before installing the pre-push hook." >&2
  exit 1
fi
mkdir -p "${root}/.git/hooks"
python3 - "${root}/.git/hooks/pre-push" "${python_bin}" <<'PY'
import pathlib
import sys

destination, python_bin = sys.argv[1], sys.argv[2]
path = pathlib.Path(destination)
path.write_text(
    f"""#!/usr/bin/env bash
set -euo pipefail
input="$(cat)"
root="$(git rev-parse --show-toplevel)"
printf '%s\\n' "${{input}}" | python3 "${{root}}/tools/hooks/deny_push_main.py"
cd "${{root}}"
printf '%s\\n' "${{input}}" | {python_bin} -mpre_commit hook-impl \\
  --config=.pre-commit-config.yaml \\
  --hook-type=pre-push \\
  --hook-dir "${{root}}/.git/hooks" \\
  -- "$@"
""",
    encoding="utf-8",
)
path.chmod(0o755)
PY
