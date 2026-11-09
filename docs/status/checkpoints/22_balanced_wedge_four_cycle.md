# Checkpoint 22 — balanced wedge-Laplace C4 implementation

2026-11-09 (America/Vancouver). **COMPLETE within implementation/smoke scope. STOP.**

The owner's pasted request explicitly authorized a new C4 implementation after
Checkpoint 21, overriding the historical Phase-19-only scope for this task. Read
STATUS/checkpoint 21, AGENTS, both supplied documents, relevant source/tests,
fixtures and evaluation standards before implementation. The request limits
execution to a smoke test despite full-evaluation instructions in the attachment.

## Phase checklist

- [x] Independently review balance, sensitivity, composition and sampling variance.
- [x] Preserve intended estimator and existing implementations/data/references.
- [x] Implement public schedule, local wedge/randomizer and server separation.
- [x] Complete focused fixture, sampling, privacy-implementation and corner checks.
- [x] Run the requested native ESCAPE fixture test successfully (not skipped).
- [x] Prepare independent fixed six-dataset C4 evaluation and cached native truth.
- [x] Exercise incremental save/resume and verify a small smoke run.
- [x] Document findings, limitations and next step; do not run full evaluation.

## Files

Created:

- `src/private_graphlets/four_cycle.py`: public AP schedule, local reports,
  server aggregate, release dataclass and seed/Generator simulation entry point.
- `src/private_graphlets/four_cycle_exact.py`: separate non-private C4 counter.
- `tests/test_four_cycle.py`: 20 focused parametrized cases in total.
- `scripts/evaluate_four_cycle.py`: independent runner adapted from the preserved
  P4 runner's SQLite/CSV/provenance/metrics conventions.
- `experiments/configs/four_cycle_six_datasets.json`: six pinned inputs, .5/1/2/4,
  200 trials/cell; endpoint halves, sensitivity 12, scale numerator 24.
- `docs/FOUR_CYCLE_BALANCED_WEDGE_SPEC_AND_PROOFS.md`: byte-identical supplied spec.
- `docs/FOUR_CYCLE_IMPLEMENTATION.md`: independent mathematical review, interfaces,
  checks, native counts, reproduction, deviations and limitations.
- This checkpoint. Updated `docs/status/STATUS.md`, preserving historical status.

No existing algorithm/test, fixture, dataset/mapping/manifest, dependency, lockfile,
reference source, gitlink or earlier checkpoint changed. No dependency installation,
upgrade, new baseline, plots, full regression, budget tuning, commit or push.

## Review findings

No correctness/privacy inconsistency requiring the requested stop was found.
The two-design cancellation is valid with ordered occurrence pairs, including
self-pairs and duplicates. Quadratic residuals are bounded by 4 and 9; the
high-overlap counts give O(q) unscaled sampling variance. Conditional fresh noise
then gives O_epsilon(n^6) MSE, hence O_epsilon(n^3) RMSE, for the ideal protocol.
Each affected endpoint has vector L1 sensitivity <=12 and epsilon/2 privacy with
scale 24/epsilon; only the two endpoints' reports depend on the changed edge.

A minor proof clarification assigns arbitrary bounded c_t to impossible overlaps
at small p, whose coefficients vanish. No algorithm change is needed. One explicit
API extension supports n<4 by the same public padding/noise, with zero true target.
The implementation has no noiseless mode. No other algorithmic discrepancy found.
See the technical report for the complete reasoning and limits of this review.

## Commands and observed outcomes

Preparation: `.venv/bin/python build/phase22/prepare_runner.py` created the new
runner/config from the existing runner; the preparation script remains ignored.
The supplied spec was copied verbatim and byte equality was verified.

```bash
.venv/bin/python -m pytest -q tests/test_four_cycle.py tests/test_escape_integration.py::test_original_six_column_fixtures
```

