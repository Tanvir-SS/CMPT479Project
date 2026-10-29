# Privacy notes — 3-star research simulation

**Scope update, 2026-10-29:** the 3-star discussion below preserves the phase-04
review record. The user subsequently reports independent 3-star review; its
memorandum is not supplied here. Phase 06 adds a separate experimental 4-clique
protocol, documented in the addendum at the end and in
[KCORED_INTEGRATION.md](KCORED_INTEGRATION.md). Its proof remains unresolved.

**No formal privacy proof has been completed or reviewed for this implementation.**
This document identifies the intended model and accounting for later independent
review. Passing automated tests is not proof of differential privacy.

Phase 03 adds a **non-private ESCAPE reference/evaluation path**. Its canonical
input, exact counts, diagnostic stdout, generator seeds and evaluation records
are only suitable for public/synthetic validation data. They are never included
in `PrivateThreeStarResult` and do not consume or justify any private mechanism
budget. The [bounded epsilon diagnostic](ESCAPE_VALIDATION.md) is implementation
evidence only; no mechanism, privacy assumption or proof status changed.

Phase 04 extends this evaluation to 15 synthetic graphs, five epsilon values
and 500 trials per cell. [EXPERIMENTS.md](EXPERIMENTS.md) and
[REVIEW_PACKAGE.md](status/REVIEW_PACKAGE.md) give the actual evidence. The
mechanism code and private result schema are unchanged.

## Neighboring graphs and public assumptions

The intended domain is simple undirected graphs on the **same fixed, public,
labeled vertex set** `V={0,…,n−1}`. Two graphs are neighbors if their edge sets
differ by the addition/removal of exactly one undirected edge `{u,v}`. This is
edge-level adjacency, not vertex-level adjacency, edge replacement (which can
change two edges), or a model with a private vertex population. Loops and parallel
edges are outside the domain; duplicate file rows normalize to the same edge set.

Each vertex is intended to know its own incident-edge list. Adding/removing
`{u,v}` changes each endpoint's degree by one and leaves every other degree
unchanged. The public parameters are epsilon, the mechanism definition and `n`.
The input file's exact edge count `m`, raw adjacency, degrees, preprocessing
diagnostics and exact star count are sensitive. They are not included in the
private result. Invalid-input rejection is outside the intended valid-graph
domain; its messages must not be treated as private releases.

## Mechanism, sensitivity and intended budget allocation

For total finite `epsilon > 0`, the specified mechanism is:

```text
b = 2 / epsilon
Y_v = d(v) + Laplace(0, b)       # independent report for every vertex
S_hat = Σ_v [Y_v(Y_v−1)(Y_v−2)/6 − b²(Y_v−1)]
```

The assumed local degree sensitivity is **1** to a change in one incident edge.
The intended local report budget is **epsilon/2**, giving sensitivity divided
by local budget `1/(epsilon/2)=2/epsilon`. At the entire graph level the degree
vector's L1 sensitivity is **2** because both endpoints change. The intended
accounting charges both endpoint reports, `epsilon/2 + epsilon/2 = epsilon`;
one must not mistake this for one endpoint spending the whole budget.

In ideal continuous Laplace arithmetic, the intended density-ratio argument
bounds each affected endpoint's factor by `exp(1/b)` and their product by
`exp(2/b)=exp(epsilon)`. This is an **informal accounting sketch for review**,
not a completed proof about the executable, PRNG, floating point arithmetic,
input handling, or deployment. The intended ideal guarantee is pure edge DP
(delta=0), subject to those assumptions; we do not assert that the NumPy
simulation realizes that guarantee.

The conceptual protocol transcript is the full set of noisy degree reports
`(Y_v)_v`; the deterministic correction and summation are intended postprocessing
and should require no additional budget when applied to that same transcript.
This implementation's `PrivateThreeStarResult` exposes only the aggregate plus
public parameters, not individual reports or raw degrees. This reduction does
not justify calibrating noise to fewer than two affected endpoints. Isolated
vertices also produce reports; dropping vertices according to true degree would
change the specified mechanism and potentially reveal graph information.

## Release boundary in this repository

