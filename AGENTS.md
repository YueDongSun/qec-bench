# Agent contract for qec-bench

This file is the contract for agents working on `qec-bench` (package `qecbench`).
`CLAUDE.md` is a symlink to it. The owner, Yuedong Sun (@YueDongSun), writes
the science. Agents build the engineering. Several agents will work in parallel.
Do not drift from this file.

## 1. Division of responsibility

- `spec/` is owner-only. It holds the scientific definitions: physics and maths
  of each task family, conventions (units, operator normalisation, basis order,
  sign conventions), tolerances, gold-data provenance, and the task list.
- Agents never edit `spec/`. If a spec point is missing or ambiguous, open a
  GitHub issue labelled `needs-science-decision`, quote the exact spec line,
  list the concrete options, and stop work on that piece.
- Never guess a convention, tolerance, or physical constant that the spec does
  not state.
- `data/gold/` is owner-only (curated literature values with a citation column).
- Everything else (`src/`, `tasks/`, `tests/`, `tools/`, `docs/`) is agent
  territory, but every behaviour must trace to a line in `spec/` or an ADR in
  `docs/adr/`.

## 2. Layout

```text
AGENTS.md  README.md  PROGRESS.md  CONTRIBUTING.md  CODEOWNERS
pyproject.toml  uv.lock  Makefile  .pre-commit-config.yaml
.cursor/rules/*.mdc  .cursor/hooks.json  .claude/settings.json
.github/PULL_REQUEST_TEMPLATE.md
.github/ISSUE_TEMPLATE/{task.yml,bug.yml,science-decision.yml}
spec/{SCIENCE,TASKS,TOLERANCES,SOURCES}.md
docs/adr/0001-record-architecture-decisions.md
docs/adr/0002-task-format.md
docs/adr/0003-tooling.md
src/qecbench/{reference,verify,taskfmt}/
tasks/<task_id>/
tests/  tools/  data/gold/  notebooks/
```

`make setup | fmt | lint | type | test | validate | check`.
`check` is fmt-check, lint, type, pytest (including slow), and validate.

## 3. Task format

See `docs/adr/0002-task-format.md`. Short version:

- `tasks/<family>_<nnn>_<slug>/` with `task.toml`, `instruction.md`,
  `environment/Dockerfile`, `solution/solve.sh`, `tests/test_outputs.py`.
- The instruction has no hidden-test details and no answers.
- The Dockerfile pins the base image. No network at test time.
- The verifier is deterministic and seeded. Numeric checks for a `ready` task
  load tolerances from `spec/TOLERANCES.md` by name. No hard-coded magic
  numbers.
- `tools/new_task.py` scaffolds a draft. `make validate` checks structure,
  that the solution passes, and that a do-nothing run fails.
- `example_000_smoke` is a format demo. It is not science.

## 4.0 Owner's personal workflow standard

This section overrides a tool's default habits.

- snake_case for every project-owned path and identifier (directories, modules,
  task ids, scripts, labels where possible).
- Keep external or required names at their boundaries: `AGENTS.md`, `README.md`,
  `Dockerfile`, `pyproject.toml`, `task.toml`, `.pre-commit-config.yaml`,
  `.cursor/`, `.claude/`, GitHub template filenames, and the repository name.
- Code comments, docs, ADRs, and agent instructions are English.
- Ordinary commits contain no attribution trailers (no `Co-authored-by`,
  `Generated-by`, or "made with" lines).
- One mutable owner per resource: one agent owns one issue, branch, and
  worktree at a time. Never edit, rebase, or push another agent's branch.
  Preserve concurrent and unknown dirty work. Never force-remove a worktree
  or branch.
- Preparation, installation, registration, successful calls, and end-to-end
  acceptance are separate states. Every pull request says which state each
  claim reached. Nothing is verified without the command output that shows it.
- Never commit credentials, real host inventories, personal chat histories,
  tokens, or token-bearing URLs. Preserve bundled third-party licenses and
  origin notes (`THIRD_PARTY_NOTICES.md` when vendoring).
- Update `README.md` and affected docs with verified behaviour only, in the
  same pull request.
- Repository visibility is decided by the owner only.

## 4.1 Code

- Python 3.12+, `uv`, `uv.lock` committed, no unpinned dependencies.
- Ruff (E, F, W, I, B, UP, SIM, RUF, N, PL, line length 100) and
  `mypy --strict` on `src/`.
