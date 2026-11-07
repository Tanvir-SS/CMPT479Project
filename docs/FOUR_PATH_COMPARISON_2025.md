# Phase 5B — Equal-nominal-budget private P4 comparison

**Complete,2026-11-07 (America/Vancouver).** The baseline has lower MSE in all26
predeclared comparisons; the candidate simulator is faster. Full resumed replay
and913-test regression pass. See the interruption audit and final verification
below; earlier plan text is preserved as the pre-execution record.

## Predeclared protocol (before full execution)

This is NON-PRIVATE synthetic research evaluation. Both private implementations
are preserved. The AISTATS 2025 baseline is the faithful independent Algorithm 1
reconstruction documented in [Phase 5A](FOUR_PATH_BASELINE_2025.md), including
its author-notebook-supported one-owner undirected RR convention. The complete
adaptive LEDP guarantee of our candidate and executable privacy of both NumPy
simulators remain experimental/unverified. Equal nominal budgets are not a
certified deployment-level privacy equivalence.

The primary question is lower MSE at equal total budget on the same fixed graph.
Secondary questions concern size/density, epsilon, allocation, runtime, memory,
truncation and consistency with ideal analytical predictions. No superiority is
presumed. No budgets, trial counts or graph realizations may change based on
observed error. No estimator tuning, optional classical control or new phase.

The checked-in `experiments/configs/four_path_phase17_comparison.json` declares:

- A: the 12 saved Phase 4B ER(.05/.30), BA(1/4) graphs at n=20/50/100;
  D/O/R/M/C=2/.5/1/1/2, total epsilon 6.5.
- B: saved ER(.30,n50) and BA(4,n50); total epsilon 1/2/4/8 with fractions
  .30/.10/.25/.15/.20, unchanged from Phase 4B.
- C: those same two graphs, total 4; balanced (.8,.8,.8,.8,.8), degree-focused
  (1.4,.5,.7,.6,.8), RR-focused (.5,.5,1.5,.5,1).
- All candidate beta=.05 and unchanged k-CoreD settings. Baseline epsilon is
  the full sum of the five candidate allocations, validated before either runs.
- 26 candidate cells, 600 fresh trials each (15,600); 20 unique baseline
  graph/epsilon conditions, 600 fresh trials each (12,000). Baseline epsilon 4
  is shared between B and all three C allocations on each graph.
- 400 fresh independent candidate prediction histories per cell (10,400), using
  the unchanged conditional-MSE and prediction infrastructure.
- Master seed 202611061705. Candidate cell masters use existing `trial_seed`
  coordinates (master, cell_index, 17, 0, 0); candidate full/prediction streams
  then use the preserved Phase 4A seed function. Baseline coordinates are
  (master, condition_index, 18, 0, trial). Smoke master 202611061700 is separate.

All 271 Phase 4B artifact hashes were verified before development. Graphs load
from those saved edge lists, with pinned historical root-manifest hash, exact
counts, deterministic generator identity and fresh native ESCAPE checks.
No missing graph is silently regenerated. Reproduction requires those historical
artifacts; their absence fails explicitly. Historical prediction/truncation
results remain historical; all primary candidate estimates are fresh.

## Statistical criteria

MSE=mean((estimate-truth)^2); sample variance uses ddof=1. MSE SE is the sample
standard deviation of squared errors divided by sqrt(600). Independent method
streams give SE_difference=hypot(SE_candidate,SE_baseline). Report candidate
minus baseline MSE, their MSE/RMSE ratios and observed lower error. Positive
difference or ratio>1 favors baseline. No clipping, rounding or deletion of
negative estimates. Relative RMSE is undefined for zero truth, retained as NaN.

Pointwise approximate 95% intervals use difference +/-1.959963984540054 SE.
Also report approximate Bonferroni simultaneous intervals across the 26 declared
comparisons: z=NormalDist().inv_cdf(1-.05/(2*26)). A directional adjusted
conclusion requires that interval to exclude zero; otherwise inconclusive.
This adjustment does not require cell independence, but the normal approximation
is not a finite-sample guarantee for heavy-tailed squared errors. No trial
expansion or stopping based on favorable/unfavorable outcomes is permitted.

Shared baseline observations remain 600 samples, never 1,800 or 2,400. Two MSE
differences sharing that baseline have estimated covariance SE_baseline^2;
therefore no pooling of their evidence as independent is allowed. When comparing
two candidate allocations directly, the common baseline cancels and independent
candidate SEs combine. Allocation ranking is descriptive/exploratory, not an
independently validated optimum. There is one graph realization per setting;
26 cells do not constitute 26 independent graph realizations.

Plots use +/-1 MSE SE, delta-method RMSE SE=SE_MSE/(2*RMSE), and delta ratio
SE=ratio*sqrt((SE_new/MSE_new)^2+(SE_base/MSE_base)^2). No smoothing across families.
Runtime figures report centralized total simulator time, not network latency.

## Independent exact ideal baseline variance

This evaluation-only extension never enters the private baseline. Write W=x+U,
where independent unordered-pair U have mean zero and variance h=e^epsilon /
(expm1(epsilon))^2. Expand the unordered P4 polynomial as sum_S c_S product U_e.
Distinct nonempty subsets are orthogonal, including those sharing coordinates:
a coordinate in their symmetric difference has a sole zero-mean factor.
Thus Var=sum_{nonempty S} c_S^2 h^|S|, accounting for all reused-report covariance.

