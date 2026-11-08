# Evaluation conventions for future patterns

Each graph pattern should have its own independent experiment script and
algorithm-specific parameters. This document defines conventions only; it does
not introduce a shared framework or implement any future experiment.

| Setting | Standard |
|---|---|
| Inputs | Karate, Dolphins, Les Misérables, Brightkite-50, BA-100, SBM-100; use the six pinned files in `data/processed/graph_manifest.json` |
| Total privacy budgets | epsilon = 0.5, 1, 2, 4 |
| Repetitions | 200 independent mechanism trials per graph/budget |
| Truth | Verified ESCAPE exact **non-induced** count of the relevant pattern |
| Accuracy | MSE, RMSE, bias, population variance, MAE, relative RMSE |
| Runtime | Seconds per complete estimator call; record hardware and exclude offline evaluation work |
| Reproducibility | Save the executed configuration, source/data hashes, versions and independent simulation seeds |
| Outputs | Individual trial records plus one summary row per graph/budget/method; save incrementally and support resume |

For estimates X_1,...,X_N and exact count K, use

- mean = sum(X_t)/N;
- MSE = sum((X_t-K)^2)/N, calculated directly;
- RMSE = sqrt(MSE);
- bias = mean-K;
- population variance = sum((X_t-mean)^2)/N (`ddof=0`);
- MAE = sum(abs(X_t-K))/N;
- relative RMSE = RMSE/K when K>0, otherwise undefined (empty CSV field).

The empirical identity is MSE = population variance + bias². Keep negative and
non-integer estimates. Distinguish discarded edges/vertices from lost pattern
copies. Exact truth, seeds and other non-private diagnostics belong in evaluation
records, never in a claimed private release.

Use consistent field names: `graph`, `method`, `epsilon`, `trial`, `seed`,
`estimate`, `exact_count`, `runtime_seconds`; summaries add `trials`, `mse`,
`rmse`, `bias`, `variance`, `variance_ddof`, `mae`, and `relative_rmse`.
Record each algorithm's actual per-stage budgets and other public parameters.
Different algorithms may use different allocations, orientations, sensitivities
and noise laws; the K4 equal-quarter split is **not** a convention for other
patterns. Total privacy claims require mathematical justification of adjacency,
sensitivity, composition and all released messages. Empirical accuracy does not
prove DP. NumPy seeds provide simulation reproducibility, not secure randomness.

Keep verification proportionate. Reuse accepted exact counts, avoid expensive
exact diagnostics inside randomized loops, and preserve completed trials across
interruptions. Do not pool smoke tests, abandoned runs or previous configurations
into a new study. A future pattern's study requires its own explicit authorization.
