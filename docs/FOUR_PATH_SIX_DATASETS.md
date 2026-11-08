# Standardized six-dataset P4 evaluation — Milestone 3

2026-11-08 (America/Vancouver). **COMPLETE: 4,800/4,800 trials, 24 cells.**

This is non-private evaluation of the unchanged modified EdgeOrientDelta
five-stage P4 research simulator. Targets are non-induced, unlabeled paths on
four distinct vertices: reversal counts once and additional host edges are
allowed. The owner's new request authorizes this study after Checkpoint 20;
the K4-only instruction in AGENTS describes the previous Phase 19 task.

## Fixed design

| Dataset | n | m | Exact P4 |
|---|---:|---:|---:|
| karate | 34 | 78 | 2371 |
| dolphins | 62 | 159 | 5023 |
| les_miserables | 77 | 254 | 26784 |
| brightkite_50 | 50 | 97 | 5404 |
| ba_n100 | 100 | 1600 | 2043892 |
| sbm_n100 | 100 | 760 | 166236 |

All six hashes, mapping hashes and sizes match the unchanged graph manifest.
Checkpoint 20's cached Python/native P4 counts are reused and cross-checked
against the manifest's saved native **3-path column**, never its K4 field.
No ESCAPE recount was required. Paths/full hashes are in the dedicated config.

| Total epsilon | Degree D | Ordering O | RR R | Cap M | Count C |
|---|---:|---:|---:|---:|---:|
| .5 | .150 | .050 | .125 | .075 | .100 |
| 1 | .300 | .100 | .250 | .150 | .200 |
| 2 | .600 | .200 | .500 | .300 | .400 |
| 4 | 1.200 | .400 | 1.000 | .600 | .800 |

Fractions .30/.10/.25/.15/.20 match Phase 4B Experiment B. All totals and API
constraints passed. Beta=.05 and k-CoreD psi=.5, threshold_fraction=.5,
bias_factor=1 are unchanged. No allocation optimization.

Each cell contains 200 new complete calls to `simulate_four_paths_private`.
Main master seed **202611082101**, smoke master **202611082100**. Coordinates
use `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`, graph order as
above, epsilon order [.5,1,2,4], trials 0..199. The existing five SeedSequence
children supply stage streams. Smoke uses two trials per cell under its separate
master; no historical or smoke estimates enter main results.

## Results

