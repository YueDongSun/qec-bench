"""Format a Python edit, or reject an edit under spec/ or data/gold/.

Cursor afterFileEdit and Claude Code PostToolUse on Edit|Write.
"""

from __future__ import annotations

import subprocess
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


def revert_owner_edit(path: Path, *, root: Path) -> None:
    """Restore a tracked owner-only file, or delete an untracked one."""
    rel = path.resolve().relative_to(root.resolve())
    restored = subprocess.run(
        ["git", "checkout", "--", rel.as_posix()],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if restored.returncode == 0:
        return
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", rel.as_posix()],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if tracked.returncode != 0 and path.is_file():
        path.unlink()
        return
    raise SystemExit(restored.stderr.strip() or f"failed to revert {rel.as_posix()}")


def format_python(path: Path) -> None:
    if path.suffix != ".py" or not path.is_file():
        return
    subprocess.run(["uv", "run", "ruff", "format", str(path)], check=True)


def response(*, denied: bool, claude: bool) -> dict[str, Any]:
    if not denied:
        return {}
    if claude:
        return {"decision": "block", "reason": OWNER_EDIT_MESSAGE}
    return {
        "permission": "deny",
        "user_message": OWNER_EDIT_MESSAGE,
        "agent_message": OWNER_EDIT_MESSAGE,
    }


def main() -> int:
    payload = read_payload()
    raw = file_path_from_payload(payload)
    if raw is None:
        raise SystemExit("edit hook payload has no file_path")
    path = Path(raw)
    root = git_root()
    claude = is_claude(payload)
    if is_owner_only(path, root=root):
        revert_owner_edit(path, root=root)
        emit(response(denied=True, claude=claude))
        return 2
    format_python(path)
    if claude:
        return 0
    emit({"permission": "allow"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
