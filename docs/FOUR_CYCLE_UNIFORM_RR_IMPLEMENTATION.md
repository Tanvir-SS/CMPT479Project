# Uniform-sampling + randomized-response non-induced C4

2026-11-11 (America/Vancouver). Stages 3–4 only. This separate implementation
preserves the previous balanced wedge-Laplace estimator and all its artifacts.
Stage 5 is not authorized or run. Formal guarantees below concern the ideal
protocol; passing implementation checks does not establish differential privacy.

## Algorithm and interface

`private_graphlets.four_cycle_uniform_rr.simulate_four_cycles_private(graph,
epsilon, seed=...)` accepts the existing validated `SimpleGraph` and alternatively
a NumPy `rng` (not both). It returns `FourCycleRelease`, including the float
estimate, epsilon, public schedule, per-request alphas, randomized bits and a
research-simulation label. No seed, RNG state, exact wedge, degree, adjacency or
unprotected local count is released. Public IDs are fixed as 0 through n−1.

For n≥4, sample **q=ceil(0.05 n²)** independent candidate cycles with replacement.
Integer `(n*n+19)//20` computes this exactly without floating-point rounding.
Each sample chooses four distinct IDs uniformly and then one of their three
undirected cycles uniformly. For sorted a<b<c<d the representatives are
(a,b,c,d), (a,b,d,c), (a,c,b,d). Each begins at its smallest ID and chooses the
orientation with second ID smaller than last. There are N=3 binom(n,4)
candidates; K4 contributes three, regardless of its extra chords. Duplicate
occurrences are retained with distinct request positions and fresh RR draws.
For public n<4 return 0 with no requests or reports.

For candidate (a,b,c,d), clients b and d respectively compute
X₁=A_ab A_bc and X₂=A_ad A_dc locally. Build the complete schedule first;
K_e counts requested wedges containing potential unordered edge e, including
nonedges. Hence sum_e K_e=4q. A request with edges e₁,e₂ receives

    alpha = epsilon / max(K_e1, K_e2).

There is no global-maximum substitution or epsilon/2 endpoint split. All alphas
and public numerical-range checks are completed before adjacency access.
Each client reports just R=X with probability 1−r and R=1−X with probability r,
where r=1/(1+exp(alpha)). The server computes

    Y = (R-r)/(1-2r)
    C_hat = [3 binom(n,4)/q] sum_t Y_(t,1) Y_(t,2).

No rounding, clipping, Laplace noise, orientation or degree cap is applied.

## Function responsibilities and privacy boundary

- `sample_count`, `cycle_orders`, `public_schedule`: graph-independent sampling.
- `schedule_from_cycles`: deterministic request and participation construction.
  This low-level helper accepts arbitrary public schedules for focused tests;
  only `public_schedule` supplies the estimator's specified distribution and q.
- `allocate_privacy`: per-request epsilon/max participation and range validation.
- `_local_report`: receives one client's neighbor set, one public request, alpha
  and private RNG; computes its wedge internally and returns one randomized bit.
- `rr_parameters`, `debias`: stable RR probabilities and server debiasing.
- `aggregate`: accepts only public schedule, alphas and RR bits; scales products.
- `simulate_four_cycles_private`: orchestrates the one-round simulator.

`PublicSchedule` is immutable: n, ordered cycle occurrences, candidate-major
requests (slot 0 then 1), and sorted `(edge,K)` entries. Omitted potential edges
have K=0. Each request holds candidate ID, slot, center and endpoint IDs; all are
public. Reports and alphas align with the request tuple. There are exactly 2q
reports irrespective of the graph. The low-level aggregation API expects this
internally constructed schedule and matching alphas, not adversarial metadata.
The simulator centrally accesses the graph to model clients, but server functions
receive no graph. This is logical separation, not process or network isolation.

Sampling and storage cost O(q) apart from sorting O(q log q) participation keys;
there is no enumeration of all N candidates in the private estimator. Python
integers avoid fixed-width combinatorial overflow; the estimates use floats.

## Ideal complete-transcript privacy

