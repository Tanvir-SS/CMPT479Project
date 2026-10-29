# Independent mathematical review package — phase 04

**2026-10-28; completed and stopped.** This handoff concerns only non-induced
3-star counting. No formal DP proof is claimed. No 4-clique design or
implementation has begun. Detailed commands/evidence are in
[checkpoint 04](checkpoints/04_experiments_and_review.md).

## 1. Implemented scope

Validated simple undirected graphs with isolates; an integer degree-formula
counter and independent small-graph enumerator; the specified Laplace-degree
simulation; an ESCAPE exact-reference adapter; a seeded 15-graph experiment
pipeline with raw/aggregate CSVs, replay, plots and statistical diagnostics.

## 2. Mechanism files and functions

- [graph.py](../../src/private_graphlets/graph.py): `SimpleGraph`,
  `parse_edge_list`, `load_edge_list`. Fixed public labels, deduplication, loop
  rejection and isolates; graph contents are sensitive input in the intended model.
- [noise.py](../../src/private_graphlets/noise.py): `validate_epsilon`,
  `laplace_scale`, `make_rng`, `sample_degree_noise`.
- [three_star.py](../../src/private_graphlets/three_star.py):
  `corrected_local_stars`, `estimate_three_stars`, `PrivateThreeStarResult.to_dict`.
- [cli.py](../../src/private_graphlets/cli.py): separate private simulation and
  non-private exact commands. No degree, exact truth, edge count, seed or RNG
  state is attached to private results.

The graph, noise and estimator sources are byte-identical to the phase-03
starting commit. This is a centralized simulation of a local-report protocol,
not secure distributed execution. Reports exist transiently in process memory.

## 3. Mathematical estimator

For fixed graph G, `S3(G)=sum_v choose(d(v),3)`, allowing extra leaf edges.
For `epsilon>0`, `b=2/epsilon`, independently `Z_v~Laplace(0,b)`, `Y_v=d(v)+Z_v`:

```text
S_hat = sum_v [Y_v(Y_v-1)(Y_v-2)/6 - b^2(Y_v-1)].
```

Each vertex uses only its own degree and public parameters. Conceptually it
sends Y_v to the coordinator; the coordinator applies the polynomial and sums.
The API exposes only the aggregate and public metadata. No rounding, clipping,
nonnegativity projection or tuning occurs, including for isolated vertices.

Ideal moment rationale: the uncorrected cubic's expectation is
`choose(d,3)+b²(d-1)`; the subtracted term has expectation `b²(d-1)`.
With `t=d-1`, `a=(3t²-1)/6`, ideal local variance is
`2a²b²+(7t²-2/3)b⁴+14b⁶`; independent vertices give the sum of these variances.
These are derivations for review, not a completed executable privacy/accuracy proof.

## 4. All budget allocations

Neighbors differ by one undirected edge on a fixed public vertex set. Each
endpoint's degree sensitivity is 1; each report is intended to spend epsilon/2.
Two affected reports compose to epsilon; degree-vector L1 sensitivity is 2.
Polynomial correction/summation of those same reports is postprocessing.

For total budgets 0.25/0.5/1/2/4, endpoint budgets are
0.125/0.25/0.5/1/2 and noise scales 8/4/2/1/0.5. No other private mechanism
or budget split is used. A full 500-trial grid on the same protected graph
would incur 3875 under basic sequential accounting; **the published synthetic
experiments are not DP releases**, and include exact truth and public seeds.
The ideal intended delta is zero; the NumPy executable has no verified DP guarantee.

## 5. Actual verification

- Full WSL setup/test command: **256 passed in 15.15s**, no failures/skips.
- Explicit ESCAPE suite: **34 passed, 222 deselected in 10.04s**.
- Earlier 24 small reference cases still pass; **15/15 experiment graphs** also
  agree with actual ESCAPE. Brute force is additionally used for n<=12.
- Every one of **37,500 estimates replays exactly**. A complete second run
  reproduces all non-timing CSV fields. Eight PNG/PDF figures regenerate with
  identical hashes. Timings are deliberately excluded from deterministic replay.
- Tests cover noise moments/independence diagnostics, unchanged correction,
  negative outputs, metrics, zero truth, quadrature, graph validity, output
  corruption, schema boundaries and process failures. They cannot prove DP.

## 6. Experimental findings

