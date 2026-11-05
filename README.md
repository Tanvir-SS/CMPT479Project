# Privacy-Preserving Counting of Size-4 Graph Patterns
Harry testing the push

CMPT 479/982 research project on Local Edge Differential Privacy (LEDP) and
low-out-degree orientations, drawing on ESCAPE and k-CoreD / EdgeOrientΔ.

**Team installation:** [TEAM_SETUP.md](docs/TEAM_SETUP.md) covers recursive Git
clones, GitHub ZIP downloads, all three pinned reference repositories, path
overrides, tests and collaboration. Phase 07 changes portability only; research
algorithms and previous results are unchanged.

**Implemented: exact non-induced 3-star counting, the specified bias-corrected
Laplace estimator, and an independent ESCAPE reference adapter.** All 24 phase-03
validation graphs agree across formula, brute force and ESCAPE. Phase 04 adds
reproducible experiments: **15 graphs, five budgets, 500 trials per cell**,
saved CSVs and plots. The estimator is a research
simulation. The user reports independent review of this 3-star work; its review
memorandum is not part of this checkout. The six project
targets are connected, undirected, **non-induced**
3-stars (`K1,3`), 3-paths (`P4`), tailed triangles, 4-cycles (`C4`), diamonds
(`K4` minus one edge), and 4-cliques (`K4`). A copy counts once per distinct
subgraph, not once per labeling. For example, `K4` contains 4 non-induced
3-stars and 3 non-induced 4-cycles, but no induced star or induced 4-cycle.

See [current status](docs/status/STATUS.md),
[phase 04 checkpoint](docs/status/checkpoints/04_experiments_and_review.md),
[independent-review handoff](docs/status/REVIEW_PACKAGE.md),
[experiments](docs/EXPERIMENTS.md),
[ESCAPE validation](docs/ESCAPE_VALIDATION.md),
[algorithm specification](docs/ALGORITHMS.md), and
[privacy notes](docs/PRIVACY_NOTES.md) for implementation and actual validation.
The [source review](docs/SOURCE_REVIEW.md) and
[setup checkpoint](docs/status/checkpoints/01_setup_and_source_review.md) preserve
phase 01 findings.

