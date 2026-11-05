# Modified EdgeOrientDelta triangle protocol — P4 Phase 2

Implemented in `src/private_graphlets/triangle.py`. This is an
**experimental_unverified research simulator**, not a certified executable LEDP
mechanism. It implements only the triangle component, not the complete P4
estimator or its degree-product stage. Existing mechanisms and references are
unchanged. Exact ground truth remains in `triangle_exact.py` and test-only code.

## Interfaces and signatures

All graph inputs are existing validated `SimpleGraph` objects on the fixed public
vertex set `0..n-1`. The dense protocol supports n<=1000. Every stage preserves
isolates. The empty graph uses cap zero; other caps lie in [0,n-1].

```python
TriangleBudget(ordering: float, cap: float, rr: float, count: float)
triangle_sensitivity(cap: int, epsilon_rr: float) -> float
triangle_local_score(vertex: int, neighbors: frozenset[int], rank: Sequence[int],
                     cap: int, weights: np.ndarray) -> float
triangle_local_report(vertex: int, neighbors: frozenset[int], rank: Sequence[int],
                      cap: int, weights: np.ndarray, epsilon_rr: float,
                      epsilon_count: float, rng: np.random.Generator) -> float
aggregate_triangle_reports(reports: Sequence[float]) -> float

# Path A: no earlier stage is run; only count noise is newly charged.
estimate_triangles_from_rr(graph: SimpleGraph, order: Sequence[int], cap: int,
                           weights: np.ndarray, *, epsilon_rr: float,
                           epsilon_count: float, rng: np.random.Generator
                           ) -> TriangleComponentRun

triangle_streams(seed: int | None = None) -> TriangleStreams

# Path B: complete standalone simulation, with explicit allocations.
simulate_triangles_private(graph: SimpleGraph, *, budget: TriangleBudget,
                           seed: int | None = None,
                           streams: TriangleStreams | None = None,
                           beta: float = 0.05,
                           kcore_config: KCoreConfig | None = None) -> TriangleRun
estimate_triangles_private(graph: SimpleGraph, *, budget: TriangleBudget,
                           seed: int | None = None,
                           streams: TriangleStreams | None = None,
                           beta: float = 0.05,
                           kcore_config: KCoreConfig | None = None) -> TriangleResult
```

`estimate_triangles_private` is the aggregate-only convenience form of Path B.
The local score/report functions are low-level kernels, like the existing clique
kernels: they require a validated public context and one validated incident list.
They are not separate full input-validation/security boundaries. In particular,
the raw local score function is sensitive internal computation, not a release API.
Use Path A for validation and calibration of an externally supplied context.

Path A checks order permutation, cap range, epsilon domains, finite scale and an
immutable float64 n-by-n RR matrix: symmetric, zero diagonal, and off-diagonal
entries exactly the two weights computed by `rr_parameters(epsilon_rr)`.
The canonical compatible table is `rr_matrix(n, rr_upper, epsilon_rr)`.
Approximate/rounded or arbitrary weights are rejected. The check establishes
shape/range, not how the bits or order were produced. The caller must supply
previously released, correctly accounted transcripts. A private-data-dependent
unprotected order or cap is not made private by calling Path A. Read-only NumPy
flags are an API contract, not protection against a malicious alias or process.

## Mechanism and reuse

Path B calls the existing `kcore_order` with the ordering allocation. It retains
its full threshold/promotion transcript and uses its deterministic ascending
`(private_level, public_ID)` order. There is no random tie breaking or fallback
to exact degree/degeneracy order. All k-CoreD numerical and parameter guards remain.

Under this same rank array, `four_clique.local_cap_report` produces

```text
Q_v = |N+(v)| + Laplace(0, 1/epsilon_cap)
B = min(n-1, max(0, ceil(max_v Q_v + log(n/beta)/epsilon_cap)))
```

`cap_from_reports` handles the empty graph separately. Beta is a utility tail
parameter, not a privacy delta. Always enforce B, even if the noisy cap
underestimates the maximum outgoing degree. Do not replace B with exact degrees.

The lower public-ID endpoint reports each unordered pair once, including
nonedges, using `sample_rr_upper`. Mirroring by `rr_matrix` copies that same bit;
it does not draw another report. Let eta=epsilon_rr, a=1/expm1(eta), M=a+1.
The RR weight is -a for false and M for true; R=M+a is its range width.
RR remains restricted to eta<=30 and finite parameters.

For each client v, `select_outgoing` sorts genuine higher-ranked neighbors by
that same rank and retains its first B. Let this prefix be S_v. The local score
is `F_v = sum_{unordered {j,k} subset S_v} W_jk`. Only closing edges use RR;
the two edges incident to the root use genuine client adjacency. Each unordered
pair is visited once. Additional edges among outgoing neighbors simply supply
additional closing-edge terms.

