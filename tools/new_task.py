"""Scaffold ``tasks/<task_id>/``. Usage: python tools/new_task.py <task_id>."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from qecbench.repo import repo_root  # noqa: E402
from qecbench.taskfmt.scaffold import create_task  # noqa: E402


def main() -> None:
    """Create one draft task directory and print its path."""
    if len(sys.argv) - 1 != 1:
        raise SystemExit("usage: python tools/new_task.py <task_id>")
    print(create_task(sys.argv[1], root=repo_root()))


if __name__ == "__main__":
    main()
