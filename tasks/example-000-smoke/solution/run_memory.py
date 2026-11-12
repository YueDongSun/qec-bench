"""FORMAT DEMO. Run one repetition-code memory experiment and report a logical error rate.

Demo parameters come from ``task.toml``. They are not a noise-model convention.
Pass thresholds are ``spec/TOLERANCES.md`` (TODO(owner)). This script does not apply one.
"""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path

import pymatching
import stim


def main() -> None:
    task_dir = Path(os.environ["TASK_DIR"])
    output_dir = Path(os.environ["OUTPUT_DIR"])
    with (task_dir / "task.toml").open("rb") as handle:
        demo = tomllib.load(handle)["demo"]
    circuit = stim.Circuit.generated(
        str(demo["circuit"]),
        rounds=int(demo["rounds"]),
        distance=int(demo["distance"]),
        before_round_data_depolarization=float(demo["before_round_data_depolarization"]),
    )
    sampler = circuit.compile_detector_sampler(seed=int(demo["seed"]))
    detection_events, observable_flips = sampler.sample(
        int(demo["shots"]),
        separate_observables=True,
    )
    matching = pymatching.Matching.from_detector_error_model(
        circuit.detector_error_model(decompose_errors=True)
    )
    predictions = matching.decode_batch(detection_events)
    errors = int((predictions != observable_flips).any(axis=1).sum())
    shots = int(demo["shots"])
    report = {
        "circuit": str(demo["circuit"]),
        "seed": int(demo["seed"]),
        "shots": shots,
        "errors": errors,
        "logical_error_rate": errors / shots,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "result.json").write_text(json.dumps(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
