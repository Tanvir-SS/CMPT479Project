# Phase 06 mathematical review package — integrated 4-clique prototype

2026-10-29. **Implementation/integration succeeded; formal privacy proof remains
unresolved.** The software is a research simulator labeled
`experimental_unverified`. No claim of executable LEDP, a guaranteed private
low-out-degree bound or accuracy superiority is made. Existing 3-star algorithms,
tests, saved results and historical checkpoints are preserved.

## 1. What is implemented

Exact non-induced/unlabeled K4 counters (oriented triples and independent
four-sets); one-owner pair RR; stable outgoing-neighbor caps; replacement-aware
local noise; fixed-order and actual noised k-CoreD protocol paths; a six-factor
RR baseline; CLI commands; tests; a reproducible 8-graph exploratory comparison,
raw/summary CSVs, actual ESCAPE output and plots. There is no hidden degree-sort
fallback. A separately named noise-disabled ordering control is non-private.

Read [FOUR_CLIQUE_IMPLEMENTATION.md](../FOUR_CLIQUE_IMPLEMENTATION.md),
[KCORED_INTEGRATION.md](../KCORED_INTEGRATION.md),
[FOUR_CLIQUE_EXPERIMENTS.md](../FOUR_CLIQUE_EXPERIMENTS.md) and the original
[phase-05 design](../FOUR_CLIQUE_DESIGN.md) alongside this handoff.

## 2. Exact files and functions

All modules below are under `src/private_graphlets/`:

- `four_clique_exact.py`: `count_four_cliques`, `count_four_cliques_bruteforce`,
  `validate_order`, `ranks`, `select_outgoing`, `validate_cap`.
- `randomized_response.py`: `rr_parameters`, `local_rr_row`, `sample_rr_upper`,
  `rr_matrix`. These supply exactly one upper-triangular report per pair.
- `kcore.py`: `KCoreConfig`, `degree_threshold`, `promotion_bit`,
  `symmetric_geometric`, `_run_levels`, `kcore_order`, `KCoreTranscript`,
  `ordering_budget_ledger`, separate `nonprivate_kcore_oracle`.
- `four_clique.py`: `CliqueBudget`, `allocate_budget`, `simulation_streams`,
  `conditional_sensitivity`, `local_cap_report`, `cap_from_reports`,
  `local_score`, `local_count_report`, `simulate_four_cliques`,
  `estimate_four_cliques`, `ProtocolTranscript`, `CliqueResult`.
- `four_clique_baseline.py`: `baseline_score`, `simulate_baseline`,
  `estimate_four_cliques_baseline`.
- `four_clique_experiments.py`: `run_experiment`, `execute_trial`, `aggregate`,
  `verify_results`, `plot_results`. This entire module is non-private evaluation.
- `cli.py`: additive exact/candidate/baseline entry points. Existing 3-star
  command branches and the underlying mechanism are preserved.

## 3. k-CoreD adaptation and audit

The attributed Python port follows Go commit
`b03da893ba1c38d3931708bac919562c5ab57963`, retaining degree-derived noised
thresholds, group/round formulas, noised same-level promotion counts, bias terms,
synchronous barriers and permanent stopping. It uses full final levels plus
public IDs. It does not reimplement a generic core-number heuristic and call it
k-CoreD. The MIT notice is included in the source distribution and wheel.

Differences from upstream: expose individual noised thresholds rather than
worker maxima; use NumPy difference-of-geometric simulation instead of the Go
secure utility; use Python integer arithmetic; validate parameters, handle
isolates and small n explicitly, and fail on numeric errors. A zero-noise oracle
is separate from private entry points. There are no random tie coins.
Go's empirical round/group constants differ from the displayed paper algorithm;
the port does not inherit its utility theorem without review.

With `lambda1=f*epsilon_O`, `lambda2=(1-f)*epsilon_O`, degree sensitivity is 1
per endpoint and the geometric parameter is `lambda1/2`. After publishing
threshold `t_v`, each eligible round's count has conditional sensitivity 1 and
geometric parameter `lambda2/(2*t_v)`. At most `t_v` queries occur per vertex;
both endpoints compose to at most epsilon_O in the proposed ideal argument.
Eligibility/stopping depend on those published thresholds and prior messages.
See the audit for exact formulas, code mapping and remaining proof obligations.

## 4. Complete modeled transcript and randomness

The coordinator sees each noisy threshold, every fixed-length promotion-bit
vector, derived levels/order, `Q_v` cap reports when used, released B, one RR
bit per unordered pair including nonedges, and each already-noised local scalar.
Ordering/cap broadcasts and final sum are derived from these same reports.
Raw degrees, adjacency, local unnoised counts, selected neighbors, sampled
noises, exact targets and seed/state are absent from this transcript.

