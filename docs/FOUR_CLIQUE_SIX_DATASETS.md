# Six-dataset K4 evaluation — phase 19

Completed **2026-11-08 UTC**: **4,800 fresh estimates, 24 cells, 200 trials each**.
No abandoned estimates or smoke observations are included. Only the existing
`kcore_noisy_cap` simulator was evaluated; no baseline or other pattern was run.

## Setup and result interpretation

Inputs are the six unchanged files in `data/processed/graph_manifest.json`.
Their previously verified native ESCAPE counts were parsed and checked against
the manifest/configuration at startup: Karate 11, Dolphins 27, Les Misérables 639,
Brightkite-50:18, BA-100:18,198, SBM-100:99. No exact enumeration occurs in a trial.
The original native output/source hashes are copied into `escape_ground_truth.json`.
No fresh native execution is claimed for this phase.

Total epsilon is .5,1,2,4. Every call explicitly receives
`CliqueBudget(epsilon,epsilon/4,epsilon/4,epsilon/4,epsilon/4)` for O/D/R/C.
Beta=.05; kcore psi=.5, threshold_fraction=.5, bias_factor=1. No parameter tuning
or estimator modification. Main seed 202611081901; smoke seed 202611081900.
Coordinates are `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`, with
indices defined by the saved configuration. Each simulator retains its existing
four independent stage streams. These are research PRNGs, not secure DP noise.

MSE is the mean squared error against native ground truth. Variance uses the
population denominator N (`ddof=0`); every cell satisfies MSE=variance+bias².
RMSE, signed bias, MAE and relative RMSE are also saved. Undefined relative RMSE
is an empty field when truth is zero. All 2,436 negative estimates and all
non-integer values were retained.

Observed RMSE decreased with epsilon on each graph, but accuracy remains poor
relative to the true counts. Representative **epsilon=4** results follow; all
24 cells and all required metrics are in `summary.csv`.

| graph | exact_count | rmse | bias | mae | relative_rmse | runtime_mean_seconds |
|---|---|---|---|---|---|---|
| karate | 11 | 4333.83 | -433.604 | 3330.7 | 393.984 | 0.00186323 |
| les_miserables | 639 | 12412.1 | -120.386 | 9864.27 | 19.4243 | 0.00604784 |
| dolphins | 27 | 7406.26 | 929.948 | 5762.27 | 274.306 | 0.00435309 |
| brightkite_50 | 18 | 5252.71 | -99.1681 | 4012.41 | 291.817 | 0.00285745 |
| ba_n100 | 18198 | 67616.3 | 2697.13 | 55720.1 | 3.71559 | 0.0546044 |
| sbm_n100 | 99 | 25676.3 | 1913.5 | 20494.4 | 259.357 | 0.0158743 |

Mean runtime is seconds per complete private simulator call. The sum of measured
call times is **76.806352s**; lightweight offline orientation diagnostics add
0.617039s. These exclude SQLite/CSV overhead and are not a full pipeline timing.
Measurements are from the same WSL Linux environment; source/version records are
in `provenance.json` (Python3.11.16, NumPy2.2.6, NetworkX3.4.2, pandas2.2.3).
No distributed communication benchmark or scalability claim is made.

B=n-1 occurred in 1415/4800 trials (29.48%). No outgoing edges
were discarded in 4800 trials (truncation observed in 0 trials).
The CSV records caps, maximum outgoing degree, clipped vertices, discarded edges,
ordering rounds and local noise scale. Retained/lost clique counts were not
recomputed: edge truncation diagnostics are distinguished from exact motif loss.
Finite trials and a single fixed graph realization limit conclusions. No MSE
prediction campaign, bootstrap interval or formal privacy audit was repeated.
The executable remains `experimental_unverified`; empirical checks do not prove DP.

## Files, recovery and verification

- Independent script: `scripts/evaluate_four_clique.py`.
- Fixed config: `experiments/configs/four_clique_six_datasets.json`.
- Results: `experiments/results/four_clique_six_datasets/` (Git-ignored).
- `trials.sqlite3`: one committed observation per transaction; durable recovery.
- `trials.csv`: individual estimates, seeds, exact budgets, runtime and diagnostics.
- `summary.csv`: all 24 graph/budget results and population statistics.
- `manifest.json`: completion/counts and CSV/config/provenance hashes.
- `config.json`, `provenance.json`, `escape_ground_truth.json`: accepted setup/truth.

```bash
.venv/bin/python scripts/evaluate_four_clique.py run
# Resume only an existing run; configuration/source/input hashes must agree:
.venv/bin/python scripts/evaluate_four_clique.py run --resume
.venv/bin/python scripts/evaluate_four_clique.py verify
# Brief separate smoke test (does not contribute to the main study):
.venv/bin/python scripts/evaluate_four_clique.py run --smoke --max-new-trials 3
.venv/bin/python scripts/evaluate_four_clique.py run --smoke --resume
.venv/bin/python scripts/evaluate_four_clique.py verify --smoke
```

Existing directories require `--resume`; use `--output` for a separately named run.
The smoke saved 3 and resumed 45 observations, then verified all 48. Full verification
passed for all 4,800 observations/24 cells: CSV/SQLite equality, unique coordinate
seeds, exact quarter budgets, hashes and recomputed metrics. No extra randomized
study or full regression suite was run. Brief logs are under `build/phase19/`.

See [future evaluation conventions](EVALUATION_STANDARDS.md),
[cleanup/checkpoint](status/checkpoints/19_six_dataset_four_clique_evaluation.md),
and [current status](status/STATUS.md). Phase 18 outputs were discarded at the
owner's request; completed older research and reference pins are preserved.
**Stop here: no other pattern, baseline, tuning, new phase, commit or push.**
