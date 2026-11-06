# Phase 4B — Private P4 accuracy study

## Predeclared plan and resumption

Study plan saved before the interruption on 2026-11-05; execution resumed on
2026-11-06 (America/Vancouver). The existing 30-cell JSON configuration is
unchanged. This is a **NON-PRIVATE synthetic research study**, not a protected
release. The existing five-stage estimator and MSE formula are unchanged.

The original implementation and configs were saved in intervening commits; the
resume began with a clean tree at `86f7ed3`. No full study had run. An interrupted
test command returned 40 passes and one failure: pandas treated CSV NaN and
Python None differently under warnings-as-errors for undefined relative RMSE.
Intervening commit99d542a already normalized null values in replay. The resumed
work additionally represents the undefined metric as NaN at aggregation, with
`relative_rmse_defined=false`; no zero-count graph is discarded.

Repository checkpoint 13 now describes independent dataset preparation. This
study keeps its predeclared `phase13` config/output identifiers and schema, but
uses checkpoint **14** to avoid overwriting that history.

## Questions and fixed design

Measure absolute/relative error versus graph size and density, total epsilon,
allocation, analytical component dominance, truncation and theory agreement.
One realization per graph setting limits population generalization.

- A: n=20,50,100; ER p=.05/.30 and BA attachment m=1/4: 12 cells.
  Allocation D/O/R/M/C=2/.5/1/1/2 (total6.5), beta=.05.
- B: the exact same ER(.30,n50) and BA(m4,n50) instances at total epsilon
  1,2,4,8, fractions .30/.10/.25/.15/.20: 8 cells, beta=.05.
- C: those two instances at total4: balanced(.8,.8,.8,.8,.8),
  degree-focused(1.4,.5,.7,.6,.8), RR-focused(.5,.5,1.5,.5,1): 6 cells.
- D2: K20 and BA(m4,n50), cap allocation .5 or2, other allocations
  D/O/R/C=2/.5/1/2: 4 cells. Predeclared beta=.9 intentionally lowers the
  conservative cap padding to investigate underestimation; it is valid but is
  **not** the beta=.05 configuration of A–C. Totals are6 or7.5, not equal.
- D1: fixed ascending orders on K4 with B=1/2 and K10 with B=2/4. These are
  conditional mathematical controls, never labeled complete-protocol trials.

Each cell: **600 full trials and400 independent prediction histories**.
Total: **30 cells,18,000 full trials,12,000 histories**,13 graph instances plus
K4/K10 controls. Master seed202611051304. ER seeds130000+n (p.05),131000+n
(p.30); BA seeds132000+n+100m. All are explicit in
`experiments/configs/four_path_phase13_accuracy.json`.

Cell-specific master seeds use the existing coordinate-seed function; full and
prediction domains remain disjoint. Prediction draws only ordering/cap. No
seed, sample size, threshold, graph or budget changes are permitted based on
observed utility. The smoke uses separate master202611051300 and3 trials per
stream in four representative cells, with no inference from its accuracy.

## Precision and resource plan (before full execution)

Predeclared discrepancy threshold: |empirical−predicted MSE| <=3 combined SE,
where combined SE=hypot(SE of squared errors, independent prediction SE).
Precision adequate only if combined SE/predicted MSE <=.15. These are per-cell
exploratory diagnostics, not simultaneous confidence guarantees. Heavy tails
and estimated standard errors make normal approximations imperfect. RMSE error
bars use the delta approximation SE(MSE)/(2 RMSE); relative RMSE is undefined
at zero exact P4, represented by a blank CSV metric plus an explicit false flag.

Initial conservative feasibility estimate: 5–20 minutes including full replay,
under1GB artifacts and under1GB peak process memory. This is a planning estimate,
not a measured outcome. Dense n100 histories and exact coefficient construction
cost much more than the Phase4A n4/n8 pilot. The smoke supplies a measured
cross-check before launching the unchanged bounded matrix. No automatic expansion.

The runner streams mechanism JSONL; verification reads one transcript at a time.
Per-cell tables retain600 full rows and400 order/analytical rows. Failure records
mark incomplete work; no existing directory can be overwritten.

## Reproducibility and boundaries

`run_four_path_study.py plan|run|verify` reuses Phase4A trial, aggregation,
artifact and replay functions through a separate Phase4B validator (n<=100,
full trials<=1000, prediction histories<=500). Phase4A public limits remain
n<=30 and <=500 trials. No second analytical formula is implemented.

