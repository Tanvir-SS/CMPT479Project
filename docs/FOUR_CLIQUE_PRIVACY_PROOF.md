# Four-clique code-to-proof privacy audit — requested Phase 8

2026-11-06 (UTC). Audited revision: **`6fba863e984fda8f55c016655df7ded917cc0576`**.
The clique mechanism files also match the initially inspected `f369d29` revision.
This report is a mathematical audit for independent review, not production certification.

**Overall classification: PARTIAL.** The complete ideal local protocol below has a
pure epsilon-star LEDP proof, and its private-data access/control flow matches the
source. Here epsilon-star is the **exact sum of actual stage allocations**. It is
pure requested-epsilon LEDP when that sum is at most the requested epsilon. The
executable cannot currently support an unqualified requested-epsilon claim:
its budget checks allow a small overspend, its PRNG/numerical kernels are not
certified, public fixed seeds make it deterministic, and it has no real client
isolation. No structural sensitivity/composition counterexample was found for
the ideal protocol. No estimator or allocation formula was changed in this audit.
These qualifications do not prevent analysis of its explicitly stated ideal laws.

## 1. Model, contract and complete transcript

V={0,...,n-1} is fixed and public. Valid inputs are simple undirected graphs;
neighboring G,G' differ in exactly one undirected edge {x,y}, changing both
endpoint adjacency lists. The intended local model gives each vertex only its
own incident list. Public parameters (including fixed order/cap, budgets, psi,
split fraction and beta) are fixed independently of protected data, or come
from a separately charged release. Passing a true degree-derived order/cap as
“public” does not satisfy this assumption.

Assume exact arithmetic, exact independent ideal randomizers, honest execution
of the specified interactive protocol, and no timing, access-pattern, file,
error/debug or memory side channels beyond the specified messages. Randomness
is private to clients, fresh across reports and stages; seeds/states are not
public. The coordinator may see all specified messages, not only the sum.
Its complete logical transcript is

```text
public parameters,
(t_v for all v; every promotion vector; derived levels and total order pi),
(Q_v for all v, when the noisy-cap stage is active; derived B),
(R_uv for all u<v; derived symmetric W),
(Y_v for all v), sum_v Y_v.
```

Fixed-order mode omits ordering queries; public/uncapped mode omits Q. When
n<4 the source returns a public constant zero with no private-stage messages.
For n>=4 and B<3 it still sends RR and n constant zero count reports. The model
protects edge adjacency, not node addition/removal, vertex identities, public
parameters or graph-dependent public inputs provided outside the mechanism.

The actual CLI loads a whole `n m` graph file in one process. Neither file access,
raw header m, nor process memory is an LEDP communication channel. Exact CLI
commands, experiment diagnostics and the noiseless oracle are non-private.
They cannot be combined with protected-data releases and called postprocessing.

## 2. Code-to-proof map and complete computation

Locations refer to the audited revision; source SHA-256 and AST line map are
saved in `build/phase08/source_map.json`. Paths below are under `src/private_graphlets/`.

| Source location | Private local input / randomness | Message or coordinator operation |
|---|---|---|
| `cli.py:16`, `four_clique.py:160` `simulate_four_cliques` | Validate graph and public parameters; dispatch simulated clients | CLI defaults kcore/noisy, API defaults fixed/uncapped; public n<4 shortcut |
| `four_clique.py:23,42` `CliqueBudget`, `allocate_budget` | No private input | Public allocation validation/defaults |
| `four_clique.py:57` `simulation_streams` | SeedSequence creates ordering, cap, RR, count generators | No seed/state in private result; numerical independence is assumed only in the idealization |
| `kcore.py:49,67` `symmetric_geometric`, `degree_threshold` | True local degree; two fresh geometric draws | Per-vertex noised threshold t_v, not degree/noise |
| `kcore.py:77,86` `promotion_bit`, `_run_levels` | Same-level incident-neighbor count; two fresh geometric draws per active query | n-bit synchronous round vector, including inactive zeros |
| `kcore.py:32,139` transcript/order, `kcore_order` | No further private reads | Levels and strict `(level, public_ID)` order |
| `four_clique.py:100,112` `local_cap_report`, `cap_from_reports` | Outgoing degree q_v; one Laplace draw per vertex | Q vector and capped/rounded maximum B |
| `randomized_response.py:21,35,44` parameters/row/table | One adjacency bit per lower-ID-owned pair; fresh uniform per pair | Exactly n(n-1)/2 RR bits, including nonedges |
| `randomized_response.py:52` `rr_matrix` | No private input | Mirrored immutable W; diagonal zero |
| `four_clique_exact.py:33` `select_outgoing` | Actual incident list, public pi/B | Local rank-prefix S_v; **not released** |
| `four_clique.py:66,76,85` sensitivity/score/report | Local triples in S_v and public W; fresh local Laplace | Already-noised Y_v; no F_v or selected set message |
| `four_clique.py:144,155,220` transcript/run/aggregate API | No new randomization | Full modeled transcript or aggregate-only result; finite sum, no clipping |
| `four_clique_baseline.py:18,29` | One RR table using all epsilon | Six-factor four-set sum, no extra adjacency queries |
| `escape.py:69,199` | Exact whole graph, non-private evaluation only | Separate C++ ground truth; never in the private protocol |

