# SC-ESCAPE standardized six-dataset evaluation — Stage 5

2026-11-22 (America/Vancouver). **COMPLETE: 4,800/4,800 main trials**, exactly
200 in each of 24 cells, with zero failed or uncertain attempts. Separate smoke:
24/24 estimates, one per cell. No estimator modifications or Stage 6 comparison.
SC-ESCAPE remains `experimental_unverified`; Stage 4's PARTIAL classification and
numerical/deployment qualifications remain in force.

## Fixed setup and input verification

The target is non-induced, unlabeled P₄ on four distinct vertices. The independent
runner is `scripts/evaluate_sc_escape.py`; the frozen source configuration is
`experiments/configs/four_path_sc_escape_six_datasets.json`. It invokes unchanged
`estimate_sc_escape`, with no clipping, rounding, graph projection or tuning.

The same six inputs and order as Checkpoints 20–21 are used. The runner reuses
the earlier P4 runner's read-only input validator, graph loader, saved native
output parser and coordinate seed encoder. It does not execute the five-stage
estimator. Graph and mapping hashes, dimensions, cached verified Python/ESCAPE
P4 counts and the manifest's saved native `3-path` outputs agree. No discrepancy
required a recount. No graph, mapping or ground-truth cache changed.

| Dataset | n | m | Cached ESCAPE P₄ | Supplied public D_max | Source |
|---|---:|---:|---:|---:|---|
| Karate | 34 | 78 | 2371 | 33 | n−1 |
| Dolphins | 62 | 159 | 5023 | 61 | n−1 |
| Les Misérables | 77 | 254 | 26784 | 76 | n−1 |
| Brightkite-50 | 50 | 97 | 5404 | 49 | n−1 |
| BA-100 | 100 | 1600 | 2043892 | 99 | n−1 |
| SBM-100 | 100 | 760 | 166236 | 99 | n−1 |

The validated graph metadata and data README contain no documented tighter public
maximum-degree values. The task explicitly authorizes n−1 in that case. These
bounds were declared before sampling, remain unchanged, and every input satisfies
its bound. No true-degree-derived bound, private bound estimate or added budget
was used. Historical `baseline_2025` dataset folder labels identify existing
synthetic graphs; no baseline algorithm was run.

| Total ε | ε_D | ε_R | ε_S | ε_T |
|---:|---:|---:|---:|---:|
| 0.5 | 0.05 | 0.10 | 0.15 | 0.15 |
| 1 | 0.10 | 0.20 | 0.30 | 0.30 |
| 2 | 0.20 | 0.40 | 0.60 | 0.60 |
| 4 | 0.40 | 0.80 | 1.20 | 1.20 |

Every allocation satisfies 2ε_D+ε_R+ε_S+ε_T=ε_total. Allocation fractions are
.10/.20/.30/.30 throughout. RR budgets .1/.2/.4/.8 are far from the documented
1e−20 rounding case; preflight checks 0<p<.5 without changing the shared RR helper.
No claim of exact executable DP follows from this range check.

## Seeds, persistence and reproducibility

Main master seed: **202611223301**. Smoke master seed: **202611223300**. Each
trial seed is `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`, with
zero-based indices in the frozen order. All 4,800 main seeds are unique and
disjoint from all 24 smoke seeds. Identifiers are `main:g:e:t` and `smoke:g:e:t`.
Within each trial, the unchanged estimator spawns degree, RR, product and triangle
streams using its existing SeedSequence implementation. No stream is shared
between trial calls. This is reproducible simulation, not cryptographic noise.

SQLite commits every completed observation and records a started attempt before
calling the estimator. Atomic CSV/JSON exports occur after completed cells and
on orderly exit. Resume validates exact config, source/environment provenance,
cached truth and saved coordinate prefixes. A unique ordinal prevents duplicate
records. Failed attempts retain their configuration/traceback and block automatic
retry; an uncompleted started attempt after a hard interruption is treated as
uncertain and also requires review. This favors preserving trial accounting over
silently repeating a possibly executed call. `run.lock` prevents concurrent writers.

