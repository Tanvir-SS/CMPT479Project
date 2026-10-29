# k-CoreD integration and transcript audit — Phase 06

2026-10-29. **Integrated as an experimental research simulator.** The ordering
is produced by noised k-CoreD threshold/promotion queries, not by a substituted
degree sort. Neither executable LEDP nor the paper's low-out-degree utility
guarantee is certified. Experiments are restricted to public synthetic graphs.

## Source correspondence

The port is [kcore.py](../src/private_graphlets/kcore.py), adapted from Go commit
`b03da893ba1c38d3931708bac919562c5ab57963`, with upstream MIT attribution in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). The original checkout stays
read-only. The primary paper is [Mundra et al., Practical and Accurate Local Edge
Differentially Private Graph Algorithms, PVLDB 2025](https://www.vldb.org/pvldb/vol18/p4199-mundra.pdf).
Its Algorithms 3.1–3.3 and Theorem 3.3 motivate the transcript accounting; its
algorithm states `epsilon_O<=1` and `psi in (0,1)`. We enforce those ranges.
Its utility statement is not automatically a statement about this adapted port.

| Upstream component | Port | Correspondence |
|---|---|---|
| `KCoreLDPTCount`, `algorithms/kcore-ldp.go:202–267` | `kcore_order`, `_run_levels` | Budget split, group size, nominal rounds, threshold-limited synchronous rounds, final levels. |
| `loadGraphWorker`, lines 57–92 | `degree_threshold` | Noised degree, capped subtraction, plus one, log2 threshold and integer conversion. |
| `workerKCore`, lines 132–180 | `promotion_bit`, `_run_levels` | Same-level neighbor count, geometric perturbation, positive bias, threshold test, permanent stopping. |
| `KCoreCoordinator.processData`, lines 40–54 | End-of-round level update | Apply all promotion bits after every client reads the same old-level snapshot. |
| `data-structures/lds.go` | Immutable tuples and local level list | `floor(round/levels_per_group)`; final `(level,ID)` total order. |
| `noise/geometric.go` | `symmetric_geometric` | Same ideal symmetric geometric distribution, different simulation sampler. |

With `f=threshold_fraction`, set `lambda1=f*epsilon_O`,
`lambda2=(1-f)*epsilon_O`. Public defaults are `psi=0.5`, `f=0.5`,
`bias_factor=1`; they were not tuned after observing experiment results.
The port follows the Go formulas

```text
L = ceil(log_(1+psi)(n)) / 4
R = max(0, ceil(4 * log_(1+psi)(n)^1.2) - 2)
z_v = degree_v + SymGeom(lambda1/2)
h_v = z_v - trunc(min(bias_factor * 2*exp(lambda1)/expm1(2*lambda1), z_v)) + 1
t_v = trunc(ceil(log2(h_v)) * L) + 1
```

Here `h_v>=1`, `t_v>=1`; `trunc` is toward zero as in Go. Each vertex publishes
**only `t_v`**, not `z_v`, `h_v` or its degree. The coordinator chooses
`min(R,max_v t_v)` rounds. In round `r`, a vertex is eligible only if it has
promoted in every previous round and `r<t_v`. It uses the current public
level snapshot to compute `U_v=sum_{w in N(v)} [level[w]==r]` and sends

```text
s_v = lambda2/(2*t_v)
bias_v = trunc(6*exp(s_v)/expm1(2*s_v)^3)
promotion_v = [U_v + SymGeom(s_v) + bias_v > trunc((1+psi)^floor(r/L))]
```

All vertices send one bit per round, including inactive vertices' zero bits.
Failure to promote stops future private queries. Levels increase synchronously
by the received bits. The output order is the increasing lexicographic order
of `(final_level[v],public_ID[v])`. There is no further tie randomness.

## Deliberate differences and unresolved source correspondence

1. **Threshold release.** Go sends worker maxima; this port explicitly sends
   each noised threshold. These are postprocessing of the same charged noisy
   degree reports. A reviewer can therefore condition on the exact per-client
   thresholds, rather than assume maxima reveal them. This increases transcript
   detail without adding an ideal-model query, but must be included in the proof.
2. **Clients and communication.** Python sequentially dispatches local functions;
   they use one incident list and public messages. A synchronous coordinator
   applies bits after the barrier. The process still holds every raw input and
   has no OS isolation, secure transport or malicious-coordinator defense. The
   Go worker's multiple raw lists are likewise a simulation convenience, not a
   secure local trust boundary.
3. **Randomness.** Instead of the Go geometric sampler's secure utility and
   finite-range binary search, use two independent NumPy geometric variates
   and subtract them as Python integers. For success probability
   `1-exp(-s)`, the ideal difference has mass
   `tanh(s/2)*exp(-s*abs(k))`. The target law agrees; samples, finite precision,
   truncation behavior and cryptographic properties do not. The simulator
   supports `s in [1e-10,30]` and raises an explicit error outside that range.
4. **Small n and isolates.** Public `n<2` yields level zero with no private
   ordering messages. The separate noiseless oracle uses `max(1,degree)` to
   avoid the Go noise-disabled `log2(0)` problem. The full clique protocol
   returns public constant zero without any stages for `n<4`.
5. **Numerics.** Python integer addition/subtraction avoids Go `int64` wrap in
   bias/count arithmetic. Stable `expm1` denominators are used. Public round
   limits above 100,000 are rejected. Errors are not silently ignored. The
   numerical mechanism, including failure transcripts, still needs review.
6. **Parameters and utility.** The port deliberately keeps Go's group and
   round formulas, which differ from the displayed paper formulas. Go's degree
   bias applies whenever noise is enabled despite an unused `bias` switch;
   the port has an explicit bias factor, without that misleading flag. The
   paper's group/log notation and constants are not all identical to the code.
   No out-degree approximation theorem is claimed for this version.
7. **Final order.** Use full final levels, not estimated/coarsened core values.
   EdgeOrientΔ's independent equal-level coins are removed entirely from our
   orientation. This is a correction to consistency, not a newly proved utility
   improvement.

## Ideal conditional privacy argument to review

Neighbors differ by one undirected edge; both endpoint lists change. For each
endpoint, its initial degree query has sensitivity 1. Ideal symmetric geometric
noise with parameter `lambda1/2` therefore suggests endpoint expenditure
`lambda1/2`; the threshold and subsequent number of rounds are postprocessing.

Fix **all thresholds and all previous promotion messages**, including public
levels. Eligibility and stopping are now public functions of that history.
For an eligible endpoint, the next same-level count changes by at most one.
Its bit is postprocessing of a geometric query with parameter
`lambda2/(2*t_v)`. A vertex makes at most `t_v` such queries, so its cumulative
conditional update expenditure is at most `lambda2/2`. Non-endpoints' lists do
not change, although their later behavior can change through public feedback;
the proof compares their kernels at the **same** feedback history.

Both endpoints together give the proposed bound
`2*(lambda1/2+lambda2/2)=epsilon_O`. A threshold can be random and large:
the count of queries and inverse-threshold parameter must be paired on every
history. A favorable threshold or a good out-degree event is not needed for
this proposed sensitivity/accounting argument. `ordering_budget_ledger`
reconstructs conservative per-vertex expenditures from public messages for tests.
It is a diagnostic, not a proof checker for executable DP.

Public reports are `thresholds`, every fixed-length promotion vector, and final
levels/order derived from those messages. The transcript also identifies public
epsilon, split, group size and nominal round limit. Raw degrees, neighbor lists,
same-level counts, sampled noise and RNG state never enter that structure.
The count protocol subsequently exposes only its separately charged messages.

The ideal argument appears defensible under these explicit contracts. What
remains unresolved is a complete independently reviewed interactive proof and
its relation to this executable: finite-support/discretized PRNG output, numeric
tail errors, parameter-dependent error exits, runtime/access leakage and actual
client isolation. Separately, the adaptation's low-out-degree utility needs its
own derivation. **The integrated configuration remains `experimental_unverified`.**

## Tests and controls

`tests/test_kcore.py` tests ideal PMF ratios, sampler PMF/mean/variance diagnostics,
a hand-derived injected zero-noise trace, synchronous updates, query budgets,
replay, order variability and zero/small graphs. The initial stage result was
**25 passed in 0.19s**. Phase-06 full test outcomes are recorded in its checkpoint.
All ideal-law checks are distinguished from statistical sampler diagnostics.

`nonprivate_kcore_oracle` disables perturbations and bias additions in a separate
function labeled `nonprivate_kcore_oracle`. It has no privacy ledger and is not
an accepted estimator ordering option. Its exact clique counts are checked
against ESCAPE for every experiment graph. The production simulation path
never calls it. Public fixed order and noised k-CoreD order have separate labels.

No Go source was patched, built or run in place. This phase uses an attributed
Python port so that tests, transcripts and seed replay share the existing locked
environment. Paper claims are not imported as test results.
