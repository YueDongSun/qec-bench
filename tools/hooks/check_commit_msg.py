"""commit-msg hook: Conventional Commits with a required scope."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.hooks.policy import commit_message_error  # noqa: E402


def main() -> None:
    """Reject a commit message file that breaks the commit contract."""
    if len(sys.argv) - 1 != 1:
        raise SystemExit("usage: check_commit_msg.py <message-file>")
    message = Path(sys.argv[1]).read_text(encoding="utf-8")
    error = commit_message_error(message)
    if error is not None:
        print(error, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
