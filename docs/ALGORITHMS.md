# Implemented algorithms — 3-star counting

Only **non-induced 3-star counting** is implemented. Phase 02 implemented the
counters and simulator; phase 03 adds an independent ESCAPE reference adapter
and validation, described in [ESCAPE_VALIDATION.md](ESCAPE_VALIDATION.md).
No private 4-clique estimator or orientation algorithm has been added. The
[source review](SOURCE_REVIEW.md) records the exact-count identity also specified
by the user from ESCAPE Section 6, Theorem 5.

## Graph model and input contract

`private_graphlets.graph.SimpleGraph` is an immutable, validated adjacency tuple
on the vertex set `{0, …, n−1}`. All edges are undirected, with no loops or
parallel edges. `SimpleGraph.from_edges(n, edges)` adds both adjacency directions
and deduplicates repeated/reversed edges. The constructor also validates symmetry,
ID bounds and self-loops when adjacency is supplied directly. It copies mutable
rows into frozensets. Raw adjacency is input data, not a mechanism release.

`parse_edge_list(lines)` and `load_edge_list(path)` use this UTF-8 format:

```text
# Five declared vertices; vertex 4 is isolated.
5 3
0 1
0 2
0 3
1 0  # Duplicate of 0 1; permitted and ignored after deduplication.
```

The first non-comment record is `n m`, where `m` is the **number of unique
undirected edges after deduplication**, not the number of physical input rows.
Every subsequent record is exactly two integer IDs in `[0,n)`. Blank lines and
text after `#` are ignored. Header counts must be nonnegative, `m ≤ C(n,2)`, and
the observed unique edge count must equal `m`. Self-loops are rejected, not
silently removed. This means a header `5 4` for the example above is invalid.

The header supports isolated vertices without special edge sentinels. `0 0`
is the empty vertex set; `5 0` is five isolated vertices. Empty/headerless files,
fractional IDs, out-of-range IDs and malformed lines are errors. Input validation
and duplicate normalization are preprocessing of the simulator's sensitive input;
they do not constitute a private graph release. No raw input filename, edge
count, checksum or duplicate count is added to the private output.

## Exact counters (non-private evaluation)

`private_graphlets.exact.count_three_stars(graph)` implements

```text
S3(G) = Σ_v C(d(v), 3).
```

For each center, choose an unordered triple of distinct neighbors. Any edges
among those neighbors are allowed. Each selected center and leaf triple is one
copy; counts are not induced counts or raw embeddings. K4 has four copies and
K5 has twenty. Python's `math.comb` and integer summation avoid fixed-width
integer overflow. With constructed adjacency, counting takes O(n) degree queries
and O(1) auxiliary storage, apart from arbitrary-precision integer arithmetic.
Building the graph takes O(n+m) storage and expected O(n+input rows) work.

`count_three_stars_bruteforce(graph)` independently enumerates every four-vertex
subset, considers each of its four vertices as center, and directly tests the
three required edges. It never calls the degree formula. Extra leaf edges do
not invalidate a copy. Its O(n^4) work is appropriate only for small graph tests.
Neither exact counter is called by the private estimator.

## Noise and local correction

`private_graphlets.noise.validate_epsilon` requires a finite positive real
scalar, rejecting zero, negatives, NaN, infinities, booleans and strings.
`laplace_scale(epsilon)` returns exactly `b = 2.0 / epsilon`.
`sample_degree_noise(epsilon, size=..., rng=...)` calls
`rng.laplace(0.0, b, size=size)` once and draws a separate sample for every
requested entry. It does not reuse one noise draw across vertices.