The simulator dispatches client functions from one process holding the graph.
This is not secure isolation. Full-table dissemination is assumed; asking the
coordinator only for secretly selected pairs could reveal neighborhoods.
Timing, transport, malicious interaction and runtime access patterns are not
protected. The private result API emits the aggregate, budget/public parameters,
already-private cap and an explicit unverified status, not the full transcript.

`SeedSequence(seed).spawn(4)` separates ordering/cap/RR/count streams. Pair coins
are independent across distinct pairs; each geometric draw subtracts two fresh
geometric variates. Local count and cap noises are independent. Reused pair
reports induce covariance across terms. NumPy, including unseeded use, is not
certified cryptographic randomness. Published research seeds are not DP releases.

## 5. Formula, caps, sensitivity and all budgets

Let `pi=(level,ID)` or a declared public order, `O_v` the actual forward neighbors
and `S_v` their first B members in pi order. With `eta=epsilon_R`,

```text
p = 1/(exp(eta)+1)
R_ab = independent binary RR(A_ab, eta), owner=min(public_ID(a),public_ID(b))
W_ab = (R_ab-p)/(1-2p) in {-a,M}, a=1/expm1(eta), M=a+1
F_v = sum_{unordered {a,b,c} subset S_v} W_ab*W_ac*W_bc
Delta_B = 0 if B<3 else choose(B-1,2)*M^2*(M+a)
L_v = 0 if B<3 else F_v + Laplace(0,Delta_B/epsilon_C)
estimate = sum_v L_v
```

At fixed preceding transcript, one changed undirected edge changes only the
earlier endpoint's outgoing list. A prefix cap can replace one member; each
changed pair-of-common-neighbors term is bounded by `M²*(M+a)`. This is why a
unit-weight or insertion-only calibration is insufficient. Each vertex noises
its score before the coordinator receives it; vertices with no triples still
participate when B>=3. No estimate is clipped, rounded or truncated.

Noisy cap: `Q_v=|O_v|+Laplace(0,1/epsilon_D)`;
`B=min(n-1,max(0,ceil(max Q+log(n/beta)/epsilon_D)))`. Conditional degree-vector
sensitivity is 1. Always enforce B. Beta=.05 is a utility parameter, not DP delta.
Public/uncapped caps spend zero D; uncapped means B=n-1. Public n<4 returns
constant zero and runs no private stages.

For total e, defaults are:

| Mode | O | D | R | C |
|---|---:|---:|---:|---:|
| k-CoreD, noisy cap | e/4 | e/4 | e/4 | e/4 |
| k-CoreD, public/uncapped | min(e/3,1) | 0 | (e-O)/2 | (e-O)/2 |
| fixed, noisy cap | 0 | e/3 | e/3 | e/3 |
| fixed, public/uncapped | 0 | 0 | e/2 | e/2 |
| six-factor baseline | 0 | 0 | e | 0 |

K-CoreD's internal f=.5 split is **within O**, not another total-epsilon call.
The ordering parameter is limited to O<=1; explicit custom budgets are validated.
Conditional composition must cover the entire transcript for every history,
not only a favorable ordering/cap event. This ideal argument still needs
independent review and does not certify the actual samplers/numerics.

Uncapped ideal expectation is K4. A capped estimator targets the retained
cliques, not necessarily all original cliques. Saved synthetic diagnostics
record both. Shared RR products can produce quadratic-in-root-count variance
even at maximum out-degree 3. See the phase-05 covariance derivation.

## 6. Baseline and actual evidence

The baseline sums six adjusted RR factors over every `a<b<c<d`, spends the
**same total epsilon** entirely on one-owner RR, and adds no count noise. It is
the canonical undirected specialization inspired by AISTATS 2025 Algorithm 1,
not a byte-for-byte reproduction of the authors' notebook. Its expectation was
checked on every one of the 64 labeled four-vertex graphs by enumerating reports.

- Full suite: **376 passing tests**, no failures/skips on the corrected run.
  All 256 previous tests remain unchanged and pass; 120 new tests cover the
  prototype. **43 marked ESCAPE integration cases** are included.
- Initial fixed-order stage: 50 passed. Initial k-CoreD stage: 25 passed.
  A CSV dtype verification issue caused one initial full-suite failure and was
  fixed; its values/formula/tolerances were not adjusted. The checkpoint records
  exact commands, timings and subsequent runs.
- Phase-05 exact recheck: **1,112 graphs**, **124,542 orders**, **10,240 finite
  sensitivity cases**, all pass against actual ESCAPE where applicable.
