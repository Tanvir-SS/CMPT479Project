# Source review: setup phase

Review date: **2026-10-28** (America/Vancouver). This is a source-level review
plus the small checks recorded in [checkpoint 01](status/checkpoints/01_setup_and_source_review.md).
It is not a security audit, a DP proof, or a reproduction of paper experiments.
No new private algorithm was implemented during phase 01. This document preserves
that review; phase 02 now implements the specified 3-star simulation, documented
in [ALGORITHMS.md](ALGORITHMS.md) and [PRIVACY_NOTES.md](PRIVACY_NOTES.md).

## Sources and scope

| Reference | Local read-only checkout | Reviewed commit |
|---|---|---|
| [ESCAPE](https://bitbucket.org/seshadhri/escape/) | `/home/tsshergi/escape` | `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3` |
| [DistributedLEDPGraphAlgos](https://github.com/mundrapranay/DistributedLEDPGraphAlgos/tree/b03da893ba1c38d3931708bac919562c5ab57963) | `/home/tsshergi/DistributedLEDPGraphAlgos` | `b03da893ba1c38d3931708bac919562c5ab57963` |

File paths and line numbers below refer to these commits. [references.json](references.json)
contains reviewed-file SHA-256 values, a digest of all tracked file contents, and
Git state. Both checkouts started clean; the final fingerprint comparison is
recorded in the checkpoint. Builds use this project's ignored `build/` directory.
ESCAPE's license is Apache-2.0; the Go repository's is MIT. Preserve their license
and attribution requirements if code is incorporated in a later phase; this
phase does not vendor upstream implementations into the Python package.

Primary research context: [ESCAPE, Pinar, Seshadhri and Vishal (2017)](https://www.cs.cornell.edu/courses/cs6241/2020sp/readings/Pinar-2017-ESCAPE.pdf)
describes exact small-subgraph counting. [Practical and Accurate Local Edge
Differentially Private Graph Algorithms, Mundra et al. (2025)](https://jshun.csail.mit.edu/LDP.pdf)
describes k-CoreD and EdgeOrientΔ. The implementation, not a presumed match to
the paper, is the basis of the detailed findings below.

## Counting conventions and identities

Assume a finite, simple, undirected graph: no loops or parallel edges, and four
distinct vertices per pattern. A **non-induced copy** selects the required edges;
extra host edges among the same vertices are allowed. An **induced copy** requires
the host's entire edge set on those vertices to equal the pattern. Counts here
are unlabeled copies, not raw injective embeddings. Dividing injective embedding
counts by the pattern's automorphism count gives the copy convention.

Let `d_v` be the full undirected degree, `T` the triangle count, `t_v` the number
of triangles containing vertex `v`, `t_uv = |N(u) ∩ N(v)|` for an edge `{u,v}`,
and `c_uv = |N(u) ∩ N(v)|` also for nonadjacent pairs. Then:

| Pattern | Non-induced identity | Automorphisms | ESCAPE `nonInd` index |
|---|---|---:|---:|
| 3-star `K1,3` | `Σ_v binom(d_v,3)` | 6 | 5 |
| 3-path `P4` (three edges) | `Σ_{uv∈E}(d_u−1)(d_v−1) − 3T` | 2 | 6 |
| Tailed triangle (paw) | `Σ_v (d_v−2)t_v` | 2 | 7 |
| 4-cycle `C4` | `(1/2) Σ_{u<v} binom(c_uv,2)` | 8 | 8 |
| Diamond / chordal cycle `K4−e` | `Σ_{uv∈E} binom(t_uv,2)` | 4 | 9 |
| 4-clique `K4` | Unique ordered clique enumeration, below | 24 | 10 |

The path identity selects the central edge and one additional neighbor at each
endpoint. The invalid choice where those two neighbors coincide occurs three
times per triangle, giving the subtraction. A tail attaches at one of the three
vertices of a triangle, outside that triangle. A diamond chooses two triangles
sharing its unique central edge; the potential sixth edge does not invalidate
that non-induced copy. A cycle has two opposite vertex pairs, explaining `1/2`.

For any consistent total vertex order, orient every edge forward. Writing `N+`
for out-neighbors, a clique identity is
`N_K4 = Σ_i Σ_{j∈N+(i)} |E(G[N+(i)∩N+(j)])|`:
the first two vertices of each clique select the shared forward neighborhood,
and its remaining edge completes the clique once. These are exact counting
identities, **not** formulas for plugging in arbitrary noisy degrees. In
particular, applying a nonlinear binomial function to an unbiased noisy degree
does not automatically produce an unbiased graphlet estimator.

The connected conversion matrix is useful for preventing convention mistakes.
Rows are non-induced counts; columns are induced types, in the order shown.
Each coefficient is the number of row-pattern copies inside one column-pattern:

| Non-induced / induced | Star | Path | Tail | Cycle | Diamond | Clique |
|---|---:|---:|---:|---:|---:|---:|
| Star | 1 | 0 | 1 | 0 | 2 | 4 |
| Path | 0 | 1 | 2 | 4 | 6 | 12 |
| Tail | 0 | 0 | 1 | 0 | 4 | 12 |
| Cycle | 0 | 0 | 0 | 1 | 1 | 3 |
| Diamond | 0 | 0 | 0 | 0 | 1 | 6 |
| Clique | 0 | 0 | 0 | 0 | 0 | 1 |

Thus `noninduced = M × induced`. `Escape/Conversion.h:92–103` implements the
corresponding backward substitution for connected four-vertex types; the Python
wrapper uses the full 11-type matrix. A K4's non-induced vector is
`(4,12,12,3,6,1)`, while its connected induced vector is `(0,0,0,0,0,1)`.
Neither convention counts only one arbitrary pattern per four-vertex set.

## ESCAPE function map

| File and location | Responsibility |
|---|---|
| `Escape/FourVertex.h:26–42` | Structures naming the six non-induced counts and the four easy counts. |
| `Escape/FourVertex.h:57–91`, `easyFourCounter` | Star, path, tail and diamond identities using degrees and triangle incidences. |
| `Escape/Triadic.h:124–171`, `betterWedgeEnumerator` | Enumerates two out-neighbors of a vertex; tests the closing directed edge by binary search; updates total, all three vertex counts and all three edge counts. |
| `Escape/FourVertex.h:133–182`, `fourCycleCounter` | Groups compatible directed two-hop wedges by their other endpoint and adds pairs of colliding wedges. Uses incoming and outgoing lists and ID comparisons to avoid duplicate cycles. |
| `Escape/FourVertex.h:295–351`, `fourCliqueCounter` | Builds common forward triangle ends for a directed edge, then finds edges among those ends. Uses binary search and an adaptive choice of which list to scan. |
| `Escape/GetAllCounts.h:66–107`, `getAllFour` | Fills all 11 non-induced four-vertex entries; connected outputs occupy indices 5–10. |
| `exe/count_four.cpp:12–54`, `main` | Loads, constructs CSR, relabels, orients, counts size 3 and 4, and writes `out.txt`. |

The `old...` functions in `FourVertex.h` are legacy alternatives and are not the
functions called by `getAllFour`. Although the comment above `getAllFour` mentions
conversion to induced counts, the body does not perform it. Its first five
entries concern disconnected non-induced patterns: empty edge set on four chosen
vertices, one edge plus two isolates, two disjoint edges, wedge plus isolate,
triangle plus isolate. In these entries “isolate” is a pattern role, not a
requirement that the host vertex has no extra edges.

### Orientation and preconditions

`Escape/Digraph.h:83–133`, `degreeOrdered`, orients `{u,v}` from smaller to larger
`(degree, vertex ID)`. `DegreeComp` at lines 21–41 implements that order. `CDAG`
stores CSR in-neighbor and out-neighbor lists. This is an acyclic **exact-degree**
orientation, not a private orientation and not the degeneracy peeling order.
Its maximum out-degree has the usual `O(sqrt(m))` bound: if a vertex has `q`
out-neighbors, its degree is at least `q` and those neighbors have degree at least
its degree, so `2m ≥ q²`.

The executable first calls `CGraph::renameByDegreeOrder` (`Graph.cpp:206–255`),
then `degreeOrdered`, then `sortById` on both directed lists. Relabeling makes
numeric IDs agree with the forward order. This matters: directed binary edge
searches and comparisons such as `k < i` in cycle enumeration rely on that
representation. Passing an arbitrary privately oriented graph straight into
these routines would be unsafe without preserving/reestablishing those
preconditions. `degreeOrdered` itself sorts its outlists with `DegreeComp`;
the executable's additional ID sorting is intentional.

`Escape/Digraph.h:146...`, `degenOrdered`, separately implements minimum residual
degree peeling (Matula–Beck style) and orients by removal times. The mathematical
degeneracy orientation has maximum out-degree at most the degeneracy. It is
**not called** by `count_four`; its implementation has a boundary concern below.

### Input and output contract

`GraphIO.cpp:19–74` reads an ESCAPE text file:

```text
4 3
0 1
0 2
0 3
```

The header is `n m` with the number of **undirected** edges; IDs must be integers
in `[0,n)`. List each distinct undirected edge once. Isolated vertices are
represented by `n`. Blank lines and lines starting with `#` are skipped. The
executable passes `undirected=1`, so the loader inserts both adjacency directions.

Run the binary with the input path as its first argument in a dedicated working
directory. Progress messages go to stdout. **`out.txt` in the current directory
is overwritten**, with exactly these 17 lines:

| 1-based lines | Contents |
|---|---|
| 1 | `n` |
| 2 | CSR directed adjacency entries, **`2m`**, not the input header's `m` |
| 3–6 | Four non-induced size-3 counts (empty, edge, wedge, triangle) |
| 7–17 | Eleven non-induced size-4 counts |
| 12–17 | The six connected counts, in the table's order |

Counts are formatted as `%f` after conversion to `double`. The wrapper
`wrappers/subgraph_counts.py` invokes the executable using `os.system`, reads
`out.txt`, applies matrix inversion and prints pattern name, non-induced count,
induced count, and induced/non-induced ratio. Its `-i` flag controls display;
it does not restore integer precision lost in floating point conversion.

### ESCAPE limitations observed in source

- `VertexIdx`, `EdgeIdx` and `Count` are `int64_t` (`Escape/Graph.h:10–12`).
  Intermediate products may overflow before division; the final `double` output
  cannot represent every integer above `2^53`. Tiny checks do not test scale limits.
- The loader does not validate `sscanf` results, ID bounds, duplicate edges or
  self-loops, and writes entries before checking too-few edges. Too many input
  edges can exceed allocated storage. A future adapter must validate first.
- `count_four` accesses `argv[1]` without checking `argc`, and returns success if
  `out.txt` cannot be opened. Check output existence and format, not only exit code.
- Several scratch arrays are allocated without release. Short-lived executable
  use limits impact; repeated in-process reuse would require ownership review.
- `degenOrdered` reads `verts_by_deg[deg_ptrs[min_deg]+1]` on removal, including
  the final iteration (`Digraph.h:205`); the final-iteration guard above it is
  commented out. This is an apparent out-of-bounds risk; that path was not run.
- `common.mk` links `-lc++` even though `CC := g++`. The local check invokes g++
  directly, avoiding a libc++ requirement without changing upstream files.
  Actual compilation emitted format warnings (`%lld` versus this platform's
  `int64_t`/`long`) and other upstream warnings; see the local compile log.
- The wrapper's shell command concatenation is unsuitable for arbitrary paths;
  our check uses subprocess argument lists and a separate directory per fixture.

## k-CoreD / EdgeOrientΔ Go source map

Names in the repository differ from the paper: the k-CoreD paths are
`KCoreLDPCoord` and `KCoreLDPTCount`; EdgeOrientΔ is `TCountCoord`. There is no
exported `EdgeOrientDelta` function. Source links at the reviewed revision:
[kcore-ldp.go](https://github.com/mundrapranay/DistributedLEDPGraphAlgos/blob/b03da893ba1c38d3931708bac919562c5ab57963/algorithms/kcore-ldp.go),
[triangle-counting-ldp.go](https://github.com/mundrapranay/DistributedLEDPGraphAlgos/blob/b03da893ba1c38d3931708bac919562c5ab57963/algorithms/triangle-counting-ldp.go).

### Private vertex levels

`data-structures/lds.go` stores one integer level per vertex, initially zero;
`GroupForLevel(r) = floor(r/g)` where `g` is `levels_per_group`.
`KCoreLDPTCount` (`kcore-ldp.go:202–267`) returns these levels for triangle
counting. `KCoreLDPCoord` (291–377) also converts levels to core-number estimates
and writes them to disk. `KCoreLDPRounds` reports round limits without performing
the full level protocol.

The following is a description of the **code**, including empirical choices:

1. For k-core call budget `εk` and split `f`, set `λ1=εk f`, `λ2=εk(1−f)`.
   It uses `g=ceil(log_(1+ψ)(n))/4` and a nominal round count
   `ceil(4 [log_(1+ψ)(n)]^1.2)`.
2. `loadGraphWorker` (57–92) adds symmetric geometric noise with parameter
   `λ1/2` to each degree. It subtracts a capped bias term computed using `λ1`,
   then adds one; the comment says “at least 2”, but the minimum is actually one
   for nonnegative bias factor. It derives the per-vertex round threshold
   `Rv = int(ceil(log2(noised_degree)) × g) + 1` and reports the worker maximum.
3. Each round, `workerKCore` (132–180) processes vertices still active at that
   round's level. It counts neighbors at that same level and, when noise is on,
   adds geometric noise with parameter `s=λ2/(2Rv)` and the additional integer
   bias `int64(6 exp(s)/(exp(2s)−1)^3)`. It sends a promotion bit if the result
   exceeds `int64((1+ψ)^group_index)`; otherwise the vertex stops permanently.
   It also stops at its degree-derived threshold.
4. Workers finish before `KCoreCoordinator.processData` (40–54) increments public
   levels. The loop runs up to `min(nominal_rounds−2, max_public_threshold)`.
5. `estimateCoreNumbers` (186–200), called with the hard-coded approximation
   parameter `lambda=0.5`, returns
   `2.5 (1+ψ)^max(floor((level+1)/g)−1,0)` for each vertex. This `lambda` is
   distinct from the geometric-noise parameters above.

Messages contain promotion vectors and threshold maxima; raw adjacency stays in
worker-local objects in the simulation. All workers and the coordinator are Go
goroutines in one process, with shared-memory access, not isolated network clients.
The code alone does not enforce a real-world local trust boundary.

### Out-degree selection, RR, and aggregation

`TCountCoord` (`triangle-counting-ldp.go:258–378`) first invokes k-core with
`ε/4`, then runs three worker stages with barriers:

| Stage | Functions and lines | Actual behavior |
|---|---|---|
| Edge RR | `randomizedResponse` 115–146; `workerRR` 148–169; `publishNoisyEdges` 58–74 | For each potential neighbor `j > vertex ID`, flip adjacency with probability `p=1/(exp(η)+1)`, where `η=ε/4`. Includes nonedges. Coordinator mirrors reports into a dense symmetric `[][]bool` matrix `X`. |
| Noisy out-degree bound | `workerMaxOutDegree` 171–208; `computePublicNoisyOutDegree` 88–101 | Keep neighbors at higher levels; for equal levels independently keep each neighbor with probability 1/2. Add geometric noise with parameter `ε/4` to each resulting degree; take worker maxima and then a global maximum, initialized at zero. |
| Local triangles | `workerCountTriangles` 210–256; `aggregateCounts` 76–86 | Recompute out-neighbor selection, sort IDs, retain the first `min(floor(B),degree)` neighbors, sum debiased RR values on their pairs, add Laplace noise per vertex, sum at workers, then sum at the coordinator. |

For true edge bit `A`, RR gives `E[X]=p+(1−2p)A`. Therefore

```text
Y = (X − p)/(1 − 2p) = ((exp(η)+1)X − 1)/(exp(η)−1)
E[Y | A] = A
Y(0) = −1/(exp(η)−1),   Y(1) = exp(η)/(exp(η)−1).
```

This elementary identity explains line 241. With one consistent total order,
no truncation, and suitable independence from edge RR, summing closing-edge `Y`
over genuine outgoing wedges counts each triangle at its earliest vertex in
expectation. It does not establish the correctness of the actual tie handling,
truncation or privacy mechanism, nor independence of all wedge terms: several
wedges can reuse the same reported closing edge.

The worker receives `η=ε/4` but calls Google's
`Laplace().AddNoiseFloat64(localTCount, 1, B, η/2, 0)` (line 244). Thus its API
epsilon argument is `ε/8`, with `l0Sensitivity=1`, `lInfSensitivity=B`, `delta=0`.
Under that API's parameterization the nominal noise scale is `8B/ε`. Merely
listing these arguments is not an endorsement of the supplied sensitivity or
of overall composition across both endpoints of a private undirected edge.

`noise/geometric.go` implements symmetric geometric integer noise using Google's
secure random utility. Ignoring finite-range truncation, its mass is proportional
to `exp(−λ|z|)`. The sampler uses an inverse-style binary search and accepts zero
only for one sign to avoid doubling its mass. It documents a lower parameter
bound for negligible truncation, but the constructor does not enforce it.
`noise/noise.go` is just a package declaration. RR and tie choices instead use
global `math/rand`; there is no recorded, user-controlled experiment seed.

`algorithms/rr-triangle-count.go:230...`, `TriangleCountingRR`, is a separate
baseline: it uses `loadGraphRR`, debiases all adjacency entries, and sums
`Y_ij Y_jk Y_ik` over `i<j<k`. Independent pairwise RR makes this algebra a useful
baseline idea, but its dense matrices and cubic triple loop limit scale. It is
not the outgoing-wedge algorithm above.

### Go formats and driver behavior

- `data-structures/graph.go:16–66`, `NewGraph`, reads whitespace-separated
  `vertex neighbor` lines **without an `n m` header or comments**. With
  `bidirectional=false`, it records only source rows; each vertex's complete
  adjacency must already be in its partition. With `true`, it inserts reverse
  adjacency. Repeated edges are not deduplicated by this loader.
- `vertex -1` represents an empty row only in the unidirectional mode. The
  bidirectional path also inserts a key `-1`, which downstream code cannot safely
  treat as a valid graph vertex. GraphSize is the number of map keys, not `maxID+1`.
- `scripts/graph_partitioner.py` constructs symmetric sets and assigns contiguous
  ID blocks. Worker offsets use `floor(n/workers)` and give the remainder to the
  final worker. Missing empty rows can break the array indexing assumptions.
  The partitioner has a hard-coded graph-size table and emits no row for an
  isolated vertex unless its input explicitly contains the negative sentinel.
- `cmd/main.go` takes `-config_file` and `-workers`, with config paths relative
  to `cmd/`. `experiments/experiments.go` loads YAML, but overwrites worker count
  with the CLI value, loops over hard-coded `epsilon=1.0` and `factor=0.8`, and
  writes beneath `/home/pranaymundra/results/` (lines 44–63).
- K-core outputs include `vertexID: estimate` and timing lines. Triangle output
  contains stage timings and `Triangle Count Approx: <float>`; it is not a CSV
  or ESCAPE-format result. Dataset/config names alone do not describe actual runs.

## Go implementation concerns and evidence

These concerns are source observations or mathematical deductions unless marked
as a runtime check. They are reasons to rederive and test future adaptations,
not declarations that a paper theorem is false.

1. **Inconsistent equal-level directions (confirmed in source).** Both endpoints
   flip their own coins, and degree measurement and triangle counting flip fresh
   coins. An edge can be selected by both endpoints or neither; cycles are also
   possible. There is no single DAG. Conditional on a triangle's vertices having
   equal levels, independent selections and no clipping give expected outgoing
   wedge total `3 × (1/2)^2 = 3/4`, rather than one. This is an analytic
   counterexample for that branch, not a measured experiment. The paper's
   Algorithm 3.1 instead specifies ordering by level and then vertex ID, and
   Algorithm 4.1 adds `12 log(n)/ε` to the noisy maximum; these steps differ from
   the checked code. See [the paper, Algorithms 3.1 and 4.1](https://jshun.csail.mit.edu/LDP.pdf).
2. **Clipping and calibration need analysis.** The code uses only the raw noisy
   maximum (floored at zero), without the paper's additive slack. It can fall
   below true out-degrees, truncation discards low-order-ID-dependent wedges, and
   the selections differ between stages. No unclipped unbiasedness claim follows.
   RR weights can exceed one in magnitude. Changing a genuine incident edge
   changes which weighted terms are included; sorting and replacement under
   clipping also matter. The `B` sensitivity argument must be rederived with the
   actual transcript, ownership convention, weights, and clipping rule. `B=0`
   and noise API errors also need explicit treatment.
3. **Configuration flags do not match all behavior.** `bias` is passed but not
   checked in the k-core bias calculations. `noise=false` skips k-core noise and
   RR in one stage, but out-degree noise, local Laplace noise, and random ties
   still occur; the RR inverse formula is then still used on unrandomized bits.
   Separately, `loadGraphRR` ignores its `noise` argument and always applies RR.
   This is not a reliable exact/no-noise comparison mode.
4. **Input and concurrency hazards.** Empty/short input lines panic at `values[0]`
   or `[1]`. Missing vertices or noncontiguous IDs can index beyond arrays sized
   by map length; invalid IDs may be logged and then processing continues.
   A worker with no rows gets an unbuffered channel; it sends before the
   coordinator's receive, while the coordinator waits for all workers first,
   causing a deadlock. Validate `n`, worker count, partition coverage and rows.
   LDS read locks are commented out; current round barriers separate reads and
   writes, so that alone is not evidence of a current data race. Changing that
   schedule would require synchronization review.
5. **Parameter and numerical hazards.** There are no comprehensive checks for
   positive epsilon, valid split, `n>1`, or positive grouping parameter. Zero
   degree with noise disabled feeds `log2(0)` into an integer threshold. Small
   geometric parameters make the extra-bias expression grow roughly as `s^-3`,
   risking integer overflow; large epsilon can overflow exponentials. No
   reproducibility or correctness guarantee follows outside analyzed ranges.
6. **Randomness and scale.** Secure geometric/Laplace sources coexist with
   noncryptographic global `math/rand` for RR. Map iteration and goroutine
   scheduling also affect draw assignment. This is unsuitable as-is for seeded,
   repeatable comparisons or a claimed production privacy mechanism. `X` is
   quadratic memory; RR visits all vertex pairs and uses linear membership
   search (`slices.Contains`), adding substantial work. Network-delay simulation
   statements are commented out, so timing is shared-memory timing.
7. **Separate RR k-core baseline defect.** `rr-baseline.go:148` ranges over an
   adjacency **matrix row's values** (`0` or `1`) and treats them as vertex IDs,
   repeatedly updating vertices 0/1 rather than actual neighbors. Its initial
   debiased degree loop also includes the fixed-zero diagonal. Do not use it as
   an unquestioned baseline. This defect is outside the main k-CoreD path.
8. **Error handling and modern toolchains.** Several callers print an error and
   continue with potentially invalid data; several use dynamic `fmt.Printf`
   format strings. Build/test behavior under the installed Go toolchain is
   recorded in the checkpoint. Successful compilation, especially with no
   upstream test files, cannot validate these algorithms.

## How these references support later work

ESCAPE provides a useful exact-count executable and algebraic specification for
small public fixtures and future ground truth, once input validation, integer
limits and order preconditions are addressed. Its exact degree orientation is
not a private preprocessing mechanism. Private core levels offer a candidate
way to reduce out-degree while exposing a controlled transcript, and the Go
coordinator shows the intended separation between local state and released
messages. Its RR algebra illustrates debiasing and why shared reports create
covariance between local terms.

For a later authorized phase, first fix the mathematical specification: public
vertex set, undirected-edge neighboring relation, which endpoint owns each RR
bit, which releases use both endpoints' data, total-order tie breaking,
clipping/bounds, and explicit budget composition. Establish exact small-graph
oracles, then derive unbiasedness/sensitivity/variance as appropriate before
coding private estimators. A successful smoke test supplies no formal privacy
claim. At the end of phase 01 this later work was deferred. See the current
[status](status/STATUS.md) for the subsequently authorized 3-star implementation;
no orientation or ESCAPE integration was added in phase 02.
