# Checkpoint 11 — Complete private four-path implementation

Date: **2026-11-05 (America/Vancouver)**.
Status: **COMPLETE — P4 Phase 3 stopping point reached; Phase 4 not started.**

## Authorization and preservation

Owner authorized the complete five-stage private P4 simulator and focused
correctness/moment checks, not the 2025 baseline or full experimental study.
Read project instructions, README/pyproject, privacy/order/triangle documents,
checkpoints 09/10, API implementations and test/experiment conventions.
The working tree already contained uncommitted Phase 1/2 work; it was preserved.
Neither Phase 1 nor Phase 2 core code or tests required modification.

## Files created or modified

Created:

- `src/private_graphlets/four_path.py`
- `tests/test_four_path_protocol.py`
- `docs/FOUR_PATH_IMPLEMENTATION.md`
- `docs/status/checkpoints/11_private_four_path_implementation.md`

Focused updates: `README.md`, `docs/ALGORITHMS.md`, `docs/PRIVACY_NOTES.md`,
`docs/status/STATUS.md`. Earlier checkpoints and results remain historical.
No dependency/lock changes, setup scripts, system installations, reference
edits, privacy changes to existing algorithms, configurations, full experiments,
plots, commits or pushes.

## APIs and implementation

All APIs live in `private_graphlets.four_path`:

- `FourPathBudget(degree, ordering, rr, cap, count)`: explicit validated positive
  finite allocations, supported O/R domains, finite total property.
- `FourPathStreams(degree, ordering, cap, rr, count)` and
  `four_path_streams(seed=None)`: five stable SeedSequence children, no detectable
  bit-generator aliases. Existing four-stream APIs are unchanged.
- `local_degree_report(neighbors, epsilon_degree, rng)`: only a noisy scalar
  leaves the local function; calls existing sample_degree_noise with size=().
- `degree_product_estimate(noisy_degrees, weights)`: finite, dimension-checked
  all-unordered-pair postprocessing; no graph input or edge filtering.
- `simulate_four_paths_private(graph, *, budget, seed=None, streams=None,
  beta=.05, kcore_config=None) -> FourPathRun`.
- `estimate_four_paths_private` with the same arguments returns `FourPathResult`.
- `FourPathResult`, `FourPathTranscript`, `FourPathRun`: aggregate/public metadata
  and modeled privatized messages, never exact-evaluation fields.

Full signatures, fields and contracts are in `docs/FOUR_PATH_IMPLEMENTATION.md`.
No CLI or new experiment runner was added.

The driver runs degree reports, existing k-CoreD, existing private cap, one RR
collection and one rr_matrix construction. It passes that same object to both
the degree product and unchanged estimate_triangles_from_rr, then returns
Ahat-3*That. Standalone triangle entry points are not called. It retains negative
and fractional estimates. Five allocations sum without redistribution; RR is
charged once and degree-product postprocessing adds no query allocation.

## Mathematical and empirical evidence

Under ideal independent noise, degree-vector sensitivity is two, giving scale
2/D. Ahat is unbiased for the exact middle-edge degree product. The full ideal
mean is P4+3*(T-E[T_retained]), so truncation may produce positive bias.

For fixed G,O,B and t=d-1, s=8/D^2, h=exp(R)/expm1(R)^2 and
g_v=sum_{u in N(v)}t_u, tests check

```text
Var(Ahat) = s*sum g_v^2 + s^2*m + h*sum_{u<v}(t_u^2+s)*(t_v^2+s)
Cov(Ahat,That) = h*sum_{u<v} c_uv*t_u*t_v
Var(Phat) = Var(Ahat)+9*Var(That)-6*Cov(Ahat,That)
```

Deterministic moment integration enumerates all 64 RR transcripts and 16 degree
moment nodes on each of path/cycle/diamond/clique fixtures for caps 1,2,3 under
a fixed nontrivial order. Nodes +/-sqrt(s) match the Laplace moments through
degree two per variable, sufficient for these first/second/cross moments; they
are a quadrature device, not a substitute sampler. Independent count-noise
variance is included analytically. K4 cap 2 retains 2 triangles and gives
expected Phat=18 versus true P4=12. Uncapped cases recover original P4.