For adjacency x, degrees d, s_u=sum_{w in N(u)}(d_w-1), and common-neighbor
counts t_uv, coefficient families are:

1. Single pair {u,v}:
   c=(d_u-x_uv)(d_v-x_uv)+s_u+s_v-x_uv(d_u+d_v-2)-3t_uv.
   The first part counts paths with uv in the middle; both possible endpoint
   roles add neighbor degree sums. Three common-neighbor corrections exclude
   repeated vertices. The pair need not itself be a true edge.
2. Adjacent pair {uv,vw}: c=d_u+d_w-x_uv-x_vw-2x_uw, counting the final
   endpoint attached at u or w outside these three vertices.
3. Disjoint pair {uv,wz}: c=x_uw+x_uz+x_vw+x_vz, the four possible bridges.
4. Three selected pairs: coefficient 1 iff they form a four-distinct-vertex
   path; there are 12*choose(n,4) such sets, independent of graph truth.

The implementation accumulates integer coefficient squares and evaluates
h*S1+h^2*S2+h^3*12*choose(n,4). Enumerating disjoint pair matchings costs O(n^4)
time, with vectorized O(n^2) working storage, practical within n<=100. Coefficient
arithmetic uses int64 at that bound (sums far below its limit), Python integer
accumulation, and float64 final polynomial. It is exact ideal-model algebra,
not exact floating-point MSE or a new private algorithm. Independent tests compare
against the existing path-set expansion oracle on every graph through n=5 and
all eight fixtures, at multiple epsilon values.

Candidate analytical MSE remains a Monte Carlo average over independent private
order/cap histories, including shared-RR covariance and truncation squared error.
Baseline ideal MSE equals its variance by unbiasedness. Agreement diagnostics
must include prediction uncertainty for the candidate, and must not be mistaken
for privacy proofs. The common fixed-epsilon O(n^3) RMSE rate does not determine
finite-n rankings or constants.

## Initial validation and execution plan

Focused infrastructure/variance tests: 33 passed in 5.65s, no failures/skips.
The smoke includes n=20,50,100, both method APIs, repeated allocation conditions,
actual ESCAPE and complete replay. It runs 3 trials/histories per selected cell;
its accuracy is not used to select the design. Runtime/storage measurements and
final executed results will be recorded below. Full execution remains pending
until smoke verification and resource review pass.

Smoke completed: 8 candidate cells / 5 baseline conditions, 24+15 private trials
and 24 prediction histories, 2.686257s pipeline, 1,509,887 artifact bytes,
265,633,792 process peak RSS bytes. Full smoke replay passed. Baseline simulator
means at n20/n50/n100 were approximately .000607/.007495/.057349 seconds;
the n100 ideal variance calculation took about .114 seconds. The smoke projection
is 193 seconds for all baseline simulator calls. Conservative allowance for the
full pipeline plus full replay is 5–20 minutes, under 1GB artifacts and under
1GB process memory. These estimates are saved in `build/phase17/resource-plan.json`.
The fixed study is feasible; no design changes were made from smoke outcomes.

## Computational interpretation and release boundaries

Both methods access exactly the same validated simple undirected graph with a
fixed public vertex set. Add/remove-one-edge adjacency and lower-public-ID RR
ownership are explicit. The candidate charges D+O+R+M+C; baseline charges their
sum entirely to RR. No baseline comparison at epsilon_R is used.

Candidate degree reporting is O(n), private ordering O(r(n+m)+n log n), cap
reporting O(n+m), RR generation/table and degree-product O(n^2), outgoing sorting
O(m log(1+Dmax)), and triangle scoring O(nB^2), plus validation/noise. Its memory
is O(n+m+n^2+nr). Baseline RR generation/debiasing is O(n^2); the exact weighted
server sum is O(n^3), with O(n^2) memory. Equal asymptotic categories do not imply
equal actual time. Per-trial timings include API validation and RNG creation,
exclude analytical evaluation, serialization, graph loading and ESCAPE.

Baseline needs one upload round and choose(n,2) logical RR bits, with no full
matrix broadcast to clients. Candidate has the same RR upload plus n degree,
cap and count scalar reports and ordering messages/feedback. Its in-memory RR
sharing is not a distributed transport implementation: full-table delivery to
all clients could cost O(n^3) bits. No communication benchmark or secure client
isolation is implemented. Process peak RSS includes interpreter, graph/evaluation
storage and plotting, not a per-method or distributed memory measurement.

Separate candidate result/transcript JSONL and baseline mechanism JSONL contain
only the modeled release fields. Graph identities, seeds, truth, errors,
predictions, timings and manifests are non-private evaluation artifacts. Even
mechanism files here are seeded research simulation records, not protected
releases on confidential data. Repeated actual private releases would require
composition; this study's epsilon is per invocation, not the entire study.

The full runner refuses existing output paths. Any failure preserves partial
artifacts and failure.json, and verification refuses to call it complete.
Verification checks full inventories/hashes, original graph identity, both
methods' coordinates, seed-domain separation, native truth, ideal variance,
recomputed metrics and complete result/transcript replay. Timing values are
observations and are not expected to replay. SHA-256 manifests detect accidental
corruption; they are not signatures against an attacker rewriting both files
and manifests.

## Executed full study and findings

