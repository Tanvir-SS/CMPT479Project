# Requested Phase 9 — Four-clique error validation

2026-11-06 (UTC). **COMPLETE. Stop after this report.**
Current revision: `6fba863e984fda8f55c016655df7ded917cc0576`. No branch, commit,
pull or push was made by this task. This specifically requested report coexists
with the historical `09_exact_four_path_triangle.md`; all earlier checkpoints
are preserved. [Phase 8](08_four_clique_privacy_audit.md) completed first with
classification **PARTIAL**, establishing an ideal complete-transcript composition
argument while retaining executable and nominal-budget qualifications.

## Scope and files

Created:

- `src/private_graphlets/four_clique_accuracy.py`: independent, non-private
  exact integer variance coefficients, retained-four-set oracle, conditional
  expectation/RR/Laplace/clipping/MSE decomposition, finite-n upper bounds,
  cap-tail evaluation, six-factor baseline variance and rational RR enumeration.
- `scripts/validate_four_clique_accuracy.py`: bounded run/verify pipeline;
  saved configuration/seeds, real ESCAPE evidence, raw draws, conditional and
  independent random-history comparisons, optional selected Phase-6 reconciliation,
  hashes and explicit failure/overwrite handling.
- `tests/test_four_clique_accuracy.py`: 37 exact and integration tests, including
  exhaustive loops and independent rational moment calculations.
- `tests/test_four_clique_accuracy_pipeline.py`: two domain/validation/artifact
  tests; a real-ESCAPE small pipeline, deterministic replay and corruption check.
- `docs/FOUR_CLIQUE_ERROR_ANALYSIS.md` and this checkpoint.

Updated README only to link the new proof/error reports and checkpoints; updated
AGENTS/STATUS for the active authorized scope and stopping point. Phase 8 also
created its proof, 26 tests and checkpoint. The only existing production-source
edit across both phases is the documented three-line **non-private P4 verifier**
None-to-NaN normalization required to fix a pre-existing strict pandas warning.
No comparison tolerance or computed numeric value changed.

All candidate/baseline estimators, APIs/defaults, CLI code, 3-star formula,
k-CoreD/RR code, Phase-6 runner/configuration, requirements lock, submodule pins
and previous experimental outputs remain unchanged. No estimator optimization,
budget tuning, benchmark expansion, notebook execution or new plotting occurred.

## Mathematical findings

The full derivation and implementation map are in
[FOUR_CLIQUE_ERROR_ANALYSIS.md](../../FOUR_CLIQUE_ERROR_ANALYSIS.md).

- Conditional mean is the retained original-clique target K_B, determined by
  true outgoing-neighbor rank prefixes. Independent four-set enumeration agrees
  with the oriented count and with original counts from actual ESCAPE.
- RR uses tau=exp(R)/(exp(R)-1)^2. Repeated closing triples require m_T^2 diagonal
  weights; distinct triples sharing one pair have covariance tau times the other
  four true edge indicators. Different roots are not independent.
- Exact conditional MSE is `V_RR + 2*n*(Delta_B/C)^2 + (K_B-K)^2`.
  Unconditional MSE averages all three over the private ordering/cap history.
  `E[(K_B-K)^2] = (E[K_B]-K)^2 + Var(K_B)`; do not add the latter variance twice.
- The proposed finite-n bound is valid:
  `V_RR <= n^2*C(B,3)*[(1+tau)^3-1 + 3*tau*(B-2)]` for B>=3, zero otherwise.
  Count occurrence pairs in ordered form; the factor two is already included.
- For fixed positive R/C and no clipping: uncapped B=n-1 gives MSE O(n^6),
  RMSE O(n^3); constant B gives MSE O(n^2), RMSE O(n). These are upper bounds,
  not equalities. MAE and RMSE are distinct.
- At small R: tau=Theta(R^-2), Delta=O(B^2 R^-3), count variance
  O(n B^4/(C^2 R^6)). A budget spent on order/cap is not available to RR/count.
