# Checkpoint 33 — SC-ESCAPE Stage 5 standardized evaluation

2026-11-22 (America/Vancouver). **COMPLETE: 4,800/4,800 main trials; zero failures.**
Exactly 24 configurations with 200 unique trials each, plus exactly 24 separately
seeded smoke estimates. **STOP before Stage 6.** No estimator or budget redesign.

## Scope, starting state and completed checklist

The explicit Stage 5 request authorizes this fixed six-dataset study after the
Stage 4 PARTIAL review. That classification and the simulator's
`experimental_unverified` label remain unchanged. Starting HEAD:
`24239de210d69c47a1fdc945536d6095eecdb646`.
Stage 3–4 were still uncommitted: STATUS modified and their seven module/test/doc/
checkpoint paths untracked. Those existing files are preserved, not new Stage 5
work. No commit, staging or push.

- [x] Read task, status/checkpoints 20, 21, 31, 32, SC-ESCAPE source and documents,
  evaluation standards, existing P4 runner/config and validated data metadata.
- [x] Verify six graph/mapping hashes, dimensions and cached native P₄ truths.
- [x] Declare public n−1 bounds and fixed four-parameter allocations.
- [x] Create separate resumable runner/config; journal attempts and freeze provenance.
- [x] Run one smoke estimate per cell; verify stop/resume/no-op/serialization/metrics.
- [x] Run exactly 4,800 fresh main estimates and save each observation.
- [x] Verify all saved coordinates, budgets, seeds, truth, metrics and artifacts.
- [x] Check preservation, write the full report and stop without Stage 6.

## Fixed configuration

| Graph | n | m | ESCAPE P₄ | Public D_max |
|---|---:|---:|---:|---:|
| karate | 34 | 78 | 2371 | 33 |
| dolphins | 62 | 159 | 5023 | 61 |
| les_miserables | 77 | 254 | 26784 | 76 |
| brightkite_50 | 50 | 97 | 5404 | 49 |
| ba_n100 | 100 | 1600 | 2043892 | 99 |
| sbm_n100 | 100 | 760 | 166236 | 99 |

No tighter public maximum degree was documented in the validated dataset manifest
or data README. The task's explicit fallback n−1 was supplied unchanged in every
call, never derived by measuring private maximum degree. Every graph satisfies
its bound. The existing P4 validator compares the Checkpoint 20 cache against
manifest native ESCAPE outputs and the six prior expected P₄ counts; all agree.
No new exact count or native build was needed or run.

Epsilon .5/1/2/4; epsilon_D/R/S/T=.10/.20/.30/.30 times total, with
`2*epsilon_D+epsilon_R+epsilon_S+epsilon_T=total`. RR allocations .1/.2/.4/.8
pass the public finite-parameter checks and avoid the documented 1e−20 case.
There is no optimization, noise substitution or clipping.

Main master seed **202611223301**; smoke master **202611223300**. Reused coordinate
encoding `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`. Main trial
indices are 0..199, smoke index 0; identifiers have distinct `main:`/`smoke:`
prefixes. All 4,824 seeds and identifiers are unique across both sets.

## Runner, dependencies and persistence

New `scripts/evaluate_sc_escape.py` imports only the existing P4 runner's read-only
input validation, seed encoder, coordinate generator and atomic JSON helper.
It calls unchanged `estimate_sc_escape`, not the original five-stage estimator.
The same population-variance/MSE conventions are used, with added required MRE.
Undefined zero-truth relative metrics remain empty CSV fields.

SQLite commits an attempt before sampling and commits its result/completed state
together. CSV/JSON writes are atomic; a lock excludes simultaneous writers.
Resume checks config, source hashes, Python/library/platform metadata, reference
gitlinks and saved coordinates. Failed/uncertain attempts are preserved and block
automatic retries. Clean stops resume only missing coordinates. No failure was
encountered; crash-during-sampling recovery was not artificially exercised.

Environment: existing Python 3.11.9 `.venv`, NumPy 2.2.6, pandas 2.2.3,
NetworkX 3.4.2, macOS 27.0.1 arm64. No install or dependency change.
SC-ESCAPE SHA-256 remains
`e587ae93c4b7f2ba585f268c483f815a69a1868c281008c658ad9d71d73741d7`.
Runner SHA-256 is
`e15fffbd4b9efe0bd8f731bc12b0e290b583ca2f4f4cee42a67b76b529e1ba1e`.
Full config, source/environment provenance and native truth evidence are saved
with results; Git HEAD alone does not identify uncommitted code.

## Actual execution and checks

Before creating the runner/config, an inline Python SHA-256 snapshot captured
**1,067 pre-existing files** under src/tests/data/scripts/experiments/plots/docs
plus the dependency/reference manifests, excluding STATUS, pycache and .pyc.
It includes previous saved experiment outputs, not just tracked files.
Evidence: `build/phase33/preservation_before.json`.

```bash
.venv/bin/python scripts/evaluate_sc_escape.py check > build/phase33/preflight.json
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase33/references.json
.venv/bin/python scripts/evaluate_sc_escape.py run --smoke --max-new-trials 3 > build/phase33/smoke_start.log
.venv/bin/python scripts/evaluate_sc_escape.py verify --smoke
.venv/bin/python scripts/evaluate_sc_escape.py run --smoke --resume > build/phase33/smoke_resume.log
.venv/bin/python scripts/evaluate_sc_escape.py verify --smoke
.venv/bin/python scripts/evaluate_sc_escape.py run --smoke --resume > build/phase33/smoke_noop.log
.venv/bin/python scripts/evaluate_sc_escape.py run > build/phase33/main_run.log
.venv/bin/python scripts/evaluate_sc_escape.py verify
.venv/bin/python build/phase33/verify_saved.py
```