All 26 candidate cells and 20 unique baseline conditions completed, without
failed/dropped trials or numerical-guard failures. Primary counts: 15,600 fresh
candidate trials, 12,000 baseline trials, 10,400 independent prediction histories.
Pipeline time262.292137s; artifact size446,652,856 bytes before final visual-QA
caption correction; process peak RSS303,136,768 bytes (~289.1MiB). Pipeline time
excludes initial compilation, subsequent replay/regression and separate profiling.

**The 2025 baseline has lower empirical MSE and RMSE in all26 comparisons.**
Every pointwise and approximate Bonferroni-adjusted interval favors baseline.
Candidate/baseline MSE ratios range5.5581 (ER(.30,n50),epsilon2) to19023.35
(ER(.05,n20),epsilon6.5). No tested accuracy regime favors the candidate, and no
primary comparison is inconclusive under the declared approximate interval rule.
This is conditional evidence on these fixed graphs/allocations, not a proof of
universal dominance or certified equal-private deployed mechanisms.

Absolute RMSE rises with graph size in each tested A series for both methods.
Relative RMSE falls in these realizations. The candidate remains poor on very
sparse inputs: ER(.05,n20) relative RMSE37.379 versus baseline.271; BA(1,n100)
1.185 versus baseline.0911. Dense ER(.30,n100) gives .04545 versus .00565.
The particularly large ratio at sparse n20 is consistent with candidate count
noise and split-budget costs; this explanation is not a causal ablation result.

Both methods' empirical MSE decreases at every tested epsilon1→2→4→8 step on
both fixed B graphs. Ranking never reverses. Ratio need not be monotone: ER
ratios12.32,5.56,6.80,78.40 and BA58.63,23.70,14.02,93.79. At epsilon8 the baseline
uses almost truthful RR, whereas the candidate still splits its budget across
five stages. These are finite-instance observations, not a universal epsilon law.

Among the three C allocations, RR-focused has lowest observed candidate MSE on
both graphs, but remains11.37x (ER) and16.59x (BA) the fixed baseline MSE.
Exploratory candidate-only differences versus balanced/degree are respectively
1.075/1.441 SE for ER and2.258/2.466 SE for BA. The selected minimum is not an
independently validated optimum; these secondary contrasts are not the primary
26 adjusted comparisons. The original B epsilon4 allocation actually has lower
observed candidate MSE than all three C choices on both graphs. No tuning follows.

All26 candidate empirical-versus-predicted MSE discrepancies are within2.142
combined SE. All20 unique baseline empirical-versus-exact-ideal MSE discrepancies
are within2.421 empirical MSE SE. These are consistency diagnostics, not exact
confirmation or privacy evidence. Baseline exact ideal variance calculations
cost0.711977s total across20 conditions, separate from private simulator timings.

Candidate mechanism calls consumed26.680685s across15,600 trials. Baseline calls
consumed190.822597s across12,000 unique trials. Per-cell mean baseline/candidate
runtime ratios range1.420–16.331, so candidate is faster in all tested cells.
The methods ran sequentially in a fixed order on this machine; these are
centralized descriptive timings, subject to cache/load/thermal effects, not a
randomized hardware benchmark. No algorithm was optimized in response.

## Truncation and bias: historical diagnostics kept separate

The baseline has zero bias under ideal independent RR. The candidate conditional
bias is3*M(H), with M omitted triangles. None of the15,600 fresh candidate trials
observed omitted triangles; all their mean missed counts are zero. The saved
Phase4B D2 records also show zero events in each of four600-trial cells, with
400 prediction histories each, even at their declared beta=.9. They are copied
as `historical_truncation.csv`; they are not new Phase5B trials or independently
repeated confirmation. No full-protocol cap was replaced to manufacture events.

The saved fixed controls retain K4 caps1/2: M=4/2, bias12/6; K10 caps2/4:
M=112/80, bias336/240. They are copied as `historical_fixed_controls.csv` and
remain conditional controls, not complete-protocol comparison results. Zero
observed truncation does not prove universal unbiasedness; per-cell0/600 has
one-sided95% binomial upper probability1-.05^(1/600)≈.00498 under iid histories,
not a simultaneous guarantee. Empirical nonzero full-protocol truncation remains
unresolved. No rare-event study was added after seeing the absence of events.

## Complete numerical tables

Rounded values below are presentation only; the saved CSV retains17-digit
precision. Both methods have600 observations per series. Repeated baseline
values are the same series, not additional samples. MSE units are squared path
copies; runtime columns are mean seconds per invocation.
### All cells: empirical error and exact target