The smoke run stopped after 3 estimates, verified as partial, then resumed with
exactly 21 new estimates. A second resume added zero. Attempting to overwrite the
existing output without `--resume` raised the expected FileExistsError. The main
run completed in one invocation; no failed trial or replacement occurred.

Config, versions, source hashes, dataset/mapping pins, native truth evidence and
all seeds are saved. Verification checks these reproduction inputs and every
saved seed coordinate; it does **not** rerun 4,800 estimators. Stage 3's recorded
replay tests remain the implementation evidence for deterministic seeded calls.
No new replay trials are claimed. Hardware/runtime portability is not guaranteed.

Execution: Python 3.11.9, NumPy 2.2.6, pandas 2.2.3, NetworkX 3.4.2,
macOS 27.0.1 arm64; no dependency changes. Git HEAD:
`24239de210d69c47a1fdc945536d6095eecdb646`. Uncommitted source hashes, not HEAD
alone, identify this run. SC-ESCAPE source SHA-256:
`e587ae93c4b7f2ba585f268c483f815a69a1868c281008c658ad9d71d73741d7`.

## Metrics and all 24 configurations

For errors e=x−T: mean estimate is mean(x); bias is mean(e); variance is
population variance (`ddof=0`); MSE is mean(e²); RMSE is sqrt(MSE); MAE is
mean(|e|); MRE is mean(|e|/T); relative RMSE is RMSE/T. All truths here are
positive. For T=0 the runner leaves MRE/relative RMSE undefined (empty CSV fields),
following the existing convention rather than adding a denominator. The saved
summaries satisfy MSE=variance+bias².

Each row below contains **200** main trials. MRE and relative RMSE are ratios
(0.1 means 10%); runtime is mean seconds per complete estimator call. Display
uses six significant digits; the CSV retains 17-digit float serialization.

