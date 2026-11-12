"""pre-push hook: refuse main, then run make check.

Git passes ref updates on stdin. pre-commit consumes that stream and exposes the
destination as ``PRE_COMMIT_REMOTE_BRANCH`` (for example ``refs/heads/main``).
See docs/adr/0003-tooling.md.
"""

from __future__ import annotations

import os
import subprocess
import sys

REFUSE_MAIN = "push to main is refused. Open a PR; the owner merges."
_MAIN_REF = "refs/heads/main"
_MIN_PRE_PUSH_FIELDS = 3
_REMOTE_REF_INDEX = 2


def refuses_push(
    stdin_text: str,
    current_branch: str,
    *,
    remote_branch: str | None = None,
) -> str | None:
    """Return a refusal when this push updates main."""
    if current_branch == "main" or _is_main_ref(remote_branch):
        return REFUSE_MAIN
    for line in stdin_text.splitlines():
        if line.strip() == "":
            continue
        parts = line.split()
        if len(parts) < _MIN_PRE_PUSH_FIELDS:
            raise SystemExit(f"unexpected pre-push line: {line}")
        if _is_main_ref(parts[_REMOTE_REF_INDEX]):
            return REFUSE_MAIN
    return None


def _is_main_ref(ref: str | None) -> bool:
    return ref is not None and ref.strip() == _MAIN_REF


def main() -> int:
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()
    reason = refuses_push(
        sys.stdin.read(),
        branch,
        remote_branch=os.environ.get("PRE_COMMIT_REMOTE_BRANCH"),
    )
    if reason is not None:
        print(reason, file=sys.stderr)
        return 1
    completed = subprocess.run(["make", "check"], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
