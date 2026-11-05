# Project status

Updated: **2026-11-05 (America/Vancouver)**.

**Current phase: 12 — P4 MSE verification/infrastructure (Phase 4A) COMPLETE.**
See [checkpoint 12](checkpoints/12_four_path_accuracy_validation.md) and
[accuracy analysis](../FOUR_PATH_ACCURACY.md). Added non-private conditional MSE
decomposition, random-history predictor and reproducible run/verify infrastructure.
Fresh baseline: **587 passed**; new tests: **72 passed**; targeted: **267 passed**;
final full suite: **659 passed in 21.24s**, no failures/errors/skips.
The five-graph pilot ran **1500 full trials + 1500 independent predictions**;
all artifacts verified with deterministic replay. All MSE discrepancies were
within the predeclared three-combined-SE threshold; precision remains limited.
No sampled missed triangles: truncation is covered by deterministic tests, not
empirically exercised by this pilot. All references verified; private code unchanged.
**STOP: Phase 4B is not started.** No baseline, large sweep, plots, commit or push.

## Current phase checklist

- [x] Read instructions, prior checkpoints and implementation/evaluation contracts.
- [x] Rerun existing tests and independently derive complete ideal MSE.
- [x] Implement non-private conditional decomposition and random-H predictor.
- [x] Implement separate streams/artifacts, provenance, integrity and replay.
- [x] Verify conditional moments, covariance and second-moment truncation averaging.
- [x] Run new, targeted and full test suites without changing private algorithms.
- [x] Run the fixed small pilot and verify/replay its artifacts.
- [x] Record uncertainty, asymptotic assumptions, costs and limitations; stop.

## Historical Phase 11 status

**Phase 11 — Complete private P4 simulator (P4 Phase 3) COMPLETE.**
See [checkpoint 11](checkpoints/11_private_four_path_implementation.md) and
[implementation](../FOUR_PATH_IMPLEMENTATION.md). The five-stage simulator uses
independent degree reports and exactly one RR table shared with the unchanged
Phase 2 triangle component. The original P4 target may have positive truncation
bias; privacy remains **experimental_unverified**. Fresh baseline: **501 passed**;
new tests: **86 passed**; targeted: **301 passed**; final full suite:
**587 passed in 19.42s**, no failures/errors/skips. All references verified.
**STOP: Phase 4 is not started.** No baseline, full study, plots, commit or push.

## Phase 11 checklist

- [x] Read instructions, prior checkpoints, privacy APIs and conventions.
- [x] Rerun the complete Phase 2 suite as a fresh baseline.
- [x] Add explicit five-stage budget and separate named RNG streams.
- [x] Add client-local noised degree reports and all-pairs postprocessing.
- [x] Share exactly one immutable RR matrix with the unchanged triangle component.
- [x] Verify assembly, transcript boundaries, means, bias, variance and covariance.
- [x] Run new/targeted/full tests and verify reference/source preservation.
- [x] Document limitations and computational/communication costs; stop before Phase 4.

## Historical Phase 10 status

**Phase 10 — Modified EdgeOrientΔ triangles (P4 Phase 2) COMPLETE.**
See [checkpoint 10](checkpoints/10_modified_triangle_protocol.md) and
[protocol specification](../TRIANGLE_PROTOCOL.md). Path A consumes an existing
order/cap/RR table; Path B runs explicit-budget private ordering, cap and one RR
transcript. Local count noise uses the derived conditional replacement bound.
The estimator targets retained triangles and is **experimental_unverified**.
Baseline rerun: **430 passed**; targeted: **215 passed**; final full suite:
**501 passed in 19.61s**, no failures/errors/skips. All references verified.
**STOP: Phase 3 is not started.** No complete private P4 estimator or experiments.

## Phase 10 checklist

- [x] Read existing instructions, checkpoint, privacy contracts and Go source.
- [x] Rerun the existing suite rather than assume historical results.
- [x] Derive fixed-transcript addition/removal/replacement sensitivity.
- [x] Implement separate reusable and standalone triangle interfaces.
- [x] Preserve shared RR ownership, deterministic order and client-side noise.
- [x] Test exhaustive sensitivity, expectation, caps, schemas and reproducibility.
- [x] Run targeted/full tests and verify unchanged pinned reference content.
- [x] Document accounting, complexity and limitations; stop before Phase 3.

