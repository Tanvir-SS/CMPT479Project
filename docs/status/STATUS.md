# Project status

Updated: **2026-10-29** (America/Vancouver).

**Current phase: 05 — Candidate LEDP 4-clique design COMPLETE. STOP POINT
REACHED.** Design, source/paper review and non-private counting/algebra checks
are complete. No private 4-clique estimator was implemented or evaluated.
Await independent mathematical review and an explicit follow-up before the
next implementation or experimental phase.

The user's explicit phase-05 request supersedes the earlier phase-04 stopping
point for this design scope. The user reports independent review of the 3-star
work; no review memorandum or detailed approval findings were supplied in this
phase. The existing implementation and historical review package remain intact.

## Current phase checklist

- [x] Read AGENTS.md, status, phase-04 handoff, checkpoints 01–04 and research docs.
- [x] Inspect actual k-CoreD / EdgeOrientΔ source and relevant primary papers.
- [x] Inspect ESCAPE's directed-diamond/clique method and orientation invariants.
- [x] Specify consistent private-level/public-ID ordering and prove exact identities.
- [x] Specify candidate pseudocode, local information and every released transcript.
- [x] Derive conditional RR-weighted sensitivity including cap-induced replacement.
- [x] Separate uncapped unbiasedness from capped target/bias; examine shared-edge covariance.
- [x] State all epsilon allocations, independence assumptions and unresolved proof obligations.
- [x] Compare fairly with the debiased-RR AISTATS 2025 baseline without utility claims.
- [x] Validate on 1,112 graphs using actual ESCAPE and independent exact oracles.
- [x] Check 124,542 orders and 10,240 finite sensitivity comparisons.
- [x] Run the full configured regression suite, including ESCAPE tests.
- [x] Record reproducible evidence, source integrity, limitations and reviewer file list.
- [x] Stop at design; no full private estimator, new utility grid or later phase.

## Findings and actual verification

The repaired candidate is plausible **conditional on an audited private-ordering
contract** and the proposed full-transcript composition argument. Important
obstacles are inconsistent equal-level ties in the Go code, RR-amplified local
sensitivity, cap-induced bias, and covariance when roots reuse closing-edge
reports. Low out-degree alone does not imply independent local errors or a
utility advantage. These are review findings, not a completed LEDP guarantee.

- **1,112/1,112 graph comparisons agree:** brute-force four-sets, outgoing triples,
  directed diamonds and actual ESCAPE. This includes all 1,100 labeled graphs
  through five vertices and 12 additional examples.
- **124,542 ordering checks** pass, including all permutations for the exhaustive
  small graphs. Mock levels and non-private peeling test identities only;
  k-CoreD was not executed in this phase.
- **10,240 finite sensitivity checks** pass at RR parameter `log(2)`. Independent
  RR product expectations pass for all eight true three-edge configurations.
  A shared-coin counterexample and K5 cap-loss examples are recorded explicitly.
- **256 passed in 14.49s**, zero failures/skips. This includes **34** marked
  ESCAPE integration tests (33 reference-module cases and one pipeline case).
- Both external source fingerprints remain identical: **82 ESCAPE and 127 Go
  tracked files**, clean worktrees. Existing package source, tests, dependency
  lock, checkpoints 01–04 and phase-04 review package are unchanged.
- No new dependencies. ESCAPE compilation succeeds with the existing **160
  upstream warnings**. No unresolved execution blocker was observed.

## Design, evidence and handoff

- [FOUR_CLIQUE_DESIGN.md: specification, derivations, source findings and review questions](../FOUR_CLIQUE_DESIGN.md)
- [Checkpoint 05: files, exact commands, observed results and limitations](checkpoints/05_four_clique_design.md)
- [Compact validation evidence](validation_05.json)
- [Non-private design-check script](../../scripts/check_four_clique_design.py)

Ignored raw evidence is under `build/phase05/`, particularly
`design_checks.json` (actual ESCAPE input/output for all 1,112 graphs), build
provenance, compiler log, pytest log/XML and reference fingerprints. Send it
separately to reviewers or reproduce it using the design document's commands.
The small `validation_05.json` is intentional source-controlled evidence; it
does not replace the raw output. New files remain local/uncommitted for review;
no commit or push was performed. Starting revision:
`8b0735e6b48559d86d1dcd943c6b44920ff736b3`.

## Preserved phase-04 work

The completed 3-star pipeline contains 15 graphs, 75 cells and 37,500 trials.
Its unchanged reports are [checkpoint 04](checkpoints/04_experiments_and_review.md),
[3-star review package](REVIEW_PACKAGE.md), [experiments](../EXPERIMENTS.md),
[algorithms](../ALGORITHMS.md), [privacy notes](../PRIVACY_NOTES.md), and
[accuracy evidence](accuracy_04.json). Phase 04's stopping/review statements are
historical; they are not authorization to implement this new candidate.

Generated 3-star results remain in `experiments/results/three_star_phase04/`,
figures in `plots/three_star_phase04/`, and its separate review bundle in
`build/phase04/review_package.tar.gz`. These artifacts remain ignored by Git.
