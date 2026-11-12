"""Create a task directory skeleton. Does not invent task science."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

_TASK_ID_PARTS = 3


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python tools/new_task.py <family-nnn-slug>", file=sys.stderr)
        return 2
    task_id = argv[0]
    error = task_id_error(task_id)
    if error is not None:
        print(error, file=sys.stderr)
        return 2
    root = Path("tasks") / task_id
    if root.exists():
        print(f"{root} already exists", file=sys.stderr)
        return 1
    _write_tree(root, task_id)
    print(f"scaffolded {root}")
    print("Fill instruction.md from the spec section in task.toml. Do not edit spec/.")
    return 0


def task_id_error(task_id: str) -> str | None:
    parts = task_id.split("-")
    if len(parts) < _TASK_ID_PARTS:
        return "task id must be <family>-<nnn>-<slug>"
    family, number, slug = parts[0], parts[1], "-".join(parts[2:])
    if not family.isascii() or not family.isalnum() or not family.islower():
        return "family must be lowercase ascii letters or digits"
    if len(number) != _TASK_ID_PARTS or not number.isdigit():
        return "the middle component must be three digits"
    if slug == "" or not all(part.isalnum() and part.islower() for part in slug.split("-")):
        return "slug must be lowercase ascii words separated by hyphens"
    return None


def _write_tree(root: Path, task_id: str) -> None:
    (root / "environment").mkdir(parents=True)
    (root / "solution").mkdir()
    (root / "tests").mkdir()
    (root / "task.toml").write_text(_task_toml(task_id), encoding="utf-8")
    (root / "instruction.md").write_text(_instruction(task_id), encoding="utf-8")
    (root / "environment" / "Dockerfile").write_text(_dockerfile(), encoding="utf-8")
    solve = root / "solution" / "solve.sh"
    solve.write_text(_solve(), encoding="utf-8")
    solve.chmod(solve.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    (root / "tests" / "test_outputs.py").write_text(_tests(), encoding="utf-8")


def _task_toml(task_id: str) -> str:
    family = task_id.split("-", 1)[0]
    return (
        f'id = "{task_id}"\n'
        f'family = "{family}"\n'
        'difficulty = "TODO"\n'
        'spec_ref = "spec/TASKS.md#task-families"\n'
        'author = "TODO"\n'
        'status = "draft"\n'
        "\n"
        "[timeouts]\n"
        "sec = 120\n"
    )


def _instruction(task_id: str) -> str:
    return (
        f"# {task_id}\n"
        "\n"
        "TODO: state what the agent under test must produce.\n"
        "Do not include hidden-test details or answers.\n"
        "Name any tolerance from spec/TOLERANCES.md. Do not hard-code one.\n"
    )


def _dockerfile() -> str:
    return (
        "FROM python:3.11.18-slim-bookworm\n"
        "\n"
        "# Pin the same direct versions as pyproject.toml. No network at test time.\n"
        "RUN pip install --no-cache-dir \\\n"
        "    stim==1.16.0 \\\n"
        "    pymatching==2.4.0 \\\n"
        "    mitiq==1.1.0 \\\n"
        "    cirq-core==1.6.1 \\\n"
        "    numpy==2.2.6 \\\n"
        "    scipy==1.17.1 \\\n"
        "    pytest==9.2.0\n"
    )


def _solve() -> str:
    return '#!/bin/sh\nset -eu\necho "TODO: reference solution" >&2\nexit 1\n'


def _tests() -> str:
    return (
        "import os\n"
        "from pathlib import Path\n"
        "\n"
        "\n"
        "def test_output_exists() -> None:\n"
        '    """Replace this with the real verifier. Read tolerances from spec/ by name."""\n'
        '    report = Path(os.environ["OUTPUT_DIR"]) / "result.json"\n'
        "    assert report.is_file()\n"
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
