# Uniform-sampling RR C4: six-dataset evaluation

2026-11-11 (America/Vancouver). **Stage 5 COMPLETE: 4,800/4,800 main trials.**
Four separate smoke observations are excluded. No Stage 6 comparison, baseline,
parameter tuning, plot or other-pattern work was performed.

## Algorithm and setup

The unchanged `four_cycle_uniform_rr.simulate_four_cycles_private` samples
q=ceil(.05 n²) candidates uniformly with replacement, each from a uniform four-set
and one of three cycle orders. Each occurrence produces two independent-model RR
wedge reports. The per-request alpha is epsilon/max(K_e1,K_e2), with potential-edge
participation calculated entirely from the public schedule. Debiasing uses
Y=(R−r)/(1−2r), r=1/(1+exp(alpha)); the estimate is
[3 binom(n,4)/q] sum_t Y_t1 Y_t2. No clipping or rounding is applied.

The six pinned graphs and mappings were hash-checked against the current manifest.
The existing exact common-neighbor C4 helper independently agreed once per graph
with the cached native ESCAPE **4-cycle** column and the owner's expected counts.
The manifest's top-level K4 labeling is not used for C4 truth. Raw historical
ESCAPE output and its original source provenance are copied to the result cache;
no fresh native execution was needed. All three bundled reference fingerprints
verified, with no changes to source or gitlinks.

| Dataset | n | m | Exact non-induced C4 | q |
|---|---:|---:|---:|---:|
| karate | 34 | 78 | 154 | 58 |
| dolphins | 62 | 159 | 278 | 193 |
| les_miserables | 77 | 254 | 2672 | 297 |
| brightkite_50 | 50 | 97 | 198 | 125 |
| ba_n100 | 100 | 1600 | 207959 | 500 |
| sbm_n100 | 100 | 760 | 7302 | 500 |

Each graph uses total epsilon .5, 1, 2 and 4, with 200 independent-model trials per
cell. Main master seed **202611112701**; smoke master **202611112700**. Trial seeds
are `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`; ordered graph and
epsilon identifiers are fixed in the config. All 4,800 main seeds are unique and
disjoint from smoke seeds. NumPy `default_rng`/PCG64 generates each fresh schedule
and RR draws. Seeds and truth belong only to non-private public-graph evaluation
records, never to a protected protocol transcript.

Environment: Python 3.11.9, NumPy 2.2.6, pandas 2.2.3, NetworkX 3.4.2;
macOS 27.0.1 arm64, 12 logical CPUs reported. Sequential execution, no dependency
changes. The execution config and provenance record full versions, platform,
Git revision, source hashes, reference pins and dataset manifest hash. The
working tree includes the preserved uncommitted Stage 3–4 files, so source hashes
supplement the Git revision.

Per-trial runtime times only the full estimator call (sampling through aggregation),
excluding validation, exact truth, serialization and summaries. SQLite commits each
completed observation; atomic CSV exports occur per completed cell and at normal
stop. Resume reads the contiguous saved prefix and rejects changed configurations,
source, dependencies, dataset provenance or references; it does not repeat saved
coordinates. A process killed after calculation but before commit may recompute
that unsaved coordinate, but cannot duplicate a saved observation.

## Results

MSE is mean squared error to truth; RMSE its square root; bias is sample mean minus
truth; variance uses ddof=0; MAE is mean absolute error; relative RMSE is RMSE/|truth|.
Every saved cell satisfies MSE=variance+bias² numerically. All truths are positive.
The table is rounded for readability; CSVs retain 17 significant digits.

