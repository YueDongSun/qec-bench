"""Cursor beforeShellExecution and Claude Code PreToolUse Bash."""

from __future__ import annotations

import subprocess
from typing import Any

from tools.hooks.common import emit, is_claude, read_payload
from tools.hooks.shell_guard import shell_denial


def current_branch() -> str:
    raw = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True)
    return raw.strip()


def command_from_payload(payload: dict[str, Any]) -> str:
    if is_claude(payload):
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
            raise SystemExit("PreToolUse Bash payload has no tool_input.command")
        return tool_input["command"]
    command = payload.get("command")
    if not isinstance(command, str):
        raise SystemExit("beforeShellExecution payload has no command")
    return command


def decision_payload(protocol_claude: bool, reason: str | None) -> dict[str, Any]:
    if protocol_claude:
        output: dict[str, Any] = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny" if reason else "allow",
        }
        if reason is not None:
            output["permissionDecisionReason"] = reason
        return {"hookSpecificOutput": output}
    if reason is None:
        return {"permission": "allow"}
    return {"permission": "deny", "user_message": reason, "agent_message": reason}


def main() -> int:
    payload = read_payload()
    reason = shell_denial(command_from_payload(payload), current_branch=current_branch())
    emit(decision_payload(is_claude(payload), reason))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
