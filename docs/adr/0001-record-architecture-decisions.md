# 1. Record architecture decisions

## Status

Accepted

## Context

Several agents will change this repository in parallel. `GOVERNANCE_SPEC.md` section 6 requires an ADR for any change to the task format, the package public API, or the directory layout. Scientific definitions stay in `spec/` and are not decided here.

## Decision

Record those decisions as `docs/adr/NNNN-title.md`. Numbers increase by one. The owner merges the ADR with the change it describes. Agents do not put physics, tolerances, or literature values in an ADR.

## Consequences

A change that cannot point at a spec line or an ADR is not ready to merge. `spec/` and `data/gold/` remain owner-only.