- **Sharper cap statement:** conditional underestimation probability is the
  product of Laplace CDFs at `d-1-log(n/beta)/D-q_v`, bounded by
  `beta*exp(-D)/(2n)`, or that value to the number of maximizers. The integer
  ceiling supplies exp(-D). Multiplying this probability by K^2 bounds expected
  squared loss; it is not the exact loss itself. The old beta/2 bound remains
  valid but is weaker. Beta is not DP delta.
- Consequently the uniform clipping bound can be O(beta n^7) for fixed D;
  an uncapped O(n^6) theorem does not automatically transfer with fixed beta.
- Baseline variance includes overlap of one **or three** RR pairs between
  quadruples. At tau=2 K5 gives 4160, K6 gives 14220. The implemented baseline
  spends all total epsilon on RR; this audit verifies that allocation separately
  from the candidate's split. No claims about reproducing published paper tables.

No proposed sensitivity or finite-n RR bound required correction. Corrections
are to interpretation: independence across roots is invalid; conditional squared
bias cannot be replaced by squared mean bias; scalar expected L2 norm is MAE,
not generally RMSE; the cap tail can be sharpened. No independently supplied
“Section E” report was available beyond the formulas in the user request.

## Concrete exact and empirical validation

All **1,100** labeled graphs with 0–5 vertices were considered for the count/bound
search: all orders for n<=4, ID/reverse for n=5, all caps, totaling **16,538**
combinations. Full rational tables cover every n=4 graph and all 64 RR outcomes
for both methods, plus 1,024 outcomes for K5 and an exact 8-table book marginal
(the remaining 33 of 36 pair reports integrate out). No random samples are used
to calculate these exact predictions.

At R=log(2), C=1, B=3:

| Graph/order | K / K_B | RR variance | Laplace variance | squared bias | MSE |
|---|---|---:|---:|---:|---:|
| K4 ID | 1 / 1 | 26 | 1152 | 0 | 1178 |
| K5 ID | 5 / 2 | 56 | 1440 | 9 | 1505 |
| book6 roots first | 6 / 6 | 936 | 2592 | 0 | 3528 |

The bounded pipeline saves **nine real ESCAPE comparisons**, all agreeing:
empty0, empty6, K4, K5, K8, a triangle with isolates, book6, and sparse/dense
seeded ER eight-vertex graphs. Counts are 0,0,1,5,70,0,6,0,11 respectively.
There are 64 selected exact order/cap diagnostic rows. Original native outputs
are retained separately from Python counts.

**16,384 conditional draws** (4 cases x4096) compare mean, variance and MSE
against exact predictions. For K4/K5/book6 at R=log(2),C=1, observed MSEs are
1184.510 / 1503.903 / 3494.979 versus predictions 1178 / 1505 / 3528.
A fourth case with R=log(5/4),C=.25 predicts 6489260, observes 6358762.490,
with analytic MSE standard error 168078.548. Population uncertainty formulas
use rationally enumerated third/fourth moments plus exact Laplace moments.
Largest absolute standardized discrepancy across all means/variances/MSEs:
**1.366**, below the predeclared six-SE attention rule. This rule is not a
formal confidence theorem or a DP test.

**3,072 full protocol draws plus 3,072 independent prediction histories**
(three cases x1024 per stream), at unchanged total epsilon=4:

| Case | Mean predicted MSE | Observed MSE | Combined estimated SE | difference / SE |
|---|---:|---:|---:|---:|
| K5 kcore/noisy | 2698.773 | 2774.532 | 147.144 | .515 |
| book6 kcore/noisy | 232985.892 | 232637.999 | 11111.360 | -.031 |
| book6 kcore/public B=3 | 93.117 | 91.311 | 4.206 | -.429 |

Prediction seeds differ from full-trial seeds. The noisy caps stayed at n-1 in
these small samples; this is not empirical evidence about rare lower tails.
Public-cap book histories exercise clipping: fraction .5078125; squared mean
bias 2.831201 and retained-target variance 3.611182 sum to expected squared
conditional bias 6.442383. Prediction orders vary in all three cases.

