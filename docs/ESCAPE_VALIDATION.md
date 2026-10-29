# ESCAPE validation of non-induced 3-stars

Phase 03, **2026-10-28** (America/Vancouver). All **24 configured cases** agree
exactly across our Python degree formula, independent brute-force enumeration,
and the actual ESCAPE C++ executable. [validation_03.json](status/validation_03.json)
retains separate method values, raw reference output, canonical inputs, generator
parameters, compiler information and source/binary hashes. See the
[checkpoint](status/checkpoints/03_escape_validation.md) for commands and tests.
No full experiment grid or private 4-clique implementation was started.

## Reviewed source and build

Reference: ESCAPE commit `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3`.
The upstream README says to run `make`, then use
`wrappers/subgraph_counts.py <input> <3|4|5> [-i]`. The root Makefile builds
`Graph.o`, `GraphIO.o`, `TriangleProgram.o`, `libescape.a`, and executables.
`common.mk` selects C++11 and links `-lescape -lc++`; the latter is an unnecessary
platform-specific link requirement for our g++ build. The wrapper has relative
paths, shell invocation and induced conversion. We invoke the original C++
executable directly, without modifying or vendoring its source:

```bash
export ESCAPE_ROOT=/path/to/escape
.venv/bin/python scripts/validate_escape.py --output build/phase03/validation.json
.venv/bin/python -m pytest -q
# Explicit argument alternative:
.venv/bin/python scripts/validate_escape.py --escape-root /path/to/escape
.venv/bin/python -m pytest -q --escape-root /path/to/escape
```

The builder executes an argument list equivalent to:

```bash
g++ -std=c++11 -O2 -Wall -I "$ESCAPE_ROOT" \
  "$ESCAPE_ROOT/exe/count_four.cpp" "$ESCAPE_ROOT/Graph.cpp" \
  "$ESCAPE_ROOT/GraphIO.cpp" "$ESCAPE_ROOT/TriangleProgram.cpp" \
  -o build/escape/compile-<temporary>/count_four
```

After success it moves the binary to `build/escape/count_four`. Each builder call
compiles anew; reuse the adapter for multiple graphs. `build.json`,
`compile-command.json` and `compile.log` record provenance. Tests use
`build/escape-pytest/`. Compilation succeeded with g++ 11.4.0 and **160 upstream
warnings**, including `%lld`/`int64_t` mismatches and unused variables. These
were not suppressed or repaired. Both reference trees retain their recorded
tracked hashes and clean Git status. Build directories within the source tree,
including paths through symlinks, are rejected.

## Graph normalization and executable protocol

Our `SimpleGraph` enforces simple symmetric undirected adjacency with IDs
`0..n-1`. The loader accepts comments and deduplicates reverse/repeated edges
while requiring header `m` to equal the unique undirected edge count. Self-loops
and out-of-range endpoints fail before invoking ESCAPE.

The adapter emits ASCII `n m`, then exactly `m` sorted pairs `u v` with `u<v`,
once each, without comments. `GraphIO.cpp::loadGraph_Escape` inserts both
directions. Its input checks are weak, and its zero-vertex header sentinel does
not provide a reliable empty-vertex contract. We append isolates until `n>=4`.
Isolates cannot participate in connected four-vertex patterns, so all six
connected counts are preserved. Every case, including zero vertices, executes
ESCAPE; there is no fabricated zero shortcut. Reports record original and
normalized vertex counts. **Three-vertex and disconnected columns describe the
normalized graph**, and need not equal those of the original graph.

`count_four <absolute-input-path>` writes **out.txt in its working directory**,
plus diagnostic stdout. It returns success even if opening out.txt fails, so a
zero exit code alone is insufficient. Each invocation uses a fresh temporary
directory, checks the process and output, reads the result, then cleans up.
Concurrent calls cannot share stale output. The parser requires exactly 17
lines, matching headers, and finite nonnegative integral decimal counts:

ESCAPE sometimes prints `-0.000000` for a disconnected zero count on edgeless
graphs. This is accepted as integer zero. Strictly negative counts still fail;
this normalization is unrelated to private estimates, which remain unclipped.

| One-based output lines | Meaning |
|---|---|
| 1 | Normalized vertex count `n` |
| 2 | Adjacency entries **`2m`**, not undirected `m` |
| 3–6 | Four non-induced three-vertex counts |
| 7–17 | Eleven non-induced four-vertex counts |
| 12 | 3-star (`nonInd_four[5]`) |
| 13 | 3-path |
| 14 | Tailed triangle |
| 15 | 4-cycle |
| 16 | Diamond |
| 17 | 4-clique |

`GetAllCounts.h::getAllFour` gets stars from `FourVertex.h::easyFourCounter`,
which accumulates `d(d-1)(d-2)/6`. Our implementation uses Python `math.comb`;
the brute-force oracle examines four-vertex sets and each possible center,
checking the three required edges. ESCAPE and our formula are independent
implementations of the **same identity**, not independent mathematical
derivations. Enumeration provides a different counting procedure.

Although a source comment mentions induced conversion, `count_four` writes the
non-induced array directly. We never call the wrapper's induced conversion.
K4 returns `[4,12,12,3,6,1]` and K5 `[20,60,60,15,30,5]` in connected-column
order. Both have zero induced 3-stars but positive non-induced counts. Extra
leaf edges are allowed; copies are neither ordered embeddings nor just vertex
sets. Parsing existing clique columns is not development of a clique estimator.