Exact source-level protocol (integer truncation is toward zero):

```text
validate public inputs; obtain allocations O,D,R,C; spawn four RNG domains
if n<4: return zero and empty private transcript
if kcore:
    lambda1=f*O; lambda2=(1-f)*O
    L=ceil(log(n)/log(1+psi))/4
    Rounds=max(0,ceil(4*(log(n)/log(1+psi))^1.2)-2)
    each client v:
        z=d_v+SymGeom(lambda1/2)
        h=z-trunc(min(bias_factor*2*exp(lambda1)/expm1(2*lambda1),z))+1
        t_v=trunc(ceil(log2(h))*L)+1; send t_v
    levels=0; active=true
    for r=0,...,min(Rounds,max(t))-1:
        freeze levels from preceding rounds
        for each v: emit 0 unless active and level_v=r and r<t_v
            s=lambda2/(2*t_v)
            U_v=sum_{w in N(v)} [level_w=r]
            bias=trunc(6*exp(s)/expm1(2*s)^3)
            bit=[U_v+SymGeom(s)+bias > trunc((1+psi)^floor(r/L))]
            permanently stop this vertex on bit=0
        publish all n bits; synchronously add bits to levels
    pi=vertices sorted by (level,ID)
else: pi=declared public permutation (ID order by default)
if noisy cap:
    send Q_v=number of later actual neighbors+Lap(0,1/D) for every v
    B=min(n-1,max(0,ceil(max(Q)+(log(n)-log(beta))/D)))
else: B=public cap or n-1
for each u<v: lower-ID u sends R_uv=A_uv XOR Bernoulli(1/(exp(R)+1))
set a=1/expm1(R), M=a+1, W_uv=M if R_uv=1 else -a; mirror once
for each v:
    S_v=first B actual later neighbors in pi order
    F_v=sum_{a<b<c in S_v} W_ab*W_ac*W_bc
    if B<3: send Y_v=0
    else: send Y_v=F_v+Lap(0,Delta_B/C)
return sum(Y), public/already-released metadata; no projection of negative values
```

## 3. Budget modes

Write e for the nominal total. Custom O,D,R,C must activate exactly the selected
stages, with R,C>0 for candidates. Ordering requires O<=1 for n>=4. Default modes:

| Mode | O | D | R | C |
|---|---:|---:|---:|---:|
| kcore / noisy (CLI default) | e/4 | e/4 | e/4 | e/4 |
| kcore / public or uncapped | min(e/3,1) | 0 | (e-O)/2 | (e-O)/2 |
| fixed / noisy | 0 | e/3 | e/3 | e/3 |
| fixed / public or uncapped (API default) | 0 | 0 | e/2 | e/2 |
| baseline | 0 | 0 | e | 0 |

Thus e=4,kcore/public uses (1,0,1.5,1.5), not four quarters. Noisy kcore defaults
reject e>4 for n>=4. RR supports R<=30, and geometric parameters are restricted
to [1e-10,30]. Further scale/finite-value guards apply. Very small positive
parameters need not be executable. Beta is in (0,1) and is **not DP delta**.
Public count sensitivity zero may leave C unused; charged budget remains a valid
upper bound. Constant public n<4 consumes no private budget, despite metadata
retaining the requested allocation.

**Exact versus floating budgets:** `math.isclose(...,rel_tol=1e-14)` accepts
`CliqueBudget(2,0,0,1,1+1e-14)`, whose stage sum is `2.0000000000000098`.
The source also tolerates a mismatch between `budget.total` and requested e.
Consequently the theorem is stated with exact epsilon-star=O+D+R+C; an exact
nominal-epsilon claim additionally requires epsilon-star<=e. A float tolerance
is not a mathematical equality. We retain API/default behavior and explicitly
flag this gap, rather than secretly change allocations. Real arithmetic ideal
default formulas sum to e; finite representation must be audited separately.