Each distinct study/control graph is checked against actual original ESCAPE:
`connected_four['3-path']` and `three_vertex[3]`. Raw input/output/stdout/stderr,
compiler/source/binary provenance are saved. Graphs, exact diagnostics, seed
coordinates and timings are separate from modeled mechanism-result/transcript
JSONL. The complete synthetic artifact set is non-private.

Verification checks file inventory/hashes, native evidence, exact counts, cell
configuration, independent seed coordinates, every conditional formula,
reconstructed aggregates and decomposition; `--replay` regenerates all full
results/transcripts and prediction histories. It does not rerun ESCAPE during
verification; initial execution is preserved as native evidence.

Generated figures are PNG and PDF under the results `plots/` directory. Their
hashes are included in the study manifest. The signed covariance is retained
as a signed fraction, not a positive stacked percentage.

## Computational and privacy limitations

Exact counts cost O(n+m+sum_edges min(d_u,d_v)), worst O(n^3).
Conditional analysis computes outgoing prefixes/coefficient multiplicities in
O(n+m log(1+D)+nB^2), adds O(n^2) pair arithmetic and exact triangle counts.
Prediction adds k-CoreD O(r(n+m)+n log n) and cap sampling. Complete simulation
costs O(n+r(n+m)+n log n+n^2+m log(1+D)+nB^2). Active graph/transcript storage
is O(n+m+n^2+nr); per-cell evaluation tables add O(F+Pn). These evaluation
costs are not private-protocol costs. Hashing/serialization scale with bytes.

RR uploads are O(n^2); full matrix delivery to n clients can cost O(n^3).
Physical transport and selective protected delivery are unimplemented. NumPy
randomness, centralized execution, floating-point/error/timing behavior and
independent formal privacy review remain unresolved. Tests establish neither
formal LEDP nor low-out-degree utility. No baseline, superiority claim or Phase5
implementation is part of this work.

## Smoke feasibility observation (before full execution)

The four-cell smoke completed12 full trials and12 histories, with actual ESCAPE
and deterministic replay passing. Pipeline8.480s (including figure/font-cache
startup), artifacts490,536 bytes excluding root manifest, process peak172,457,984
bytes. Measured mean full-estimator time ranged0.448–1.782ms; analytical time
0.062–0.739ms; prediction-order/cap time0.163–0.723ms for n20/n50 smoke cells.
A simple n^2 extrapolation to n100, with allowance for denser coefficient loops,
puts simulation plus evaluation in the low minutes; serialization/replay and
plotting justify the conservative5–20-minute planning allowance. Per-cell smoke
artifacts22–58KB with only3 trials suggest order100–300MB for the full matrix,
well below the1GB allowance. These extrapolations are estimates, not guarantees.
Matplotlib's default cache was sandbox-blocked; it successfully used a temporary
cache. Subsequent run commands set MPLCONFIGDIR to project build storage.


## Completed execution and observed accuracy

All30 cells completed:18,000 full trials and12,000 independent histories.
Actual ESCAPE validated all13 study graphs and K4/K10 controls (15 distinct
graphs), with raw evidence retained. No failed or dropped trials.

Pipeline77.698711s; modeled private estimation29.312820s; full-history analytical
diagnostics21.957268s; prediction ordering/cap6.652776s; prediction analytical
calculations6.738763s. Remaining13.037085s includes native validation, aggregation,
serialization, provenance and plotting; it is not pure serialization time.
Compilation occurs before this pipeline timer. Process peak RSS284,721,152 bytes
(about271.5MiB), including interpreter/plotting; artifact bytes318,410,150
(about303.7MiB), excluding only the root manifest. Replay is separate.

### Graph truth and size/density experiment A

