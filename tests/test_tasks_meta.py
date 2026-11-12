"""Every task solution must pass its verifier, and a do-nothing run must not."""

from qecbench.repo import repo_root
from qecbench.taskfmt.run import check_all


def test_every_task_solution_passes_and_empty_run_fails() -> None:
    check_all(repo_root())
