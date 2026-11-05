# Checkpoint 10 — Modified EdgeOrientDelta triangle protocol

Date: **2026-11-05 (America/Vancouver)**.
Status: **COMPLETE — P4 Phase 2 stopping point reached; Phase 3 not started.**

## Scope and starting state

Owner authorized the modified triangle component only, including sensitivity
analysis, tests and documentation. Read AGENTS.md, README, pyproject.toml,
PRIVACY_NOTES, KCORED_INTEGRATION, FOUR_CLIQUE_IMPLEMENTATION, status/checkpoint
09, Python APIs/tests and the pinned Go triangle-counting-ldp.go source.

The working tree already contained the eight uncommitted Phase 1 files recorded
in checkpoint 09. They were preserved; README, ALGORITHMS and STATUS receive
additional Phase 2 documentation. No existing algorithm or reference was edited.

## Files

Created:

- `src/private_graphlets/triangle.py`
- `tests/test_triangle_protocol.py`
- `docs/TRIANGLE_PROTOCOL.md`
- `docs/status/checkpoints/10_modified_triangle_protocol.md`

Updated in this phase: `README.md`, `docs/ALGORITHMS.md`,
`docs/PRIVACY_NOTES.md`, `docs/status/STATUS.md`.

Existing Phase 1 counters/tests/checkpoint and ESCAPE validation text were not
rewritten. No dependency changes, setup scripts, lock regeneration, upstream
changes, configurations, full experiments, plot generation, commits or pushes.

## Implemented interfaces and behavior

`TriangleBudget(ordering, cap, rr, count)` validates explicit positive finite
allocations and supported ordering/RR ranges; total is their finite sum.
`TriangleStreams` names independent simulation domains. `triangle_streams`
reuses the existing seeded stream constructor without modifying it.

Path A: `estimate_triangles_from_rr(graph, order, cap, weights, *, epsilon_rr,
epsilon_count, rng)` accepts a validated immutable canonical RR table and prior
order/cap. It runs no ordering, cap or RR mechanism. Result scope is count-only;
epsilon_rr is provenance and is not charged again. Caller must establish input
transcript provenance and account for previous releases.

Path B: `simulate_triangles_private(graph, *, budget, seed=None, streams=None,
beta=.05, kcore_config=None)` reuses kcore_order, its `(level,ID)` order,
local_cap_report/cap_from_reports and exactly one sample_rr_upper/rr_matrix
transcript before calling Path A. `estimate_triangles_private` returns only
its aggregate result. Full signatures and all result/transcript classes are
documented in `docs/TRIANGLE_PROTOCOL.md` and typed in the module.

`triangle_local_score` selects genuine outgoing prefixes and sums unordered
closing-edge weights. `triangle_sensitivity` calculates the range-aware bound;
`triangle_local_report` adds calibrated noise before returning any client
message. `aggregate_triangle_reports` sums only finite already-noised reports.
Low-level kernels have explicit validated-context preconditions like existing
clique kernels; the full Path A entry validates the dense context once.

## Mathematical analysis and test interpretation

Hold previous ordering/cap/RR transcript fixed. Only the earlier endpoint's
outgoing list changes under an undirected edge change. Insertion/deletion below
the cap changes <=B-1 terms, each magnitude <=M. Full-cap replacement changes
<=B-1 differences, each magnitude <=M+a. Thus Delta=(B-1)(M+a) for B>=2,
zero for B<=1. The B=2, epsilon_R=log(2) example changes -1 to 2 and attains 3;
calibration using only M=2 would fail. This derivation covers both weight signs.

Under ideal independent RR/count randomization, conditional expectation given
G,O,B equals retained triangles. This is not expectation conditioned on fixed
RR bits as well. K4 with B=2 retains 2 instead of 4. No truncation correction or
clipping is applied. Full O+D+R+C adaptive composition remains subject to review;
tests and budget objects are not a formal LEDP proof.