| graph | n | m | maximum_degree | exact_four_paths | exact_triangles | empirical_bias | empirical_rmse | relative_rmse |
|---|---|---|---|---|---|---|---|---|
| er05_n20 | 20 | 10 | 3 | 5 | 0 | -18.6819 | 180.76 | 36.152 |
| er30_n20 | 20 | 56 | 9 | 1447 | 25 | -15.0184 | 482.949 | 0.333759 |
| ba1_n20 | 20 | 19 | 10 | 45 | 0 | -13.062 | 250.884 | 5.5752 |
| ba4_n20 | 20 | 64 | 11 | 2400 | 55 | 22.5596 | 636.18 | 0.265075 |
| er05_n50 | 50 | 60 | 8 | 378 | 6 | -1.92277 | 499.618 | 1.32174 |
| er30_n50 | 50 | 343 | 22 | 59712 | 411 | 768.021 | 6068.81 | 0.101635 |
| ba1_n50 | 50 | 49 | 16 | 351 | 0 | -20.3841 | 539.303 | 1.53648 |
| ba4_n50 | 50 | 184 | 20 | 13214 | 116 | 103.575 | 2166.92 | 0.163987 |
| er05_n100 | 100 | 257 | 11 | 6318 | 23 | 11.8953 | 1750.73 | 0.277102 |
| er30_n100 | 100 | 1469 | 42 | 1218873 | 4189 | -1580.74 | 55704.9 | 0.045702 |
| ba1_n100 | 100 | 99 | 25 | 839 | 0 | 51.9911 | 1012.38 | 1.20666 |
| ba4_n100 | 100 | 384 | 36 | 41746 | 194 | 304.279 | 5331.54 | 0.127714 |

Absolute RMSE increased along each of these four size series, whereas relative
RMSE decreased. This is descriptive for one seeded realization per setting,
not a general scaling theorem. Sparse ER(n20,p.05) has just5 paths and relative
RMSE36.15; BA(m1) remains above1 even at n100. ER(p.30,n100) has relative
RMSE.04570, while BA(m4,n100) has.12771. Increasing size did not improve absolute
error. The BA m1 graphs are trees: T=0 does not eliminate local triangle noise.

### Every cell: empirical versus ideal prediction

MSE units are squared P4 copies. SEs are estimated standard errors, not confidence
intervals. All30 discrepancies are within3 combined SE; maximum standardized
discrepancy2.527. Combined SE/prediction ranges4.80%–7.48%, below the predeclared
15% precision threshold. This supports limited consistency, not exact confirmation
or a proof. No threshold or seed was adjusted after observing these outcomes.

