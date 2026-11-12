"""Shared path and payload helpers for Cursor and Claude Code hooks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

OWNER_EDIT_MESSAGE = (
    "spec/ and data/gold/ are owner-only. Do not edit them. "
    "Open a GitHub issue labelled needs-science-decision, quote the exact spec line, "
    "list the concrete options, and stop work on that piece."
)


def read_payload() -> dict[str, Any]:
    data = json.load(sys.stdin)
    if not isinstance(data, dict):
        raise SystemExit("hook payload must be a JSON object")
    return data


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")


def git_root() -> Path:
    raw = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True)
    return Path(raw.strip())


def is_owner_only(path: Path, *, root: Path) -> bool:
    """True when ``path`` is inside ``root/spec`` or ``root/data/gold``."""
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return False
    parts = resolved.relative_to(root_resolved).parts
    if parts[:1] == ("spec",):
        return True
    return parts[:2] == ("data", "gold")


def file_path_from_payload(payload: dict[str, Any]) -> str | None:
    direct = payload.get("file_path")
    if isinstance(direct, str):
        return direct
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        nested = tool_input.get("file_path")
        if isinstance(nested, str):
            return nested
    return None


def is_claude(payload: dict[str, Any]) -> bool:
    return payload.get("hook_event_name") in {"PreToolUse", "PostToolUse", "Stop"}