| cell | epsilon | truth | new_mse | baseline_mse | new_rmse | baseline_rmse | mse_ratio |
|---|---|---|---|---|---|---|---|
| A_er05_n20_pilot | 6.5 | 5 | 34930.5 | 1.83619 | 186.897 | 1.35506 | 19023.3 |
| A_er30_n20_pilot | 6.5 | 1447 | 209250 | 2165.4 | 457.438 | 46.5339 | 96.633 |
| A_ba1_n20_pilot | 6.5 | 45 | 61309.5 | 55.5432 | 247.608 | 7.45273 | 1103.82 |
| A_ba4_n20_pilot | 6.5 | 2400 | 366497 | 3554.75 | 605.39 | 59.6217 | 103.101 |
| A_er05_n50_pilot | 6.5 | 378 | 223852 | 870.486 | 473.13 | 29.504 | 257.157 |
| A_er30_n50_pilot | 6.5 | 59712 | 3.20879e+07 | 543343 | 5664.62 | 737.118 | 59.0564 |
| A_ba1_n50_pilot | 6.5 | 351 | 329912 | 1136.28 | 574.38 | 33.7088 | 290.343 |
| A_ba4_n50_pilot | 6.5 | 13214 | 4.74966e+06 | 67089 | 2179.37 | 259.015 | 70.7964 |
| A_er05_n100_pilot | 6.5 | 6318 | 3.28339e+06 | 43803.4 | 1812.01 | 209.293 | 74.9575 |
| A_er30_n100_pilot | 6.5 | 1218873 | 3.0693e+09 | 4.73643e+07 | 55401.3 | 6882.17 | 64.802 |
| A_ba1_n100_pilot | 6.5 | 839 | 988054 | 5837.01 | 994.009 | 76.4003 | 169.274 |
| A_ba4_n100_pilot | 6.5 | 41746 | 2.89145e+07 | 448214 | 5377.22 | 669.488 | 64.5104 |
| B_er30_n50_e1 | 1 | 59712 | 4.48303e+09 | 3.63997e+08 | 66955.4 | 19078.7 | 12.3161 |
| B_er30_n50_e2 | 2 | 59712 | 3.72339e+08 | 6.69904e+07 | 19296.1 | 8184.77 | 5.5581 |
| B_er30_n50_e4 | 4 | 59712 | 4.66593e+07 | 6.85952e+06 | 6830.76 | 2619.07 | 6.80212 |
| B_er30_n50_e8 | 8 | 59712 | 9.30115e+06 | 118644 | 3049.78 | 344.447 | 78.3954 |
| C_er30_n50_balanced | 4 | 59712 | 8.52833e+07 | 6.85952e+06 | 9234.9 | 2619.07 | 12.4328 |
| C_er30_n50_degree | 4 | 59712 | 8.81576e+07 | 6.85952e+06 | 9389.23 | 2619.07 | 12.8519 |
| C_er30_n50_rr | 4 | 59712 | 7.79664e+07 | 6.85952e+06 | 8829.86 | 2619.07 | 11.3662 |
| B_ba4_n50_e1 | 1 | 13214 | 3.63329e+09 | 6.19656e+07 | 60276.8 | 7871.82 | 58.634 |
| B_ba4_n50_e2 | 2 | 13214 | 2.1026e+08 | 8.87142e+06 | 14500.3 | 2978.49 | 23.7008 |
| B_ba4_n50_e4 | 4 | 13214 | 1.16615e+07 | 831928 | 3414.9 | 912.101 | 14.0175 |
| B_ba4_n50_e8 | 8 | 13214 | 1.36956e+06 | 14602.1 | 1170.28 | 120.839 | 93.7923 |
| C_ba4_n50_balanced | 4 | 13214 | 1.67279e+07 | 831928 | 4089.97 | 912.101 | 20.1074 |
| C_ba4_n50_degree | 4 | 13214 | 1.69472e+07 | 831928 | 4116.7 | 912.101 | 20.371 |
| C_ba4_n50_rr | 4 | 13214 | 1.38034e+07 | 831928 | 3715.29 | 912.101 | 16.5921 |

### Uncertainty and directional interpretation

