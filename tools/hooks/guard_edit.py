"""Deny writes under spec/ or data/gold/ before the tool runs.

Used by Cursor preToolUse and Claude Code PreToolUse on Edit|Write|MultiEdit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.hooks.common import (
    OWNER_EDIT_MESSAGE,
    emit,
    file_path_from_payload,
    git_root,
    is_claude,
    is_owner_only,
    read_payload,
)


def decision(path: str | None, *, root: Path, claude: bool) -> dict[str, Any]:
    denied = path is not None and is_owner_only(Path(path), root=root)
    if claude:
        output: dict[str, Any] = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny" if denied else "allow",
        }
        if denied:
            output["permissionDecisionReason"] = OWNER_EDIT_MESSAGE
        return {"hookSpecificOutput": output}
    if not denied:
        return {"permission": "allow"}
    return {
        "permission": "deny",
        "user_message": OWNER_EDIT_MESSAGE,
        "agent_message": OWNER_EDIT_MESSAGE,
    }


def main() -> int:
    payload = read_payload()
    emit(decision(file_path_from_payload(payload), root=git_root(), claude=is_claude(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
