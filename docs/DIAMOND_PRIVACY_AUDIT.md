# Diamond: conditional mechanism and accuracy review

2026-11-10 UTC. Reviewed against [the owner's Sections B–E](Diamond_Research_Reference.md)
and [the actual implementation](../src/private_graphlets/diamond.py).
No structural counterexample or required estimator correction was found.
The reasoning below is for independent mathematical review of the **ideal
protocol**. Tests verify finite implementation cases, not production LEDP.

## Model, complete transcript and stage composition

V={0,...,n-1} is public and fixed. Neighboring simple undirected graphs differ
by adding/removing one edge {u,v}; both endpoint adjacency lists change.
Each logical client may inspect only its own incident list. Public B>=2,
budgets/configuration and ID-based ownership must be independent of private
inputs. The modeled release is

```text
T = (public parameters,
     k-CoreD thresholds, every promotion-bit vector, derived levels/order,
     one RR bit for every public unordered pair,
     every noisy coordinate of every eligible outgoing-wedge vector).
```

The final estimate and other released metadata are deterministic functions of T.
No raw neighbor set, selected cap prefix, local indicator, unnoised common-neighbor
count, exact ground truth or noise seed/state is released. Protocol functions
take local rows; the coordinator reconstruction signature contains no graph.

**Ordering costs O conditionally on the existing full-transcript k-CoreD
guarantee.** `kcore_order` uses noised thresholds and synchronous private
promotion bits; order is `(level,ID)`. It is the established attributed Python
port, not the upstream Go executable or a private-ordering oracle.
With f=threshold_fraction, thresholds charge fO/2 per changed endpoint;
promotion at threshold t charges (1-f)O/(2t) per active query, with at most t
queries per endpoint. The existing ideal argument therefore totals at most O.
Condition on the SAME thresholds and preceding messages under both graphs;
do not compare separately realized orders and assume other clients are unchanged.
The executable/source differences are documented in
[KCORED_INTEGRATION](KCORED_INTEGRATION.md) and the
[previous full-transcript analysis](FOUR_CLIQUE_PRIVACY_PROOF.md).

In particular, the port releases individual thresholds rather than Go's worker
maxima, retains Go's group/round constants rather than all displayed paper
constants, replaces the noise sampler with NumPy geometric differences, and
uses consistent public-ID ties. Theorem 3.3 cannot simply be cited as a proof
of this executable or its low-out-degree utility. This task preserves the port
and relies conditionally on its established ideal transcript argument.

**RR costs R.** At each a<b the lower-ID client sends randomized A_ab, including
nonedges, with flip probability p=1/(1+exp(R)). Exactly one input bit changes
under edge adjacency, so the full product kernel has likelihood ratio at most
exp(R), in either direction, for either bit value. Ownership is independent
of the ordering. Debiasing gives W in {-a,1+a}, a=1/expm1(R), with E[W]=A and
Var(W)=v=a(1+a). Every distinct pair gets a fresh coin; reuse of an already
reported pair adds covariance, not another privacy charge.

**The complete wedge stage costs W, not W per coordinate or 2W.** Fix the same
complete earlier transcript. Its order and all pair schedules are now fixed.
Only the earlier endpoint of the changed edge changes its actual outgoing set;
the later endpoint sees a changed incoming edge. Prefix selection has three
possibilities: no change, insertion/deletion with a common set of size at most
B-1, or replacement with exactly B-1 common selected neighbors.

An insertion/deletion changes at most B-1 wedge coordinates. Replacement removes
B-1 distinct pairs and adds B-1 different pairs. All other coordinates/clients
stay the same, hence the whole concatenated vector satisfies
`||X(G)-X(G')||_1 <= 2(B-1)`. This includes a neighbor previously just outside
the cap entering after deletion. Independent Laplace(0,b), b=2(B-1)/W, on every
eligible coordinate has joint density ratio at most
`exp(||X-X'||_1/b) <= exp(W)`. Zero entries must be sent too. Row lengths are
functions of the released order, and total length is always C(n,3).

At each fixed history multiply the O, R, W kernels: ratio <=exp(O+R+W).
Post-processing adds zero. The argument covers both edge directions and all
histories; it does not assume a good orientation or absence of clipping.
It requires ideal independent randomization, exact arithmetic and the full
k-CoreD guarantee above. In ideal arithmetic the default split is three equal
thirds; explicit positive allocations must sum to the stated total.

## Independence, expectation and clipping

Fix G and condition only on the ordering history H for accuracy. The independent
O/R/W streams model fresh ideal stage randomization; conditioning on H does
not condition on RR outcomes. Let q_c,ab=A_ac*A_bc and

```text
mu_c,ab = q_c,ab                                      if c is not earlier
mu_c,ab = lambda*q_c,ab + (1-lambda)*X_c,ab            if c is earlier.
```

For fixed {a,b,c,d}, W_ab, Xhat_c,ab and Xhat_d,ab use disjoint RR pairs
and distinct wedge-noise coordinates, so they are conditionally independent.
This statement is about factors of ONE contribution. Different candidate
diamonds generally share reports and are NOT independent.

Therefore the conditional expected target is exactly
`T(H)=sum_{a<b} A_ab sum_{c<d, c,d!=a,b} mu_c,ab*mu_d,ab`.
When B>=n-1 (or the fixed history has no clipping), X=q and T(H)=D(G).
If no clipping occurs for every possible history, averaging over H proves
ideal unbiasedness. A favorable event in only some histories is insufficient
to claim unconditional unbiasedness at a smaller B.

With clipping, 0<=mu<=q, so 0<=T(H)<=D and delta(H)=D-T(H)>=0. Each true
diamond's conditional weight is 1, lambda or lambda² depending on whether
zero, one or two of its early outer wedges were clipped. False diamonds still
have zero expectation. This is a **fractional hybrid target**, not the count
of diamonds in a retained graph. For K4, order(0,1,2,3), B=2, the target is
4+2lambda (4.5 at lambda=.25), whereas B=3 gives 6. Exact integration of all
64 RR tables on three four-vertex graphs verifies both capped and uncapped
targets; linearity and independent wedge noise integrate Y to X.

## Review of Section E's preliminary bound

All following variances are **conditional on H and fixed G**. Without that
qualification, random clipping targets can add variance. For two independent
debiased RR weights with binary means x,y,
`Var(W1*W2)=v(x+y)+v² <= VR=2v+v²`. Wedge noise has variance VW=2b².
Its noise is independent of RR, so the hybrid variance is at most
`lambda² VR + (1-lambda)² VW = VR*VW/(VR+VW) <= VR`.
This is a variance statement; it does not remove clipping bias or guarantee
minimum full-estimator MSE. Lambda minimizes this public per-factor upper bound.

For a single candidate contribution Z=W_ab*U*V, the three factors are independent
conditional on H. Write A=A_ab in {0,1}, means m1,m2 in [0,1] and variances
s1,s2<=VR. Then

```text
Var(Z|H) = (A+v)(s1+m1²)(s2+m2²) - A*m1²*m2²
          = (A+v)(s1*s2+s1*m2²+s2*m1²) + v*m1²*m2²
          <= (1+v)(1+VR)² - 1
          = (1+v)^5 - 1 = Q.
```

For n>=4 there are N=C(n,2)C(n-2,2) candidate contributions. Each uses five
distinct RR reports and at most two wedge reports. A fixed RR edge occurs in
exactly 5*C(n-2,2) candidates: choose the other two vertices, then five of the
six possible central edges include that edge among their five required edges.
A particular wedge report (c,{a,b}) occurs in n-3 candidates, with central
pair {a,b} and any fourth vertex. Thus at most
`L=25*C(n-2,2)+2(n-3)` contributions share a random report with a fixed
contribution. This is an overcount and **includes the contribution itself**.
Disjoint-report contributions are conditionally independent; shared-report
covariance has magnitude <=sqrt(Var Zi Var Zj)<=Q. Summing ordered covariance
pairs yields `Var(Dhat|H) <= N*L*Q` (also bounded using min(N,L)).

Since D is fixed, conditional squared-error decomposition gives exactly
`MSE=E_H[Var(Dhat|H)+delta(H)²] <= N*L*Q + E_H[delta(H)²]`.
This already includes random-order effects; a separate Var_H(T) term must not
be added again. In the globally unclipped case delta=0, so the stated
O(n^6 Q) MSE / O(n³ sqrt(Q)) RMSE bounds follow. If R is a fixed positive
fraction of small total epsilon, v=Theta(epsilon^-2), giving the stated
epsilon^-10 / epsilon^-5 upper bounds. These are conservative bounds, not
experimental predictions or evidence of improvement over any baseline.
For n<4 there are no contributions; the zero target is handled directly.

No algebraic correction to Sections B–E was required under these conditions.
Independent review should still check the complete k-CoreD argument, exact
conditioning, candidate normalization and dependency bound. Finite simulations
and the report's existence alone do not establish any theorem.

## Checked behavior and unresolved limits

The 49 diamond tests cover: 14 actual native count comparisons; separate test-only
deterministic reconstruction; caps 2/3/n-1; exhaustive neighboring vectors
(18,432 at n=4 over all orders, 61,440 at n=5 over forward/reverse orders);
tight replacements attaining 2(B-1); both RR outcomes and both likelihood
directions; complete schedule/zero entries; stage allocation and independent
stream replay; absence of forbidden transcript fields; graph-free reconstruction;
explicit outer-pair equivalence; finite exact RR integration; primitive moments
and small full-protocol means. Dependency counts for n=4..7 and per-contribution
variance cases also satisfy the proposed bounds. The existing 25 k-CoreD tests
pass separately. None is labeled an empirical test of differential privacy.

Remaining deployment and interpretation limitations:

- Python orchestration owns all adjacency lists; logical local interfaces are
  not process isolation, secure transport or a malicious-coordinator defense.
- NumPy (seeded or unseeded), finite geometric support, float arithmetic,
  exceptional exits, access patterns and timing are not certified DP kernels.
  Publishing simulation seeds would permit deterministic disclosures. They
  appear only in tests/commands, not protected result/transcript records.
- `math.fsum` enforces the represented total with no tolerance, but is rounded
  binary arithmetic, not an exact-real budget proof. Sensitivity/noise/budget
  reasoning above concerns ideal laws and real allocations.
- k-CoreD O<=1, RR R<=30, geometric parameter guards and float finiteness restrict
  the executable domain. Defaults reject total>3 rather than change the split.
  Finite cancellation in squared-sum reconstruction can affect numerical error;
  no projection, clipping or rounding is applied to mask it.
- The native adapter's existing <=1000-vertex guard is unchanged. Test graphs
  are small; no real-world diamond utility, baseline advantage or revised
  low-out-degree guarantee has been established.

The implementation matches the specified estimator. Its privacy classification
remains **experimental_unverified**, conditional on the stated ideal protocol
assumptions and independent mathematical review.