| cell | empirical_bias | empirical_mse | se_mse | empirical_rmse | relative_rmse | predicted_mse | prediction_se | relative_discrepancy |
|---|---|---|---|---|---|---|---|---|
| A_er05_n20_pilot | -18.6819 | 32674.2 | 1891.04 | 180.76 | 36.152 | 37342.2 | 519.855 | -0.125006 |
| A_er30_n20_pilot | -15.0184 | 233240 | 13728.7 | 482.949 | 0.333759 | 222364 | 799.92 | 0.0489128 |
| A_ba1_n20_pilot | -13.062 | 62942.8 | 4552.83 | 250.884 | 5.5752 | 63493.7 | 1361.4 | -0.00867618 |
| A_ba4_n20_pilot | 22.5596 | 404725 | 23049.7 | 636.18 | 0.265075 | 388460 | 1080.74 | 0.0418688 |
| A_er05_n50_pilot | -1.92277 | 249618 | 14639.2 | 499.618 | 1.32174 | 231589 | 2337.78 | 0.0778503 |
| A_er30_n50_pilot | 768.021 | 3.68305e+07 | 2.2036e+06 | 6068.81 | 0.101635 | 3.60819e+07 | 5483.83 | 0.0207449 |
| A_ba1_n50_pilot | -20.3841 | 290848 | 22999.1 | 539.303 | 1.53648 | 318680 | 6095.24 | -0.0873354 |
| A_ba4_n50_pilot | 103.575 | 4.69555e+06 | 267169 | 2166.92 | 0.163987 | 4.74638e+06 | 7697.04 | -0.0107095 |
| A_er05_n100_pilot | 11.8953 | 3.06505e+06 | 169339 | 1750.73 | 0.277102 | 3.18715e+06 | 5223.77 | -0.0383099 |
| A_er30_n100_pilot | -1580.74 | 3.10304e+09 | 1.74294e+08 | 55704.9 | 0.045702 | 3.18083e+09 | 30493 | -0.0244576 |
| A_ba1_n100_pilot | 51.9911 | 1.02492e+06 | 60350.8 | 1012.38 | 1.20666 | 996268 | 17904 | 0.0287606 |
| A_ba4_n100_pilot | 304.279 | 2.84253e+07 | 1.54471e+06 | 5331.54 | 0.127714 | 2.90306e+07 | 31612.8 | -0.020851 |
| B_er30_n50_e1 | -4912.96 | 5.34995e+09 | 3.01335e+08 | 73143.3 | 1.22494 | 4.79609e+09 | 22470.5 | 0.11548 |
| B_er30_n50_e2 | 471.313 | 4.40859e+08 | 2.40075e+07 | 20996.6 | 0.351632 | 3.95763e+08 | 1.17328e+06 | 0.113947 |
| B_er30_n50_e4 | 73.8273 | 5.04938e+07 | 2.9049e+06 | 7105.9 | 0.119003 | 4.88377e+07 | 46409.4 | 0.0339099 |
| B_er30_n50_e8 | -24.0213 | 9.25272e+06 | 539541 | 3041.83 | 0.0509417 | 8.96007e+06 | 2601 | 0.0326615 |
| C_er30_n50_balanced | -464.029 | 8.32361e+07 | 4.77315e+06 | 9123.38 | 0.15279 | 8.62467e+07 | 48626.8 | -0.0349068 |
| C_er30_n50_degree | 230.47 | 9.10187e+07 | 5.09793e+06 | 9540.37 | 0.159773 | 8.76505e+07 | 100325 | 0.0384278 |
| C_er30_n50_rr | -154.133 | 8.2751e+07 | 5.42938e+06 | 9096.76 | 0.152344 | 7.65419e+07 | 22082.2 | 0.0811201 |
| B_ba4_n50_e1 | 729.09 | 3.65327e+09 | 2.052e+08 | 60442.3 | 4.57411 | 3.79515e+09 | 6215.14 | -0.0373833 |
| B_ba4_n50_e2 | -403.159 | 1.97427e+08 | 1.14314e+07 | 14050.9 | 1.06333 | 2.05674e+08 | 1.32963e+06 | -0.040093 |
| B_ba4_n50_e4 | -81.9898 | 9.61212e+06 | 523951 | 3100.34 | 0.234626 | 1.04984e+07 | 66173.9 | -0.084417 |
| B_ba4_n50_e8 | 9.27725 | 1.18691e+06 | 70256.1 | 1089.46 | 0.0824471 | 1.27604e+06 | 3054.86 | -0.0698433 |
| C_ba4_n50_balanced | -14.2756 | 1.48337e+07 | 889234 | 3851.46 | 0.291468 | 1.60698e+07 | 59000.3 | -0.0769197 |
| C_ba4_n50_degree | 97.0803 | 1.70196e+07 | 980929 | 4125.48 | 0.312206 | 1.80482e+07 | 110657 | -0.0569898 |
| C_ba4_n50_rr | 91.2205 | 1.33322e+07 | 817578 | 3651.33 | 0.276323 | 1.40518e+07 | 21893.9 | -0.0512095 |
| D2_complete_n20_cap05 | -31.1534 | 2.0201e+07 | 1.23777e+06 | 4494.56 | 0.0773058 | 2.14559e+07 | 1.86498e-10 | -0.0584848 |
| D2_complete_n20_cap2 | -30.3724 | 2.33851e+07 | 1.41875e+06 | 4835.82 | 0.0831754 | 2.14559e+07 | 1.86498e-10 | 0.0899163 |
| D2_ba4_n50_cap05 | 34.6428 | 4.26214e+06 | 232501 | 2064.5 | 0.156235 | 4.85019e+06 | 9701.44 | -0.121242 |
| D2_ba4_n50_cap2 | 3.68916 | 4.28028e+06 | 242987 | 2068.88 | 0.156568 | 4.55946e+06 | 6072.38 | -0.0612321 |

### Every cell: analytical decomposition

These five terms reconstruct predicted MSE within the checked numerical tolerance.
The adjustment is signed, not a standalone variance. All sampled squared
truncation terms are zero.

