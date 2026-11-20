# Checkpoint 30 — RR-only diamond evaluation, 20 trials per cell

2026-11-19 (America/Vancouver). **COMPLETE.** The owner authorized direct use of
the existing evaluation script for six datasets, epsilon .5/1/2, 20 trials per
dataset/budget and seed 42. No code changes, additional tests, separate
verification, figures, estimator redesign, commit or push were authorized or done.
Only the mandatory STATUS update and this checkpoint were written as documentation.

## Command and outcome

Executed from `/home/tsshergi/CMPT479Project`:

```bash
.venv/bin/python scripts/evaluate_diamond_rr_only.py run --trials 20 --seed 42 --output experiments/results/diamond_rr_only_six_datasets_20_seed42
```

Observed exit 0. The existing runner reported **360 new trials, 360 complete,
zero remaining**. Its saved configuration uses 20 trials, leaving the script's
default 200 unchanged. Seed 42 is the master seed consumed by the existing
coordinate-derived seed rule; seeds are recorded in the trial CSV. Epsilon_RR
equals each total epsilon, while ordering and Laplace allocations remain zero.
The existing post-processing retains negative and fractional estimates.

No separate `check`/`verify` command, pytest, sensitivity/probability check,
native build/count or additional simulation was run. Only the runner's own
existing input checks and per-cell export computations executed. No independent
verification or new test pass is claimed.

## Ground-truth source discrepancy

The request named `expected_counts.json`. The only such repository file,
`data/fixtures/expected_counts.json`, contains the eight small correctness
fixtures, not Karate/Dolphins/Les Misérables/Brightkite/BA/SBM. The existing
script does not accept a truth-file override; it reads the cached native ESCAPE
diamond column from `data/processed/graph_manifest.json`. This was explicitly
reported before running the unchanged script. No ground-truth file or count
was altered and no fixture counts were substituted for the benchmark counts.

Actual truths used: Karate 151, Dolphins 300, Les Misérables 4544,
Brightkite-50 245, BA-100 217982, SBM-100 3093. These are the existing script's
non-induced diamond counts; they are **not** attributed to expected_counts.json.
Native output/source provenance is saved in `escape_ground_truth.json`.

## Results and terminal display

Output directory: `experiments/results/diamond_rr_only_six_datasets_20_seed42/`.

- `trials.csv`: all 360 individual estimates, settings, seeds, exact truth/runtime.
- `summary.csv`: all 18 cells, including true count, mean, bias, MSE and RMSE.
- Existing runner also saved SQLite, config/provenance/native truth and manifest.

After completion, an inline standard-library CSV reader printed all 18 rows
with dataset, epsilon, exact_count, mean_estimate, bias, mse and rmse. It read
saved summaries only and neither recomputed metrics nor executed the estimator.
An initial display-only format specifier `>7:g` raised ValueError; correcting
it to `>7g` printed the full table successfully. No evaluation trial was rerun,
and no code file or output CSV changed in resolving this display typo.
Displayed values use nine significant digits; saved CSV precision is unchanged.

No figures/plots, extra analysis or comparisons were produced. All prior
mechanisms, the shared RR implementation, datasets and defaults were left alone.
No dependencies installed. No Git commit or push. **STOP after this run.**
