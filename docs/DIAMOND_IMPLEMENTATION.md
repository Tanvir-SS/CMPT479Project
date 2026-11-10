# Hybrid non-induced diamond implementation

2026-11-10 UTC. Task 24 implements the owner's supplied specification and
[Diamond research reference, Sections B–E](Diamond_Research_Reference.md).
The reference was supplied during this task and remains unchanged. No estimator
redesign, other-pattern change, baseline or six-dataset study was performed.
Status: **implemented and targeted checks passed; experimental_unverified**.

## Interfaces and exact target

`src/private_graphlets/diamond.py` provides `DiamondBudget`, `allocate_budget`,
`hybrid_parameters`, `wedge_requests`, `local_wedge_reports`,
`aggregate_diamonds`, `simulate_diamonds` (result plus modeled transcript), and
`estimate_diamonds` (aggregate result only). The driver calls the existing
`kcore.kcore_order`, `randomized_response.sample_rr_upper`/`rr_matrix` and
`four_clique_exact.select_outgoing`/ordering utilities without changing them.
It never calls a noiseless k-CoreD oracle or substitutes a public ordering.

`diamond_exact.count_diamonds` is a separate **non-private** oracle:

```text
D(G) = sum_{actual edges {a,b}} choose(|N(a) intersect N(b)|, 2).
```

Each common-neighbor pair supplies two triangles sharing the central edge.
Different choices of central edge give different non-induced edge-subgraphs.
The optional sixth edge is allowed: a pure diamond contributes 1, K4 contributes
6, and K4 plus isolates still contributes 6. This is not induced counting or a
count of four-vertex sets. The oracle uses Python integer arithmetic.
ESCAPE calls this pattern `chordalcycles`: `easyFourCounter` in
`third_party/escape/Escape/FourVertex.h` accumulates `t_e*(t_e-1)/2` once per
oriented edge; `GetAllCounts.h` places it at `nonInd[9]`. The adapter exposes it
as `counts.connected_four["diamond"]` without invoking a Python substitute.

Input is the existing validated `SimpleGraph` on public IDs `0,...,n-1`.
The CLI reads `n m` followed by edges, deduplicates reversed/repeated edges,
checks unique m, rejects self-loops and preserves isolates. File loading and
raw m are simulator inputs, never a private release to the coordinator.

## Implemented protocol

Public inputs are n, B>=2, positive O/R/W allocations, and k-CoreD configuration.
B is required, fixed independently of the protected graph; there is no cap
selection stage. B may exceed n-1, in which case its declared scale still applies.
The implementation always executes these stages, including on small universes:

```text
spawn separate simulation RNG streams O, R, W
H = kcore_order(G, epsilon_O); pi = sort vertices by (H.level[v], public ID)
for every public unordered pair a<b:
    lower-ID endpoint reports R_ab using RR(epsilon_R), including nonedges
W_ab = -1/expm1(epsilon_R) if R_ab=0 else 1+1/expm1(epsilon_R)
b = 2(B-1)/epsilon_W
v = exp(epsilon_R)/expm1(epsilon_R)^2
VR = 2v+v^2; VW = 2b^2; lambda = VW/(VR+VW)
for each client c:
    S = first B actual later neighbors in pi order     # LOCAL ONLY
    for every ID-ordered pair a<b with pi(c)<min(pi(a),pi(b)):
        send Y_c,ab = 1[{a,b} subset S] + fresh Laplace(0,b)
for every central pair a<b:
    for each c != a,b:
        x_c = W_ac * W_bc
        if c is earlier than both a and b:
            x_c = lambda*x_c + (1-lambda)*Y_c,ab
    term_ab = W_ab * ((sum_c x_c)^2 - sum_c x_c^2)/2
return sum_ab term_ab
```

The schedule has exactly C(n,2) RR bits and C(n,3) wedge coordinates. Wedge
rows are indexed by client ID; each row lists its eligible pairs in public-ID
order. Even zero wedges are noised and transmitted. Later-pair eligibility
depends on the already released order, not actual edge or wedge existence.
Each pair has one RR draw, reused consistently everywhere it appears.

