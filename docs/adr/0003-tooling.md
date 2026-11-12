# 3. Tooling

## Status

Accepted

## Context

Local `make check` is the source of truth (governance spec section 7). Dependencies are pinned and installed with uv. The scientific stack is Stim, PyMatching, and Mitiq. Mitiq 1.1.0 requires `cirq-core` as its frontend, so `cirq-core` is a direct pin. Qiskit is not a Mitiq core dependency and is not pinned.

## Decision

- Python 3.11. `uv.lock` is committed. Direct dependencies use `==` pins.
- Ruff formats and lints with rule set E, F, W, I, B, UP, SIM, RUF, N, PL, line length 100. Lint does not pass `--fix` in `make lint` or CI.
- `mypy --strict` covers `src/` only.
- Pytest uses `--strict-markers`. Tests that run a task solution are marked `slow`. `make test` skips them. `make check` runs them.
- Git hooks are installed by `make setup` through pre-commit: pre-commit, commit-msg, and pre-push. pre-push refuses `main` and runs `make check`.
- Cursor (`.cursor/hooks.json`) and Claude Code (`.claude/settings.json`) call the same Python scripts in `tools/hooks/`.
- Shell hooks refuse `git push --force` (including `--force-with-lease` and `-f`), `git push` to `main`, `git commit --no-verify` (including `-n`), `git reset --hard` when the current branch is `main` or the target is `main`, any command that sets `OWNER_SPEC_EDIT`, and `pip install` / `python -m pip install` / `uv pip install`. Dependencies are added with `uv add`.
- Edits under `spec/` or `data/gold/` are denied. Reads are allowed, because an agent must be able to quote a spec line.
- The stop hook runs `make check` and, on failure, tells the agent to keep working.

Pinned direct versions at M0: `stim==1.16.0`, `pymatching==2.4.0`, `mitiq==1.1.0`, `cirq-core==1.6.1`.

## Consequences

A push that has not passed `make check` is refused by the pre-push hook. CI runs the same `make check`. If CI is unavailable, the local output in the PR body decides.
