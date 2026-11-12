"""pre-commit ruff lint. ``--fix`` is off when ``CI=true``."""

import os
import subprocess
import sys
from pathlib import Path


def ruff_check_command(files: list[str], *, ci: bool) -> list[str]:
    """Build the ``uv run ruff check`` command for these files."""
    uv = Path(__file__).with_name("uv.sh")
    command = [str(uv), "run", "ruff", "check"]
    if not ci:
        command.append("--fix")
    command.extend(files)
    return command


def main() -> None:
    """Lint the paths pre-commit passes on argv."""
    ci = os.environ.get("CI") == "true"
    raise SystemExit(subprocess.call(ruff_check_command(sys.argv[1:], ci=ci)))


if __name__ == "__main__":
    main()
