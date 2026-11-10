# Diamond accuracy on the six standardized datasets

2026-11-10 UTC. Fixed no-clipping evaluation of the existing
`private_graphlets.diamond.estimate_diamonds` simulator; all 4,800 trials are complete. The estimator remains
`experimental_unverified`. This study does not certify executable LEDP.

## Fixed setup

Use the six unchanged graphs resolved from `data/processed/graph_manifest.json`,
200 independent simulation seeds per graph/budget, and these explicit
`DiamondBudget` allocations:

| Total epsilon | Ordering O | RR R | Wedges W |
|---:|---:|---:|---:|
| 0.5 | 0.125 | 0.1875 | 0.1875 |
| 1 | 0.25 | 0.375 | 0.375 |
| 2 | 0.5 | 0.75 | 0.75 |
| 4 | 1 | 1.5 | 1.5 |

O+R+W equals the total; O<=1 throughout. No default allocation is used.
The existing noised k-CoreD ordering, all-pair RR and full noisy wedge vectors
execute on every trial, with unchanged k-CoreD defaults. No final noise is added.

| Dataset | Vertices n | Edges m | Exact non-induced diamonds | Public B=n−1 |
|---|---:|---:|---:|---:|
| Karate Club | 34 | 78 | 151 | 33 |
| Dolphins | 62 | 159 | 300 | 61 |
| Les Misérables | 77 | 254 | 4,544 | 76 |
| Brightkite-50 | 50 | 97 | 245 | 49 |
| BA-100 | 100 | 1,600 | 217,982 | 99 |
| SBM-100 | 100 | 760 | 3,093 | 99 |

Ground truth is the existing native ESCAPE `chordalcycles`/diamond column, with
raw output and source provenance copied from the pinned manifest. No new exact
enumeration or native build/run was performed. A K4 contributes six diamonds.

B=n−1 depends only on public n and retains every actual outgoing neighbor under
every ordering. Thus this study has no clipping bias under the ideal estimator
analysis. The scale is still **2(B−1)/W**, without reduction. Eliminating clipping
does not eliminate RR or Laplace variance; finite-sample empirical bias can also
be nonzero. This setting may introduce substantially more wedge noise than a
tighter cap, so it does not establish optimal low-out-degree performance.

Master seed **202611102501**; each trial uses
`(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`, with graph indices
in the table's order, budget indices .5/1/2/4 and trial indices 0..199.
Saved seeds (decimal strings; read CSV seeds as strings) and exact counts are
non-private evaluation records, never private mechanism releases.
Seeded/unseeded NumPy are research simulators.

## Metrics and reproduction

For estimates x_t and truth D: mean=mean(x), bias=mean−D, population variance
uses ddof=0, MSE=mean((x−D)²) directly, RMSE=sqrt(MSE), MAE=mean(|x−D|).
Mean Relative Error (MRE)=MAE/D; relative RMSE=RMSE/D. Neither relative metric
is the absolute relative bias; zero truth would yield an empty relative field.
All six truths are positive. Runtime is the complete estimator call only,
excluding input loading, durable storage, summary computation and plotting.
Negative and noninteger estimates are preserved.

```bash
# Fresh run only: refuses an existing output directory.
.venv/bin/python scripts/evaluate_diamond.py run
# Recover after interruption without repeating saved observations.
.venv/bin/python scripts/evaluate_diamond.py run --resume
.venv/bin/python scripts/evaluate_diamond.py verify
# Regenerate the single plot from saved summary data; no new trials.
.venv/bin/python scripts/evaluate_diamond.py plot
```

Configuration: `experiments/configs/diamond_six_datasets.json`. Results are under
`experiments/results/diamond_six_datasets/`: `trials.csv`, `summary.csv`,
`trials.sqlite3`, executed `config.json`, `provenance.json`,
`escape_ground_truth.json`, `manifest.json`, and verification/progress records.
SQLite commits and CSV flushes each observation; resume restores CSV from SQLite.
Source/data/mapping hashes, native evidence, versions and all seeds are recorded.
Generated results/plots remain Git-ignored. The report and configuration are
reviewable source files; another run should use a fresh `--output` directory
to preserve existing observations (runtime measurements are hardware-dependent).

## Measured results

**Complete: 4,800/4,800 trials, 24 cells with 200 each.** Minimal saved-output
verification passed: unique coordinates/seeds, B=n−1, all fixed budgets/scales,
CSV/SQLite agreement, summary metrics and population MSE identity. No errors
or incomplete trials. The first main observation was saved separately and
the remaining 4,799 resumed without repeating it; no extra trials were run.

Values below are rounded for readability; full-precision CSVs also contain
population variance, direct MSE and relative RMSE for every cell.

