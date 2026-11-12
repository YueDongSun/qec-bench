# Contributing

Humans and agents follow the same rules. `AGENTS.md` is the short contract. `spec/` is the science, and only the owner edits it.

## Setup

```bash
make setup
make check
```

`make setup` installs the uv environment and the pre-commit, commit-msg, and pre-push hooks.

## Branches

`main` is protected. One issue, one branch, one PR.

```text
<agent>/<issue-number>-<slug>
```

Comment `claim` on the issue and add the `in-progress` label before editing. Do not touch files outside the issue's declared scope. If two issues need the same file, the second waits or the change is split.

## Commits

Conventional Commits, with a mandatory scope:

```text
feat(task): add decoding-001-repetition-memory
```

Scopes: `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`, `deps`, `spec`.

The commit-msg hook rejects anything else. Do not use `--no-verify`. Do not commit directly to `main`.

## Pull requests

Rebase on `main` before review. Squash merge only. The owner merges; agents do not.

The PR template sections are all required. Aim for under 400 changed lines excluding `data/` and lockfiles, and say why when a PR is larger. Paste the tail of `make check`. Update `PROGRESS.md` when a milestone or task status changes.

A change to the task format, the public API, or the directory layout needs a new ADR in `docs/adr/`.

## Spec questions

Do not invent a convention, tolerance, or literature value. Open an issue with the `needs-science-decision` label, quote the spec line, list the concrete options, and stop that piece of work.

## Adding a task

```bash
uv run python tools/new_task.py decoding-001-short-name
```

The id is `<family>-<nnn>-<slug>`. Point `spec_ref` at the spec section the owner has written. Read tolerances from `spec/TOLERANCES.md` by name. `make validate` must pass: the reference solution passes its tests, and a run that writes nothing fails them.
