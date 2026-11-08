# Project status

Updated: **2026-11-08 UTC**.

**Current phase: 19 — six-dataset candidate-only 4-clique evaluation COMPLETE.**
Phase 18 is explicitly abandoned; its estimates and unfinished tooling are removed.

- [x] Inspect and discard only abandoned evaluation work.
- [x] Retain six selected graphs unchanged; remove 18 inactive graphs/mappings.
- [x] Document future evaluation conventions without implementing other patterns.
- [x] Add a lightweight resumable K4 script and brief smoke test.
- [x] Run 4,800 fresh trials: six graphs × four budgets × 200.
- [x] Save metrics/results, verify preservation, complete checkpoint and stop.

**4,800/4,800 fresh trials completed**, 24 cells at 200 trials each. Brief 48-trial
smoke/recovery and full saved-output verification pass. Equal O/D/R/C quarters;
population variance and direct MSE. No observations are reused from Phase 18.
RMSE falls with epsilon on all six graphs but remains large relative to truth.
All 2,436 negative estimates are retained; no outgoing-edge truncation observed.

See [results and commands](../FOUR_CLIQUE_SIX_DATASETS.md),
[future evaluation conventions](../EVALUATION_STANDARDS.md), and
[checkpoint 19](checkpoints/19_six_dataset_four_clique_evaluation.md).
Full CSVs/SQLite: `experiments/results/four_clique_six_datasets/` (ignored).
The six graph/mapping snapshots, all fixtures, private algorithms, proofs,
dependencies, reference pins and 54 historical result/plot files are preserved.
No full regression was rerun; verification was intentionally limited as requested.

**STOP.** No baseline, other-pattern run, tuning, extensive audit, commit or push.

## Preserved earlier completed status

**Current phase: P4 Phase 5B — COMPLETE (2026-11-07, America/Vancouver).**
See [full technical report](../FOUR_PATH_COMPARISON_2025.md) and
[checkpoint 17](checkpoints/17_four_path_comparison_2025.md).
Resumed from clean `acf3442`; the study, plots, profiling and earlier verification
were already saved. Completed documentation and fresh checks without changing
code, configurations or experiment artifacts.

The fixed comparison completed26 candidate cells/20 unique baseline conditions:
15,600 candidate trials,12,000 baseline trials,10,400 prediction histories.
Both methods use identical saved graphs and equal nominal total epsilon.
**Baseline lower MSE in all26 cells**, including approximate Bonferroni-adjusted
intervals; candidate/baseline MSE ratios5.56–19023.35. Candidate centralized
simulation is faster in all cells. These are conditional research results, not
universal superiority or certified executable privacy.

## Current Phase 5B checklist

- [x] Preserve Phase5A, earlier mechanisms, graph instances, budgets and references.
- [x] Predeclare26 comparisons,20 shared baseline conditions and independent seeds.
- [x] Validate framework and exact ideal baseline variance;35 focused tests passed.
- [x] Pass n100 smoke and execute the bounded study without dropped trials.
- [x] Verify exact/native targets,312 artifact hashes and full deterministic replay.
- [x] Generate/inspect seven PNG/PDF figure pairs; record stage/memory diagnostics.
- [x] Fresh resumed regression:913 passed in40.56s, no failures/errors/skips.
- [x] Fresh reference verification;57 protected files and271 Phase4B artifacts unchanged.
- [x] Complete report/checkpoint, whitespace check and change review; stop.

Full resumed replay verifies38,000 distinct coordinates, including every saved
estimate/transcript and independent prediction history. Study artifacts remain
ignored at experiments/results/four_path_phase17_comparison/ (446,650,529 bytes
excluding root manifest). No estimator changes, new phase, commit or push.

## Historical Phase 5A completion

Updated: **2026-11-06 (America/Vancouver)**.

**Current phase: P4 Phase 5A — COMPLETE.** See
[checkpoint 16](checkpoints/16_four_path_baseline_2025.md) and
[technical reconstruction](../FOUR_PATH_BASELINE_2025.md).
Resumed from clean revision `8849987`, preserving its saved baseline module,
57 tests and source specification. Verified fidelity to Algorithm 1 under the
author notebook's one-report-per-unordered-pair convention; completed handoff
documentation without modifying code. Fresh baseline: **57 passed in 3.50s**;
full regression: **878 passed in 32.15s**, zero failures/errors/skips.
All three reference fingerprints verified; 55 protected pre-baseline source,
test and dependency files retain their recorded hashes.

## Current Phase 5A checklist

