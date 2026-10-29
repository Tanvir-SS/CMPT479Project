# Candidate LEDP 4-clique estimator — design for independent review

Date: **2026-10-29**. Phase 05 is **design and non-private mathematical validation
only**. There is no private 4-clique implementation, utility experiment, or
completed formal privacy proof. The user reports that the preceding 3-star work
was independently reviewed; no review memorandum was supplied in this phase.
The 3-star implementation and historical reports are unchanged.

**Assessment:** the proposal is mathematically plausible with a consistent total
order, fresh independent RR for distinct pairs, a stable enforced cap, and noise
added at each vertex before transmission. It is not justified by directly
extending the Go loops. Capping introduces downward bias; shared edge reports
create potentially substantial covariance; and the private ordering's complete
transcript still needs an implementation-level audit. A utility advantage over
the AISTATS baseline has **not** been established.

The sensitivity, expectation and covariance derivations below are our proposed
arguments for review, not guarantees inherited from either reference. Actual
finite checks are separated from those arguments in section 10.

## 1. Model, notation and output contract

The vertex set `V={0,...,n-1}` and its identifiers are fixed and public. Inputs
are simple undirected graphs; neighbors differ by adding/removing **one
undirected edge**. Both endpoints' incident-edge lists change. This is not
vertex privacy or edge replacement. Each client `v` holds only `N(v)`; an
untrusted coordinator sees all protocol messages. We assume honest execution
of the specified protocol, public client assignments and public parameters.
Protection against an endpoint revealing its own input is outside this model.

Write `A_ab` for the indicator of the unordered pair `{a,b}`, `K4(G)` for the
number of unordered complete four-vertex subsets, and `pi` for a strict total
order. Orient `v -> w` when `A_vw=1` and `pi(v)<pi(w)`; let `O_v=N_pi^+(v)`
and `q_v=|O_v|`. A clique is counted once, not four times and not 24 embeddings.
For K4 specifically induced and non-induced counts coincide; that equivalence
does not hold for the other five connected four-vertex patterns.

The proposed external result is an unrounded real aggregate plus public
mechanism parameters. It contains no raw degrees, true edge count, adjacency,
exact count, selected neighbor sets, clipping indicators, seeds or RNG state.
The privacy analysis must nevertheless cover the **entire coordinator-visible
transcript**, including ordering messages, noisy degrees, RR and individual
noisy local counts. An aggregate-only API does not erase prior disclosure.
All exact outputs in this phase are non-private synthetic evaluation data.

## 2. What the references actually do

Source locations refer to commits in [references.json](references.json): ESCAPE
`7ec2f93c524a0b47cdc8c639602e90d1c1fceff3`, Go
`b03da893ba1c38d3931708bac919562c5ab57963`. Both are read-only references.
The earlier [source review](SOURCE_REVIEW.md) supplies additional context.

### k-CoreD and `workerCountTriangles`

In `algorithms/kcore-ldp.go`, `loadGraphWorker` (lines 57–92) adds two-sided
geometric noise to a degree, transforms it into a level/round threshold and
reports a worker maximum. `workerKCore` (132–180) repeatedly counts neighbors
at the current level, adds geometric noise and a deterministic bias term, then
reports promotion bits; thresholds and permanent-stop state limit participation.
`KCoreLDPTCount` (202–267) returns the LDS containing final levels. Use those
levels to define **`pi(v)=(level[v], public_ID[v])`**, increasing lexicographically.
Do not sort coarsened estimated core numbers and call that a degeneracy order:
even exact core numbers put every vertex of a star at core 1 and can place its
high-degree center first.

