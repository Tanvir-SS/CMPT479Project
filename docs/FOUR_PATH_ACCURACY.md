# Four-path MSE verification and validation infrastructure — Phase 4A

**NON-PRIVATE EVALUATION CODE.** The modules `four_path_accuracy.py` and
`four_path_experiments.py` access actual graphs, exact counts, retained triangles,
seeds and timings. They are not imported by the private release path. The private
P4/triangle/degree/RR/k-CoreD implementations are unchanged and retain
`experimental_unverified` status. This phase verifies ideal moments and establishes
bounded reproducible evaluation, not deployment privacy or comparative utility.

## Exact ideal-mechanism identity

Fix a simple undirected graph G on public vertices. Let x_uv be its edge bit,
t_v=d_v-1, Z_v be independent Laplace(0,2/epsilon_D),
s=Var(Z_v)=8/epsilon_D^2, and X_v=t_v+Z_v. Write W_uv=x_uv+U_uv, where
E[U_uv]=0 and Var(U_uv)=h=exp(epsilon_R)/expm1(epsilon_R)^2. Different unordered
pairs use independent RR coins; copies of the same report do not.

Let H be the ordering O and cap B, and c_uv(H) the number of roots whose genuine
capped outgoing prefixes contain u and v. Set
T_retained(H)=sum c_uv*x_uv, M(H)=T-T_retained(H), and
g_v=sum_{u in N(v)} t_u. The triangle count noise is a sum of n independent
Laplace variables with scale Delta_T(B)/epsilon_C, with zero scale/no draw for
B<=1. Its variance is 2n Delta_T(B)^2/epsilon_C^2.

The implementation creates five separate SeedSequence domains. Neither ordering
nor cap is derived from degree reports or RR: ordering uses its own randomization
and true graph, and cap uses true outgoing lists under that order and its own
randomization. Thus, for fixed G, conditioning on H does not alter the ideal law
of degree noise, RR or count-stage base random draws. This independence is
essential; it would fail for an arbitrary order or cap chosen using the shared
RR table or the released degree reports. Distinct PRNG streams model these
independent ideal draws; their cryptographic independence is not certified.

Expand the error conditional on H:

```text
Phat-P4 = Q(Z) + sum_{u<v} U_uv*(X_u X_v-3c_uv) - 3 sum_v L_v + 3M(H)
Q(Z) = sum_v g_v Z_v + sum_{uv in E} Z_u Z_v.
```

E[Q]=0. Its linear and quadratic parts are uncorrelated by independence and zero
means. Distinct edge quadratic terms are uncorrelated, even for edges sharing
one endpoint. Consequently Var(Q)=s sum g_v^2+s^2 m.

Conditional on Z,H, the RR term has zero mean and variance
`h sum (X_u X_v-3c_uv)^2`. It is therefore uncorrelated with Q(Z). For u!=v,
independent vertex noise gives

```text
E[(X_u X_v-3c_uv)^2 | H]
  = (t_u t_v-3c_uv)^2 + s(t_u^2+t_v^2) + s^2.
```

Count noise has conditional mean zero, independent of the other noise. All
cross terms with the fixed conditional bias 3M vanish. Therefore

```text
MSE(Phat | H) = s sum_v g_v^2 + s^2 m
  + h sum_{u<v} [(t_u t_v-3c_uv(H))^2 + s(t_u^2+t_v^2) + s^2]
  + 18n Delta_T(B)^2/epsilon_C^2
  + 9M(H)^2.
```

Taking E_H verifies the proposed complete MSE identity exactly in the ideal
model. No missing covariance term was found. This is an identity, not an
asymptotic approximation. It does not certify identical moments of finite-precision
NumPy sampling or failure/timing transcripts.

The sensitivity is obtained from the unchanged Phase 2 `triangle_sensitivity`:
zero for B<=1, otherwise `(B-1)*(exp(epsilon_R)+1)/expm1(epsilon_R)`. The fixed-H
add/remove/replacement analysis and full privacy limitations remain in
[TRIANGLE_PROTOCOL.md](TRIANGLE_PROTOCOL.md).

## Conditional variance, bias and signed decomposition

The calculator reports five additive MSE contributions:

1. `degree_noise = s sum g_v^2+s^2 m`.
2. `rr_unadjusted = h sum (t_u^2+s)(t_v^2+s) + 9h sum c_uv^2`.
3. `shared_rr_adjustment = -6h sum c_uv t_u t_v`.
4. `triangle_laplace = 18n Delta_T(B)^2/epsilon_C^2`.
5. `truncation_squared_error = 9M(H)^2`.