| Dataset | Epsilon | Exact P4 | Mean estimate | MSE | RMSE | Relative RMSE (%) | MAE | Runtime (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| karate | 0.5 | 2371 | 16369.58 | 2.017e+10 | 142023.54 | 5990.03% | 113411.87 | 0.789 |
| karate | 1 | 2371 | 4598.52 | 1.015e+09 | 31866.42 | 1344.01% | 25744.93 | 0.777 |
| karate | 2 | 2371 | 1477.33 | 6.393e+07 | 7995.46 | 337.22% | 6404.07 | 0.791 |
| karate | 4 | 2371 | 2319.81 | 2.192e+06 | 1480.69 | 62.45% | 1141.21 | 0.753 |
| dolphins | 0.5 | 5023 | 13091.09 | 1.1e+11 | 331716.58 | 6603.95% | 259094.57 | 1.806 |
| dolphins | 1 | 5023 | 16458.72 | 6.086e+09 | 78012.16 | 1553.10% | 62891.70 | 1.747 |
| dolphins | 2 | 5023 | 4368.57 | 2.046e+08 | 14304.46 | 284.78% | 11314.98 | 1.726 |
| dolphins | 4 | 5023 | 5128.22 | 7.489e+06 | 2736.63 | 54.48% | 2141.71 | 1.735 |
| les_miserables | 0.5 | 26784 | 9711.88 | 2.542e+11 | 504167.76 | 1882.35% | 403639.48 | 2.450 |
| les_miserables | 1 | 26784 | 29280.83 | 1.19e+10 | 109085.71 | 407.28% | 89837.69 | 2.495 |
| les_miserables | 2 | 26784 | 28281.20 | 3.931e+08 | 19827.35 | 74.03% | 16480.79 | 2.459 |
| les_miserables | 4 | 26784 | 26476.54 | 2.571e+07 | 5070.34 | 18.93% | 4013.50 | 2.487 |
| brightkite_50 | 0.5 | 5404 | 9784.64 | 6.411e+10 | 253195.35 | 4685.33% | 203030.20 | 1.327 |
| brightkite_50 | 1 | 5404 | 4729.04 | 3.738e+09 | 61143.25 | 1131.44% | 49452.99 | 1.279 |
| brightkite_50 | 2 | 5404 | 5231.52 | 1.77e+08 | 13304.35 | 246.19% | 10797.49 | 1.260 |
| brightkite_50 | 4 | 5404 | 5658.13 | 5.599e+06 | 2366.20 | 43.79% | 1909.80 | 1.246 |
| ba_n100 | 0.5 | 2043892 | 2132972.48 | 1.12e+12 | 1058307.61 | 51.78% | 826169.92 | 5.740 |
| ba_n100 | 1 | 2043892 | 2114125.66 | 1.562e+11 | 395266.21 | 19.34% | 318241.34 | 5.742 |
| ba_n100 | 2 | 2043892 | 2024513.45 | 2.982e+10 | 172678.83 | 8.45% | 138084.70 | 6.088 |
| ba_n100 | 4 | 2043892 | 2046655.68 | 7.418e+09 | 86129.10 | 4.21% | 67097.74 | 6.295 |
| sbm_n100 | 0.5 | 166236 | 150046.21 | 5.755e+11 | 758647.53 | 456.37% | 588278.78 | 4.205 |
| sbm_n100 | 1 | 166236 | 162016.41 | 3.236e+10 | 179891.09 | 108.21% | 142435.86 | 4.240 |
| sbm_n100 | 2 | 166236 | 163563.47 | 1.519e+09 | 38976.79 | 23.45% | 30962.80 | 4.251 |
| sbm_n100 | 4 | 166236 | 167068.53 | 2.7e+08 | 16430.33 | 9.88% | 13214.87 | 4.412 |

Rounded presentation only; `summary.csv` retains full precision. Relative RMSE
is dimensionless in CSV and explicitly a percentage here. All **1,098 negative
estimates** and fractional values are retained.

Karate has the lowest absolute RMSE at every budget, reaching 1480.69 at epsilon
4. BA-100 has the lowest relative RMSE at every budget, reaching 4.21%, despite
having the largest absolute RMSE. Dolphins has the highest relative RMSE at .5
and 1 (6603.95% and 1553.10%); Karate is highest at 2 and 4 (337.22% and 62.45%).

MSE and RMSE decrease at every epsilon step on every graph. These observations
agree qualitatively with Phase 4B's budget trend and difficulty on sparse,
low-count inputs. Different graphs and sample sizes prevent treating this as
a matched replication or a new theory-versus-prediction study.

At epsilon 4, relative empirical biases in table graph order are -2.16%, +2.09%,
-1.15%, +4.70%, +0.135%, +0.501%. Some low-budget means are far from truth:
Karate at .5 has +590.41% bias and Dolphins at 1 has +227.67%. Population variance
accounts for **96.84%–99.99% of MSE** across cells. A near-correct average does
not imply accurate individual estimates.

## Metrics and uncertainty

For errors e=X-T: MSE=mean(e²), RMSE=sqrt(MSE), bias=mean(X)-T,
variance=mean((X-mean(X))²) with ddof=0, MAE=mean(abs(e)), and
relative RMSE=RMSE/abs(T), undefined for zero truth. All six truths are positive.
Every cell satisfies MSE≈variance+bias². MSE SE is sample_std(e²)/sqrt(200),
using ddof=1 only for this SE. Observed SE/MSE is 8.78%–12.09%; this reporting
diagnostic is not a confidence guarantee, bias test or reason for extra trials.

| Dataset | Epsilon | Bias | Population variance | MSE SE |
|---|---:|---:|---:|---:|
| karate | 0.5 | 13998.582 | 1.99747e+10 | 1.90707e+09 |
| karate | 1 | 2227.520 | 1.01051e+09 | 9.57928e+07 |
| karate | 2 | -893.674 | 6.31287e+07 | 6.25153e+06 |
| karate | 4 | -51.194 | 2.18983e+06 | 234248 |
| dolphins | 0.5 | 8068.091 | 1.09971e+11 | 1.13931e+10 |
| dolphins | 1 | 11435.717 | 5.95512e+09 | 6.47765e+08 |
| dolphins | 2 | -654.434 | 2.04189e+08 | 2.18895e+07 |
| dolphins | 4 | 105.215 | 7.47807e+06 | 820287 |
| les_miserables | 0.5 | -17072.120 | 2.53894e+11 | 2.37257e+10 |
| les_miserables | 1 | 2496.828 | 1.18935e+10 | 1.1171e+09 |
| les_miserables | 2 | 1497.199 | 3.90882e+08 | 3.45006e+07 |
| les_miserables | 4 | -307.456 | 2.56138e+07 | 2.65672e+06 |
| brightkite_50 | 0.5 | 4380.644 | 6.40887e+10 | 6.26264e+09 |
| brightkite_50 | 1 | -674.961 | 3.73804e+09 | 3.32003e+08 |
| brightkite_50 | 2 | -172.476 | 1.76976e+08 | 1.76434e+07 |
| brightkite_50 | 4 | 254.128 | 5.53434e+06 | 522985 |
| ba_n100 | 0.5 | 89080.479 | 1.11208e+12 | 1.14465e+11 |
| ba_n100 | 1 | 70233.662 | 1.51303e+11 | 1.506e+10 |
| ba_n100 | 2 | -19378.546 | 2.94424e+10 | 2.94954e+09 |
| ba_n100 | 4 | 2763.682 | 7.41058e+09 | 8.31869e+08 |
| sbm_n100 | 0.5 | -16189.790 | 5.75284e+11 | 5.92601e+10 |
| sbm_n100 | 1 | -4219.595 | 3.2343e+10 | 3.40432e+09 |
| sbm_n100 | 2 | -2672.527 | 1.51205e+09 | 1.83611e+08 |
| sbm_n100 | 4 | 832.529 | 2.69263e+08 | 2.60765e+07 |

## Execution and verification

`scripts/evaluate_four_path.py` adapts the existing K4 runner's SQLite/resume/
export structure and reuses graph loading, hashing, serialization and the full
P4 simulator. Each observation is committed separately. Validated prefix
coordinates and primary keys prevent duplicate trials; CSV exports are atomic.
Resume rejects altered config, code, dataset manifest, dependency versions,
reference pins or cached truth. Numerical errors stop rather than drop trials.

SQLite is authoritative after interruption; CSV exports may lag by a partial
cell. `run --resume` continues saved coordinates and exports metrics. Do not
change runner/config during resumption. New runs refuse existing output paths.
`verify` compares CSV/SQLite, reconstructs metrics and validates current inputs
and provenance without randomized replay. This runner targets the fixed config.

Artifacts in `experiments/results/four_path_six_datasets/` (Git-ignored):
config.json, trials.sqlite3, trials.csv, summary.csv, provenance.json,
escape_ground_truth.json, manifest.json, verification.json and
independent_verification.json. Transfer ignored outputs separately if needed.
No transcript file is saved; evaluation metadata is never inserted into the
modeled transcript. The complete research CSV is **not a DP release**.

Smoke stopped after 3 observations, resumed 45, and verified all 48. Focused
protocol tests: **13 passed, 73 deselected in 0.06s**. Main verification confirms
4,800 finite unique trial records, 24 cells of 200, correct budgets/seeds and
reproducible metrics. Separate standard-library statistics recomputation checks
every metric, including MSE SE, and coverage. A 198-file preservation comparison
found only the intended STATUS edit among pre-existing tracked/cache files.
All three reference fingerprints verified. No failures or skipped tests.

```bash
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase21/reference_fingerprints.json
.venv/bin/python scripts/evaluate_four_path.py run --smoke --max-new-trials 3
.venv/bin/python scripts/evaluate_four_path.py run --smoke --resume > build/phase21/smoke_resume.log
.venv/bin/python scripts/evaluate_four_path.py verify --smoke
.venv/bin/python -m pytest -q tests/test_four_path_protocol.py -k 'one_rr_same_object or replay_transcript_schema or stream_domains or controlled_assembly'
.venv/bin/python scripts/evaluate_four_path.py run > build/phase21/main_run.log
.venv/bin/python scripts/evaluate_four_path.py verify
git diff --check
```

Resume only if interrupted:
`.venv/bin/python scripts/evaluate_four_path.py run --resume`.
The Checkpoint 20 cache was present; missing-cache reconstruction was not needed
or exercised. Full historical regression and randomized replay were not run.

## Runtime and limitations

Summed complete-estimator time: **13.220280 seconds**. Cell means range
0.753–6.295 ms. Timings include the five-stage call and its validations; exclude
graph loading, offline truth, parameter construction, database commits and
summary/export work. Environment: macOS 27.0.1 arm64, Python 3.11.9,
NumPy 2.2.6, pandas 2.2.3, NetworkX 3.4.2. These are centralized local timings,
not network performance claims. Hashes and Git/reference pins are in provenance.

One fixed graph per dataset and 200 draws per cell limit generalization.
No analytical prediction, retained-triangle or cap-truncation diagnostics were
run, so no claims about truncation frequency or noise-component dominance are
made here. No numerical errors occurred in these supported configurations.

The estimator remains `experimental_unverified`. NumPy randomness, floating
point/error/timing behavior, physical transport and client isolation are not
certified. Experiments do not establish formal privacy or low-out-degree utility.

No estimator, dataset, third-party source, dependency pin, Phase 4B/5B output or
Checkpoint 20 result was modified. No baseline, tuning, plots, additional study,
commit or push. **Stop after this study.**
