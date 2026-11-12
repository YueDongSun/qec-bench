"""Cursor and Claude Code hook entry point. Both configs call this script."""

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.hooks.policy import (  # noqa: E402
    OWNER_EDIT_DENIAL,
    claude_stop_body,
    cursor_stop_body,
    denied_shell_reason,
    is_owner_only,
)

_EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit"})
_CURSOR_WRITE_TOOLS = frozenset(
    {"Write", "Edit", "StrReplace", "Delete", "MultiEdit", "ApplyPatch"}
)
_PYTHON_SUFFIXES = frozenset({".py", ".pyi"})
CURSOR_DENY_EXIT = 2


def parse_payload(raw: str) -> dict[str, object]:
    """Parse a hook payload. Fail when the body is not a JSON object."""
    loaded = cast(object, json.loads(raw))
    if not isinstance(loaded, dict):
        raise SystemExit("hook payload must be a JSON object")
    return cast(dict[str, object], loaded)


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or value == "":
        raise SystemExit(f"hook payload field {key} must be a non-empty string")
    return value


def _tool_input(payload: dict[str, object]) -> dict[str, object]:
    value = payload.get("tool_input")
    if not isinstance(value, dict):
        raise SystemExit("tool_input must be an object")
    return cast(dict[str, object], value)


def edit_path(payload: dict[str, object]) -> str:
    """Return the file path an edit hook is about to touch or has touched."""
    direct = payload.get("file_path")
    if isinstance(direct, str) and direct != "":
        return direct
    table = payload.get("tool_input")
    if isinstance(table, dict):
        fields = cast(dict[str, object], table)
        for key in ("file_path", "path"):
            value = fields.get(key)
            if isinstance(value, str) and value != "":
                return value
    raise SystemExit("edit hook payload has no file path")


def cursor_deny(reason: str) -> dict[str, str]:
    """Cursor permission denial, including the message sent back to the agent."""
    return {"permission": "deny", "user_message": reason, "agent_message": reason}


def claude_permission(reason: str | None) -> dict[str, object]:
    """Claude Code ``PreToolUse`` decision."""
    inner: dict[str, str] = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow" if reason is None else "deny",
    }
    if reason is not None:
        inner["permissionDecisionReason"] = reason
    return {"hookSpecificOutput": inner}


def format_python(path: Path) -> None:
    """Run ``ruff format`` on a Python file. Other suffixes are left alone."""
    if path.suffix not in _PYTHON_SUFFIXES:
        return
    uv = Path(__file__).with_name("uv.sh")
    subprocess.run([str(uv), "run", "ruff", "format", str(path)], check=True)


def run_make_check() -> tuple[int, str]:
    """Run ``make check`` and return its exit code plus combined output."""
    result = subprocess.run(
        ["make", "check"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def _cursor_shell(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    reason = denied_shell_reason(_require_str(payload, "command"))
    if reason is None:
        return 0, {"permission": "allow"}
    return CURSOR_DENY_EXIT, cast(dict[str, object], cursor_deny(reason))


def _cursor_write(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    tool_name = _require_str(payload, "tool_name")
    if tool_name not in _CURSOR_WRITE_TOOLS:
        raise SystemExit(f"preToolUse tool {tool_name} is not handled")
    if is_owner_only(edit_path(payload)):
        return CURSOR_DENY_EXIT, cast(dict[str, object], cursor_deny(OWNER_EDIT_DENIAL))
    return 0, {"permission": "allow"}


def _cursor_read(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    _require_str(payload, "file_path")
    return 0, {"permission": "allow"}


def _cursor_after_edit(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    path = edit_path(payload)
    if is_owner_only(path):
        return CURSOR_DENY_EXIT, cast(dict[str, object], cursor_deny(OWNER_EDIT_DENIAL))
    format_python(Path(path))
    return 0, {}


def _cursor_stop(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    status = payload.get("status", "completed")
    if not isinstance(status, str):
        raise SystemExit("stop status must be a string")
    if status != "completed":
        return 0, {}
    code, output = run_make_check()
    return 0, cast(dict[str, object], cursor_stop_body(code, output))


def _claude_pretool(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    tool_name = _require_str(payload, "tool_name")
    if tool_name == "Bash":
        reason = denied_shell_reason(_require_str(_tool_input(payload), "command"))
        return 0, claude_permission(reason)
    if tool_name in _EDIT_TOOLS:
        reason = OWNER_EDIT_DENIAL if is_owner_only(edit_path(payload)) else None
        return 0, claude_permission(reason)
    raise SystemExit(f"PreToolUse tool {tool_name} is not handled")


def _claude_posttool(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    path = edit_path(payload)
    if is_owner_only(path):
        return 0, {"decision": "block", "reason": OWNER_EDIT_DENIAL}
    format_python(Path(path))
    return 0, {}


def _claude_stop(_payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    code, output = run_make_check()
    return 0, cast(dict[str, object], claude_stop_body(code, output))


_HANDLERS = {
    "beforeShellExecution": _cursor_shell,
    "preToolUse": _cursor_write,
    "beforeReadFile": _cursor_read,
    "afterFileEdit": _cursor_after_edit,
    "stop": _cursor_stop,
    "PreToolUse": _claude_pretool,
    "PostToolUse": _claude_posttool,
    "Stop": _claude_stop,
}


def handle(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    """Dispatch one hook payload to an exit code and a JSON body."""
    event = _require_str(payload, "hook_event_name")
    handler = _HANDLERS.get(event)
    if handler is None:
        raise SystemExit(f"unknown hook event: {event}")
    return handler(payload)


def main() -> None:
    """Read one JSON payload from stdin and write the hook response."""
    code, body = handle(parse_payload(sys.stdin.read()))
    json.dump(body, sys.stdout)
    sys.stdout.write("\n")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