The third term is a **signed covariance adjustment**, not a standalone
nonnegative variance. Covariance is subtracted exactly once. The calculator also
reports `rr_compact`, the equivalent nonnegative square-form RR sum used for
numerically stable total MSE; it includes the degree/RR interaction terms.
`degree_product_variance` includes degree noise plus the RR degree-product term.

Conditional bias is 3M(H); conditional variance is the first four contributions.
For random H, unconditional bias is 3E[M] and unconditional variance is
E[conditional variance]+9Var(M). Therefore total MSE contains **9E[M^2]**, not
just 9(E[M])^2. A two-history K4 test with caps 1 and 3 gives mean squared
truncation error 72, squared mean bias 36, and between-history variance 36.
Averaging caps or orderings is not used.

## Accuracy APIs

In `src/private_graphlets/four_path_accuracy.py`:

```python
degree_product_variance(graph: SimpleGraph, budget: FourPathBudget) -> float
closing_edge_multiplicities(graph: SimpleGraph, order: Sequence[int],
                            cap: int) -> dict[tuple[int, int], int]
retained_triangle_count(graph: SimpleGraph, order: Sequence[int], cap: int) -> int
conditional_four_path_mse(graph: SimpleGraph, budget: FourPathBudget,
                          order: Sequence[int], cap: int) -> ConditionalMSE
sample_order_cap(graph: SimpleGraph, budget: FourPathBudget, *, seed: int,
                 beta: float = .05, kcore_config: KCoreConfig | None = None
                 ) -> tuple[tuple[int, ...], int]
summarize_predictions(rows: Sequence[ConditionalMSE]) -> dict
predicted_four_path_mse(graph: SimpleGraph, budget: FourPathBudget, *,
                        seeds: Sequence[int], beta: float = .05,
                        kcore_config: KCoreConfig | None = None) -> dict
```

Multiplicities are a sparse map of Python integers, with absent pairs meaning
zero. They include nonedge closing pairs. Original, retained and missed triangle
counts remain exact integers. ConditionalMSE separates all contributions, bias,
variance and total, with explicit non-private labeling in `to_dict()`.
Numerical results must be finite; extreme analytical parameters raise rather
than silently emit NaN/Infinity. The direct predictor requires at least two
distinct seeds. It samples only ordering/cap, never degree/RR/count noise.

`summarize_predictions` returns Monte Carlo mean MSE, sample standard error,
mean conditional variance, mean bias, squared mean bias, between-history
variance, mean missed triangles, truncation frequency and mean contributions.
This is a prediction estimate over sampled H, not an exact integration of the
full k-CoreD/cap distribution. Its standard error is recorded separately.

## Reproducible bounded experiment framework

`src/private_graphlets/four_path_experiments.py` provides `load_config`,
`experiment_graph`, `experiment_seed`, `prediction_trial`, `full_trial`,
`aggregate`, `run_experiment(config_path, output)` and
`verify_results(output, replay=False)` (replay is keyword-only).
It reuses existing deterministic graph generation, injective coordinate seeds,
SHA-256 hashing and software/source provenance. No existing experiment is changed.

The checked-in config is
`experiments/configs/four_path_phase12_validation.json`:

- Four fixed fixtures: path, cycle, diamond, clique.
- ER(n=8,p=.35), graph-generation seed 120401.
- Explicit allocations D=2, O=.5, R=1, M=1, C=2, total **6.5**.
- Beta=.05; default k-CoreD config.
- Master seed 202611051204.
- 300 full-estimator trials and 300 separate prediction histories per graph.
- Predeclared discrepancy multiplier 3, maximum relative combined SE .25.

These are verification settings, not a recommended budget allocation. Schema
guards bound Phase 4A to 1..10 graphs, n<=30 and 2..500 trials per stream.
Fixture names and IDs are validated before writing outputs. The existing
coordinate seed utility assigns different domains to prediction and full trials;
there is no shared random draw between them. Prediction then spawns ordering/cap
children; full simulation retains the original five-stage stream convention.

```bash
.venv/bin/python scripts/run_four_path_experiments.py run
.venv/bin/python scripts/run_four_path_experiments.py verify --replay
```

Use `--config`/`--output` for run or `--results` for verify. Existing output paths
are refused; failures retain `failure.json` and cannot be verified as complete.
There is no plot or baseline command.

Artifacts under ignored `experiments/results/four_path_phase12_validation/`:

| Artifact | Meaning |
|---|---|
| `config.json` | Exact saved settings and seeds; non-private metadata. |
| `graphs/*.edges` | Original true graphs, including isolates; non-private. |
| `graph_evaluation.json` | Exact n,m,P4,T; non-private. |
| `mechanism_outputs/*.jsonl` | Modeled result/transcript only: privatized messages and public parameters, without seed/exact diagnostic fields. |
| `evaluation_trials.csv` | NON-PRIVATE join of full-run estimates, replay seeds, retained/missed counts and separate timings. |
| `prediction_trials.csv` | NON-PRIVATE realized orders/caps, conditional MSE contributions, seeds and timings. |
| `summary.csv` | NON-PRIVATE empirical/predicted metrics and uncertainty. |
| `manifest.json` | Completion status, artifact hashes, schema separation, source/software/Git provenance and reference-manifest hash. |

The entire study is **non-private synthetic evaluation**; publishing its graphs
and seeds precludes calling the experiment itself a protected-data release.
Mechanism-only files model the allowed release fields, not secure isolation.

Verification checks inventory and file hashes, configuration/seed coordinates,
graph reconstruction, exact counts, summary reconstruction and analytical
predictions. Replay additionally reproduces the complete result/transcript and
sampled prediction order/cap; runtime equality is not expected. Manifests record
source hashes, including the driver, and dependency versions. Hashes detect
accidental alteration, not an attacker who rewrites both data and manifest.

## Statistical methodology and observed pilot

For N independent full-trial errors e_i, empirical MSE is mean(e_i^2), and
SE_MSE is sample_std(e_i^2)/sqrt(N). Empirical variance uses ddof=1; thus empirical
MSE equals bias^2+(N-1)/N times that sample variance, not bias^2+sample variance.
Prediction SE is sample_std(conditional MSE)/sqrt(N_prediction). Independent
streams justify combining the two SEs in quadrature for discrepancy diagnostics.

A discrepancy is flagged when its magnitude exceeds three combined SEs. Even
within that threshold, combined SE/predicted MSE above .25 is labeled
`inconclusive_precision`. These are predeclared diagnostic thresholds, not
rigorous finite-sample confidence guarantees for heavy-tailed squared errors.
No seeds, budgets, sample sizes or tolerances were changed after observing data.
No automatic study expansion was performed.

Actual study, 2026-11-05: 1500 full trials plus 1500 prediction trials; replay
verified all of them. Values below are rounded for presentation; CSVs preserve
17-digit float output.

| Graph | P4 | T | Empirical MSE | SE(MSE) | Predicted MSE | Prediction SE | Relative discrepancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| path | 1 | 0 | 472.341270 | 47.925826 | 395.334329 | .239592 | +19.4789% |
| cycle | 4 | 0 | 501.130803 | 66.173978 | 442.981504 | .500192 | +13.1268% |
| diamond | 6 | 2 | 558.293463 | 47.383580 | 594.953528 | .660509 | -6.1618% |
| clique | 12 | 4 | 859.143392 | 83.440740 | 809.351201 | 0 | +6.1521% |
| er8 | 38 | 3 | 7817.094418 | 724.529537 | 7488.715618 | 1.021146 | +4.3850% |

| Graph | Mean estimate | Bias | Sample variance | RMSE | Full mechanism seconds |
|---|---:|---:|---:|---:|---:|
| path | 1.646122 | .646122 | 473.502138 | 21.733414 | .032211 |
| cycle | 5.327699 | 1.327699 | 501.038145 | 22.385951 | .031906 |
| diamond | 2.539390 | -3.460610 | 548.144792 | 23.628234 | .032179 |
| clique | 13.293779 | 1.293779 | 860.337320 | 29.311148 | .032162 |
| er8 | 37.787723 | -.212277 | 7843.193335 | 88.414334 | .049639 |

All five received `no_discrepancy_detected` under the fixed rule. Standard errors
are substantial; this is limited consistency evidence, not precise empirical
confirmation or validation over all graphs. In both streams, every graph had
mean missed triangles **0** and truncation frequency **0**. The pilot therefore
does not empirically exercise nonzero truncation or variation in missed counts;
those are covered by deterministic capped and mixed-history tests. It does not
establish that truncation probability is zero.

Measured pipeline time was 0.447785875 seconds on this environment. CSVs separately
record full-mechanism time, full diagnostic time, prediction history-sampling
time and conditional-analysis time. These local process timings are neither
network measurements nor comparative performance claims.

## Worst-case order and graph-dependent qualifications

For fixed positive allocations independent of n, s,h and the RR range width
are constants. For n>=4, |t_v|<=n, |g_v|<=n^2, m=O(n^2), c_uv<=n-2,
B<=n-1 and M<=T<=choose(n,3). Uniformly over H:

- Degree-noise terms: O(n^5)+O(n^2).
- Compact RR term: O(n^2*n^4)=O(n^6); interaction terms are at most O(n^4).
- Local triangle Laplace term: O(nB^2)<=O(n^3).
- Squared missed-triangle term: O(T^2)<=O(n^6).

Averaging H preserves these bounds. Thus **ideal MSE=O(n^6), RMSE=O(n^3)**.
This mathematical asymptotic statement extends the specified ideal mechanism;
the actual simulator enforces n<=1000 and is not an asymptotic experiment.
It requires neither a proved k-CoreD out-degree theorem nor a favorable cap event.

The bound is loose for many sparse inputs but cannot be uniformly improved just
by better orientation. For K_n, t_u*t_v=(n-2)^2 and c_uv<=n-2, so for n>5 every
square term is at least `[(n-2)(n-5)]^2`. With fixed h>0 and choose(n,2) pairs,
the RR term alone is Omega(n^6), uniformly over H. This establishes matching
worst-case order in that ideal dense family, not numerical behavior at arbitrary
n or an empirical theorem.

For a graph-dependent bound let D_max=D and dbar=max(1,D), and suppose B<=K on
all histories being considered. Since c_uv<=D and T<=mD/3,

```text
MSE = O(n D^2 dbar^2 + m
        + n^2(dbar^4 + D^2 + dbar^2 + 1)
        + n K^2 + m^2 D^2)
```

for fixed allocations. This follows by `(a-b)^2<=2a^2+2b^2` and the preceding
bounds; it is not claimed optimal. With bounded D and K it is O(n^2). Such a
uniform small-cap condition is not assumed for the private random cap: for an
unconditional claim retain E[B^2] or the public n-1 bound. Sparsity alone does
not imply small maximum degree or a particular ordering/cap distribution.
Matching another estimator's asymptotic order says nothing about its constants,
finite-graph accuracy, truncation, or practical superiority. No baseline was run.

## Evaluation complexity and memory

This evaluation is outside the private mechanism's computational/accounting path.
Let q_v be outgoing degree and s_v=min(q_v,B).

- Exact triangle and P4 evaluation use existing adjacency intersections:
  O(n+m+sum_{uv in E}min(d_u,d_v)), worst O(n^3). P4 adds O(n+m).
- Multiplicities scan/sort actual outgoing neighbors and enumerate closing pairs:
  O(n+m+sum q_v log(1+q_v)+sum choose(s_v,2)); at most O(n+m log(1+D)+nB^2).
  Sparse map size is at most O(n^2), with O(D) selection workspace.
- One conditional MSE additionally computes degree terms in O(n+m+n^2),
  the compact pair sum in O(n^2), and exact triangles. Counts are not cached
  across histories in this implementation; repeated exact evaluation is included.
- A prediction trial adds existing private ordering O(r(n+m)+n log n) and
  O(n+m) cap work, but generates no degree/RR/count randomness.
- A full trial runs the unchanged private estimator with its documented
  O(n+r(n+m)+n log n+n^2+m log(1+D)+nB^2) computational bound, then separately
  times conditional evaluation diagnostics.
- The runner retains O(F+P) scalar trial rows, plus O(Pn) serialized orders,
  for F full and P prediction trials. Mechanism JSONL is streamed. One active
  full run uses O(n+m+n^2+nr) memory. Verification currently loads one graph's
  JSONL records, requiring O(F_graph*(n^2+nr)) memory in addition to CSV tables.
- Recording/hashing costs are linear in artifact bytes; replay repeats full
  trials and prediction histories plus analytical checks. Metrics are linear
  in trial rows after grouping. Saved transcripts include O(n^2+nr) entries per
  full trial; floating-point formatting/large integer costs are abstracted here.

The private mechanism's communication caveat remains: O(n^2) RR upload does not
include delivery of the full matrix to n clients, potentially O(n^3) bits.
Physical distribution and private-access protection are not implemented.

## Limits and next phase

No demonstrated defect required changing a private mechanism. Ideal algebra,
deterministic finite checks and empirical diagnostics have distinct evidentiary
roles. Independent mathematical/privacy review, finite-precision distributions,
error/timing/access transcripts, cryptographic randomness and real client
isolation remain unresolved. The pilot has only five small graphs and 300 draws
per stream; it neither validates worst-case scaling empirically nor justifies
utility superiority. A separately authorized Phase 4B study is technically
supported, but should predeclare precision targets and include truncation regimes.
No Phase 4B run, baseline, sweep, plot, commit or push was performed.