`make_rng(seed=None)` creates `numpy.random.default_rng(seed)`; simulation seeds
must be nonnegative integers. Callers can reuse a Generator across trials, which
advances its state, or recreate it with the same seed for replay. Do not reset
the seed for each vertex or each nominally independent trial. NumPy's
[Generator.laplace](https://numpy.org/doc/2.2/reference/random/generated/numpy.random.Generator.laplace.html)
uses the location/scale convention above. These are simulation PRNGs, including
when seeded from the operating system, and are
[not suitable for cryptographic use](https://numpy.org/doc/2.2/reference/random/index.html).

`private_graphlets.three_star.corrected_local_stars(Y, b)` evaluates exactly

```text
Y * (Y - 1.0) * (Y - 2.0) / 6.0 - b**2 * (Y - 1.0).
```

It accepts a scalar or array of already-noisy degrees and is **postprocessing**,
not a randomizer by itself. It permits negative and fractional noisy degrees
and returns negative/fractional estimates unchanged. There is no rounding,
clipping, truncation, projection, or substitution of noisy degrees with valid
graph degrees. It does not change the correction based on test outcomes.

### Moment calculation motivating the implementation

For ideal `Z ~ Laplace(0,b)`, `E[Z]=E[Z³]=0` and `E[Z²]=2b²`. With `Y=d+Z`,
expansion of the cubic gives

```text
E[Y(Y−1)(Y−2)/6] = C(d,3) + b²(d−1).
E[b²(Y−1)] = b²(d−1).
```

This explains the specified correction. This calculation is recorded for
independent mathematical review, and is not a formal verification of the
floating point implementation or its privacy properties.

## Full estimator and released result

`estimate_three_stars(graph, epsilon, *, seed=None, rng=None)` performs:

1. Validate epsilon; derive `b=2/epsilon`; accept either a seed or an existing
   Generator, rejecting simultaneous use of both.
2. Obtain each vertex's local degree in numeric vertex-ID order. In this
   centralized research simulation they are held temporarily in one array.
3. Form `Y_v = d_v + Z_v` using a separate Laplace draw for each vertex, including
   isolated vertices. There is no special case suppressing noise for degree < 3.
4. Apply the specified correction to each noisy report; sum with `math.fsum`.
5. Return an immutable `PrivateThreeStarResult`, containing only the aggregate,
   epsilon, scale and the assumed-public vertex count. Reports and raw degrees
   are not stored in that result. An empty vertex set returns the empty sum 0.0.

Runtime and temporary storage are O(n) after graph construction. The Python
package simulates local releases; it does not implement client isolation or
transport. The privacy assumptions and unreviewed accounting are in
[PRIVACY_NOTES.md](PRIVACY_NOTES.md).

`result.to_dict()` supplies a versioned JSON schema:

| Field | Meaning |
|---|---|
| `schema_version` | `1` |
| `result_type` | `private_estimate` |
| `mechanism` | `laplace_degree_corrected_three_star` |
| `pattern`, `count_semantics` | `3-star`, `non-induced` |
| `estimate` | Unrounded, possibly negative floating point total |
| `epsilon`, `laplace_scale` | Requested total edge budget and `2/epsilon` |
| `num_vertices` | Fixed public vertex-set size |
| `simulation_only` | `true`; this is not a secure production release implementation |

The CLI adds Python, NumPy and package versions in `software`. It omits the seed
and generator state from this record. Record simulation commands/seeds in
**separate non-private research metadata**, only for public/synthetic data;
publishing noise seeds is incompatible with the intended privacy model.

## CLI

```bash
# Private mechanism simulation: one JSON object on stdout.
.venv/bin/private-graphlets estimate-three-stars data/fixtures/star.edges --epsilon 2 --seed 123

# NON-PRIVATE ground truth: a separate command and record type.
.venv/bin/private-graphlets exact-three-stars data/fixtures/star.edges
```

Omit `--seed` for a fresh OS-seeded NumPy Generator, still simulation-only.
Redirect stdout to an experiment JSON file if needed. The exact command emits
`result_type=exact_ground_truth`, `count`, vertex/edge counts and software
metadata; it is not a privacy-preserving release. There is no combined command
or optional exact field on the private result. Errors exit with code 2, write a
message to stderr and emit no result record.

## Numerical limits

The exact counter uses Python integers. The simulator uses float64. Very small
positive epsilon can make `b`, `b²` or cubic outputs overflow; extremely large
epsilon can make `b²` underflow. The implementation fails explicitly on these
conditions and on nonfinite inputs/outputs, rather than replacing an estimate
or writing JSON Infinity/NaN. Representability checks are numerical constraints,
not a change in the mathematical epsilon domain. Other floating point rounding,
tail discretization and cancellation remain limitations. Error transcripts and
data-dependent numerical failures are outside any reviewed privacy guarantee.

## Automated validation and statistical tolerances

Run `.venv/bin/python -m pytest -q` for **all** project tests. No external
executable or large dataset is required. The suite includes:

- Required named graphs, overlapping centers, complete bipartite and wheel
  examples, disconnected components and isolates; exact and brute-force agreement
  on **all 1,100 labeled simple graphs with 0 through 5 vertices**.
- Graph/file validation, loop rejection, duplicate normalization, immutable
  adjacency, relabeling invariance, and seeded edge-order invariance.
- Deterministic scale/call checks, numeric failures, RNG state advancement,
  hand-calculated polynomial values, retention of negative fractional estimates,
  and absence of ground truth/degrees/seeds from private records.
- Four-node Gauss–Laguerre quadrature, symmetrized for Laplace noise: a
  deterministic moment check of the cubic mean and squared-cubic variance
  (polynomial degree ≤ 6). It is a numerical regression check, not a DP proof.
- Empirical noise moments and independence diagnostics using 200,000 disjoint
  pairs at epsilon 0.5, 2 and 8. Tests cover the cross moment, squared cross
  moment and joint signs; these cannot prove distributional independence.
- Empirical local correction means for degrees 0, 1, 2, 3, 4 and 9, using
  200,000 samples per degree at epsilon 0.8, 2 and 8.
- Graph-level means from **12,000 calls of the actual estimator per case**, for
  four tiny graph families at epsilon 0.8 and 4; the Generator advances across
  trials. This is bounded unit-test validation, not a utility benchmark.

All Monte Carlo thresholds are **six analytic standard errors**, chosen before
running the tests. For N draws, the noise mean has SE `sqrt(2b²/N)`. The unbiased
sample variance has SE
`sqrt((24b⁴ − 4b⁴(N−3)/(N−1))/N)`. For disjoint independent draws X,Z, the
cross moment XZ has SE `2b²/sqrt(N)`; X²Z² has mean `4b⁴` and SE
`sqrt(560b⁸/N)`; joint positive signs have mean 1/4 and SE `sqrt(3/(16N))`.

For local corrected counts, define `t=d−1` and `a=(3t²−1)/6`. Using the ideal
Laplace moments `E[Z^(2k)] = (2k)! b^(2k)` gives the variance used by tests:

```text
V(d,b) = 2a²b² + (7t² − 2/3)b⁴ + 14b⁶.
```

The local mean's SE is `sqrt(V/N)`. With independent per-vertex reports the graph
mean's SE is `sqrt(Σ_v V(d_v,b)/N)`. Exact degrees used in this **test-only**
calibration are not released by the estimator. The variance formula is itself
checked against the separate quadrature calculation. Six-SE checks are practical
large-sample diagnostics with a conservative margin for repeated comparisons;
they are not exact Gaussian confidence guarantees for the heavy-tailed cubic.
Fixed test seeds aid reproducibility and are never changed to make tests pass.
Neither these checks nor favorable empirical means prove unbiasedness or DP.
