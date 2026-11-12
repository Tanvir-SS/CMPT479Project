# Checkpoint 27 — uniform-sampling RR C4 Stage 5

2026-11-11 (America/Vancouver). **COMPLETE. Stop before Stage 6.**
The new owner request explicitly authorizes the fixed evaluation after checkpoint
26, including a small separate smoke. Estimator redesign/optimization, old-study
reruns, Stage 6 comparison, baselines, plots and other patterns are excluded.

## Inspection and files

Read the supplied Stage 5 attachment, STATUS/checkpoint 26, RR implementation and
report, previous C4 runner/config, EVALUATION_STANDARDS, TEAM_SETUP, dataset manifest,
graph loading, exact C4 helper and cached ESCAPE parsing conventions.
`ProjectWorkflow.md` was absent in repository/hidden-file name searches; followed
the explicit request and evaluation standards. No missing workflow content is
claimed to have been read. The previous uncommitted Stage 3–4 additions and STATUS
edit were preserved; starting Git HEAD was `2ec1484eb117ed1ace325410309c530a2c6384e3`.

Created:

- `scripts/evaluate_four_cycle_uniform_rr.py` — independent runner adapted from
  the previous runner's storage/metrics conventions, without editing that runner.
- `experiments/configs/four_cycle_uniform_rr_six_datasets.json` — six hashes/paths,
  truth, four budgets, 200 trials/cell, q rule, alpha rule, seed mapping/environment.
- `docs/FOUR_CYCLE_UNIFORM_RR_SIX_DATASETS.md` — full 24-cell results and limitations.
- This checkpoint. Updated only `docs/status/STATUS.md` among pre-existing files.

All results exclusively under `experiments/results/four_cycle_uniform_rr_six_datasets/`:
main CSVs/SQLite/config/provenance/native-truth cache/manifest/verification and an
independent `smoke/` directory. Logs, read-only verification evidence and helper
scripts are under ignored `build/phase27/`. No dependencies were added or upgraded.

## Dataset verification and fixed protocol

All six files and mappings match manifest SHA-256 and n/m. Once before simulation,
`count_four_cycles` independently agreed with cached native ESCAPE's named
`connected_four['4-cycle']` column (not the K4 column):

| Graph | n | m | C4 | q |
|---|---:|---:|---:|---:|
| karate | 34 | 78 | 154 | 58 |
| dolphins | 62 | 159 | 278 | 193 |
| les_miserables | 77 | 254 | 2672 | 297 |
| brightkite_50 | 50 | 97 | 198 | 125 |
| ba_n100 | 100 | 1600 | 207959 | 500 |
| sbm_n100 | 100 | 760 | 7302 | 500 |

Exact truth was not recomputed inside randomized trials. Original native output
and source hashes are copied into `escape_ground_truth.json`. All three bundled
references fingerprint verified in place. No new native build/execution needed;
original `/home/tsshergi` paths are unavailable on this Mac, so only bundled
checkouts are claimed verified. No source, pin, dataset or manifest changes.

Total epsilon .5/1/2/4, q=(n*n+19)//20, two reports per candidate, unchanged
participation-adjusted alpha. Each release's q, 2q requests/reports, sum K=4q,
binary responses, finite estimate and exact per-request alpha formula checked
outside timing. No change to estimator source or its randomness, scaling or caps.

Main master seed 202611112701; smoke master 202611112700. Fixed ordered dataset
and epsilon identifiers map to `(master<<64)|(gi<<48)|(ei<<32)|trial`.
Preflight checked all 4,800 distinct main seeds; final check confirms disjointness
from smoke. Seeds are non-private research metadata, not protected releases.

## Exact execution commands and outcomes

Helper source files remain in build/phase27. Preparation captured preservation
hashes and wrote the new runner/config; preflight called the exact helper once
per graph and checked seeds. Report/finish only read saved observations and update
documentation/preservation receipts, never call an estimator.

