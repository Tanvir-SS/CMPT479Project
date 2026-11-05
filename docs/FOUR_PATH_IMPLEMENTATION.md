# Complete private 4-path simulator — P4 Phase 3

Implementation: `src/private_graphlets/four_path.py`. Status:
**experimental_unverified**, including seeded and unseeded execution. This
centralized research simulator models local releases; it does not implement
secure client isolation, physical message distribution or certified LEDP.

## APIs and explicit budgets

```python
FourPathBudget(degree: float, ordering: float, rr: float, cap: float, count: float)
FourPathStreams(degree: np.random.Generator, ordering: np.random.Generator,
                cap: np.random.Generator, rr: np.random.Generator,
                count: np.random.Generator)
four_path_streams(seed: int | None = None) -> FourPathStreams
local_degree_report(neighbors: frozenset[int], epsilon_degree: float,
                    rng: np.random.Generator) -> float
degree_product_estimate(noisy_degrees: Sequence[float], weights: np.ndarray) -> float

simulate_four_paths_private(
    graph: SimpleGraph, *, budget: FourPathBudget, seed: int | None = None,
    streams: FourPathStreams | None = None, beta: float = 0.05,
    kcore_config: KCoreConfig | None = None,
) -> FourPathRun
estimate_four_paths_private(
    graph: SimpleGraph, *, budget: FourPathBudget, seed: int | None = None,
    streams: FourPathStreams | None = None, beta: float = 0.05,
    kcore_config: KCoreConfig | None = None,
) -> FourPathResult
```

`FourPathRun` contains `result: FourPathResult` and
`transcript: FourPathTranscript`. The convenience estimator returns only the
result. No CLI, baseline or experiment runner is added in this phase.

The budget names correspond to D=degree, O=ordering, R=RR, M=cap, C=count.
Every allocation is explicit, positive and finite. `budget.total` is the finite
sum D+O+R+M+C. Degree scale must be representable; O<=1 and R<=30 preserve the
existing domains. Existing k-CoreD/geometric and cap/count numerical guards still
apply at execution. No allocation is redistributed or silently reduced, and the
four-stage `TriangleBudget` is not used as a substitute for this five-stage budget.

## Exact identity and implemented estimator

The graph is simple, undirected, validated by `SimpleGraph`, with fixed public
IDs 0..n-1, including isolates. The original target is the number of non-induced
P4 copies on four distinct vertices. Extra host edges are allowed; reversal does
not produce another copy. ESCAPE calls this a three-edge `3-path`.

```text
P4(G) = sum_{uv in E, u<v} (d_u-1)(d_v-1) - 3*T(G)
Ahat = sum_{0<=u<v<n} W_uv*(dhat_u-1)*(dhat_v-1)
Phat = Ahat - 3*That_EO
```

The exact middle-edge identity is implemented separately in `four_path_exact.py`
and checked against independent enumeration and actual ESCAPE in Phase 1.
Neither exact counter nor ESCAPE is imported by the private implementation.

Execution:

1. Validate graph (n<=1000), explicit budget, beta and stream options.
2. Each simulated client sends one `local_degree_report` on the degree stream.
3. Run the unchanged `kcore_order` on the ordering stream.
4. Use its `(private_level, public_ID)` total order for all following orientation.
5. Run unchanged `local_cap_report` and `cap_from_reports` on the cap stream.
6. Call `sample_rr_upper` exactly once; construct one immutable `rr_matrix`.
7. Compute `degree_product_estimate` from noisy degrees and that matrix only.
8. Pass the identical matrix object/order/cap to `estimate_triangles_from_rr`.
9. Sum `Ahat - 3*That_EO` with no clipping, rounding or bias correction.

The standalone triangle entry points are never called. They would repeat prior
stages. There is no data-dependent bypass using exact graph counts, even for
small graphs; the empty graph naturally aggregates empty reports to zero.

## Degree mechanism and all-pairs postprocessing

