# Checkpoint 14 — P4 Phase 4B accuracy study

Date: **2026-11-06 (America/Vancouver)**. Status: **COMPLETE; stop before Phase5**.
This completes the interrupted P4 Phase4B request, not the independent dataset
preparation work in checkpoint13. Predeclared schema/config/result names retain
`phase13`; this checkpoint uses14 to preserve existing history.

## Starting state and saved work

Resume inspection: clean Git working tree, HEAD`86f7ed3` (Real world Graph data).
User expressly authorized continuation of the P4 study and superseded the
completed dataset-only stopping point for this scope. Read current AGENTS,
STATUS/checkpoint13, prior P4 request/checkpoint12 and saved implementation.
No private algorithm, reference, dependency, dataset or Phase4A result changed.

Already saved before interruption (subsequently committed by others):

- `src/private_graphlets/four_path_study.py`
- `scripts/run_four_path_study.py`
- `tests/test_four_path_study.py`
- `experiments/configs/four_path_phase13_accuracy.json`
- `experiments/configs/four_path_phase13_smoke.json`
- Shared internal run/verify engines and streaming transcript replay in
  `src/private_graphlets/four_path_experiments.py`, preserving Phase4A public limits.

These files were present in`6fba863`;`99d542a` additionally normalized nulls in
study replay. No Phase4B smoke/full result directory existed at resume. The
original interrupted test process returned **1 failed,40 passed in12.54s**:
zero-truth replay compared None versus CSV NaN under warnings-as-errors. The
intervening replay normalization addressed it. Resumed work additionally uses
NaN directly when aggregating undefined relative RMSE; the explicit false flag
is preserved. No numerical tolerance or valid metric changed.

Before the interruption a fresh baseline had **659 passed in22.41s**. Since
then unrelated authorized repository work expanded the suite. Do not confuse
that historical baseline with the new821-test result below.

## Work completed after resumption

- Confirmed saved matrix and source inventory, preserved intervening work.
- Normalized undefined relative RMSE at its producer; current targeted tests pass.
- Saved resource/precision plan, ran actual ESCAPE smoke and full replay.
- Executed the unchanged30-cell matrix and all four fixed-history controls.
- Verified native truth for13 study graphs and K4/K10 controls (15 graphs).
- Verified hashes/inventory, all summary metrics, analytical contributions and
  deterministic replay of18,000 full outputs and12,000 prediction histories.
- Generated six PNG/PDF figures, visually inspected all six PNGs.
- Wrote complete tables, interpretations, resource results and limitations in
  `docs/FOUR_PATH_STUDY.md`; updated README and STATUS.

Resumed tracked changes: `src/private_graphlets/four_path_study.py` (one-line
undefined-metric normalization), `README.md`, `docs/status/STATUS.md`.
New documents: `docs/FOUR_PATH_STUDY.md` and this checkpoint. Saved Phase4B configs,
runner, tests and Phase4A shared-engine implementation were not rewritten.

## Fixed design

Config`experiments/configs/four_path_phase13_accuracy.json`:13 graph instances,
30 cells,600 full trials and400 prediction histories per cell. Master202611051304.
A: ER p=.05/.30 and BA m=1/4 at n20/50/100, pilot budget2/.5/1/1/2 (12 cells).
B: unchanged ER(.30,n50) and BA(m4,n50), total1/2/4/8 with fractions
.30/.10/.25/.15/.20 (8 cells). C: same instances, total4, three predeclared
balanced/degree/RR allocations (6 cells). D2: K20 and BA(m4,n50), cap epsilon
.5/2, other stages unchanged, beta=.9 (4 cells). A–C use beta=.05.
D1: fixed ascending order K4 caps1/2 and K10 caps2/4, evaluation-only controls.

Predeclared discrepancy3 combined SE; precision threshold15% relative combined
SE. No seed, budget, graph, sample size, tolerance or output selection was tuned.
Smoke uses a separate seed and3+3 trials on four cells; it was not used for
accuracy inference. Plan estimated5–20 minutes including replay and <1GB memory
and storage. Actual smoke supported bounded execution; no expansion occurred.

## Exact commands and actual outcomes

Interrupted command (historical failure, preserved separately):

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_four_path_study.py tests/test_four_path_experiments.py
```

**1 failed,40 passed in12.54s**, zero skips; resolved null-representation warning
as described above. It was not a privacy/statistical or algorithm failure.

Resumed targeted new/Phase4A/3/2/1 run:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_four_path_study.py tests/test_four_path_accuracy.py tests/test_four_path_experiments.py tests/test_four_path_protocol.py tests/test_triangle_protocol.py tests/test_four_path_exact.py
```

**288 passed in16.73s**, zero failures/errors/skips. Includes all21 new study
cases, deterministic moment tests, native ESCAPE tests, zero-truth behavior,
invalid configurations, seed separation, fixed controls, contribution sums,
non-overwrite guards, corruption detection, plot smoke and full replay.

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

**821 passed in31.25s**, zero failures/errors/skips. All existing tests preserved.

