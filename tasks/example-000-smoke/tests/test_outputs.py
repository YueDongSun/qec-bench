"""FORMAT DEMO verifier.

Confirms a logical-error-rate report exists and is internally consistent.
It does not compare the rate to a threshold. ``spec/TOLERANCES.md`` is TODO(owner).
"""

from __future__ import annotations

import json
import math
import os
import tomllib
from pathlib import Path


def test_logical_error_rate_report() -> None:
    report_path = Path(os.environ["OUTPUT_DIR"]) / "result.json"
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    with (Path(os.environ["TASK_DIR"]) / "task.toml").open("rb") as handle:
        demo = tomllib.load(handle)["demo"]
    assert report["circuit"] == demo["circuit"]
    assert report["seed"] == demo["seed"]
    assert report["shots"] == demo["shots"]
    errors = report["errors"]
    shots = report["shots"]
    assert isinstance(errors, int) and not isinstance(errors, bool)
    assert isinstance(shots, int) and not isinstance(shots, bool)
    rate = report["logical_error_rate"]
    assert isinstance(rate, float)
    assert math.isfinite(rate)
    assert rate == errors / shots
