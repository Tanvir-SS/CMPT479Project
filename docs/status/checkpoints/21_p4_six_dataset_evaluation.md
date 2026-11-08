# Checkpoint 21 — standardized six-dataset P4 evaluation

2026-11-08 (America/Vancouver). **COMPLETE. Stop; no commit or push.**

Owner authorized the fixed Milestone 3 P4 study after Checkpoint 20. Read AGENTS,
EVALUATION_STANDARDS, TEAM_SETUP, P4 implementation/accuracy/study reports,
STATUS/checkpoint 20, manifest, cache and existing experiment infrastructure.
Preserved the pre-existing uncommitted Checkpoint 20/STATUS documentation.

## Completed work

- Added `scripts/evaluate_four_path.py`, adapted from the existing resumable K4
  runner, invoking unchanged `simulate_four_paths_private` for all five stages.
- Added `experiments/configs/four_path_six_datasets.json`: exactly six saved
  graphs, 200 trials/cell, epsilon .5/1/2/4, D/O/R/M/C=.30/.10/.25/.15/.20.
  Beta .05; k-CoreD psi .5, threshold_fraction .5, bias_factor 1.
- Reused Checkpoint 20 P4 cache, verifying hashes and saved native 3-path values.
  No graph regeneration or native recount; no exact work inside private trials.
- Completed **4,800 fresh finite estimates**, 24 cells of 200 unique trials.
  Main master 202611082101; separate smoke master 202611082100; coordinate rule
  `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`. Config fixes order.
- Saved SQLite after every trial and atomic CSV exports after each cell. Resume
  validates coordinates, config and source/data/dependency/reference provenance.
- Computed direct MSE, RMSE, bias, population variance, MAE, relative RMSE,
  MSE SE (sample standard deviation of squared errors / sqrt(N)), and runtime.
- Created `docs/FOUR_PATH_SIX_DATASETS.md` with all 24 results, metric appendix,
  interpretation, methodology, commands and limitations; updated STATUS.

## Commands and observed checks

```bash
.venv/bin/python build/phase21/adapt_runner.py
.venv/bin/python scripts/evaluate_four_path.py run --smoke --max-new-trials 3
.venv/bin/python scripts/evaluate_four_path.py run --smoke --resume > build/phase21/smoke_resume.log
.venv/bin/python scripts/evaluate_four_path.py verify --smoke
.venv/bin/python -m pytest -q tests/test_four_path_protocol.py -k 'one_rr_same_object or replay_transcript_schema or stream_domains or controlled_assembly'
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase21/reference_fingerprints.json
.venv/bin/python scripts/evaluate_four_path.py run > build/phase21/main_run.log
.venv/bin/python scripts/evaluate_four_path.py verify
git diff --check
git status --short
```

All execution commands exited 0. Smoke stopped at 3, resumed 45 and verified 48
observations across all 24 settings. Focused tests: **13 passed, 73 deselected
in 0.06s**, no skips/failures. Main verification: 4,800 trials, 24 cells, zero
remaining; all seeds unique, finite estimates, correct allocation, CSV/SQLite
agreement and reproducible summaries. MSE=population variance+bias² passes.

An additional inline `.venv/bin/python -` check used csv/math/statistics to
independently recompute every summary metric (including sample-based MSE SE),
require exactly trial IDs 0..199 in every cell, and compare 198 pre-existing
tracked/cache hashes to `build/phase21/preservation_before.json`. Only intended
STATUS changes were found; Checkpoint 20 cache, graphs, manifest, private code,
dependencies and prior tracked outputs are unchanged. Receipt:
`experiments/results/four_path_six_datasets/independent_verification.json`.
All three reference fingerprints verify; no source writes were performed.

One attempted documentation-generation tool call had a JavaScript parsing error
before execution; retried successfully in smaller calls. This did not affect
experiment execution or results. No experimental failure or unsupported budget.

## Artifacts and findings

`experiments/results/four_path_six_datasets/` contains config.json, trials.csv,
summary.csv, trials.sqlite3, provenance.json, escape_ground_truth.json,
manifest.json, verification.json and independent_verification.json. Generated
artifacts remain ignored; source/config/report/checkpoint are ordinary files.
`build/phase21/` holds separate smoke outputs, logs and preparation evidence.
Git HEAD during execution: d930c5031354b76ba2c2698eaea6291599b14742.
No dependencies installed/upgraded: Python 3.11.9, NumPy 2.2.6, pandas 2.2.3,
NetworkX 3.4.2, macOS 27.0.1 arm64. Provenance saves exact code/reference hashes.

RMSE decreases at every epsilon step on each graph. Karate has lowest absolute
RMSE; BA-100 lowest relative RMSE. Largest relative RMSE is Dolphins at .5:
6603.95%. At epsilon 4 relative RMSE ranges 4.21% (BA100) to 62.45% (Karate).
All **1,098 negative estimates** retained. Variance contributes 96.84%–99.99%
of MSE, so close means in some cells do not demonstrate accurate estimates.
MSE SE/MSE ranges 8.78%–12.09%. Summed mechanism time 13.220280 seconds;
cell means .753–6.295 ms, excluding offline evaluation/storage.

## Limitations and stopping point

No full historical regression, randomized full replay, Phase 4B/5B rerun,
baseline, extra predictions, plots, budget tuning or other pattern experiment.
No truncation-frequency diagnostic; do not infer absence of truncation.
The ignored truth cache was available; reconstruction was not needed/tested.
Runtime is centralized process time; statistical uncertainty and one graph per
dataset limit generalization. Research CSVs contain seeds/exact truth and are
not private releases. Privacy remains experimental_unverified; tests provide
no mathematical privacy certification.

All requested completion criteria met. No new phase, commit or push. Any future
study needs separate authorization. Preserve ignored artifacts for handoff.