**P4 Phase 1 adds exact non-induced 4-path and triangle counting**, plus an
independent permutation oracle. Import `count_four_paths` and
`count_four_paths_bruteforce` from `private_graphlets.four_path_exact`, and
`count_triangles` from `private_graphlets.triangle_exact`. These are non-private
evaluation APIs; no private P4 estimator is implemented. See the
[algorithm contract](docs/ALGORITHMS.md#exact-p4-and-triangle-counters-p4-phase-1)
and [checkpoint 09](docs/status/checkpoints/09_exact_four_path_triangle.md).

**P4 Phase 2 adds an experimental modified EdgeOrientΔ triangle simulator.**
`private_graphlets.triangle.estimate_triangles_from_rr` consumes an existing
released order/cap/RR table and adds only local count noise. The separate
`simulate_triangles_private` runs private k-CoreD, a noisy cap and one RR
transcript with explicit `TriangleBudget` allocations. See
[TRIANGLE_PROTOCOL.md](docs/TRIANGLE_PROTOCOL.md) for interfaces, conditional
sensitivity, retained-triangle target and unresolved privacy questions.
The full private P4 estimator remains unimplemented.

**Phase 06 implements an experimental 4-clique prototype with k-CoreD ordering,
public/noisy caps, local count noise and a six-factor debiased-RR baseline.**
Its full executable privacy proof and low-out-degree utility remain unverified.
See [implementation](docs/FOUR_CLIQUE_IMPLEMENTATION.md),
[k-CoreD audit](docs/KCORED_INTEGRATION.md),
[preliminary experiments](docs/FOUR_CLIQUE_EXPERIMENTS.md) and
[review package 06](docs/status/REVIEW_PACKAGE_06.md).
The [phase-05 design](docs/FOUR_CLIQUE_DESIGN.md) remains the mathematical
specification. Its exact checks still agree with ESCAPE on 1,112 graphs:

```bash
.venv/bin/python scripts/check_four_clique_design.py
```

The script saves raw reference output and its summary under ignored
`build/phase05/`; it does not run a privacy mechanism.

After setup, these commands run the new functionality in the WSL virtual environment:

```bash
.venv/bin/private-graphlets exact-four-cliques data/fixtures/clique.edges
.venv/bin/private-graphlets estimate-four-cliques data/fixtures/clique.edges \
  --epsilon 2 --seed 123 --ordering fixed --cap-mode uncapped
.venv/bin/private-graphlets estimate-four-cliques data/fixtures/clique.edges \
  --epsilon 2 --seed 123 --ordering kcore --cap-mode noisy
.venv/bin/private-graphlets estimate-four-cliques data/fixtures/clique.edges \
  --epsilon 4 --seed 123 --ordering kcore --cap-mode public --cap 3
.venv/bin/private-graphlets baseline-four-cliques data/fixtures/clique.edges --epsilon 2 --seed 123
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_four_clique_experiments.py run
.venv/bin/python scripts/run_four_clique_experiments.py verify --replay
.venv/bin/python scripts/run_four_clique_experiments.py plot
```

Use `--budget O D R C` for explicit allocations summing to total epsilon;
`--public-order 0,1,2,3` is accepted only for declared public fixed order.
No noise-disabled/non-private oracle option exists in the private CLI.
The 8-graph comparison uses 100 trials per cell, 16,000 trials total. Results
are saved under `experiments/results/four_clique_phase06/`, plots under
`plots/four_clique_phase06/`; both are ignored. A new run refuses to overwrite
existing output: use `--output` to choose a new directory. No seed appears in
private result records. All simulations, including unseeded calls, are unverified.

## Setup on Ubuntu / WSL

Run these commands inside Ubuntu, preferably in the Linux home filesystem rather
than `/mnt/c`. Required: Git, Python **3.11**, and the matching `venv` support.
The default `python3` on Ubuntu 22.04 may be Python 3.10; use `python3.11` explicitly.

```bash
sudo apt-get update
sudo apt-get install git build-essential python3.11 python3.11-venv
python3.11 --version
git clone --recurse-submodules https://github.com/Tanvir-SS/CMPT479Project.git
cd CMPT479Project
bash scripts/bootstrap_references.sh
bash scripts/setup.sh
source .venv/bin/activate
private-graphlets info
private-graphlets info --json
python -m private_graphlets --help
python -m pytest -q
```

Check out the project revision you intend to reproduce. A private remote requires
GitHub access (use SSH if configured: `git@github.com:Tanvir-SS/CMPT479Project.git`).

Python package availability depends on your Ubuntu release and configured apt
repositories. If apt cannot find Python 3.11 or `python3.11-venv`, obtain both
through your course-approved Python provider, or install CPython 3.11 separately;
do not change Ubuntu's system `python3` symlink. Use
`PYTHON_BIN=/path/to/python3.11 bash scripts/setup.sh` for a custom interpreter.
The verified interpreter here is CPython **3.11.16** on Ubuntu 22.04.3 / WSL2.
Other 3.11 patch releases are allowed, but record the exact patch for comparisons.
If venv creation fails with `ensurepip` missing, install the matching venv package
and recreate the incomplete `.venv` before retrying. No sudo is needed for pip.

`setup.sh` works from any directory. It creates/reuses `.venv`, installs every
dependency from the exact, SHA-256-verified `requirements.lock`, installs this
package editable without further dependency resolution or isolated build
downloads, checks dependencies, runs pytest, and shows project information.
Internet access to PyPI is needed on the first run. It never installs into system
Python. The virtual environment itself is intentionally not committed.

To recreate from scratch, deactivate the active environment, remove only this
project's `.venv`, and rerun the setup script. To prepare an offline install on a
matching Ubuntu architecture/Python version, download wheels in advance:

```bash
.venv/bin/python -m pip download --require-hashes -r requirements.lock -d build/wheelhouse
PIP_NO_INDEX=1 PIP_FIND_LINKS="$PWD/build/wheelhouse" bash scripts/setup.sh
```

To verify a fresh environment without replacing your working `.venv`, run
`.venv/bin/python scripts/check_clean_setup.py` after downloading the wheelhouse.
This copies Git-visible project files (excluding reference gitlinks) to a temporary
directory and verifies Python-only setup offline, with explicit ESCAPE skips. It
preserves `build/reproduction-check.log`. To test complete recursive-clone and ZIP
setup with references, run `.venv/bin/python scripts/check_portable_setup.py`; see
[TEAM_SETUP.md](docs/TEAM_SETUP.md).

## Count non-induced 3-stars

The edge list starts with `n m`, declaring vertices `0..n-1` and the number of
**unique undirected edges**. Subsequent lines contain two vertex IDs. Duplicates
and reverse copies count once; the deduplicated count must match `m`. Self-loops
are rejected. Blank lines and `#` comments are accepted. Declaring `n` preserves
isolated vertices; `0 0` and `5 0` are valid edgeless inputs.

```bash
# One structured simulation result; seed is optional.
private-graphlets estimate-three-stars data/fixtures/star.edges --epsilon 2 --seed 123

# Separate NON-PRIVATE ground-truth result.
private-graphlets exact-three-stars data/fixtures/star.edges

# Run every automated test, including small Monte Carlo diagnostics.
python -m pytest -q
```

The estimator uses exactly `b=2/epsilon` and the local correction
`Y*(Y-1)*(Y-2)/6 - b**2*(Y-1)`. It preserves negative/fractional estimates and
returns the aggregate, public parameters and software metadata as JSON. It does
not release raw degrees, true edge counts, exact star counts or the seed. The
fixed vertex set is assumed public. NumPy randomness, with or without a seed,
is for simulations and is not cryptographically secure. Record seeds separately
only in non-private experiment metadata for public/synthetic data. Never publish
exact-evaluation records alongside purported private outputs on protected data.

See [ALGORITHMS.md](docs/ALGORITHMS.md) for APIs, file/output schemas and test
tolerances, and [PRIVACY_NOTES.md](docs/PRIVACY_NOTES.md) for assumptions and
unresolved questions. No formal DP proof is claimed.

## Reproduce the accuracy experiments

After setting up the read-only ESCAPE checkout as below, run from the project root:

```bash
.venv/bin/python scripts/run_experiments.py run
.venv/bin/python scripts/run_experiments.py verify --replay
.venv/bin/python scripts/run_experiments.py plot
.venv/bin/python scripts/analyze_experiments.py --output build/phase04/accuracy.json
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q -m escape_integration
```

The checked-in config is `experiments/configs/three_star_phase04.json`. Results
go to `experiments/results/three_star_phase04/` (`trials.csv`, `summary.csv`,
`graphs.csv`, original graphs, exact config and provenance). Four figures in
PNG/PDF go to `plots/three_star_phase04/`. These outputs are Git-ignored and must
be generated after cloning or transferred separately for review. The compact
saved [accuracy summary](docs/status/accuracy_04.json) records observed findings.

An existing result directory is never overwritten. For another run choose
`run --output experiments/results/my_run`; supply `--results` with that directory
to verify, plot and analyze. The root argument `--escape-root` overrides the
environment. Verification rechecks hashes and metrics; `--replay` additionally
regenerates all estimates exactly. Timings are not expected to match. To verify
figure regeneration, use `plot --output build/phase04/regenerated-plots` and
compare the figure hashes in each `plot_manifest.json`.

All experiments are non-private synthetic evaluation, with published seeds and
exact truth. Relative errors are undefined for zero true counts. No estimate
is clipped or rounded. See [EXPERIMENTS.md](docs/EXPERIMENTS.md) for metric
definitions, observed accuracy, finite-sample limitations and precise commands.

## Dependencies and reproducibility

Direct scientific dependencies are NumPy 2.2.6, NetworkX 3.4.2, pandas 2.2.3,
and Matplotlib 3.10.1. pytest 8.3.5 is the test runner. Packaging tools and every
transitive dependency are also pinned in `requirements.lock`.
`requirements-constraints.txt` pins pyparsing 3.2.3 for compatibility with the
Matplotlib baseline (newer parser deprecations failed our strict smoke test).
These are deliberate
baseline versions, not a claim to be the newest releases. `pyproject.toml` is the
direct dependency source of truth; normal setup consumes the lock unchanged.

To intentionally update dependencies, edit pins, run
`bash scripts/lock_dependencies.sh` in the installed environment, inspect the
lock diff, recreate the environment and rerun checks. pip-tools 7.5.0 generates
the lock under Python 3.11. Record the change in a new status checkpoint. Initial
bootstrap of the resolver, if needed before a lock exists, is:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install pip==25.1.1 setuptools==80.9.0 wheel==0.45.1 pip-tools==7.5.0
bash scripts/lock_dependencies.sh
```

The lock targets Python 3.11 on Ubuntu/Linux. Package pins and hashes control
dependencies; they do not guarantee identical floating point results across
architectures or BLAS implementations. Future runs must record environment,
dataset hashes, graph preprocessing, random seeds, privacy budgets, repetitions,
and project/reference revisions in separate non-private research metadata.
Setup runs the automated tests, including bounded seeded Monte Carlo checks on
tiny synthetic graphs. No large dataset experiments have been run.

For a distributable wheel and source archive:

```bash
.venv/bin/python -m build --no-isolation
```

For plots on headless WSL, use `MPLBACKEND=Agg` and save figures to `plots/`.
If the home cache is unwritable, set
`MPLCONFIGDIR="$PWD/.cache/matplotlib"`; setup does this automatically.

## Reference checks (optional for Python setup)

All three reference repositories are pinned Git submodules under `third_party/`.
Their roles are independent exact verification (ESCAPE), the original Go k-CoreD /
EdgeOrientΔ implementation, and the baseline authors' 4-cycle notebooks. None
replaces our Python algorithms. Go and the notebooks are not runtime dependencies.

```bash
bash scripts/bootstrap_references.sh
.venv/bin/python scripts/reference_fingerprints.py --verify
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_escape.py  # eight exact-only reference fixtures
```

For a GitHub ZIP, extract the main repository, run the same bootstrap command,
then `bash scripts/setup.sh`. Bootstrap handles absent Git metadata, fetches
public HTTPS upstreams and verifies pinned revisions/content. It refuses modified
or mismatched existing source trees. ZIP-equivalent snapshots and recursive
clones were tested; unpublished Phase-7 changes require the owner's commit/push
before GitHub can serve them. See [team instructions](docs/TEAM_SETUP.md).

Reference resolution: explicit `--escape-root` > `ESCAPE_ROOT` >
`third_party/escape`. Defaults and relative overrides use the project root,
independently of the working directory. `KCORED_ROOT` and `BASELINE_ROOT` plus
`--kcored-root` / `--baseline-root` configure the fingerprint utility similarly.
Without an ESCAPE checkout, its **43 integration cases explicitly skip**; ordinary
Python estimation still works. A configured or partially populated broken checkout
fails instead of skipping. Default bundled sources are automatically detected.

Exact pins and inclusion basis:

| Reference | Commit | License / permission |
|---|---|---|
| ESCAPE | `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3` | Apache-2.0 |
| DistributedLEDPGraphAlgos | `b03da893ba1c38d3931708bac919562c5ab57963` | MIT |
| Counting Graphlets of Size k under Local Differential Privacy | `85eff6efa2b1d649ee238620a998ec7f1d305aac` | No license found; project owner reports author permission for inclusion in this academic repository |

No license is assigned to the baseline. Broader redistribution scope requires
confirmation; no private correspondence is published. The authors' notebooks
implement 4-cycle examples, not all six patterns. Our 4-clique RR comparator is
independently implemented. An equivalent 3-star baseline comparison remains future
work. See [source review](docs/SOURCE_REVIEW.md#phase-07-baseline-inspection-and-portable-references).

[third_party/references.json](third_party/references.json) is the portable pin/hash
manifest. [references_phase07.json](docs/references_phase07.json) records original
source inspection; [references.json](docs/references.json) and previous research
provenance are preserved. The original three external directories are unchanged.

Compilation reads the original four C++ translation units and puts the binary,
command, source hashes and warning log in `build/escape/` (`build/escape-pytest/`
for pytest). It avoids the upstream Makefile's `-lc++` setting. Each invocation
runs in a temporary directory because ESCAPE hardcodes `out.txt`; raw output is
retained in the JSON report before temporary files are removed. Original sources
are unchanged. No reference executable is shipped in the Python package.

Default outputs are `build/phase03/validation.json` and
`build/phase03/epsilon_samples.json`. To choose a report location, pass
`--output path/to/report.json`; the saved phase-03 evidence is
[validation_03.json](docs/status/validation_03.json). All these reports contain
**non-private evaluation of synthetic graphs**, including exact truth and seeds.
The existing private result schema is unchanged.

The adapter canonicalizes our validated edge lists, pads inputs with fewer than
four vertices using isolates, and limits inputs to 1,000 vertices. Connected
four-vertex counts are preserved by padding; disconnected columns describe the
normalized graph. See [ESCAPE_VALIDATION.md](docs/ESCAPE_VALIDATION.md) for the
output map, API, failures, numerical limits and actual diagnostic results.

The Go reference requires Go 1.21 or newer according to `go.mod` (verified here
with Go 1.26.4). To reproduce its compile checks without writing to the original:

```bash
mkdir -p build/reference-checks/go-source
git -C third_party/DistributedLEDPGraphAlgos archive b03da893ba1c38d3931708bac919562c5ab57963 | tar -x -C build/reference-checks/go-source
export GOCACHE="$PWD/.cache/go-build"
export GOMODCACHE="$PWD/.cache/go-mod"
export GOPATH="$PWD/.cache/go"
export GOTOOLCHAIN=local
(cd build/reference-checks/go-source && go test ./...)
(cd build/reference-checks/go-source && go build ./...)
```

These Go checks are separate from pytest. The checkpoint records their
actual outcomes; `[no test files]` is compilation evidence, not behavioral or DP
validation. Do not run the Go experiment driver without reviewing its hard-coded
paths and parameter overrides described in the source review.

## Layout and development workflow

```text
src/private_graphlets/  Graphs, counters, noise, estimator, CLI and ESCAPE adapter
tests/                 Exact, mechanism, statistical, CLI and ESCAPE integration tests
scripts/               Locked setup, reference bootstrap/integrity and ESCAPE checks
third_party/           Three pinned submodules plus pin/hash manifest
.gitmodules            Public reference URLs (gitlinks pin exact commits)
docs/TEAM_SETUP.md     Clone/ZIP setup, commands, troubleshooting and collaboration
data/fixtures/         Tiny public synthetic reference inputs and expected counts
data/raw/              Ignored original datasets
data/processed/        Ignored processed datasets
experiments/configs/   Versioned experiment configuration, seeds and budgets
experiments/results/   Ignored generated research output
plots/                 Ignored generated figures
docs/SOURCE_REVIEW.md   Source map, counting identities and implementation concerns
docs/ALGORITHMS.md      Implemented 3-star algorithms, formats and validation
docs/PRIVACY_NOTES.md   Intended model/accounting and unresolved proof questions
docs/ESCAPE_VALIDATION.md  Reference build/interface, comparisons and limitations
docs/EXPERIMENTS.md     Reproduction, metric definitions and observed findings
docs/FOUR_CLIQUE_DESIGN.md  Candidate design, mathematical assumptions and review questions
docs/status/REVIEW_PACKAGE.md  Technical handoff for independent review
docs/references.json    Reviewed commits and source hashes
docs/status/           Current status and numbered phase checkpoints
build/                 Ignored local builds and verification logs
```

Read [AGENTS.md](AGENTS.md) before working. Keep documentation and status current,
add a numbered checkpoint for each phase, and distinguish observations from
mathematical claims. Empirical tests cannot establish a formal DP guarantee.
**Phase 07 stops after repository portability and regression validation. Do not
change privacy mechanisms, optimize algorithms, run new utility experiments or
start another phase without explicit follow-up. No automatic commit/push.**
