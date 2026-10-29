# Project status

Updated: **2026-10-28** (America/Vancouver).

**Current phase: 02 — Non-induced 3-star implementation COMPLETE.
STOP POINT REACHED.** Exact counters, the specified bias-corrected Laplace
simulation, CLI and automated tests are implemented and verified. Formal privacy
and accuracy proofs remain pending independent review. Do not begin ESCAPE
integration, large experiments, 4-clique estimation or other algorithms.

## Current phase checklist

- [x] Read permanent instructions, source review, status and checkpoint 01.
- [x] Define and validate simple undirected graphs and a headered edge-list format.
- [x] Preserve isolates; deduplicate undirected edges; reject loops and malformed input.
- [x] Implement exact `Σ_v C(d(v),3)` with Python integer arithmetic.
- [x] Implement an independent brute-force counter for small graphs.
- [x] Implement Laplace scale `2/epsilon`, finite-positive epsilon validation and seeded simulation RNG.
- [x] Implement the requested correction unchanged, with no clipping/rounding.
- [x] Keep private results separate from exact evaluation and exclude raw degrees/seeds.
- [x] Add private-estimate and exact-evaluation CLI commands with structured JSON.
- [x] Validate named graphs and all 1,100 labeled simple graphs through five vertices.
- [x] Test scale, RNG replay/advancement, noise moments and independence diagnostics.
- [x] Test polynomial and graph-level empirical unbiasedness with analytic SE tolerances.
- [x] Run the entire pytest suite and check packaging and installed dependencies.
- [x] Document algorithms, privacy assumptions, numerical limits and unresolved questions.
- [x] Record checkpoint 02 and actual validation evidence; preserve checkpoint 01.
- [x] Verify both external reference repositories remain unchanged.
- [x] Stop without ESCAPE integration, large experiments or 4-clique development.

## Actual verification

- **138 passed in 6.04s**, with no failed, errored or skipped tests.
- Exact degree/oracle agreement on **1,100** labeled simple graphs, plus named
  examples covering required counts, overlapping patterns and isolates.
- **41** Monte Carlo moment comparisons passed their preselected **6-SE**
  thresholds; maximum absolute standardized residual **1.9530**. These are
  bounded synthetic unit tests, not formal privacy/accuracy proofs.
- Wheel and source archive built; wheel contains all five algorithm/CLI modules.
- `pip check` succeeded; all **25** installed dependency pins match the unchanged
  hash lock. No dependency installation or upgrade occurred in phase 02.
- External source fingerprints match phase 01 (82 ESCAPE and 127 Go tracked
  files, clean worktrees). No reference binaries were executed in phase 02.

Phase 02 began from commit `f34984478e0d0275ea4372eb1a0378c10c729d86`
(`Initial Environment Setup`). Current implementation changes are local and
uncommitted; no commit or push was performed during this phase.

## Limitations and reports

NumPy randomness is simulation-only even without a seed. The intended fixed
public vertex set, edge neighboring relation and two-endpoint privacy accounting
are documented, but not formally verified. Float64 numerical extremes fail
explicitly; finite-precision DP, secure deployment, repeated-release accounting
and full accuracy review remain unresolved.

- [Checkpoint 02: implementation, commands and results](checkpoints/02_three_star_implementation.md)
- [Machine-readable validation evidence](validation_02.json)
- [Algorithms and test methodology](../ALGORITHMS.md)
- [Privacy notes and open questions](../PRIVACY_NOTES.md)
- [Checkpoint 01: historical setup/source review](checkpoints/01_setup_and_source_review.md)
- [Source review](../SOURCE_REVIEW.md)
- [Usage and reproduction](../../README.md)

Await a later explicit scope. Create `checkpoints/03_<phase>.md` and update this
checklist for the next authorized phase. No further phase is active.
