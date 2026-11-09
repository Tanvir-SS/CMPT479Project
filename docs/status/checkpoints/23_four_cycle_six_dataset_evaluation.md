# Checkpoint 23 — full balanced wedge-Laplace C4 evaluation

2026-11-09 (America/Vancouver). Owner explicitly authorized the full standardized
C4 study following Checkpoint 22. This supersedes the earlier smoke-only stopping
point for this task. Preserve all previous uncommitted implementation work.

## Scope and preflight

Read the pasted full-evaluation request, STATUS/checkpoint 22, existing runner and
configuration, and EVALUATION_STANDARDS. The previously read Milestone 3 workflow
Sections 6–9 define the same six-input, four-budget, 200-trial conventions.

An inline `.venv/bin/python` preflight asserted Python 3.11 in a virtual
environment, invoked the existing runner's `load_inputs`, and confirmed exactly
4,800 coordinates. Python is 3.11.9, executable project `.venv/bin/python`.
All six graph and mapping hashes match the manifest. Native C4 counts match
154/278/2672/198/207959/7302 in configured graph order. No main output directory
existed, so no prior main results were overwritten. Recorded SHA256 of all
pre-existing tracked and untracked nonignored regular files to
`build/phase23/preservation_before.json` before updating STATUS.

Checkpoint 22 records all 20 focused tests and eight GNU-compiled native ESCAPE
fixture checks passing. These were not rerun; the unchanged mechanism/runner
hashes are checked against saved smoke provenance by its verification command.
No new smoke trials, full regression or native recount were needed.

## Commands

```bash
.venv/bin/python scripts/evaluate_four_cycle.py verify --smoke
.venv/bin/python scripts/evaluate_four_cycle.py run > build/phase23/main_run.log
.venv/bin/python scripts/evaluate_four_cycle.py verify
.venv/bin/python build/phase23/verify_and_report.py > build/phase23/independent_analysis.log
git diff --check
git status --short
```

The analysis helper is ignored and performs no mechanism trials. It independently
uses Python csv/statistics to recompute metrics from saved observations, checks
cell trial IDs, seed uniqueness, noise scale, endpoint allocations and schedule
size, verifies preservation hashes, and generates the report's results tables.
Simulation seeds and exact truth remain exclusively non-private evaluation data.

## Preserved implementation and dependencies

No changes to estimator, exact helper, tests, runner, config, seed scheme, noise,
sensitivity, normalization, references, dependencies, fixtures or datasets.
Main master 202611092201 with `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`;
smoke master 202611092200 remains separate. Exactly .5/1/2/4, 200 trials per cell.
No dependency installation, upgrade, baseline, tuning, other pattern, plots,
commit or push. Existing Phase-22 files and historical checkpoints are preserved.

## Artifacts

Main output: `experiments/results/four_cycle_six_datasets/` (Git-ignored).
Required config/provenance/native-truth JSON, trials/summary CSV, manifest and
SQLite are produced by the unchanged runner, with one SQLite commit per trial.
Additional verification and independent-verification JSON capture completed checks.
`build/phase23/` holds run log, preservation snapshot and analysis helper/output.
Report: `docs/FOUR_CYCLE_SIX_DATASETS.md`. Updated STATUS and this new checkpoint
are the only other task documentation changes.

## Completed outcomes and phase checklist

- [x] Preflight environment, saved smoke, configuration and six native truths pass.
- [x] All 4,800 fresh main trials completed; no failures or resume required.
- [x] Runner verification: verified/complete, 24 cells, zero remaining trials.
- [x] Independent metric, identifier, seed and preservation checks pass.
- [x] Report all 24 cells, runtime, accuracy limitations and completion status.
- [x] Update STATUS and stop within scope.

All listed execution commands exited 0. Main execution has 200 observations per
cell, IDs 0..199, 4,800 distinct seeds and composite trial identifiers. All 2,376
negative and all 4,800 noninteger values remain saved. Native truth/provenance,
CSV/SQLite agreement and population MSE identity verify. Independent preservation
receipt reports only the intended STATUS modification among pre-existing files.

RMSE decreases with epsilon on every graph, but relative errors are enormous.
Best relative RMSE is BA-100 at epsilon 4: 41.3282 times truth; worst is Dolphins
at .5: 590,490.13 times truth. Variance accounts for 97.9734%–99.9988% of MSE.
Total estimator runtime 54.015406 seconds; cell mean 2.3263–20.2860 ms. These are
fixed-study observations, not universal utility or formal privacy conclusions.
Python 3.11.9, NumPy 2.2.6, pandas 2.2.3, NetworkX 3.4.2, macOS 27.0.1 arm64.

No errors or unresolved execution issues in this phase. Skipped intentionally:
new test runs, native recounts, full regression, simulation replay, plots,
baselines and additional experiments. Prior focused tests were confirmed from
Checkpoint 22 and source preservation/smoke provenance, not relabeled as fresh
passes. Finite samples, large b, NumPy/floating-point and physical-timing privacy
limitations remain. No empirical test proves LEDP or the asymptotic bound.

**COMPLETE. Stop after this authorized evaluation; no commit or push.**