Selected Phase-6 reconciliation verifies the unchanged old **16,000-trial,
160-cell** artifacts, selects **50** cells and replays **150** old estimates
exactly. It reconstructs O/D histories from the selected candidate seeds without
rerunning the full benchmark. Newly calculated component columns are explicitly
separate from historical observed RMSE/bias. Laplace dominates all ten selected
kcore/noisy and ten fixed/uncapped cells. Fixed small caps make clipping dominate
K8/dense14 at epsilon=4; roots-first book retains all cliques but has RR reuse
cost. The four candidate methods each have worse historical RMSE than baseline
in all ten selected graph/epsilon comparisons. This is not a universal theorem
about orientations. No measured value or formula was adjusted to improve it.

## Commands, failures and actual results

Commands were run in the existing `.venv`, Python 3.11.16 on Linux/WSL2 x86_64,
with locked NumPy 2.2.6 and unchanged dependencies. Outputs/JUnit XML are in
ignored `build/phase08/` and `build/phase09/`. Shell redirection only saves logs.

```bash
.venv/bin/python -m pytest -q tests/test_four_clique_accuracy.py \
  --junitxml=build/phase09/accuracy.xml
.venv/bin/python -m pytest -q tests/test_four_clique_accuracy.py \
  --junitxml=build/phase09/accuracy-final.xml
.venv/bin/python scripts/validate_four_clique_accuracy.py run
.venv/bin/python scripts/validate_four_clique_accuracy.py verify
.venv/bin/python -m pytest -q tests/test_four_clique_privacy_audit.py \
  tests/test_four_clique_accuracy.py tests/test_four_clique_accuracy_pipeline.py \
  --junitxml=build/phase09/new-tests.xml
.venv/bin/python -m pytest -q --junitxml=build/phase09/full.xml
.venv/bin/python -m pytest -q -m escape_integration \
  --junitxml=build/phase09/escape-integration.xml
.venv/bin/python scripts/check_escape.py
.venv/bin/python scripts/reference_fingerprints.py --verify
.venv/bin/python -m pip check

.venv/bin/private-graphlets exact-three-stars data/fixtures/star.edges
.venv/bin/private-graphlets estimate-three-stars data/fixtures/star.edges --epsilon 2 --seed 123
.venv/bin/private-graphlets exact-four-cliques data/fixtures/clique.edges
.venv/bin/private-graphlets estimate-four-cliques data/fixtures/clique.edges --epsilon 2 --seed 123
.venv/bin/private-graphlets estimate-four-cliques data/fixtures/clique.edges \
  --epsilon 2 --seed 123 --ordering fixed --cap-mode uncapped
.venv/bin/private-graphlets baseline-four-cliques data/fixtures/clique.edges --epsilon 2 --seed 123

git diff --check
git submodule status
```

| Check | Observed result |
|---|---|
| Initial accuracy tests | **1 failed,33 passed in4.62s**: only the test's bookkeeping total was 16539 instead of actual 16538; all individual mathematical assertions had passed. Corrected the expected loop count, not a variance/count formula. |
| Accuracy rerun after that correction | **34 passed in4.38s**. |
| Final new Phase-8/9 tests | **65 passed in6.03s**, including rational odds and diagnostic-pipeline additions. |
| Full current suite | **745 passed in41.04s**, no failures/errors/skips. |
| Explicit ESCAPE integration selection | **61 passed,684 deselected in12.47s**, no skips. |
| Existing standalone ESCAPE validation | **8 fixtures passed**, including all six pattern columns. |
| Bounded diagnostic run/verify | Complete; **10 hashed artifacts verified**, nine native reference comparisons, all raw-summary checks pass; no statistical attention cases. |
| Six installed CLI invocations | All return valid JSON with exit0; both exact fixtures count1; protected result records omit exact data/seeds. |
| Three reference fingerprints | All exact pins/content verified, clean submodule status. |
| Preservation audit | 189 original snapshot files compared; only four authorized existing-file changes listed below; no missing files, no staged files, HEAD unchanged. |
| Dependency/link/artifact checks | `pip check`: no broken requirements; all linked local files exist; new output and `.venv` paths remain Git-ignored. |