`aggregate_diamonds` accepts only `DiamondTranscript`, containing budget, cap,
the complete `KCoreTranscript` (thresholds, promotion messages and derived levels),
RR bits and noisy wedge rows. It reads no graph and uses no randomness.
Selected sets, exact indicators, degrees/counts, seeds and RNG state never enter
the transcript or aggregate result. The result includes only estimate, public
budget/cap/scale/weight and semantic/status labels. Negative and noninteger
estimates remain intact. There is no final Laplace step or count clipping.

## Budget and computational scope

The total is O+R+W; default is equal thirds, an initial setting, not a tuned split.
`DiamondBudget` rejects nonpositive/nonfinite allocations and requires
`math.fsum((O,R,W)) == total`, without a loose overspend tolerance. Exact
real-arithmetic equality is an ideal-model assumption, not certified by float
equality. See the privacy audit for this and other executable limitations.

The reused k-CoreD port requires O<=1; equal thirds therefore reject total>3.
Explicit allocations permit larger totals within existing simulator ranges,
e.g. total 4 with (1,1.5,1.5). **No allocation is silently redistributed.**
RR requires R<=30; geometric and float range checks can also reject parameters.
The hybrid ratio uses an algebraically equivalent scaled calculation to avoid
overflow; saturated/unrepresentable parameters cause an explicit error.

Beyond existing k-CoreD cost, RR takes O(n²) work/storage. The complete wedge
messages, their lookup tables and reconstruction take O(n³) work/storage,
plus local neighbor sorting O(sum_v d_v log(d_v+1)). Squared-sum reconstruction
avoids O(n⁴) enumeration without changing the estimator. B limits sensitivity
and local selection but does not reduce the full message schedule. k-CoreD's
round transcript additionally uses O(nr) storage. This implementation is for
manageable research graphs, not scalable distributed deployment.

## Targeted verification and use

```bash
.venv/bin/python -m pytest -q tests/test_diamond_exact.py tests/test_diamond_protocol.py tests/test_diamond_privacy_audit.py
.venv/bin/python -m pytest -q tests/test_kcore.py
.venv/bin/python scripts/reference_fingerprints.py --verify
.venv/bin/python scripts/estimate_diamonds.py data/fixtures/diamond.edges --epsilon 3 --cap 3 --seed 2460
.venv/bin/python scripts/estimate_diamonds.py data/fixtures/clique.edges --epsilon 4 --cap 3 --budget 1 1.5 1.5 --seed 2461
```

Observed on Python 3.11.16 / Ubuntu WSL: **49 diamond tests passed in 5.39s**;
**25 reused k-CoreD tests passed in 0.20s**, no failures/errors/skips. Actual GNU
ESCAPE compilation succeeded; all **14 native graphs** (eight existing fixtures
and six seeded random graphs) match the exact formula, independent four-set
enumeration and test-only noise-free reconstruction. Each native graph is
reconstructed under three orders and three weights. No deterministic option
is exposed by the simulator or CLI. Books with 0–6 outer vertices satisfy
C(k,2); all 64 four-vertex graphs pass the independent exact check.

The audit checks 79,872 neighboring full-vector cases, including additions,
deletions, both rank directions and tight cap replacement; all pass. See
[the audit](DIAMOND_PRIVACY_AUDIT.md) for independence, clipping and MSE reasoning.
The full prior regression suite was intentionally not run: existing mechanisms
are unchanged and this task requested targeted verification.

Small statistical diagnostics use 20,000 primitive samples and 600 full-protocol
trials on each of K4 and edgeless n=4, at explicit (O,R,W)=(1,4,4), B=3.
There was no budget search. K4 mean=6.0642049794, estimated SE=0.0660311592;
edgeless mean=0.0000035164, SE=0.0000034080. Both are within the predeclared
six-SE diagnostic threshold; respective negative counts are 1 and 315.
These checks are limited consistency evidence, not a privacy/unbiasedness proof
or a utility comparison. The single CLI examples emit -1.3171736750947745 and
-1.9531426197902977 unchanged.

Ignored evidence: `build/phase24/` holds test logs, 14 native input/output JSONs,
statistical summaries, CLI outputs, environment, reference and preservation
receipts. `build/escape-pytest/build.json` and `compile.log` record the native
build. The supplied research reference and test seeds are source-controlled
research material; seeds must never accompany a protected deployment release.
Seeded **and unseeded** NumPy are simulations, not cryptographic randomizers.

**Stop here.** A separate authorization is required for the standardized diamond
experiment script and six-dataset evaluation. No such runner/study exists from
this task; no improved-accuracy claim is made.