For B>=2 each client, including zero-score clients and isolates, returns
`F_v + Laplace(0, Delta_T(B)/epsilon_count)`. Noise is added before the scalar
reaches the coordinator. For B<=1 all scores are identically zero on every
private input, so each local report is zero and no count noise is sampled.
The aggregate is an unrounded, unclipped `math.fsum` of already-noised reports.

Path A never calls ordering, cap or RR mechanisms and accepts only a count RNG.
It does not return or duplicate the supplied weight matrix. Its result describes
`accounting_scope=count_only_given_previous_releases` and
`additional_epsilon=epsilon_count`; epsilon_rr is previous-release provenance.
Path B constructs RR exactly once and passes its table to Path A. Phase 3 can
construct the table itself and share it with its degree-product component.

## Sensitivity derivation: ideal arithmetic, fixed prior transcript

Fix the entire previous transcript, including order O, cap B and RR bits, when
comparing graphs differing by one undirected edge. Never recompute the order or
cap on each graph inside this conditional argument. With this fixed total order,
only the earlier endpoint's genuine outgoing list changes; the later endpoint
has only an incoming-edge change. All other clients' score functions are equal.

A fixed-order prefix under one insertion/deletion has only these possibilities:

1. It does not change (the edge is outside the prefix).
2. It gains/loses one vertex while below the cap. At most B-1 new/removed pair
   terms occur. Each has absolute value <=M, since a<M, so the change is at most
   (B-1)M <= (B-1)(M+a).
3. A full prefix replaces x with y. There are B-1 common vertices C, and all
   common-common terms cancel. The difference is
   `sum_{z in C}(W_yz-W_xz)`. Every summand has magnitude <=M+a. Hence the total
   magnitude is at most (B-1)(M+a).

Deletion is the reverse comparison. This covers both signs of RR weights. For
B=0 or 1 no pairs exist, giving zero. For B=2 a replacement changes one weight;
at eta=log(2), weights -1 and 2 give a difference of 3, exceeding the positive
weight bound 2. For example a root prefix {2,3} becomes {1,2} after inserting 1,
with W_23=-1 and W_12=2. Thus using only a positive-weight magnitude is unsafe.

The resulting conditional bound is

```text
Delta_T(B) = 0                       B<=1
Delta_T(B) = (B-1)*(M+a)              B>=2
scale = Delta_T(B)/epsilon_count
```

No counterexample to this bound was found; the general derivation above is the
reason for calibration. Exhaustive finite tests are regression evidence, not a
universal privacy proof. Bounds need not be tight for every public n/order/cap.

## Privacy accounting and release boundary

`TriangleBudget` requires strictly positive finite O, D, R and C allocations,
O<=1, R<=30 and a finite total. Its total is their sum, with no hidden split or
redistribution. Existing k-CoreD guards may reject additional unsupported numeric
regimes. The full standalone allocation is O+D+R+C. No degree allocation exists
in this phase. Allocations are conservative even for public degenerate cases
where a stage emits constant outputs.

Under ideal local mechanisms and edge add/remove adjacency, the proposed
conditional accounting is:

- Ordering: existing threshold/promotion analysis charges both incident endpoints
  together O. Its complete adaptive transcript and unverified status are retained.
- Cap: fixed O makes the outgoing-degree vector's L1 sensitivity one. Only the
  earlier endpoint's query changes, so the noisy vector is charged D, not nD.
- RR: fixed public-ID ownership changes one truth bit, charged R once.
- Count: fixed O/B/RR changes one client's score by at most Delta_T. Independent
  ideal Laplace reports at scale Delta_T/C give the proposed conditional charge C.
- Summation and reusing a previously charged RR transcript add no further query.

This requires an adaptive composition argument comparing identical histories,
independent stage randomization, and accounting for every released message. Local
scores are NOT postprocessing of RR alone: they access genuine incident lists.
Repeating the count component with fresh noise is a new count-stage release.
Reusing or exporting the existing RR bits does not itself resample a mechanism,
but transmitting/storing them still has a communication cost.

Released structures:

- `TriangleComponentResult`: aggregate, n, cap, epsilon_rr, epsilon_count, scale;
  `to_dict` adds scope, target and experimental/simulation labels.
- `TriangleComponentTranscript`: previous order/cap and noisy local reports only.
- `TriangleResult`: aggregate, n, released cap, explicit budget, scale, beta;
  `to_dict` adds total, ordering/mechanism/target labels and experimental status.
- `TriangleTranscript`: k-CoreD transcript, derived order, noisy cap reports, B,
  upper-triangular RR bits and locally noised count reports.
- `TriangleComponentRun` and `TriangleRun`: corresponding result/transcript pairs.

None contains genuine adjacency, selected neighbors, raw local scores, exact
triangle truth, noise draws, seeds or RNG state. As with the existing ordering
protocol, numeric outputs such as levels or zero reports can equal true values
by coincidence; the schema does not label them as non-private diagnostics.
The separate test-only `retained` oracle enumerates true triangles and checks
prefix inclusion. No diagnostic structure is attached to a private result.

## Expected value and truncation