| Dataset | ε | Mean estimate | Bias | RMSE | MAE | MRE | Mean ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| Karate Club | 0.5 | 28689 | 28538 | 2.4219e+06 | 1.979e+06 | 13106 | 14.41 |
| Karate Club | 1 | -531.8 | -682.8 | 75004 | 60328 | 399.52 | 14.19 |
| Karate Club | 2 | 103.06 | -47.943 | 2519.7 | 1949.1 | 12.908 | 13.88 |
| Karate Club | 4 | 132.8 | -18.203 | 168.1 | 134.76 | 0.89245 | 12.83 |
| Dolphins | 0.5 | 4.6963e+05 | 4.6933e+05 | 9.025e+06 | 7.0716e+06 | 23572 | 73.86 |
| Dolphins | 1 | -22121 | -22421 | 2.4794e+05 | 2.0153e+05 | 671.76 | 75.65 |
| Dolphins | 2 | -458.12 | -758.12 | 7228.1 | 5714.8 | 19.049 | 76.01 |
| Dolphins | 4 | 302.02 | 2.0247 | 390.58 | 309.87 | 1.0329 | 80.66 |
| Les Misérables | 0.5 | 19937 | 15393 | 1.371e+07 | 1.0807e+07 | 2378.3 | 208.6 |
| Les Misérables | 1 | -43223 | -47767 | 3.8158e+05 | 3.0556e+05 | 67.246 | 161.1 |
| Les Misérables | 2 | 3985.6 | -558.43 | 12894 | 10366 | 2.2813 | 164.8 |
| Les Misérables | 4 | 4581 | 36.975 | 1371 | 1113.4 | 0.24502 | 144.2 |
| Brightkite-50 | 0.5 | 4.4623e+05 | 4.4599e+05 | 5.5051e+06 | 4.3054e+06 | 17573 | 39.65 |
| Brightkite-50 | 1 | -890.59 | -1135.6 | 1.6863e+05 | 1.3673e+05 | 558.06 | 40.72 |
| Brightkite-50 | 2 | 317.66 | 72.655 | 5203.9 | 4152.3 | 16.948 | 38.31 |
| Brightkite-50 | 4 | 234.28 | -10.718 | 306.23 | 249.08 | 1.0167 | 39.76 |
| BA-100 | 0.5 | -1.0988e+06 | -1.3168e+06 | 2.122e+07 | 1.6893e+07 | 77.499 | 305.9 |
| BA-100 | 1 | 1.7558e+05 | -42399 | 8.1326e+05 | 6.5362e+05 | 2.9985 | 315.4 |
| BA-100 | 2 | 2.2501e+05 | 7025.1 | 83937 | 66274 | 0.30403 | 316.9 |
| BA-100 | 4 | 2.1551e+05 | -2471.7 | 29251 | 23688 | 0.10867 | 307.3 |
| SBM-100 | 0.5 | 5.4714e+05 | 5.4404e+05 | 1.9685e+07 | 1.5487e+07 | 5007.1 | 298.9 |
| SBM-100 | 1 | -2436.6 | -5529.6 | 7.1508e+05 | 5.6914e+05 | 184.01 | 321.9 |
| SBM-100 | 2 | 2493.9 | -599.12 | 24578 | 20185 | 6.526 | 319.2 |
| SBM-100 | 4 | 3035.3 | -57.71 | 1786 | 1426.8 | 0.46131 | 340.2 |

MRE decreases with epsilon on **6 of six** graphs. At epsilon 4,
the observed MRE values (ratios, not percentages) are Karate Club 0.89245, Dolphins 1.0329, Les Misérables 0.24502, Brightkite-50 1.0167, BA-100 0.10867, SBM-100 0.46131.
These describe the fixed graph instances and 200 observations per setting;
they do not establish universal utility or improvement over another estimator.

All **1,822 negative** and **4,800 noninteger** observations are retained.
Summed estimator-call runtime is **744.832675 seconds**; this excludes
storage, setup, verification and plotting. Existing Python 3.11.16, NumPy
2.2.6, pandas 2.2.3 and Matplotlib 3.10.1 ran on Ubuntu WSL2 x86_64
(eight logical CPUs reported; sequential trial execution).

## Accuracy plot

![Mean relative diamond error on four real-world datasets](../plots/diamond_six_datasets/mean_relative_error.png)

The logarithmic y-axis shows MAE divided by the exact non-induced count.
This single plot is generated directly from saved summary.csv, using the
line/marker/grid style of earlier K4/P4 plots. Its provenance JSON records
the source summary hash and image hash. No other plot or sweep was made.

## Limits and stopping point

No clipping bias does not mean zero error: RR and Laplace randomness remain,
and only 200 trials estimate each error distribution. Large B increases the
required wedge noise and can shift the public hybrid weight toward RR.
This is an untuned no-clipping reference, not optimal performance of the
low-out-degree approach. No alternate cap, allocation or baseline was tested.
Private k-CoreD and full-transcript privacy assumptions, finite arithmetic,
NumPy randomness and centralized simulation retain their existing limitations.
Empirical accuracy does not prove differential privacy.

The 49 diamond tests, 25 k-CoreD tests, exhaustive audits and additional
Monte Carlo checks were deliberately **not rerun**. The checks in this phase
only concern the saved requested study and its artifact provenance.
No estimator, proof, dataset, dependency or previous result was changed;
no commit or push. See [checkpoint 25](status/checkpoints/25_diamond_six_dataset_evaluation.md).
**Complete; stop pending an explicit follow-up instruction.**
