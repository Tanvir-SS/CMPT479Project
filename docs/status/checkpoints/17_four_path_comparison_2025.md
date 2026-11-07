# Checkpoint 17 — P4 Phase 5B comparison

Date: 2026-11-06 (America/Vancouver). **IN PROGRESS: full study complete; replay/handoff pending.**

## Authorized scope and starting state

User explicitly authorized Phase 5B after completed Phase 5A. Initial HEAD is
8849987; the six uncommitted Phase 5A documentation changes are preserved.
No private mechanism, exact counter, reference pin or dependency is changed.
Read current instructions/status, checkpoints 14/16, P4 implementation/accuracy/
study/baseline documentation, and existing orchestration and test conventions.
All 271 recorded Phase 4B artifact hashes and all three reference fingerprints
verified before development. Saved edge-list instances are available.

## Completed implementation and predeclaration

New dedicated evaluation module `src/private_graphlets/four_path_comparison.py`,
runner `scripts/run_four_path_comparison.py`, full/smoke Phase17 configurations,
and `tests/test_four_path_comparison.py`. Reuses Phase 4A candidate execution,
metrics/prediction/replay engines without editing them. New exact ideal baseline
variance uses centered-noise coefficient families; independent exhaustive tests
compare the Phase 5A path-set oracle. The public/private schema separation and
negative estimates remain unchanged.

Initial focused run: 33 passed in 5.65s, no errors/failures/skips. Two additional
boundary/statistical tests were added for final regression, pending execution.

Full design saved before results: 26 candidate cells, 20 unique baseline
conditions, 600 trials each, 400 candidate prediction histories per cell.
Fresh master202611061705; distinct candidate/full/prediction/baseline coordinates.
A/B/C budgets and graph instances exactly match Phase 4B; the baseline receives
full total epsilon. Approximate pointwise95% and Bonferroni26 intervals are
predeclared. Shared baseline series are not counted as independent repetitions.

Smoke master202611061700: 8 cells/5 baseline conditions, 24+15 full trials and
24 histories. Completed in2.686257s,1,509,887 bytes,265,633,792 peak RSS bytes.
Complete smoke replay passed (63 distinct seeds). Includes n100 and shared
baseline allocation cells. Baseline timing projection193s; conservative total
including replay5–20min, memory/artifact allowance each1GB. No design changes.

## Pending work

- Complete full run and inventory/graph/native/metric verification and full replay.
- Separate bounded stage/memory profiling and complete result analysis.
- Inspect all seven PNG/PDF figure pairs.
- Run updated focused tests/full regression; verify references/preserved hashes.
- Finish report, current status and final whitespace/change review.

No Phase 5B completion or research ranking is asserted by this interim record.
No commit/push or next phase is authorized.
