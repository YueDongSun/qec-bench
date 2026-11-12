"""pre-commit hook: 500 KiB, with ``data/gold/`` allowed up to 5 MiB."""

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.hooks.policy import size_limit  # noqa: E402


def staged_paths() -> list[str]:
    """Return added, copied, modified, or renamed paths in the index."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def staged_size(path: str) -> int:
    """Return the staged blob size of ``path`` in bytes."""
    result = subprocess.run(
        ["git", "cat-file", "-s", f":{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip())


def oversized(paths: list[tuple[str, int]]) -> list[str]:
    """Return human-readable failures for paths over their limit."""
    failures: list[str] = []
    for path, size in paths:
        limit = size_limit(path)
        if size > limit:
            failures.append(f"{path} is {size} bytes; limit is {limit} bytes")
    return failures


def main() -> None:
    """Reject staged blobs over the large-file policy."""
    failures = oversized([(path, staged_size(path)) for path in staged_paths()])
    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
