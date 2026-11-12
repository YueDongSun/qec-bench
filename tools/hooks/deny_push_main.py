"""pre-push hook: refuse updates to ``refs/heads/main``."""

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.hooks.policy import denied_push  # noqa: E402


def current_branch() -> str:
    """Return the current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    """Read pre-push stdin and refuse a destination of ``main``."""
    reason = denied_push(sys.stdin.read(), current_branch())
    if reason is not None:
        print(reason, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
