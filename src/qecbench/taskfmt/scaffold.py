"""Create a draft task directory. See ``docs/adr/0002-task-format.md``."""

from pathlib import Path

from qecbench.taskfmt.validate import BASE_IMAGE, DEFAULT_RUN_SEC, TaskFormatError, parse_task_id


def create_task(task_id: str, *, root: Path) -> Path:
    """Create ``tasks/<task_id>/`` and return that directory.

    The placeholder verifier is intentionally non-scientific. Replace it
    before setting ``status = "ready"``.
    """
    family, _number, _slug = parse_task_id(task_id)
    task_dir = root / "tasks" / task_id
    if task_dir.exists():
        raise TaskFormatError(f"{task_dir} already exists")
    (task_dir / "environment").mkdir(parents=True)
    (task_dir / "solution").mkdir()
    (task_dir / "tests").mkdir()
    (task_dir / "task.toml").write_text(
        "\n".join(
            [
                "# Draft scaffold. Not a scientific task. See docs/adr/0002-task-format.md.",
                f'id = "{task_id}"',
                f'family = "{family}"',
                'difficulty = "easy"',
                'spec_reference = "spec/TASKS.md#task-families"',
                'author = "qecbench"',
                'status = "draft"',
                "format_demo = false",
                "",
                "[timeouts]",
                f"run_sec = {DEFAULT_RUN_SEC}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (task_dir / "instruction.md").write_text(
        "\n".join(
            [
                f"# {task_id}",
                "",
                "Draft scaffold. This is not a scientific task.",
                "",
                "Replace this instruction with the statement the agent under test should see.",
                "Do not include hidden-test details or answers.",
                "",
                "The placeholder solution writes `output.json` with a scaffold token so the",
                "verifier is not vacuous. Replace `tests/test_outputs.py` with a deterministic",
                "check that loads a named tolerance from `spec/TOLERANCES.md` before setting",
                '`status = "ready"`. If the tolerance or convention is missing, open a',
                "`needs-science-decision` issue and stop.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (task_dir / "environment" / "Dockerfile").write_text(
        "\n".join(
            [
                f"FROM {BASE_IMAGE}",
                "",
                "# Pinned base for a draft task. Do not add unpinned installs.",
                "# Test-time network stays disabled once the Docker runner exists.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    solve = task_dir / "solution" / "solve.sh"
    solve.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'if [[ -z "${TASK_OUTPUT_DIR:-}" ]]; then',
                '  echo "TASK_OUTPUT_DIR is not set" >&2',
                "  exit 1",
                "fi",
                "printf '%s\\n' '{\"scaffold_token\": 1}' > \"${TASK_OUTPUT_DIR}/output.json\"",
                "",
            ]
        ),
        encoding="utf-8",
    )
    solve.chmod(0o755)
    (task_dir / "tests" / "test_outputs.py").write_text(
        "\n".join(
            [
                '"""Placeholder verifier for a draft task. Not a scientific check."""',
                "",
                "import json",
                "import os",
                "from pathlib import Path",
                "",
                "SCAFFOLD_TOKEN = 1",
                "",
                "",
                "def test_scaffold_marker() -> None:",
                '    path = Path(os.environ["TASK_OUTPUT_DIR"]) / "output.json"',
                '    observed = json.loads(path.read_text(encoding="utf-8"))',
                '    assert observed == {"scaffold_token": SCAFFOLD_TOKEN}',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return task_dir
