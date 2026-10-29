# Four-clique research prototype — Phase 06

2026-10-29. Implements the [Phase-05 design](FOUR_CLIQUE_DESIGN.md), including
noised k-CoreD ordering and a canonical debiased-RR comparison. This is an
**experimental, unverified research simulation**, not a deployed LEDP guarantee.
Existing 3-star mechanism/counter sources and tests are preserved.

## Entry points and modules

| File | Functions / purpose |
|---|---|
| `four_clique_exact.py` | `count_four_cliques`, `count_four_cliques_bruteforce`; permutation validation, ranks, stable `select_outgoing`. Exact data are non-private. |
| `randomized_response.py` | `rr_parameters`, `local_rr_row`, `sample_rr_upper`, `rr_matrix`; one owner for each unordered pair, no duplicate endpoint reports. |
| `four_clique.py` | `CliqueBudget`, `allocate_budget`, `simulation_streams`, `conditional_sensitivity`, `local_count_report`, `local_cap_report`, `cap_from_reports`, `simulate_four_cliques`, aggregate-only `estimate_four_cliques`. |
| `kcore.py` | Private threshold/level port, explicit transcript/ledger and separately labeled non-private control; see [integration audit](KCORED_INTEGRATION.md). |
| `four_clique_baseline.py` | `baseline_score`, `simulate_baseline`, `estimate_four_cliques_baseline`; independent six-factor enumeration. |
| `four_clique_experiments.py` | Public-synthetic graph/configuration, metrics, raw evidence, replay and plots. Never called by private estimator entry points. |
| `cli.py` | Adds exact, candidate and baseline commands; previous 3-star commands retain their behavior. |

All source paths in this table are under `src/private_graphlets/`. The legacy
`info.implemented_estimators` field retains its 3-star list for compatibility;
`info.experimental_estimators` separately lists 4-clique, and phase is 06.

## Input, orientation and exact count

Use the existing simple undirected `n m` edge-list contract, public IDs in
`[0,n)`, isolates, undirected deduplication and loop rejection. The target is
the number of unordered complete four-vertex subsets. K4 induced/non-induced
counts coincide. The exact oriented counter sums the three closing-edge
indicators over triples of actual forward neighbors. Its independent oracle
enumerates four-sets and tests all six edges. Each clique belongs to its unique
earliest vertex, with no division by four or 24.

`fixed` uses the ID order unless the caller declares another fixed public
permutation. `kcore` runs the private-level port, then uses `(level,ID)`.
Supplying a public permutation with k-CoreD is rejected. There is no degree or
degeneracy option in the private API. All stages use the same total order.

## Protocol and parameters

```text
validate public parameters and budget allocations
if n<4: return constant zero, with no private messages
spawn independent simulation streams for ordering, cap, RR and local noise
obtain public fixed order or run k-CoreD(epsilon_O)
construct ranks from the total order
obtain public B, uncapped B=n-1, or noised cap using epsilon_D
each lower-ID endpoint sends one RR bit for every possible higher-ID neighbor
coordinator mirrors the noisy table and publishes it
each vertex keeps its first B true outgoing neighbors in rank order
each vertex sums W_ab*W_ac*W_bc over their unordered triples
each vertex adds Laplace noise before sending its scalar report
coordinator sums reports without clipping, truncating or rounding
```

At `eta=epsilon_R`, set `p=1/(exp(eta)+1)`,
`a=1/expm1(eta)`, `M=a+1`. Each pair bit flips with probability `p`.
The adjusted weight is `-a` for report zero and `M` for report one; the diagonal
is zero. The implementation computes the two values directly rather than
subtracting nearly equal `1-2p` values. Distinct pairs have distinct independent
coins; one reported pair is reused across candidate triples. Every nonedge
participates too. There is no sparse filtering of negative weights.

The conditional sensitivity is exactly the Phase-05 proposed bound:

```text
Delta_B = 0                                     if B<3
Delta_B = choose(B-1,2) * M^2 * (M+a)             otherwise
local Laplace scale = Delta_B / epsilon_C
```

At fixed prior transcript, only the earlier endpoint's outgoing set changes
under one changed edge. Stable prefix selection permits an insertion/deletion
or one replacement. The replacement term
`W_xy*(W_ax*W_ay-W_bx*W_by)` is bounded by `M^2*(M+a)`; summing over common
pairs gives the bound. The general derivation remains subject to review;
finite tests include the score change 12 at `eta=log(2), B=3`.

For `B>=3`, every vertex sends a noisy scalar even if it has no triples. For
`B<3`, the entire score function is identically zero and no count noise is
sampled. The private cap is