## 4. Ordering privacy — a direct proof for this port

For s>0, let q=exp(-s). Difference of independent Geom(1-q) variates on
{1,2,...} has PMF p_s(k)=(1-q)/(1+q) q^|k| for k in Z. This follows by summing
(1-q)^2 q^(j+k-1+j-1) over j>=1 for k>=0 and using symmetry. Hence
p_s(z-d)/p_s(z-d')<=exp(s) whenever |d-d'|<=1. A noised integer sensitivity-one
query is s-DP; any deterministic threshold/bias transformation is postprocessing.

Each endpoint's initial degree query uses s=lambda1/2. Threshold generation
has h>=1,t_v>=1 and is deterministic given that noised degree and public inputs.
The whole threshold vector costs lambda1 because only two degrees change.
The round limit is a function of the public n/config and released thresholds.

Fix the same threshold vector and previous round messages under both graphs.
All levels, active flags, eligibility and zero-message positions are now equal.
Synchronous updates imply level_w<=r before round r; thus same-level and
at-or-above-level neighbor queries agree for an eligible vertex at level r.
A changed edge changes the eligible query at each endpoint by at most one;
non-endpoints' local lists and conditional kernels are identical. A queried
endpoint spends lambda2/(2t_v) on its bit. Failure permanently stops private
queries and only public zero bits follow. Each endpoint is queried at most t_v
times, so its total conditional promotion expenditure is at most lambda2/2.
The two endpoint likelihood ratios multiply to at most exp(lambda2). This holds
on **every** threshold/history, not just on a high-probability event or in
expectation over stopping times.

Multiplying by the initial threshold ratio gives exp(lambda1+lambda2)=exp(O).
One can pad to the public Rounds limit with deterministic zeros: variable length
is then postprocessing of already released thresholds. Final levels and the
ID-tiebroken order are deterministic transcript functions, adding zero cost.
This proves the complete ideal ordering transcript O-LEDP. Non-endpoints may
behave differently on separately generated histories; the proof compares their
kernels at an **identical history**, not at identical random seeds.

Paper/source relation: [Mundra et al., PVLDB 2025](https://www.vldb.org/pvldb/vol18/p4199-mundra.pdf),
Algorithms 3.1–3.3 and Theorem 3.3, motivate threshold-conditional endpoint
accounting. The port follows the pinned Go `KCoreLDPTCount`, `loadGraphWorker`
and `workerKCore` formulas, not every displayed paper constant. It publishes
all thresholds rather than worker maxima, uses Go's group/round formulas and
integer +1 convention, and replaces the sampler. The argument above explicitly
covers these changes; no paper utility theorem is inherited. The paper's proof
conditions on public thresholds. Releasing them explicitly makes that condition
valid here. See [the earlier detailed source map](KCORED_INTEGRATION.md).

## 5. Cap stage and its exact lower tail

Condition on identical released ordering pi. Orient each present edge from its
earlier endpoint. Toggling {x,y} changes exactly one coordinate of q=(|O_v|),
by one: the earlier endpoint. Thus the complete q-vector L1 sensitivity is 1,
not 2 and not n. Independent Lap(0,1/D) coordinates have joint density ratio
at most exp(D*||q-q'||_1)<=exp(D). B is deterministic postprocessing; clipping
Q-derived B into [0,n-1] and applying ceil costs no privacy. Publishing both Q
and B costs D, not 2D. Public/uncapped modes query no q values for release and
spend D=0. Selection is always enforced, even if B is an underestimate.

For n>=4, condition on G,pi, let d=max q and h=log(n/beta)/D. For d=0 the
underestimate event is impossible. For d>=1, because d is an integer in [1,n-1],

```text
B<d  iff  max_v(q_v+L_v)+h <= d-1.
Pr[B<d | G,pi] = product_v F_L(d-1-h-q_v),
F_L(x) = .5 exp(D*x)             for x<=0,
         1-.5 exp(-D*x)          for x>0.
```

The equality boundary has probability zero for continuous ideal noise. Pick any
vertex attaining d. The intersection event implies its noise <=-1-h, so

```text
Pr[B<d | G,pi] <= beta*exp(-D)/(2n) <= beta/2.
```

If r vertices attain d, independence improves this to
`(beta*exp(-D)/(2n))^r`; the full CDF product is exact and may be smaller still.
The extra exp(-D) comes from the integer ceiling; there is no need for a union
bound over all vertices. For n<4 the full protocol's public shortcut makes this
stage absent. These are ideal-law bounds, not guarantees about finite PRNG tails.

## 6. RR stage

Fixed lower-ID ownership sends every unordered pair exactly once, independent
of pi and whether the pair is an edge. Exactly one input bit changes under
edge adjacency. Binary RR with flip probability p=1/(1+exp(R)) has likelihood
ratio at most (1-p)/p=exp(R). Other pair kernels are unchanged, so the entire
independent pair table is R-LEDP. Mirroring/debiasing it is postprocessing.
There is no true sparse-edge filtering or release of an adjacency-dependent
query list. The same pair bit is reused everywhere it is needed; it is not
resampled for each triple. Distinct pair coins must be independent for the
later moment formulas; repeated use creates covariance, not new privacy cost.

The source uses `expm1` for a=1/(exp(R)-1), M=a+1 and computes weights directly
as -a or M, avoiding cancellation in 1-2p. It computes p using exp(-R). All
pair information in the modeled table is randomized; raw A is not a field.
Numerical range checks and finite uniform resolution do not themselves prove
these are exact ideal RR probabilities, especially at extreme R.

## 7. Conditional local-count sensitivity — full-vector proof

Now fix the **entire same earlier transcript**, including pi, B and W. This
conditioning is for privacy; it is different from conditioning only on pi,B
when computing accuracy. Let a>0,M=a+1 and W_e in {-a,M}. Define

```text
F_v=sum_{T subset S_v, |T|=3} product_{e in pairs(T)} W_e.
Delta_B=0                              for B<3;
Delta_B=C(B-1,2)*M^2*(M+a)             for B>=3.
```

Only the earlier endpoint's raw outgoing set changes. Other roots may use the
changed edge as a closing pair, but W is **fixed** here; their selected sets
and scores do not change. Therefore an individual changed-root bound is also
the L1 sensitivity bound of the **whole vector** F.

The rank-prefix rule, for any single insertion/deletion, has just three cases:
no selected-set change; insertion/deletion of one element with a common set of
size <=B-1; or replacement of one element with a common set of size B-1.
There is no arbitrary data-dependent resorting. Deletions are reversals of these
same comparisons, including promotion of the first previously excluded neighbor.

For an insertion with common set C, every new triple contains the inserted x.
Its absolute contribution is <=M^3. Thus change <=C(|C|,2)M^3 <=Delta_B.
Deletion has the same bound. For replacement x by y, triples wholly within C
cancel. For each {i,j} subset C the difference is

```text
W_ij * (W_xi W_xj - W_yi W_yj).
```

A two-weight product belongs to {a^2,-aM,M^2}; since M>a, its range is
[-aM,M^2]. Therefore the two products differ by at most M^2+aM=M(M+a),
and |W_ij|<=M gives M^2(M+a) per common pair. Triangle inequality over the
C(B-1,2) pairs yields Delta_B. B<3 has no triples and F is identically zero.
These cases prove `||F(G)-F(G')||_1 <= Delta_B` for arbitrary valid n/order/cap
and any fixed RR table. The formula is a sufficient bound, not asserted globally
tight for every B/n. It is attained at B=3 with M=2,a=1: replacement changes
12, whereas the insertion-only bound M^3=8 fails. No correction is needed.

Independent finite checks cover all 64 four-vertex graphs, all 24 orders and all
64 RR tables: **294,912 neighboring full-vector checks**. A five-vertex
replacement/deletion case checks all 1,024 full RR tables and attains 12. These
checks supplement the general proof; they are not that proof.

## 8. Final local noise and adaptive composition

For B>=3 every client, even one with no triples, releases
Y_v=F_v+Lap(0,Delta_B/C) using fresh independent noise. At a fixed prior transcript,
the joint density ratio is bounded by

```text
exp(C * ||F(G)-F(G')||_1 / Delta_B) <= exp(C).
```

The scale uses the same released B and same R as the weights. Omitting messages
or count noise only for empty private sets would be a different protocol; the
source does neither. B<3 sends a fixed zero vector, requiring zero budget.

For any common complete logical history, multiply the stage kernels:

```text
ordering ratio <= exp(O)
cap-vector ratio given ordering <= exp(D)
RR-table ratio given prior history <= exp(R)
count-vector density ratio given all preceding messages <= exp(C)
aggregation/metadata: deterministic postprocessing.
```

Hence joint density/mass ratio <=exp(epsilon-star), where epsilon-star=O+D+R+C.
Integration against the product of counting and Lebesgue measures proves, for
every measurable transcript set S,
`Pr[T(G) in S] <= exp(epsilon-star) Pr[T(G') in S]`.
The reverse inequality follows by swapping neighbors. Adaptivity and random
ordering/cap do not require conditioning on a favorable utility event. No
privacy delta is introduced by beta. Full transcripts, and thus the aggregate
alone, satisfy this ideal pure-LEDP guarantee. Exact allocation <=e gives the
requested inequality with e. The six-factor baseline similarly spends only
its one-owner RR budget e; its sum is postprocessing.

## 9. Discrepancies, executable limitations and decisions

- **Nominal-budget tolerance:** the concrete accepted overspend above prevents
  replacing epsilon-star with requested e without an extra assumption. This is
  an accounting-contract gap, not hidden additional graph queries. No default
  was retuned. Exact real budgets or conservative machine accounting need future
  certification before an executable claim.
- **Known/fixed seeds:** conditioned on a fixed public simulator seed, the RR
  table is deterministic. Toggling one edge toggles its reported bit; a singleton
  transcript event has probabilities 1 and 0. No finite epsilon protects that
  conditional mechanism. Seed replay is research reproducibility only. Hiding a
  NumPy seed does not establish exact independent ideal or cryptographic sampling.
- **Geometric support/numerics:** two NumPy geometric draws target the right law,
  but finite integer support/rounding are not analyzed DP kernels. Initial
  lambda1/2 validation is not validation of every later lambda2/(2t_v). Example:
  n=4 edgeless, O=4e-10, default config, seed=8 passes the initial guard then raises
  the per-query range error. Such a guard is a function of released thresholds
  in the ideal transcript, but its executable error behavior is not a certified
  secure protocol. The earlier “smallest per-round” comment overstates that check.
- **Floating operations/errors:** local-score and final-sum finite checks can
  abort; score calculation happens before count noise. Timing, overflow,
  finite-support noise and validation/debug failures are not proven private.
  Exact randomized and rounded distributions would require a separate audit.
- **Isolation:** one Python process owns the entire graph, RNGs and scores. The
  transcript dataclass is a logical release boundary, not isolation or transport.
  Local query access/timing is not padded, and malicious coordination is excluded.
- **Paper utility and source differences:** public ID ties are consistent here;
  Go triangle code uses equal-level coins, a different cap/noise implementation
  and pairs rather than triples. Its privacy or utility claims are not imported.
  ESCAPE uses exact degree order and directed-diamond closure as a non-private
  reference; no private raw-edge pruning is introduced. Baseline authors' pinned
  notebooks implement 4-cycles, not this six-factor K4 implementation.
- **Small-graph shortcut/configuration:** n<4 omits all stages, so some later
  k-CoreD guards are never reached. This changes error checking, not private
  data release. All legal result records remain `experimental_unverified`.

No verified structural mechanism defect required changing an estimator. The only
production-source fix in Phase 8 is unrelated non-private P4 study verification:
normalize recomputed None metrics to the NaN representation written by CSV;
strict pandas warnings had failed a pre-existing zero-truth test. Numerical
comparisons/tolerances, estimators, study configuration and saved data are unchanged.

The independent error analysis may proceed for these **ideal-law** randomizers,
with explicit finite-simulator qualifications. Its exact expectations are not
assertions about every finite-precision/failed execution. This is why overall
status remains PARTIAL despite establishing the ideal composition theorem.

## 10. Reproduction and review

```bash
.venv/bin/python -m pytest -q tests/test_four_clique_privacy_audit.py
.venv/bin/python -m pytest -q tests/test_kcore.py tests/test_four_clique_core.py tests/test_four_clique_protocol.py
.venv/bin/python scripts/reference_fingerprints.py --verify
```

Actual results and failures are recorded in
[checkpoint 08](status/checkpoints/08_four_clique_privacy_audit.md). The pre-existing
[macOS setup checkpoint](status/checkpoints/08_macos_setup.md) is a distinct
historical report. The present tests run on Linux/WSL2 x86_64, Python 3.11.16;
macOS was not re-tested in this audit. No platform-specific production dependency
or randomness behavior was added.
