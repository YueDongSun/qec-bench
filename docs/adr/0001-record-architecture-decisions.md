# 0001. Record architecture decisions

## Status

Accepted

## Context

Several agents will change this repository in parallel. Task format, the package
public API, and the directory layout need a written decision so later edits do
not drift. Scientific decisions are not architecture: they belong in `spec/`
and are written by the owner.

## Decision

- Architecture decisions are numbered Markdown files in `docs/adr/`.
- A change to the task format, the package public API, or the directory layout
  requires a new ADR in the same pull request.
- Agents do not record physics, conventions, tolerances, or literature values
  here. If a spec point is missing, the agent opens a `needs-science-decision`
  issue and stops that piece of work.

## Consequences

Reviewers can reject a contract change that has no ADR. `AGENTS.md` stays the
agent contract; an ADR records one decision, it does not replace `spec/`.
