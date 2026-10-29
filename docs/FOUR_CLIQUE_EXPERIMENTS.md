# Preliminary four-clique comparison — Phase 06

2026-10-29. **Public synthetic diagnostics only.** All candidate/private-baseline
records are research simulations with unverified executable privacy. No result
here is a formal privacy proof or an established general utility comparison.
The configuration was fixed before running; no seeds, corrections, negative
outputs or cap rules were adjusted in response to results.

## Configuration and exact references

[four_clique_phase06.json](../experiments/configs/four_clique_phase06.json)
specifies **8 graphs × 4 epsilons × 5 methods × 100 trials = 16,000 trials**,
160 cells. Epsilons are **0.5, 1, 2, 4**. This is a small exploratory grid,
not the next large experimental campaign. Each method receives the same total
edge epsilon; allocations differ as explicitly recorded per trial.

| Graph | n | m | Degeneracy | Exact K4 |
|---|---:|---:|---:|---:|
| empty6 | 6 | 0 | 0 | 0 |
| K4 | 4 | 6 | 3 | 1 |
| K8 | 8 | 28 | 7 | 70 |
| book6: six earlier centers on one closing triangle | 9 | 21 | 3 | 6 |
| er_sparse14, p=.25, seed 6101 | 14 | 18 | 2 | 0 |
| er_dense14, p=.65, seed 6102 | 14 | 58 | 6 | 71 |
| ba16, attachment m=3, seed 6201 | 16 | 39 | 3 | 0 |
| sbm16, blocks 8+8, within .7/between .1, seed 6301 | 16 | 47 | 5 | 22 |

Empty6 uses ER p=0, seed 6100; cliques and book are deterministic. All eight
counts agree among actual ESCAPE, independent four-set enumeration, exact
oriented triples and the separate noise-disabled k-CoreD oracle. Every realized
private ordering additionally passes an uncapped exact-count identity check
inside the synthetic evaluation driver. This driver is not a private release.

Methods: canonical six-factor `baseline`; `fixed_uncapped`; `fixed_cap3`;
`kcore_noisy_cap`; and `kcore_cap3`. Fixed means public ID order. k-CoreD uses
psi=.5, threshold fraction=.5, bias factor=1. Noisy cap uses beta=.05. The full
budget table is in [implementation](FOUR_CLIQUE_IMPLEMENTATION.md); raw CSVs
also record epsilon_O/D/R/C and local count-noise scale. Public-cap k-CoreD at
total epsilon 4 uses `(1,0,1.5,1.5)` to keep ordering epsilon within 1.

Master simulation seed is **202610290600**. Trial seeds are injective integer
encodings `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|
(method_index<<16)|trial`, with 16-bit coordinate bounds. Each trial then spawns
four independent NumPy stream domains for ordering/cap/RR/count. Graph seeds
are separate. Replay uses the same observations, not new independent trials.
Seeds and exact diagnostics occur only in this non-private evaluation output.

## Measurements and observed findings

Raw CSVs contain graph size, exact truth, estimate, retained-clique target,
cap, exact maximum outgoing degree, number of clipped vertices, ordering rounds,
budgets, runtime, method, seed coordinates and experimental status. Aggregates
compute mean, signed empirical bias, sample variance (`ddof=1`), standard
deviation, MAE, RMSE against original truth, relative RMSE where truth>0, empirical
mean SE, and errors against the per-trial retained target. Original-target bias
and cap-induced target loss are separate quantities.

**The candidate did not show an observed accuracy advantage in this grid.**
All four oriented configurations had larger observed RMSE than the baseline in
all **32 graph–epsilon cells**. For the full `kcore_noisy_cap` configuration,
the median observed RMSE ratio to baseline was **1194.91**. This descriptive
ratio is strongly affected by small/zero targets and rare RR events; it is not
a confidence statement or an asymptotic comparison.

Representative observed RMSE at total epsilon 4:

| Graph | Baseline | Fixed uncapped | Fixed cap 3 | k-CoreD noisy cap | k-CoreD cap 3 |
|---|---:|---:|---:|---:|---:|
| K4 | 0.3407 | 2.8082 | 2.5780 | 15.9938 | 5.1524 |
| K8 | 10.3790 | 58.2257 | 65.3317 | 324.8712 | 66.6862 |
| book6 | 2.2731 | 86.7683 | 6.4987 | 465.4868 | 9.4107 |
| er_dense14 | 11.0390 | 300.0803 | 69.5501 | 1907.8589 | 71.7850 |
| sbm16 | 4.6137 | 472.9419 | 21.4833 | 2014.5462 | 23.3287 |

