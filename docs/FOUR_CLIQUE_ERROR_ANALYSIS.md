# Four-clique ideal error analysis — requested Phase 9

2026-11-06 (UTC). Source revision `6fba863e984fda8f55c016655df7ded917cc0576`.
The estimator, its defaults and Phase-6 configuration are unchanged. This is
**non-private offline evaluation** of the ideal laws audited in
[Phase 8](FOUR_CLIQUE_PRIVACY_PROOF.md); executable privacy remains
`experimental_unverified` and the audit classification is **PARTIAL**.
No separately supplied research report containing “Section E” was present in
this checkout/request. This document independently derives and checks the
formulas stated in the Phase-9 instructions; it does not claim to review an
unprovided report.

## 1. Estimand, conditioning and assumptions

G is a simple undirected graph on a fixed public vertex set of size n. A K4
counts once per unordered four-set with all six edges, not 24 embeddings.
Induced and non-induced K4 counts coincide, although this does not hold for
our other patterns. Write K for the original K4 count.

Let H be the ordering/cap history, pi its resulting strict total order, and B
its enforced cap. Each S_v contains the first B **actual** later neighbors of v,
in pi order. K_B counts precisely those original cliques whose unique earliest
root retains all three leaves. Thus 0<=K_B<=K; K_B=K if B>=max_v |O_v|.
It can also equal K when some discarded neighbors do not belong to any lost
clique. An independent four-set/rank-position counter implements this definition.

Condition on G,H for accuracy. Only pi,B affect the following formulas. The
RR/count randomizers are fresh and independent of H, all distinct unordered
pairs have independent RR coins, and every occurrence of a pair reuses its
one report. Count noises are independent across all n clients and independent
of RR. This is different from the privacy sensitivity proof, which also fixes
an identical **RR table** before comparing neighboring graphs.

The evaluator models exact real randomizers, not exact floating-point/PRNG laws.
Integers and rational finite-table checks are exact; transcendental moments and
real-valued outputs are evaluated using Python floats. The finite simulator,
public seeds, abort behavior and numerical kernels retain the limitations in
Phase 8. An empirical match establishes neither DP nor a finite-machine theorem.

## 2. RR expectation, covariance and repeated triples

Set eta=epsilon_R>0, a=1/(exp(eta)-1), M=a+1. For a pair e, A_e is its true
0/1 adjacency and W_e is its debiased RR weight in {-a,M}. Direct two-outcome
summation gives

```text
E W_e = A_e,
tau = Var(W_e) = exp(eta)/(exp(eta)-1)^2,
E W_e^2 = A_e + tau.
```

For an unordered leaf triple T, write E(T) for its three closing pairs and
P_T=product_{e in E(T)} W_e. Pair independence implies

```text
E P_T = product_{e in E(T)} A_e,
Var(P_T) = product_{e in E(T)} (A_e+tau) - product_{e in E(T)} A_e.
```

Two distinct three-vertex sets share zero or one pair. No shared pair means
independent products (sharing one vertex alone is irrelevant). If their common
pair is e, expanding E(P_T P_U)-E(P_T)E(P_U) gives

```text
Cov(P_T,P_U) = tau * product_{f in (E(T) union E(U)) minus {e}} A_f.
```

There are four unshared factors. The covariance can be nonzero even when the
shared pair is a **nonedge**, since Var(W_e)=tau for both input bits.

Let m_T be the number of roots with T contained in S_v. The full score is
F=sum_T m_T P_T, so its exact conditional variance is

```text
V_RR = sum_T m_T^2 Var(P_T)
       + 2 sum_{T<U} m_T m_U Cov(P_T,P_U).
```

Identical triples are collected before the distinct-triple sum. F is unbiased
for K_B: each true retained clique has exactly one earliest root. Reusing RR
makes different roots dependent; treating their scores as independent is wrong.
For a book with six independent roots joined to one closing triangle, with
roots first and B=3, m_T=6. At eta=log(2), tau=2 and V_RR=36*26=936;
an independent-root calculation would incorrectly give 6*26=156.

The evaluator returns exact nonnegative integer coefficients (c1,c2,c3) such
that V_RR=c1*tau+c2*tau^2+c3*tau^3. Diagonal terms use m_T^2. A shared-pair
index counts each distinct-triple covariance once and contributes 2*m_T*m_U
to c1 when its four unshared edges exist. This is algebraic adjacency evaluation,
not a fit to sampled estimates.