| cell | mse_difference | se_difference | ci95_low | ci95_high | simultaneous_low | simultaneous_high | adjusted_conclusion |
|---|---|---|---|---|---|---|---|
| A_er05_n20_pilot | 34928.7 | 2315.54 | 30390.3 | 39467 | 27746.2 | 42111.1 | baseline |
| A_er30_n20_pilot | 207084 | 11761.2 | 184033 | 230136 | 170603 | 243566 | baseline |
| A_ba1_n20_pilot | 61253.9 | 4627.45 | 52184.3 | 70323.6 | 46900.2 | 75607.6 | baseline |
| A_ba4_n20_pilot | 362943 | 19909.1 | 323921 | 401964 | 301187 | 424698 | baseline |
| A_er05_n50_pilot | 222981 | 13164.8 | 197179 | 248784 | 182146 | 263817 | baseline |
| A_er30_n50_pilot | 3.15446e+07 | 1.86677e+06 | 2.78857e+07 | 3.52034e+07 | 2.57541e+07 | 3.7335e+07 | baseline |
| A_ba1_n50_pilot | 328776 | 24497.7 | 280761 | 376791 | 252788 | 404765 | baseline |
| A_ba4_n50_pilot | 4.68257e+06 | 281039 | 4.13174e+06 | 5.2334e+06 | 3.81083e+06 | 5.55432e+06 | baseline |
| A_er05_n100_pilot | 3.23959e+06 | 192208 | 2.86287e+06 | 3.61631e+06 | 2.64339e+06 | 3.83579e+06 | baseline |
| A_er30_n100_pilot | 3.02193e+09 | 1.89376e+08 | 2.65076e+09 | 3.39311e+09 | 2.43452e+09 | 3.60935e+09 | baseline |
| A_ba1_n100_pilot | 982217 | 64610.7 | 855582 | 1.10885e+06 | 781803 | 1.18263e+06 | baseline |
| A_ba4_n100_pilot | 2.84663e+07 | 1.5962e+06 | 2.53378e+07 | 3.15948e+07 | 2.3515e+07 | 3.34175e+07 | baseline |
| B_er30_n50_e1 | 4.11903e+09 | 2.55725e+08 | 3.61782e+09 | 4.62024e+09 | 3.32581e+09 | 4.91226e+09 | baseline |
| B_er30_n50_e2 | 3.05349e+08 | 2.33888e+07 | 2.59508e+08 | 3.5119e+08 | 2.328e+08 | 3.77897e+08 | baseline |
| B_er30_n50_e4 | 3.97998e+07 | 2.89285e+06 | 3.41299e+07 | 4.54697e+07 | 3.08265e+07 | 4.8773e+07 | baseline |
| B_er30_n50_e8 | 9.1825e+06 | 508605 | 8.18565e+06 | 1.01793e+07 | 7.60488e+06 | 1.07601e+07 | baseline |
| C_er30_n50_balanced | 7.84238e+07 | 5.12952e+06 | 6.83701e+07 | 8.84775e+07 | 6.25127e+07 | 9.43349e+07 | baseline |
| C_er30_n50_degree | 8.12981e+07 | 5.4739e+06 | 7.05694e+07 | 9.20267e+07 | 6.43188e+07 | 9.82773e+07 | baseline |
| C_er30_n50_rr | 7.11068e+07 | 4.51698e+06 | 6.22537e+07 | 7.996e+07 | 5.70958e+07 | 8.51179e+07 | baseline |
| B_ba4_n50_e1 | 3.57132e+09 | 1.98722e+08 | 3.18183e+09 | 3.96081e+09 | 2.95491e+09 | 4.18773e+09 | baseline |
| B_ba4_n50_e2 | 2.01388e+08 | 1.20374e+07 | 1.77796e+08 | 2.24981e+08 | 1.6405e+08 | 2.38727e+08 | baseline |
| B_ba4_n50_e4 | 1.08296e+07 | 711326 | 9.43544e+06 | 1.22238e+07 | 8.62318e+06 | 1.3036e+07 | baseline |
| B_ba4_n50_e8 | 1.35496e+06 | 78255.1 | 1.20158e+06 | 1.50834e+06 | 1.11223e+06 | 1.5977e+06 | baseline |
| C_ba4_n50_balanced | 1.5896e+07 | 1.00485e+06 | 1.39265e+07 | 1.78654e+07 | 1.2779e+07 | 1.90129e+07 | baseline |
| C_ba4_n50_degree | 1.61153e+07 | 978699 | 1.41971e+07 | 1.80335e+07 | 1.30795e+07 | 1.91511e+07 | baseline |
| C_ba4_n50_rr | 1.29715e+07 | 819745 | 1.13648e+07 | 1.45781e+07 | 1.04287e+07 | 1.55142e+07 | baseline |

### Bias, variance and relative error

| cell | new_mean | baseline_mean | new_bias | baseline_bias | new_variance | baseline_variance | new_relative_rmse | baseline_relative_rmse |
|---|---|---|---|---|---|---|---|---|
| A_er05_n20_pilot | -0.448899 | 4.99959 | -5.4489 | -0.000407157 | 34959.1 | 1.83926 | 37.3794 | 0.271012 |
| A_er30_n20_pilot | 1458.72 | 1449.42 | 11.7174 | 2.42111 | 209461 | 2163.15 | 0.316129 | 0.0321589 |
| A_ba1_n20_pilot | 35.7701 | 44.6667 | -9.2299 | -0.333272 | 61326.5 | 55.5247 | 5.50239 | 0.165616 |
| A_ba4_n20_pilot | 2423.61 | 2401.5 | 23.6077 | 1.49924 | 366551 | 3558.43 | 0.252246 | 0.0248424 |
| A_er05_n50_pilot | 412.701 | 378.815 | 34.7005 | 0.814655 | 223019 | 871.274 | 1.25167 | 0.0780529 |
| A_er30_n50_pilot | 59149.1 | 59693.4 | -562.919 | -18.5789 | 3.18241e+07 | 543904 | 0.0948657 | 0.0123446 |
| A_ba1_n50_pilot | 367.104 | 353.885 | 16.104 | 2.88549 | 330203 | 1129.84 | 1.63641 | 0.0960365 |
| A_ba4_n50_pilot | 13280.6 | 13220.7 | 66.5754 | 6.66751 | 4.75315e+06 | 67156.4 | 0.164929 | 0.0196016 |
| A_er05_n100_pilot | 6317.72 | 6307.81 | -0.278637 | -10.1854 | 3.28887e+06 | 43772.6 | 0.286802 | 0.0331264 |
| A_er30_n100_pilot | 1.21997e+06 | 1.21928e+06 | 1098.33 | 406.684 | 3.07321e+09 | 4.72777e+07 | 0.0454529 | 0.00564634 |
| A_ba1_n100_pilot | 822.899 | 838.067 | -16.1011 | -0.932915 | 989443 | 5845.88 | 1.18475 | 0.0910611 |
| A_ba4_n100_pilot | 41484.3 | 41749.3 | -261.664 | 3.3016 | 2.88942e+07 | 448951 | 0.128808 | 0.0160372 |
| B_er30_n50_e1 | 58868.9 | 59724.6 | -843.087 | 12.626 | 4.4898e+09 | 3.64605e+08 | 1.12131 | 0.319512 |
| B_er30_n50_e2 | 58583.2 | 59856 | -1128.77 | 143.997 | 3.71684e+08 | 6.70814e+07 | 0.323153 | 0.137071 |
| B_er30_n50_e4 | 59669.4 | 59573.1 | -42.569 | -138.899 | 4.67354e+07 | 6.85165e+06 | 0.114395 | 0.0438617 |
| B_er30_n50_e8 | 59475.2 | 59735.1 | -236.776 | 23.1162 | 9.26052e+06 | 118307 | 0.0510748 | 0.00576848 |
| C_er30_n50_balanced | 60163 | 59573.1 | 450.967 | -138.899 | 8.5222e+07 | 6.85165e+06 | 0.154657 | 0.0438617 |
| C_er30_n50_degree | 59117.3 | 59573.1 | -594.737 | -138.899 | 8.79504e+07 | 6.85165e+06 | 0.157242 | 0.0438617 |
| C_er30_n50_rr | 60112.9 | 59573.1 | 400.891 | -138.899 | 7.79355e+07 | 6.85165e+06 | 0.147874 | 0.0438617 |
| B_ba4_n50_e1 | 10806.6 | 14054 | -2407.42 | 839.977 | 3.63355e+09 | 6.13623e+07 | 4.56158 | 0.595718 |
| B_ba4_n50_e2 | 13301.8 | 13255 | 87.8329 | 40.9836 | 2.10603e+08 | 8.88455e+06 | 1.09735 | 0.225404 |
| B_ba4_n50_e4 | 13377.8 | 13240.5 | 163.796 | 26.5156 | 1.16541e+07 | 832612 | 0.25843 | 0.0690253 |
| B_ba4_n50_e8 | 13270 | 13206.6 | 56.0231 | -7.39765 | 1.36871e+06 | 14571.7 | 0.0885639 | 0.00914478 |
| C_ba4_n50_balanced | 13453 | 13240.5 | 238.98 | 26.5156 | 1.66986e+07 | 832612 | 0.309518 | 0.0690253 |
| C_ba4_n50_degree | 13229.9 | 13240.5 | 15.895 | 26.5156 | 1.69753e+07 | 832612 | 0.311541 | 0.0690253 |
| C_ba4_n50_rr | 13459.7 | 13240.5 | 245.681 | 26.5156 | 1.3766e+07 | 832612 | 0.281163 | 0.0690253 |

