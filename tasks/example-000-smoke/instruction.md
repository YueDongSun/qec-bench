# example-000-smoke

FORMAT DEMO. This task checks that a solution can run a repetition-code memory experiment and write a logical-error-rate report. It has no pass-threshold science. `spec/TOLERANCES.md` is TODO(owner). Do not treat the `[demo]` table in `task.toml` as a noise-model convention.

## What to produce

Read `[demo]` in `task.toml`. Run that Stim repetition-code memory experiment, decode it with PyMatching, and write `result.json` under `OUTPUT_DIR` (or `./output` when `OUTPUT_DIR` is unset) with:

- `circuit`: the demo circuit name
- `seed`: the demo seed
- `shots`: the demo shot count
- `errors`: how many shots have a decoded observable that does not match that shot's observable flip
- `logical_error_rate`: `errors / shots`

The report is the whole deliverable. No target logical error rate is part of this task.