All commands exited 0. Preflight verified all six cached truths/inputs, public
bounds and four budgets without sampling. Smoke stopped with 3 complete/21
remaining, resumed exactly 21 and verified 24 cells. Second resume produced
zero new estimates. Inline checks caught the expected FileExistsError for an
overwrite attempt; tested summary inputs −1/3 against truth 1 (mean 1, bias 0,
variance=MSE=4, RMSE=MAE=MRE=relative RMSE=2); and confirmed undefined relative
metrics for a zero-truth fixture. These checks did not execute additional trials.
The smoke saved five negative and 24 fractional estimates. Receipt:
`build/phase33/smoke_checks.json`.

Main execution completed **4,800 new estimates**, 24 cells, zero remaining,
zero failed/uncertain attempts. No replacement/retry, no NaN/infinite estimate
or component. All 1,193 negative and all 4,800 fractional estimates are retained.

Runner verification checks CSV/SQLite equality, all fixed per-row settings,
coordinate prefixes, seed uniqueness, finite outputs, original component
aggregation, file hashes and recomputed summary metrics. Independent verification
uses only csv/math/statistics/hashlib: all 200 trial indices in each cell,
all requested accuracy/runtime metrics, zero duplicate/missing coordinates,
main/smoke seed and ID separation, public bounds, total/stage budgets and
preservation hashes. **All pass.** Final result is saved in
`independent_verification.json`; no estimator replay was performed. Reproduction
inputs are verified, but no fresh 4,800-call replay is claimed.

The three pinned references were available, clean and hash-verified against their
unchanged manifest: ESCAPE `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3`, k-CoreD
`b03da893ba1c38d3931708bac919562c5ab57963`, notebook reference
`85eff6efa2b1d649ee238620a998ec7f1d305aac`. Sources were read/hashed in place;
no upstream setup/build/experiment was executed. `/home/tsshergi` originals were
not accessed or changed.

## Findings and report

[SC_ESCAPE_SIX_DATASETS.md](../../SC_ESCAPE_SIX_DATASETS.md) contains all 24 rows
with truth, mean, bias, variance, MSE, RMSE, MAE, MRE, relative RMSE and runtime.
Machine-readable summary and individual observations retain 17-digit serialization.

MSE, RMSE and MRE decrease at every epsilon step on each graph. Variance contributes
96.6386%–99.9992% of MSE. At ε=4, MRE ranges from .0221284 on BA-100 to .747340
on Brightkite-50. Low-budget real-world relative accuracy is poor; Brightkite-50
at ε=1 even has negative mean −2883.42 against truth 5404. All unfavorable
results were preserved. Denser synthetic graphs have lower relative errors but
larger count scales; no causal density conclusion or cross-estimator ranking is made.
Summed estimator time: **5.62586372718215 seconds**, excluding evaluation/storage.

These are empirical results from six fixed graphs, not proofs of privacy,
unbiasedness, a theoretical MSE rate or universal utility. No Stage 6 comparison.

## Files and artifacts

Created ordinary files:

- `scripts/evaluate_sc_escape.py`
- `experiments/configs/four_path_sc_escape_six_datasets.json`
- `docs/SC_ESCAPE_SIX_DATASETS.md`
- `docs/status/checkpoints/33_sc_escape_stage5_evaluation.md`

Modified ordinary file: `docs/status/STATUS.md` (new phase section; history kept).

Ignored `experiments/results/four_path_sc_escape_six_datasets/` contains
`trials.csv`, `summary.csv`, `trials.sqlite3` (results and attempt journal),
`config.json`, `provenance.json`, `escape_ground_truth.json`, `manifest.json`,
`failures.json` (empty), `verification.json`, `independent_verification.json`,
and `run.lock`. These evaluation records include exact truth and simulation
seeds and must not be represented as private releases.

Ignored `build/phase33/` contains separate smoke artifacts, execution logs,
preflight/fingerprint/preservation/smoke-check receipts and `verify_saved.py`.
No previous result directory was overwritten. No dataset, mapping, exact truth,
reference pin/source, estimator or dependency changed.

Final checks after writing the report/status/checkpoint:

```bash
.venv/bin/python build/phase33/verify_saved.py
.venv/bin/python scripts/evaluate_sc_escape.py verify
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase33/references_after.json
git diff --check
git status --short
```

All exited 0. Independent verification again reports 4,800 main/24 smoke, 24
cells × 200, zero failures and **1,067 protected files unchanged**. Inline JSON
comparison of `references.json` and `references_after.json` confirmed identical
fingerprints for all three references. A five-file newline/trailing-whitespace
check passed, and the report's 24-row table placeholder was confirmed replaced.
`git diff --check` was clean. Final status consists of the eight pre-existing
Stage 3–4 paths plus the four new Stage 5 files; STATUS is the only tracked
modified file. These checks consumed only saved records/files, no estimator calls.

## Failures, skipped checks and stopping point

No unexpected command, smoke, main-trial or verification failure occurred.
The expected overwrite refusal is a successful infrastructure check, not a trial
failure. No tests were skipped and counted as passing. No pytest/historical
regression suite, ground-truth recomputation, new dataset, full replay, extra
private simulation, baseline, optimization, new theory, figure, commit or push.
Exactly **24 smoke + 4,800 main estimator calls** were authorized and executed.

Stage 5 deliverables are complete. **STOP: Stage 6, comparisons, baselines and
budget optimization remain unstarted and require a separate explicit request.**
