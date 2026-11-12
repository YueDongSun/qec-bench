# Contributing

`main` stays green. The owner merges. Agents do not merge, force-push, or push
to `main`.

## Branch and issue

One issue, one branch, one pull request. Branch name:
`<agent>/<issue_number>_<slug>`, for example `cursor/12_decoder_scaffold`.
The M0 branch is the exception named by the owner: `cursor/m0_scaffold`.

Before editing, comment `claim` on the issue and add `in-progress`. Stay inside
the issue's file scope. If two issues need the same file, the second waits or
the change is split. Do not edit, rebase, or push another agent's branch.
Do not delete a worktree or branch that is not yours. Leave unrelated dirty
files alone.

## Commits

Conventional Commits with a required scope:

```text
feat(task): add example_000_smoke
```

Scopes: `task`, `verify`, `reference`, `taskfmt`, `tooling`, `docs`, `ci`,
`deps`, `spec`.

No `Co-authored-by`, `Generated-by`, or "made with" trailers. No
`git commit --no-verify`. `spec/` and `data/gold/` are owner-only; do not set
`OWNER_SPEC_EDIT`.

## Pull request

Rebase on `main` before review. Prefer under 400 changed lines excluding
`data/` and lockfiles; a larger diff needs a reason in the body. Squash merge
is the owner's action.

The pull request template is mandatory. Every claim names the state it reached:
prepared, installed, registered, a successful call, or end-to-end acceptance.
Nothing is verified without the command output.

A change to the task format, the package public API, or the directory layout
needs a new ADR in `docs/adr/`. Update `PROGRESS.md` when a milestone or task
status changes. Update `README.md` only with behaviour you have run.

## Checks

```bash
make setup && make check
```

`make check` is the source of truth. Paste its output in the pull request.
The pre-push hook runs it and refuses `refs/heads/main`.

## Science

Do not guess a convention, tolerance, unit, or constant. Quote the spec line,
list the options in a `needs-science-decision` issue, and stop that piece.