## 3. Laplace variance, conditional and unconditional MSE

Phase 8 proves the sufficient full-vector sensitivity bound

```text
Delta_B = 0                                    if B<3,
Delta_B = C(B-1,2)*M^2*(M+a)                    if B>=3.
```

For B>=3 **all n** clients add independent Laplace noise with scale
s=Delta_B/epsilon_C, including clients with zero local score. The aggregate
Z has mean zero and variance V_L=2*n*s^2. B<3 returns constant zero scores
and has V_RR=V_L=0. For the aggregate estimate X=F+Z,

```text
E[X | G,H] = K_B,
b_H = K_B-K,
MSE_H = E[(X-K)^2 | G,H] = V_RR(H) + V_L(H) + b_H^2.
```

For random private ordering and cap, total expectation and variance give

```text
Bias(X) = E_H K_B - K,
Var(X) = E_H[V_RR+V_L] + Var_H(K_B),
MSE(X) = E_H[V_RR+V_L+b_H^2],
E_H[b_H^2] = (E_H b_H)^2 + Var_H(K_B).
```

Do not replace mean squared conditional bias by squared mean bias or add
Var_H(K_B) again after already averaging b_H^2. The square of a finite-sample
empirical bias is another noisy quantity. For example, an equal mixture of
K5 caps 2 and 4 has E[b_H^2]=12.5, (E b_H)^2=6.25 and Var(K_B)=6.25.
Order changes also affect RR covariance and cap-dependent noise even when
K_B is constant; the expectation over H covers those effects.

Here RMSE=sqrt(MSE) is the **L2 norm of the scalar random error**. The scalar
expected Euclidean norm is E|X-K| (MAE), bounded by RMSE via Cauchy–Schwarz;
it is not in general equal to RMSE.

## 4. Finite-n bound and its combinatorial factors

For B>=3, every triple variance is at most
Vmax=(1+tau)^3-1=3*tau+3*tau^2+tau^3. Let N=sum_T m_T be the number of
root/triple occurrences. N<=n*C(B,3) and m_T<=n. Therefore the diagonal sum
is at most n*N*Vmax<=n^2*C(B,3)*Vmax; this includes all repeated-triple
covariances, rather than erroneously treating them as distinct independent terms.

To bound distinct-triple terms, fix an occurrence (v,T). For each possible
root u and each of T's three pairs, a triple U contained in S_u and sharing
that pair has at most B-2 choices of its third vertex. If U=T it belongs to
the already-counted repeated-triple term and is excluded; retaining B-2 is a
safe upper bound. A distinct U cannot share two pairs with T. Thus at most
3*n*(B-2) other occurrences have a distinct triple sharing a pair. Each
covariance is between 0 and tau. Counting **ordered** occurrence pairs now
already equals the 2*sum_{T<U} convention; no additional factor of two belongs
in this bound. Consequently

```text
V_RR <= U_RR(n,B,eta)
      = n^2*C(B,3)*[Vmax + 3*tau*(B-2)].

MSE_H <= U_RR + 2*n*(Delta_B/epsilon_C)^2 + (K-K_B)^2.
RMSE_H <= sqrt(the preceding right-hand side).
```

Set U_RR=0 for B<3; then MSE_H=K^2. For the full protocol, take the expectation
of the right-hand side over H and then its square root for an RMSE bound.
Averaging conditional RMSE values is not unconditional RMSE.

The proposed finite-n bound is valid as written; no combinatorial factor needed
correction. Automated search checks 16,538 graph/order/cap combinations: all
1,100 labeled simple graphs on 0 through 5 vertices, all orders through n=4,
and ID/reverse orders at n=5, with every legal cap. It checks retained counts,
exact polynomial variance and the bound at tau=2. Additional K8 checks cover
eta=0.0001,0.1,1,30 and several caps. These finite checks supplement the general
counting argument; they do not prove it or establish tightness.

## 5. Asymptotics and explicit budget dependence

