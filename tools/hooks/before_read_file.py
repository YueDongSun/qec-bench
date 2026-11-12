"""Cursor beforeReadFile. Reads of spec/ are allowed; edits are not.

Agents have to read spec/ in order to quote a line in a needs-science-decision issue.
"""

from __future__ import annotations

from tools.hooks.common import emit, read_payload


def main() -> int:
    read_payload()
    emit({"permission": "allow"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