Each client computes its own degree from its incident frozenset and adds one
sample using `sample_degree_noise(epsilon_degree, size=(), rng=degree_stream)`.
The raw degree remains local to that function. Only its float noisy report is
returned to the coordinator. Reports are neither clipped nor rounded, even for
isolates, low-degree vertices or negative values. They are not derived from RR,
k-CoreD thresholds, or outgoing-cap reports.

Under undirected edge add/remove adjacency, two endpoint degrees change by one;
the degree-vector L1 sensitivity is 2. Independent ideal Laplace draws with
scale 2/D therefore give the intended full-vector allocation D. This accounts
for both endpoint reports, not D per endpoint.

`degree_product_estimate` has no graph parameter and no adjacency access. It
visits every u<v, including false RR reports and genuine nonedges, and does not
subtract triangles. It validates a one-dimensional finite real degree sequence
and a finite immutable symmetric float64 matrix of matching dimensions with a
zero diagonal. It uses streamed Python-float products and `math.fsum`; finite
checks reject overflow. This postprocessor checks numerical structure, not the
privacy provenance of an arbitrary caller's table. The full driver supplies
canonical weights and the triangle component additionally verifies their values
against R. No weight matrix copy is substituted between components.

## Shared RR, ordering and cap

The existing lower-public-ID pair ownership is independent of private order.
With eta=R, a=1/expm1(eta), M=a+1, the debiased weights are -a and M and have
ideal expectation x_uv, with variance h=a*M. Only one bit is generated per
unordered pair and mirrored. The same report can enter both Ahat and That;
this is reuse of a charged release, not an additional RR query.

k-CoreD supplies genuine private levels; equal levels use public IDs. Both the
cap and triangle selection use the same rank. The cap is postprocessing of noisy
outgoing-degree reports, with scale 1/M_budget (here M_budget denotes the cap
allocation, not positive RR weight M), plus log(n/beta)/M_budget margin, ceiling,
and public [0,n-1] bounds (zero for empty graphs). Beta is a utility parameter,
not a privacy delta. Never substitute an exact maximum or increase B after
inspecting selected lists.

The unchanged Phase 2 component forms each genuine outgoing prefix S_v and
sums the closing RR weights over its unordered pairs. Its fixed-transcript
sensitivity is zero for B<=1, otherwise `(B-1)*(M+a)`. It adds independent local
Laplace noise of scale `triangle_sensitivity(B,R)/C` before aggregation. All
clients participate for B>=2, even zero-score clients. See
[TRIANGLE_PROTOCOL.md](TRIANGLE_PROTOCOL.md) for the insertion/deletion/replacement
argument, provenance contract and numerical restrictions.

## Accounting and transcript boundary

The intended ideal adaptive composition is D+O+R+M_budget+C. Degree-product
calculation is postprocessing of degree and RR releases and has no additional
budget. Reusing RR in the triangle score does not recharge R, but accessing raw
local incident lists requires the separate C protection. The conditional count
argument fixes the entire previous transcript; it does not compare scores after
recomputing different orders/caps on neighboring graphs. Both endpoints are
accounted for in D and O; fixed-order cap/count affect only the earlier endpoint.

`FourPathResult` fields:

```text
estimate, degree_product_estimate, triangle_estimate, num_vertices,
released_cap, budget, degree_noise_scale, triangle_noise_scale, beta
```

`epsilon_total` is a property. `to_dict()` adds the total, schema/mechanism,
`target=original_noninduced_P4`, `truncation_bias_possible=True`, non-induced
unlabeled semantics, `simulation_only=True`, and
`privacy_status=experimental_unverified`. Publishing both components is covered
by the modeled transcript; this is not an aggregate-only privacy argument.

`FourPathTranscript` fields:

```text
noisy_degrees, ordering, order, cap_reports, cap, rr_upper,
local_triangle_reports
```