The simulator loads the entire graph in one Python process and temporarily
constructs degree and noisy-report arrays. It models per-vertex local computation
but provides **no client isolation or distributed transport**. Access to the
input object/process memory is not protected by the aggregate output API.

The private CLI command emits `result_type=private_estimate` with the estimate,
epsilon, scale, public vertex count, constant mechanism labels, software versions
and `simulation_only=true`. No raw degrees, edge count, graph hash/path, exact
count, sampled noises, seed or RNG state are added. Negative/fractional estimates
are retained. Finite-precision diagnostics are local errors, not private outputs.

`count_three_stars`, its brute-force oracle, and `exact-three-stars` are explicitly
**non-private evaluation tools**. Their output can disclose protected information.
Do not combine their records with a private release on confidential data. Tests
use public synthetic inputs; exact degrees and truth are available only there
to validate accuracy and calibrate statistical tolerances.

## Randomness, replay and repeated releases

The implementation uses NumPy Generator/`default_rng`, with an optional
nonnegative simulation seed. NumPy explicitly describes these PRNGs as suitable
for simulation rather than cryptography; see its
[random-sampling documentation](https://numpy.org/doc/2.2/reference/random/index.html).
Omitting a seed does **not** turn NumPy into a cryptographically secure mechanism.

- A fixed known seed makes this a deterministic simulation. Conditional on that
  seed, the intended random privacy mechanism is absent. Publishing seeds or
  state can expose the noise, so these are excluded from private result records.
- A seed/command may be recorded separately for **public or synthetic research
  data**. Do not publish randomness metadata for confidential releases. The
  absence of a seed in JSON by itself does not establish DP.
- For independent simulation trials, create one Generator and advance it across
  calls. Reinitializing with the same seed deliberately replays the same noise;
  reusing such noise across different protected inputs can reveal differences.
- Repeated fresh reports on a protected graph consume additional privacy budget.
  The current API manages **one invocation only**, with no privacy ledger.
  Simple sequential composition would charge k·epsilon for k separately released
  invocations under the intended ideal model. Tests do not authorize such use
  on confidential data or establish a tighter accountant.

## Accuracy rationale and unresolved review questions

The requested correction is implemented unchanged. Under the ideal noise model,
the uncorrected cubic's extra expectation is `b²(d−1)`, matched by the expected
subtracted term. [ALGORITHMS.md](ALGORITHMS.md) records this moment calculation
and a variance expression used only to calibrate tests. Empirical tests are
consistent with those calculations on the tested cases; they do not replace
the independently reviewed privacy and accuracy proofs still required.

Open questions/limitations for that review:

1. Formalize the full local transcript, endpoint ownership, adversary knowledge,
   independence assumptions and composition on the fixed-vertex graph domain.
   Assess any future adaptation beyond simple edge addition/removal separately.
2. Review exact-arithmetic unbiasedness and the variance derivation, and quantify
   finite-sample tails of the cubic correction, particularly at small epsilon.
3. Analyze floating point sampling/discretization, polynomial cancellation,
   overflow/underflow handling and data-dependent error transcripts. Current
   checks explicitly fail on detected nonfinite/unrepresentable results; they
   do not implement a proven finite-precision DP sampler.
4. Specify a secure deployment RNG, report transport, local trust boundary and
   release accounting before treating this simulation as a production mechanism.
5. Review any future filtering, clipping, nonnegativity projection, rounding,
   parameter selection or data-dependent preprocessing. None is used to improve
   the present estimates; such changes can affect unbiasedness/accounting.

## Explicit implementation contract and sources of randomness

| Boundary | Exact contract |
|---|---|
| Valid graph input | Simple, undirected, labeled, fixed public vertices `0..n-1`; full adjacency is sensitive input. UTF-8 loader validates `n m`, IDs, loops and unique-edge count; isolates are declared by n. |
| Local information | Vertex v uses only its own incident neighbors to obtain d(v), plus public epsilon. No private degree orientation, neighbor degrees or exact star count is used. |
| Conceptual message | One scalar `Y_v=d(v)+Laplace(0,2/epsilon)` from every vertex, including degree-zero vertices, with public vertex identity. The coordinator's intended transcript includes all reports. |
| Coordinator output | Deterministic corrected sum; the API returns only aggregate, epsilon, scale, public n and constant simulation metadata. The CLI adds software versions. |
| Actual simulation | One process owns the entire graph and temporarily stores true/noisy degrees. This is not an implemented distributed security boundary. |
| Invalid/numeric input | Raises errors on invalid epsilon, graph input and detected numeric overflow/underflow; no replacement estimate. Error and runtime transcripts require separate privacy review. |
| Non-private research outputs | Trial estimates with stream coordinates/timings, graph seeds, graph files, exact counts and metrics. These are synthetic-data evaluation artifacts, not private release records. |

Randomness is fully specified for reproduction:

1. Production-style local randomness is **not implemented**. `make_rng` calls
   NumPy `default_rng`; given the pinned version its default bit generator is
   PCG64. A supplied seed is deterministic; without a seed it uses OS entropy
   to seed a simulation PRNG. Neither is claimed cryptographically secure.
2. The phase-04 runner explicitly creates PCG64 with
   `SeedSequence(202610280400, spawn_key=(graph_index, epsilon_index, trial))`.
   The indices are zero-based and saved. Every trial has a distinct stream;
   each invocation draws one fresh Laplace variate per vertex. No common-noise
   coupling is used across epsilon values, graphs or trials. Independence is
   an ideal-model assumption supported, not proved, by this PRNG construction.
3. NetworkX ER/BA/SBM graph generators receive separate integer seeds
   4101–4103, 4201–4203 and 4301–4303. Their graph-generation RNGs do not feed
   mechanism streams. Stars and complete graphs are deterministic. Exact
   generated edges and NetworkX version are saved so the graph realization is
   reviewable independently of future generator changes.
4. Aggregation and plotting introduce no randomness. Plotting reads saved data;
   there is no bootstrap, seed search, tail filtering or graphical resampling.

Within-vertex samples, inter-vertex noise and trial streams are treated as
independent for variance/Monte Carlo calculations. Graphs stay fixed within a
cell; reported mechanism uncertainty is conditional on those generated graphs,
not uncertainty over an entire random-graph population. Replaying an existing
stream is verification and is never counted as an additional independent trial.

## Budget table and review boundary

| Operation | Intended accounting in the ideal model |
|---|---|
| One endpoint's degree report | Sensitivity 1, epsilon/2, Laplace scale 2/epsilon. |
| One changed undirected edge | Both endpoints change: epsilon/2 + epsilon/2 = epsilon. Unchanged vertices do not add factors for this neighbor pair. |
| Corrected local polynomial and aggregate from the same reports | Deterministic postprocessing; no additional budget intended. |
| Releasing k fresh invocations on the same protected graph | Basic sequential accounting would be k*epsilon; no privacy ledger is implemented. |
| Full phase-04 grid on one protected graph, if it were deployed | 500*(0.25+0.5+1+2+4) = 3875 by basic composition, not epsilon per whole experiment. Published seeds/exact evaluation already preclude treating these artifacts as DP releases. |
| Graph generation, ESCAPE, exact oracle, CSV metrics, timings and plots | No private budget is assigned. These are non-private synthetic disclosures, not zero-cost private releases on protected data. |

For epsilon 0.25/0.5/1/2/4 the per-endpoint budgets are
0.125/0.25/0.5/1/2 and scales are 8/4/2/1/0.5. No other private mechanism or
budget split is hidden in the experiment pipeline. The intended ideal delta
is zero; **no delta=0 guarantee is claimed for this executable**.

Empirical evidence includes exact/reference agreement, deterministic formula
checks, noise moments, independence diagnostics, quadrature checks, private
schema tests, 500-trial accuracy measurements and exact replay of all 37,500
estimates. It cannot establish the joint-transcript DP inequality, PRNG
independence, real-arithmetic unbiasedness, finite-precision privacy, or a
uniform finite-sample accuracy bound. Those remain independent review tasks.

No orientation or external algorithm is required inside this private 3-star
mechanism. ESCAPE supplies only non-private evaluation truth. 4-clique design
and implementation were explicitly unstarted at the end of that phase-04 record.

## Phase 06 addendum — Experimental 4-clique protocol

The fixed public vertex set and one-undirected-edge add/remove adjacency are
unchanged. Each client uses only its incident list in the intended local model.
The simulator holds all clients in one process; an aggregate API is not a
security boundary against access to process memory. All configurations emit
`privacy_status=experimental_unverified`; NumPy randomness is simulation-only.

`four_clique.simulate_four_cliques` constructs the complete modeled coordinator
transcript. It contains private degree-derived **thresholds**, all noised
promotion bits, derived levels/order, noisy cap reports `Q_v`, published cap B,
one RR bit per unordered pair including nonedges, and locally noised scalar
scores. It excludes raw degrees, original adjacency, selected neighbors,
unnoised scores, seed/state and exact evaluation. The released noisy cap is
postprocessing of charged reports; exact clipping/max-out-degree diagnostics
exist only in the separate public-synthetic experiment runner.

With total epsilon e, the full protocol initially uses
`epsilon_O=epsilon_D=epsilon_R=epsilon_C=e/4`. For public/uncapped k-CoreD mode,
`epsilon_O=min(e/3,1)`, D=0 and R=C=(e-O)/2. Fixed order omits O and redistributes
over remaining stages; the baseline spends all e on RR. Custom allocations must
sum to e and match active stages. Each k-CoreD endpoint initially spends at most
`f*epsilon_O/2`, then at most `(1-f)*epsilon_O/2` over threshold-limited level
queries; both endpoints compose to O. The default f is .5.

Conditional on the same total order, outgoing-degree-vector L1 sensitivity is
1. Each cap report uses independent `Laplace(0,1/epsilon_D)` and the coordinator
adds `log(n/beta)/epsilon_D` before ceiling and restricting B to `[0,n-1]`.
Clients always enforce B. The tail parameter beta controls utility loss and
is not a privacy delta; rare cap underestimation must not invalidate privacy.

RR has flip probability `1/(exp(epsilon_R)+1)` and weights
`W=(R-p)/(1-2p)`, implemented as `-a` or `M` with
`a=1/expm1(epsilon_R)`, `M=a+1`. Only the smaller public-ID endpoint owns a pair.
Distinct pair coins and all ordering/cap/count randomness are independent in
the ideal model. Reuse of one pair report across products is postprocessing;
fresh duplicate endpoint/query reports would require further accounting.

For a fixed preceding transcript, one earlier endpoint's true outgoing set can
change. Stable prefix selection changes at most one retained neighbor, so the
proposed count sensitivity is `Delta_B=choose(B-1,2)*M²*(M+a)` for B>=3, zero
otherwise. Each client sends `F_v+Laplace(0,Delta_B/epsilon_C)`. Noise precedes
the coordinator; all clients participate when B>=3. Coordinator-side noise
after receiving true scores would require a different trust model. The final
sum is postprocessing and is not rounded or projected to nonnegative values.

The conditional proof must compare identical prior transcripts; a changed edge
can otherwise alter many levels and orientations. The candidate composition is
O+D+R+C, covering the whole interactive transcript. The port's audit and
outstanding finite-precision, error, timing, adaptive interaction and client
isolation issues are in [the integration audit](KCORED_INTEGRATION.md). No
complete implementation-level LEDP guarantee is asserted.

Uncapped ideal expectation equals original K4. Capped expectation instead equals
the retained-clique target averaged over order/cap randomness; no loss correction
is implemented. RR products at different roots can be correlated. Testing exact
counts, RR moments, conditional sensitivity, query budgets and replay cannot
establish the full privacy inequality or all utility claims.

The [phase-06 experiments](FOUR_CLIQUE_EXPERIMENTS.md) publish synthetic truth,
seeds, diagnostics and timings and are **not private releases**. Repeating five
methods 100 times at e=.5/1/2/4 on one protected graph would spend 3,750 under
basic composition if each invocation satisfied its ideal contract; that ledger
alone would not justify publishing the experiment's exact metadata/seeds.