| Dataset | ε | Truth | Mean | Bias | Variance | MSE | RMSE | MAE | MRE | Rel. RMSE | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| karate | 0.5 | 2371 | 7825.19 | 5454.19 | 3.93938e+10 | 3.94235e+10 | 198554 | 150850 | 63.623 | 83.7426 | 0.000301556 |
| karate | 1 | 2371 | 5107.23 | 2736.23 | 1.05858e+09 | 1.06607e+09 | 32650.8 | 25471.1 | 10.7428 | 13.7709 | 0.000301798 |
| karate | 2 | 2371 | 2031.49 | -339.508 | 5.35531e+07 | 5.36684e+07 | 7325.87 | 5825.75 | 2.45709 | 3.08978 | 0.000303385 |
| karate | 4 | 2371 | 2434.09 | 63.0902 | 3.68562e+06 | 3.68961e+06 | 1920.83 | 1527.29 | 0.644155 | 0.810137 | 0.00033823 |
| dolphins | 0.5 | 5023 | 7337.1 | 2314.1 | 1.24211e+11 | 1.24216e+11 | 352444 | 292256 | 58.1835 | 70.166 | 0.000762916 |
| dolphins | 1 | 5023 | 13480 | 8457.01 | 5.80654e+09 | 5.87806e+09 | 76668.5 | 62171.7 | 12.3774 | 15.2635 | 0.000781423 |
| dolphins | 2 | 5023 | 4111.33 | -911.666 | 3.22069e+08 | 3.229e+08 | 17969.4 | 13986 | 2.7844 | 3.57743 | 0.000742077 |
| dolphins | 4 | 5023 | 4867.43 | -155.568 | 2.14872e+07 | 2.15114e+07 | 4638.04 | 3643.51 | 0.725365 | 0.92336 | 0.000749129 |
| les_miserables | 0.5 | 26784 | 33488.9 | 6704.87 | 2.64712e+11 | 2.64757e+11 | 514545 | 395759 | 14.7759 | 19.2109 | 0.00112248 |
| les_miserables | 1 | 26784 | 27568 | 783.965 | 1.00938e+10 | 1.00944e+10 | 100471 | 80887.9 | 3.02001 | 3.75115 | 0.00111574 |
| les_miserables | 2 | 26784 | 29149.5 | 2365.5 | 6.92407e+08 | 6.98003e+08 | 26419.7 | 21362.2 | 0.797571 | 0.9864 | 0.00112569 |
| les_miserables | 4 | 26784 | 26547.4 | -236.621 | 6.18485e+07 | 6.19045e+07 | 7867.94 | 6448.16 | 0.240747 | 0.293755 | 0.0011244 |
| brightkite_50 | 0.5 | 5404 | 14012.4 | 8608.37 | 8.14319e+10 | 8.1506e+10 | 285493 | 221018 | 40.8989 | 52.8299 | 0.000534776 |
| brightkite_50 | 1 | 5404 | -2883.42 | -8287.42 | 3.29143e+09 | 3.36012e+09 | 57966.5 | 46703.8 | 8.64245 | 10.7266 | 0.000535791 |
| brightkite_50 | 2 | 5404 | 5608.9 | 204.905 | 2.37534e+08 | 2.37576e+08 | 15413.5 | 11880.6 | 2.19848 | 2.85224 | 0.000534289 |
| brightkite_50 | 4 | 5404 | 5418.44 | 14.4423 | 2.58944e+07 | 2.58946e+07 | 5088.67 | 4038.63 | 0.74734 | 0.941649 | 0.000530648 |
| ba_n100 | 0.5 | 2043892 | 1.96399e+06 | -79905 | 7.89911e+11 | 7.96296e+11 | 892354 | 682374 | 0.33386 | 0.436596 | 0.00240585 |
| ba_n100 | 1 | 2043892 | 2.04193e+06 | -1957.81 | 7.19353e+10 | 7.19391e+10 | 268215 | 216468 | 0.105909 | 0.131227 | 0.0023846 |
| ba_n100 | 2 | 2043892 | 2.05095e+06 | 7060.73 | 1.45184e+10 | 1.45683e+10 | 120699 | 96422.7 | 0.047176 | 0.0590536 | 0.00240297 |
| ba_n100 | 4 | 2043892 | 2.03329e+06 | -10602.4 | 3.23175e+09 | 3.34416e+09 | 57828.7 | 45228 | 0.0221284 | 0.0282934 | 0.00240304 |
| sbm_n100 | 0.5 | 166236 | 112607 | -53629.5 | 3.91036e+11 | 3.93912e+11 | 627624 | 503627 | 3.02959 | 3.7755 | 0.00191631 |
| sbm_n100 | 1 | 166236 | 148939 | -17296.7 | 2.11716e+10 | 2.14708e+10 | 146529 | 112991 | 0.679702 | 0.881452 | 0.00191365 |
| sbm_n100 | 2 | 166236 | 165828 | -407.68 | 1.70376e+09 | 1.70393e+09 | 41278.7 | 31978.3 | 0.192367 | 0.248314 | 0.00190663 |
| sbm_n100 | 4 | 166236 | 165482 | -754.034 | 1.88569e+08 | 1.89137e+08 | 13752.7 | 10984.9 | 0.0660802 | 0.0827301 | 0.00189195 |

Runtime excludes loading, exact evaluation, SQLite persistence and CSV exports.
Total time inside the 4,800 estimator calls was **5.62586372718215 seconds**;
this is centralized simulation time, not distributed communication/latency.

## Preliminary interpretation

MSE, RMSE and MRE decrease strictly with each increase of epsilon for every
dataset in this run. That is consistent with a privacy–accuracy tradeoff but
does not prove the theoretical MSE bound or establish monotonicity in every
finite experiment. No parameter search or post-hoc allocation change was made.

