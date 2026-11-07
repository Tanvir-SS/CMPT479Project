# Checkpoint 17 — P4 Phase 5B comparison

Started: 2026-11-06. Resumed: 2026-11-07 (America/Vancouver).
**COMPLETE. Stop after Phase5B; no next phase, commit or push.**

## Authorized scope and starting state

User explicitly authorized Phase 5B after completed Phase 5A. Initial HEAD is
8849987; the six uncommitted Phase 5A documentation changes are preserved.
No private mechanism, exact counter, reference pin or dependency is changed.
Read current instructions/status, checkpoints 14/16, P4 implementation/accuracy/
study/baseline documentation, and existing orchestration and test conventions.
All 271 recorded Phase 4B artifact hashes and all three reference fingerprints
verified before development. Saved edge-list instances are available.

## Completed implementation and predeclaration

New dedicated evaluation module `src/private_graphlets/four_path_comparison.py`,
runner `scripts/run_four_path_comparison.py`, full/smoke Phase17 configurations,
and `tests/test_four_path_comparison.py`. Reuses Phase 4A candidate execution,
metrics/prediction/replay engines without editing them. New exact ideal baseline
variance uses centered-noise coefficient families; independent exhaustive tests
compare the Phase 5A path-set oracle. The public/private schema separation and
negative estimates remain unchanged.

Initial focused run:33 passed in5.65s. With the two additional boundary/statistical
tests and plot-only regression checks:35 passed in6.79s. No errors/failures/skips.

Full design saved before results: 26 candidate cells, 20 unique baseline
conditions, 600 trials each, 400 candidate prediction histories per cell.
Fresh master202611061705; distinct candidate/full/prediction/baseline coordinates.
A/B/C budgets and graph instances exactly match Phase 4B; the baseline receives
full total epsilon. Approximate pointwise95% and Bonferroni26 intervals are
predeclared. Shared baseline series are not counted as independent repetitions.

Smoke master202611061700: 8 cells/5 baseline conditions, 24+15 full trials and
24 histories. Completed in2.686257s,1,509,887 bytes,265,633,792 peak RSS bytes.
Complete smoke replay passed (63 distinct seeds). Includes n100 and shared
baseline allocation cells. Baseline timing projection193s; conservative total
including replay5–20min, memory/artifact allowance each1GB. No design changes.

## Completed before interruption; saved in acf3442

The full26-cell candidate/20-condition baseline comparison completed in262.292137s.
15,600 candidate trials +12,000 baseline trials +10,400 prediction histories.
All312 result artifacts are present. Final post-caption-correction size:
446,650,529 bytes excluding root manifest; peak RSS303,136,768 bytes.
No dropped cells, failed trials or numerical-guard failures.

Full deterministic replay passed for all38,000 distinct seed coordinates.
Seven PNG/PDF figure pairs were generated and all PNGs visually inspected. The
runtime caption was corrected through audited plot-only regeneration; no trial
or metric changed. Final artifact verification after replot passed.

Bounded stage profiling and incremental allocator-memory diagnostics completed
and are saved in build/phase17/profile.json. Full regression passed913 tests in
37.66s before the plot-only enhancement, then913 in38.23s afterward. The old
checkpoint's pending wording had not yet been updated when the turn stopped.

The user subsequently saved implementation/docs in commit acf3442. Resumption
began with a clean tree there. No experiment or source file was restarted,
overwritten or modified during resumption. Only documentation completion and
fresh checks remain necessary.

## Research findings

- Baseline lower MSE/RMSE in all26 comparisons; all approximate pointwise95% and
  Bonferroni26 adjusted intervals favor it. Candidate/baseline MSE ratio5.5581
  to19023.35. No tested accuracy regime favors the candidate; none is inconclusive
  under the declared approximate rule. No universal dominance claim.
- Candidate simulator faster in every cell: baseline/candidate mean-time ratios
  1.420–16.331. Primary candidate time26.680685s; baseline190.822597s. These totals
  cover different numbers of unique trials; the ratios compare per-cell means.
- Both methods' errors decrease along epsilon1/2/4/8 on both B instances; no
  ranking reversal. RR-focused has lowest observed candidate MSE among C, but
  remains11.37x/16.59x the ER/BA baseline MSE. Selection is exploratory.
- Ideal predictions are consistent within2.142 combined SE for candidate and
  2.421 empirical SE for20 unique baseline conditions. This is not proof.
- No full-protocol truncation in fresh trials or prediction histories. Historical
  D2 also has none. Fixed-cap controls demonstrate nonzero conditional3M bias,
  but are not complete-protocol evidence or newly run comparison trials.

Full per-cell truth, means, bias, variance, MSE/RMSE, ratios, intervals,
predictions/timing, all figure explanations, stage/memory tables and exact
commands appear in [the technical report](../../FOUR_PATH_COMPARISON_2025.md).

## Resumed verification and preservation

Fresh regression: **913 passed in40.56s**, no failures/errors/skips. Reference
fingerprint verification exited0; all three sources remain clean at their pins.
57 pre-existing source/test/dependency files and271 Phase4B artifacts retain
pre-Phase5B hashes. Saved Phase5B inventory also verifies all312 hashes.
Full resumed replay passed:15,600 candidate outputs/transcripts,12,000 baseline
outputs/transcripts and10,400 independent prediction histories;38,000 distinct
seed coordinates. No estimate mismatch. Final git diff --check passed. Resumed
changes are only README, ALGORITHMS, comparison report, STATUS and this checkpoint.

Source implementation/API inventory:

- src/private_graphlets/four_path_comparison.py
- scripts/run_four_path_comparison.py
- scripts/analyze_four_path_comparison.py
- scripts/profile_four_path_comparison.py
- tests/test_four_path_comparison.py
- experiments/configs/four_path_phase17_comparison.json
- experiments/configs/four_path_phase17_smoke.json
- docs/FOUR_PATH_COMPARISON_2025.md and this checkpoint

README, ALGORITHMS and STATUS receive focused completion updates. During this
resumption no source, test, config, private mechanism, lock or reference changes.

Reproduction receipts live in ignored build/phase17/: full-run.log,
full-replay.json, final-verification.json, final-tests.log, focused-final.log,
profile.json, analysis.json, resumed-tests.log/xml, resumed-references.json,
resumed-preservation.json and resumed-replay.json. The complete study resides at
experiments/results/four_path_phase17_comparison/. Historical graph artifacts
must be transferred intact for the pinned-manifest reproduction workflow.

## Limitations and stopping boundary

Equal nominal D+O+R+M+C versus baseline epsilon assumes the same fixed-public-
vertex, undirected-one-edge adjacency and ideal one-owner RR. The candidate's
adaptive guarantee and both executable samplers remain experimental/unverified.
One graph realization per setting,600 trials, normal/delta approximations,
shared baseline observations, selected allocation minima and fixed timing order
limit inference. n<=100; no real-world comparison or observed full truncation.
No deployed communication or cryptographic sampler. Source-only checkout omits
ignored experiment artifacts. The baseline variance calculator is non-private
ideal evaluation, not an algorithm replacement or privacy proof.

The bounded results support a final report of unfavorable candidate accuracy
and favorable centralized runtime. Further graph realizations, real-world or
rare-event experiments and independent proofs would require separate scope.
No new phase, estimator tuning, commit or push.