For fixed G,O,B, with RR independent of ordering/cap randomization, each closing
weight has ideal mean A_jk. Linearity (no independence between different roots
is needed for the mean) gives

```text
E[sum_v F_v | O,B] = sum_v sum_{{j,k} subset S_v} A_jk = T_retained(O,B).
```

Fresh independent Laplace noise has mean zero. Every retained triangle belongs
to its unique earliest vertex. With B=n-1 all triangles are retained; otherwise
some may be missing. K4 under ID order and B=2 retains 2 of its 4 triangles.
The unconditional target is E[T_retained(O,B)], not generally T(G). No rescaling
or clipping is performed. Once RR itself is conditioned on, the remaining mean
is sum F_v for that fixed table, not T_retained; the displayed expectation
averages over RR as well as count noise. Arbitrary caller-supplied tables do not
establish the independence assumptions needed for this expectation identity.

Tests enumerate every RR assignment on every four-vertex graph, two orders and
all caps, weighting assignments by their ideal probabilities. Seeded mean tests
on capped/uncapped K4 use a prechosen six-analytic-standard-error tolerance with
3000 trials each. If c_jk is the number of roots reusing a closing report, the
conditional variance used there is
`a*M*sum c_jk^2 + 2*n*scale^2`. This includes covariance caused by RR reuse.
Empirical agreement does not certify unbiased floating-point execution.

## Randomness and reproducibility

`triangle_streams` reuses `simulation_streams`: `SeedSequence(seed).spawn(4)` in
fixed order ordering, cap, RR, count. `TriangleStreams` names these domains and
rejects aliased bit generators. A supplied stream bundle and seed are mutually
exclusive. Streams advance in place; no mechanism resets them per vertex.
Externally supplied generators must actually be independent: distinct objects
alone do not prove independent seeds/states. Seeds are non-private research
inputs and never added to release records. Both seeded and unseeded NumPy draws
are simulation PRNGs. Path A consumes the caller's count stream only.

## Computational and communication costs

Let q_v be the true outgoing degree and s_v=min(B,q_v). The existing
`select_outgoing` scans d_v neighbors, sorts all q_v outgoing neighbors, then
slices the prefix. It does not select in O(B) time. Total selection work is
`O(n+m+sum q_v log(1+q_v))`, bounded by `O(n+m log(1+D_max))`; its temporary
storage is O(D_max). Pair scoring adds `O(sum choose(s_v,2)) <= O(n B^2)`.
Count draws and aggregation add O(n) work, with O(n) retained reports/ranks.

Path A validates the supplied dense RR table in O(n^2) time, with up to O(n^2)
validation temporaries. Thus its incremental time includes O(n^2), selection,
and pair scoring; it generates no RR bits. Besides the caller's O(n^2) table,
peak auxiliary memory can be O(n^2) due to validation. The trusted local kernels
do not repeat full-table validation per client. B<=1 bypasses local selection
and pair scoring, but public table validation still occurs.

Path B additionally:

- k-CoreD: with r executed synchronous rounds, expected O(r(n+m)+n) work under
  constant-cost noise/arithmetic assumptions; final ordering costs O(n log n).
  This implementation retains O(nr) promotion bits. r is bounded by the existing
  public nominal limit and released thresholds, with no low-out-degree guarantee.
- Cap: O(n+m) scans/draws and O(n) max/postprocessing, O(n) reports.
- RR: O(n^2) pair draws/queries, bits and dense matrix construction/storage;
  frozenset membership is expected O(1). No sparse-RR shortcut is used.

Overall time is bounded by
`O(r(n+m) + n log n + n^2 + m log(1+D_max) + n B^2)` and storage by
`O(n+m+n^2+nr)` including graph and full transcripts. These are local-process
computational bounds, not measured distributed timings or communication costs.
In an ideal transport, RR uploads n(n-1)/2 bits; cap/count each upload n scalars;
ordering records O(nr) bits plus thresholds. Broadcasting the entire RR table
to n clients can deliver O(n^3) bits. No secure transport or private table-access
protocol is implemented, and accessing only selected entries could leak patterns.

## Limitations and verification

General sensitivity and ideal expectation derivations are provided for independent
review. Full adaptive LEDP proof, finite/discrete PRNG effects, floating-point
errors and error transcripts, timing/access leakage, malicious clients and actual
client isolation remain unresolved. Numerical failures raise explicitly, never
fall back to exact answers. Python's centralized simulator holds all raw inputs.
No formal privacy, executable LEDP, low-out-degree utility or production security
claim follows from tests or budget objects.

The original Go source uses fresh equal-level coins in cap/count stages, an
internal RR matrix and different noise calibration. This module reuses the
existing Python deterministic order/cap/RR utilities and implements the specified
triangle score and range-aware calibration; it is not a byte-for-byte Go port.
Third-party sources are unchanged.

See checkpoint 10 for exact commands, actual outcomes, source preservation and
the Phase 2 stopping point. Phase 3 is not implemented or automatically started.
