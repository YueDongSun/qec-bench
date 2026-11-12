"""Repository root lookup."""

from pathlib import Path


def repo_root() -> Path:
    """Return the checkout that contains this package and ``spec/``.

    The layout is the one in ``AGENTS.md``. A missing ``spec/`` directory is
    an error, not a prompt to invent a path.
    """
    here = Path(__file__).resolve()
    for path in here.parents:
        if (path / "pyproject.toml").is_file() and (path / "spec").is_dir():
            return path
    raise RuntimeError(f"repository root not found starting from {here}")
