# qec-bench

Execution-graded agent benchmark for quantum error correction and error mitigation.
A solver designs a decoder or code (Stim and PyMatching) or a mitigation routine
(mitiq). Grading uses logical error rate or expectation-value error against a
target, with the seeds and shot budgets in `spec/`. Those scientific definitions
are not written yet.

## Status

| Item | Status |
| --- | --- |
| M0 scaffold | in review, not merged |
| `spec/` | headings and `TODO(owner)` only |
| Tasks | `example_000_smoke` format demo only |
| Reference solvers, verifier statistics, Docker runner | not started (M1) |

## Quickstart

```bash
make setup && make check
```

`make check` is fmt-check, lint, typecheck, pytest, and `make validate`.

## Add a task

```bash
uv run python tools/new_task.py <family>_<nnn>_<slug>
```

Fill the scaffold from `spec/`, then run `make validate`. If a convention or
tolerance is missing, open a `needs-science-decision` issue and stop.

## Contract

- Agents: [AGENTS.md](AGENTS.md)
- Science: [spec/](spec/)
- Task format: [docs/adr/0002-task-format.md](docs/adr/0002-task-format.md)