| Dataset | ε | Truth | Mean estimate | MSE | RMSE | Relative RMSE | Bias | Variance | MAE | Mean runtime (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| karate | 0.5 | 154 | -17883.78 | 5.582413e+10 | 236271.3 | 1534.229 | -18037.78 | 5.549877e+10 | 189527.7 | 0.0004702233 |
| karate | 1 | 154 | 3240.577 | 3.472864e+09 | 58931.01 | 382.6689 | 3086.577 | 3.463337e+09 | 46731.63 | 0.0004689357 |
| karate | 2 | 154 | -241.984 | 2.036217e+08 | 14269.61 | 92.65979 | -395.984 | 2.034649e+08 | 11310.04 | 0.0004673154 |
| karate | 4 | 154 | -9.220157 | 9083672 | 3013.913 | 19.57086 | -163.2202 | 9057031 | 2414.411 | 0.0004747262 |
| dolphins | 0.5 | 278 | -60001.13 | 2.409997e+12 | 1552416 | 5584.232 | -60279.13 | 2.406363e+12 | 1228351 | 0.001594312 |
| dolphins | 1 | 278 | -25112.61 | 1.796256e+11 | 423822.7 | 1524.542 | -25390.61 | 1.78981e+11 | 342920.1 | 0.001686245 |
| dolphins | 2 | 278 | -2158.538 | 9.044175e+09 | 95100.87 | 342.0894 | -2436.538 | 9.038238e+09 | 75723.7 | 0.001635867 |
| dolphins | 4 | 278 | 1144.464 | 4.001808e+08 | 20004.52 | 71.9587 | 866.4639 | 3.9943e+08 | 15845.89 | 0.001626161 |
| les_miserables | 0.5 | 2672 | -173007.5 | 1.017414e+13 | 3189693 | 1193.747 | -175679.5 | 1.014328e+13 | 2489467 | 0.00253604 |
| les_miserables | 1 | 2672 | -4020.074 | 6.294327e+11 | 793367.9 | 296.9191 | -6692.074 | 6.293879e+11 | 637999.2 | 0.00254498 |
| les_miserables | 2 | 2672 | -1346.042 | 3.247243e+10 | 180201.1 | 67.44053 | -4018.042 | 3.245629e+10 | 141775.7 | 0.002536995 |
| les_miserables | 4 | 2672 | 842.5212 | 1.454345e+09 | 38135.88 | 14.27241 | -1829.479 | 1.450998e+09 | 30315.5 | 0.00254893 |
| brightkite_50 | 0.5 | 198 | 125879.3 | 7.326586e+11 | 855954.8 | 4323.004 | 125681.3 | 7.168628e+11 | 676376.7 | 0.001068256 |
| brightkite_50 | 1 | 198 | -8328.209 | 4.687702e+10 | 216511 | 1093.49 | -8526.209 | 4.680432e+10 | 173155.4 | 0.001036805 |
| brightkite_50 | 2 | 198 | -6106.65 | 2.662616e+09 | 51600.54 | 260.6088 | -6304.65 | 2.622867e+09 | 41174.78 | 0.001042542 |
| brightkite_50 | 4 | 198 | 1247.392 | 1.215135e+08 | 11023.32 | 55.67333 | 1049.392 | 1.204123e+08 | 8540.541 | 0.001034063 |
| ba_n100 | 0.5 | 207959 | 663827.2 | 4.405717e+13 | 6637557 | 31.91762 | 455868.2 | 4.384935e+13 | 5236566 | 0.004338984 |
| ba_n100 | 1 | 207959 | 367998.4 | 3.384972e+12 | 1839829 | 8.847077 | 160039.4 | 3.359359e+12 | 1400267 | 0.004328981 |
| ba_n100 | 2 | 207959 | 144222.9 | 2.179727e+11 | 466875.4 | 2.245036 | -63736.14 | 2.139104e+11 | 376430.5 | 0.004397935 |
| ba_n100 | 4 | 207959 | 213186.1 | 2.029257e+10 | 142452 | 0.6850004 | 5227.096 | 2.026525e+10 | 111085.8 | 0.004336267 |
| sbm_n100 | 0.5 | 7302 | -369326.5 | 4.286414e+13 | 6547071 | 896.6134 | -376628.5 | 4.272229e+13 | 5287285 | 0.00436414 |
| sbm_n100 | 1 | 7302 | 65270.59 | 3.52392e+12 | 1877211 | 257.0817 | 57968.59 | 3.520559e+12 | 1469594 | 0.004315122 |
| sbm_n100 | 2 | 7302 | 24766.76 | 1.736245e+11 | 416682.7 | 57.06419 | 17464.76 | 1.733195e+11 | 337368.5 | 0.004340997 |
| sbm_n100 | 4 | 7302 | -245.2549 | 7.623933e+09 | 87315.14 | 11.9577 | -7547.255 | 7.566972e+09 | 72264.85 | 0.004303044 |

## Observations

MSE and RMSE decrease at each successive epsilon on all six graphs. The largest
relative RMSE is 5584.23 for
dolphins at epsilon 0.5;
the smallest is 0.685 for
ba_n100 at epsilon 4.
BA-100, the densest graph by edge density in this set, has much larger truth and
smaller relative error than the sparse real-world graphs. Its absolute error can
still be large. This observation does not isolate density as a causal factor:
graph size, pattern abundance and structure differ too.

There are **2,319 negative estimates (48.3125%)**, all retained,
and **4,800 noninteger estimates**, also retained. Summed estimator runtime
is **11.499573741 seconds**. Variance contributes between
**97.8440% and 99.9929%** of empirical MSE across cells,
so variance dominates. Empirical bias may be large relative to small truths, but
its largest magnitude in estimated standard errors of the mean is
2.0940 (sample-variance SE, 200 observations). This descriptive measure
is not a formal test of unbiasedness, especially across 24 cells; these results
do not establish systematic estimator bias or disprove ideal unbiasedness.

## Verification and limitations

A predeclared four-call smoke at Karate/epsilon .5 ran as one call plus three
resumed calls. It retained one negative estimate, passed finite/q/2q-report/4q-
participation checks, CSV/SQLite exact round-trip verification, and population-MSE
identity. Resuming the completed smoke added zero calls. Main observations are
separate. During each main call the returned alpha vector was checked against
epsilon/max(K_e1,K_e2), outside the timing interval.

Final saved-output verification passes: exactly six graphs, four budgets each,
200 distinct trial indices per cell, 4,800 finite estimates and unique seeds,
correct schedule sizes, unchanged dataset hashes/truth, artifact hashes,
CSV/SQLite equality and summary recomputation. No failed calls, skipped requested
checks or unresolved execution errors. Existing algorithm tests and native fixture
tests were not rerun; their Stage 4 outcomes remain historical evidence.

`ProjectWorkflow.md` was not found in the repository (including hidden-file name
search); the explicit Stage 5 request and EVALUATION_STANDARDS supplied the
workflow. The unavailable `/home/tsshergi` originals were not verified on this Mac;
the three bundled reference checkouts were verified in place.

Two hundred trials provide finite and potentially noisy empirical moments; an
ideal unbiased estimator can have nonzero sample bias. Sparse graphs contain a
small fraction of all candidate cycles, so uniform sampling can be inefficient.
Random public edge-participation counts produce varying alpha and RR variance.
Nonnegative truth does not justify censoring signed estimates. The ideal fixed-
epsilon O(n³) RMSE bound is asymptotic and does not imply useful relative accuracy
on these finite sparse graphs. NumPy randomness and floating-point arithmetic
are research simulations, not deployment-grade private randomization; side-channel
and isolation protections are absent. These experiments do not prove epsilon-LEDP
or certify the ideal mathematical privacy argument for executable code.

## Artifacts and reproduction

- Runner: `scripts/evaluate_four_cycle_uniform_rr.py`.
- Fixed config: `experiments/configs/four_cycle_uniform_rr_six_datasets.json`.
- Results root: `experiments/results/four_cycle_uniform_rr_six_datasets/`.
- Main files: `trials.csv`, `summary.csv`, `trials.sqlite3`, `config.json`,
  `provenance.json`, `escape_ground_truth.json`, `manifest.json`, `verification.json`.
- Separate smoke: `smoke/` beneath that same root.
- Commands and preservation evidence: [checkpoint 27](status/checkpoints/27_four_cycle_uniform_rr_evaluation.md).

All previous Laplace artifacts and other research files are preserved. Generated
results remain Git-ignored. No commit or push. **Stop here; Stage 6 is deferred.**