```bash
.venv/bin/python scripts/run_four_path_study.py plan
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python scripts/run_four_path_study.py run --config experiments/configs/four_path_phase13_smoke.json --output experiments/results/four_path_phase13_smoke
.venv/bin/python scripts/run_four_path_study.py verify --output experiments/results/four_path_phase13_smoke --replay
mkdir -p build/phase13/matplotlib
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python scripts/run_four_path_study.py run
.venv/bin/python scripts/run_four_path_study.py verify --replay > build/phase13/p4_study_replay.json
.venv/bin/python scripts/run_four_path_experiments.py verify --replay
.venv/bin/python -B scripts/reference_fingerprints.py --verify
git diff --check
```

All exit0. Smoke:4 cells,12+12 trials,8.479741s,490,536 artifact bytes,
172,457,984 peak RSS bytes. Full:30 cells,18,000+12,000 trials,77.698711s,
318,410,150 artifact bytes excluding root manifest,284,721,152 peak RSS bytes.
Replay verified all full outputs and prediction histories; status saved in
`build/phase13/p4_study_replay.json`. Existing Phase4A replay also verified its
1,500+1,500 trials, with no result rewrite. All three reference pins verified
clean. Eight protected mechanism files match pre-interruption SHA-256 values.

Native compilation emitted13 existing upstream warnings; no source edit or
suppression. Smoke Matplotlib default cache was sandbox-blocked and successfully
fell back to a temporary cache. Full run used writable MPLCONFIGDIR; no dependency
or system installation was needed. No unresolved test/build/runtime failure.

## Actual findings

- All30 empirical/predicted MSE discrepancies are within3 combined SE; largest
  standardized discrepancy2.527. Relative combined SE4.80%–7.48%, all below15%.
  Limited empirical consistency is not exact confirmation or formal proof.
- Absolute RMSE rose with size in all four tested series, while relative RMSE
  fell. Sparse cases can be unusable: ER(n20,p.05), truth5, relative RMSE36.152;
  BA(m1,n100), truth839, relative RMSE1.207. Dense ER(n100,p.30) relative RMSE.0457.
- Both fixed graphs' MSE decreases at each total-epsilon1→2→4→8 step, with
  differences exceeding3 combined MSE SE. This is conditional on these instances.
- RR-focused has lowest predicted MSE among the three C allocations, but empirical
  differences versus alternatives do not exceed3 combined SE (maximum2.888).
  No optimal allocation or unbiased selected-winner performance claim is made.
- Triangle Laplace noise dominates sparse small/low-epsilon cases; RR dominates
  many dense/larger cells; degree noise dominates the RR-focused C setting.
  Signed shared covariance reduces the pre-adjustment sum by.0084%–8.6838%.
  This is not an equal-budget comparison to an independent-RR mechanism.
- No missed triangles in any full or prediction history, including D2. Thus
  mean M, mean M², truncation bias and sampled truncation MSE are all zero.
  No event was forced. Per fixed cell,0/600 permits a one-sided95% probability
  upper bound.00498; it does not prove impossibility.
- Fixed controls show nonzero conditional bias: K4 B1/B2 have M4/2 and bias12/6;
  K10 B2/B4 have M112/80 and bias336/240. They are not full-protocol observations.

Complete per-cell exact counts, bias, MSE/SE, RMSE/relative RMSE, predicted MSE/SE,
all five contributions and timing tables are in`docs/FOUR_PATH_STUDY.md` and
full-precision ignored`experiments/results/four_path_phase13_accuracy/summary.csv`.
Six figures have explicit interpretations there; truncation bars are all zero.

## Artifacts and limits

Study/source/dependency provenance and file hashes are in the root manifest.
Every cell retains config, graph, exact truth, separate mechanism JSONL,
non-private evaluation and prediction CSVs, summary and a nested manifest.
Raw native evidence and build provenance are under results/escape and
escape_provenance.json; build evidence lives in build/phase13/escape.
No output directory was overwritten. Partial results would be labeled failed;
none were silently dropped. The entire synthetic study is non-private.

Mechanism timing29.312820s, full analytical diagnostics21.957268s, prediction
sampling6.652776s, prediction analytics6.738763s; other pipeline overhead13.037085s
includes native validation, plots and provenance, not just serialization.
The77.7s excludes native compilation and subsequent verification/replay.
Process peak memory includes plotting/interpreter, not a per-trial memory claim.

Runtime has dense O(n²) RR/pair work, O(nB²) coefficient/triangle work, and
O(r(n+m)) ordering; exact evaluation may be cubic. Streaming replay avoids
all-trial transcript memory. Analytical costs are not private-protocol costs.
RR uploadO(n²) does not establish end-to-endO(n²): full broadcast can costO(n³).
Centralized execution, noncryptographic PRNGs, finite arithmetic, client isolation,
transcript privacy and independent formal review remain unresolved.

One graph realization per setting,600 trials, approximate heavy-tail SEs,
multiple exploratory comparisons and no observed full truncation limit inference.
No real-world P4 study or fair2025 baseline comparison was run. Data/infrastructure
are ready to support a separately authorized baseline phase after checking P4
normalization, adjacency/accounting, equal budgets, same inputs and feasibility.
No superiority or optimality claim. **STOP before Phase5; no commit or push.**
