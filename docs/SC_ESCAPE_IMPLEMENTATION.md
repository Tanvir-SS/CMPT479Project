# SC-ESCAPE: Stage 3 implementation

SC-ESCAPE (Separate-Component ESCAPE) estimates **non-induced, unlabeled P₄**
copies on four distinct vertices; extra host edges are allowed. It lives in
`src/private_graphlets/four_path_sc_escape.py`, independently of the existing
five-stage estimator. Status: **experimental_unverified**. Stage 4 is complete
with a **PARTIAL** classification; see [verification](SC_ESCAPE_VERIFICATION.md).
Stage 5 has not begun. The supplied Stage 1–2 equations
are the implementation contract; their full proof/MSE documents were not present
under an SC-ESCAPE name in the repository and are not reconstructed here.

## API and configuration

```python
from private_graphlets.graph import SimpleGraph
from private_graphlets.four_path_sc_escape import SCEscapeBudget, estimate_sc_escape

graph = SimpleGraph.from_edges(4, [(0, 1), (1, 2), (2, 3)])
budget = SCEscapeBudget(degree=.1, rr=.2, product=.3, triangle=.3)
result = estimate_sc_escape(graph, budget=budget, public_max_degree=3, seed=3101)
record = result.to_dict()
assert budget.total == 1.0  # 2*.1 + .2 + .3 + .3
```

This is an illustrative call, not an experimental result or recommended
allocation. All four epsilon values are required, positive and finite. Their
actual total is computed as `2*degree + rr + product + triangle`; there is no
separate nominal total, automatic split, optimizer or extra privacy mechanism.
`public_max_degree` is a required nonnegative integer supplied independently of
the private data. A loose bound is used unchanged. It is never inferred from
degrees or replaced by n−1. Graphs exceeding it are rejected during offline
input validation; no graph projection occurs. D_max=0 accepts only empty graphs.

`estimate_sc_escape` returns aggregate estimates and public metadata.
`simulate_sc_escape` additionally returns the four report collections in an
immutable `SCEscapeTranscript`. Neither includes raw degrees, true counts,
neighbors, seeds, RNG state, t_i or s_i. Evaluation records must remain separate.
`sc_escape_streams(seed)` spawns four NumPy generators in fixed order: degree,
RR, product, triangle. Advanced simulation callers may instead supply
`SCEscapeStreams`; supplying both a seed and streams or sharing a bit generator
is rejected. Distinct caller-provided generators can still have correlated
initialization; independence remains the caller's responsibility in that mode.

## Two rounds

The exact identity used for normalization is

\[
P_4=\tfrac12\sum_v(d_v-1)\sum_{u\in N(v)}(d_u-1)-3T.
\]

**Round 1:** every vertex releases
\(\hat d_v=d_v+\operatorname{Lap}(0,1/\epsilon_D)\).
Independently, vertex i reports each pair (i,j) with j<i exactly once, including
nonedges, flipping its adjacency bit with
\(p=1/(e^{\epsilon_R}+1)\). Public IDs 0,…,n−1 determine ownership, never a
private ordering. All clients receive all degree reports and the complete RR
table. The table is packed by rows: pair (k,j), j<k, has offset k(k−1)/2+j.
It represents G′ without a dense or redundant copy of the original graph.

**Round 2A:** put \(x_v=\hat d_v-1\) and \(H=\max_u|x_u|\).
Each client computes \(S_v=x_v\sum_{u\in N(v)}x_u\) locally and sends

\[
\hat S_v=S_v+\operatorname{Lap}(0,2|x_v|H/\epsilon_S),
\qquad \hat A=\tfrac12\sum_v\hat S_v.
\]

**Round 2B:** each client selects its actual neighbors below its own public ID.
It computes s_i as their unordered-pair count and t_i as the number of those
pairs present in the already received G′. It sends

\[
\hat w_i=t_i-p s_i+\operatorname{Lap}(0,D_{\max}/\epsilon_T),
\qquad \hat T=\frac{\sum_i\hat w_i}{1-2p}.
\]

