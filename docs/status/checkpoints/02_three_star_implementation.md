# Checkpoint 02 — Non-induced 3-star implementation

Date: **2026-10-28** (America/Vancouver).
Outcome: **implemented and verified; stopped at the requested boundary**.

## Scope and starting state

The user explicitly authorized exact and private non-induced 3-star counting,
an independent small-graph oracle, graph validation, CLI/output schemas,
automated tests, and algorithm/privacy documentation. This supersedes the phase
01 stop for that scope only. No ESCAPE integration, large experiments, orientation
implementation, other graphlet estimator, or 4-clique development was started.

Read `AGENTS.md`, `docs/SOURCE_REVIEW.md`, `docs/status/STATUS.md` and checkpoint
01 before implementation. The initial worktree was clean at commit
`f34984478e0d0275ea4372eb1a0378c10c729d86` (`Initial Environment Setup`).
Phase 02 changes are local and uncommitted; no Git commit or push was performed.
Historical checkpoint 01 was preserved.

## Completed implementation and files

| File | Main functions / change |
|---|---|
| `src/private_graphlets/graph.py` | Immutable `SimpleGraph`, `from_edges`, `parse_edge_list`, `load_edge_list`; symmetry/ID/loop/count validation and undirected deduplication. |
| `src/private_graphlets/exact.py` | `count_three_stars` with `math.comb`; independent `count_three_stars_bruteforce` over 4-sets and candidate centers. |
| `src/private_graphlets/noise.py` | `validate_epsilon`, `laplace_scale`, `make_rng`, `sample_degree_noise`; NumPy Generator simulation with scale exactly `2/epsilon`. |
| `src/private_graphlets/three_star.py` | `corrected_local_stars`, `estimate_three_stars`, immutable `PrivateThreeStarResult` and `to_dict`; aggregate-only release boundary. |
| `src/private_graphlets/cli.py`, `__init__.py` | Updated scope/info; separate private and exact commands, JSON software metadata and error exits. |
| `tests/test_graph.py`, `test_exact.py` | Format/model checks and independent exact correctness validation. |
| `tests/test_noise.py`, `test_three_star.py` | Mechanism, parameter, negative-output, release-boundary and numeric checks. |
| `tests/test_statistics.py` | Analytic-SE Monte Carlo diagnostics and independent quadrature checks. |
| `tests/test_cli.py`, updated `test_smoke.py` | Installed CLI, exact/private separation, error behavior and environment smoke tests. |
| `docs/ALGORITHMS.md`, `docs/PRIVACY_NOTES.md` | Specification, APIs/formats, intended privacy assumptions/accounting and unresolved questions. |
| `README.md`, `AGENTS.md`, `experiments/README.md`, `docs/SOURCE_REVIEW.md` | Current usage/stopping rules; source review marked as historical phase 01. |
| `docs/status/STATUS.md`, this checkpoint, `docs/status/validation_02.json` | Current phase checklist, execution record and actual machine-readable diagnostics. |

Input contract: UTF-8 `n m` header followed by integer pairs, IDs in `[0,n)`.
`m` is the number of **unique** undirected edges after deduplication; reverse
duplicates must not inflate it. Loops are rejected. Blank lines and `#` comments
are accepted. The vertex count represents isolates, including edgeless graphs.

The estimator uses the user's formula unchanged: `b=2/epsilon`,
`Y_v=d(v)+Laplace(0,b)`, and `Y_v(Y_v−1)(Y_v−2)/6 − b²(Y_v−1)`, summed using
`math.fsum`. Every vertex, including isolates, contributes a separate draw.
There is no formula tuning, negative-value clipping, truncation or rounding.
Detected numeric overflow/nonfinite results and squared-scale underflow fail
explicitly rather than producing a replacement estimate.

Private records omit raw degrees, exact edge counts, exact star counts, report
vectors, seeds and RNG state. Exact evaluation has a separate command/record
type and is never called by the private path. Both seeded and unseeded NumPy
randomness remain simulation-only.

## Dependencies and environment

No dependencies were added, installed or upgraded. The existing `.venv` uses
CPython **3.11.16**, NumPy **2.2.6**, pytest **8.3.5**, and the 25 exact pins from
phase 01. `pip check` reported **No broken requirements found.** Installed
versions were compared against the unchanged `requirements.lock`.

Lock SHA-256 remains
`ffbb7a1cbe39daaaecba70d68bdd163d5e8e27bbf3a39f17a47f6e13fff6ed4f`.
Package metadata remains `private-graphlets 0.1.0`; use source revision/change
set as well as package version to identify this implementation. The starting
commit does not contain these uncommitted changes.

Consulted official NumPy 2.2 `Generator.laplace` and random-sampling documentation
for API parameterization and the simulation-only randomness limitation; links
are in the algorithm and privacy notes. No reference source was modified.

## Commands run

Read-only inspection used `cat`, `rg --files`, `git status --short`,
`git log -1 --format='%H %s'`, and `.venv/bin/python --version`.
Substantive verification commands, from the project directory:

```bash
mkdir -p build/phase02
.venv/bin/python -m pytest -q -rP --junitxml=build/phase02/pytest.xml > build/phase02/pytest.log 2>&1
.venv/bin/python -m pip check
.venv/bin/python -m build --no-isolation > build/phase02/package-build.log 2>&1
.venv/bin/python scripts/reference_fingerprints.py > build/phase02/references-after.json
git diff --check
.venv/bin/private-graphlets estimate-three-stars data/fixtures/star.edges --epsilon 2 --seed 123
.venv/bin/private-graphlets exact-three-stars data/fixtures/star.edges
```