| cell | degree_noise | rr_unadjusted | shared_rr_adjustment | triangle_laplace | truncation_squared_error |
|---|---|---|---|---|---|
| A_er05_n20_pilot | 88 | 1189.26 | -3.1487 | 36068.1 | 0 |
| A_er30_n20_pilot | 38596 | 121832 | -14505.5 | 76441.2 | 0 |
| A_ba1_n20_pilot | 2020 | 5623.58 | -134.276 | 55984.4 | 0 |
| A_ba4_n20_pilot | 76032 | 245004 | -29618.2 | 97042.4 | 0 |
| A_er05_n50_pilot | 6532 | 50476.1 | -1897.99 | 176479 | 0 |
| A_er30_n50_pilot | 3.49632e+06 | 3.35016e+07 | -1.49589e+06 | 579942 | 0 |
| A_ba1_n50_pilot | 10884 | 76041.9 | -534.41 | 232289 | 0 |
| A_ba4_n50_pilot | 528684 | 3.98298e+06 | -214321 | 449036 | 0 |
| A_er05_n100_pilot | 158380 | 2.47669e+06 | -58956 | 611039 | 0 |
| A_er30_n100_pilot | 1.47584e+08 | 3.09537e+09 | -6.56227e+07 | 3.5007e+06 | 0 |
| A_ba1_n100_pilot | 38276 | 397435 | -2484.13 | 563042 | 0 |
| A_ba4_n100_pilot | 1.98466e+06 | 2.66386e+07 | -795772 | 1.20316e+06 | 0 |
| B_er30_n50_e1 | 1.58041e+08 | 1.31137e+09 | -2.56898e+07 | 3.35237e+09 | 0 |
| B_er30_n50_e2 | 3.90021e+07 | 1.78031e+08 | -6.34073e+06 | 1.85071e+08 | 0 |
| B_er30_n50_e4 | 9.71876e+06 | 3.49006e+07 | -1.49589e+06 | 5.7143e+06 | 0 |
| B_er30_n50_e8 | 2.42771e+06 | 6.54012e+06 | -295164 | 287411 | 0 |
| C_er30_n50_balanced | 2.1897e+07 | 6.06998e+07 | -2.41768e+06 | 6.06762e+06 | 0 |
| C_er30_n50_degree | 7.13825e+06 | 7.30372e+07 | -3.17731e+06 | 1.06523e+07 | 0 |
| C_er30_n50_rr | 5.62703e+07 | 1.8552e+07 | -601255 | 2.32087e+06 | 0 |
| B_ba4_n50_e1 | 2.49182e+07 | 4.21425e+08 | -3.56902e+06 | 3.35237e+09 | 0 |
| B_ba4_n50_e2 | 5.95695e+06 | 3.06774e+07 | -894713 | 1.69934e+08 | 0 |
| B_ba4_n50_e4 | 1.4722e+06 | 4.48342e+06 | -213206 | 4.75595e+06 | 0 |
| B_ba4_n50_e8 | 366985 | 766698 | -42859.3 | 185212 | 0 |
| C_ba4_n50_balanced | 3.32842e+06 | 8.91993e+06 | -351518 | 4.17298e+06 | 0 |
| C_ba4_n50_degree | 1.08051e+06 | 9.09299e+06 | -457105 | 8.33178e+06 | 0 |
| C_ba4_n50_rr | 8.63558e+06 | 3.65378e+06 | -86055.1 | 1.84846e+06 | 0 |
| D2_complete_n20_cap05 | 4.67932e+06 | 1.86804e+07 | -2.04036e+06 | 136547 | 0 |
| D2_complete_n20_cap2 | 4.67932e+06 | 1.86804e+07 | -2.04036e+06 | 136547 | 0 |
| D2_ba4_n50_cap05 | 528684 | 3.98292e+06 | -214772 | 553357 | 0 |
| D2_ba4_n50_cap2 | 528684 | 3.983e+06 | -214865 | 262648 | 0 |

Local triangle noise dominates sparse small graphs and low-epsilon settings.
Unadjusted RR dominates many denser/larger settings; degree noise becomes the
largest contribution in the RR-focused allocation, showing the tradeoff. The
signed covariance reduces the hypothetical sum before its subtraction by
0.0084%–8.6838% across cells (largest for K20). This algebraic comparison is
**not** a comparison against an independent-RR mechanism at equal total budget.

### Budget and allocation findings

On both fixed graph instances, empirical and predicted MSE decrease at every
tested epsilon step1→2→4→8. Adjacent empirical differences exceed3 combined
MSE SEs; no monotonicity violation required investigation. For ER, empirical
MSE decreases5.350e9→9.253e6; BA decreases3.653e9→1.187e6.

At total4, the three Experiment C allocations have predicted MSE ordering
RR-focused < balanced < degree-focused on both graphs. Empirical ER RR-focused
and balanced are almost indistinguishable: difference0.067 combined SE. BA
RR-focused versus balanced is1.243 SE, versus degree-focused2.888 SE; ER
RR-focused versus degree-focused1.110 SE. Thus no C pair involving RR-focused
clears a conservative3-SE comparison. These are exploratory comparisons, with
no multiple-comparison correction or independent winner-confirmation trials.
The Experiment B total4 fractions yield lower predicted MSE than all three C
allocations on these instances, underscoring that C does not identify an optimum.