Assume a fixed public vertex universe, one-undirected-edge adjacency, public
edge-independent sampling, ideal independent RR coins for every occurrence,
exact probabilities/arithmetic and no additional released private information.
Condition on any public schedule S. Changing edge e can affect only K_e wedge
reports, including those centered at either endpoint. Each affected report is
alpha-RR on a binary function and alpha≤epsilon/K_e. Thus the sum of its affected
report budgets is at most epsilon. Unaffected reports have identical laws, and
independent composition bounds the entire conditional transcript likelihood
ratio by exp(epsilon). K_e=0 means no affected reports. Averaging over the same
graph-independent distribution of S preserves this bound; aggregation is
postprocessing. This is the specified ideal pure epsilon-LEDP guarantee under
undirected-edge adjacency, not whole-neighbor-list/user-level privacy.

## Ideal accuracy

E[Y|X,S]=X and v(alpha)=exp(alpha)/(exp(alpha)−1)². Independent coins imply

    E[Z_t|S,G] = I_t
    Var(Z_t|S,G) = X_t1 v_t2 + X_t2 v_t1 + v_t1 v_t2.

Uniform candidates give E[I_t]=C4/N and therefore E[C_hat]=C4. Conditional
cross-occurrence RR covariances vanish even when candidates repeat. The total
variance is the sampling variance N² Var(I)/q plus
(N/q)² E_S[sum_t Var(Z_t|S,G)].

For fixed epsilon>0 and q=Theta(n²), the specified worst-case RMSE is O(n³).
To interpret this as an average over public schedules, condition on one sampled
cycle. Participation of each of its four edges is 1+Binomial(q−1,8/[n(n−1)]),
so its moments through order four are bounded uniformly in n. The two wedge
maxima inherit bounded fourth moments (edge counts need not be independent).
Since v(alpha)=1/[4 sinh²(alpha/2)]≤1/alpha², the expected conditional product
variance per candidate is O_epsilon(1). Both variance components are consequently
O_epsilon(N²/q)=O_epsilon(n⁶). This is not a bound for every realized schedule.
The multiplier .05 is fixed and theoretically motivated, not a proven optimum;
no graph-specific tuning or relative-error/empirical superiority is asserted.
These mathematical arguments remain subject to independent review.

## Verification and limits

Executed with existing Python 3.11.9 and dependencies, without upgrades:

```bash
.venv/bin/python -m pytest -q tests/test_four_cycle_uniform_rr.py
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_escape_integration.py::test_original_six_column_fixtures
```

The focused suite: **26 passed in 0.19s**. It checks all eight fixture candidate
sums, K4/isolate normalization, exact q, controlled sampler calls, repeated
participation, local allocations, RR moments by two-output enumeration, fresh
random draws, both changed-edge endpoints, release schemas, public-before-private
ordering, negative/fractional output, n<4 and numerical/input guards. Deterministic
coin checks establish call behavior, not statistical independence of a PRNG.
Native ESCAPE: **8 passed in 2.62s**, no skips. A second run with a temporary
evidence-capture plugin retained the eight raw outputs; see checkpoint 26.
No Monte Carlo unbiasedness study or full historical regression suite is run.

The implementation uses exp(−alpha) to avoid exponential overflow and
`−expm1(−alpha)/(1+exp(−alpha))` for the debiasing gap. Unrepresentable gaps are
rejected before adjacency access; nonfinite aggregates raise rather than being
clipped or silently discarded. Extremely large alpha can underflow the flip
probability to zero; extremely small alpha yields large debiased values, and
products or sums can overflow. Floating-point RR probabilities, finite PRNG
resolution and these failure behaviors are not certified pure-DP execution.
No resampling or retry policy is implemented. Do not interpret finite-precision
outputs as an exact realization of the ideal guarantee over all epsilon.

NumPy seeded and unseeded generators are research simulation randomness, not
cryptographic protection. Sequential fresh draws model ideal independent public
and private randomness; revealing the simulation seed or generator state can
reveal private coins. Never publish them as part of a protected transcript.
Physical timing, side channels, deployment isolation and secure randomness are
out of scope. No full evaluation, new dataset, baseline, plot, tuning or other
pattern implementation was performed. Stop before Stage 5.