The nested ordering is the existing noised threshold/promotion transcript. No
raw degree vector, adjacency, genuine outgoing lists, unnoised local scores,
exact count, sampled noise, seed or RNG state appears in either structure.
Local functions may access sensitive data inside the simulation. Exact P4/T,
retained T and coefficient counts used below exist only in test-only non-private
evaluation, never in result metadata.

A complete independently reviewed adaptive transcript proof is still required.
Budget objects and tests do not prove privacy of executable floating-point
mechanisms, errors, timing, memory or transport.

## Randomness

`four_path_streams` creates five `SeedSequence(seed).spawn(5)` children in stable
order degree, ordering, cap, RR, count. It does not change the existing four-stream
clique/triangle APIs. A seed and supplied streams are mutually exclusive. Aliased
objects/shared bit generators are rejected. Different generator objects with
identical or correlated states cannot be detected reliably; their independence
is a caller obligation. Each stage advances only its own stream. Seeds are
research metadata and are not released. Unseeded NumPy is also simulation-only.

## Mean and truncation bias

Write t_v=d_v-1 and X_v=dhat_v-1=t_v+Z_v. For u!=v, independent zero-mean degree
noise gives E[X_u X_v]=t_u t_v. Independent RR gives E[W_uv]=x_uv, hence

```text
E[Ahat] = sum_{uv in E} t_u*t_v.
```

For fixed G,O,B, let c_uv be the number of roots whose retained outgoing sets
contain u and v. Then the triangle score is sum c_uv W_uv and its ideal mean is
`T_retained(O,B)=sum c_uv*x_uv`. Fresh count noise has zero mean. Since degree
and RR randomness are independent of O/B in this implementation,

```text
E[Phat | O,B] = P4(G) + 3*(T(G)-T_retained(O,B))
E[Phat] = P4(G) + 3*(T(G)-E[T_retained])
```

The original P4 count remains the scientific target. The estimate may have
positive truncation bias. For K4 under a fixed order, B=2 retains 2 rather than
4 triangles, yielding expected Phat=18 instead of P4=12. An uncapped order
retains every triangle, yielding the ideal unbiased estimator. No correction
for missed triangles is implemented. Noise can still produce negative samples.

## Preliminary second-moment derivation

These formulas concern ideal arithmetic, independent continuous Laplace draws
and independent one-owner RR coins, on a fixed graph. They do not establish a
worst-case O(n^3) RMSE theorem or certify sampler accuracy.

Let s=Var(Z_v)=8/D^2, h=Var(W_uv)=exp(R)/(exp(R)-1)^2, and
`g_v=sum_{u in N(v)} t_u`. Conditioning on the degree reports, RR independence
across unordered pairs gives

```text
Var(Ahat | X) = h * sum_{u<v} X_u^2*X_v^2.
```

The conditional mean is `sum_{uv in E} X_u X_v`. Its centered expansion has
linear part `sum_v g_v Z_v` and quadratic part `sum_{uv in E} Z_u Z_v`.
They are uncorrelated by zero means and independent vertex draws. Distinct edge
quadratic terms are uncorrelated, even when they share one endpoint. Thus

```text
Var(Ahat) = s*sum_v g_v^2 + s^2*m
          + h*sum_{u<v} (t_u^2+s)*(t_v^2+s).
```

For fixed O/B, c_uv is deterministic, degree noise is independent of RR, and
count noise is independent of both. Distinct pair RR noises have covariance
zero; the shared pair contributes h. Therefore

```text
Cov(Ahat,That_EO | O,B) = h*sum_{u<v} c_uv*t_u*t_v
Var(That_EO | O,B) = h*sum_{u<v} c_uv^2 + 2*n*scale(B)^2
Var(Phat | O,B) = Var(Ahat) + 9*Var(That_EO | O,B)
                 - 6*Cov(Ahat,That_EO | O,B).
```

