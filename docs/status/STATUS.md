# Project status

Updated: **2026-10-29** (America/Vancouver).

**Current phase: 06 — Full 4-clique research prototype COMPLETE. STOP POINT
REACHED.** Fixed-order counting, k-CoreD integration, full local-report protocol,
baseline, tests and preliminary synthetic comparisons are complete. Await
independent mathematical review and explicit follow-up before another phase.
No other pattern or expanded experimental grid has been started.

The k-CoreD integration **succeeded** as a noised research implementation.
The full executable privacy proof and adapted ordering's low-out-degree utility
guarantee remain **unresolved**. Every experimental result is labeled
`experimental_unverified`; tests do not establish LEDP.

## Current phase checklist

- [x] Read instructions, Phase-5 design/checkpoint and relevant reference/review documents.
- [x] Implement and test exact/oriented counters, one-owner RR, stable cap selection and local noise.
- [x] Run fixed-order tests before automatically proceeding to k-CoreD.
- [x] Audit and port actual k-CoreD threshold/promotion/stop behavior.
- [x] Use one consistent `(private_level, public_ID)` order throughout.
- [x] Record full coordinator transcript and explicit two-endpoint ordering accounting.
- [x] Integrate public/noisy/uncapped modes with explicit total-budget allocation.
- [x] Add independent six-factor debiased-RR baseline at the same total epsilon.
- [x] Keep public fixed, noised private and non-private oracle configurations distinct.
- [x] Validate counts against actual ESCAPE and independent exact oracles.
- [x] Run all regression tests, fix the observed CSV verification issue, preserve earlier tests.
- [x] Complete 8-graph, 160-cell, 16,000-trial preliminary comparison.
- [x] Save truth/retained targets, all raw trials/metrics, seeds/config and reference provenance.
- [x] Replay every estimate/non-timing diagnostic and regenerate all eight plot files.
- [x] Preserve 3-star results, external source trees and dependency lock.
- [x] Complete implementation/audit/experiment documentation and independent-review package.
- [x] Stop; no expanded grid, other pattern or next phase.

## Actual tests and findings

- **376 passed in 28.54s**, zero failures/errors/skips in the final full suite.
  All **256 previous tests** remain unchanged; **120 new tests** pass.
  **43 marked ESCAPE integration cases** are included.
- Initial full run had **1 failed, 375 passed** from CSV integer/float dtype
  inference. The verifier fix preserves all numerical comparisons; no
  estimator, seed or statistical tolerance was altered.
- Phase-5 recheck: **1,112 actual ESCAPE comparisons**, **124,542 order checks**
  and **10,240 finite sensitivity checks**, all pass.
- **8/8 experiment graph counts** agree across actual ESCAPE, independent
  four-sets, forward triples and the separately labeled noiseless k-CoreD oracle.
- **16,000 trials**, 100 per graph/epsilon/method. All saved estimates and
  non-timing diagnostics replay exactly. A complete repeated run matches every
  non-timing CSV field; it is the same observations reproduced, not new trials.
- Every oriented method has higher **observed** RMSE than the baseline in all
  **32 graph–epsilon comparisons**. No general ranking or utility advantage is
  claimed. Noisy caps equal n-1 in **92.0625%** of their trials; cap 3 loses many
  original cliques. One hundred trials poorly resolve some RR tails.
- **7,326 negative estimates** retained; **60 cells** have undefined relative
  error because truth is zero. No output clipping or round-off projection.
- All **82 ESCAPE + 127 Go tracked files** remain unchanged and clean. The
  original 3-star artifact set still verifies: 15 graphs, 75 cells, 37,500 trials.
- No third-party dependency changes. Offline editable reinstall, dependency
  check, README CLI examples and wheel/source packaging succeed.

## Reports and artifacts

- [Independent-review package 06 and exact file list](REVIEW_PACKAGE_06.md)
- [Checkpoint 06: commands, outcomes, failures, differences and limitations](checkpoints/06_full_four_clique_implementation.md)
- [Internal fixed-order checkpoint](checkpoints/06a_fixed_order_internal.md)
- [Internal k-CoreD checkpoint](checkpoints/06b_kcore_internal.md)
- [4-clique implementation](../FOUR_CLIQUE_IMPLEMENTATION.md)
- [k-CoreD source/transcript audit](../KCORED_INTEGRATION.md)
- [Preliminary experiments and observations](../FOUR_CLIQUE_EXPERIMENTS.md)
- [Compact machine-readable observations](accuracy_06.json)
- [Original Phase-5 design](../FOUR_CLIQUE_DESIGN.md) and [privacy notes](../PRIVACY_NOTES.md)

Ignored generated outputs: `experiments/results/four_clique_phase06/`,
`plots/four_clique_phase06/` and `build/phase06/`.
Transfer these separately or reproduce them with README commands.
The small accuracy JSON is intentionally retained with the source reports.
Source changes are local/uncommitted; no commit or push was performed.
Starting revision: `396f9215ac1c97b54e3717f4acf56f95442ae743`.

## Preserved earlier work

Checkpoints 01–05 and the phase-04 [3-star review package](REVIEW_PACKAGE.md)
remain historical records. The user reported independent review of 3-star work;
no review memorandum was supplied in this phase. Its unchanged mechanism,
counters, tests and results remain available under the original paths.
The present stop permits no further implementation without explicit follow-up.
