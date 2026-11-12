"""Named tolerances from ``spec/TOLERANCES.md``.

When the owner fills a value, the line format (ADR 0002) is::

    - `name`: abs=<float>, rel=<float>

This module does not choose how ``abs`` and ``rel`` combine and does not
supply a missing number. Statistical acceptance is ``spec/SCIENCE.md``.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from qecbench.repo import repo_root

_LINE = re.compile(
    r"^- `(?P<name>[a-z][a-z0-9_]*)`: "
    r"abs=(?P<abs>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?), "
    r"rel=(?P<rel>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)$"
)


class ToleranceFileError(Exception):
    """``spec/TOLERANCES.md`` has a tolerance bullet the loader cannot parse."""


class ToleranceNotDefinedError(Exception):
    """The owner has not defined this name in ``spec/TOLERANCES.md``."""


@dataclass(frozen=True)
class Tolerance:
    """Absolute and relative numbers for one named observable.

    Both fields are dimensionless as written by the owner. Their meaning is
    the named row in ``spec/TOLERANCES.md``, not a value chosen here.
    """

    name: str
    abs: float
    rel: float


def tolerances_path() -> Path:
    """Return the owner tolerance file for this checkout."""
    return repo_root() / "spec" / "TOLERANCES.md"


def load_tolerances(spec_path: Path | None = None) -> dict[str, Tolerance]:
    """Parse every named tolerance.

    Raises ``ToleranceFileError`` on a malformed bullet or a duplicate name.
    Returns an empty mapping when the owner has not added any bullets.
    """
    path = tolerances_path() if spec_path is None else spec_path
    if not path.is_file():
        raise ToleranceFileError(f"missing {path}")
    found: dict[str, Tolerance] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("- `"):
            continue
        match = _LINE.fullmatch(line)
        if match is None:
            raise ToleranceFileError(f"malformed tolerance line in {path}: {line}")
        name = match.group("name")
        if name in found:
            raise ToleranceFileError(f"duplicate tolerance `{name}` in {path}")
        found[name] = Tolerance(
            name=name,
            abs=float(match.group("abs")),
            rel=float(match.group("rel")),
        )
    return found


def load_tolerance(name: str, *, spec_path: Path | None = None) -> Tolerance:
    """Return one named tolerance.

    Raises ``ToleranceNotDefinedError`` when the name is absent. Quote that
    gap in a ``needs-science-decision`` issue and stop. Do not guess a number.
    """
    found = load_tolerances(spec_path)
    if name not in found:
        location = tolerances_path() if spec_path is None else spec_path
        raise ToleranceNotDefinedError(
            f"tolerance `{name}` is not defined in {location}. "
            "Quote that line in a needs-science-decision issue and stop."
        )
    return found[name]