### Analytical predictions and centralized runtime

| cell | new_predicted_mse | new_prediction_se | baseline_ideal_mse | new_seconds | baseline_seconds |
|---|---|---|---|---|---|
| A_er05_n20_pilot | 37325.8 | 541.092 | 1.95022 | 0.000361676 | 0.000570548 |
| A_er30_n20_pilot | 220679 | 794.176 | 1914.65 | 0.000415103 | 0.000601011 |
| A_ba1_n20_pilot | 62141.1 | 1327.09 | 55.9343 | 0.00036918 | 0.000566221 |
| A_ba4_n20_pilot | 388193 | 1035.68 | 3627.48 | 0.000423348 | 0.00060098 |
| A_er05_n50_pilot | 232498 | 2190.37 | 784.276 | 0.00115368 | 0.00727485 |
| A_er30_n50_pilot | 3.60854e+07 | 5282.43 | 534254 | 0.0015851 | 0.00784762 |
| A_ba1_n50_pilot | 310954 | 5706.53 | 929.509 | 0.00113532 | 0.00716774 |
| A_ba4_n50_pilot | 4.7513e+06 | 7400.63 | 67794.1 | 0.00131969 | 0.00745047 |
| A_er05_n100_pilot | 3.18705e+06 | 5061.81 | 49374.4 | 0.00357404 | 0.055111 |
| A_er30_n100_pilot | 3.18086e+09 | 31149.7 | 4.76014e+07 | 0.00602012 | 0.0601707 |
| A_ba1_n100_pilot | 972181 | 16572.8 | 6048.89 | 0.00331103 | 0.0540733 |
| A_ba4_n100_pilot | 2.89834e+07 | 28516.5 | 482306 | 0.00379092 | 0.0553678 |
| B_er30_n50_e1 | 4.79607e+09 | 22382.1 | 3.64828e+08 | 0.00150024 | 0.00745621 |
| B_er30_n50_e2 | 3.97368e+08 | 1.1881e+06 | 6.55488e+07 | 0.00155637 | 0.0078944 |
| B_er30_n50_e4 | 4.88709e+07 | 53258.3 | 6.74774e+06 | 0.00165417 | 0.00787651 |
| B_er30_n50_e8 | 8.95829e+06 | 2713.62 | 118913 | 0.00169371 | 0.0078852 |
| C_er30_n50_balanced | 8.63692e+07 | 53730.3 | 6.74774e+06 | 0.00167312 | 0.00787651 |
| C_er30_n50_degree | 8.75274e+07 | 89527.9 | 6.74774e+06 | 0.00163255 | 0.00787651 |
| C_er30_n50_rr | 7.65332e+07 | 21003.2 | 6.74774e+06 | 0.00165465 | 0.00787651 |
| B_ba4_n50_e1 | 3.79514e+09 | 5850.09 | 5.55912e+07 | 0.00136466 | 0.00737568 |
| B_ba4_n50_e2 | 2.07644e+08 | 1.4215e+06 | 8.61677e+06 | 0.0013598 | 0.00766828 |
| B_ba4_n50_e4 | 1.05573e+07 | 69293.1 | 859184 | 0.00137475 | 0.00753657 |
| B_ba4_n50_e8 | 1.27356e+06 | 3160.07 | 15086 | 0.00138716 | 0.00754259 |
| C_ba4_n50_balanced | 1.62017e+07 | 62339.6 | 859184 | 0.00139992 | 0.00753657 |
| C_ba4_n50_degree | 1.81483e+07 | 110484 | 859184 | 0.00137673 | 0.00753657 |
| C_ba4_n50_rr | 1.40754e+07 | 22826.4 | 859184 | 0.00138077 | 0.00753657 |

