# Project status

Updated: **2026-10-28** (America/Vancouver).

**Current phase: 04 — Experiments and independent-review handoff COMPLETE.
STOP POINT REACHED.** Reproducible non-induced 3-star experiments, plots, tests
and technical reports are complete. The private mechanism is unchanged. Formal
privacy/accuracy review remains pending. Do not design or implement the 4-clique
or start another phase without explicit follow-up.

## Current phase checklist

- [x] Read permanent instructions, status and all three prior checkpoints.
- [x] Freeze 15 synthetic graph configurations covering five requested families.
- [x] Evaluate epsilon 0.25, 0.5, 1, 2, 4 with 500 distinct trial streams per cell.
- [x] Separate graph-generation seeds from privacy-mechanism stream coordinates.
- [x] Save exact config, original graphs, provenance, raw CSV and aggregate CSV.
- [x] Compute n, m, exact truth, mean, bias, variance, SD, MAE, RMSE, relative errors and timing.
- [x] Preserve all negative estimates and mark zero-truth relative errors undefined.
- [x] Verify all experiment graph counts with actual ESCAPE; use brute force for n<=12.
- [x] Produce four readable figures in PNG/PDF directly from saved CSVs.
- [x] Investigate mean deviations and noisy empirical variance with ideal moments.
- [x] Reproduce every estimate and every non-timing metric in a clean second run.
- [x] Regenerate all eight figure files with identical hashes.
- [x] Run full WSL setup/tests and explicit ESCAPE integration tests.
- [x] Review estimator source for clipping/rounding/formula changes; none introduced.
- [x] Expand algorithm/privacy notes, experiment documentation and reviewer file list.
- [x] Preserve prior checkpoints, dependency lock and both external repositories.
- [x] Verify generated results/plots are ignored; prepare a separate review bundle.
- [x] Stop without any 4-clique design/implementation or further research phase.

## Actual results

- **256 passed in 15.15s** in the full configured suite, no failures/skips.
- Separate real ESCAPE suite: **34 passed, 222 deselected in 10.04s**.
- **15 graphs, 75 cells, 37,500 trials**; all 15 experiment truth counts match
  ESCAPE. The earlier 24-case reference suite also passes.
- Exact seed replay succeeds for every estimate. A complete second run matches
  all non-timing CSV fields; all eight figure hashes match regeneration.
- Observed RMSE decreases with epsilon on **15/15 graphs**, but low-count graphs
  can have very poor relative accuracy. Maximum absolute mean deviation is
  **2.281724 analytic SE**; three of 75 exceed 2 SE, none exceed 3 SE.
- Empirical/ideal variance ratios span **0.279039–1.681334**. Fourth-moment
  diagnostics put these two extrema within one sample-variance SE of their
  ideal values. Five hundred trials do not precisely resolve heavy tails.
- **6,882 negative estimates** retained; **five zero-truth cells** have undefined
  relative metrics. No correction adjustment, clipping, rounding or trial removal.
- No new third-party dependencies; 25 pins match the unchanged hash lock.
  WSL setup reinstall of the editable project succeeds without network access.
- External reference trees remain clean with all 82 ESCAPE and 127 Go tracked
  file hashes unchanged. Core estimator/counter sources and checkpoints 01–03
  match the phase-04 starting commit.

## Artifacts and handoff

- [Independent-review package and exact file list](REVIEW_PACKAGE.md)
- [Checkpoint 04: work, commands, tests and limitations](checkpoints/04_experiments_and_review.md)
- [Experiments and observed findings](../EXPERIMENTS.md)
- [Compact machine-readable accuracy evidence](accuracy_04.json)
- [Algorithms](../ALGORITHMS.md) and [privacy contract/open questions](../PRIVACY_NOTES.md)
- [README reproduction commands](../../README.md)

Generated local results: `experiments/results/three_star_phase04/`.
Generated local figures: `plots/three_star_phase04/`.
Local review bundle: `build/phase04/review_package.tar.gz` with a SHA-256 sidecar.
These files are ignored by Git; transfer them separately or reproduce them.
The small `accuracy_04.json` summary is intentionally retained with source docs.

Phase 04 began from clean commit
`ea02371d0e38dc6ad4ebb1801a7fa112844bee81`. Changes remain local and uncommitted;
new source/config/report files are listed in checkpoint 04 for review. No commit
or push was performed. Await explicit instructions before any next phase.