- [x] Inspect saved work and verify paper, supplement and author-code provenance.
- [x] Distinguish proposed debiased product estimator from classical RR counting.
- [x] Verify non-induced P4 normalization and exact cubic server identity.
- [x] Document ideal edge privacy, unbiasedness and theoretical RMSE qualifications.
- [x] Run baseline, exact/ESCAPE/RR and full regression checks.
- [x] Verify references, preservation and whitespace; complete checkpoint/handoff.
- [x] Stop before Phase 5B; no comparative experiments, commit or push.

## Historical macOS dataset verification

Updated: **2026-11-06 (America/Vancouver)**.

**Current task: all 24 graph datasets verified on macOS — COMPLETE.**
See [checkpoint15](checkpoints/15_macos_dataset_verification.md). main and fetched
origin/main are both86f7ed3; existing uncommitted Phase4B work was preserved.
Apple Silicon arm64, macOS27.0.1, Python3.11.9, GNU g++16.2.0. All24 graphs
are tracked, canonical, hash-correct and accepted by K4/P4/baseline input paths.
Fresh brute-force/Python/ESCAPE K4 counts agree with the manifest; all 24 P4 counts
also agree with ESCAPE. All49 processed graph/mapping/manifest files unchanged.
Dataset tests: **76 passed in6.40s**; full suite: **821 passed in30.92s**, no skips,
failures or errors. All reference pins verified. No private sweep, algorithm edit,
dataset regeneration, dependency change, commit or push. **STOP after verification.**

## Current verification checklist

- [x] Fetch/check branch and preserve uncommitted work; no update necessary.
- [x] Verify environment, pinned dependencies and all three submodules.
- [x] Check all 24 tracked graphs, mappings, canonical structure and hashes.
- [x] Check actual estimator input boundaries without private sampling.
- [x] Execute actual ESCAPE and independent exact K4/P4 checks.
- [x] Run dataset/full tests and confirm all49 dataset artifacts unchanged.
- [x] Record macOS evidence, limitations and stop.

## Historical P4 Phase4B completion

Updated: **2026-11-06 (America/Vancouver)**.

**Current work: P4 Phase 4B accuracy study COMPLETE (checkpoint 14).**
See [checkpoint 14](checkpoints/14_four_path_accuracy_study.md) and
[complete study report](../FOUR_PATH_STUDY.md). The resumed predeclared matrix
completed **30 cells / 18,000 full trials / 12,000 independent prediction histories**,
with full deterministic replay and actual ESCAPE truth for15 distinct graphs.
Targeted suite: **288 passed**; full regression: **821 passed in31.25s**, no skips,
failures or errors. All references and protected mechanism hashes unchanged.

All MSE discrepancies fall within the predeclared3 combined SE criterion; this
is limited consistency evidence, not formal proof. Sparse cases have poor relative
accuracy. Full-protocol truncation remained unobserved; fixed-cap controls show
the predicted bias. Saved configs still use phase13 names; checkpoint13 below
is separate dataset work and is preserved. No Phase5, commit or push.

## Current P4 Phase 4B checklist

- [x] Inventory saved changes and preserve intervening dataset/research work.
- [x] Complete/review framework with unchanged Phase4A limits and private code.
- [x] Run targeted/full tests; record historical null-representation failure.
- [x] Save resource/precision plan; run native-validation smoke and replay.
- [x] Execute unchanged bounded30-cell matrix and fixed-history controls.
- [x] Verify all artifacts, native truth, metrics and deterministic replay.
- [x] Generate/inspect figures; report unfavorable and inconclusive findings.
- [x] Document costs, limitations and next-phase readiness; stop before Phase5.

## Historical dataset preparation status (checkpoint 13)

Updated: **2026-11-06 (UTC)**.

**Current phase: 13 — Dataset preparation and exact validation COMPLETE.**
See [checkpoint13](checkpoints/13_dataset_preparation.md),
[data instructions and all 24 counts](../../data/README.md), and
[dataset manifest](../../data/processed/graph_manifest.json).
Starting revision: `99d542abe4aa81b448b9859561af703605259fd5`.

Prepared four real-world graphs and twenty paper-compatible BA/SBM realizations.
Every graph agrees across oriented exact counting, independent brute force and
actual ESCAPE. Brightkite seed130050 selects original start2044 and yields an
induced **50-vertex,97-edge graph with18 K4s**; no seed/structure search was used.
All49 graph/mapping/manifest files regenerate byte-identically (174,456 bytes).
Sources, parameters, seeds, typed ID mappings, full hashes and native count
output are preserved. The notebook n20,m2 discrepancy is documented; BA follows
paper m=n//5. Original dataset downloads remain ignored.