## Historical Phase 09 status

**Phase 09 — Exact P4 and triangle counting (P4 Phase 1) COMPLETE.**
See [checkpoint 09](checkpoints/09_exact_four_path_triangle.md). Added integer
P4/triangle counters and an independent permutation oracle. Exhaustive verification
covers all 1,100 labeled graphs through five vertices; all eight fixture P4 and
triangle comparisons against actual ESCAPE pass. Full suite: **430 passed in
18.49s**, no failures/errors/skips. No private P4/triangle mechanism, experiment,
dependency update, commit, or push. **STOP: Phase 2 is not started.**

## Phase 09 checklist

- [x] Read project instructions, status/checkpoint, graph/reference contracts.
- [x] Implement exact integer triangle and non-induced P4 counters.
- [x] Implement independent ordered-quadruple P4 oracle.
- [x] Verify named fixtures, exhaustive small graphs, invariants and normalization.
- [x] Execute native ESCAPE comparisons and preserve separate raw evidence.
- [x] Run targeted tests (168 passed) and full suite (430 passed).
- [x] Verify reference fingerprints and preserve existing private algorithms.
- [x] Document correctness, complexity, commands and limitations; stop at Phase 1.

## Historical Phase 08 status

**Phase 08 — Mac setup COMPLETE. STOP POINT REACHED.**
The follow-up setup request authorizes local installation and validation only.
See [checkpoint 08](checkpoints/08_macos_setup.md). Python 3.11.9 `.venv` and all
three pinned references are installed and fingerprints verified. GNU GCC 16.2.0
is selected by `.venv/bin/g++` when the environment is activated. Full setup:
**392 passed in 22.06s**, no skips/errors; **8/8 exact ESCAPE fixtures** passed.
The initial Apple Clang failure is recorded separately in checkpoint 08.

## Phase 08 checklist

- [x] Read setup guide, status and latest checkpoint; inspect local prerequisites.
- [x] Bootstrap and fingerprint all three pinned references.
- [x] Install unchanged hashed Python lock and editable package; check dependencies.
- [x] Run full suite and record compiler failures separately from passes.
- [x] Install/select GNU GCC after administrator authentication.
- [x] Complete full suite and exact ESCAPE validation on macOS.
- [x] Finalize macOS setup instructions and stop without experiments/commit/push.

## Historical Phase 07 status

**Phase 07 — Repository portability COMPLETE. STOP POINT REACHED.**
All three references are pinned submodules; recursive-clone and ZIP setup are
verified. Algorithms, privacy mechanisms, budgets, configurations and saved
research results are unchanged. No main-repository commit or push was performed.
Await explicit follow-up before further work.

## Phase 07 checklist

- [x] Read instructions, prior status/checkpoint and current research/setup documentation.
- [x] Record clean starting Git state and hashes; run 376-test baseline regression.
- [x] Inspect all three originals, including baseline files, commit, remote and licensing.
- [x] Verify public upstream access and pin all three exact reviewed revisions.
- [x] Include baseline under owner-reported author permission; assign no new license.
- [x] Add safe, idempotent submodule/ZIP bootstrap and three-reference integrity checks.
- [x] Resolve explicit root > environment > project-relative bundled checkout.
- [x] Validate default and explicit-override ESCAPE builds and exact comparisons.
- [x] Run full regression: 392 passed, no skips/failures with bundled references.
- [x] Test actual recursive clone of a temporary snapshot with all three public upstreams.
- [x] Test ZIP-equivalent snapshot bootstrap and fresh locked environment.
- [x] Verify Python-only installation works with optional references absent.
- [x] Preserve algorithm modules, lock, configurations, saved results and original sources.
- [x] Finish team instructions, source review, checkpoint and permission provenance.
- [x] Stop without new utility experiments, optimization, commit or push.

## Actual verification

