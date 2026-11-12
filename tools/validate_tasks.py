"""``make validate`` entry point."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from qecbench.repo import repo_root  # noqa: E402
from qecbench.taskfmt.run import check_all  # noqa: E402


def main() -> None:
    """Check every task directory. A format error exits non-zero."""
    check_all(repo_root())


if __name__ == "__main__":
    main()
