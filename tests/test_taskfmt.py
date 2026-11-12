"""Unit tests for task-format checks and the task scaffolder."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from qecbench.taskfmt.validate import TaskFormatError, check_structure, validate_task
from tools.new_task import main, task_id_error

_SOLVE = """#!/bin/sh
set -eu
mkdir -p "$OUTPUT_DIR"
echo '{"ok": true}' > "$OUTPUT_DIR/result.json"
"""

_TEST_PRESENT = """import os
from pathlib import Path

def test_report() -> None:
    assert (Path(os.environ["OUTPUT_DIR"]) / "result.json").is_file()
"""

_TEST_VACUOUS = """def test_ok() -> None:
    assert True
"""


def _write_task(root: Path, task_id: str, *, test_body: str, solve_body: str = _SOLVE) -> Path:
    task = root / task_id
    (task / "environment").mkdir(parents=True)
    (task / "solution").mkdir()
    (task / "tests").mkdir()
    (task / "task.toml").write_text(
        "\n".join(
            [
                f'id = "{task_id}"',
                'family = "example"',
                'difficulty = "smoke"',
                'spec_ref = "spec/TASKS.md#task-families"',
                'author = "test"',
                'status = "draft"',
                "",
                "[timeouts]",
                "sec = 60",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (task / "instruction.md").write_text("# demo\n", encoding="utf-8")
    (task / "environment" / "Dockerfile").write_text(
        "FROM python:3.11.18-slim-bookworm\n", encoding="utf-8"
    )
    solve = task / "solution" / "solve.sh"
    solve.write_text(solve_body, encoding="utf-8")
    solve.chmod(solve.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    (task / "tests" / "test_outputs.py").write_text(test_body, encoding="utf-8")
    return task


def test_task_id_rules() -> None:
    assert task_id_error("decoding-001-repetition-memory") is None
    assert task_id_error("example-000-smoke") is None
    assert task_id_error("Nope") is not None
    assert task_id_error("dec-01-x") is not None
    assert task_id_error("Dec-001-x") is not None


def test_new_task_scaffolds_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["decoding-001-demo"]) == 0
    created = tmp_path / "tasks" / "decoding-001-demo"
    assert (created / "instruction.md").is_file()
    assert os.access(created / "solution" / "solve.sh", os.X_OK)
    assert main(["decoding-001-demo"]) == 1
    assert main([]) == 2


def test_structure_rejects_a_missing_file(tmp_path: Path) -> None:
    task = _write_task(tmp_path, "example-001-ok", test_body=_TEST_PRESENT)
    (task / "instruction.md").unlink()
    with pytest.raises(TaskFormatError, match="missing"):
        check_structure(task)


def test_validate_accepts_a_solution_and_rejects_a_vacuous_verifier(tmp_path: Path) -> None:
    good = _write_task(tmp_path, "example-002-good", test_body=_TEST_PRESENT)
    validate_task(good)
    vacuous = _write_task(tmp_path, "example-003-vacuous", test_body=_TEST_VACUOUS)
    with pytest.raises(TaskFormatError, match="vacuous"):
        validate_task(vacuous)