A separate 5000-trial seeded actual degree-noise/RR mean check uses a prechosen
six-analytic-standard-error tolerance. No seed tuning or full utility experiment.
Controlled injected-noise tests cover required graph fixtures and isolates;
spies verify exactly one RR sample/matrix call, object identity, no repeated
prior stages, epsilon_C calibration and immutable table preservation. Tests
also cover exact result/transcript field sets, replay, stream separation, alias
rejection, negative/fractional outputs, budgets, numeric overflow and scope.

This is deterministic/empirical implementation evidence plus ideal-model
derivations, not an independently reviewed privacy or worst-case RMSE theorem.

## Actual commands and outcomes

Fresh Phase 2 baseline:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

**501 passed in 20.49s**, 0 failures/errors/skips.

New Phase 3 tests:

```bash
.venv/bin/python -m pytest -q tests/test_four_path_protocol.py
```

**86 passed in 0.35s**, 0 failures/errors/skips.

Targeted Phase 3/2/1, RR, cap/orientation and k-CoreD regression:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_four_path_protocol.py tests/test_triangle_protocol.py tests/test_four_path_exact.py tests/test_four_clique_core.py tests/test_four_clique_protocol.py tests/test_kcore.py
```

**301 passed in 4.61s**, 0 failures/errors/skips, including actual ESCAPE exact
fixture comparisons. Existing Phase 1/2 tests are unchanged.

Final full regression:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

**587 passed in 19.42s**, 0 failures/errors/skips. This includes existing bounded
statistical unit checks and native ESCAPE integration. No test failures occurred
in this phase; no test was weakened or skipped to obtain a pass.

Preservation checks:

```bash
.venv/bin/python -B scripts/reference_fingerprints.py --verify
git diff -- src/private_graphlets/three_star.py src/private_graphlets/kcore.py src/private_graphlets/randomized_response.py src/private_graphlets/four_clique.py src/private_graphlets/four_clique_baseline.py src/private_graphlets/four_clique_experiments.py third_party pyproject.toml requirements.lock experiments/configs
git diff --check
git status --short
```

All three pinned references verified, clean, exit 0. Protected tracked-source
diff was empty. Whitespace check passed. Phase 1/2 modules and tests were left
unchanged by this phase. Final Git status lists only the eight intended Phase 3
files above; earlier pending files no longer appear relative to the current HEAD.
No Git commit or push was performed by this implementation task.

## Complexity and unresolved limitations

Expected computational cost, under constant-cost numeric/sampling operations and
expected O(1) membership, is
`O(n+r(n+m)+n log n+n^2+m log(1+D_max)+nB^2)`.
This includes O(n) degree releases, final order sorting, O(n+m) cap scans, dense
RR and product work, triangle table validation, outgoing sorting and pair scores.
Memory including graph, dense temporaries and modeled transcript is
`O(n+m+n^2+nr)`. No low-out-degree utility guarantee is assumed.

RR uploads are O(n^2) bits, while distribution of the complete matrix to all
clients can require O(n^3) delivered bits. Degree/cap/count each send n scalars;
ordering has thresholds and O(nr) promotion bits plus feedback dissemination.
Physical distribution and protected table access are not implemented, so no
O(n^2) end-to-end communication claim is made.

All outputs are experimental_unverified. Full adaptive composition, finite
arithmetic/error behavior, PRNG privacy, timing/access leakage, client isolation
and independent mathematical review remain unresolved. The n<=1000 simulator
and inherited numeric guards remain. Truncation bias and shared-RR covariance
must be retained in future accuracy evaluation; conditional fixed-cap formulas
alone do not describe unconditional MSE with random order/cap.

Ready for separately authorized Phase 4 accuracy evaluation at research-simulator
scope. **Stop here: no Phase 4 study, 2025 baseline, plots, commit or push.**
