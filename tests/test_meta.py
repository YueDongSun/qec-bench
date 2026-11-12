"""The meta-test runs every committed task, including the empty-workspace check."""

from pathlib import Path

import pytest

from qecbench.taskfmt.validate import validate_all


@pytest.mark.slow
def test_every_task_solution_and_empty_workspace() -> None:
    validate_all(Path(__file__).resolve().parents[1] / "tasks")
