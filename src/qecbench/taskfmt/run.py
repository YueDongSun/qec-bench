"""Run a task solution, or a do-nothing directory, against its verifier."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from qecbench.repo import repo_root
from qecbench.taskfmt.validate import TaskFormatError, task_dirs, validate_task_dir


def run_task(task_dir: Path, *, empty: bool, stream: bool = True) -> int:
    """Return the verifier's exit code.

    When ``empty`` is false, ``solution/solve.sh`` runs first and a non-zero
    exit from that script is returned without calling the verifier.
    ``TASK_OUTPUT_DIR`` is a fresh directory. The timeout in ``task.toml`` is
    not applied here; it is recorded for the later Docker runner.
    ``stream`` prints the verifier. ``make validate`` turns it off for the
    do-nothing run, whose failure is the expected result.
    """
    with tempfile.TemporaryDirectory(prefix="qecbench-") as tmp:
        output_dir = Path(tmp)
        env = os.environ.copy()
        env["TASK_OUTPUT_DIR"] = str(output_dir)
        if not empty:
            solution = subprocess.run(
                ["bash", str(task_dir / "solution" / "solve.sh")],
                cwd=task_dir,
                env=env,
                check=False,
            )
            if solution.returncode != 0:
                return solution.returncode
        tests = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--strict-markers",
                str(task_dir / "tests" / "test_outputs.py"),
            ],
            cwd=repo_root(),
            env=env,
            check=False,
            capture_output=not stream,
            text=True,
        )
        return tests.returncode


def check_all(root: Path) -> None:
    """Validate every task, require the solution to pass, and require a do-nothing run to fail."""
    directories = task_dirs(root)
    if not directories:
        raise TaskFormatError(f"no tasks under {root / 'tasks'}")
    for task_dir in directories:
        spec = validate_task_dir(task_dir)
        print(f"validate {spec.task_id}: structure ok")
        solution_code = run_task(task_dir, empty=False)
        if solution_code != 0:
            raise TaskFormatError(f"{spec.task_id}: solution tests exited {solution_code}")
        print(f"validate {spec.task_id}: solution passed")
        empty_code = run_task(task_dir, empty=True, stream=False)
        if empty_code == 0:
            raise TaskFormatError(f"{spec.task_id}: do-nothing run passed tests")
        print(f"validate {spec.task_id}: do-nothing exited {empty_code}")