### Truncation: controls versus full protocol

| control | original_triangles | retained_triangles | missed_triangles | bias | variance | mse |
|---|---|---|---|---|---|---|
| K4_B1 | 4 | 0 | 4 | 12 | 510.865 | 654.865 |
| K4_B2 | 4 | 2 | 2 | 6 | 567.534 | 603.534 |
| K10_B2 | 120 | 8 | 112 | 336 | 281779 | 394675 |
| K10_B4 | 120 | 40 | 80 | 240 | 272831 | 330431 |

Controls satisfy conditional bias=3M and MSE=variance+9M²; these are exact
ideal-model diagnostics, not measured five-stage performance.

| cell | trials | samples | full_truncation_frequency | full_mean_missed_triangles | full_mean_squared_missed | full_truncation_bias | truncation_frequency | prediction_mean_squared_missed | mean_truncation_squared_error | empirical_mse |
|---|---|---|---|---|---|---|---|---|---|---|
| D2_complete_n20_cap05 | 600 | 400 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2.0201e+07 |
| D2_complete_n20_cap2 | 600 | 400 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2.33851e+07 |
| D2_ba4_n50_cap05 | 600 | 400 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4.26214e+06 |
| D2_ba4_n50_cap2 | 600 | 400 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4.28028e+06 |

No sampled history missed triangles in any cell, including D2 with beta=.9.
Neither caps nor histories were replaced to force events. Zero observations
do not prove zero probability: for one fixed cell,0/600 gives a one-sided95%
binomial upper bound1−.05^(1/600)=.00498;0/400 gives.00746, assuming independent
identically distributed histories. These are per-cell bounds, not simultaneous
claims. Truncation frequency here means M>0, not merely a shortened neighbor
list. Full-protocol nonzero truncation remains empirically unvalidated.

### Per-cell timing

Mean/median seconds are stored for mechanism, prediction sampling and analytical
work in summary.csv; the table lists mechanism and analytical timing.

| cell | mechanism_mean_seconds | mechanism_median_seconds | analytical_mean_seconds | analytical_median_seconds |
|---|---|---|---|---|
| A_er05_n20_pilot | 0.000362782 | 0.000359479 | 5.47693e-05 | 5.44579e-05 |
| A_er30_n20_pilot | 0.000444638 | 0.000417626 | 8.64773e-05 | 8.58749e-05 |
| A_ba1_n20_pilot | 0.000389234 | 0.000372333 | 6.12372e-05 | 5.9417e-05 |
| A_ba4_n20_pilot | 0.000428996 | 0.000427791 | 9.46433e-05 | 9.3583e-05 |
| A_er05_n50_pilot | 0.00117913 | 0.00117685 | 0.000261532 | 0.000260333 |
| A_er30_n50_pilot | 0.00161092 | 0.00161015 | 0.00057947 | 0.000579771 |
| A_ba1_n50_pilot | 0.0011635 | 0.00115985 | 0.000251647 | 0.000249312 |
| A_ba4_n50_pilot | 0.0013756 | 0.00135412 | 0.000367876 | 0.000362645 |
| A_er05_n100_pilot | 0.00358274 | 0.00358379 | 0.000982336 | 0.000984875 |
| A_er30_n100_pilot | 0.00608492 | 0.0060709 | 0.00384212 | 0.00380275 |
| A_ba1_n100_pilot | 0.00336676 | 0.00336185 | 0.000868475 | 0.000867625 |
| A_ba4_n100_pilot | 0.00379803 | 0.00379992 | 0.00110939 | 0.00110848 |
| B_er30_n50_e1 | 0.00150215 | 0.00150033 | 0.000614693 | 0.000612604 |
| B_er30_n50_e2 | 0.00155754 | 0.00155479 | 0.000615354 | 0.00061498 |
| B_er30_n50_e4 | 0.00162118 | 0.00161827 | 0.000614117 | 0.000613188 |
| B_er30_n50_e8 | 0.00168314 | 0.00168367 | 0.000605068 | 0.000605271 |
| C_er30_n50_balanced | 0.00168017 | 0.0016816 | 0.00059335 | 0.000579875 |
| C_er30_n50_degree | 0.00166499 | 0.00165333 | 0.00061582 | 0.000611875 |
| C_er30_n50_rr | 0.00165607 | 0.00165767 | 0.000585018 | 0.000583626 |
| B_ba4_n50_e1 | 0.0013663 | 0.00136362 | 0.000412699 | 0.000412687 |
| B_ba4_n50_e2 | 0.00136267 | 0.0013636 | 0.000404696 | 0.000403104 |
| B_ba4_n50_e4 | 0.00138244 | 0.00137848 | 0.000386965 | 0.000385292 |
| B_ba4_n50_e8 | 0.00139424 | 0.00139615 | 0.000376055 | 0.000373667 |
| C_ba4_n50_balanced | 0.00140458 | 0.00140571 | 0.000355406 | 0.000353854 |
| C_ba4_n50_degree | 0.00137986 | 0.00137938 | 0.000385608 | 0.000383812 |
| C_ba4_n50_rr | 0.00139226 | 0.00138904 | 0.000365538 | 0.000364021 |
| D2_complete_n20_cap05 | 0.000640773 | 0.000620916 | 0.000301312 | 0.000300271 |
| D2_complete_n20_cap2 | 0.000623331 | 0.000621917 | 0.00032408 | 0.000300666 |
| D2_ba4_n50_cap05 | 0.00138517 | 0.0013719 | 0.000365933 | 0.000363959 |
| D2_ba4_n50_cap2 | 0.00137057 | 0.00136921 | 0.000365224 | 0.000362459 |