Hold positive epsilon_R,epsilon_C fixed as n grows. Without clipping, B=n-1
makes the RR bound O(n^6) and Laplace variance O(n^5). Therefore MSE=O(n^6)
and RMSE=O(n^3). With constant B>=3 and **no lost cliques**, RR variance is
O(n^2), Laplace variance O(n), MSE=O(n^2) and RMSE=O(n). These are upper
bounds, not equalities or universal matching lower bounds. For example, edgeless
graphs have zero RR variance; the oriented simulator may still add count noise.
The book family shows quadratic RR growth can occur with constant B due to
repeated triples. No low-degeneracy ordering guarantee was proved here.

For 0<eta=epsilon_R<=1, exact formulas imply

```text
tau = Theta(eta^-2),
M,a = Theta(eta^-1),
Delta_B = C(B-1,2) * exp(2*eta)*(exp(eta)+1)/(exp(eta)-1)^3
        = O(B^2*eta^-3),
V_L = 2*n*C(B-1,2)^2
      * exp(4*eta)*(exp(eta)+1)^2 / [epsilon_C^2*(exp(eta)-1)^6]
    = O(n*B^4/(epsilon_C^2*eta^6)),
U_RR = O(n^2*B^3*(eta^-6 + B*eta^-2)).
```

These constants are independent of n,B in that eta regime; B<3 is the zero
case. The exact formulas, rather than small-eta approximations, are used in
all CSVs. Ordering/cap budgets influence H's distribution and divert budget
from R/C; they do not vanish from the full error problem. Do not replace
individual stage allocations by the total epsilon in these expressions.

## 6. Cap-underestimate and clipping-loss bound

For n>=4, fix G,pi, q_v=|O_v|, d=max q, D=epsilon_D and
h=log(n/beta)/D. The actual cap is clamp(ceil(max_v(q_v+L_v)+h),0,n-1),
where independent L_v have scale 1/D. If d=0, underestimation is impossible.
Otherwise, the integer ceiling gives exactly

```text
P(B<d | G,pi) = product_v F_L(d-1-h-q_v),
F_L(x) = .5*exp(D*x)                for x<=0,
         1-.5*exp(-D*x)             for x>0.
```

For any vertex attaining d, this event requires L_v<=-1-h, hence the product
is at most beta*exp(-D)/(2*n). With r maximizers, it is at most that bound
raised to r. The old beta/2 bound is valid but weaker; the extra exp(-D)
factor comes from ceil, and the n denominator does not require a union bound.
At n<4 the simulator skips the stage and has no clique loss.

Since K-K_B is nonnegative, at most K, and is zero when B>=d,

```text
E[(K-K_B)^2 | G,pi] <= K^2 * product_v F_L(d-1-h-q_v)
                    <= K^2 * (beta*exp(-D)/(2*n))^r
                    <= beta*exp(-D)/(2*n) * K^2 <= (beta/2)*K^2.
```

The CDF product is an exact **underestimate probability**, not exact expected
squared clipping loss: an underestimated cap need not discard any clique.
The uniform last bound also holds after averaging private orders. Beta is a
cap utility parameter, never the delta of a DP guarantee.

For arbitrary graphs K=O(n^4), the refined uniform loss bound is O(beta*n^7)
for fixed D, versus O(beta*n^8) from the old coarse bound. Thus an uncapped
O(n^6) theorem does **not automatically** prove the same full privately capped
bound with fixed beta. This particular uniform argument would suffice if
beta=O(1/n) and D is fixed, or if stronger graph/order-specific loss bounds
were established. That is a condition on a theorem, not a budget/configuration
change or tuning recommendation in this phase. The exact product may be much
smaller; its worst-case improvement remains a separate analysis question.

## 7. Six-factor baseline and fair allocation accounting

The repository's `four_clique_baseline.py::estimate_four_cliques_baseline` uses all
of total epsilon for a single one-owner RR table and sums the six weights over
every unordered four-set. Its release is RR postprocessing, with no ordering,
cap or local count noise. Candidate modes split **the same total** epsilon
according to the unchanged allocation table in Phase 8. Comparing at equal
RR-stage budgets alone would not compare equal total budgets.

For any four-set Q, its six-factor product has mean product A_e and variance
product(A_e+tau)-product A_e. For distinct Q,U,

```text
Cov(P_Q,P_U) = [product_{e in E(Q) intersect E(U)}(A_e+tau)
               - product_{e in E(Q) intersect E(U)} A_e]
              * product_{e in E(Q) symmetric-difference E(U)} A_e.
```

