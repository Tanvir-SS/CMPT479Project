# Reproducible 3-star accuracy experiments — phase 04

Date: **2026-10-28** (America/Vancouver). This is **non-private evaluation of
public synthetic graphs**. The experiment uses the unchanged phase-02 estimator
and actual ESCAPE counts as an independent implementation check. It is not a
formal privacy proof or an evaluation of a distributed deployment.

## Design fixed before observing results

The checked-in [configuration](../experiments/configs/three_star_phase04.json)
specifies **15 graphs × 5 budgets × 500 trials = 37,500 estimates**. Budgets are
`[0.25, 0.5, 1.0, 2.0, 4.0]`. There are three graph instances per family; each
graph is held fixed across trials and budgets. This probes different degrees and
sizes, not a statistically representative sample of graph families. No seeds,
budgets, graphs or trial counts were selected in response to outcomes.

| Graph ID | n | m | Exact S3 | Graph seed |
|---|---:|---:|---:|---:|
| star_n5 | 5 | 4 | 4 | deterministic |
| star_n20 | 20 | 19 | 969 | deterministic |
| star_n50 | 50 | 49 | 18,424 | deterministic |
| er_n30_p004 | 30 | 24 | 9 | 4101 |
| er_n60_p010 | 60 | 191 | 2,602 | 4102 |
| er_n100_p015 | 100 | 735 | 52,744 | 4103 |
| ba_n30_m1 | 30 | 29 | 279 | 4201 |
| ba_n60_m2 | 60 | 116 | 2,281 | 4202 |
| ba_n100_m4 | 100 | 384 | 24,852 | 4203 |
| sbm_n30 | 30 | 39 | 48 | 4301 |
| sbm_n60 | 60 | 165 | 1,392 | 4302 |
| sbm_n100 | 100 | 568 | 34,317 | 4303 |
| complete_n3 | 3 | 3 | 0 | deterministic |
| complete_n10 | 10 | 45 | 840 | deterministic |
| complete_n25 | 25 | 300 | 50,600 | deterministic |

ER probabilities are 0.04/0.10/0.15. BA attachment parameters are 1/2/4, using
NetworkX 3.4.2's default initial graph. SBM blocks are `[15,15]`, `[20,20,20]`,
and `[50,50]`; the complete symmetric probability matrices are in the config.
The last SBM has different within-block densities 0.12 and 0.30. Isolates are
retained: er_n30_p004 has six and sbm_n30 has three. Graph metadata records the
degree mean, maximum and population variance for interpretation, never release.

All 15 formula counts agree with actual ESCAPE output. The independent brute
force oracle is additionally used when n<=12 (star_n5, complete_n3,
complete_n10). For n=3, ESCAPE receives an additional isolate, preserving the
connected four-vertex count. Raw source output and normalized input are saved.

## Reproduction on Ubuntu/WSL

From the project root, after the README's Python 3.11 setup and reference clone:

```bash
export ESCAPE_ROOT=/path/to/escape
bash scripts/setup.sh
.venv/bin/python scripts/run_experiments.py run
.venv/bin/python scripts/run_experiments.py verify --replay
.venv/bin/python scripts/run_experiments.py plot
.venv/bin/python scripts/analyze_experiments.py --output build/phase04/accuracy.json

# Recreate figures independently from the same saved data:
.venv/bin/python scripts/run_experiments.py plot --output build/phase04/regenerated-plots
# Run real reference tests explicitly:
.venv/bin/python -m pytest -q -m escape_integration
```

`run` accepts `--config`, `--output`, `--escape-root` and `--build-dir`. The root
argument overrides ESCAPE_ROOT. It refuses to overwrite an existing result
directory: use a new `--output` for another run, then pass that directory via
`--results` to verify/plot. The default is
`experiments/results/three_star_phase04/`; plots default to
`plots/three_star_phase04/`. Verification and plotting do not need an ESCAPE
checkout or executable once results are saved. They use the installed locked
Python environment. A source archive includes configuration and scripts but
intentionally excludes generated outputs; reproduce or transfer them separately.

Graph seeds are independent of mechanism stream construction. The master
mechanism seed is **202610280400**. For zero-based graph index g, epsilon index e
and trial t, the runner creates
`Generator(PCG64(SeedSequence(master_seed, spawn_key=(g,e,t))))`. Every cell has
500 distinct trial streams; every vertex gets one Laplace draw from its trial's
stream. Reordering the config changes the index-to-stream mapping and is a new
experiment. There is no shared-noise coupling across budgets. These streams are
for simulation, not cryptographically secure releases or a proof of independence.

