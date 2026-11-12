"""Task ids, the format demo, and the scaffolder."""

import shutil
from pathlib import Path

import pytest

from qecbench.reference.smoke import FORMAT_DEMO_TOKEN, payload
from qecbench.repo import repo_root
from qecbench.taskfmt.run import run_task
from qecbench.taskfmt.scaffold import create_task
from qecbench.taskfmt.validate import (
    BASE_IMAGE,
    DEFAULT_RUN_SEC,
    TaskFormatError,
    parse_task_id,
    validate_task_dir,
)


def test_task_id_grammar() -> None:
    assert parse_task_id("example_000_smoke") == ("example", "000", "smoke")
    assert parse_task_id("cf_t2_001_laf3_er_levels") == ("cf_t2", "001", "laf3_er_levels")
    with pytest.raises(TaskFormatError):
        parse_task_id("Example_000_smoke")
    with pytest.raises(TaskFormatError):
        parse_task_id("example_00_smoke")
    with pytest.raises(TaskFormatError):
        parse_task_id("example_000_smoke_001_again")


def test_format_demo_structure() -> None:
    task_dir = repo_root() / "tasks" / "example_000_smoke"
    spec = validate_task_dir(task_dir)
    assert spec.format_demo is True
    assert spec.status == "draft"
    assert spec.family == "example"
    assert spec.run_sec == DEFAULT_RUN_SEC
    dockerfile = (task_dir / "environment" / "Dockerfile").read_text(encoding="utf-8")
    assert dockerfile.startswith(f"FROM {BASE_IMAGE}\n")
    assert payload() == {"demo_token": FORMAT_DEMO_TOKEN}


def test_unpinned_image_is_rejected(tmp_path: Path) -> None:
    task_dir = tmp_path / "example_000_smoke"
    shutil.copytree(repo_root() / "tasks" / "example_000_smoke", task_dir)
    (task_dir / "environment" / "Dockerfile").write_text("FROM python:latest\n", encoding="utf-8")
    with pytest.raises(TaskFormatError, match="not pinned"):
        validate_task_dir(task_dir)


def test_ready_task_must_name_a_tolerance(tmp_path: Path) -> None:
    task_dir = tmp_path / "example_000_smoke"
    shutil.copytree(repo_root() / "tasks" / "example_000_smoke", task_dir)
    toml = (task_dir / "task.toml").read_text(encoding="utf-8")
    toml = toml.replace('status = "draft"', 'status = "ready"')
    toml = toml.replace("format_demo = true", "format_demo = false")
    (task_dir / "task.toml").write_text(toml, encoding="utf-8")
    with pytest.raises(TaskFormatError, match="load_tolerance"):
        validate_task_dir(task_dir)


def test_scaffold_solution_passes_and_empty_run_fails(tmp_path: Path) -> None:
    created = create_task("example_001_scaffold", root=tmp_path)
    validate_task_dir(created)
    assert run_task(created, empty=False) == 0
    assert run_task(created, empty=True) != 0
    with pytest.raises(TaskFormatError, match="already exists"):
        create_task("example_001_scaffold", root=tmp_path)
