# Checkpoint 26 — uniform-sampling + RR C4 implementation

2026-11-11 (America/Vancouver). **Stages 3–4 COMPLETE. STOP before Stage 5.**
The new owner attachment explicitly authorizes this implementation and lightweight
verification after task 25. No prior evaluation is resumed or altered.

## Work and files

Read STATUS/checkpoint 25, AGENTS, the supplied request, previous C4 private and
exact modules, graph/exact/ESCAPE APIs, fixture JSON, existing C4/ESCAPE tests,
EVALUATION_STANDARDS, TEAM_SETUP, previous C4 specification/proofs and implementation
report. Starting `git status --short` was empty. A read of the guessed filename
`scripts/fingerprint_references.py` failed (file absent); located and used the
actual `scripts/reference_fingerprints.py`. This was an inspection error, not a
failed verification. No dependency installation or upgrade was needed.

Created:

- `src/private_graphlets/four_cycle_uniform_rr.py`: public uniform sampling,
  canonical cycle requests, potential-edge participation, local allocations,
  one-bit local RR, stable debiasing and server-only aggregation.
- `tests/test_four_cycle_uniform_rr.py`: 26 focused deterministic cases.
- `docs/FOUR_CYCLE_UNIFORM_RR_IMPLEMENTATION.md`: API, formulas, mathematical
  assumptions, implementation checks and simulation limitations.
- This checkpoint. Modified only `docs/status/STATUS.md` among pre-existing files.

The simulator uses the existing immutable SimpleGraph with public IDs and
retains isolates. q is exactly ceil(n²/20) for n≥4; n<4 returns zero. Every
sample retains its occurrence ID, two wedges and fresh independent-model RR
coins. Alpha is epsilon/max of the two local potential-edge participation
counts; sum K=4q. Scheduling and alpha validation precede private adjacency
access. No raw private quantities enter the release schema. The server returns
N/q times the sum of paired debiased products without clipping or rounding.

## Commands and actual results

Environment: existing macOS Python **3.11.9** `.venv`; existing NumPy/dependencies.
The documented PATH prefix selects the installed GNU compiler. Commands:

```bash
.venv/bin/python --version
.venv/bin/python /tmp/phase26_preserve.py
.venv/bin/python -m pytest -q tests/test_four_cycle_uniform_rr.py
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_escape_integration.py::test_original_six_column_fixtures
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase26/reference_fingerprints.json
PATH="$PWD/.venv/bin:$PATH" PYTHONPATH="$PWD/build/phase26" .venv/bin/python -m pytest -q -p capture_escape tests/test_escape_integration.py::test_original_six_column_fixtures
.venv/bin/python /tmp/phase26_finish.py
git diff --check
git status --short
```

- Focused tests: **26 passed in 0.19s**, zero failures/errors/skips.
- Required native ESCAPE fixtures: **8 passed in 2.62s**, zero skips.
- Repeated native fixtures solely to capture otherwise temporary raw outputs:
  **8 passed in 1.85s**. Temporary plugin wraps the adapter return value without
  altering calculations, original tests or reference source. No simulation added.
- Reference verification: ESCAPE, k-CoreD and baseline all available and verified.
- Preservation comparison: **1,224 existing files** checked; only the intended
  STATUS edit differs. Includes all available reference files, pinned datasets,
  prior source/tests, configs and saved results/plots. No missing file detected.
- `git diff --check`: passed. No commit, staging or push.

Temporary helper scripts are retained under `build/phase26/` for reproducibility;
`/tmp` versions were invoked during execution. Preservation helper hashes Git
files plus existing results, plots and reference contents; finish helper prepends
status, updates test documentation and compares hashes. No private estimator is
called by either helper.

Ignored evidence: `build/phase26/preservation_before.json`,
`preservation_after.json`, `reference_fingerprints.json`, `capture_escape.py`,
`escape_fixture_outputs.json` (all eight complete native outputs and inputs),
and `build/escape-pytest/` (actual compiler command/log/build provenance).
Original `/home/tsshergi/` checkouts are unavailable on this Mac; no access or
verification of those original paths is claimed. Bundled references are verified
in place and unchanged, with pins and manifest preserved.

## Findings, limitations and next step

All eight fixtures' candidate indicator sums equal their expected non-induced C4
counts and the exact helper (K4=3). Controlled schedules verify duplication,
participation, local alpha and fresh draws. Clique/diamond checks explicitly
account for both endpoints of the removed edge, show identical public metadata,
and bound affected budgets. Stable two-output RR moment checks, public-before-
private guards and release schemas check implementation obligations. They do
not prove DP or PRNG independence.

The ideal complete-transcript edge-LEDP argument, unbiasedness and O(n³) fixed-
epsilon RMSE are documented separately from tests. Finite precision (including
large-alpha probability underflow), floating-point overflow, simulation seeds,
noncryptographic randomness, physical timing and lack of deployment isolation
prevent a certified executable privacy claim. Formal proofs await independent
review. Errors are not clipped away, retried or silently omitted.

Deliberately not run: full historical regression suite, extensive Monte Carlo,
standardized 4,800-trial evaluation, baseline reruns, benchmark generation,
plots, tuning or other-pattern work. No failed/skipped requested check remains.
Previous Laplace implementation, tests, evaluation configuration/scripts/results,
other patterns, data/mappings/manifest, references and dependency locks preserved.
Next step is owner review; **Stage 5 requires separate explicit authorization**.