- Pytest `--strict-markers`. Tests are deterministic (explicit seeds).
  Slow tests use `@pytest.mark.slow`.
- Type hints in `src/`. Docstrings state units and conventions and point at
  the spec section.
- No defensive programming: no broad `try/except`, no silent fallbacks, no
  "just in case" branches, no hand-rolled sanitising beyond what the spec
  requires. Fail loudly with a clear error.
- No speculative abstraction. No checksum or sha256 manifests. No notebooks
  in `src/` or `tasks/` (exploratory notebooks go in `notebooks/`, outputs
  stripped by the nbstripout hook).
- Numerical code uses numpy and scipy. Prefer exact diagonalisation for
  references. Document matrix basis order. Do not invent that order.
- No live or paid LLM inference anywhere in the test suite.
- Dependencies are added with `uv add`, not `pip install`.

## 5. Hooks

Three layers, one policy. Details: `docs/adr/0003-tooling.md`.
Scripts: `tools/hooks/`, tested by `tests/test_hooks.py`.

Git, installed by `make setup`:

- pre-commit: ruff format, ruff lint (`--fix` off when `CI=true`), mypy,
  nbstripout, check-yaml, check-toml, end-of-file-fixer, trailing-whitespace,
  large files (500 KiB, `data/gold/` up to 5 MiB),
  `tools/check_spec_untouched.py`, `no-commit-to-branch` on `main`.
- commit-msg: Conventional Commits. Scope is required and one of
  `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`,
  `spec`.
- pre-push: `make check`, and a push to `main` is refused.

`tools/check_spec_untouched.py` rejects staged changes under `spec/` or
`data/gold/` unless `OWNER_SPEC_EDIT=1`. Agents must never set that variable.

Cursor (`.cursor/hooks.json`) and Claude Code (`.claude/settings.json`) share
`tools/hooks/dispatch.py`.

- Deny `git push --force*`, `git push origin main`, `git commit --no-verify`,
  `git reset --hard` on `main`, `OWNER_SPEC_EDIT=`, and `pip install`.
- Deny edits under `spec/` and `data/gold/`. The message points at the
  `needs-science-decision` flow. Reads of `spec/` are allowed.
- `afterFileEdit` / Claude `PostToolUse` runs `ruff format` on the edited
  Python file.
- On stop, run `make check`. If it fails, tell the agent to keep working.

## 6. Branching and review

- `main` is always green: pull request, linear history, no force-push,
  CODEOWNERS review. The owner merges. Agents do not merge.
- One issue, one branch, one pull request. Branch name
  `<agent>/<issue_number>_<slug>`, for example `cursor/12_decoder_scaffold`.
- Claim an issue by commenting `claim` and adding `in-progress` before
  starting. Do not touch files outside the issue's declared scope. If two
  issues need the same file, the second waits or the change is split.
- Pull requests should stay under 400 changed lines excluding `data/` and
  lockfiles. A larger diff needs a reason in the body.
- Rebase on `main` before review. Squash merge only.
- Pull request sections, all mandatory: issue link; spec reference (exact
  `spec/...#anchor` lines); contract changes (public API, task format, or
  tolerances: "none" or a list plus an ADR link); which state each claim
  reached; local `make check` output; what is not verified; open science
  questions (links to `needs-science-decision` issues).
- Any change to the task format, package public API, or directory layout
  requires a new ADR.
- `PROGRESS.md` is updated in the same pull request whenever a milestone or
  task status changes.

## 7. CI

Local `make check` plus the pre-push hook is the source of truth. Paste that
output in the pull request. GitHub Actions runs the same `make check`. Do not
spend the turn debugging Actions billing or infrastructure. If CI is
unavailable, the local output decides.

## 8. Milestone M0

M0 is the layout, the three hook layers, ADRs 0001–0003, the `spec/` skeleton
(headings and `TODO(owner)` only), `tools/new_task.py`, `make validate`, and
the format demo `example_000_smoke`. The owner reviews the pull request
`chore(tooling): M0 scaffold` and is the one who merges it.

M1 engineering (not started): reference-solver scaffolding, verifier helpers
beyond the named-tolerance loader, and a Docker base image. Each of those is
blocked on the spec sections listed in `PROGRESS.md`. Do not invent the
missing science in order to start them.
