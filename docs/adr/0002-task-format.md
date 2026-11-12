# 2. Task format

## Status

Accepted

## Context

Tasks are execution-graded and Terminal-Bench shaped. The layout is fixed so agents can add tasks without inventing a second format. Pass thresholds are names in `spec/TOLERANCES.md`, which is still TODO(owner). This ADR does not choose those thresholds.

## Decision

Each `tasks/<family>-<nnn>-<slug>/` directory contains:

- `task.toml` with `id`, `family`, `difficulty`, `spec_ref` (a `spec/...` path), `author`, `status` (`draft` or `ready`), and `[timeouts] sec` (positive integer, seconds).
- `instruction.md` for the agent under test, with no hidden-test details and no answers.
- `environment/Dockerfile` starting with `FROM`, with package versions pinned. No network at test time.
- `solution/solve.sh`, executable, the reference solution.
- `tests/test_outputs.py`, the hidden verifier.

`tools/new_task.py` creates that skeleton. `make validate` checks the structure, runs the reference solution and requires the verifier to pass, then runs the verifier with no solution output and requires it to fail.

The reference solution and the verifier share three environment variables set by the local runner: `TASK_DIR` (the task directory), `TASK_ROOT` (an empty workspace), and `OUTPUT_DIR` (where the solution writes `result.json`).

`example-000-smoke` is the format demo required by milestone M0. Its id matches `<family>-<nnn>-<slug>`. It is not a scientific task: the verifier checks the report schema and does not apply a logical-error-rate threshold. Demo circuit parameters live only in that task's `task.toml` and are not a noise-model convention.

## Consequences

A verifier that passes on an empty workspace is a failed task. Tolerances, once the owner names them, are read from `spec/TOLERANCES.md` by name and are not hard-coded magic numbers.
