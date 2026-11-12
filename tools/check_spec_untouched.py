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


def paths_from_name_status(payload: str) -> list[str]:
    """Return every path in a NUL-terminated ``git diff --name-status -z`` record.

    Rename and copy records contain the source and the destination. A rename
    out of ``spec/`` or ``data/gold/`` must still name the source. ``--name-only``
    with rename detection reports only the destination.
    """
    tokens = payload.split("\0")
    if tokens and tokens[-1] == "":
        tokens = tokens[:-1]
    paths: list[str] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if status[:1] in {"R", "C"}:
            if index + 1 >= len(tokens):
                raise SystemExit(f"truncated git name-status record: {status}")
            paths.extend((tokens[index], tokens[index + 1]))
            index += 2
            continue
        if index >= len(tokens):
            raise SystemExit(f"truncated git name-status record: {status}")
        paths.append(tokens[index])
        index += 1
    return paths


def staged_paths() -> list[str]:
    """Return staged paths, including deletions and both sides of a rename."""
    result = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-status",
            "-z",
            "--find-renames",
            "--find-copies",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return paths_from_name_status(result.stdout)


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