- All **8 experiment graph counts** agree with actual ESCAPE, both independent
  exact implementations and the separate noiseless k-CoreD control. Every
  realized order also satisfies the uncapped identity in the evaluation driver.
- **16,000 trials**, **160 cells**, 100 independent trials per graph/epsilon/method;
  every saved estimate and non-timing diagnostic replays exactly. All eight
  PNG/PDF plot hashes match regeneration from saved CSVs.

The observed candidate RMSE exceeds baseline in all 32 graph–epsilon comparisons
for each oriented configuration. Noisy caps equal n-1 in 92.0625% of their trials;
cap 3 causes severe target loss on dense graphs. All 7,326 negative estimates
remain; 60 cells have undefined relative error. These are preliminary descriptive
observations. With 100 trials rare RR products can be poorly sampled: empty6,
epsilon 4 has ideal baseline SD 2.6587690e-5 but observed RMSE 6.4216166e-8.
No statistically established general ranking or utility theorem follows.

## 7. Output paths and reproduction commands

Raw/aggregate CSVs, exact configuration, actual ESCAPE output, source/build
provenance and original synthetic graphs:
`experiments/results/four_clique_phase06/`.
Figures and plot manifest: `plots/four_clique_phase06/`.
Compact intentionally retained observations: `docs/status/accuracy_06.json`.
Test/build/audit logs and the phase-05 recheck: `build/phase06/`.
Generated data/builds are ignored and must be transferred separately or recreated.

```bash
export ESCAPE_ROOT=/path/to/escape
bash scripts/setup.sh
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q -m escape_integration
.venv/bin/private-graphlets exact-four-cliques data/fixtures/clique.edges
.venv/bin/private-graphlets estimate-four-cliques data/fixtures/clique.edges \
  --epsilon 2 --seed 123 --ordering fixed --cap-mode uncapped
.venv/bin/private-graphlets estimate-four-cliques data/fixtures/clique.edges \
  --epsilon 2 --seed 123 --ordering kcore --cap-mode noisy
.venv/bin/private-graphlets baseline-four-cliques data/fixtures/clique.edges --epsilon 2 --seed 123
.venv/bin/python scripts/run_four_clique_experiments.py run
.venv/bin/python scripts/run_four_clique_experiments.py verify --replay
.venv/bin/python scripts/run_four_clique_experiments.py plot
.venv/bin/python scripts/analyze_four_clique_experiments.py
```

Existing result directories are not overwritten; select a new `--output` when
rerunning. `--escape-root` is an alternative to the environment variable.
The full suite already includes the marked ESCAPE tests; the separate selector
above is available for independent reproduction, not an additional test outcome.

## 8. Remaining issues and files to send for review

No unresolved observed test failure remains. Limits: dense communication/storage,
small synthetic graph scope, conservative cap/noise scales, cap bias, overlap
covariance, NumPy/float64/tail behavior, public numeric scope guards and error
transcripts, no secure client isolation, and an unproved adapted ordering-utility
bound. The port's ideal full-transcript accounting appears defensible under its
stated model; **independent proof review and executable privacy validation remain
outstanding**. The earlier Go code/paper is not proof of this implementation.

Give the independent researcher:

- This package, `docs/FOUR_CLIQUE_{DESIGN,IMPLEMENTATION,EXPERIMENTS}.md`,
  `docs/KCORED_INTEGRATION.md`, `docs/PRIVACY_NOTES.md`, `docs/SOURCE_REVIEW.md`,
  `docs/references.json`, `docs/status/{STATUS.md,accuracy_06.json}`, and all
  phase-06 internal/final checkpoints. Preserve phase-01–05 reports for context.
- Every new module listed in section 2 plus `graph.py`, `noise.py`, `escape.py`,
  `experiments.py` (shared synthetic generation/provenance), `cli.py`, and all tests.
- `scripts/{run_four_clique_experiments,analyze_four_clique_experiments,check_four_clique_design,reference_fingerprints}.py`,
  `experiments/configs/four_clique_phase06.json`, fixtures, setup script, Python
  version file, dependency lock/pins, packaging files and THIRD_PARTY_NOTICES.
- The generated result/plot directories, `build/phase06/escape/build.json`,
  test logs/XML and raw `design_recheck.json`, transferred separately.
- The pinned external reference files and the papers linked in the design/audit.

Review priorities: complete the interactive edge-privacy proof, audit numerical
randomizers and failure behavior, validate retained-target/variance arguments,
and determine whether a better justified cap/order/noise strategy can improve
utility. No such algorithm revision or expanded experimental grid was begun.
**Phase 06 ends here. Other patterns and another phase require explicit approval
through a follow-up instruction.**
