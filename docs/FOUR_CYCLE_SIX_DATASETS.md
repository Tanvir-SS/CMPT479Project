# Balanced wedge-Laplace C4: six-dataset evaluation

2026-11-09 (America/Vancouver). **4,800/4,800 trials complete; verification passed.**

## Setup

Unchanged `simulate_four_cycles_private` uses the balanced arithmetic-progression
schedule with p the smallest prime >= max(n,5), one global public permutation,
independent cycle choices, two local noisy wedge reports per candidate and
normalization 3*C(p,4)/[p(p-1)]. Sensitivity is 12 per affected endpoint;
endpoint privacy is epsilon/2 and Laplace scale is 24/epsilon. Duplicates and all
negative/noninteger estimates are retained. No tuning or baseline comparison.

Six unchanged pinned graphs, epsilon .5/1/2/4, 200 trials per cell. Exact
non-induced C4 truth is reused from pinned native ESCAPE output, with graph and
mapping hashes validated. No exact counting inside private trials. Configuration:
`experiments/configs/four_cycle_six_datasets.json`; master seed 202611092201;
trial seed `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`.
Smoke master 202611092200 and its 24 observations are separate and not reused.

MSE is the mean squared error against native truth, RMSE its square root, bias
mean minus truth, variance uses ddof=0, MAE averages absolute errors, and relative
RMSE is RMSE/abs(truth). Runtime covers each complete estimator call, excluding
truth preparation, storage and reporting. Table values are rounded for display
only; full precision records are in the saved CSVs.

## Results

Relative RMSE below is a **ratio**, not percent. Runtime is milliseconds per call.

| Dataset | epsilon | Exact C4 | Mean estimate | MSE | RMSE | Bias | Variance | MAE | Relative RMSE | Mean ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| karate | 0.5 | 154 | 1.60559e+06 | 8.02717e+14 | 2.83323e+07 | 1.60543e+06 | 8.0014e+14 | 2.27468e+07 | 183976 | 2.3518 |
| karate | 1 | 154 | -271768 | 4.12271e+13 | 6.42083e+06 | -271922 | 4.11532e+13 | 5.15577e+06 | 41693.7 | 2.4971 |
| karate | 2 | 154 | 50235.5 | 2.41524e+12 | 1.55411e+06 | 50081.5 | 2.41274e+12 | 1.25053e+06 | 10091.6 | 2.5318 |
| karate | 4 | 154 | -53387.7 | 1.41456e+11 | 376106 | -53541.7 | 1.38589e+11 | 300914 | 2442.24 | 2.3263 |
| dolphins | 0.5 | 278 | -4.23643e+06 | 2.69473e+16 | 1.64156e+08 | -4.23671e+06 | 2.69293e+16 | 1.33191e+08 | 590490 | 8.2179 |
| dolphins | 1 | 278 | 454527 | 1.72922e+15 | 4.15839e+07 | 454249 | 1.72902e+15 | 3.34319e+07 | 149582 | 8.3760 |
| dolphins | 2 | 278 | -422979 | 1.09873e+14 | 1.0482e+07 | -423257 | 1.09694e+14 | 8.65652e+06 | 37705.1 | 8.2353 |
| dolphins | 4 | 278 | 144402 | 4.47277e+12 | 2.11489e+06 | 144124 | 4.45199e+12 | 1.70032e+06 | 7607.52 | 8.8353 |
| les_miserables | 0.5 | 2672 | 1.56148e+07 | 6.4514e+16 | 2.53996e+08 | 1.56121e+07 | 6.42703e+16 | 2.02197e+08 | 95058.4 | 12.0544 |
| les_miserables | 1 | 2672 | 2.33856e+06 | 4.25147e+15 | 6.52033e+07 | 2.33588e+06 | 4.24601e+15 | 5.32385e+07 | 24402.4 | 11.5834 |
| les_miserables | 2 | 2672 | -1.50284e+06 | 2.54348e+14 | 1.59483e+07 | -1.50551e+06 | 2.52082e+14 | 1.27675e+07 | 5968.68 | 11.4909 |
| les_miserables | 4 | 2672 | 199960 | 1.77065e+13 | 4.20791e+06 | 197288 | 1.76676e+13 | 3.31605e+06 | 1574.82 | 11.5907 |
| brightkite_50 | 0.5 | 198 | 4.66919e+06 | 6.02083e+15 | 7.7594e+07 | 4.66899e+06 | 5.99903e+15 | 6.19025e+07 | 391889 | 4.8840 |
| brightkite_50 | 1 | 198 | -1.45799e+06 | 4.13626e+14 | 2.03378e+07 | -1.45819e+06 | 4.115e+14 | 1.61933e+07 | 102716 | 4.9453 |
| brightkite_50 | 2 | 198 | 16664.3 | 2.21171e+13 | 4.70288e+06 | 16466.3 | 2.21168e+13 | 3.51437e+06 | 23751.9 | 4.8972 |
| brightkite_50 | 4 | 198 | -106163 | 1.30705e+12 | 1.14326e+06 | -106361 | 1.29573e+12 | 911346 | 5774.05 | 4.8761 |
| ba_n100 | 0.5 | 207959 | -1.0495e+07 | 2.96526e+17 | 5.44542e+08 | -1.07029e+07 | 2.96412e+17 | 4.32079e+08 | 2618.51 | 20.0738 |
| ba_n100 | 1 | 207959 | 1.23305e+07 | 1.87948e+16 | 1.37094e+08 | 1.21226e+07 | 1.86479e+16 | 1.0953e+08 | 659.237 | 19.7874 |
| ba_n100 | 2 | 207959 | 684437 | 1.09248e+15 | 3.30527e+07 | 476478 | 1.09225e+15 | 2.65528e+07 | 158.938 | 20.1910 |
| ba_n100 | 4 | 207959 | 989688 | 7.38667e+13 | 8.59457e+06 | 781729 | 7.32556e+13 | 6.99641e+06 | 41.3282 | 19.9051 |
| sbm_n100 | 0.5 | 7302 | -2.61003e+07 | 3.01242e+17 | 5.48855e+08 | -2.61077e+07 | 3.0056e+17 | 4.36254e+08 | 75165 | 19.9646 |
| sbm_n100 | 1 | 7302 | 1.67879e+07 | 2.04304e+16 | 1.42935e+08 | 1.67806e+07 | 2.01488e+16 | 1.13841e+08 | 19574.8 | 20.2860 |
| sbm_n100 | 2 | 7302 | 3.87282e+06 | 1.57472e+15 | 3.96827e+07 | 3.86551e+06 | 1.55978e+15 | 3.10059e+07 | 5434.5 | 20.1901 |
| sbm_n100 | 4 | 7302 | 419145 | 8.25935e+13 | 9.0881e+06 | 411843 | 8.24239e+13 | 7.15846e+06 | 1244.6 | 19.9855 |

