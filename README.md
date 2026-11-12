# qec-bench

Execution-graded agent benchmark for quantum error correction and error mitigation. Agents under test design decoders or codes with Stim and PyMatching, or apply error mitigation with Mitiq. Scoring is logical error rate or expectation-value error under a noise model, with fixed seeds and shot budgets. The scientific definitions are not written yet (`spec/` is owner-only).

## Status

| Milestone | Status |
| --- | --- |
| M0 scaffold | in review |
| M1 reference solvers, verifiers, docker base | not started |

`tasks/example-000-smoke` is a format demo: a repetition-code memory experiment runs and reports a logical error rate. It has no pass threshold.

## Quickstart

```bash
make setup && make check
```

`make check` runs the formatter check, ruff, mypy, pytest (including slow tests), and `make validate`.

## Add a task

```bash
uv run python tools/new_task.py <family>-<nnn>-<slug>
```

Then fill the task from the spec section named in `task.toml`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Contract

- [AGENTS.md](AGENTS.md) — rules for agents and humans
- [spec/](spec/) — scientific definitions (owner-only, currently `TODO(owner)` headings)
- [docs/adr/](docs/adr/) — architecture decisions
