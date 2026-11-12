"""Pure decisions shared by the git, Cursor, and Claude Code hooks.

The matchers look at the raw command string. They do not try to parse shell
quoting. See ``docs/adr/0003-tooling.md``.
"""

import re

DEFAULT_MAX_BYTES = 500 * 1024
GOLD_MAX_BYTES = 5 * 1024 * 1024

OWNER_EDIT_DENIAL = (
    "spec/ and data/gold/ are owner-only. An edit here is denied. "
    "Open a GitHub issue labelled needs-science-decision, quote the exact spec line, "
    "list the concrete options, and stop."
)

_HEADER = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"\((task|verify|reference|taskfmt|tooling|docs|ci|deps|spec)\): "
    r"\S(?:.*\S)?$"
)
_TRAILER = re.compile(r"(?i)^(co-authored-by|generated-by|made-with)\s*:")
_FORCE_PUSH = re.compile(r"\bgit\s+push\b[^\n;&|]*(\s--force-with-lease\b|\s--force\b|\s-f\b)")
_PUSH_MAIN = re.compile(r"\bgit\s+push\b[^\n;&|]*\sorigin\s+main\b")
_NO_VERIFY = re.compile(r"\bgit\s+commit\b[^\n;&|]*(--no-verify\b|\s-n\b)")
_HARD_RESET = re.compile(r"\bgit\s+reset\s+--hard\s+(\S+)")
_PIP = re.compile(r"(?:^|[\s;&|])pip3?\s+install\b")
_PYTHON_PIP = re.compile(r"\bpython3?\s+-m\s+pip\s+install\b")
_SHARED_REVISION = re.compile(r"^(?:main|.+/main)$")
_REMOTE_REF_INDEX = 2

COMMIT_HINT = (
    "commit message must be Conventional Commits with a scope from "
    "task, verify, reference, taskfmt, tooling, docs, ci, deps, spec. "
    "Example: feat(task): add example_000_smoke"
)


def _parts(path: str) -> list[str]:
    return [part for part in path.replace("\\", "/").split("/") if part not in {"", "."}]


def is_gold(path: str) -> bool:
    """Return whether ``path`` is inside ``data/gold``."""
    parts = _parts(path)
    return any(
        part == "data" and parts[index + 1] == "gold" for index, part in enumerate(parts[:-1])
    )


def is_owner_only(path: str) -> bool:
    """Return whether ``path`` is under ``spec/`` or ``data/gold/``."""
    return "spec" in _parts(path) or is_gold(path)


def size_limit(path: str) -> int:
    """Return the maximum staged blob size for ``path`` in bytes."""
    if is_gold(path):
        return GOLD_MAX_BYTES
    return DEFAULT_MAX_BYTES


def denied_shell_reason(command: str) -> str | None:
    """Return a denial message, or ``None`` when the command may run."""
    reset = _HARD_RESET.search(command)
    reset_on_main = reset is not None and _SHARED_REVISION.fullmatch(reset.group(1)) is not None
    pip_install = _PIP.search(command) is not None or _PYTHON_PIP.search(command) is not None
    checks = (
        (
            "OWNER_SPEC_EDIT=" in command,
            "OWNER_SPEC_EDIT is reserved for the owner. "
            "Open a needs-science-decision issue instead of setting it.",
        ),
        (pip_install, "pip install is denied. Add dependencies with uv add."),
        (_FORCE_PUSH.search(command) is not None, "git push --force is denied."),
        (
            _PUSH_MAIN.search(command) is not None,
            "git push origin main is denied. Open a pull request; the owner merges.",
        ),
        (_NO_VERIFY.search(command) is not None, "git commit --no-verify is denied."),
        (reset_on_main, "git reset --hard on main is denied."),
    )
    for matched, reason in checks:
        if matched:
            return reason
    return None


def commit_message_error(text: str) -> str | None:
    """Return a rejection reason, or ``None`` when the message is acceptable."""
    lines = text.splitlines()
    if not lines or _HEADER.fullmatch(lines[0]) is None:
        return COMMIT_HINT
    for line in lines:
        if _TRAILER.match(line) is not None or re.search(r"(?i)\bmade with\b", line):
            return "ordinary commits must not carry attribution trailers"
    return None


def denied_push(stdin_text: str, branch: str) -> str | None:
    """Return a rejection reason for a pre-push stdin payload.

    An empty payload means the destination refs were not forwarded. In that
    case a checkout of ``main`` is still refused.
    """
    lines = [line for line in stdin_text.splitlines() if line.strip()]
    refusal = "push to main is refused. Open a pull request; the owner merges."
    if not lines:
        if branch == "main":
            return refusal
        return None
    for line in lines:
        parts = line.split()
        if len(parts) <= _REMOTE_REF_INDEX:
            return f"unreadable pre-push line: {line}"
        if parts[_REMOTE_REF_INDEX] == "refs/heads/main":
            return refusal
    return None


def cursor_stop_body(returncode: int, output: str) -> dict[str, str]:
    """Build the Cursor ``stop`` response. An empty mapping allows the stop."""
    if returncode == 0:
        return {}
    tail = "\n".join(output.splitlines()[-80:])
    return {"followup_message": "make check failed. Keep working until it passes.\n" + tail}


def claude_stop_body(returncode: int, output: str) -> dict[str, str]:
    """Build the Claude Code ``Stop`` response. An empty mapping allows the stop."""
    if returncode == 0:
        return {}
    tail = "\n".join(output.splitlines()[-80:])
    return {
        "decision": "block",
        "reason": "make check failed. Keep working until it passes.\n" + tail,
    }