## Runtime and negative estimates

| Dataset | epsilon | Total seconds | Negative / 200 |
|---|---:|---:|---:|
| karate | 0.5 | 0.470356 | 98 |
| karate | 1 | 0.499425 | 99 |
| karate | 2 | 0.506356 | 97 |
| karate | 4 | 0.465256 | 109 |
| dolphins | 0.5 | 1.643573 | 103 |
| dolphins | 1 | 1.675193 | 105 |
| dolphins | 2 | 1.647062 | 95 |
| dolphins | 4 | 1.767055 | 97 |
| les_miserables | 0.5 | 2.410888 | 101 |
| les_miserables | 1 | 2.316674 | 94 |
| les_miserables | 2 | 2.298180 | 104 |
| les_miserables | 4 | 2.318149 | 94 |
| brightkite_50 | 0.5 | 0.976799 | 96 |
| brightkite_50 | 1 | 0.989068 | 104 |
| brightkite_50 | 2 | 0.979445 | 103 |
| brightkite_50 | 4 | 0.975229 | 111 |
| ba_n100 | 0.5 | 4.014754 | 97 |
| ba_n100 | 1 | 3.957478 | 91 |
| ba_n100 | 2 | 4.038204 | 95 |
| ba_n100 | 4 | 3.981026 | 89 |
| sbm_n100 | 0.5 | 3.992911 | 104 |
| sbm_n100 | 1 | 4.057194 | 95 |
| sbm_n100 | 2 | 4.038022 | 97 |
| sbm_n100 | 4 | 3.997109 | 98 |

## Accuracy analysis

RMSE decreases at every epsilon step on all six graphs. Doubling epsilon
roughly quarters RMSE in these observations, consistent with the importance of
products of two Laplace noise terms; this is a description of this fixed study,
not an empirical proof of an asymptotic rate.

Karate has the smallest absolute RMSE at every budget (376,105.71 at epsilon 4).
SBM-100 has the largest absolute RMSE at every budget (548,854,792.76 at epsilon
.5). Relative error tells a different story: BA-100 is best at every budget,
with its best RMSE still **41.3282 times the true count** (4,132.82%) at epsilon 4.
Dolphins is worst by relative RMSE at every budget, reaching 590,490.13 times
truth at epsilon .5. Thus none of these settings demonstrates practically small
relative error, despite improvement as epsilon increases.

