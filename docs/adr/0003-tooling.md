# 0003. Tooling and hooks

## Status

Accepted

## Context

Local `make check` is the source of truth. Git hooks, Cursor hooks, and Claude
Code hooks have to enforce the same owner-only paths and the same denied
commands, or parallel agents will bypass whichever layer is weakest.

## Decision

- Python 3.12, dependencies in `pyproject.toml`, lockfile `uv.lock` committed.
  Add dependencies with `uv add`. `pip install` is denied.
- `make setup` runs `uv sync --frozen --all-groups` and installs the
  pre-commit, commit-msg, and pre-push hooks.
- `make check` runs `fmt-check`, `lint` (`ruff check` with `--fix` off),
  `mypy --strict` on `src/qecbench`, pytest (including `slow`), and `validate`.
- Ruff rule set: E, F, W, I, B, UP, SIM, RUF, N, PL. Line length 100.
  The pre-commit lint hook may pass `--fix` when `CI` is not `true`.
- Git pre-commit stage: ruff format, ruff lint, mypy, nbstripout, check-yaml,
  check-toml, end-of-file-fixer, trailing-whitespace, large files, the
  owner-path check, and no commit on `main`.
- Large files: 500 KiB, except `data/gold/` which may reach 5 MiB. The stock
  `check-added-large-files` hook cannot express the second cap, so
  `tools/hooks/check_large_files.py` implements that policy under the same
  hook id.
- `tools/check_spec_untouched.py` rejects staged paths under `spec/` or
  `data/gold/` unless `OWNER_SPEC_EDIT=1`. Agents do not set that variable.
- Commit messages are Conventional Commits with a required scope:
  `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`,
  `spec`. No `Co-authored-by`, `Generated-by`, or "made with" trailers.
- Pre-push runs `make check` and refuses a push whose destination is
  `refs/heads/main`. `tools/hooks/install_pre_push.sh` wraps the pre-commit
  pre-push hook so the destination ref on stdin is visible. pre-commit's
  hook runner does not forward that stdin.
- Cursor (`.cursor/hooks.json`) and Claude Code (`.claude/settings.json`) call
  `tools/hooks/dispatch.py`. Shell denials: `git push --force*`,
  `git push origin main`, `git commit --no-verify` (and `git commit -n`),
  `git reset --hard` when the revision is `main` or ends in `/main`, any
  command containing `OWNER_SPEC_EDIT=`, and `pip install` / `python -m pip
  install`.
- Cursor `preToolUse` on `Write` and `Delete` denies owner-only paths before
  the write. `afterFileEdit` denies the same paths and runs `ruff format` on
  other Python files. `beforeReadFile` allows reads, including `spec/`.
  Claude `PreToolUse` on `Edit`, `Write`, and `MultiEdit` denies the same
  paths. `PostToolUse` on `Edit` and `Write` formats Python files.
- The `stop` hook runs `make check` when the agent completed. On failure,
  Cursor gets `followup_message` and Claude gets `decision: block`, both
  telling the agent to keep working.

Numerical code, when it exists, uses numpy and scipy. Those packages are not
dependencies yet: there is no numerical code in M0. No checksum manifests, no
notebooks under `src/` or `tasks/`, and no live or paid LLM calls in tests.

## Consequences

A hook failure is a failed commit, push, or agent turn, not a warning.
`tests/test_hooks.py` covers the scripts. GitHub Actions runs the same
`make check`; if Actions is unavailable, the local output decides.