An empty intersection gives zero. Sharing two vertices gives one shared edge;
sharing three gives three shared edges. The evaluator sums all diagonal and
unordered-pair terms with factor two, as a degree-six integer polynomial in
tau. At tau=2, K5 variance is 5*(3^6-1)+2*10*(3^3-1)=4160, verified by all
1,024 RR tables. K6 has 60 pairs sharing three vertices and 45 sharing two,
giving 15*728+2*(60*26+45*2)=14220.

This is our K4 specialization of the general debiased-product approach in the
[AISTATS 2025 author paper](https://arxiv.org/pdf/2505.12954), not a reproduction
of its published experimental tables. The authors' two pinned notebooks are
4-cycle references, not implementations of all six patterns. They were read,
not modified or executed. ESCAPE remains an exact non-private reference; its
[Section 6 oriented counting](https://www.cs.cornell.edu/courses/cs6241/2020sp/readings/Pinar-2017-ESCAPE.pdf)
does not supply private RR variance or a privacy theorem.

## 8. Independent implementation and cost

`src/private_graphlets/four_clique_accuracy.py` is never called by private
release paths. Its public offline functions are:

- `triangle_multiplicities`, `retained_cliques_bruteforce`: independent
  rank-prefix triple counts versus true four-set/rank-position retained counts.
- `ideal_rr_variance`, `ideal_count_sensitivity`: stable equivalent formulas
  using exp(-eta), independently of the mechanism's parameter functions.
- `rr_variance_coefficients`, `evaluate_polynomial`, `conditional_error`:
  exact integer polynomial, separate ideal RR/Laplace/bias components and MSE.
- `rr_upper_bound`, `cap_underestimate_probability`: proved finite-n bound and
  exact ideal cap CDF product, including log-probability for underflow diagnosis.
- `baseline_variance_coefficients`, `baseline_error`: optional small-graph
  baseline variance including all shared-edge dependencies.
- `enumerate_rr_moments`: rational integration over full binary RR tables for
  rational odds exp(eta)>1, independently constructing score terms; returns
  exact mean and central moments through order four. Up to ten sampled pairs
  (1,024 tables). For the book, unused independent pairs can be marginalized
  exactly; outputs distinguish 3 enumerated pairs from 36 full-table pairs.

No sampler or private scorer is used by the analytical functions. Shared input
validators do not calculate scores. The runner separately calls the unchanged
simulator for observed values. Exact counts, orders, seeds and these diagnostics
are **not private messages** and are only suitable for public synthetic/offline
research data.

The analytical scope is deliberately n<=20. With U distinct closing triples,
the shared-pair calculation takes O(sum_e t_e^2) covariance work, where t_e is
the number of triples containing e, at most O(n^4); storing triples/pair indexes
and the order uses O(n+U), with U<=C(n,3). Building and sorting multiplicities
costs O(n^2+n*B^3+U*log(U+1)), and the
independent retained-four-set path takes O(n^5) in this implementation because
it checks an outgoing rank for each true four-set. Baseline quadruple-pair
variance is O(C(n,4)^2)=O(n^8), with O(n^4) stored sets. Enumeration is
exponential in the number of sampled RR pairs and explicitly guarded.
These diagnostic costs are not a performance optimization of the estimator.
Extreme allocations can overflow real moment evaluation and are rejected;
CDF products may underflow, with finite log-probability retained. Small float
summation differences are not algebraic changes to the estimator.

## 9. Actual validation and sampling uncertainty

`build/phase09/validation/` holds the completed ignored run and SHA-256 manifest.
Nine real ESCAPE executions agreed with independent brute force: empty0=0,
empty6=0, K4=1, K5=5, K8=70, triangle-with-isolates=0, book6=6,
sparse8=0 and dense8=11. The two ER seeds are 900101 (p=.2) and 900102 (p=.75).
ID/reverse orders and selected caps give **64 exact diagnostic rows**. Full
native input/output/stdout/stderr are saved in `escape_reference.json`; Python
counts are not relabeled as ESCAPE results. Additional all-cap comparisons are
in the automated tests.

Rational tests exhaust all 64 graph inputs and all 64 full RR outputs at n=4
for both candidate and baseline, plus K5's 1,024 tables and the book's exact
8-table marginal. They agree with coefficients/expectations, including negative
weights and nonedges. At eta=log(2), C=1, B=3:

| Graph/order | K | K_B | V_RR | V_L | squared bias | MSE |
|---|---:|---:|---:|---:|---:|---:|
| K4, ID | 1 | 1 | 26 | 1152 | 0 | 1178 |
| K5, ID | 5 | 2 | 56 | 1440 | 9 | 1505 |
| book6, roots first | 6 | 6 | 936 | 2592 | 0 | 3528 |

Four fixed-order/cap cases each have **4,096** fresh simulator trials. The last
uses rational RR odds 5/4 and C=.25 to exercise small RR allocation. Raw draws
are unchanged; analytic standard errors use the exact enumerated third/fourth
RR moments and Laplace moments. If V is total conditional variance and mu4 is
the centered fourth moment, SE(mean)=sqrt(V/N),
SE(unbiased sample variance)=sqrt((mu4-(N-3)/(N-1)*V^2)/N).
For squared-error means, SE(MSE)=sqrt((E[(X-K)^4]-MSE^2)/N).
Here mu4=mu4_RR+6*V_RR*V_L+12*n*(n+1)*s^4, and the fourth error moment is
mu4+4*b_H*mu3_RR+6*b_H^2*V+b_H^4. These are population uncertainty formulas,
not a sample standard deviation mislabeled as variance.

| Conditional case | Predicted MSE | Observed MSE | Analytic SE of observed MSE | discrepancy / SE |
|---|---:|---:|---:|---:|
| K4, odds 2, C=1 | 1178 | 1184.510 | 30.337 | 0.215 |
| K5, odds 2, C=1 | 1505 | 1503.903 | 37.532 | -0.029 |
| book6, odds 2, C=1 | 3528 | 3494.979 | 79.346 | -0.416 |
| K4, odds 5/4, C=.25 | 6489260 | 6358762.490 | 168078.548 | -0.776 |

These custom **diagnostic** allocations isolate a law for checking and do not
change defaults or the Phase-6 benchmark. All mean, variance and MSE discrepancies
are below the predeclared six-SE attention threshold; the largest absolute
standardized discrepancy is 1.366. Six SE is an attention rule, not a proved
normal-theory simultaneous confidence guarantee.

Three unconditional cases use the unchanged defaults at total epsilon=4.
Each has 1,024 full trials and **separate** 1,024 ordering/cap histories for
analytical prediction, avoiding shared-history coupling of prediction and
observation. Prediction runs never sample RR/count noise. Reported uncertainty
combines the independent sample SEs of full squared errors and predicted
conditional MSEs in quadrature; it is approximate for this finite heavy-tailed
sample, unlike the fixed-history exact-moment SE above.

| Graph/mode | Mean predicted MSE | Observed MSE | Combined SE | discrepancy / SE |
|---|---:|---:|---:|---:|
| K5, kcore/noisy | 2698.773 | 2774.532 | 147.144 | 0.515 |
| book6, kcore/noisy | 232985.892 | 232637.999 | 11111.360 | -0.031 |
| book6, kcore/public B=3 | 93.117 | 91.311 | 4.206 | -0.429 |

The noisy-cap predictions had 115 and 958 distinct orders respectively but
always B=n-1 and no clipping. This does not validate rare cap-loss frequencies;
they are addressed by the CDF proof/tests. The public-cap book had 952 orders,
clipping in 50.78125% of predicted histories, mean conditional bias -1.682617,
squared mean bias 2.831201 and retained-target variance 3.611182. Their sum
6.442383 is mean **squared** conditional bias. Its mean RR/Laplace variances
are 32.231602 and 54.443466. This exercises the random-history decomposition
and real clipping, not just a fixed-order law.

### Reconciliation with preserved Phase-6 results

The original manifest verifies **16,000 saved trials, 160 cells, eight graphs**.
No benchmark was rerun or edited. This diagnostic selects five graphs, epsilon
1 and 4, and all five methods (**50 cells**, 100 saved trials each). It replays
three existing estimates per cell (**150** exact deterministic matches), verifies
allocations and counts, and reconstructs only O/D histories for all selected
candidate seeds. Baseline variance is exact algebraic evaluation at total
epsilon. Candidate predictions below average exact conditional MSE over the
100 **saved histories**, not all possible histories. Old empirical values and
new analytical predictions are separate columns in `phase06_reconciliation.csv`.

The following compact selection uses total epsilon=4 throughout. MSE components
are newly evaluated; “saved RMSE” is an actual historical observation. Rounded
display values do not modify the full-precision CSV.

| Graph / method | Saved RMSE | Predicted RMSE | V_RR | V_L | E squared clipping bias |
|---|---:|---:|---:|---:|---:|
| K4 / baseline | .341 | .346 | .120 | 0 | 0 |
| K4 / kcore noisy | 15.994 | 15.515 | 6.085 | 234.631 | 0 |
| K8 / baseline | 10.379 | 11.016 | 121.345 | 0 | 0 |
| K8 / fixed B=3 | 65.332 | 65.131 | 4.685 | 12.337 | 4225 |
| K8 / kcore noisy | 324.871 | 329.231 | 2808.937 | 105584.132 | 0 |
| book6 / baseline | 2.273 | 2.275 | 5.178 | 0 | 0 |
| book6 / fixed B=3 | 6.499 | 6.098 | 23.302 | 13.880 | 0 |
| book6 / kcore noisy | 465.487 | 482.684 | 170.845 | 232813.011 | 0 |
| dense14 / baseline | 11.039 | 10.827 | 117.233 | 0 | 0 |
| dense14 / fixed B=3 | 69.550 | 70.176 | 3.068 | 21.590 | 4900 |
| dense14 / kcore noisy | 1907.859 | 1892.195 | 3212.359 | 3577190.385 | 0 |

Laplace is the largest predicted component in all ten selected kcore/noisy
cells and all ten fixed/uncapped cells. Small public caps reduce this cost but
can make clipping dominant (K8/dense14). The roots-first book preserves all
cliques at B=3 but has substantial shared-triple RR covariance. All four
candidate methods had worse saved RMSE than baseline in **each of these ten
graph/epsilon comparisons**. This subset does not establish universal rankings
or prove that low-degeneracy orientation cannot help; it supports no accuracy
advantage for the existing settings. We do not tune them here. Hundred-trial
RMSEs can fluctuate, particularly for rare RR products, so discrepancies are
not silently “fixed” by editing data or changing formulas.

## 10. Reproduce, review and remaining questions

```bash
# Run from the project root after the documented locked Python 3.11 setup.
.venv/bin/python -m pytest -q tests/test_four_clique_privacy_audit.py \
  tests/test_four_clique_accuracy.py tests/test_four_clique_accuracy_pipeline.py
# New output required; no overwrite. Uses bundled ESCAPE or --escape-root.
.venv/bin/python scripts/validate_four_clique_accuracy.py run --output build/phase09/reproduction
.venv/bin/python scripts/validate_four_clique_accuracy.py verify --output build/phase09/reproduction
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_escape.py
.venv/bin/python scripts/reference_fingerprints.py --verify
```

The runner saves complete seed/configuration metadata: master=2026110609,
`(master<<64)|(domain<<48)|(case<<32)|trial`, domains 1=conditional,
2=full protocol, 3=prediction histories. Graph-generation seeds are separate.
All source/lock/executable hashes, source revision, build metadata and actual
ESCAPE evidence are in the manifest. Raw CSVs and all summaries are generated
by code, hashed, and checked against raw squared errors/components by `verify`.
The runner refuses an existing output directory and records failures explicitly.
A clean clone lacking ignored Phase-6 artifacts reports historical reconciliation
as unavailable; it does not fabricate old measurements or rerun the full study.
The saved Phase-6 results are needed only for that optional retrospective part.

Review `four_clique_accuracy.py`, the diagnostic script, both accuracy test
files, this document, the Phase-8 proof/tests, and the unchanged mechanism,
kcore, RR and baseline files together. See
[checkpoint 09](status/checkpoints/09_four_clique_error_validation.md) for actual
regression commands, failures/fixes, integrity checks and the final test count.
No new dependencies or plots were required. macOS was not available for this
run; results are Linux/WSL2 x86_64, Python 3.11.16, NumPy 2.2.6. Existing
macOS instructions and pinned references are preserved.

Independent mathematical review remains needed for the derivations and their
scope, tighter graph/order-dependent covariance and cap-loss bounds, ordering
utility guarantees and conditions for a real advantage over the six-factor
baseline. Secure randomness, finite arithmetic/budget accounting, error
channels and actual client isolation remain implementation proof obligations.
Neither passing tests nor these bounded diagnostics resolves them. Stop here;
no optimization, budget tuning, new benchmark or next phase is started.
