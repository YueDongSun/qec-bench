"""Run one task on the host. Usage: python tools/run_task_locally.py <task_id> [--empty]."""

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from qecbench.repo import repo_root  # noqa: E402
from qecbench.taskfmt.run import run_task  # noqa: E402


def main() -> None:
    """Run ``solve.sh`` and the verifier, or only the verifier with ``--empty``."""
    parser = argparse.ArgumentParser(description="Run one task locally.")
    parser.add_argument("task_id")
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Do not run solve.sh. A passing verifier is a failure of the task.",
    )
    args = parser.parse_args()
    task_dir = repo_root() / "tasks" / args.task_id
    if not task_dir.is_dir():
        raise SystemExit(f"missing task directory: {task_dir}")
    raise SystemExit(run_task(task_dir, empty=args.empty))


if __name__ == "__main__":
    main()
