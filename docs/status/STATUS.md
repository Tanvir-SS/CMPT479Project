# Project status

Updated: **2026-10-28** (America/Vancouver).

**Current phase: 03 — ESCAPE validation COMPLETE. STOP POINT REACHED.**
The adapter executes the original ESCAPE size-4 counter and preserves actual
reference evidence. All 24 configured graphs agree exactly across the Python
formula, independent enumeration and ESCAPE. Small controlled epsilon checks
passed. The private estimator and its release schema remain unchanged.

## Current phase checklist

- [x] Read AGENTS.md, current status, both previous checkpoints and source review.
- [x] Inspect actual ESCAPE build instructions, loader, executable and output map.
- [x] Compile original C++ translation units into project build directories.
- [x] Support ESCAPE_ROOT and explicit --escape-root without reusable personal paths.
- [x] Canonicalize unique undirected edges and preserve isolates.
- [x] Normalize fewer than four vertices by adding isolates; document affected columns.
- [x] Parse actual non-induced output with explicit process/output errors.
- [x] Check formula, brute force and ESCAPE on 24 named/ER/BA cases.
- [x] Distinguish induced/non-induced counts using K4 and K5 and six-column fixtures.
- [x] Test errors, signed zero, configuration, limits and concurrent working directories.
- [x] Run two graphs x three epsilon values x 3,000 trials with preset 6-SE checks.
- [x] Store actual reference outputs and non-private synthetic evaluation summaries.
- [x] Run all tests with real ESCAPE; verify optional unconfigured skips separately.
- [x] Update README, algorithm/privacy notes and permanent scope instructions.
- [x] Record checkpoint 03; preserve historical checkpoints and reference sources.
- [x] Stop without full epsilon grid, large experiments or 4-clique development.

## Actual verification

- **229 passed in 13.80s**, no failures/errors/skips in the configured full suite.
  This includes 33 real integration tests: 24 comparisons, 8 six-column fixtures,
  and one test of four concurrent calls. The other 196 are Python/unit tests.
- **24/24** three-way comparisons agree exactly: 12 named/boundary cases,
  6 seeded Erdos-Renyi and 6 seeded Barabasi-Albert cases (at most 12 vertices).
- **8/8** original six-column fixture comparisons pass in the separate script.
- Six diagnostic means pass preselected six-analytic-SE thresholds; maximum
  absolute z-score **1.759120**. Empirical MSE decreases at epsilon 1, 2, 4 on
  both K1,4 and K5. These are 18,000 bounded simulation trials, not a DP proof.
- Optional-dependency check: without ESCAPE_ROOT, **33 integration tests skipped
  in 0.22s**, with explicit configuration reasons. These are not counted as passes.
- Compilation succeeds with g++ 11.4.0 and 160 upstream warnings. A parser
  regression rejecting ESCAPE's signed zero was found, fixed and covered by a
  test; the intermediate failures are recorded in checkpoint 03.
- Wheel and source archive build succeeds. No dependency installs/upgrades;
  the 25 pinned dependencies and requirements.lock remain unchanged.
- Both external reference trees match recorded hashes and remain clean.

## Limitations and reports

The adapter is scoped to at most 1,000 vertices and rejects output counts at or
above 2**53. Actual behavior was checked only on small graphs. Padding preserves
connected four-vertex counts, while other columns describe the normalized graph.
Reference warnings, upstream arithmetic limits and unsupported revisions remain
limitations. NumPy randomness is simulation-only; formal privacy and accuracy
review remains pending. Exact evaluation artifacts must not accompany private
releases on protected data.

- [Checkpoint 03: commands, results, resolved failures and files](checkpoints/03_escape_validation.md)
- [Actual structured comparison and diagnostic output](validation_03.json)
- [ESCAPE integration, API and limitations](../ESCAPE_VALIDATION.md)
- [Checkpoint 02: 3-star implementation](checkpoints/02_three_star_implementation.md)
- [Checkpoint 01: setup/source review](checkpoints/01_setup_and_source_review.md)
- [Algorithms](../ALGORITHMS.md), [privacy notes](../PRIVACY_NOTES.md), [README](../../README.md)

Phase 03 began from clean commit
`7c917674a12b2c8739317e5b44bccbb9ca253a88` (3 star counting). Its changes are
local and uncommitted; no commit or push was performed. Await a later explicit
instruction before phase 04; create its numbered checkpoint when authorized.