```bash
mkdir -p build/phase27
.venv/bin/python build/phase27/prepare.py
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase27/reference_fingerprints.json
.venv/bin/python build/phase27/preflight.py
.venv/bin/python scripts/evaluate_four_cycle_uniform_rr.py run --smoke --max-new-trials 1 > build/phase27/smoke_initial.log
.venv/bin/python scripts/evaluate_four_cycle_uniform_rr.py run --smoke --resume > build/phase27/smoke_resume.log
.venv/bin/python scripts/evaluate_four_cycle_uniform_rr.py verify --smoke
.venv/bin/python scripts/evaluate_four_cycle_uniform_rr.py run --smoke --resume > build/phase27/smoke_noop_resume.log
.venv/bin/python scripts/evaluate_four_cycle_uniform_rr.py run > build/phase27/main_run.log 2>&1
.venv/bin/python build/phase27/update_status.py
.venv/bin/python scripts/evaluate_four_cycle_uniform_rr.py verify > build/phase27/verification.log
.venv/bin/python build/phase27/report.py
.venv/bin/python build/phase27/finish.py
git diff --check
git status --short
git check-ignore experiments/results/four_cycle_uniform_rr_six_datasets/trials.csv experiments/results/four_cycle_uniform_rr_six_datasets/summary.csv
```

All execution/verification commands succeeded; no failed trial or skipped requested
check. Smoke uses four Karate/epsilon .5 calls: one initial, three resumed, then
zero new on completed resume. Estimates include −104707.61009053867 unchanged.
All smoke values finite, sizes correct, exact CSV/SQLite round-trip successful,
and MSE decomposition passes. Smoke is not pooled into the main run.

Main completed **4,800/4,800**, all 24 cells × 200, no duplicate IDs or seeds, no
missing/nonfinite observations. Saved-output verification checks artifact hashes,
CSV/SQLite exact equality, summary recomputation, ddof=0 MSE decomposition,
config/source/dependency/reference provenance and unchanged graph hashes/truth.
The report helper independently checks cell sizes, unique coordinates and smoke
seed separation. No extra simulations, replay trials or empirical DP tests.

Runtime covers only each complete estimator call, measured with perf_counter.
Sum: **11.499573740642518 seconds**; excludes checks, serialization and offline
truth. macOS 27.0.1 arm64, 12 logical CPUs, Python 3.11.9, NumPy 2.2.6, pandas 2.2.3,
NetworkX 3.4.2; sequential run. Full provenance records versions and source hashes.

## Findings and limits

All 24 cells are tabulated in the report. MSE falls monotonically with epsilon
on every graph. Relative RMSE ranges from .68500038 (BA-100, epsilon 4) to
5584.23191 (Dolphins, epsilon .5). Variance contributes 97.844–99.993% of MSE.
All **2,319 negative estimates (48.3125%)** and **4,800 noninteger estimates** remain.
Empirical bias may be large relative to sparse truth; the largest standardized
sample-mean error is about 2.094 sample standard errors, a descriptive statistic
rather than an unbiasedness proof or multiple-comparison-adjusted test.

Two hundred trials per cell give limited moment precision. Uniform sampling can
miss rare cycles; random participation alters RR variance. Asymptotic O(n³) RMSE
does not imply good finite relative error. NumPy PRNGs and floats do not certify
production pure-LEDP; deployment isolation and side channels remain out of scope.
No privacy claim is inferred from experiments. No unresolved execution errors.

The preservation receipt compares all snapshotted existing files and allows only
the intended STATUS change. Earlier RR/Laplace modules/tests/reports, all previous
results/configs, other-pattern implementations, data/mappings, dependency locks
and reference contents remain byte-identical; no pre-existing file is missing.
Results are Git-ignored. No staging, commit or push.

Deliberately skipped: repeated Stage 4 pytest/native checks, full regression,
additional Monte Carlo, old-study reruns, Stage 6 comparisons, baselines, plots,
tuning and other patterns. **STOP after Stage 5; await owner review.**
