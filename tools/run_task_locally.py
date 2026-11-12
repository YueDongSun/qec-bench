"""Run task validation on the host. Docker is the task environment, not this runner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qecbench.taskfmt.validate import (
    TaskFormatError,
    run_without_solution,
    validate_all,
    validate_task,
)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate task directories locally.")
    parser.add_argument("task_id", nargs="?")
    parser.add_argument("--all", action="store_true", help="validate every tasks/* directory")
    parser.add_argument(
        "--empty",
        action="store_true",
        help="run tests with no solution and propagate pytest's exit code",
    )
    args = parser.parse_args(argv)
    tasks_root = Path("tasks")
    if args.all:
        validate_all(tasks_root)
        print("validate: every task passed structure, solution, and empty-solution checks")
        return 0
    if not args.task_id:
        print("pass a task id or --all", file=sys.stderr)
        return 2
    task_dir = tasks_root / args.task_id
    if args.empty:
        result = run_without_solution(task_dir)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode
    validate_task(task_dir)
    print(f"validate: {args.task_id} passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except TaskFormatError as exc:
        print(f"validate: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