```text
Q_v = |O_v| + Laplace(0,1/epsilon_D)
B = min(n-1,max(0,ceil(max_v Q_v + (log(n)-log(beta))/epsilon_D)))
```

Only the noisy `Q_v` values reach the coordinator. Always enforce the cap,
including underestimates. `beta` is a utility tail parameter, **not DP delta**.
The released noisy cap can appear in the result as `released_cap`; this is
charged postprocessing, not an exact maximum-degree diagnostic.

Default budget splits, with total `e`:

| Ordering / cap | epsilon_O | epsilon_D | epsilon_R | epsilon_C |
|---|---:|---:|---:|---:|
| k-CoreD / noisy | e/4 | e/4 | e/4 | e/4 |
| k-CoreD / public or uncapped | min(e/3,1) | 0 | (e-epsilon_O)/2 | (e-epsilon_O)/2 |
| fixed / noisy | 0 | e/3 | e/3 | e/3 |
| fixed / public or uncapped | 0 | 0 | e/2 | e/2 |
| general RR baseline | 0 | 0 | e | 0 |

The cap on the **public allocation** `epsilon_O<=1` keeps k-CoreD in its stated
parameter domain. Thus public-cap total e=4 uses `(1,0,1.5,1.5)`. The four-quarter
noisy-cap default supports total e<=4; larger custom totals must keep ordering
epsilon<=1. Explicit custom budgets must sum to total and match active stages.
No hidden extra total epsilon is passed to k-CoreD.

## Transcript, randomness and target

`CliqueRun.transcript` contains only the ordering transcript, derived order,
noisy cap reports, cap, upper-triangular RR bits and already-noised local reports.
It contains no raw degrees, neighbor lists, true scores, clipping rates, exact
counts or seed/state. `CliqueResult.to_dict()` exposes only aggregate/public or
already-private metadata and `privacy_status=experimental_unverified`.
The simulator driver holds all client inputs in one process; these structures
model a release boundary and do not provide memory isolation.

NumPy `SeedSequence(seed).spawn(4)` gives separate domains in the fixed order
ordering/cap/RR/count. Unused stages do not shift later streams. Each domain is
advanced across calls/vertices; it is not reset per vertex. The k-CoreD stream
uses disjoint draws for degree and round queries. Seeded and unseeded NumPy
sampling are research randomness, not cryptographically certified mechanisms.
Seeds are saved only by the non-private synthetic experiment runner.

For no cap, fresh independent RR makes the ideal conditional expected total
equal to original K4. For a cap, it equals the count of cliques whose earliest
vertex retains all other three vertices. This retained target is computed
separately in synthetic evaluation. It may be strictly smaller; e.g. K5 with
cap 3 has target 2 instead of 5. Reuse of pair reports creates covariance across
roots, even on graphs of degeneracy 3. Neither empirical agreement nor replay
establishes privacy, unbiasedness of floating-point execution, or superiority.

## Baseline, complexity and limitations

The baseline is the six-factor product over each unordered four-set, using the
entire total epsilon for one-owner RR. It is the canonical undirected
specialization inspired by [Algorithm 1 of the AISTATS 2025 graphlet
paper](https://arxiv.org/pdf/2505.12954), not a notebook reproduction. It shares
the pair randomizer specification but has an independent enumeration/counting
path and no ordering/cap/count-noise stages.

Dense RR upload/storage costs O(n²); table dissemination to n separate clients
can cost O(n³) delivered bits. A shared public-table abstraction must not conceal
private query access patterns. Triple scoring costs
`O(sum_v choose(min(q_v,B),3)) <= O(n B³)` plus local adjacency scans. Ordering
adds O(R(n+m)) work for this straightforward simulator and O(nR) recorded bits;
baseline enumeration costs O(n⁴). Timings are local process measurements, not
distributed benchmarks or padding against timing leakage.

Scope guards: candidate n<=1000, baseline n<=100, RR epsilon<=30, geometric
parameters in `[1e-10,30]`, finite-positive noise scales. Numeric errors fail
explicitly, never substitute an exact answer. These guards and finite sampling
are executable limitations to review. This phase does not establish a formal
DP proof, cryptographic execution or a guaranteed low-out-degree bound.

Reproduction commands, actual test results and observed utility are in
[experiments](FOUR_CLIQUE_EXPERIMENTS.md), [checkpoint 06](status/checkpoints/06_full_four_clique_implementation.md)
and [review package 06](status/REVIEW_PACKAGE_06.md).