Empirical variance contributes **96.6386%–99.9992%** of MSE across the 24 cells;
squared bias contributes the remainder. This decomposition is descriptive, not
proof that finite-sample bias is zero. A mean close to truth can coexist with
large individual errors. For example, Brightkite-50 at ε=1 has a negative mean
estimate of approximately −2883.42 despite true P₄=5404; that unfavorable result
is retained.

At ε=4, MRE is 64.42% (Karate), 72.54% (Dolphins), 24.07% (Les Misérables),
74.73% (Brightkite-50), 2.21% (BA-100) and 6.61% (SBM-100). At ε=.5, the four
real-world graphs have MRE between 14.78 and 63.62 **times** truth. Accuracy for
these sparse examples is therefore poor at the stricter budgets.

The denser n=100 synthetic graphs have much larger P₄ targets and lower relative
errors than the smaller real-world examples, even though BA-100 has the largest
absolute RMSE at every budget. Size, density, degree structure and count scale
vary together, so these six graphs do not isolate a causal density effect.
There is one fixed realization per dataset and only 200 trials per cell; no
additional uncertainty/bootstrap experiment or cross-estimator comparison was run.

All **1,193 negative estimates** (24.8542%) and all **4,800 fractional estimates**
remain in the saved data and metrics. Every estimate and component was finite;
no NaN, infinity, numerical failure, dropped trial or silent replacement occurred.

## Actual commands and verification

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

All commands exited 0. Additional inline saved-only checks tested overwrite
refusal, exact metric fixtures and undefined relative errors for zero truth.
Smoke contained five negative and 24 fractional estimates. No pytest suite or
extra estimator simulation was run during Stage 5.

The runner verifies exact CSV/SQLite agreement, coordinates, budgets/bounds,
source/config provenance, unique seeds, finite components and saved summaries.
An independent standard-library CSV/math/statistics verifier recomputed all ten
requested metrics, checked all 200 trial indices per cell and smoke/main seed/ID
separation. Its tolerance for independently accumulated metrics is relative 1e−12
and absolute 1e−9. All checks passed; `failures.json` is empty.

SHA-256 comparison confirms **1,067 pre-existing files unchanged**, including
all prior experiment results, both estimators, graph/mapping files, cached truths,
prior reports/checkpoints, tests and dependency pins (STATUS intentionally
excluded). All three references passed the existing fingerprint verifier.
No old evaluation directory was opened for writes.

## Deliverables and stopping point

Created source/config/docs:

- `scripts/evaluate_sc_escape.py`
- `experiments/configs/four_path_sc_escape_six_datasets.json`
- `docs/SC_ESCAPE_SIX_DATASETS.md`
- `docs/status/checkpoints/33_sc_escape_stage5_evaluation.md`

Modified: `docs/status/STATUS.md`. Earlier uncommitted Stage 3–4 files were
preserved and are not newly created Stage 5 work.

Results in `experiments/results/four_path_sc_escape_six_datasets/`:
`trials.sqlite3` (trials and attempt journal), `trials.csv`, `summary.csv`,
`config.json`, `provenance.json`, `escape_ground_truth.json`, `manifest.json`,
`failures.json`, `verification.json`, `independent_verification.json`, `run.lock`.
Generated outputs are Git-ignored. `build/phase33/` holds separate smoke outputs,
logs, preflight/reference/preservation evidence and the saved-only verifier.

The research CSVs contain exact truth, public dataset diagnostics and seeds and
are **not private releases**. Empirical results neither prove privacy nor certify
the theoretical MSE bound. All Stage 4 caveats remain documented in
[SC_ESCAPE_VERIFICATION.md](SC_ESCAPE_VERIFICATION.md).
**STOP after Stage 5.** No Stage 6 comparison, new baseline, optimization,
new derivation, dataset change, plot, commit or push.