Phase 8's initial old-revision baseline and subsequent current-revision P4
None/NaN failure are documented there, separately from these Phase-9 test results.
Nothing labels a skipped or failing check as passed. ESCAPE compiled successfully
with GNU g++11.4.0 in a project build directory; its existing upstream code
produced 160 compiler warnings, preserved in build metadata/logs. The warnings
were not repaired by editing third-party source.
`pip check` also warned that the user's pip cache was not writable under the
sandbox and disabled that cache; its dependency check succeeded without installs.

## Artifacts and preservation

`build/phase09/validation/` contains:

- `config.json`, `manifest.json`: seeds, case definitions, source/lock/executable
  hashes, platform, exact revision, compiler/source provenance and artifact hashes.
- `escape_reference.json`, `exact_diagnostics.csv`: native reference evidence and
  separate offline exact decomposition (no synthetic relabeling as ESCAPE).
- `conditional_trials.csv`, `conditional_summary.csv`: fixed-history draws and
  exact-moment SE comparisons.
- `unconditional_trials.csv`, `history_predictions.csv`, `unconditional_summary.csv`:
  disjoint full/history streams and decomposed prediction/observed uncertainty.
- `cap_tails.csv`, `phase06_reconciliation.csv`: exact tail products/bounds and
  newly computed comparison against selected preserved historical measurements.

Supporting evidence: `build/phase09/cli-checks.json`, `preservation.json`,
`references-final.json`, test XML/logs, and `build/reference-checks/escape/results.json`.
No new plots were needed/requested for this analytical audit; previous plots
remain byte-identical. These generated artifacts are Git-ignored, not staged.
A fresh reproduction uses `run --output build/phase09/reproduction`, then
`verify --output build/phase09/reproduction`. An existing directory is rejected.
Historical reconciliation is explicitly unavailable if ignored Phase-6 data are
absent; this does not substitute new results for the old study.

Hash comparison against `build/phase08/before_current.json` verifies all 35 prior
result files, all 19 prior plot files, and all 14 earlier checkpoints unchanged.
The only changed existing files are `AGENTS.md`, `README.md`, `docs/status/STATUS.md`
and the justified non-private `four_path_study.py` verifier fix. The original
STATUS body is preserved below the new active-phase report. The mechanism,
baseline, config and lock hashes recorded by the diagnostic match current files.

Unchanged submodules:

| Reference | Exact pinned revision |
|---|---|
| ESCAPE | `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3` |
| DistributedLEDPGraphAlgos | `b03da893ba1c38d3931708bac919562c5ab57963` |
| Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy | `85eff6efa2b1d649ee238620a998ec7f1d305aac` |

No direct dependency, build requirement, lock entry or reference pin changed;
no packages were installed. macOS ARM64 was **not available for execution** in
this audit. The new code uses existing Python 3.11 dependencies/portable APIs;
prior macOS evidence is historical, not a new test result.

## Handoff and stopping point

Give an independent reviewer the Phase-8 proof and test, this report and
`FOUR_CLIQUE_ERROR_ANALYSIS.md`, the new accuracy module/script/two test files,
and unchanged `four_clique.py`, `four_clique_exact.py`, `kcore.py`,
`randomized_response.py`, `four_clique_baseline.py` and Phase-6 config/runner.
Include the generated validation directory for numerical evidence and saved
Phase-6 artifacts if the retrospective comparisons are to be reproduced.

Still unresolved: independent review of the ideal derivations, secure/exact
randomness and finite arithmetic, strict nominal-budget accounting, abort/timing
channels, true client isolation, ordering utility, tighter structural covariance
and cap-loss bounds, and conditions for useful accuracy relative to baseline.
The offline n<=20 evaluator is deliberately not scalable and does not prove
executable DP. **Stop: both requested phases are complete; no Phase10, tuning,
new estimator, large experiment, commit or push is authorized or performed.**
