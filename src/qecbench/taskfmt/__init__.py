"""Task-format validator, local runner, and scaffolder.

The directory contract is ``docs/adr/0002-task-format.md``.
"""

from qecbench.taskfmt.run import check_all, run_task
from qecbench.taskfmt.scaffold import create_task
from qecbench.taskfmt.validate import TaskFormatError, validate_task_dir

__all__ = [
    "TaskFormatError",
    "check_all",
    "create_task",
    "run_task",
    "validate_task_dir",
]