Deterministic tests cover every n=4 total order/root/incident list/single-edge
change/cap and all assignments of that root's relevant closing RR bits. Other
bits/private edges cannot affect the root score. Separate graph-level tests
enumerate all 64 n=4 graphs, six toggles and 24 orders to check only the earlier
endpoint changes. Expectation tests enumerate all 64 RR transcripts for all
64 graphs, two orders and all four caps. Seeded mean tests use 3000 draws each
on capped/uncapped K4 with six analytic standard errors and shared-RR covariance.
These are bounded unit checks, not full utility experiments or privacy proofs.

Other tests verify prior-stage non-invocation, immutable input tables, count noise
before aggregation (including zero-score clients), negative estimates, schemas,
small/empty graphs, alias rejection, stable named streams, one RR draw stage per
invocation, cap underestimation, and budget/parameter/numerical guards.

## Actual commands and outcomes

Pre-change baseline (fresh execution, not historical assumption):

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

**430 passed in 19.32s**, no failures/errors/skips.

Initial new-test run:

```bash
.venv/bin/python -m pytest -q tests/test_triangle_protocol.py
```

**69 passed in 0.84s**, no failures/errors/skips. Subsequently added explicit
total-budget overflow handling and two scope/cap-underestimation tests.

Final targeted new/existing RR, ordering, cap/orientation and Phase 1 tests:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_triangle_protocol.py tests/test_four_clique_core.py tests/test_four_clique_protocol.py tests/test_kcore.py tests/test_four_path_exact.py
```

**215 passed in 4.35s**, no failures/errors/skips, including all **71** final
triangle tests and actual ESCAPE Phase 1 fixture comparisons.

Final full regression:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

**501 passed in 19.61s**, no failures/errors/skips. Existing bounded statistical
tests ran as part of regression. No full P4 experiment was run.

Preservation and whitespace:

```bash
.venv/bin/python -B scripts/reference_fingerprints.py --verify
git diff -- src/private_graphlets/three_star.py src/private_graphlets/kcore.py src/private_graphlets/randomized_response.py src/private_graphlets/four_clique.py src/private_graphlets/four_clique_baseline.py src/private_graphlets/four_clique_experiments.py third_party pyproject.toml requirements.lock experiments/configs
git diff --check
git status --short
```

Fingerprint command exited 0, all three pinned references verified with clean
statuses. Protected-source diff was empty. Whitespace check passed. No test
failure occurred. One documentation patch initially failed context matching;
it applied no changes and was retried successfully with the actual heading.

## Complexity, limitations and next step

For outgoing degree q_v and retained size s_v=min(B,q_v), selection scans true
adjacency and sorts q_v neighbors; score work is sum choose(s_v,2). Path A costs
O(n^2+n+m+sum q_v log(1+q_v)+nB^2), including dense table validation, with O(n^2)
peak validation temporaries and O(n) output reports. Path B adds k-CoreD
O(r(n+m)) work/O(nr) transcript storage, O(n log n) final order, O(n+m) cap
work and O(n^2) RR generation/storage. These assume expected O(1) hash membership
and constant-cost arithmetic/sampling; r is the executed bounded round count.
See the focused document for graph-dependent bounds and distinct communication
costs, including potential O(n^3) table dissemination to all clients.

No unresolved tested correctness issue was observed. Unverified matters remain:
full adaptive transcript privacy, finite arithmetic and failures, noncryptographic
PRNGs, actual client isolation, timing/table access leakage and low-out-degree
utility. External matrix/order/cap provenance and RNG independence are caller
obligations; validation cannot certify them. Dense n<=1000 and existing numeric
guards remain; low-level raw score APIs are sensitive internal computations.

The reusable triangle component is ready for Phase 3 engineering subject to these
research qualifications. **Do not start Phase 3 automatically.** No degree-product
mechanism, complete private P4 estimator or 2025 baseline was implemented.
