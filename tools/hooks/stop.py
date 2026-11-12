"""Stop hook: make check must pass, or the agent keeps working."""

from __future__ import annotations

import subprocess
from typing import Any

from tools.hooks.common import emit, is_claude, read_payload

_TAIL_LINES = 40


def failure_message(output: str) -> str:
    tail = "\n".join(output.splitlines()[-_TAIL_LINES:])
    return "make check failed. Keep working until it passes.\n" + tail


def stop_response(output: str, *, returncode: int, claude: bool) -> dict[str, Any]:
    if returncode == 0:
        return {}
    reason = failure_message(output)
    if claude:
        return {"decision": "block", "reason": reason}
    return {"followup_message": reason}


def main() -> int:
    payload = read_payload()
    completed = subprocess.run(["make", "check"], check=False, capture_output=True, text=True)
    body = stop_response(
        completed.stdout + completed.stderr,
        returncode=completed.returncode,
        claude=is_claude(payload),
    )
    if body:
        emit(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