## Python API and errors

```python
from private_graphlets.escape import EscapeAdapter, build_count_four
from private_graphlets.graph import load_edge_list

binary = build_count_four()  # ESCAPE_ROOT, or escape_root="/path/to/escape"
adapter = EscapeAdapter(binary)
graph = load_edge_list("data/fixtures/clique.edges")
count = adapter.count_three_stars(graph)  # integer 4, actually runs ESCAPE
run = adapter.run(graph)                 # another invocation, richer evidence
assert run.counts.three_stars == 4
print(run.counts.connected_four)
```

`EscapeConfigurationError`, `EscapeBuildError`, `EscapeExecutionError`, and
`EscapeOutputError` distinguish configuration, compilation, process and parsing
failures. Commands use subprocess argument lists without a shell. Defaults are
120 seconds to compile and 30 seconds per graph. Nonzero exits, timeouts,
missing output, invalid encoding, fractional/negative/nonfinite counts,
incorrect headers and unexpected output lengths fail explicitly. No error
path calls our counter to impersonate ESCAPE. The validation script writes a
failed report with completed comparisons and the error, then exits nonzero.

Counts must be below `2**53`, reflecting double output. The adapter also rejects
inputs above **1,000 vertices** to keep this phase in a conservative numerical
domain for the reviewed integer/double expressions. Decimal parsing cannot
repair upstream rounding or overflow. This is a guard, not a proof or performance
guarantee: behavioral validation here uses at most 12 vertices. Larger support
requires numeric review, not silently lifting the guard. Other revisions,
compilers/platforms and arbitrary external binaries have not been certified.
Arbitrary string labels require explicit preprocessing outside our loader;
they are not silently remapped. Source/binary hashes identify the tested build.

## Comparison cases

Every row records the same integer from all three methods:

| Graph | Agreed 3-star count |
|---|---:|
| Edgeless, 6 vertices | 0 |
| K1,3 | 1 |
| K1,4 | 4 |
| K4 | 4 |
| K5 | 20 |
| Path, 7 vertices | 0 |
| Two overlapping stars | 2 |
| Two disjoint stars plus two isolates | 2 |
| Zero vertices / one isolate / single edge / triangle | 0 each |
| ER, n=10, p=0.2, seeds 11 / 29 / 47 | 4 / 10 / 0 |
| ER, n=10, p=0.6, seeds 11 / 29 / 47 | 169 / 255 / 223 |
| BA, n=12, m=1, seeds 11 / 29 / 47 | 22 / 56 / 5 |
| BA, n=12, m=2, seeds 11 / 29 / 47 | 59 / 64 / 100 |

The **24 configured cases** comprise 12 named/boundary graphs, 6 ER and 6 BA.
Several boundary cases normalize to the same edgeless graph, but retain distinct
original vertex counts. Pytest also checks all six connected columns on eight
historical fixture files and four simultaneous calls. These regression/repeated
checks are separate from the 24-case total.

The optional original fixture command is
`.venv/bin/python scripts/check_escape.py --escape-root /path/to/escape`;
`--source` remains an alias. It now uses the same adapter. Without a root,
pytest explicitly skips 33 integration tests. A configured failure is an error.
The validation script always requires a checkout. Unit-test executable stubs
exercise errors only; they never enter the saved reference comparison report.

## Controlled epsilon diagnostic

Preselected: K1,4 and K5, epsilon **1, 2, 4**, **3,000 trials per cell**
(18,000 total), seeds 2026102804–2026102806 and 2026102814–2026102816.
Every trial invokes the existing estimator with a persistent NumPy Generator.
Its formula, noise scale, negative values and private result schema are unchanged.
Ground truth comes from actual ESCAPE output after all three counters agree.
Reports and sample files are **non-private synthetic evaluation**; truth and
seeds are never attached to private release records.

For `t=d-1`, `a=(3t²-1)/6`, the phase-02 variance identity is
`V(d,b)=2a²b²+(7t²-2/3)b⁴+14b⁶`. Independent vertex draws give graph variance
`Σ_v V(d(v),b)`. Mean checks use six analytic standard errors,
`SE=sqrt(Σ_v V/3000)`, chosen before observing results. This moment-based
diagnostic is not an exact Gaussian confidence guarantee for the heavy-tailed
cubic estimator. Sample variance need not closely match population variance
at this trial count.

| Graph | epsilon | Mean estimate | Exact | Mean z-score | Empirical MSE |
|---|---:|---:|---:|---:|---:|
| K1,4 | 1 | 4.795480 | 4 | 0.582972 | 4416.817937 |
| K1,4 | 2 | 4.366643 | 4 | 1.551917 | 169.066680 |
| K1,4 | 4 | 4.025934 | 4 | 0.376068 | 14.567210 |
| K5 | 1 | 16.753518 | 20 | -1.759120 | 8468.006126 |
| K5 | 2 | 19.953972 | 20 | -0.105646 | 546.175430 |
| K5 | 4 | 20.083543 | 20 | 0.556885 | 68.412908 |

All means pass; maximum absolute z-score **1.759120**. Observed MSE decreases
with epsilon on both graphs, consistent with decreasing noise scale. This
checks these fixed runs; it does not require each individual estimate to improve,
establish unbiasedness mathematically, or prove DP. Raw samples are in ignored
`build/phase03/epsilon_samples.json`; summaries and actual exact-reference output
are retained in the tracked JSON. The full epsilon experiment grid is deferred.