## Figures and visual review

Seven PNG/PDF pairs are in
`experiments/results/four_path_phase17_comparison/plots/`. All seven PNGs were
visually inspected. PDF counterparts are generated from the same figures.

- `rmse_vs_size`: baseline lower in each family/size; both absolute errors rise.
- `relative_rmse_vs_size`: relative error falls on these fixed instances, while
  sparse candidate errors can remain above100%.
- `mse_vs_epsilon`: both errors fall as epsilon increases; no ranking reversal.
- `mse_ratio_vs_size`: all candidate/baseline ratios are above1; the largest is
  the sparse ER n20 case. Delta-method SE bars are descriptive.
- `runtime_vs_size`: candidate simulator faster in each tested family/size;
  means only, not an inference about distributed communication.
- `allocation_sensitivity`: same epsilon4 baseline series shown at all three
  candidate allocations; RR-focused candidate is descriptively best among C.
- `comparison_summary`: all standardized differences favor baseline; pointwise
  intervals and Bonferroni thresholds are shown, with per-cell total epsilon.

Visual QA found the runtime plot inherited the RMSE error-bar caption. This
caption is corrected by the audited plot-only regeneration command; no trial,
metric, budget or statistical decision changes. Original run source provenance
remains in the manifest; plot-source hash and prior manifest hash record the
postprocessing revision. The analysis script reads existing summaries only.

## Files and reproduction

New tracked-source candidates (not committed by this task):

- `src/private_graphlets/four_path_comparison.py`: config/privacy validation,
  saved-graph validation, exact ideal baseline variance, metrics/uncertainty,
  shared-baseline orchestration, integrity/replay and seven figures.
- `scripts/run_four_path_comparison.py`: plan/run/verify/plot commands.
- `scripts/analyze_four_path_comparison.py`: saved-summary tables and descriptive
  findings, including exploratory allocation contrasts.
- `scripts/profile_four_path_comparison.py`: separate bounded stage/allocator
  diagnostic, without modifying either private mechanism.
- `tests/test_four_path_comparison.py`:35 tests, including exhaustive variance,
  equality/domain checks, native target/replay, shared series, corruption and
  plot-only regeneration preserving trial bytes.
- `experiments/configs/four_path_phase17_comparison.json` and
  `experiments/configs/four_path_phase17_smoke.json`.
- This report and `docs/status/checkpoints/17_four_path_comparison_2025.md`.

Phase5B updates only README, ALGORITHMS and STATUS among existing documentation.
The prior uncommitted Phase5A documentation is preserved separately. No changes
to private mechanisms, exact counters, pre-existing tests, locks, references or
historical result artifacts. No commit or push.

Actual execution commands (repository root, Python3.11 `.venv`):

```bash
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase17/references-before.json
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_four_path_comparison.py
.venv/bin/python scripts/run_four_path_comparison.py plan
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python scripts/run_four_path_comparison.py run --config experiments/configs/four_path_phase17_smoke.json --output experiments/results/four_path_phase17_smoke > build/phase17/smoke.log
.venv/bin/python scripts/run_four_path_comparison.py verify --output experiments/results/four_path_phase17_smoke --replay > build/phase17/smoke-replay.json
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python scripts/run_four_path_comparison.py run > build/phase17/full-run.log
.venv/bin/python scripts/run_four_path_comparison.py verify --replay > build/phase17/full-replay.json
.venv/bin/python scripts/analyze_four_path_comparison.py
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q --junitxml=build/phase17/full-tests.xml > build/phase17/full-tests.log
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_four_path_comparison.py > build/phase17/focused-final.log
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q --junitxml=build/phase17/final-tests.xml > build/phase17/final-tests.log
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase17/references-after.json
```

For reproduction, use `run --output experiments/results/four_path_phase17_reproduction`
with a new directory; existing outputs are refused. Verification uses `--output`
to select that directory. All historical graphs/results are required by this
config's pinned manifest. Transfer the saved artifacts intact; regenerating an
old run's timing-dependent manifest will not reproduce its pinned root hash.
If those artifacts are unavailable, explicitly reconstruct and validate original
graph hashes in a separately reviewed provenance update; do not silently switch
inputs or relax verification. No graph reconstruction was needed in this run.

The report/analysis and profiling scripts currently target the declared default
study paths. They refuse overwriting their existing output receipts; use their
saved outputs for inspection. Primary runner output overrides remain supported.
The complete generated study and build diagnostics remain ignored local artifacts,
not files added to Git. A final research handoff should transfer those artifacts
with their manifests; source-only checkout is insufficient to inspect this run.

## Limitations and research-report readiness

The bounded study supplies a reproducible negative accuracy result for the
candidate and a favorable centralized runtime result. It supports reporting
this tradeoff under the declared assumptions, not claiming candidate accuracy
superiority, optimal allocation, universal baseline dominance or formal LEDP.

Remaining limitations: one graph realization per setting,600 draws, normal/delta
approximations for possibly heavy-tailed errors, shared baseline dependence,
exploratory allocation selection, n<=100, no real-world comparative evaluation,
no observed complete-protocol truncation, fixed execution order for timings,
unimplemented distributed transport, noncryptographic PRNGs, finite-precision
privacy and unresolved independent adaptive-composition review. The exact
variance formula concerns ideal algebra, not numerical/distributional certification.