The complete config is copied byte-for-byte. The manifest records command,
Git revision/worktree status, Python/platform/dependency versions, relevant source
hashes, locked-dependency hash, ESCAPE build/source/binary hashes and artifact
hashes. Failed runs receive `status=failed`; partial results are never verified
as complete. Running the pipeline a second time reproduced every estimate and
every non-timing metric exactly. This is replay, not another 37,500 independent
observations. Runtime, timestamp and working-tree provenance naturally differ.

## Saved outputs and metric definitions

Under `experiments/results/three_star_phase04/`:

| File | Content |
|---|---|
| `config.json` | Exact original configuration, graph seeds and master mechanism seed. |
| `graphs/*.edges` | Original generated simple graphs, including isolates via n. |
| `graphs.csv` | n, m, true S3, separately named ESCAPE count, graph hashes/seeds and degree summaries. |
| `trials.csv` | All 37,500 unrounded estimates, graph ID/index, epsilon/index, trial index and mechanism runtime. Stream coordinates plus master seed reproduce each draw. |
| `summary.csv` | 75 graph–epsilon rows containing every metric below. |
| `escape_reference.json` | Actual ESCAPE input, output, stdout/stderr and separately labeled formula/oracle results. `bruteforce_count=null` means it was not run. |
| `manifest.json` | Status, dimensions, environment, source/reference hashes, command and checksums. |

For estimates `X_1,...,X_T`, exact count S and mean `Xbar`, definitions are:

| CSV field | Definition / units |
|---|---|
| `num_vertices`, `num_edges`, `exact_three_stars` | Graph characteristics and exact non-induced truth. |
| `mean_estimate` | `sum(X_i)/T`, count units. |
| `empirical_bias` | `Xbar-S`, signed count units; finite-sample deviation, not established systematic bias. |
| `sample_variance` | `sum((X_i-Xbar)^2)/(T-1)`, count squared, ddof=1. |
| `sample_std` | Square root of sample variance, count units. |
| `mae` | `sum(abs(X_i-S))/T`, count units. |
| `rmse` | `sqrt(sum((X_i-S)^2)/T)`, count units. |
| `relative_bias`, `relative_mae`, `relative_rmse` | Corresponding metric divided by S, dimensionless, only when S>0. |
| `relative_error_defined` | False when S=0; relative fields are **blank/NaN**, never zero or infinity. |
| `trials` | 500 in every cell. No failed/outlier trial is dropped. |
| `negative_trials`, `min_estimate`, `max_estimate` | Diagnostics preserving negative values and tails. |
| `analytic_variance`, `analytic_rmse` | Ideal-noise variance V_G and sqrt(V_G), conditional on the fixed graph and unbiasedness assumption. |
| `analytic_mean_se`, `empirical_mean_se` | `sqrt(V_G/T)` and sample_std/sqrt(T), respectively. These are uncertainty of the mean, not variability of one estimate. |
| `bias_z`, `variance_ratio` | empirical_bias/analytic_mean_se and sample_variance/analytic_variance. |
| `mechanism_seconds_total`, `mechanism_seconds_mean` | Sum/mean of per-trial `perf_counter` wall times around the estimator API only. |

The identity `RMSE² = (T-1)/T * sample_variance + empirical_bias²` is tested.
There is no ambiguous single "relative error" column: the three definitions are
explicit. Zero-truth K3 has five undefined relative-metric rows. The data are
non-private evaluation records; the private result object's schema is untouched.

Timing excludes RNG construction, graph generation, exact/ESCAPE checks and
CSV/plot work. Manifest `pipeline_seconds` includes the run loop, generation,
reference execution, aggregation and I/O, but excludes compilation, initial
configuration/provenance preparation, plotting and replay. Timings are subject
to OS scheduling and concurrent verification load; this is not a performance
benchmark or a measure of distributed communication.

## Plots from saved data

Four figures are saved as PNG and PDF (eight files):

1. `rmse_vs_epsilon`: family panels, one curve per graph, log–log axes.
2. `mean_vs_exact`: panels by epsilon, exact diagonal and mean estimates with
   ±2 **analytic Monte Carlo SE** bars. Symmetric log axes retain zero/negative
   values. Bars are illustrative, not guaranteed confidence intervals for the
   heavy-tailed estimator.
3. `estimate_distributions`: the preselected ba_n60_m2, 500 estimates at each
   budget, 40 bins covering each full range, exact-count reference line.
   Panel axes are independent; no tails are clipped or hidden by quantile limits.
4. `variance_ratio`: empirical/ideal variance by graph and epsilon. Labels give
   actual ratios; color is log2(ratio) centered at agreement, 1.

`plot_manifest.json` hashes input config/CSVs and all figures. Regeneration to a
separate directory produced identical hashes for all eight figure files in this
pinned environment. PDFs omit variable creation/modification dates. Visual
inspection checked titles, units, legends, negative values and full plot ranges.
No image-generation tool or manual alteration was used.