The paper's Theorem 3.3 splits an ordering budget into degree-threshold and
level-update budgets. Its Lemma 4.3 states a low-out-degree bound of order
`d + log(Dmax)*log(n)^2/epsilon`, with `d` degeneracy. This motivates the
ordering; it is not a deterministic guarantee for every noisy transcript or a
certification of this checkout. The precise parameter range, failure event and
port correspondence require review. See [Mundra et al., PVLDB 2025, sections
3–4](https://www.vldb.org/pvldb/vol18/p4199-mundra.pdf).

The actual `algorithms/triangle-counting-ldp.go` flow is:

| Function / lines | Behavior relevant to the extension |
|---|---|
| `randomizedResponse`, 115–146; `workerRR`, 148–169 | For every pair with `j>nodeID`, including nonedges, flip the adjacency bit with probability `1/(exp(eta)+1)`. Only the lower-ID endpoint reports. |
| Coordinator RR publication, 58–74 | Constructs and mirrors a common noisy adjacency matrix `X`. |
| `workerMaxOutDegree`, 171–208 | Keeps higher-level neighbors; uses separate coin flips for equal levels; adds geometric noise to each out-degree, then reports a maximum. |
| `workerCountTriangles`, 210–256 | Reconstructs outgoing neighbors, sorts IDs, keeps an initial segment of length at most the noisy maximum, and sums `(X_ab*(exp(eta)+1)-1)/(exp(eta)-1)` over pairs. Adds Laplace noise to each vertex's sum, then sends a worker aggregate. |
| `TCountCoord`, 258–378 | Calls ordering, RR, max-out-degree and counting with nominal `epsilon/4` allocations. |

The pair-to-triple extension replaces the last pair summand by
`W_ab*W_ac*W_bc` over three distinct outgoing neighbors. It retains the three
true incident edges locally. It needs a new sensitivity/variance argument.

Specific issues to resolve rather than copy:

- Equal-level ties use independent coins at endpoints, and fresh coins in the
  out-degree and counting stages. These choices need not define a consistent
  orientation or agree between stages. If all four K4 vertices tie, the analogous
  triple loop counts it in expectation `4*(1/2)^3=1/2`, even with noiseless
  closing edges and no cap. For an all-tied triangle the expectation is `3/4`.
  Public ID tie-breaking fixes this combinatorial issue without new disclosure.
- The reference maximum has no explicit upper-tail safety margin in this code;
  truncation can discard genuine patterns. A private upper bound can also
  underestimate with positive probability; sensitivity must hold then too.
- The triangle noise call at line 244 uses `l0Sensitivity=1`,
  `lInfSensitivity=noisy_out_degree`, and **`epsilon/2` of the function's
  argument**. With the caller's quarter budget, that API epsilon is total
  `epsilon/8`. Its nominal scale is `8*noisy_out_degree/epsilon` when valid.
  Debiased RR values can exceed 1 in magnitude; this call alone does not justify
  the required conditional sensitivity. A sampling error is printed and the
  function continues. Neither behavior is a specification for our candidate.
- The Go worker owns several raw adjacency lists in memory. This simulates
  local randomizers; it does not itself establish client isolation. The active
  RR path uses pseudorandom `math/rand`; commented cryptographic code is not
  executed. Distributed transport, timing and error behavior need separate work.
- Threshold transformations, bias additions, round constants and adaptive
  stopping in k-CoreD must be matched to the paper's assumptions. Treat
  `KCORE_ORDER` below as an audited-contract requirement, not an available
  certified primitive.

### ESCAPE's directed diamonds

Section 6, Theorem 7 enumerates a specific directed diamond with the first two
vertices as its diagonal, then tests the missing edge. It gives
`O(W++ + DD)` time and `O(m)` additional space in its access model. Every
ordered K4 contains exactly one such directed diamond. See [ESCAPE, Pinar,
Seshadhri and Vishal (2017), Figure 3 and Theorem
7](https://www.cs.cornell.edu/courses/cs6241/2020sp/readings/Pinar-2017-ESCAPE.pdf).

In `Escape/FourVertex.h:295–351`, `fourCliqueCounter` builds `triends` for each
forward edge `(i,j)`, then checks edges between triangle ends. It chooses between
scanning remaining ends and scanning the smaller relevant adjacency list, using
binary search. `Escape/Digraph.h:21–41,83–133` implements exact degree/ID
orientation. `exe/count_four.cpp` relabels before counting; the clique routine
requires forward lists sorted by ID with IDs consistent with the order. A
future alternative orientation cannot simply replace the comparator while
ignoring relabeling/list invariants. Binary searches also matter when translating
the paper's access-model bound to this particular C++ implementation.

## 3. Noise-free counting identities and their proofs

For **every** total order, including a graph-dependent one,

```text
K4(G) = sum_v sum_{ {a,b,c} subset O_v } A_ab A_ac A_bc.       (1)
```

Proof: a nonzero summand has the three incident edges from `v` by membership
in `O_v`, and the three closing edges by the product. It is a clique with `v`
its unique earliest vertex. Conversely each clique has one earliest vertex
and exactly one unordered triple of later vertices. These maps are inverse.
No division or correction for extra edges is needed.

For a forward edge `u->v`, let `T_uv=O_u intersect O_v`. The corresponding
diamond identity is

```text
K4(G) = sum_{u->v} sum_{ {b,c} subset T_uv } A_bc.             (2)
```

The first two vertices of a clique uniquely specify `u,v`; the remaining pair
is a closing edge in their common forward neighborhood. Conversely that
configuration supplies all six edges. This is not enumeration of all six
undirected diamonds inside K4. Identities (1) and (2) were checked independently
against brute force and actual ESCAPE; see section 10.

Exact intersections can prune enormous numbers of non-closing triples. In the
local model a root knows `A_va,A_vb,A_vc`, but not the true leaf edges. Shipping
true triangle/intersection lists would be an additional private release. Using
only positive RR edges as a sparse surrogate discards nonzero **negative**
adjusted weights and biases the polynomial. Weighted regrouping is possible:
if `H_v` is the symmetric zero-diagonal matrix of weights on selected neighbors,
the same triple sum is `trace(H_v^3)/6`. This is algebraic reorganization, not
a new privacy argument, variance reduction or guarantee of sparse computation.
Recommend the transparent triple specification first; defer a separate private
diamond protocol until its information requirements are proved.

## 4. Randomized-response construction and independence

Allocate `eta=epsilon_R>0`. For each unordered pair independently, including
nonedges, the endpoint with smaller **public ID** reports

```text
p = 1 / (exp(eta) + 1)
R_ab = A_ab with probability 1-p; otherwise 1-A_ab
W_ab = (R_ab-p)/(1-2*p) = ((exp(eta)+1)*R_ab-1)/(exp(eta)-1)
a = 1/(exp(eta)-1);   M = exp(eta)/(exp(eta)-1) = a+1
W_ab is either -a or M;   E[W_ab | G] = A_ab.
```

One shared report is mirrored as `W_ba=W_ab`; there are no diagonal reports.
All three edges within a triple are distinct, so independent pair coins give
`E[W_ab W_ac W_bc | G,pi,B]=A_ab A_ac A_bc`, provided the ordering, cap and
selection do not use these RR coins. Randomness for ordering, cap noise, pair
RR and local count noise must be mutually independent conditional on the input.
The order can depend on the true graph through a private protocol; that alone
does not invalidate this conditional expectation.

Reuse the **same pair report** across all occurrences, without extra RR budget.
This preserves each summand's expectation but makes summands and vertices
dependent. Independently re-reporting an edge for each query costs composition
budget; treating these as free independent observations is invalid. Sharing
one coin across different pairs is also invalid for the product calculation:
with three absent edges and `eta=log(2)`, one shared weight gives
`E[W^3]=2`, whereas the correct target is zero.

Publish all pair reports, or provide a public shared table with access patterns
independent of private neighbor sets. Queries only for pairs in `O_v` can expose
the very adjacency that local counting is supposed to keep private. The design
does not assume uncharged private information retrieval or secure aggregation.
Publishing seeds makes reports deterministic given those seeds and is not a
private release. Any eventual NumPy version is a research simulation only.

## 5. Candidate pseudocode and complete budget ledger

Public parameters: `epsilon>0`, `epsilon_O+epsilon_D+epsilon_R+epsilon_C=epsilon`,
`beta in (0,1)`, ordering parameters and fixed ID tie-break rule. A concrete
**illustrative** allocation is one quarter to each stage; it is not utility
optimized. If the cap is fixed publicly in advance, omit the cap mechanism and
set `epsilon_D=0`, for example splitting the other stages into thirds.
`B=n-1` is an uncapped comparison variant; low-degeneracy utility cannot be
assumed for its worst-case count-noise calibration. For public `n<4`, return
constant zero without running any stage.

```text
CANDIDATE_K4(public V, epsilon split, beta; each client holds N(v)):
    # Ideal protocol specification, NOT an implementation.
    T_O, level = KCORE_ORDER(epsilon_O, public parameters)
    # REQUIRED contract: the complete ordering transcript is epsilon_O-LEDP.
    pi = increasing lexicographic order of (level[v], v)
    each client privately forms O_v = {w in N(v): pi(v) < pi(w)}

    if cap is fixed publicly:
        B = public integer in [0,n-1]
    else:
        each client sends Q_v = |O_v| + independent Laplace(0,1/epsilon_D)
        t = log(n/beta)/epsilon_D
        B = min(n-1, max(0, ceil(max_v Q_v + t)))
    # Clients MUST enforce this cap, including when it underestimates.

    independently of all ordering/cap randomness:
        for every unordered pair {a,b}, lower-public-ID endpoint sends
            R_ab = independent binary RR(A_ab, epsilon_R)
        coordinator publishes the symmetric table R
    derive W, a, M by section 4
    Delta_B = 0 if B<3 else choose(B-1,2) * M^2 * (M+a)

    each client v:
        S_v = first min(B,|O_v|) members of O_v in the fixed order pi
        F_v = 0
        for each UNORDERED triple {a,b,c} in S_v:
            F_v += W_ab * W_ac * W_bc
        if B<3: L_v = 0
        else: L_v = F_v + independent Laplace(0,Delta_B/epsilon_C)
        send L_v in a fixed public reporting schedule

    coordinator returns sum_v L_v, with permitted public metadata
```

`B<3` is public and makes all local scores identically zero; do not call a
sampler with zero scale. When `B>=3`, clients with fewer than three true outgoing
neighbors still send a noisy report. Omitting their reports based on true
degree would be a new disclosure. The estimate itself is never rounded,
clipped or projected to nonnegative values. Rounding the **public noisy cap**
is a different, explicitly specified postprocessing operation.

| Visible stage | Conditional edge sensitivity / accounting | Allocation |
|---|---|---|
| Ordering: thresholds or their maxima, promotion messages, stopping, levels | Complete audited k-CoreD transcript; cannot charge only final ranks | `epsilon_O` |
| Cap reports `Q_v` | Fixed order: adding one edge changes only the earlier endpoint's out-degree; vector L1 sensitivity 1, independent scale `1/epsilon_D` | `epsilon_D` |
| RR table, including nonedges | Fixed public ownership: one changed unordered edge changes one owner's input bit; binary RR parameter `epsilon_R` | `epsilon_R` |
| All local reports `L_v`, including worker aggregates | Fixed preceding transcript: only the earlier endpoint's raw outgoing set changes; section 6 bound, scale `Delta_B/epsilon_C` at each vertex | `epsilon_C` |
| Order construction from levels, noisy maximum/cap, broadcast, sum | Postprocessing of already charged reports | 0 additional |

Inside the **required ordering contract**, a paper-style split is
`epsilon_1=f*epsilon_O`, `epsilon_2=(1-f)*epsilon_O`, `0<f<1`: each endpoint's
degree threshold costs `epsilon_1/2`; conditioned on its threshold `t_v`, at
most `t_v` level queries each cost `epsilon_2/(2*t_v)`. Both endpoints together
then cost `epsilon_O`. This is an audit target, not permission to assume that
all adaptive stopping/threshold behavior in the Go implementation satisfies it.
Degenerate thresholds and public parameter ranges must be resolved.

If both endpoints instead report the same pair independently, charge both or
use `epsilon_R/2` at each. The one-endpoint sensitivities above rely on strictly
forward local sets and fixed ownership. They do not apply to an undirected
neighbor-set score or local access to other vertices' true leaf edges.

For the proposed noisy cap, conditional on any order, a union bound on the
lower Laplace tails gives `P(B<max_v q_v | G,pi) <= beta/2 <= beta`. This is a
**utility** event, not a DP delta. Neither count-noise calibration nor transcript
privacy may fail outside it. Cap noise and the margin are our design choice;
they are not claimed to reproduce the Go maximum routine.

## 6. Conditional local sensitivity, including replacement by the cap

Fix one complete preceding transcript `h=(T_O,Q,R)` and hence `pi,B,W`.
Compare neighboring graphs at **this same transcript**. Only the earlier
endpoint of their changed edge has a changed raw outgoing list. Prefix selection
under a fixed total priority changes `S_v` by at most an insertion/deletion or
one replacement; arbitrary graph-dependent selection need not have this property.

Insertion/deletion affects at most `choose(B-1,2)` triple products, each of
absolute value at most `M^3`. For replacement of `b` by `a`, the unchanged
`B-1` members contribute, for each pair `{x,y}`, the difference

```text
W_xy * (W_ax W_ay - W_bx W_by).
```

Each two-weight product is in `[-a*M, M^2]`. Thus each difference has absolute
value at most `M*(M^2+a*M)=M^2*(M+a)`. A valid uniform bound is

```text
Delta_B = choose(B-1,2) * M^2 * (M+a),   B>=3;  Delta_B=0 otherwise.   (3)
```

It also dominates the insertion bound, since `M+a>=M`. The cruder
`2*choose(B-1,2)*M^3` is sufficient. Neither is asserted to be tight for every
`B,n`. With no cap (`B=n-1`), replacement is impossible and the smaller
`choose(n-2,2)*M^3` insertion bound suffices; (3) remains conservative.

Concrete failure of a smaller bound: at `eta=log(2)`, weights are `-1,2`.
Take root 0, order `0<1<2<3<4`, cap 3, old outgoing set `{2,3,4}` and add
edge `{0,1}`. The new selected set is `{1,2,3}`. Set
`W23=W12=W13=W34=2`, `W24=-1`. The old score is `-4`, the new score is `8`,
and the change is **12**, exceeding both a unit-weight bound and `M^3=8`.
Every such RR table has positive probability at finite epsilon. Our finite
checks attain this 12; (3) gives 12 for this cap.

Adding a changed edge may in reality alter many private levels, flip many
orientations and change many selected sets. It is invalid to compare scores
using `pi(G)` versus `pi(G')` and then assert one affected root. The proposed
composition argument instead bounds the likelihood of the ordering transcript,
then each subsequent conditional kernel at identical prior messages. At the
RR stage the changed edge affects a report's distribution and costs
`epsilon_R`; at the final stage that report is fixed, so its appearances in
many products do not become additional raw-input changes. These appearances
still matter for **variance**.

An ideal proof would factor transcript likelihoods into ordering, cap, RR and
local-count kernels, bound ratios respectively by
`exp(epsilon_O), exp(epsilon_D), exp(epsilon_R), exp(epsilon_C)`, and compose.
Each conditional bound must hold for **every** possible history, not just
likely good orderings. Client-side noise and one affected final local score
make this a plausible LEDP argument. Adding one noise value after an untrusted
coordinator has received all `F_v` would not establish it. A complete proof for
the audited ordering, all messages and the executable remains outstanding.

## 7. Accuracy, capping bias and correlated RR

Conditional on `G,pi,B` (before RR), the expected aggregate is

```text
K_B(G,pi) = number of cliques whose earliest vertex retains all three
            other vertices in S_v.
E[sum L_v | G,pi,B] = K_B(G,pi) <= K4(G).                     (4)
```

With `B>=max q_v`, this is exactly `K4(G)` for any ordering, giving an unbiased
ideal uncapped estimator. Under a smaller cap it is not generally unbiased for
the original graph. It is also not simply the clique count of a globally
edge-trimmed graph: closing edges are estimated from the original adjacency.
For K5 in ID order, caps 2, 3 and 4 retain respectively **0, 2 and 5** cliques.
A deterministic loss bound, useful only for non-private analysis, is

```text
0 <= K4(G)-K_B(G,pi)
   <= sum_v [choose(q_v,3)-choose(min(q_v,B),3)].
```

If the noisy cap covers every out-degree with probability at least `1-beta`,
then `0 <= K4-E[K_B] <= beta*K4 <= beta*choose(n,4)`. This is bounded bias,
not zero bias. High-probability ordering/cap bounds must not be presented as
unconditional unbiasedness. No correction for lost cliques is proposed here.

For independent pair RR, write `tau=exp(eta)/(exp(eta)-1)^2`. Direct moments give
`Var(W_e)=tau`, `E[W_e^2]=A_e+tau`. Let `T` denote an unordered leaf triple,
`E(T)` its three pairs, `P_T=product_{e in E(T)} W_e`, and
`m_T=|{v:T subset S_v}|`. The total pre-Laplace score is `F=sum_T m_T P_T`.
Our conditional variance expansion for review is

```text
Var(P_T) = product_{e in E(T)}(A_e+tau) - product_{e in E(T)} A_e

Cov(P_T,P_U) =
  [product_{e in E(T) intersect E(U)}(A_e+tau)
   - product_{e in E(T) intersect E(U)} A_e]
  * product_{e in E(T) symmetric_difference E(U)} A_e

Var(F | G,pi,B) = sum_T m_T^2 Var(P_T)
                   + 2 sum_{T<U} m_T m_U Cov(P_T,P_U).       (5)
```

Empty products are 1. Distinct leaf triples share either zero or one edge;
sharing only a vertex creates no covariance. Identical triples are already
grouped in `m_T`. Formula (5) follows by independence of distinct pair reports
in the product of two terms, and is not an empirical independence assumption.
For `B>=3` independent local Laplace reports add
`2*n*(Delta_B/epsilon_C)^2` to this conditional variance. Across random orders
and caps, total MSE adds `E[(K_B-K4)^2]` to the expected conditional variance;
equivalently it includes `Var(K_B)` and squared bias.

**Low out-degree does not imply independent roots or linear variance in n.**
Take a triangle `{a,b,c}` and `r` mutually nonadjacent centers each joined to
all three. Put centers first. This graph has degeneracy 3 and maximum out-degree
3; nevertheless `F=r*W_ab*W_ac*W_bc`, so its RR variance is
`r^2*((1+tau)^3-1)`. This is an explicit obstruction to ignoring shared closing
edges. A sharper utility theorem needs triangle multiplicities and overlaps,
not only a cap on each root's outgoing degree.

At small `eta`, `M` and `a` grow as `1/eta`, so (3) scales as
`O(B^2/eta^3)` and local Laplace scale as `O(B^2/(epsilon_C*eta^3))`.
For fixed allocation fractions this is `O(B^2/epsilon^4)` when `B` is fixed.
Private ordering/cap margins can themselves enlarge `B` at small epsilon.
Three RR factors therefore do not guarantee a practical low-noise estimator.

## 8. Comparison with the general AISTATS 2025 baseline

The identified reference is Suppakitpaisarn, Ponnoprat, Hirankarn and Hillebrand,
[Counting Graphlets of Size k under Local Differential Privacy, AISTATS 2025,
PMLR 258:5005–5013](https://proceedings.mlr.press/v258/suppakitpaisarn25a.html).
Algorithm 1 uses debiased RR products, not naive counts in the randomized
graph. Theorem 3.4 gives fixed-privacy RMSE order `n^(k-1)`, hence `n^3` for
K4; the noninteractive lower bound has its stated worst-case scope. We read
the authors' [arXiv v1, 19 May 2025](https://arxiv.org/pdf/2505.12954), because
the linked proceedings PDF did not render in the web reader. Definition 2's
per-user adjacency privacy convention must be reconciled with our two-endpoint
undirected-edge convention before importing guarantees.

A fair **canonical undirected specialization for our model** is

```text
K_hat_RR = sum_{a<b<c<d} product_{e among these six pairs} W_e(epsilon),
```

using one independently randomized report per unordered pair from its fixed
owner. This is our comparison specification, not a claim that the authors'
ordered-tuple implementation literally uses that ownership. A literal two-owner
implementation needs endpoint budget accounting. Unordered enumeration supplies
the same automorphism normalization as dividing injective K4 embeddings by 24.

| Feature | General debiased-RR comparison | Proposed oriented candidate |
|---|---|---|
| True private incident edges in a local term | None after RR | Three retained locally at the earliest root |
| Noisy factors per term | Six | Three |
| Pair RR budget | Entire `epsilon` with one owner | `epsilon_R`, only part of total budget |
| Additional releases/noise | Sum is RR postprocessing | Ordering, optional cap and local count noise |
| Expected target | Original K4 count | Original count without clipping; `E[K_B]` otherwise |
| Direct counting work | `O(n^4)` four-sets | `O(sum_v choose(min(q_v,B),3))`, at most `O(n B^3)` |
| Pair-report upload | `Theta(n^2)` bits | Still `Theta(n^2)` bits in this design |
| Interaction | One RR round | Ordering rounds, optional cap, RR and count reports |

The following comparison is **our inference**, not a result of either paper:
at the same RR parameter, a single true-clique product has variance
`(1+tau)^3-1` for three factors versus `(1+tau)^6-1` for six. That comparison
ignores budget splitting, correlations, differing candidate sets, cap loss and
local Laplace variance. It cannot establish that the whole estimator wins.
Noninteractive worst-case results also cannot by themselves settle the utility
of an interactive protocol restricted to favorable sparse graphs.

Counting can additionally be bounded by `O(m B^2)` since selected outgoing
degrees sum to at most `m`; selecting neighbors still reads private adjacency.
Ordering costs extra rounds/work. A dense public RR table uses `Theta(n^2)`
storage. Literally sending the entire table separately to every client costs
`Theta(n^3)` delivered bits; a shared bulletin-board abstraction must be stated
explicitly. Cheap uploads do not establish cheap dissemination or private access.
Practical advantages are plausible on low-degeneracy graphs with modest caps;
dense graphs, many shared leaf triples, small epsilon and conservative cap
margins are likely difficulties to examine later, not measured findings.

## 9. Requirements and unresolved review questions

Before any private implementation, an independent reviewer should resolve:

1. **Ordering contract:** audit k-CoreD's complete transcript, its internal
   budget ledger, adaptive thresholds/stopping, parameter domain and utility
   failure event. Retain final levels and public tie-breaking. Establish which
   changes are required relative to the supplied Go code.
2. **Full LEDP proof:** validate conditional sensitivity (3), fixed ownership,
   one affected endpoint per later stage, composition for every transcript,
   client/coordinator trust boundaries, message scheduling and access patterns.
   The proposed ideal argument is not an implementation proof.
3. **Target and cap:** choose an uncapped unbiased reference, a public cap or a
   privately chosen enforced cap. Explicitly accept/quantify clipping bias;
   do not silently report a clipped estimator as unbiased for `K4(G)`.
4. **Accuracy:** verify (4)–(5), bound multiplicities/covariances, cap-loss tails
   and ordering failure contributions, and find regimes where total MSE could
   improve over the baseline at the same total edge privacy budget.
5. **Numerics/randomness:** stable `expm1`-based RR weights, overflow/underflow
   and cancellation checks, no output clipping, sound samplers, independent
   domains of randomness, and explicit simulation-versus-production status.
   Review visible error/timing behavior before claiming executable privacy.
6. **Information releases:** no true out-degree maxima, real clipping rates,
   private neighbor queries, exact references or raw metadata in a private run.
   Budgets compose across repeated releases and parameter tuning on protected
   data. Evaluation diagnostics belong to public synthetic data only.

After review and **new authorization**, recommend first implementing a small
research simulator of the accepted triple specification with separately named
uncapped/capped targets and the fair debiased-RR comparison. Tests should cover
local replacement sensitivity, fixed tie-breaking, independence within products,
covariance across roots, cap-loss examples and all reported transcripts. Only
then consider utility experiments or alternative private diamond structures.
No implementation or experiment in that next phase is authorized by this file.

## 10. Actual validation and reproducibility

The new [design-check script](../scripts/check_four_clique_design.py) implements
only non-private small-graph oracles and finite exact algebra. It does not run
k-CoreD, generate private RR samples, or expose a private estimator API.

From the existing Python 3.11 virtual environment:

```bash
ESCAPE_ROOT=/path/to/escape .venv/bin/python scripts/check_four_clique_design.py \
  --output build/phase05/design_checks.json \
  --summary build/phase05/design_summary.json
ESCAPE_ROOT=/path/to/escape .venv/bin/python -m pytest -q
```

`--escape-root /path/to/escape` is an alternative to the environment variable.
The existing adapter compiles under `build/phase05/escape`, preserves actual
input/stdout/`out.txt` separately from Python counts, pads graphs below four
vertices with isolates, and retains its 1,000-vertex and exact-double-integer
guards. The last connected output is `4-clique` (`nonInd[10]`); no induced
conversion or 3-star field is used. ESCAPE chooses its own exact-degree order;
we compare its count, not a claim that it executed our test orders.

Observed results:

- **1,112 graphs:** all 1,100 labeled simple graphs with 0–5 vertices, plus 12
  named examples. Brute force, outgoing triples, directed diamonds and actual
  ESCAPE agree exactly.
- **124,542 order checks:** every permutation for each graph through five
  vertices; six orders for each larger example (ID, reverse, degree/ID,
  non-private exact peeling, shuffled seed `2026102905`, mock levels plus ID).
  Mock levels test tie consistency; they are not outputs of k-CoreD.
- Larger examples: K6 (15 cliques), K7 (35), star/path/cycle, K3,3, K4 plus
  four isolates (1), four centers on a triangle (4); ER seeds 5001/5002,
  BA seed 5003, SBM seed 5004. Their full generation parameters and counts are
  in the script and saved report, not sampled until a favorable result appeared.
- Exact rational RR expectation checks for all eight true leaf-edge patterns
  at `eta=log(2)` pass. The shared-coin counterexample returns expectation 2.
- **10,240 finite sensitivity comparisons** cover all 64 RR tables on four
  potential neighbors, all neighboring root sets, and caps 0–4. Maxima for
  caps 0/1/2/3/4 are 0/0/0/12/24; all respect (3). This checks a finite instance,
  not all epsilon values or arbitrary graph sizes. The cap examples return
  K5 counts 0/2/5 as above.
- Existing full configured suite: **256 passed in 14.49s**, including all 34
  ESCAPE integration tests; no failures or skips. No private 4-clique utility
  experiment, distributed execution or formal DP verification was performed.

Compact evidence: [validation_05.json](status/validation_05.json). Ignored raw
evidence: `build/phase05/design_checks.json`, `design-checks.log`,
`escape/build.json`, `escape/compile.log`, `pytest.log`, `pytest.xml` and
`references-after.json`. The raw JSON retains 1,112 actual ESCAPE executions.
Transfer it separately or reproduce it; a source clone does not contain ignored
build artifacts. No dependencies changed and both reference trees remain clean.

For review, provide **this design**, [checkpoint 05](status/checkpoints/05_four_clique_design.md),
[STATUS](status/STATUS.md), the script, compact evidence, `references.json`,
`SOURCE_REVIEW.md`, `src/private_graphlets/{graph,escape}.py`, the pinned
dependency files, the cited papers and the indicated upstream source files.
Include raw validation evidence separately. The phase-04
[review package](status/REVIEW_PACKAGE.md) is historical context for 3-star work.

**STOP: design and validation only. Await independent mathematical review and
an explicit follow-up before implementing the private 4-clique estimator.**
