"""pre-push hook: refuse main, then run make check."""

from __future__ import annotations

import subprocess
import sys

REFUSE_MAIN = "push to main is refused. Open a PR; the owner merges."
_MIN_PRE_PUSH_FIELDS = 3
_REMOTE_REF_INDEX = 2


def refuses_push(stdin_text: str, current_branch: str) -> str | None:
    """Return a refusal when this push updates main."""
    if current_branch == "main":
        return REFUSE_MAIN
    for line in stdin_text.splitlines():
        if line.strip() == "":
            continue
        parts = line.split()
        if len(parts) < _MIN_PRE_PUSH_FIELDS:
            raise SystemExit(f"unexpected pre-push line: {line}")
        remote_ref = parts[_REMOTE_REF_INDEX]
        if remote_ref == "refs/heads/main":
            return REFUSE_MAIN
    return None


def main() -> int:
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()
    reason = refuses_push(sys.stdin.read(), branch)
    if reason is not None:
        print(reason, file=sys.stderr)
        return 1
    completed = subprocess.run(["make", "check"], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