The cap/order vary in the full private simulation. One cannot simply substitute
a fixed-order conditional variance as its unconditional MSE. Total variance
also accounts for variation of retained T and cap-dependent scales; MSE adds
the squared truncation bias. In particular, conditional means of Ahat are
constant in O/B here, while conditional means of That are T_retained.
Shared RR means the two component estimates must not be treated as independent.

Tests use all 64 RR assignments and 16 degree moment nodes on four-vertex
fixtures. A product rule with Z_v=+/-sqrt(s), each weight 1/2, matches Laplace
moments through degree two in each variable. That suffices for A, A^2 and A*That;
it is deterministic integration of these moments, not a replacement Laplace
sampler. Independent count-noise variance is then added analytically. Tests
check mean, variance, covariance and full-estimator bias for B=1,2,3. A separate
5000-trial seeded degree-product mean check uses six analytic standard errors.
No full Phase 4 study or parameter tuning is performed.

## Computational cost, memory and communication

Let r be executed k-CoreD rounds and q_v the outgoing degree. For the actual
implementation with validated frozenset adjacency:

| Stage | Computational cost |
|---|---|
| Degree | O(n) constant-time set lengths and scalar noise draws; list-scanning clients would instead sum local degrees, O(n+m). |
| Ordering | O(r(n+m)+n) under constant-cost noise/arithmetic; O(n log n) for final sorting. |
| Cap | O(n+m) local scans, draws and aggregation. |
| RR | O(n^2) pair sampling and matrix construction. |
| Degree-product | O(n^2) validation and all-pairs summation; O(n) centered degrees. |
| Triangle validation | O(n^2) dense table checks. |
| Triangle selection | O(n+m+sum q_v log(1+q_v)), bounded by O(n+m log(1+D_max)). |
| Triangle score/noise | O(nB^2+n), using all unordered pairs in retained lists. |
| Aggregation | O(n) triangle reports plus constant-size final combination. |

Total expected computational work is
`O(n + r(n+m) + n log n + n^2 + m log(1+D_max) + nB^2)`.
The r bound is the existing public nominal round bound and released thresholds;
no low-out-degree performance guarantee is assumed. These operation counts
abstract numeric bit costs and expected hash membership, and are not measured
network timings. B<=1 skips local score/noise work but not earlier stages/table
validation.

Memory including graph and modeled transcript is `O(n+m+n^2+nr)`; dense matrix
validation can also allocate O(n^2) temporaries. Local neighbor sorting uses
O(D_max) temporary storage. Raw path quadruples are not enumerated.

Communication is separate:

- RR upload: n(n-1)/2 owned bits to the coordinator, O(n^2).
- Degree, cap and local triangle stages: each n scalar reports.
- Ordering: threshold reports and O(nr) promotion bits in this model, plus
  coordinator dissemination of feedback/order.
- Sending the complete RR table separately to n clients can require O(n^3)
  delivered bits. Requesting only genuine selected entries can reveal private
  neighbor-selection information unless a separate protected access protocol
  is specified.

This process shares one in-memory object; it implements no physical transport,
secure broadcast or oblivious/private table lookup. Consequently no O(n^2)
end-to-end communication claim is made. Fixed-width packet/encoding choices,
ordering feedback costs and security overhead need a deployment design.

## Limitations and readiness

All outputs remain `experimental_unverified`. Full adaptive LEDP, finite/discrete
PRNG effects, numerical/error transcripts, timing/access leakage, malicious
participants, actual client isolation and independent accuracy/privacy review
remain unresolved. Numerical failures raise; they never invoke an unprotected
exact answer. Existing k-CoreD numeric/round limits, RR<=30, dense n<=1000 and
finite-scale guards remain. The simulator may be inefficient on dense inputs.

Focused correctness/moment tests support engineering readiness for a separately
authorized Phase 4 evaluation, not empirical utility superiority or a universal
RMSE theorem. No 2025 baseline, full study, plot generation or new pattern was
implemented. Exact commands and outcomes are recorded in
[checkpoint 11](status/checkpoints/11_private_four_path_implementation.md).
