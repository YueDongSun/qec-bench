"""Reject staged changes under spec/ or data/gold/ unless OWNER_SPEC_EDIT=1.

Agents must never set OWNER_SPEC_EDIT. See AGENTS.md.
"""

from __future__ import annotations

import os
import subprocess
import sys

_OWNER_ENV = "OWNER_SPEC_EDIT"


def owner_staged(paths: list[str]) -> list[str]:
    """Return staged paths that sit under spec/ or data/gold/."""
    bad: list[str] = []
    for path in paths:
        norm = path.replace("\\", "/").removeprefix("./")
        spec = norm == "spec" or norm.startswith("spec/")
        gold = norm == "data/gold" or norm.startswith("data/gold/")
        if spec or gold:
            bad.append(path)
    return bad


def main() -> int:
    if os.environ.get(_OWNER_ENV) == "1":
        return 0
    raw = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"])
    paths = [item.decode() for item in raw.split(b"\0") if item]
    bad = owner_staged(paths)
    if not bad:
        return 0
    print("refusing commit of owner-only paths:", file=sys.stderr)
    for path in bad:
        print(f"  {path}", file=sys.stderr)
    print(
        "spec/ and data/gold/ are owner-only. "
        "Open a GitHub issue labelled needs-science-decision, quote the spec line, "
        "list the concrete options, and stop.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
