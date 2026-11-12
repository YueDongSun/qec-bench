"""Validate Terminal-Bench-style task directories.

The file layout is ``docs/adr/0002-task-format.md``. Numeric pass criteria are
not applied here; those names will come from ``spec/TOLERANCES.md`` (TODO(owner)).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

REQUIRED_FILES: tuple[str, ...] = (
    "task.toml",
    "instruction.md",
    "environment/Dockerfile",
    "solution/solve.sh",
    "tests/test_outputs.py",
)
REQUIRED_KEYS: tuple[str, ...] = (
    "id",
    "family",
    "difficulty",
    "spec_ref",
    "author",
    "status",
)
TASK_STATUSES: frozenset[str] = frozenset({"draft", "ready"})
_TASK_ID = re.compile(r"^[a-z0-9]+-\d{3}-[a-z0-9-]+$")


class TaskFormatError(Exception):
    """A task directory does not match the format, or its verifier is vacuous."""


def validate_all(tasks_root: Path) -> None:
    """Validate every immediate subdirectory of ``tasks_root``."""
    task_dirs = sorted(path for path in tasks_root.iterdir() if path.is_dir())
    if not task_dirs:
        raise TaskFormatError(f"no task directories under {tasks_root}")
    for task_dir in task_dirs:
        validate_task(task_dir)


def validate_task(task_dir: Path) -> None:
    """Check structure, that the reference solution passes, and that doing nothing fails."""
    task_dir = task_dir.resolve()
    cfg = check_structure(task_dir)
    solution = _run_tests(task_dir, cfg, run_solution=True)
    if solution.returncode != 0:
        message = (
            f"{task_dir.name}: reference solution failed tests\n"
            f"{solution.stdout}\n{solution.stderr}"
        )
        raise TaskFormatError(message)
    empty = _run_tests(task_dir, cfg, run_solution=False)
    if empty.returncode == 0:
        raise TaskFormatError(
            f"{task_dir.name}: tests passed with no solution output; verifier is vacuous"
        )


def check_structure(task_dir: Path) -> dict[str, Any]:
    """Return the parsed ``task.toml`` when the directory has the required files and keys."""
    task_dir = task_dir.resolve()
    missing = [rel for rel in REQUIRED_FILES if not (task_dir / rel).is_file()]
    if missing:
        raise TaskFormatError(f"{task_dir.name}: missing {missing}")
    solve = task_dir / "solution" / "solve.sh"
    if not os.access(solve, os.X_OK):
        raise TaskFormatError(f"{task_dir.name}: solution/solve.sh is not executable")
    dockerfile = (task_dir / "environment" / "Dockerfile").read_text(encoding="utf-8")
    if not dockerfile.startswith("FROM "):
        raise TaskFormatError(f"{task_dir.name}: environment/Dockerfile must start with FROM")
    with (task_dir / "task.toml").open("rb") as handle:
        cfg: dict[str, Any] = tomllib.load(handle)
    missing_keys = [key for key in REQUIRED_KEYS if key not in cfg]
    if missing_keys:
        raise TaskFormatError(f"{task_dir.name}: task.toml missing {missing_keys}")
    _check_identity(task_dir, cfg)
    _check_timeout(task_dir, cfg)
    return cfg


def _check_identity(task_dir: Path, cfg: dict[str, Any]) -> None:
    task_id = cfg["id"]
    if not isinstance(task_id, str) or _TASK_ID.fullmatch(task_id) is None:
        raise TaskFormatError(f"{task_dir.name}: id {task_id!r} is not <family>-<nnn>-<slug>")
    if task_id != task_dir.name:
        raise TaskFormatError(f"{task_dir.name}: task.toml id is {task_id!r}")
    for key in ("family", "difficulty", "author"):
        value = cfg[key]
        if not isinstance(value, str) or value == "":
            raise TaskFormatError(f"{task_dir.name}: task.toml {key} must be a non-empty string")
    spec_ref = cfg["spec_ref"]
    if not isinstance(spec_ref, str) or not spec_ref.startswith("spec/"):
        raise TaskFormatError(f"{task_dir.name}: spec_ref must point at spec/")
    status = cfg["status"]
    if status not in TASK_STATUSES:
        raise TaskFormatError(f"{task_dir.name}: status {status!r} is not draft or ready")


def _check_timeout(task_dir: Path, cfg: dict[str, Any]) -> None:
    timeouts = cfg.get("timeouts")
    if not isinstance(timeouts, dict):
        raise TaskFormatError(f"{task_dir.name}: [timeouts] sec must be an int")
    sec = timeouts.get("sec")
    if isinstance(sec, bool) or not isinstance(sec, int) or sec <= 0:
        raise TaskFormatError(f"{task_dir.name}: [timeouts] sec must be a positive int")


def run_without_solution(task_dir: Path) -> subprocess.CompletedProcess[str]:
    """Run the task tests in an empty workspace and return the pytest process result."""
    task_dir = task_dir.resolve()
    cfg = check_structure(task_dir)
    return _run_tests(task_dir, cfg, run_solution=False)


def _run_tests(
    task_dir: Path,
    cfg: dict[str, Any],
    *,
    run_solution: bool,
) -> subprocess.CompletedProcess[str]:
    timeout = cfg["timeouts"]["sec"]
    if isinstance(timeout, bool) or not isinstance(timeout, int):
        raise TaskFormatError(f"{task_dir.name}: [timeouts] sec must be an int")
    with tempfile.TemporaryDirectory(prefix="qecbench-task-") as raw:
        workspace = Path(raw)
        env = os.environ.copy()
        env["TASK_DIR"] = str(task_dir.resolve())
        env["OUTPUT_DIR"] = str(workspace / "output")
        env["TASK_ROOT"] = str(workspace)
        if run_solution:
            _run_solution(task_dir, workspace, env, timeout)
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", str(task_dir / "tests")],
            cwd=workspace,
            env=env,
            check=False,
            timeout=timeout,
            capture_output=True,
            text=True,
        )


def _run_solution(task_dir: Path, workspace: Path, env: dict[str, str], timeout: int) -> None:
    completed = subprocess.run(
        ["bash", str(task_dir / "solution" / "solve.sh")],
        cwd=workspace,
        env=env,
        check=False,
        timeout=timeout,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = (
            f"{task_dir.name}: solution/solve.sh exited {completed.returncode}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
        raise TaskFormatError(message)
