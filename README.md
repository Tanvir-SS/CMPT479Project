# Privacy-Preserving Counting of Size-4 Graph Patterns

CMPT 479/982 research project on Local Edge Differential Privacy (LEDP) and
low-out-degree orientations, drawing on ESCAPE and k-CoreD / EdgeOrientΔ.

**Current scope: repository setup and source review only. No private estimator
is implemented.** The six targets are connected, undirected, **non-induced**
3-stars (`K1,3`), 3-paths (`P4`), tailed triangles, 4-cycles (`C4`), diamonds
(`K4` minus one edge), and 4-cliques (`K4`). A copy counts once per distinct
subgraph, not once per labeling. For example, `K4` contains 4 non-induced
3-stars and 3 non-induced 4-cycles, but no induced star or induced 4-cycle.

See [current status](docs/status/STATUS.md),
[setup checkpoint](docs/status/checkpoints/01_setup_and_source_review.md), and
[source review](docs/SOURCE_REVIEW.md) for findings and actual validation.

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

The remote must first contain these project files; phase 01 creates local files
and does not push a commit. A private remote requires GitHub access (use SSH if
configured: `git@github.com:Tanvir-SS/CMPT479Project.git`).

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
and project/reference revisions. No random research run occurs during setup.

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
.venv/bin/python scripts/check_escape.py --source ../escape
```

The ESCAPE check compiles the original C++ translation units directly with g++
and runs eight small synthetic fixtures, keeping binaries, logs and `out.txt`
under ignored `build/reference-checks/escape/`. It checks the six connected count
columns and header convention, using hand-checked expectations, and does not
implement an estimator. It avoids the upstream Makefile's `-lc++` link setting.
Do not run the upstream wrapper in the original repository: it writes `out.txt`
in its working directory. No reference executable is part of the Python package.

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

These are upstream checks, independent of pytest. The checkpoint records their
actual outcomes; `[no test files]` is compilation evidence, not behavioral or DP
validation. Do not run the Go experiment driver without reviewing its hard-coded
paths and parameter overrides described in the source review.

## Layout and development workflow

```text
src/private_graphlets/  Installable package and information-only CLI
tests/                 Installation, CLI and scientific-stack smoke tests
scripts/               Locked setup, lock regeneration and ESCAPE checks
data/fixtures/         Tiny public synthetic reference inputs and expected counts
data/raw/              Ignored original datasets
data/processed/        Ignored processed datasets
experiments/configs/   Reserved for future reviewed experiment configurations
experiments/results/   Ignored generated research output
plots/                 Ignored generated figures
docs/SOURCE_REVIEW.md   Source map, counting identities and implementation concerns
docs/references.json    Reviewed commits and source hashes
docs/status/           Current status and numbered phase checkpoints
build/                 Ignored local builds and verification logs
```

Read [AGENTS.md](AGENTS.md) before working. Keep documentation and status current,
add a numbered checkpoint for each phase, and distinguish observations from
mathematical claims. Empirical tests cannot establish a formal DP guarantee.
**Stop after setup and source review. Private 3-star estimation and all other
private algorithms require a later explicit instruction.**
