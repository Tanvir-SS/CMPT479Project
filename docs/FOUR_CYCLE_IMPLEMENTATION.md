# Balanced wedge-Laplace non-induced C4 implementation

2026-11-09 (America/Vancouver). Implementation and focused verification complete;
the full 4,800-trial study is **not run**. See checkpoint 22 for execution history.

## Specification consistency review

The supplied [specification](FOUR_CYCLE_BALANCED_WEDGE_SPEC_AND_PROOFS.md) is
preserved verbatim. Its instructions to run main evaluations are subordinate to
the owner's current request: prepare the runner and run only a small smoke test.
No inconsistency affecting correctness or ideal privacy was found. This review
does not substitute for independent review of the formal proofs.

For a fixed unordered pair, each assignment to two distinct progression positions
determines exactly one nonzero slope and intercept. There are 12 assignments.
Thus an incident-edge change alters at most 12 coordinates in either endpoint's
entire local vector; other clients' wedges do not use that edge. Fresh Laplace
noise of scale 24/epsilon gives epsilon/2 per affected vector and epsilon after
composing the two endpoints. This analysis is conditional on all public requests;
their distribution and lengths are independent of the graph. There is no
additional data-dependent message in the simulated protocol.

The sampling-variance proof's factorial moments are correct, including diagonal
occurrence pairs and repeated blocks. For r=0,1,2 both overlap distributions have
moment q²*C(4,r)²/C(p,r). Thus subtracting a quadratic interpolating c0,c1,c2
removes all overlap-0/1/2 terms exactly. In particular,
Q(3)=c0-3c1+3c2 and Q(4)=3c0-8c1+6c2; the residual absolute bounds are 4 and 9.
H3+H4 <= 96q, while the independent-set tail is
[4(p-4)+1]/C(p,4)=O(p^-3). Hence Var(T_h)=O(q), uniformly over bounded h.
Independent cycle choices add at most q/4. Independent occurrence noise adds at
most (N²/q)(4b²+4b⁴); conditioning on the schedule and total variance gives the
claimed O_epsilon(p^6) MSE and O_epsilon(n^3) RMSE, since p=Theta(n).

Minor clarification, without an algorithm change: for p=5 or 7 some intersection
events are impossible. Assign arbitrary bounded c_t to these zero-probability
events; H_t and P_t are both zero, so neither the moment calculation nor the
variance changes. The large-p asymptotic includes these finitely many small cases
by enlarging its constant. No independence of the permuted blocks is assumed.

Unbiasedness follows from each block's uniform four-set marginal, the independent
uniform choice of one of three cycles, and independent centered noise on the two
wedges. The normalization uses padded p, not original n. Extra chords are ignored:
K4 contains three non-induced C4 copies, not one induced cycle or one vertex set.

## Implementation and interface

`private_graphlets.four_cycle.simulate_four_cycles_private(graph, epsilon,
seed=...)` also accepts a NumPy `rng` instead of a seed. Graph input uses the
existing immutable `SimpleGraph`, public IDs 0..n-1 and existing edge-list loader.
It constructs all p(p-1) progression occurrences, applies one global permutation,
draws one independent cycle choice per occurrence, and fixes all requests before
local adjacency access. Sorted four-set representatives are exactly those in the
specification. Duplicates are never removed.

Each local call receives only one adjacency row and that client's public requests.
It computes binary wedges locally and returns a noisy vector, with a fresh noise
coordinate for every request. Dummies use public empty adjacency and fresh noise.
The server receives only the public schedule and noisy vectors and multiplies the
two reports per candidate. `FourCycleRelease` contains the estimate, epsilon,
endpoint epsilon, sensitivity, scale, schedule, reports and simulation label.
It contains no seed, RNG state, exact wedge, exact degree or exact edge count.
All client vectors represent one logical reporting round, including empty vectors.
There is no noiseless API switch, clipping, rounding or graph-dependent selection.

The independent `four_cycle_exact.py` helper is non-private evaluation only. It
uses common-neighbor pairs, dividing by two for opposite-pair multiplicity. The
noiseless local candidate helper exists only in tests. Python integers are used
for combinatorics; estimates and noise use float64/Python float. Extremely large
sizes or extreme epsilon can exceed floating-point range or practical memory;
the runner rejects nonfinite observations rather than silently dropping them.
There is no universal numerical-range certification.