This follows the lower-triangle reports and centered wedge calculation in
[Imola, Murakami and Chaudhuri, USENIX Security 2021, Algorithm 3](https://www.usenix.org/system/files/sec21-imola.pdf).
Its projection is unnecessary on our validated public-bound input domain.
No private maximum-degree estimate is added.

The server returns **\(\hat P_4^{SC}=\hat A-3\hat T\)** unchanged, including
negative and fractional values. It uses `tanh(epsilon_R/2)` for the algebraically
identical denominator 1−2p to avoid subtractive cancellation. Product and
triangle reports use independent random streams, and neither component consumes
the other's Round 1 randomness. Round 2A and 2B are one interaction round: neither
needs the other's output. Empty rows still send both reports. Empty public vertex
sets have H=0 by convention and yield zero without any client reports.

## Privacy assumptions and review boundary

The intended ideal model fixes a public vertex set and D_max, and compares
simple undirected graphs differing by one edge, both satisfying the bound.
The accounting behind the supplied contract is:

| Release | Edge-change accounting |
|---|---|
| Degrees | Both endpoint degrees change by one: 2ε_D |
| Lower RR | Exactly one owner reports the changed pair: ε_R |
| Product reports | Conditional on Round 1, endpoint v changes by at most \(|x_v|H\); scale \(2|x_v|H/ε_S\) charges at most ε_S/2 at each endpoint |
| Triangle reports | Conditional on G′, only the larger endpoint's lower-neighbor list changes; at most D_max−1 pairs change, each by at most 1; scale D_max/ε_T gives at most ε_T |
| Total | 2ε_D + ε_R + ε_S + ε_T |

Zero product sensitivity uses the exact zero-scale distribution; for a fixed
Round 1 transcript the corresponding local sum cannot change. A public zero
degree bound restricts the domain to the empty graph. H is derived solely from
released degrees and is not an extra private statistic. Client routines access
only their own private row; the coordinator aggregates reports without raw
adjacency. The broadcast and reporting schedule depend only on n, never on the
actual neighbors. Local loops do depend on private row sizes: this single-process
research simulator is not a deployed client/server system or timing-side-channel
defense. Raw-input validation errors are offline diagnostics, not private messages.

This accounting is an implementation explanation, **not a formal software DP
certification**. The separate Stage 4 report derives ideal full-transcript privacy,
unbiasedness and MSE, while retaining executable qualifications. NumPy streams are reproducible
research noise, not cryptographic randomness. Floating-point sampling, roundoff,
underflow and observable numerical failures need separate deployment analysis.
Do not publish seeds with a claimed private release. Focused tests establish
selected mathematical/mechanism behavior only, not DP or an empirical MSE claim.

## Reuse, costs and limits

The module reuses `SimpleGraph` (validated undirected adjacency, deduplication,
isolates), `validate_epsilon` and `rr_parameters`. Existing degree-noise helpers
use 2/epsilon, so they cannot implement the supplied 1/epsilon_D degree scale.
Existing RR sampling uses the smaller-ID owner; a separate lower-row sampler
uses the same probability helper and the specified larger-ID ownership. None of
those shared helpers or existing estimators was changed.

Sampling/storage costs are O(n²) for RR, O(n+m) for degree products apart from
deterministic neighbor sorting, and O(sum_i binom(d_i^-,2)) for triangle pairs.
The transcript uses O(n²+n) storage; local neighbor lists use at most O(D_max)
temporary storage. A deployment broadcasting the full table to every client has
O(n³) total downstream communication. The simulator passes a shared immutable
tuple and performs no neighbor-dependent server queries.

The research guard is n≤1000. The shared RR helper limits epsilon_R≤30 and rejects
nonfinite RR parameters. Nonrepresentable scales, detected overflow/underflow or
nonfinite reports raise errors rather than silently clipping or retrying. Python
integers count local pairs; aggregate estimates use float64-compatible arithmetic
and `math.fsum`. Low-level `local_*` routines assume validated driver inputs and
are not independent privacy entry points.

Stage 4 identified an accepted tiny-RR-budget limitation: at epsilon_R=1e-20,
the computed flip probability rounds to 0.5 while the debiasing denominator is
positive, losing the triangle signal. The implementation is unchanged; exact
unbiasedness is an ideal-arithmetic statement. The theoretical MSE bound also
needs max(1,D_max) in its adaptive-noise term to cover D_max=0 uniformly over
budgets. The O(n^5) corollary requires supplied D_max=O(n); a looser public bound
is not silently capped. See the verification report for derivations and examples.

## Targeted verification

```bash
.venv/bin/python -m pytest -q tests/test_four_path_sc_escape.py
.venv/bin/python scripts/reference_fingerprints.py --verify
```

Tests cover eight small cached fixtures against the integer identity and an
independent ordered-quadruple oracle, the implemented noiseless local algebra,
RR probability/ownership, exact Laplace scales, a two-outcome triangle expectation,
budget validation, independent streams, seeded replay, isolates, duplicate edges,
fixed report schedules, explicit bound use, signed fractional outputs and numeric
guards. They do not recompute native ESCAPE truth. See
[checkpoint 31](status/checkpoints/31_sc_escape_stage3_implementation.md) for observed
results, command history and limitations. No standardized evaluation, historical
regression suite, baseline, budget tuning or Stage 5 runner was executed or added.