Initial outcome: **19 passed, 8 setup errors in 1.25s**, no skips. All new C4 tests
passed. Native source compilation used Apple Clang through `/usr/bin/g++` and
failed on ESCAPE `JSIterator` lacking a subscript operator with libc++.
This was a compiler compatibility failure, not a passed reference comparison.
Saved failure log: `build/phase22/escape_clang_failure.log`.
Read `docs/TEAM_SETUP.md` and used its documented local GNU compiler setup:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_escape_integration.py::test_original_six_column_fixtures
```

Outcome: **8 passed in 2.35s**, no failures/errors/skips. No reference edits.
The real binary and compiler/source provenance remain in `build/escape-pytest/`.
A short inline Python evidence-capture command called the same `EscapeAdapter`
for the eight fixture files and saved `dataclasses.asdict(run)` values to
`build/phase22/fixture_escape_evidence.json` (actual native input/output/stdout/
stderr separate from Python counts). It also computed `count_four_cycles` once
on each of the six saved benchmark graphs: 154/2672/278/198/207959/7302 in manifest
order (Karate/Les Mis/Dolphins/Brightkite/BA/SBM), agreeing with native C4 columns.
These were evidence capture and one small independent truth check, not private
experiments or a repeated regression suite.

```bash
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase22/reference_fingerprints.json
.venv/bin/python scripts/evaluate_four_cycle.py run --smoke --max-new-trials 3 > build/phase22/smoke_start.log
.venv/bin/python scripts/evaluate_four_cycle.py run --smoke --resume > build/phase22/smoke_resume.log
.venv/bin/python scripts/evaluate_four_cycle.py verify --smoke
```

All exit 0. All three reference fingerprints verify. Smoke saves 3, resumes 21,
and verifies **24 trials / 24 cells**, zero remaining smoke trials. Main trials
remain **0/4,800**. Smoke master 202611092200; reserved main master 202611092201.
CSV/SQLite agreement, saved hashes, unique seeds, configuration/provenance and
population MSE identity pass. This smoke is functional validation only.

One additional controlled two-observation metrics test was then added to exercise
nonzero variance (one-observation smoke cells necessarily have variance zero):

```bash
.venv/bin/python -m pytest -q tests/test_four_cycle.py -k runner_population_metrics
```

Outcome: **1 passed, 19 deselected in 0.35s**. Thus all 20 new cases have passed,
without rerunning the already-passing 19. Controlled MSE=10, bias=1, variance=9,
MAE=3; negative observation retained.

```bash
git diff --check
git status --short
```

Whitespace check passed. A read-only inline Python comparison of every existing
tracked regular file's `git hash-object` to `git rev-parse HEAD:<path>` found no
pre-existing changes before the intended STATUS update. Receipt:
`build/phase22/preservation.json`. It also confirmed that the main C4 output
folder does not exist and the copied specification is byte-identical.

An initial overly broad instruction-file search traversed the parent directory
and emitted macOS permission errors. It made no changes; a subsequent scoped
`rg --files -g AGENTS.md .` located only the repository AGENTS.md. No inaccessible
content was needed. This search issue is separate from test/experimental results.

## Dependencies and artifacts

Used the existing Python 3.11 environment and installed dependencies unchanged.
Exact Python/platform/dependency versions, source and dataset hashes, git revision,
submodules and reference manifest hash are recorded in
`build/phase22/smoke/provenance.json`. Native compile metadata records GNU g++.
All raw smoke/evidence/build outputs remain ignored under `build/phase22/`.
The smoke directory includes config, cached native truth, SQLite, trial/summary
CSVs, manifest and verification JSON. No main evaluation directory was created.

## Limitations and next step

NumPy sampling and floats are research simulation, not certified executable pure
LEDP. Logical one-round messages are modeled; physical timing/transport security
is not implemented. Empirical checks do not prove DP. Ideal privacy, unbiasedness
and asymptotic accuracy arguments remain subject to independent review; numerical
range, finite precision and PRNG limitations are explicit in the report. No
empirical superiority/novelty or practical relative-accuracy claim is made.

The runner is ready for review and a later explicitly authorized full study.
It reuses native C4 manifest evidence, never K4 truth, and fails on missing or
mismatched evidence. It does not bootstrap a missing manifest or missing datasets.
The full 4,800-trial experiment, broad regressions and further graph patterns were
intentionally not run. **Stop after this task.**