### Figure descriptions

All six PNGs were visually inspected; PDFs were also generated. Paths below are
relative to `experiments/results/four_path_phase13_accuracy/plots/`:

- `rmse_vs_size.png` / `.pdf`: absolute RMSE rises in each separate family/parameter
  series; dashed ideal predictions track the measured points.
- `relative_rmse_vs_size.png` / `.pdf`: relative error decreases for the tested
  realizations, but sparse BA(m1) stays above100%; this is not uniform utility.
- `mse_vs_epsilon.png` / `.pdf`: strong monotonic reduction across the four
  budgets on both unchanged instances, with empirical and prediction SE bars.
- `mse_by_allocation.png` / `.pdf`: RR-focused is analytically promising, but
  empirical allocation differences are not conclusive under3 combined SE.
- `mse_components.png` / `.pdf`: signed fractions show noise dominance shifting
  with graph/budget; negative covariance is explicitly below zero.
- `truncation.png` / `.pdf`: every bar has height zero, so no bar is visible.
  Both streams observed no missed triangles; this is an absence-of-events result,
  not missing data or a demonstration that truncation is impossible.

No smooth trend is fitted across unrelated families. Size-series connecting
segments are descriptive guides, not inferred scaling laws. Prediction-history
Monte Carlo SEs are in the CSV; size plots show point predictions and empirical
delta-method RMSE SEs.

## Verification, reproduction and next phase

Targeted new/Phase4A/3/2/1 suite: **288 passed in16.73s**. Full suite:
**821 passed in31.25s**, no failures/errors/skips. Smoke replay and full study
replay both passed, including every full transcript and prediction history.
The saved verification receipt is`build/phase13/p4_study_replay.json`. Existing
Phase4A results also passed replay unchanged. All three reference fingerprints
and the eight pre-interruption protected mechanism hashes match. Exact commands,
the historical interrupted test failure and resumed file inventory are recorded
in [checkpoint14](status/checkpoints/14_four_path_accuracy_study.md).

```bash
.venv/bin/python scripts/run_four_path_study.py plan
# Existing saved study: verify, do not overwrite.
.venv/bin/python scripts/run_four_path_study.py verify --replay
# Reproduction requires a NEW output directory; identical random outputs,
# runtime/provenance metadata may differ.
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" \
  .venv/bin/python scripts/run_four_path_study.py run \
  --output experiments/results/four_path_phase13_reproduction
```

The study is complete within its bounded design. It does not resolve rare-event
truncation, population-level graph variability or formal privacy. A separately
authorized Phase5 can reuse these graphs, exact counts, seeds/artifact conventions
and uncertainty measurements for a fair baseline comparison, after checking P4
normalization, adjacency/budget conventions and baseline runtime. No baseline
implementation or superiority claim was made, and no Phase5 work, commit or push
was performed.
