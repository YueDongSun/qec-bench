"""Structural checks for a Terminal-Bench-style task directory."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

_NUMBER_GROUP = re.compile(r"_([0-9]{3})_")
_SNAKE = re.compile(r"[a-z][a-z0-9_]*")
_SPEC_REFERENCE = re.compile(r"spec/[A-Za-z0-9_./-]+#[A-Za-z0-9-]+")
_FROM = re.compile(r"^FROM\s+(\S+)\s*$")
_DIFFICULTIES = frozenset({"easy", "medium", "hard"})
_STATUSES = frozenset({"draft", "ready"})

BASE_IMAGE = "python:3.12.12-slim-bookworm"
DEFAULT_RUN_SEC = 30


class TaskFormatError(Exception):
    """A task directory does not match ADR 0002."""


@dataclass(frozen=True)
class TaskSpec:
    """Fields required by the task format.

    ``run_sec`` is an engineering timeout in seconds, not a physical duration.
    See ``docs/adr/0002-task-format.md``.
    """

    task_id: str
    family: str
    difficulty: str
    spec_reference: str
    run_sec: int
    author: str
    status: str
    format_demo: bool


def parse_task_id(task_id: str) -> tuple[str, str, str]:
    """Return ``(family, number, slug)`` for ``<family>_<nnn>_<slug>``.

    Exactly one three-digit group is allowed, so ``cf_t2_001_laf3_er_levels``
    parses as family ``cf_t2``.
    """
    groups = list(_NUMBER_GROUP.finditer(task_id))
    if len(groups) != 1:
        raise TaskFormatError(f"{task_id} must match <family>_<nnn>_<slug> with one 3-digit group")
    group = groups[0]
    family = task_id[: group.start()]
    slug = task_id[group.end() :]
    if _SNAKE.fullmatch(family) is None or _SNAKE.fullmatch(slug) is None:
        raise TaskFormatError(f"{task_id} must be snake_case <family>_<nnn>_<slug>")
    return family, group.group(1), slug


def _read_toml(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        loaded = cast(dict[str, object], tomllib.load(handle))
    return loaded


def _require_str(data: dict[str, object], key: str, task_id: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or value.strip() == "":
        raise TaskFormatError(f"{task_id}: {key} must be a non-empty string")
    return value


def load_task_spec(task_dir: Path) -> TaskSpec:
    """Read ``task.toml`` and check its fields against the directory name."""
    path = task_dir / "task.toml"
    if not path.is_file():
        raise TaskFormatError(f"{task_dir}: missing task.toml")
    data = _read_toml(path)
    task_id = _require_str(data, "id", task_dir.name)
    if task_dir.name != task_id:
        raise TaskFormatError(f"{task_dir.name}: directory name must equal id {task_id}")
    family, _number, _slug = parse_task_id(task_id)
    declared_family = _require_str(data, "family", task_id)
    if declared_family != family:
        raise TaskFormatError(f"{task_id}: family must be {family}")
    difficulty = _require_str(data, "difficulty", task_id)
    if difficulty not in _DIFFICULTIES:
        raise TaskFormatError(f"{task_id}: difficulty must be easy, medium, or hard")
    spec_reference = _require_str(data, "spec_reference", task_id)
    if _SPEC_REFERENCE.fullmatch(spec_reference) is None:
        raise TaskFormatError(f"{task_id}: spec_reference must be spec/<file>.md#<anchor>")
    author = _require_str(data, "author", task_id)
    status = _require_str(data, "status", task_id)
    if status not in _STATUSES:
        raise TaskFormatError(f"{task_id}: status must be draft or ready")
    timeouts = data.get("timeouts")
    if not isinstance(timeouts, dict):
        raise TaskFormatError(f"{task_id}: timeouts must be a table")
    run_sec = cast(dict[str, object], timeouts).get("run_sec")
    if isinstance(run_sec, bool) or not isinstance(run_sec, int) or run_sec <= 0:
        raise TaskFormatError(f"{task_id}: timeouts.run_sec must be a positive integer")
    format_demo = False
    if "format_demo" in data:
        flag = data["format_demo"]
        if not isinstance(flag, bool):
            raise TaskFormatError(f"{task_id}: format_demo must be a boolean")
        format_demo = flag
    if format_demo and status == "ready":
        raise TaskFormatError(f"{task_id}: a format demo cannot be status ready")
    return TaskSpec(
        task_id=task_id,
        family=family,
        difficulty=difficulty,
        spec_reference=spec_reference,
        run_sec=run_sec,
        author=author,
        status=status,
        format_demo=format_demo,
    )


def _require_file(task_dir: Path, relative: str) -> Path:
    path = task_dir / relative
    if not path.is_file():
        raise TaskFormatError(f"{task_dir.name}: missing {relative}")
    return path


def _check_dockerfile(task_dir: Path) -> None:
    text = _require_file(task_dir, "environment/Dockerfile").read_text(encoding="utf-8")
    images = [
        match.group(1) for line in text.splitlines() if (match := _FROM.match(line)) is not None
    ]
    if len(images) != 1:
        raise TaskFormatError(f"{task_dir.name}: Dockerfile must contain one FROM line")
    image = images[0]
    if ":" not in image:
        raise TaskFormatError(f"{task_dir.name}: base image {image} is not pinned")
    tag = image.split(":", 1)[1]
    if tag in {"", "latest"} or not any(char.isdigit() for char in tag):
        raise TaskFormatError(f"{task_dir.name}: base image tag {tag} is not pinned")


def validate_task_dir(task_dir: Path) -> TaskSpec:
    """Check one task directory. Raise ``TaskFormatError`` on the first miss."""
    spec = load_task_spec(task_dir)
    instruction = _require_file(task_dir, "instruction.md").read_text(encoding="utf-8")
    if instruction.strip() == "":
        raise TaskFormatError(f"{spec.task_id}: instruction.md is empty")
    _check_dockerfile(task_dir)
    _require_file(task_dir, "solution/solve.sh")
    _require_file(task_dir, "tests/test_outputs.py")
    return spec


def task_dirs(root: Path) -> list[Path]:
    """Return task directories under ``root/tasks`` in name order."""
    parent = root / "tasks"
    if not parent.is_dir():
        raise TaskFormatError(f"missing {parent}")
    return sorted(
        path for path in parent.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