Inline Python checks inspected wheel modules, compared all installed pins and
the lock hash, and compared reference fingerprints byte-for-byte. Parsed actual
JUnit XML and captured stdout into `validation_02.json`; values are rounded as
printed by tests. Status/docs links and source-distribution contents were checked
before finishing. Logs are under ignored `build/phase02/`; summarized evidence
and tests are project source files. The package build was repeated after final
documentation changes so the source archive contains current status files.

## Actual test results

**First complete run: 138 passed in 6.04s.** Zero failures, errors or skips. No
implementation correction or statistical-threshold relaxation was needed after
that run. The fixed simulation seeds were not changed in response to outcomes.

| Module | Passed cases |
|---|---:|
| `test_graph` | 39 |
| `test_exact` | 19 |
| `test_noise` | 22 |
| `test_three_star` | 25 |
| `test_statistics` | 17 |
| `test_cli` | 12 |
| `test_smoke` | 4 |
| **Total** | **138** |

Required exact values passed: empty graph 0, P4 0, K3 0, K1,3 1, K1,4 4, K4 4,
K5 20. Additional cases: seven isolates 0, adjacent overlapping centers 2,
K2,4 8, four-rim wheel 8, and disconnected K4 + star + isolates 5.
Both counters agreed on **all 1,100 labeled simple graphs through five vertices**.
Relabeling and leaf-edge tests distinguish non-induced counts.

The 17 statistical cases contain three noise-distribution cases, three variance
quadrature cases, three local empirical-mean cases and eight graph-level cases:

- Noise diagnostics: 200,000 disjoint pairs at each epsilon 0.5, 2 and 8.
- Local means: 200,000 samples per degree for degrees 0, 1, 2, 3, 4 and 9 at
  each epsilon 0.8, 2 and 8.
- Graph means: 12,000 calls to the **actual estimator API** per case, four tiny
  graphs and two epsilons (96,000 total calls).
- All **41** moment comparisons satisfied the preselected **6 analytic SE**
  bound. Maximum absolute standardized residual: **1.9530**, for degree 1 at
  epsilon 2 (observed mean 0.0159796301; expected 0; SE 0.00818196).
- The analytic local variance used for SEs was checked against separate
  symmetrized Gauss–Laguerre quadrature. Tolerances are not chosen from whichever
  empirical variance would make a run pass.

Graph-level means (synthetic unit tests, not utility claims):

| Graph | Epsilon | Exact | Observed mean | Analytic SE |
|---|---:|---:|---:|---:|
| Four isolates | 0.8 | 0 | -0.147289772 | 1.10555 |
| K1,4 | 0.8 | 4 | 4.11018708 | 1.27987 |
| K4 | 0.8 | 4 | 3.30599646 | 1.22851 |
| Overlapping centers + isolates | 0.8 | 2 | 2.80901729 | 1.58003 |
| Four isolates | 4 | 0 | 0.000577312808 | 0.0149459 |
| K1,4 | 4 | 4 | 4.01520656 | 0.0344811 |
| K4 | 4 | 4 | 3.96648081 | 0.0346777 |
| Overlapping centers + isolates | 4 | 2 | 2.01812258 | 0.0278679 |

These diagnostics are consistent with the specified moment calculation for the
tested cases; finite tests cannot prove unbiasedness, independence or privacy.
Six-SE margins are large-sample diagnostics, not exact Gaussian confidence
guarantees for the heavy-tailed cubic. Full rounded values: `validation_02.json`.

The private CLI example on public `star.edges` returned **2.2168852600487927**
at epsilon 2, seed 123; the separate exact command returned **1**. Both parsed
as JSON with distinct result types. This is a command check, not an accuracy
experiment. A deterministic test verified preservation of **-7.4765625**.

## Packaging, integrity and issues

- Wheel/source archive builds succeeded; the wheel contains `graph.py`,
  `exact.py`, `noise.py`, `three_star.py` and `cli.py`.
- Reference fingerprints remained identical: **82 ESCAPE** and **127 Go** tracked
  files and clean Git states. No reference executable/driver/setup/cleanup or
  integration was run in phase 02.
- No dependency/test failure occurred. `pip check` warned the default home pip
  cache is unwritable in the sandbox; it completed successfully with no download.
- Documentation patches initially failed context/format validation and made no
  changes; they were reapplied. This was unrelated to implementation/tests.
- Formal privacy/accuracy proofs remain pending. Fixed public vertices and
  two-endpoint budget accounting await independent review.
- NumPy is not a secure release RNG; the code simulates local computation in
  one process, with no secure transport, client isolation or privacy ledger.
- Float64 precision, heavy tails, numeric failure transcripts and secure
  finite-precision sampling remain open. No results are silently clipped or
  replaced at extreme parameters.

## Stop and next steps

**Stop condition satisfied.** Exact counting, the specified simulation, automated
verification and documentation are complete. Wait for explicit next instructions;
do not start ESCAPE integration, larger utility experiments, 4-clique estimation
or other algorithms. Independent mathematical review is pending. A later
authorized phase needs checkpoint 03 and an updated status checklist.
