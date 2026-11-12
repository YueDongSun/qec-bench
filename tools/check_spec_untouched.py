"""Reject staged edits under ``spec/`` or ``data/gold/``.

``OWNER_SPEC_EDIT=1`` is the owner's bypass. Agents must not set it.
"""

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.hooks.policy import OWNER_EDIT_DENIAL, is_owner_only  # noqa: E402


def staged_paths() -> list[str]:
    """Return staged paths, including deletions."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def owner_violations(paths: list[str], *, owner_edit: bool) -> list[str]:
    """Return owner-only paths that this commit is not allowed to stage."""
    if owner_edit:
        return []
    return [path for path in paths if is_owner_only(path)]


def main() -> None:
    """Fail the commit when an agent has staged owner-only paths."""
    violations = owner_violations(
        staged_paths(),
        owner_edit=os.environ.get("OWNER_SPEC_EDIT") == "1",
    )
    if violations:
        print(OWNER_EDIT_DENIAL, file=sys.stderr)
        for path in violations:
            print(f"staged owner-only path: {path}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
