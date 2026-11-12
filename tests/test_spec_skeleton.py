"""The owner has not written science yet. Keep spec/ to headings and TODO markers."""

from pathlib import Path

from qecbench.repo import repo_root

_REQUIRED = {
    "SCIENCE.md": (
        "## Scope",
        "## Noise models",
        "## Code and decoder conventions",
        "## Mitigation targets",
        "## Statistical acceptance (shots, seeds, confidence)",
    ),
    "TASKS.md": ("## Task families",),
    "TOLERANCES.md": ("## Tolerances",),
    "SOURCES.md": ("## Sources",),
}


def test_spec_files_are_headings_and_owner_todos() -> None:
    spec_dir = repo_root() / "spec"
    assert sorted(path.name for path in spec_dir.glob("*.md")) == sorted(_REQUIRED)
    for name, headings in _REQUIRED.items():
        text = (spec_dir / name).read_text(encoding="utf-8")
        for heading in headings:
            assert heading in text.splitlines()
        for line in text.splitlines():
            if line.startswith("#") or line.strip() == "":
                continue
            assert line.strip() == "TODO(owner)"
            assert not any(char.isdigit() for char in line)


def test_spec_paths_are_the_contract_files() -> None:
    present = {path.name for path in (repo_root() / "spec").iterdir()}
    assert present == set(_REQUIRED)
    assert (repo_root() / "data" / "gold").is_dir()
    assert Path(repo_root() / "CLAUDE.md").is_symlink()