15 fixed synthetic graphs, five families, n=3–100; five budgets, 500 trials per
cell, 75 cells. Observed RMSE decreases with epsilon on all 15 graphs. Relative
accuracy is poor for low counts: at epsilon 4, relative RMSE is 0.7372 for the
five-vertex star and 0.6900 for sparse 30-vertex ER, versus 0.0160 for the
100-vertex ER instance. These are instance comparisons, not causal family rankings.

Maximum absolute mean deviation is **2.281724 analytic SE**; three of 75 exceed
2 SE, none exceed 3. Variance ratios range **0.279039–1.681334**. Fourth-moment
diagnostics put the two extrema within one sample-variance SE of their ideal
values, highlighting unstable tail estimates at 500 trials. All **6,882 negative
estimates** are retained. Five zero-truth cells have undefined relative metrics.
See [EXPERIMENTS.md](../EXPERIMENTS.md) and [accuracy_04.json](accuracy_04.json).

## 7. Results and figures to transfer separately

Paths are relative to the project root:

- `experiments/results/three_star_phase04/{trials,summary,graphs}.csv`
- The same directory's `config.json`, `manifest.json`, `escape_reference.json`
  and `graphs/*.edges`.
- `plots/three_star_phase04/{rmse_vs_epsilon,mean_vs_exact,estimate_distributions,variance_ratio}.{png,pdf}`
  and `plot_manifest.json`.

These generated files are intentionally ignored by Git. A clone alone does not
include them; rerun the documented pipeline or send the directories with this
review package. `docs/status/accuracy_04.json` is the small intentional evidence
summary, not a substitute for the raw data.

## 8. Known bugs and limitations

No unresolved implementation/test failure was observed in phase 04. This does
not certify absence of bugs. ESCAPE retains 160 upstream compiler warnings,
weak raw-input checks, numeric limits and allocations; our adapter validates
inputs, uses process isolation, caps n at 1000 and checks counts below 2**53.
NumPy randomness is not cryptographically secure. Float64/tail discretization,
numeric errors, runtime leakage and release composition are unproved. There is
no privacy ledger, secure transport or client isolation. Five hundred trials
and three instances per family do not establish uniform utility. Runtime is a
local wall-time observation under shared verification load, not a benchmark.

## 9. Questions for independent review

1. Prove the ideal full-transcript edge-DP inequality with both endpoint reports,
   correct adjacency, public assumptions and independence; distinguish the
   simulation's aggregate API from its actual process-memory trust boundary.
2. Check the unbiasedness, local/graph variance and fourth central moment
   calculations; obtain tail-aware precision/accuracy bounds for the cubic.
3. Analyze finite-precision sampling, cancellation, error transcripts and secure
   implementation requirements. No empirical comparison establishes these.
4. Review repeated releases, graph-dependent preprocessing, side channels and
   any future output transformation separately. Confirm no current correction
   or negative-output handling needs modification before approving theory.

## 10. Pending milestones and files to review

The Milestone 3 rubric was not supplied. Pending work, subject to that rubric
and new authorization: independent privacy/accuracy review, resolution of the
questions above, and agreement on the next research scope. Other pattern
algorithms, including 4-clique, remain unstarted. The final project still needs
the approved pattern coverage, reviewed theoretical claims, representative
dataset/precision studies, and a final report/presentation with a reproducible
artifact bundle. None is represented as completed by these synthetic experiments.

Give the independent assistant these **source/configuration documents**:

- `AGENTS.md`, `README.md`, `pyproject.toml`, `requirements.lock`,
  `requirements-constraints.txt`, `.python-version` and `MANIFEST.in`.
- All `src/private_graphlets/*.py`, particularly `graph.py`, `noise.py`,
  `three_star.py`, `exact.py`, `escape.py`, `experiments.py`, `experiment_plots.py`.
- All `tests/*.py`; `scripts/{setup.sh,run_experiments.py,analyze_experiments.py,validate_escape.py,reference_fingerprints.py}`.
- `experiments/configs/three_star_phase04.json`, `data/fixtures/`,
  `docs/{ALGORITHMS,PRIVACY_NOTES,EXPERIMENTS,ESCAPE_VALIDATION,SOURCE_REVIEW}.md`
  and `docs/references.json`.
- `docs/status/{STATUS.md,REVIEW_PACKAGE.md,accuracy_04.json}` and all numbered
  checkpoints. Include the generated directories listed above separately.

Reference source is not vendored; README describes obtaining the exact ESCAPE
commit. Reviewers can inspect saved raw output without compiling, and can
independently reproduce it by following those build instructions. **STOP: no
additional phase or 4-clique design is authorized by this handoff.**