The specification assumes n>=4. The implementation additionally supports public
n=0,1,2,3 by the same padding/noise procedure: every true candidate indicator is
zero, so the unbiased target is zero. Tests cover empty and singleton universes.
This is an explicitly documented domain extension, not a changed estimator.

## Focused checks

- Prime schedules 5/7/11/13: occurrence counts, distinct vertices, exact pair
  multiplicity 12, triple bound 24, duplicates and overlap moment identities.
- All eight fixtures: local noiseless candidate sums and independent exact counter
  agree with the authoritative JSON. Analytical marginal expectation checks plus
  exhaustive integration over all 120 p=5 permutations and all three cycle choices.
- Clique/diamond and every K4 edge deletion: per-endpoint coordinate difference
  <=12, unaffected rows unchanged, equal public schedules and vector lengths.
- All four budgets: total/endpoint accounting, scale 24/epsilon and primitive
  per-occurrence noise replay. Code review establishes separate iid draw calls;
  observing distinct samples alone is not a mathematical independence test.
- Isolates, prime/nonprime sizes, negative and large signed server products,
  release schema and server-only aggregation; no rounding or clipping.
- Controlled two-observation metrics check exercises nonzero population variance.
- Existing native ESCAPE eight-fixture integration passes, with real source builds.

## Evaluation preparation

Independent runner: `scripts/evaluate_four_cycle.py`; configuration:
`experiments/configs/four_cycle_six_datasets.json`. Six unchanged graph/mapping
hashes, four fixed total budgets, 200 trials per cell. Per-endpoint fractions .5/.5
describe composition of the same edge change, not two sequential reporting rounds.
Each run caches the correct native C4 column and original ESCAPE output/provenance
from the existing manifest into `escape_ground_truth.json`. Missing/mismatched
manifest evidence fails; it is not replaced by Python counts or a different source.

| Dataset | Cached native non-induced C4 |
|---|---:|
| Karate | 154 |
| Dolphins | 278 |
| Les Miserables | 2672 |
| Brightkite-50 | 198 |
| BA-100 | 207959 |
| SBM-100 | 7302 |

A one-time Python common-neighbor check agrees with all six cached C4 counts.
No new benchmark native recount was needed. SQLite commits each estimate; CSV
exports and summaries are atomic. Resume checks config, source, dependency,
reference and dataset provenance. Every negative/noninteger estimate is retained.
Exact counts and simulation seeds are in non-private evaluation files only.
Runtime covers the complete simulator call and excludes truth/storage work.
Metrics are direct MSE, RMSE, bias, population variance, MAE, relative RMSE,
runtime, mean and MSE SE (undefined for a one-sample smoke cell).

```bash
.venv/bin/python scripts/evaluate_four_cycle.py run --smoke --max-new-trials 3
.venv/bin/python scripts/evaluate_four_cycle.py run --smoke --resume
.venv/bin/python scripts/evaluate_four_cycle.py verify --smoke
```

The smoke uses one trial per cell (24 total), seed master 202611092200, separate
from the reserved main master 202611092201. Main output would be
`experiments/results/four_cycle_six_datasets/`; it has not been created by this task.
The main run requires later owner authorization. Smoke results demonstrate runner
functionality, not accuracy or superiority, and must not be pooled with main data.

## Remaining limitations

Pure epsilon relationship-edge privacy and unbiasedness are statements about the
ideal real-arithmetic protocol. NumPy PRNGs (seeded or unseeded), finite-precision
Laplace sampling and data-dependent physical execution timing are not certified
for deployment. One logical synchronous round is modeled; no network transport,
constant-time client implementation or side-channel protection is provided.
Publishing noise seeds invalidates the protected-transcript interpretation.
Public schedule generation has no graph input; private randomness is never
published as a seed. Formal privacy/accuracy proofs remain subject to independent
review. No novelty, empirical superiority, low-out-degree utility or production
LEDP claim is made. No change to the algorithm's sensitivity, noise or allocation
was made to improve empirical results.
