"""Command deny list shared by Cursor beforeShellExecution and Claude Code Bash hooks."""

from __future__ import annotations

import re

DENY_OWNER_SPEC = (
    "OWNER_SPEC_EDIT must not be set. spec/ and data/gold/ are owner-only. "
    "Open a needs-science-decision issue instead."
)
DENY_PIP = "pip install is refused. Add dependencies with `uv add`."
DENY_FORCE_PUSH = "git push --force is refused."
DENY_PUSH_MAIN = "git push to main is refused. Open a PR; the owner merges."
DENY_NO_VERIFY = "git commit --no-verify is refused."
DENY_RESET_HARD = "git reset --hard on a shared branch is refused."

SHARED_BRANCHES = frozenset({"main"})

_STATEMENT_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\n)\s*")
_GIT_PUSH = re.compile(r"(?:^|[^\w./-])git\s+push\b")
_GIT_COMMIT = re.compile(r"(?:^|[^\w./-])git\s+commit\b")
_GIT_RESET_HARD = re.compile(r"(?:^|[^\w./-])git\s+reset\s+--hard\b")
_FORCE_FLAG = re.compile(r"(?:^|\s)--force(?:\b|=)|(?:^|\s)-f(?:\s|$)")
_NO_VERIFY = re.compile(r"(?:^|\s)--no-verify\b|(?:^|\s)-n(?:\s|$)")
_PIP_INSTALL = re.compile(
    r"(?:^|[^\w./-])(?:pip3?\s+install|python3?\s+-m\s+pip\s+install|uv\s+pip\s+install)\b"
)
_PUSH_MAIN = re.compile(
    r"(?:^|\s)main(?:\s|$)|:main(?:\s|$)|(?:^|\s)origin/main(?:\s|$)|refs/heads/main(?:\s|$)"
)
_RESET_MAIN = re.compile(r"--hard\s+(?:(?:origin/)?main|refs/heads/main)(?:\s|$)")


def shell_denial(command: str, *, current_branch: str | None) -> str | None:
    """Return a denial reason, or None when the command is allowed."""
    if "OWNER_SPEC_EDIT=" in command:
        return DENY_OWNER_SPEC
    for statement in _statements(command):
        reason = _statement_denial(statement, current_branch=current_branch)
        if reason is not None:
            return reason
    return None


def _statements(command: str) -> list[str]:
    return [part.strip() for part in _STATEMENT_SPLIT.split(command) if part.strip()]


def _statement_denial(statement: str, *, current_branch: str | None) -> str | None:
    if _PIP_INSTALL.search(statement):
        return DENY_PIP
    if _GIT_COMMIT.search(statement) and _NO_VERIFY.search(statement):
        return DENY_NO_VERIFY
    if _GIT_PUSH.search(statement) and _FORCE_FLAG.search(statement):
        return DENY_FORCE_PUSH
    if _GIT_PUSH.search(statement) and _PUSH_MAIN.search(statement):
        return DENY_PUSH_MAIN
    if _GIT_RESET_HARD.search(statement) and (
        current_branch in SHARED_BRANCHES or _RESET_MAIN.search(statement) is not None
    ):
        return DENY_RESET_HARD
    return None
