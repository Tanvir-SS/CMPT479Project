# Checkpoint 28 — WLocal C4 baseline

2026-11-14 (America/Vancouver). **COMPLETE.** The explicit seven-stage user
request authorizes this baseline, its validation and exactly 4,800 main trials,
superseding historical task-25/phase-27 stops for this scope only.

- [x] Inspect STATUS/checkpoint 27, six supplied files, prior RR config/results,
  evaluation standards, graph format and original paper privacy definitions.
- [x] Resolve StatsLib/GCEM dependencies and compile isolated author source.
- [x] Document odd-n pairing, allocation-check and macOS header fixes.
- [x] Convert six pinned graphs losslessly; match cached native ESCAPE C4 truth.
- [x] Validate C4/Karate sample means and six-graph sanitizer/seeded replay.
- [x] Save/resume 4,800 main trials, 200 per each of 24 cells.
- [x] Verify every saved coordinate/seed, metric, comparison and artifact hash.
- [x] Complete methodology/privacy report and stop without commit/push.

## Files and commands

New scripts, source patch, report and ignored outputs:
`experiments/baselines/wlocal/`. Supplied originals remain `WLocal4Cycle/`.
Working executable `build/wlocal/wlocal`; author CLI and sanitizer executables
are alongside it. Dependency checkouts and logs remain under ignored build/.
Only existing project file edited is `docs/status/STATUS.md`.

See [complete report](../../../experiments/baselines/wlocal/REPORT.md) for exact
commands, revision pins, all 24 comparison rows, input/estimator definitions,
limitations, failures and reproduction. Dependencies: StatsLib
`f8dcb15ae51cce7142b239805745a0de56aa509f`, GCEM
`012ae73c6d0a2cb09ffe86475f5c6fba3926e200`. No Python lock/dependency changes.

## Actual validation and evaluation

Six SHA-256-verified graphs retain their original vertices/edges and exact
non-induced C4 counts: 154, 278, 2672, 198, 207959, 7302 in config order.
Python converted-graph counts and the native adapter's reader/count diagnostic
agree with cached ESCAPE evidence. No fresh ESCAPE invocation claimed.

Separate epsilon-4 validation: 20,000 one-C4 trials mean 0.9957774605 (SE
0.0101296320); 5,000 Karate trials mean 151.9589013688 (SE 2.3806401156).
Both meet predeclared abs(z)<4; C4 mean error also <.05. These are finite-sample
consistency checks, not proofs. Thirty sanitizer calls (five per pinned graph)
and thirty release replays match exactly with no diagnostics; this includes odd
n=77. Main trial seeds are distinct and disjoint from validation ranges.

Main: 4,800 finite estimates, 24 × 200, no failures/missing observations.
First call saved one; resume added 4,799; completed resume added zero.
Saved-output verification passes; 1,478 negatives retained. Summed C++ estimator
call time 0.059077949 seconds, excluding all input, diagnostics and process cost.

All 24 empirical WLocal RMSEs are smaller at equal **nominal** epsilon, with
Our/WLocal RMSE ratio 6.2772–74.3009. These are not equal-undirected-edge-privacy
results: WLocal at epsilon has an ideal 2epsilon full-transcript bound whereas
our allocation accounts for both endpoints within epsilon. No half-epsilon
additional sweep was run. The report gives a concrete two-affected-report
example and cites original definitions and experimental interpretation.

## Failures, preservation and remaining limitations

Initial sandbox StatsLib clone: DNS failure; approved network retry passed.
GCEM fetched with approval. Inspection of absent StatsLib `.gitmodules` produced
a file-not-found message. Builds and all validation/main checks passed.

All three bundled references fingerprint verified. Original Linux paths are
unavailable here; no original-source verification claim is made. Supplied source
hashes verified against build receipt; existing tracked algorithms/data/pins and
old result summaries remain unchanged. No existing RR trial was rerun or replaced.
Full Python pytest and fresh native ESCAPE intentionally skipped because this
is an isolated baseline using accepted exact caches; targeted native validation
is recorded above. Finite PRNG/modulo bias, floating arithmetic, uncertain moment
estimates, non-cryptographic seeds and transcript-vs-scalar privacy distinctions
remain explicit. No formal DP proof is inferred from experiments.

**STOP after baseline evaluation and report.** No further simulations, tuning,
plots, original-estimator changes, commit or push.

Final independent inline Python standard-library metric recomputation passed all
24 cells. Six supplied source-file hashes match their build receipt. Git's only
modified tracked file is STATUS; no staged changes. `git diff --check` passes
and `git check-ignore` confirms raw CSV/executable exclusion.
