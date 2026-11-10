# Checkpoint 25 — six-dataset no-clipping diamond evaluation

2026-11-10 UTC. **COMPLETE.** The owner authorizes only the fixed 4,800-trial diamond study,
minimal saved-output checks, one accuracy plot and a brief report. This replaces
task 24's stopping point for this evaluation. No additional simulations, tests,
exhaustive audits, baselines, alternative caps or parameter optimization.

## Setup and files

Read AGENTS, STATUS/checkpoint 24, the new task attachment, diamond/private and
exact modules, EVALUATION_STANDARDS, dataset manifest, and existing C4/P4 runners
and plotting conventions. Starting revision:
`178fe87a03b3ab58af9694b738f0b64e032fc73c`, with a clean working tree.
Captured 275 available pre-existing file hashes (including prior outputs) in
`build/phase25/preservation_before.json` before changing project documentation.

Created `scripts/evaluate_diamond.py`, a separate runner using the actual unchanged
`estimate_diamonds` API and `DiamondBudget`. Created
`experiments/configs/diamond_six_datasets.json` with master seed **202611102501**.
Graph order is Karate, Dolphins, Les Misérables, Brightkite-50, BA-100, SBM-100.
Trial seeds are `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`;
all 4,800 coordinates/seeds are distinct. O/R/W use fractions 1/4,3/8,3/8 of
total epsilon .5/1/2/4, with 200 trials per cell. Explicit default k-CoreD
configuration is psi=.5, threshold_fraction=.5, bias_factor=1. B=n-1 uses only
public n, and scale remains exactly 2(B-1)/epsilon_W. No maximum-degree query,
cap reduction or additional noise is used.

Input paths are resolved from the existing manifest; loader checks graph/mapping
hashes and sizes without preprocessing. Reused native ESCAPE diamond counts:
151, 300, 4544, 245, 217982, 3093 in graph order. Raw native output and historical
source fingerprints are copied into the new run's `escape_ground_truth.json`.
Neither native compilation/execution nor a Python exact recount was needed.
K4 contributes six non-induced diamonds; no induced count is substituted.

The runner commits every observation to SQLite, flushes each trials.csv row,
and exports summaries per completed cell. Resume checks config/source/dependency/
data provenance and rebuilds CSV from SQLite before continuing missing coordinates.
It does not repeat completed estimates. Runtime measures only the estimator call;
exact truth/seeds are separate non-private evaluation fields, not private releases.
`verify` recomputes the requested metrics from saved data and checks CSV/SQLite,
unique IDs/seeds, all caps/budgets/scales, 24×200 completion and artifact hashes.
`plot` reads the saved summary to generate just the four-real-world MRE chart.

Updated `AGENTS.md` scope, README evaluation link and STATUS/current checklist.
The result report is `docs/DIAMOND_SIX_DATASETS.md`; this is the new checkpoint.
No existing algorithm, exact helper, test, proof, reference, dataset or dependency
was edited. No shared experimental framework was added.

## Execution commands

An inline Python preflight loaded the six graphs, checked native truth and unique
coordinates, and confirmed Python 3.11 in `.venv`; it made no estimator calls.
The first invocation intentionally saves one **main** observation, then resume
continues the remaining 4,799. This is not a separate smoke/sanity trial.

```bash
.venv/bin/python scripts/evaluate_diamond.py run --max-new-trials 1 > build/phase25/initial_run.log 2>&1
.venv/bin/python scripts/evaluate_diamond.py run --resume > build/phase25/main_run.log 2>&1
.venv/bin/python scripts/evaluate_diamond.py verify > build/phase25/verification.log
MPLCONFIGDIR=build/phase25/matplotlib .venv/bin/python scripts/evaluate_diamond.py plot > build/phase25/plot.log
.venv/bin/python build/phase25/complete_report.py
git diff --check
```

Environment: existing Python 3.11.16, NumPy 2.2.6, pandas 2.2.3, NetworkX 3.4.2,
Matplotlib 3.10.1; Ubuntu WSL2 x86_64, eight logical CPUs reported. No dependency
installation or upgrade. The simulator is executed sequentially. NumPy seeds
are for reproducibility, not production DP randomness.

## Completion

- [x] Fixed configuration, cached native truth and six input snapshots checked.
- [x] Exactly 4,800 main observations saved: one first invocation + 4,799 resumed.
- [x] All 24 cells contain 200 distinct trial IDs and 4,800 distinct seeds.
- [x] B=n-1, allocations, unchanged noise scale and saved metrics verify.
- [x] One requested MRE plot generated from summary.csv and visually inspected.
- [x] Complete brief report, preservation/status checks, and stop.

All execution commands above exited 0. No errors, failed estimator calls or
incomplete trials. No additional smoke/sanity/replay trials were run. Final
manifest records **4,800 complete, zero remaining**. Verification confirms exact
CSV/SQLite equality, summary recomputation, population variance/MSE identity,
fixed settings and recorded source/data/artifact hashes. The plot is a readable
1360×832 PNG with four labeled curves and a log MRE axis; no extra figures.

MRE decreases monotonically with epsilon for all six graphs. At epsilon 4:
Karate .892454, Dolphins 1.032889, Les Misérables .245023, Brightkite-50 1.016664,
BA-100 .108671, SBM-100 .461314. These are MAE/truth ratios, not percentages or
relative bias. All **1,822 negative** and **4,800 noninteger** estimates remain
unchanged. Total measured estimator time is **744.8326747420015 seconds**;
storage/verification/plotting time is excluded. Complete 24-cell results and
the no-clipping/variance limitations are in `docs/DIAMOND_SIX_DATASETS.md`.

Generated, Git-ignored artifacts:

- `experiments/results/diamond_six_datasets/`: trials/summary CSV, durable
  SQLite, executed config, provenance, raw native ground truth, manifest,
  verification, progress and run-lock files.
- `plots/diamond_six_datasets/mean_relative_error.png` and `provenance.json`.
- `build/phase25/`: execution/verification/plot logs, preservation snapshot and
  receipt, report-rendering helper, results summary and local Matplotlib cache.

The report helper only reads saved summaries to render documentation; it makes
no estimator calls. Plot provenance links summary SHA256
`c6368d09061638b637bc446333f3574df7ff34074a5e273a54a03975c6937ed1`
to PNG SHA256
`c098d98cacd82f0e036fc42465f4bd4258eb5b52223c69db5f7bfaf477c3e570`.
The trial CSV SHA256 is
`8be3e32eb5a85b2b6c393335c8437a98965d906ca0689a2a1a6406adbc436f61`.

The pre-task 275-file preservation comparison allows only the intended AGENTS,
README and STATUS edits. Existing estimators, tests, proofs, fixtures, six
datasets/mappings, dependencies, reference pins and historical outputs remain
unchanged; no pre-existing file is missing. The three reference pins and Git
HEAD/index remain unchanged. Generated CSV/SQLite/PNG artifacts remain ignored.
No dependency installation, commit, staging or push.

Deliberately skipped: the existing 49 diamond and 25 k-CoreD tests, exhaustive
privacy/correctness checks, new exact/native counting, additional Monte Carlo,
baseline, alternative caps/budgets and parameter optimization. No new test
results are claimed. This is a finite, untuned no-clipping accuracy reference;
RR/Laplace variance remains, the larger public cap can be noisy, and deployment
privacy is still experimental/unverified. It makes no comparative-accuracy claim.

**STOP.** No follow-on work is authorized without a new instruction.
