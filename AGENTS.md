# Agent contract

This file is the working contract for qec-bench. `CLAUDE.md` points here. The owner's binding document is the shared governance spec; this file is the repo-local copy of the rules that follow from it.

## What this bench is

Agents under test design decoders or codes with Stim and PyMatching, or apply error mitigation with Mitiq, under a noise model the owner defines. Grading is by logical error rate or expectation-value error, with fixed seeds and shot budgets. Those definitions are not written yet.

## Owner-only paths

- `spec/` and `data/gold/` are owner-only.
- Do not edit them. Do not set `OWNER_SPEC_EDIT`.
- If a spec line is missing or ambiguous, open a GitHub issue labelled `needs-science-decision`, quote the exact spec line, list the concrete options, and stop work on that piece.
- Do not guess a convention, tolerance, physical constant, or literature value.

## Where behaviour comes from

Code under `src/`, `tasks/`, `tests/`, `tools/`, and `docs/` must trace to a line in `spec/` or an ADR in `docs/adr/`. A change to the task format, the package public API, or the directory layout needs a new ADR.

## Code

- Python 3.11, uv, committed `uv.lock`. Add dependencies with `uv add`, never `pip install`.
- Ruff (E, F, W, I, B, UP, SIM, RUF, N, PL, line length 100) and `mypy --strict` on `src/`.
- Pytest, `--strict-markers`, explicit seeds. Slow tests use `@pytest.mark.slow`.
- Type hints on `src/`. Docstrings that state a unit or convention point at the spec section.
- No broad `try/except`, no silent fallbacks, no speculative abstraction, no checksum manifests, no notebooks under `src/` or `tasks/`, no live or paid LLM calls in the test suite.
- Numerical code uses numpy/scipy. Do not hard-code a tolerance; read the name from `spec/TOLERANCES.md` once the owner has written it.

## Hooks

`make setup` installs pre-commit, commit-msg, and pre-push. Commit messages are Conventional Commits with a scope from `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`, `spec`. Example: `feat(task): add decoding-001-repetition-memory`.

Do not skip hooks. Do not force-push. Do not push to `main`. Do not `git reset --hard` on `main`. The owner merges.

## Tasks

`uv run python tools/new_task.py <family>-<nnn>-<slug>` scaffolds a task. `make validate` checks structure, requires the reference solution to pass, and requires an empty workspace to fail the verifier.

`tasks/example-000-smoke` is a format demo. It runs a repetition-code memory experiment and reports a logical error rate. It has no pass threshold.

## Branches and PRs

One issue, one branch, one PR. Branch name: `<agent>/<issue-number>-<slug>`. Comment `claim` and add `in-progress` before starting. Stay inside the issue's files. PRs aim for under 400 changed lines excluding `data/` and lockfiles. Rebase on `main`. Do not merge.

PR sections: Issue link; Spec reference; Contract changes; Local check output; What is NOT verified; Open science questions. Update `PROGRESS.md` in the same PR when a milestone or task status changes.

## Checks

`make setup && make check` is the bar. `make check` is format, lint, mypy, pytest (including slow), and validate.
