# Checkpoint 09 — Exact P4 and triangle counting

Date: **2026-11-05 (America/Vancouver)**.
Status: **COMPLETE — P4 Phase 1 stopping point reached.**

## Authorization and preservation

The owner authorized exact counting, correctness tests and ESCAPE validation;
no private P4 or modified EdgeOrientDelta implementation was authorized.
This is project checkpoint 09, corresponding to the owner's P4 **Phase 1**.
Read AGENTS.md, STATUS.md and checkpoint 08 before editing, plus README,
pyproject.toml, graph/exact/escape implementations, fixtures/tests and relevant
SOURCE_REVIEW/ESCAPE_VALIDATION documentation. Starting Git status was clean.

## Files and APIs

Created:

- `src/private_graphlets/triangle_exact.py`:
  `count_triangles(graph: SimpleGraph) -> int`.
- `src/private_graphlets/four_path_exact.py`:
  `count_four_paths(graph: SimpleGraph) -> int` and
  `count_four_paths_bruteforce(graph: SimpleGraph) -> int`.
- `tests/test_four_path_exact.py`: 38 collected tests, including eight native
  ESCAPE fixture comparisons and six exhaustive graph-size parameter cases.
- `docs/status/checkpoints/09_exact_four_path_triangle.md` (this record).

Updated `README.md`, `docs/ALGORITHMS.md`, `docs/ESCAPE_VALIDATION.md` and
`docs/status/STATUS.md`. Corrected the obsolete algorithms-document introduction
while retaining historical reports/checkpoints. No existing package modules,
private mechanisms, budgets, configurations, fixtures, dependency pins, lock,
reference sources or gitlinks were edited. No CLI was added.

## Correctness and complexity

Triangles are counted by adjacency intersections with `u < v < w`; each
triangle contributes exactly once. The P4 formula sums `(d(u)-1)*(d(v)-1)`
once per undirected middle edge and subtracts `3*T`. The only repeated-vertex
choices have identical outer vertices, one per edge of each triangle. Extra
edges are allowed, so this counts non-induced copies, not induced vertex sets.
The independent oracle enumerates distinct ordered quadruples and tests their
three consecutive edges, dividing by two for reversal. It calls neither the
formula nor triangle counter. All arithmetic is Python integer arithmetic.

With n vertices, m edges, maximum degree D and expected O(1) set membership:

| Function | Graph-dependent time | Worst-case time | Auxiliary space |
|---|---|---|---|
| `count_triangles` | O(n+m+sum over edges min(d(u),d(v))) | O(n^3) | O(1+D) |
| `count_four_paths` | Triangle cost plus O(n+m) | O(n^3) | O(1+n) |
| `count_four_paths_bruteforce` | Enumerates n falling-factorial 4 quadruples | O(n^4) | O(1+n) |

Bounds exclude the existing O(n+m) graph and assume unit-cost integer arithmetic.
Big-integer operations depend on bit length. `permutations` stores an input
pool/indices; it does not materialize all quadruples. Intersections are temporary.

## Actual commands and results

Environment checks:

```bash
.venv/bin/python --version
.venv/bin/g++ --version
```

Observed Python **3.11.9** and GNU **GCC 16.2.0**. No environment installation,
dependency download, OS change or setup script was run.

Targeted new exact, existing graph, adapter and native integration tests:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_four_path_exact.py tests/test_graph.py tests/test_escape.py tests/test_escape_integration.py
```

**168 passed in 3.58s; 0 failed, 0 errors, 0 skipped.** All 38 new tests ran.
Exhaustive tests enumerate all **1,100** simple labeled graphs on 0–5 vertices,
comparing P4 formula/oracle and triangles against independent triple enumeration.
Other tests cover eight named fixtures, isolates, relabeling, repeated calls,
immutability, non-induced edge additions, reversal normalization and K0–K5/K8.

Full regression, also executing native integration:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

**430 passed in 18.49s; 0 failed, 0 errors, 0 skipped.** This includes existing
bounded statistical unit tests; no new statistical experiment was launched.
The combined targeted/full runs satisfy the requested integration checks without
a redundant additional standalone integration run.

Reference preservation:

```bash
.venv/bin/python -B scripts/reference_fingerprints.py --verify
git diff --check
git status --short
```

Fingerprint command exited 0: all three pinned references verified and clean.
Whitespace validation exited 0. Final Git status contains only the eight intended
source/test/documentation files listed above. No commit or push.

## Actual ESCAPE evidence

The unchanged session fixture compiled original bundled source using GNU g++
into `build/escape-pytest/count_four`, then executed it on all eight fixtures.
Both P4 implementations agree with `connected_four["3-path"]`, and triangles
agree with `three_vertex[3]` on every fixture:

| Fixture | P4 | Triangles |
|---|---:|---:|
| edgeless | 0 | 0 |
| star | 0 | 0 |
| path | 1 | 0 |
| tailed_triangle | 2 | 1 |
| cycle | 4 | 0 |
| diamond | 6 | 2 |
| clique | 12 | 4 |
| clique_with_isolates | 12 | 4 |

Native input, raw `out.txt`, stdout/stderr and separately named Python/native
counts are retained in eight ignored `build/phase09/escape/<fixture>.json` files.
Compiler command/log/source hashes and binary hash are in
`build/escape-pytest/{compile-command.json,compile.log,build.json}`.
The final build records **13 upstream compiler warnings**; compilation and
comparisons succeeded. Warnings were not suppressed or upstream sources edited.
These generated artifacts may be overwritten by subsequent test runs.

## Limitations and next step

No failed or skipped checks occurred in this phase; no unresolved counting
correctness issue was observed within the tested scope. The brute-force oracle
is for small graphs, and dense triangle counting has cubic worst-case work.
The unchanged ESCAPE adapter retains its 1,000-vertex and numerical guards.
Go/notebook execution and utility experiments were not run or needed here.

The exact counters and bounded native validation are ready to support a later
modified EdgeOrientDelta development phase. This does not establish privacy,
accuracy or utility of any private estimator. **Stop here: Phase 2 requires a
new instruction and has not begun.**