New tests: **76 passed in12.90s**. Full regression: **821 passed in51.47s**, no
failures/errors/skips; includes85 ESCAPE integration cases. Existing standalone
ESCAPE check: **8 fixtures passed**. All24 datasets passed exact CLI smoke tests.
Fresh verification and source-package inclusion checks passed. All three pinned
submodules and all three original references verify unchanged. New macOS execution
was unavailable; no cross-platform result is invented.

Two future file-based configs share hash-pinned inputs/exact truth and total
privacy budgets, with distinct simulation coordinates. **No private counting
trial on these datasets or full comparison was run.** All graphs fit current
size guards; n100 baseline has3,921,225 four-sets per trial, so repeated-trial
feasibility needs future measurement. Existing privacy mechanisms, mathematical
analysis, Phase-6 config, fixtures, results and plots are unchanged. The experiment
adapter adds file loading only, plus a label for future file-based evaluation.
The four-clique simulator remains `experimental_unverified`; the earlier audit
classification remains PARTIAL.

## Current phase checklist

- [x] Inspect current repository, reports, actual paper, source notebooks and providers.
- [x] Pin/download original archives and normalize the four real-world graphs.
- [x] Fix Brightkite selection before inspecting counts; retain its induced edges.
- [x] Generate twenty independent seeded graphs using documented paper conventions.
- [x] Preserve all vertex mappings, isolates, hashes and stable source provenance.
- [x] Validate all 24 with three independent exact counting methods.
- [x] Verify identical regeneration, all76 new tests and full821-test regression.
- [x] Prepare future configs without changing privacy accounting or running them.
- [x] Check source/archive portability, protected files and all reference fingerprints.
- [x] Finish docs/reports and stop; no automatic commit/push.

**STOP: dataset phase complete. Await an explicit follow-up before private
experiments, optimization or another phase.** The processed files are eligible
for version control; publishing them remains the owner's later action.

## Preserved previous status (four-clique Phases8–9 and earlier)

Updated: **2026-11-06 (UTC)**.

**Active request: 4-clique Phases 8–9 COMPLETE. Privacy audit: PARTIAL; ideal error analysis and validation complete.**
The requested checkpoint names coexist with earlier macOS/P4 reports; none is
renumbered or replaced. Current audited revision is `6fba863e984fda8f55c016655df7ded917cc0576`.
No estimator redesign, budget tuning, new benchmark grid, P4 work, commit or push
is authorized.

See [privacy proof](../FOUR_CLIQUE_PRIVACY_PROOF.md),
[error analysis](../FOUR_CLIQUE_ERROR_ANALYSIS.md),
[checkpoint 08](checkpoints/08_four_clique_privacy_audit.md) and
[checkpoint 09](checkpoints/09_four_clique_error_validation.md).
Ideal full-transcript privacy is established for exact actual stage allocations
and independent ideal randomizers; finite execution, nominal-budget tolerance,
seeds and client isolation remain unresolved. The simulator remains
`experimental_unverified`. The replacement-aware sensitivity is unchanged.

Final full suite: **745 passed in 41.04s**, no failures/errors/skips. All **65**
new tests pass; explicit ESCAPE selection: **61 passed**, plus **8** standalone
reference fixtures. Nine diagnostic graphs agree with actual ESCAPE. Exact
RR/Laplace/clipping formulas and the finite-n bound pass exhaustive checks;
16,384 conditional trials, 3,072 full trials and 3,072 independent histories
show no discrepancies beyond the predeclared attention rule. Fifty preserved
Phase-6 cells were reconciled, with 150 existing estimates replayed exactly.
Local count noise dominates the selected kcore/noisy cases; no accuracy advantage
over baseline is established. Results: `build/phase09/validation/` (Git-ignored).

Estimator code, Phase-6 config/results, lock and all three reference pins are
unchanged. A verified pre-existing non-private P4 verifier None/NaN comparison
defect was fixed without changing numeric values or tolerances. Prior reports,
35 result files and 19 plot files retain their hashes. macOS was not retested.
**STOP: no further phase, optimization, tuning, commit or push. Await explicit instruction.**

## Active request checklist

- [x] Inspect actual source, prior documentation and pinned papers/references.
- [x] Record external checkout advance; preserve existing P4 work.
- [x] Complete code-to-proof map, conditional sensitivity and full transcript argument.
- [x] Run Phase-8 targeted tests and record classification before Phase 9.
- [x] Implement independent non-private analytical error evaluator and tests.
- [x] Validate exact RR enumeration, bounded seeded diagnostics and selected old results.
- [x] Run full regression, ESCAPE, CLI and preservation checks; finish reports and stop.

## Preserved previous status

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