## Actual findings and statistical interpretation

Observed RMSE decreases monotonically across the five budgets on **15/15**
graphs. Example endpoints (epsilon 0.25 → 4):

| Graph | RMSE at 0.25 | RMSE at 4 | Relative RMSE at 4 |
|---|---:|---:|---:|
| star_n5, S=4 | 4318.054 | 2.949 | 0.7372 |
| star_n50, S=18,424 | 21,696.348 | 778.445 | 0.0423 |
| er_n30_p004, S=9 | 13,221.753 | 6.210 | 0.6900 |
| er_n100_p015, S=52,744 | 32,646.086 | 844.365 | 0.0160 |
| ba_n60_m2, S=2,281 | 16,231.582 | 171.004 | 0.0750 |
| sbm_n100, S=34,317 | 29,716.844 | 648.918 | 0.0189 |
| complete_n25, S=50,600 | 26,645.385 | 936.798 | 0.0185 |
| complete_n3, S=0 | 2979.687 | 1.531 | undefined |

Absolute errors can grow with graph size/degree while relative error shrinks
because the signal grows faster. Among these instances, high-count graphs have
much better relative utility than low-count graphs. For example, sparse ER with
S=9 has relative RMSE about 1469 at epsilon 0.25. Unbiasedness alone would not
make such an individual estimate useful. These comparisons vary n, density and
degree distribution together; they are not controlled causal claims about graph
family or a general ranking of models.

All 75 mean deviations have `abs(bias_z)<=2.281724`; three exceed 2 and none
exceed 3. The largest is complete_n10 at epsilon 4: observed mean 832.537279,
truth 840, empirical bias -7.462721 and z=-2.281724. With 75 comparisons, a
handful of two-SE deviations is not evidence of systematic bias. There was no
outcome-based filtering or rerun with changed seeds. No claim of unbiasedness
is established by these observations.

The cubic correction is sensitive to rare large noise values. Sample/ideal
variance ratios span **0.279039–1.681334**. The low endpoint is complete_n3 at
epsilon 1 (835.627973 observed versus 2994.666667 ideal); the high endpoint is
star_n5 at epsilon 1. This is an observed discrepancy needing tail-aware
interpretation, not an excuse to tune the correction. At 500 trials, empirical
RMSE/variance may materially under- or overestimate population accuracy. Exact
quadrature regression tests support the stated ideal variance formula; formal
variance/tail review and any larger precision study remain future work.

To investigate these two extrema, `scripts/analyze_experiments.py` computes
ideal fourth central moments using seven-node Gauss–Laguerre quadrature and
independently checks each local moment by polynomial expansion through order
12. With independent vertex errors, `mu4_G=sum(mu4_v-3V_v²)+3V_G²`. The standard
error of the unbiased sample variance is
`sqrt((mu4_G - (T-3)/(T-1)*V_G²)/T)`. For complete_n3 at epsilon 1 it is
2916.933710, **97.4%** of V_G; its observed variance is -0.740174 such SE below
the ideal. For star_n5 at epsilon 1, relative SE is **71.6%**, and the observed
variance is +0.952049 such SE above the ideal. Thus these discrepancies are
not large relative to their ideal sampling variability. These are explicitly
post-hoc diagnostic selections, not added trials or exact confidence intervals;
the ideal moments and independence assumptions still need mathematical review.
The compact saved analysis is [accuracy_04.json](status/accuracy_04.json).

There are **6,882 negative estimates** among 37,500. They are all saved, counted
and plotted. Removing them would alter the experiment and bias the estimator.
Five relative-metric rows are undefined because truth is zero; none is divided
by an artificial denominator. The ideal variance contains b², b⁴ and b⁶ terms
with b=2/epsilon, explaining why low budgets are especially noisy. These
interpretations concern the specified ideal moment calculation and finite
synthetic runs, not a formal privacy theorem or uniform accuracy guarantee.

## Review and limitations

See [PRIVACY_NOTES.md](PRIVACY_NOTES.md) for every randomness source and budget
allocation, [ALGORITHMS.md](ALGORITHMS.md) for pseudocode/complexity, and the
[review handoff](status/REVIEW_PACKAGE.md) for files and unresolved questions.
The checkpoint records test counts, commands, timings, preserved failures/skips
and artifact audits. Results/plots are deliberately Git-ignored; the config,
runner, tests, documentation and compact evidence summary belong in source
control. No generated experiment files or virtual environment were committed.

This is one realization of each configured random graph, 500 mechanism trials,
float64 arithmetic and a simulation PRNG. It provides no deployment-ready LEDP
protocol, secure sampler, privacy ledger, full finite-precision proof, graph
population inference or large-dataset performance claim. The 4-clique remains
neither designed nor implemented. Further work requires explicit authorization.
