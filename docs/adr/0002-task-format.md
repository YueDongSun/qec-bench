# 0002. Task format

## Status

Accepted

## Context

Tasks follow a Terminal-Bench-style directory so an agent under test can be
graded by a hidden verifier. Milestone M0 needs that directory, a scaffolder,
and one format demo. `spec/` does not yet state families, tolerances, or
acceptance rules, so the demo cannot be a scientific task.

## Decision

Each `tasks/<task_id>/` directory contains:

- `task.toml` with `id`, `family`, `difficulty` (`easy`, `medium`, or `hard`),
  `spec_reference` (`spec/<FILE>.md#<anchor>`), `author`, `status` (`draft` or
  `ready`), optional `format_demo` (boolean), and `[timeouts]` with `run_sec`
  (positive integer, seconds, engineering limit).
- `instruction.md`: the statement shown to the agent under test. No hidden-test
  details and no answers.
- `environment/Dockerfile`: one `FROM` image with a pinned tag that contains a
  digit and is not `latest`. No network at test time once the runner exists.
- `solution/solve.sh`: the reference solution. It must pass `tests/`.
- `tests/test_outputs.py`: the hidden verifier. It reads `TASK_OUTPUT_DIR`.

Task ids match `<family>_<nnn>_<slug>` in snake_case, with exactly one
three-digit group, for example `example_000_smoke` and
`cf_t2_001_laf3_er_levels`. `family` in `task.toml` must equal the family in
the id. The directory name equals `id`.

`example_000_smoke` is a format demo (`format_demo = true`, `status = draft`).
Its solution writes `output.json` from `qecbench.reference.smoke.payload`.
The verifier checks exact equality with that object. `demo_token` is a
dimensionless scaffold token, not a physical observable. A format demo cannot
be `status = ready`.

The tolerance model, including any line format in `spec/TOLERANCES.md`, is
TBD by owner (TODO(owner)). This record does not define one.

`make validate` checks every task directory: structure, the solution's tests
pass, and a do-nothing run (no `solve.sh`) fails the tests.

`tools/new_task.py <task_id>` creates a draft whose placeholder solution writes
`{"scaffold_token": 1}`. That token is the same kind of non-physical marker.
Replace it with a spec-backed verifier before `status = ready`.

The M0 Docker image is `python:3.12.12-slim-bookworm`. It is a pinned base for
the format demo and the scaffolder. It does not pin Stim, PyMatching, or
mitiq. Local `make validate` runs `solve.sh` on the host with the project
environment. Running tasks inside Docker is later engineering.

## Consequences

Scientific tasks stay blocked until the owner fills `spec/`. The format demo
keeps `make validate` honest without inventing a tolerance. Changing this
layout or the public names (`payload`, `validate_task_dir`,
`run_task`, `check_all`, `create_task`) requires a new ADR.