The noisy cap equaled `n-1` in **92.0625%** of its 3,200 trials; no actual
outgoing set was clipped in those trials. Its mean maximum outgoing degree
was 4.988125, versus 5.0 for the fixed-order configurations across this balanced
grid. Those averages mix different graphs; they are not a theorem about order
quality. Large conservative caps and local Laplace scales are consistent with
the poor observed utility; this experiment does not isolate a single cause.

Cap 3 reduces sensitivity but can lose most of the target. K8 retains **5 of
70** cliques under both orders. Dense ER retains **1 of 71** under ID order;
the private-order mean retained count at epsilon 4 is **2.54**. Book6 retains
all six under its fixed center-first order, versus mean **4.49** under private
order at epsilon 4. These are cap-target observations, not tuning opportunities
used to alter this run.

**100 trials do not resolve all RR tails.** For empty6 at epsilon 4, the ideal
baseline has variance `choose(6,4)*tau^6`, where
`tau=exp(4)/expm1(4)^2`: its ideal SD is **2.6587690e-5**, but observed RMSE
was **6.4216166e-8**. Distinct four-set products have zero covariance on this
edgeless input; rare large products dominate the second moment and were poorly
represented. This explains why extreme observed ratios must not be interpreted
as precise population ratios. Empirical mean SEs are diagnostics, not guaranteed
confidence intervals. No finite-sample ranking is presented as a general result.

All **7,326 negative estimates** are retained. **60 cells** have undefined
relative RMSE because truth is zero. No observations were clipped, rounded,
dropped, filtered or replaced. Runtime was **12.689841s** for the final experiment
pipeline under concurrent verification load; summed mechanism-call time was
**10.279106s**. An earlier complete run took 11.296029s; a rerun after adding
complete ESCAPE build provenance matched every non-timing CSV field exactly.
These are the same 16,000 observations reproduced, not 32,000 independent trials.
Mechanism timers include stream construction and protocol work,
excluding subsequent exact diagnostics. Neither timing is a distributed benchmark.

## Files, plots and reproduction

Local ignored results:
`experiments/results/four_clique_phase06/{config.json,trials.csv,summary.csv,escape_reference.json,manifest.json,graphs/*.edges}`.
`manifest.json` records source hashes, versions, Git state and output hashes.
Actual ESCAPE inputs/outputs are retained independently of Python counts.
The small [accuracy_06.json](status/accuracy_06.json) is intentional evidence
stored with the reports; the CSVs must be transferred separately or recreated.

Local ignored plots, each PNG/PDF:
`plots/four_clique_phase06/{rmse_vs_epsilon,mean_vs_exact,estimate_distributions,retained_targets}`.
Plots use verified saved CSVs only. RMSE uses a log axis; mean estimates use a
labeled symmetric-log axis; histograms preserve the full estimate range and mark
both original truth and mean retained target. Source-data hashes accompany plots.

From the project root, after `bash scripts/setup.sh`:

```bash
export ESCAPE_ROOT=/path/to/escape
.venv/bin/python scripts/run_four_clique_experiments.py run
.venv/bin/python scripts/run_four_clique_experiments.py verify --replay
.venv/bin/python scripts/run_four_clique_experiments.py plot
.venv/bin/python scripts/analyze_four_clique_experiments.py \
  --output build/phase06/accuracy_summary.json

# Existing result directories are never overwritten by a new run.
.venv/bin/python scripts/run_four_clique_experiments.py run \
  --output experiments/results/four_clique_phase06_repeat
# Regenerate figures from the original saved data into another directory.
.venv/bin/python scripts/run_four_clique_experiments.py plot \
  --output build/phase06/regenerated_plots
```

`--escape-root` may replace the environment variable. The default build is under
`build/phase06/escape`. Verification replays **all 16,000 estimates and every
non-timing trial diagnostic exactly**, checks saved hashes and recalculates
aggregate metrics. Figures also regenerate with matching file hashes. A full
test of the small pipeline checks corruption detection and output overwrite
rejection. No further grid expansion or new pattern is authorized by this report.