Empirical bias can be very large compared with truth: the BA-100 mean at epsilon
4 is 989,688.20 versus truth 207,959, while the Dolphins mean at epsilon .5 is
-4,236,434.17 versus truth 278. However, variance accounts for **97.9734%–99.9988%**
of empirical MSE across the 24 cells. These finite-sample mean deviations do not
establish systematic bias of the ideal unbiased estimator. The maximum absolute
mean-error/sample-standard-error ratio is approximately 2.03 across the 24 cells;
this descriptive diagnostic is not a multiple-comparison test or proof of
unbiasedness. Only 200 observations inform each empirical bias estimate.

**2,376/4,800 estimates (49.5%) are negative.** All 4,800 observations are
noninteger. They are preserved exactly in the saved numerical records; no
clipping, rounding, exclusions or outlier filtering was used.

Absolute error generally grows with padded graph size in this collection. At
n=100, BA (m=1,600) and SBM (m=760) have similar absolute errors despite very
different C4 truth (207,959 versus 7,302). BA's much larger target makes its
relative errors smaller. Sparse low-count graphs such as Dolphins and
Brightkite-50 have especially large relative errors. These six fixed graphs
confound size, density and structure; this is not a controlled scaling or density
experiment and cannot isolate causal effects.

## Runtime, reproducibility and completion

Summed estimator-call runtime is **54.015406 seconds**. Cell mean runtime ranges
from **2.3263 to 20.2860 ms**; the runtime table above also reports every cell's
summed time. These are centralized simulation measurements, not distributed
network latency. Environment: Python 3.11.9, NumPy 2.2.6, pandas 2.2.3, NetworkX
3.4.2, macOS 27.0.1, Apple Silicon arm64. Full environment, source and data hashes
and reference gitlinks are preserved in provenance.json. The working tree
included the reviewed uncommitted Phase-22 implementation; the saved source
hashes, rather than Git HEAD alone, identify executed code.

```bash
.venv/bin/python scripts/evaluate_four_cycle.py verify --smoke
.venv/bin/python scripts/evaluate_four_cycle.py run > build/phase23/main_run.log
.venv/bin/python scripts/evaluate_four_cycle.py verify
.venv/bin/python build/phase23/verify_and_report.py > build/phase23/independent_analysis.log
```

All commands exited 0. Main verification returned:

```json
{"cells":24,"population_variance_identity":true,"remaining_trials":0,"status":"verified","study_status":"complete","trials":4800}
```

The separate csv/statistics calculation confirmed all requested metrics and
MSE=variance+bias², exactly 200 observations in every cell, IDs 0..199 per cell,
4,800 unique composite trial identifiers and 4,800 unique seeds. It also checked
scale, endpoint budgets and q=p(p-1) in every record. Runner verification checks
CSV/SQLite equivalence, hashes, configuration, native truth and provenance.
All required files exist under `experiments/results/four_cycle_six_datasets/`:

- `trials.csv` and `summary.csv`;
- `config.json`, `provenance.json`, `escape_ground_truth.json`;
- `manifest.json`, `trials.sqlite3`;
- `verification.json`, `independent_verification.json`.

Raw artifacts remain Git-ignored and must be shared separately if handing off a
source-only archive. There was no technical failure, interrupted main run or
required resume in this phase. Existing smoke resume verification was reused.
No estimator, runner, configuration, seed scheme, dataset, dependency or reference
source was changed. No main observation was reused from smoke testing.

## Limitations

At epsilon .5/1/2/4 the Laplace scales are 48/24/12/6. These are large compared
with binary wedge indicators. Multiplication produces a noise-product term with
variance 4b^4 per candidate, and aggregation multiplies by a large public scaling
factor. This explains why a valid worst-case O_epsilon(n³) RMSE bound does not
imply useful relative accuracy on these sparse or modest-size benchmarks.
The experiment measures practical error; it neither proves nor disproves the
ideal asymptotic bound, nor certifies the mathematical privacy analysis.

NumPy PRNGs and floating-point Laplace sampling remain research simulations, not
certified production pure LEDP. The protocol models a logical reporting round,
not secure transport or constant-time physical execution. Saved simulation seeds
and exact ground truth make these evaluation artifacts non-private; they must
not be treated as protected mechanism transcripts. Formal privacy and accuracy
proofs remain subject to independent review. Results are conditional on these six
fixed graphs, budgets and trial seeds; no novelty, baseline superiority or
universal utility claim is made.

**Evaluation complete. Stop; no additional estimator, baseline, tuning or study.**
