# WLocal C4 baseline evaluation

Completed 2026-11-14 (America/Vancouver). Phase 28. All 4,800 requested main
trials completed: six pinned graphs × epsilon {0.5, 1, 2, 4} × 200 trials.
The user's explicit baseline request supersedes the historical stopping points.
Existing uniform candidate-sampling RR code and results were not modified.

WLocal's empirical RMSE is smaller in all 24 **nominal-epsilon** cells. The
ratio Our RMSE / WLocal RMSE ranges from 6.2772 to 74.3009. This is not a
comparison at equal undirected-edge privacy; see the privacy review below.
All 1,478 negative estimates (30.7917%) are retained, without clipping or rounding.

## Files and reproduction

The six supplied files remain byte-for-byte in `WLocal4Cycle/`. The actual
Makefile filename is `Makefile.txt`. New scripts are isolated here:

- `build.py`: pinned dependency checks, isolated source patch and native builds.
- `source.patch`: complete source changes applied only under `build/wlocal/`.
- `driver.cpp`: strict input adapter, explicit per-trial seeds, full-precision output.
- `convert.py`: six pinned graph conversions, round-trip and exact-count checks.
- `run.py`: validation, incremental main run/resume, aggregation and verification.
- `outputs/trials.csv`: every main estimate, seed, truth and measured call runtime.
- `outputs/summary.csv`: all requested metrics, including negative percentage.
- `outputs/comparison.csv`: all 24 comparisons with explicit privacy-bound columns.
- `outputs/validation_*.csv`, `validation.json`: separate validation samples/evidence.
- `outputs/conversion.json`, `escape_ground_truth.json`: input hashes and cached native truth.
- `outputs/configuration.json`, `artifacts.json`: provenance and artifact hashes.

Working executables are `build/wlocal/SubgraphShuffle` (authors' CLI with the
isolated patch), `build/wlocal/wlocal` (evaluation adapter) and
`build/wlocal/wlocal_sanitize` (AddressSanitizer + UndefinedBehaviorSanitizer).
Build products, dependencies and experimental outputs are Git-ignored.

From the repository root, on a fresh checkout with the previous RR result cache:

```bash
.venv/bin/python experiments/baselines/wlocal/build.py
.venv/bin/python experiments/baselines/wlocal/convert.py
.venv/bin/python experiments/baselines/wlocal/run.py validate
.venv/bin/python experiments/baselines/wlocal/run.py run
.venv/bin/python experiments/baselines/wlocal/run.py analyze
.venv/bin/python experiments/baselines/wlocal/run.py verify
```

`run` resumes existing complete CSV rows and checks their coordinates, seeds,
truth and source/config/input fingerprints. `--max-new-trials 1` exercises a
bounded first call. A completed run adds zero samples. Validation refuses to
silently repeat if its receipt exists. Do not delete prior results to repeat a
study; use a separate checkout/output archive. The ignored prior RR cache must
be transferred separately: Git alone does not contain research outputs.
CSV is flushed after every trial; abrupt partial-line corruption fails closed
and needs explicit recovery. Concurrent writers are unsupported. Seeds are
32-bit MT19937 initializations; seeded pseudorandom streams model independent
trials but are not cryptographic or mathematically independent randomness.

For a direct call, pipe decimal seeds to:
`build/wlocal/wlocal experiments/baselines/wlocal/outputs/inputs/karate.csv 1`.
It prints a non-private exact diagnostic first, then seed, estimate, seconds.
This interface and all CSVs are **non-private evaluation artifacts**, not private
releases. Exact diagnostics and seeds must not accompany a private release.

## Source inspection, dependencies and changes

The provided README requires StatsLib, absent from the supplied files. StatsLib
also requires GCEM. Downloaded from their official repositories and pinned:

- [StatsLib](https://github.com/kthohr/stats): `f8dcb15ae51cce7142b239805745a0de56aa509f`.
- [GCEM](https://github.com/kthohr/gcem): `012ae73c6d0a2cb09ffe86475f5c6fba3926e200`.

No Python dependency or lock changes. The build copies the supplied Makefile to
an ignored build directory and invokes make with `c++`, C++11, O3 and GCEM's
include path. The original `-march=native` is omitted for portability; there is
no fast-math flag. Exact compiler/version/commands and source hashes are in
`build/wlocal/build.json` and the output configuration. StatsLib's fixed engine
is not used by Algorithm 9: pairing and RR use the supplied MT19937 functions.

`CalcShuffleCy4(..., 9)` uses RR probability 1/(exp(epsilon)+1), the authors'
quadratic bias correction, and n(n-1)/(4 floor(n/2)) scaling. None is changed.
The official source is identified by the user's provenance and the
[authors' repository](https://github.com/Triangle4CycleShuffle/Triangle4CycleShuffle);
no byte-for-byte comparison against a separate upstream checkout is claimed.

Three source-level fixes in the isolated copy:

1. C4 loop `i<NodeNum` becomes `i+1<NodeNum`. The old loop reads `node_order[n]`
   when n is odd. Dropping only the unpaired final permutation position implements
   exactly floor(n/2) pairs, without removing a vertex from the graph. That vertex
   can still report wedges for all sampled pairs. Les Misérables retains all 77
   vertices and 254 edges; no isolate padding or graph regeneration.
2. Remove nonportable `<malloc.h>`; `<stdlib.h>` supplies the required declarations.
3. Correct the allocation check from `source == NULL` to `*source == NULL`.

The adapter includes the entire patched author translation unit, renames its
main, and calls the original estimator directly. It resets MT with each explicit
seed, avoiding identical process-start seeds; uses 17 significant output digits
instead of the CLI's six-place `%e`; validates simple canonical inputs; fixes
PairNum=-1 and Bip=0; accepts n=4..1000 and epsilon in (0,20]. These are evaluation
boundaries, not modifications of the estimator. The authors' CLI remains for
inspection; the adapter is the supported reproducible experiment entry point.

Other limitations found but deliberately not redesigned: `MakeRndPerm` uses
integer modulo, giving slight finite-PRNG permutation bias; `genrand_real2` has
32-bit resolution; the standalone CLI permits unsafe pair counts and malformed
input; other algorithms have not been audited (the triangle pairing loop is
unchanged). Thus ideal unbiasedness/DP do not certify this binary. The adapter
prevents the relevant invalid n/pair/input settings for this study. Integer C4
diagnostics use 64-bit integers; these six graphs fit comfortably.

## Dataset and numerical validation

Conversion writes three header lines (`nodes`, n, `source,target`) followed by
one `u,v` record per undirected edge. It verifies original SHA-256, n/m, ordered
unique non-loop edges, endpoint bounds, preserved vertex universe and exact
round-trip edge identity. No synthetic graph was regenerated.

| Dataset | n | m | Exact non-induced C4 | Disjoint pairs |
|---|---:|---:|---:|---:|
| Karate |34|78|154|17|
| Dolphins |62|159|278|31|
| Les Misérables |77|254|2672|38|
| Brightkite-50 |50|97|198|25|
| BA-100 |100|1600|207959|50|
| SBM-100 |100|760|7302|50|

Independent common-neighbor counting on the converted inputs agrees with cached
native ESCAPE's non-induced C4 column on all six graphs. The C++ adapter's reader
and common-neighbor diagnostic also agree. Native output/source provenance is
copied without changing old caches. No new ESCAPE run is claimed. The adapter
computes its diagnostic at each process start; this overhead is outside timed
estimator calls and is not a private step. All three bundled reference
fingerprints passed verification; original `/home/tsshergi` paths are unavailable
on this Mac and were not accessed or modified.

Before main evaluation, fixed validation ranges were used at epsilon 4:

| Graph | Trials | Truth | Mean | Sample-mean SE | Absolute z |
|---|---:|---:|---:|---:|---:|
| Single four-vertex C4 |20000|1|0.9957774605|0.0101296320|0.41685|
| Karate |5000|154|151.9589013688|2.3806401156|0.85737|

The predetermined criterion was absolute z<4 for both, plus absolute mean error
<0.05 for the single C4. Both passed. The first 200 C4 trials averaged 0.939795;
the full 20,000 mean is closer to one. This is finite-sample consistency evidence,
not proof of unbiasedness or monotonic convergence. Algebraically, with ideal
uniform pairing and independent RR, the quadratic correction subtracts half the
wedge-sum variance, leaving choose(common-neighbors,2). Each unordered pair is
sampled with probability floor(n/2)/choose(n,2), and each C4 has two diagonals;
the unchanged scale therefore recovers the non-induced count in expectation,
including odd n. Chorded cycles are included; embeddings/induced four-sets are
not the target.

Five seeds on each of the six graphs were run through sanitizer and release
builds: all 30 matched exactly, all were finite, and changing seeds changed
estimates on every graph. No sanitizer diagnostics or failures. These 60 calls
and 25,000 statistical-validation trials are separate from the 4,800 main trials.
Validation seed ranges 100000..119999, 200000..204999, 300000..300004 are disjoint
from main seeds. The repeated five replay seeds across graphs are intentional
and occur only in validation.

## Evaluation and results

Main seed = 28000000 + graph_index*100000 + epsilon_index*1000 + trial,
with dataset order as in the existing RR configuration, epsilon order .5/1/2/4,
and trial 0..199. All 4,800 main seeds and coordinates are distinct. Per-trial
runtime covers only `CalcShuffleCy4`; the summed call runtime was 0.059077949 s.
This excludes loading, exact diagnostics, seed setup and subprocess/CSV overhead;
it is not an end-to-end speed comparison with Python RR.

Metrics reuse `docs/EVALUATION_STANDARDS.md`: direct mean squared error,
sqrt(MSE), mean-truth bias, population variance (ddof=0), mean absolute error,
RMSE/truth, and 100*negative_count/200. MSE=variance+bias² was verified in every
cell. All estimates remain signed double values. WLocal relative RMSE ranges
from 0.1091254 to 97.14148. Two hundred samples per cell leave substantial moment
uncertainty; these observed ratios are descriptive, not significance claims.

Our RMSE is read from the preserved phase-27 summary, not rerun. Ratio is
**Our RMSE / WLocal RMSE** (>1 means WLocal's empirical RMSE is lower).

| Dataset | ε | True C4 | Our RMSE | WLocal RMSE | RMSE Ratio |
|---|---:|---:|---:|---:|---:|
| karate | 0.5 | 154 | 236271 | 6089.06 | 38.8026 |
| karate | 1 | 154 | 58931 | 1403.94 | 41.9755 |
| karate | 2 | 154 | 14269.6 | 386.806 | 36.8909 |
| karate | 4 | 154 | 3013.91 | 160.752 | 18.7488 |
| dolphins | 0.5 | 278 | 1.55242e+06 | 27005.3 | 57.4856 |
| dolphins | 1 | 278 | 423823 | 6225.16 | 68.0822 |
| dolphins | 2 | 278 | 95100.9 | 1460.61 | 65.1102 |
| dolphins | 4 | 278 | 20004.5 | 289.33 | 69.1409 |
| les_miserables | 0.5 | 2672 | 3.18969e+06 | 50789.2 | 62.8026 |
| les_miserables | 1 | 2672 | 793368 | 12514.3 | 63.3968 |
| les_miserables | 2 | 2672 | 180201 | 3307.59 | 54.4811 |
| les_miserables | 4 | 2672 | 38135.9 | 1701.3 | 22.4157 |
| brightkite_50 | 0.5 | 198 | 855955 | 15991.3 | 53.5263 |
| brightkite_50 | 1 | 198 | 216511 | 4259.99 | 50.8243 |
| brightkite_50 | 2 | 198 | 51600.5 | 963.753 | 53.5412 |
| brightkite_50 | 4 | 198 | 11023.3 | 249.308 | 44.2157 |
| ba_n100 | 0.5 | 207959 | 6.63756e+06 | 142085 | 46.7154 |
| ba_n100 | 1 | 207959 | 1.83983e+06 | 50741.7 | 36.2587 |
| ba_n100 | 2 | 207959 | 466875 | 32168.1 | 14.5136 |
| ba_n100 | 4 | 207959 | 142452 | 22693.6 | 6.27719 |
| sbm_n100 | 0.5 | 7302 | 6.54707e+06 | 103744 | 63.1078 |
| sbm_n100 | 1 | 7302 | 1.87721e+06 | 25265 | 74.3009 |
| sbm_n100 | 2 | 7302 | 416683 | 5851.87 | 71.2051 |
| sbm_n100 | 4 | 7302 | 87315.1 | 2151.58 | 40.582 |

## Privacy and comparison fairness

The [paper](https://arxiv.org/html/2205.01429), Definitions 3.3–3.5, distinguishes
one-bit adjacency-list/element privacy from changing an undirected edge. Section
6.3 defines WLocal using epsilon_L=epsilon without shuffling. Section 7.2 explicitly
interprets its plotted epsilon as element/edge-local epsilon and twice that value
as edge-DP epsilon. Theorem 6.1 states the corresponding factor of two for WShuffle.

Our source-level accounting for Algorithm 9 is as follows. Condition on the
public vertex pairing. A bit in row u belongs to at most one requested wedge
at center u, since the endpoint pairs are disjoint. Its complete local transcript
therefore has an ideal epsilon bound. An undirected edge {u,v} changes two rows.
When u and v are in different selected pairs, it can change one wedge report at
u and another at v. Independent RR composition gives **2 epsilon** for the full
undirected-edge transcript. For example, pair (u,a) and (v,b), with edges (u,b)
and (v,a) present: toggling (u,v) flips both those wedge inputs. The event where
both reports favor the added edge has likelihood ratio exp(2 epsilon), conditional
on that public schedule. Consequently epsilon for the entire public-schedule-plus-
reports transcript cannot generally be asserted. Paired endpoints can have zero
influence, but that does not remove the conditional worst case for public pairing.
This argument is for the ideal transcript; it is not a tight privacy analysis
of a scalar-only output or a proof for finite-precision executable behavior.

By contrast, our existing RR allocation epsilon/max(K_e1,K_e2) counts all requests
affected by each undirected edge, including both endpoint rows. Summing their
allocated budgets is at most epsilon for that edge under the ideal protocol.
Thus the table compares our epsilon guarantee with WLocal's **2 epsilon bound**,
not the same guarantee. WLocal also uses floor(n/2)*(n-2) reports per trial,
whereas our method uses 2*ceil(.05*n²); communication workloads differ.

An equal-undirected-edge comparison would run WLocal at half our epsilon. It is
not performed here: the user requested the explicit 4,800-trial nominal grid.
No claim of superiority at equal privacy follows from this table. Neither method
is node-private. No trusted shuffler/amplification is assumed for Algorithm 9.
Empirical accuracy checks cannot prove DP, and these PRNG/float simulations are
not production privacy mechanisms. Formal guarantees remain subject to independent
review; raw graphs, truth and seeds are confined to non-private evaluation data.

## Observed commands, failures and skipped checks

Commands were run from the project root:

```bash
git clone --depth 1 https://github.com/kthohr/stats.git build/wlocal/stats
git clone --depth 1 https://github.com/kthohr/gcem.git build/wlocal/gcem
.venv/bin/python experiments/baselines/wlocal/build.py > build/wlocal/build.log 2>&1
.venv/bin/python experiments/baselines/wlocal/convert.py
.venv/bin/python experiments/baselines/wlocal/run.py validate > build/wlocal/validation.log 2>&1
.venv/bin/python experiments/baselines/wlocal/run.py run --max-new-trials 1
.venv/bin/python experiments/baselines/wlocal/run.py run > build/wlocal/main.log 2>&1
.venv/bin/python experiments/baselines/wlocal/run.py run
.venv/bin/python experiments/baselines/wlocal/run.py analyze
.venv/bin/python experiments/baselines/wlocal/run.py verify
.venv/bin/python scripts/reference_fingerprints.py --verify > build/wlocal/reference_fingerprints.json
```

The first sandboxed StatsLib clone failed with DNS resolution; the approved
network-enabled retry succeeded. GCEM download succeeded with network approval.
All native builds, conversions, validation, main trials, resume and saved-output
verification succeeded. Resume added 4,799 after the first saved trial and zero
after completion. No main trial failures, missing rows or nonfinite estimates.
The missing `.gitmodules` inspection returned a file-not-found message; StatsLib
uses an external GCEM header dependency, which was obtained explicitly.

Skipped deliberately: full Python regression (no package implementation changed),
new native ESCAPE runs (cached native truth reused), all-trial replay (30 selected
replays passed), equal-privacy additional simulations, algorithm redesign,
additional graphs, plots, commit and push. Earlier sources, datasets, pins and
results are preserved. No extra experimental phase is started.

Final verification also ran an inline `.venv/bin/python -` check using only
`csv`, `math`, and `statistics`: independently recomputed mean, bias, RMSE,
MAE, population variance and negative percentage for every cell, agreeing with
saved metrics (relative tolerance 1e-12, absolute 1e-10). The same check hashed
all six supplied files against the build receipt and asserted that `git diff
--name-only` contains only STATUS and `git diff --cached --name-only` is empty.
All passed. `git diff --check` passed; `git check-ignore` confirms main CSV and
executable exclusion. The report/checkpoint/scripts are new untracked files for
owner review; nothing was staged or committed.