- Before changes: **376 passed in 26.59s** using original ESCAPE.
- After changes: **392 passed in 28.53s**, including **43 ESCAPE integration cases**.
- Explicit ESCAPE argument over invalid environment: **43 passed**, 349 deselected.
- Fresh recursive clone: **392 passed in 31.94s** with new Python 3.11.16 venv.
- ZIP-style extraction/bootstrap: **392 passed in 31.39s** with new venv.
- Fresh Python-only setup: **349 passed, 43 explicitly skipped** (ESCAPE absent).
- **8/8 exact ESCAPE fixtures** agree; five exact/private/baseline CLI examples run.
- Previous saved 3-star results verify: **15 graphs / 75 cells / 37,500 trials**.
- Previous saved 4-clique results verify: **8 graphs / 160 cells / 16,000 trials**.
- All **212 original reference tracked files** remain unchanged and clean.
- All **87 protected algorithm/config/data/result/plot files** remain byte-identical.
  The only edited existing package module is the ESCAPE adapter's path resolver.
- No dependency changes; wheel/source builds and artifact exclusion checks pass.

The clone test uses a disposable Git snapshot because these changes are not yet
committed/pushed. It actually executes `git clone --recurse-submodules` and fetches
all three public upstreams. ZIP verification uses the same main-file snapshot
without Git metadata or submodule contents. Both repeat bootstrap successfully
and install the unchanged, hashed lock from a prepared wheelhouse. This does not
claim that unpublished changes are already served by GitHub.

## References

| Reference | Pinned revision | Inclusion |
|---|---|---|
| ESCAPE | `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3` | Submodule; Apache-2.0 |
| DistributedLEDPGraphAlgos | `b03da893ba1c38d3931708bac919562c5ab57963` | Submodule; MIT |
| Counting Graphlets of Size k under Local Differential Privacy | `85eff6efa2b1d649ee238620a998ec7f1d305aac` | Submodule; owner reports author permission for this academic repository, no license assigned |

The baseline has two 4-cycle notebooks and a README, not an all-six-pattern
package. Our six-factor 4-clique comparator is independent and unchanged. Go
and notebook sources are optional references, not Python runtime dependencies.

## Reports, team handoff and limitations

- [Team setup: clone/ZIP, commands, Git workflow and troubleshooting](../TEAM_SETUP.md)
- [Checkpoint 07: all changed files, commands, outcomes and owner commit/push commands](checkpoints/07_repository_portability.md)
- [Compact actual verification record](portability_07.json)
- [Baseline source inspection and permission provenance](../SOURCE_REVIEW.md#phase-07-baseline-inspection-and-portable-references)
- [Portable pin/hash manifest](../../third_party/references.json)
- [Original source and public-access evidence](../references_phase07.json)

The owner must commit and push before team members can download this phase from
GitHub. `.gitmodules` and gitlinks are staged by submodule addition; other changes
await review/staging. Ignored logs live under `build/phase07/`. Generated research
results/plots remain ignored. No private emails or personal information are stored.
Permission beyond the stated academic inclusion requires confirmation before
broader redistribution; no open-source license is inferred for the notebooks.
For pytest overrides use `--escape-root=/absolute/path` to avoid initial root
selection treating a separate absolute argument as a test location.

## Future work — not completed or authorized in this phase

- Independent formal privacy/accuracy/utility review of the existing experimental
  4-clique mechanism: [Phase-6 review package](REVIEW_PACKAGE_06.md). Executable
  LEDP and adapted low-out-degree utility guarantees remain unresolved.
- An equivalent general-RR baseline comparison for the private **3-star** estimator
  has **not** been completed. Review the necessary specialization, normalization
  and edge-budget convention before implementation and a separately authorized
  experiment phase. Including authors' notebooks does not complete that task.
- Further utility experiments, optimization or patterns require explicit follow-up.

Historical [Phase 06](checkpoints/06_full_four_clique_implementation.md),
[3-star review](REVIEW_PACKAGE.md), checkpoints 01–05 and all saved findings are
preserved. Their mathematical qualifications and observed results still apply.
