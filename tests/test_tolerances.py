"""Named tolerances come only from the owner file."""

from pathlib import Path

import pytest

from qecbench.repo import repo_root
from qecbench.verify.tolerances import (
    ToleranceFileError,
    ToleranceNotDefinedError,
    load_tolerance,
    load_tolerances,
)


def test_shipped_tolerance_file_defines_nothing() -> None:
    path = repo_root() / "spec" / "TOLERANCES.md"
    assert load_tolerances(path) == {}
    with pytest.raises(ToleranceNotDefinedError, match="needs-science-decision"):
        load_tolerance("example_000_smoke", spec_path=path)


def test_loader_reads_a_named_line(tmp_path: Path) -> None:
    path = tmp_path / "TOLERANCES.md"
    path.write_text(
        "# Tolerances\n\n## Tolerances\n\n- `demo_bound`: abs=0.25, rel=1e-3\n",
        encoding="utf-8",
    )
    found = load_tolerance("demo_bound", spec_path=path)
    assert found.name == "demo_bound"
    assert found.abs == float("0.25")
    assert found.rel == float("1e-3")


def test_malformed_bullet_fails(tmp_path: Path) -> None:
    path = tmp_path / "TOLERANCES.md"
    path.write_text("- `demo_bound`: maybe\n", encoding="utf-8")
    with pytest.raises(ToleranceFileError, match="malformed"):
        load_tolerances(path)


def test_duplicate_name_fails(tmp_path: Path) -> None:
    path = tmp_path / "TOLERANCES.md"
    path.write_text(
        "- `demo_bound`: abs=0, rel=0\n- `demo_bound`: abs=1, rel=0\n",
        encoding="utf-8",
    )
    with pytest.raises(ToleranceFileError, match="duplicate"):
        load_tolerances(path)