No further experiment is necessary to report this bounded Phase5B result as
such. Broader generalization would require independently declared additional
graph realizations/real-world studies and stronger uncertainty analysis; formal
privacy and communication claims require separate review/design. Those are
future work, not silently completed here. Neither estimator was adjusted in
response to unfavorable results. Stop after the technical handoff.


## Saved stage and memory diagnostic

The separately instrumented diagnostic was completed before the interruption;
resumption reads its saved `build/phase17/profile.json` without rerunning it.
Three profile calls per method/size and one separate traced-memory call use
explicit diagnostic seeds (18 profile calls +6 memory calls), never primary
accuracy samples. Graphs are the saved ER(.30) instances at total epsilon6.5.
Inclusive cProfile times include instrumentation overhead and are not primary
runtime estimates; concurrent machine load was uncontrolled. They must not be
summed with primary timings or interpreted as distributed execution costs.

| n | method | incremental traced peak bytes | serialized transcript bytes |
|---|---|---|---|
| 20 | candidate | 27152 | 3648 |
| 20 | baseline | 16176 | 1288 |
| 50 | candidate | 81424 | 14367 |
| 50 | baseline | 74753 | 8247 |
| 100 | candidate | 279962 | 46700 |
| 100 | baseline | 270089 | 33192 |

Tracemalloc measures Python-tracked allocations during a call with the graph
already loaded; it is neither total process RSS nor comprehensive native-library
allocation. JSON transcript bytes are an encoding diagnostic, not theoretical
bit communication. The candidate uses more traced storage here, but these six
bounded observations do not establish general memory superiority.

For n100, inclusive instrumented seconds per call are:

| method | stage | seconds |
|---|---|---|
| candidate | local_cap_report | 0.000382285 |
| candidate | sample_rr_upper | 0.00236872 |
| candidate | kcore_order | 0.007931 |
| candidate | local_degree_report | 0.000377175 |
| candidate | cap_from_reports | 1.70833e-05 |
| candidate | rr_matrix | 0.000505917 |
| candidate | estimate_triangles_from_rr | 0.00306114 |
| candidate | degree_product_estimate | 0.00113725 |
| baseline | sample_rr_upper | 0.0023995 |
| baseline | rr_matrix | 0.000500208 |
| baseline | four_path_weighted_sum | 0.0972961 |

Candidate triangle timing includes score validation, selection and local count
noise; ordering includes its internal queries and bookkeeping. Baseline weighted
sum dominates its measured profile, consistent with its cubic loops. These are
implementation observations, not evidence that low out-degree utility or secure
transport has been achieved.

## Interruption audit and resumed completion

Resumed on2026-11-07 from clean Git revision `acf3442` (previous `8849987`).
That commit already contained all comparison code,35 tests, full/smoke configs,
three utility scripts, this report and an interim checkpoint17. The ignored
artifacts additionally contained the complete26/20 study, seven PNG/PDF pairs,
full38,000-coordinate replay receipt, plot-only caption correction, profiling,
analysis, reference verification and913 passing final tests (38.23s). STATUS
and checkpoint17 were stale about replay/profiling/test completion.

Resumption preserves all experiment bytes and completes documentation, current
status and handoff. It also reruns full deterministic replay and the regression
suite from the saved commit, using new receipt names. No experiment, graph,
allocation, trial count, plot or private mechanism is overwritten or restarted.
Final saved artifact bytes are446,650,529 (excluding root manifest),312 hashed
files; the earlier446,652,856 figure predates the recorded caption correction.
Root manifest SHA256:
`3d5882281574e0cd43db0ef12ee169e5d15533cda6c9d92d252e4e2f0e9f4d80`.
All57 pre-existing source/test/dependency hashes and271 Phase4B artifact hashes
match their pre-Phase5B records. All three references verify unchanged.

Additional executed commands (the first three completed before interruption):

```bash
.venv/bin/python scripts/profile_four_path_comparison.py
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" .venv/bin/python scripts/run_four_path_comparison.py plot > build/phase17/plot-revision.json
.venv/bin/python scripts/run_four_path_comparison.py verify > build/phase17/final-verification.json
# Resumed verification; preserves prior receipts and all experiment artifacts.
.venv/bin/python scripts/run_four_path_comparison.py verify --replay > build/phase17/resumed-replay.json
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q --junitxml=build/phase17/resumed-tests.xml > build/phase17/resumed-tests.log
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase17/resumed-references.json
git diff --check
git status --short
```

No failed test, dropped cell or numerical execution failure was observed in this
phase. The corrected figure caption was a presentation defect, not a mechanism
or statistical defect. Broader privacy certification and optional future studies
are unresolved limitations, not checks counted as passed.


Final resumed outcomes: **913 passed in40.56s**, zero failures/errors/skips.
Complete deterministic replay: **verified**,15,600 candidate trials,12,000
baseline trials,10,400 prediction histories,38,000 distinct coordinates. Every
modeled result/transcript and prediction history reproduces; timings are not
replayed observations. All three reference fingerprints verified. Final
`git diff --check` passes. Resumption changed only five documentation files;
no source/config/test changes and no study artifact rewrites.

The final handoff is complete within Phase5B scope. The saved full tables include
all unfavorable results. No new phase, private-estimator edit, commit or push.
