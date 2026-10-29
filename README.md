# Privacy-Preserving Counting of Size-4 Graph Patterns

CMPT 479/982 research project on Local Edge Differential Privacy (LEDP) and
low-out-degree orientations, drawing on ESCAPE and k-CoreD / EdgeOrientΔ.

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

**Phase 05 is design only and stopped for mathematical review.** See the
[candidate 4-clique design](docs/FOUR_CLIQUE_DESIGN.md) and
[checkpoint 05](docs/status/checkpoints/05_four_clique_design.md) for pseudocode,
sensitivity/cap-bias analysis, privacy assumptions and unresolved questions.
No private 4-clique estimator is implemented. Its non-private identity/algebra
checks agree with actual ESCAPE on 1,112 graphs. Reproduce them after setup:

```bash
ESCAPE_ROOT=/path/to/escape .venv/bin/python scripts/check_four_clique_design.py
```

The script saves raw reference output and its summary under ignored
`build/phase05/`; it does not run a privacy mechanism. The CLI's informational
phase label still describes the implemented phase-04 software.

## Setup on Ubuntu / WSL

Run these commands inside Ubuntu, preferably in the Linux home filesystem rather
than `/mnt/c`. Required: Git, Python **3.11**, and the matching `venv` support.
The default `python3` on Ubuntu 22.04 may be Python 3.10; use `python3.11` explicitly.

```bash
sudo apt-get update
sudo apt-get install git build-essential python3.11 python3.11-venv
python3.11 --version
git clone https://github.com/Tanvir-SS/CMPT479Project.git
cd CMPT479Project
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
This copies Git-visible project files to a temporary directory, runs setup there
offline, preserves `build/reproduction-check.log`, and removes the temporary copy.

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
export ESCAPE_ROOT="$(realpath ../escape)"
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

The reference repositories are separate, read-only checkouts. Their exact reviewed
revisions and source fingerprints are in [references.json](docs/references.json).
The original locations on this machine are `/home/tsshergi/escape` and
`/home/tsshergi/DistributedLEDPGraphAlgos`. On another machine:

```bash
git clone https://bitbucket.org/seshadhri/escape.git ../escape
git -C ../escape checkout 7ec2f93c524a0b47cdc8c639602e90d1c1fceff3
git clone https://github.com/mundrapranay/DistributedLEDPGraphAlgos.git ../DistributedLEDPGraphAlgos
git -C ../DistributedLEDPGraphAlgos checkout b03da893ba1c38d3931708bac919562c5ab57963
export ESCAPE_ROOT="$(realpath ../escape)"

# All 24 three-way comparisons plus six bounded epsilon diagnostics.
.venv/bin/python scripts/validate_escape.py

# All Python and real ESCAPE tests; the fixture builds ESCAPE once.
.venv/bin/python -m pytest -q

# Optional original eight hand-counted six-column fixtures.
.venv/bin/python scripts/check_escape.py
```

Alternatively pass `--escape-root /path/to/escape` to either script or pytest;
the argument overrides the environment. No personal path is required by the
adapter. Without either setting, **34 real integration tests explicitly skip**;
ordinary Python setup still works. A configured missing/broken checkout or failed
build is an error, never a skip or a substitute Python result.

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
git -C ../DistributedLEDPGraphAlgos archive b03da893ba1c38d3931708bac919562c5ab57963 | tar -x -C build/reference-checks/go-source
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
scripts/               Locked setup, lock regeneration and ESCAPE checks
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
**Phase 05 stops after the 4-clique design and mathematical-review documentation.
Do not implement the candidate or start another phase without explicit follow-up.**
