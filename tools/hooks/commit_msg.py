"""commit-msg hook: Conventional Commits with a mandatory allowed scope."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_HEADER = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"\((task|verify|reference|taskfmt|tooling|docs|ci|deps|spec)\)"
    r"!?: \S(?:.*\S)?$"
)

_EXAMPLE = "feat(task): add decoding-001-repetition-memory"


def commit_message_error(message: str) -> str | None:
    """Return an error for a non-conforming message, else None."""
    header = message.splitlines()[0].strip() if message.splitlines() else ""
    if header == "":
        return "commit message is empty"
    if header.startswith("Merge "):
        return "merge commits are refused; rebase onto main"
    if _HEADER.fullmatch(header) is None:
        return (
            "commit message must be Conventional Commits with a scope from "
            "task, verify, reference, taskfmt, tooling, docs, ci, deps, spec. "
            f"Example: {_EXAMPLE}"
        )
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: commit_msg.py <message-file>", file=sys.stderr)
        return 2
    error = commit_message_error(Path(argv[0]).read_text(encoding="utf-8"))
    if error is None:
        return 0
    print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
