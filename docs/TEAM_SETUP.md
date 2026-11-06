# Team setup on Ubuntu / WSL and macOS

Phase 07 makes the existing research code portable; it does not change algorithms,
privacy accounting, experimental configurations or saved findings. The 4-clique
prototype remains `experimental_unverified`. See [STATUS](status/STATUS.md) and
[checkpoint 07](status/checkpoints/07_repository_portability.md) for actual checks.

## macOS prerequisites and current verification

Use native Python **3.11**, Git and GNU GCC for ESCAPE. On the Apple Silicon
Mac checked on 2026-11-05, Python 3.11.9 and Xcode were already installed.
`/usr/bin/g++` was Apple Clang 21, not GNU GCC. The pinned ESCAPE source failed
to compile with its libc++ (unsupported operations on `Escape::JSIterator`).
Do not edit the pinned reference to work around this failure.

If GNU GCC is absent, install [Homebrew](https://brew.sh/) in Terminal, where
its initial administrator authentication can be completed, then install GCC:

```bash
/opt/homebrew/bin/brew install gcc
python3.11 -m venv .venv  # only if .venv is absent
# This Mac installed GCC 16.2.0; use the installed major version in the path.
ln -s /opt/homebrew/bin/g++-16 .venv/bin/g++  # only if this link is absent
source .venv/bin/activate
bash scripts/bootstrap_references.sh
bash scripts/setup.sh
python scripts/check_escape.py
```

Homebrew uses `/opt/homebrew` on Apple Silicon. Python 3.11 can be selected
with `PYTHON_BIN=/absolute/path/to/python3.11`; do not replace system Python.
The current adapter defaults to the executable named `g++`, so installing a
versioned GNU compiler alone is insufficient: the local `.venv/bin/g++` symlink
selects it when this environment is activated. Check `g++ --version` after
activation. Run setup and tests in the activated shell (or prefix commands with
`PATH="$PWD/.venv/bin:$PATH"`). Calling `.venv/bin/python` alone does not change
the compiler search path. Recreate the symlink if the venv is recreated; review
its target if Homebrew removes that GCC major version. No system compiler or
reference source is modified. See [checkpoint 08](status/checkpoints/08_macos_setup.md)
for actual verification results.

## Ubuntu / WSL prerequisites

Use Ubuntu inside WSL and the Linux filesystem (for example `~/CMPT479Project`).
Required: Git, Python **3.11** with venv support, and g++ for ESCAPE validation.
No Go compiler, Jupyter installation or notebook-specific environment is needed
for our Python implementation.

```bash
sudo apt-get update
sudo apt-get install git build-essential python3.11 python3.11-venv
python3.11 --version
```

Availability of Python 3.11 depends on configured apt repositories. If unavailable,
use your course-approved CPython 3.11 installation with matching venv/ensurepip;
do not replace Ubuntu's system `python3`. `PYTHON_BIN=/path/to/python3.11` selects
an interpreter for setup. Bootstrap uses system `python3` (3.10+); override with
`BOOTSTRAP_PYTHON` if necessary.

## Git clone

```bash
git clone --recurse-submodules https://github.com/Tanvir-SS/CMPT479Project.git
cd CMPT479Project
bash scripts/bootstrap_references.sh   # checks all pins, fills missing references
bash scripts/setup.sh
source .venv/bin/activate
python -m pytest -q
```

The Phase-7 changes must first be committed and pushed by the project owner.
A private main repository requires GitHub access. All three reference remotes
were publicly reachable without authentication during this phase. If you already
cloned without `--recurse-submodules`, run the same bootstrap command. Never run
an upstream reference's setup, cleanup or graph-partitioning script in place.

## GitHub ZIP download

Download the ZIP for the desired project revision from GitHub's **Code → Download
ZIP**, extract it, and open a terminal in its top-level directory. ZIPs do not
include submodule source, Git history or an initialized `.git` directory.

```bash
bash scripts/bootstrap_references.sh
bash scripts/setup.sh
source .venv/bin/activate
python -m pytest -q
```

Bootstrap uses `third_party/references.json` to fetch the three public HTTPS Git
repositories, checks out each exact commit, and verifies content fingerprints.
It never requires `.git` in the main directory. An interrupted ZIP download is
staged in a temporary directory before installation; partial sources are not
promoted. Repeating bootstrap checks existing sources without downloading again.

Both installation paths were tested using an unpublished source snapshot: an
actual recursive clone of a disposable Git fixture, and a ZIP containing the
same main-repository files with no Git metadata or reference contents. References
were fetched from their real public upstreams. Each copy used a new venv and
hash-verified wheels from the unchanged lock. This is not a claim that unpublished
changes are already downloadable from GitHub. See the checkpoint for outcomes.

## References, pins and overrides

| Reference | Upstream / exact pin | Runtime role |
|---|---|---|
| ESCAPE | [Bitbucket](https://bitbucket.org/seshadhri/escape.git), `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3` | Compiled/executed only for independent exact reference checks |
| DistributedLEDPGraphAlgos | [GitHub](https://github.com/mundrapranay/DistributedLEDPGraphAlgos.git), `b03da893ba1c38d3931708bac919562c5ab57963` | Go source informing k-CoreD and EdgeOrientΔ; no runtime dependency |
| Counting Graphlets of Size k under Local Differential Privacy | [GitHub](https://github.com/gcwsilver/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy.git), `85eff6efa2b1d649ee238620a998ec7f1d305aac` | Two reference notebooks demonstrating 4-cycles; no runtime dependency |

All three are pinned submodules. ESCAPE is Apache-2.0; the Go source is MIT.
No license grant was found in the baseline's three tracked files. **The project
owner reports that the authors granted permission to include their code in this
academic research repository (2026-11-05).** This is the inclusion basis for the
baseline, not a newly assigned software license. Original authorship/source is
preserved. The permission's scope beyond this academic repository is not recorded;
confirm it with the project owner before broader redistribution. No private email
or personal information is included.

Path priority is **explicit argument > environment > bundled checkout**:

| Reference | Argument to fingerprint script | Environment | Default relative to project root |
|---|---|---|---|
| ESCAPE | `--escape-root` (`--escape` alias) | `ESCAPE_ROOT` | `third_party/escape` |
| k-CoreD | `--kcored-root` (`--ledp` alias) | `KCORED_ROOT` | `third_party/DistributedLEDPGraphAlgos` |
| Baseline | `--baseline-root` (`--baseline` alias) | `BASELINE_ROOT` | `third_party/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy` |

The adapter, validation/experiment scripts and pytest accept `--escape-root`.
For pytest use `--escape-root=/absolute/path` (with `=`): a separate absolute
argument can confuse pytest's initial root-directory discovery before its local
option is registered.
The Go and notebook roots are for source inspection/fingerprinting, not estimator
options. Relative reference overrides resolve against the project root, even when
called elsewhere; absolute overrides continue working. Invalid explicit settings
fail instead of falling back. A standalone installed wheel needs absolute overrides
because bundled sources are a checkout feature. Bootstrap intentionally only writes
its own `third_party/` directories; it ignores these environment overrides.

```bash
bash scripts/bootstrap_references.sh --check-only
.venv/bin/python scripts/reference_fingerprints.py --verify
git submodule status
.venv/bin/python -m pytest -q --escape-root=/absolute/path/to/escape
ESCAPE_ROOT=/absolute/path/to/escape .venv/bin/python scripts/check_escape.py
```

Fingerprints cover all tracked files and reject revision/content drift. Historical
`docs/references.json` and experiment provenance retain their original paths;
`docs/references_phase07.json` records the three original read-only trees and
public remote verification. No historical results were rewritten.

## Python environment and counting commands

`setup.sh` installs all pinned, hash-verified dependencies in `.venv`, installs our
package editable with build isolation/dependency resolution disabled, checks
requirements, runs pytest and prints package info. It works from any directory.
Normal setup does not update the lock or compile Go. Missing optional references
do not prevent Python estimation; absent ESCAPE means explicit integration skips.
If ESCAPE is present or explicitly configured but broken, tests fail.

From the project root after activating `.venv`:

```bash
# Exact, NON-PRIVATE truth; separate from released simulation records.
private-graphlets exact-three-stars data/fixtures/star.edges
private-graphlets exact-four-cliques data/fixtures/clique.edges

# Existing research estimators (simulation seeds are not production DP noise).
private-graphlets estimate-three-stars data/fixtures/star.edges --epsilon 2 --seed 123
private-graphlets estimate-four-cliques data/fixtures/clique.edges \
  --epsilon 2 --seed 123 --ordering kcore --cap-mode noisy

# Independently implemented six-factor RR 4-clique comparator.
private-graphlets baseline-four-cliques data/fixtures/clique.edges --epsilon 2 --seed 123

# Full regression and exact-reference checks.
python -m pytest -q
python -m pytest -q -m escape_integration
python scripts/check_escape.py
```

The fixture's true star count is 1; the complete four-vertex fixture has one
4-clique. No private command exposes true degrees or exact truth. Graph files
start with `n m`, use vertex IDs `0..n-1`, include isolates via `n`, deduplicate
undirected edges and reject self-loops. Private negative estimates remain unchanged.

`check_escape.py` builds four original C++ translation units with C++11/g++ into
`build/reference-checks/escape/`, runs eight hand-counted fixtures, and saves raw
ESCAPE output. Pytest compiles to `build/escape-pytest/`. Upstream compiler warnings
are preserved; binaries are never written into source trees. For the previous
24 three-way comparisons plus their existing bounded epsilon diagnostics, use
`python scripts/validate_escape.py`; output paths can be overridden. That command
includes simulations; use `check_escape.py` for exact-only validation.

## Reproduce existing experiments later

### Prepared graph benchmarks (dataset phase 13)

After the project owner commits/pushes these additions, `git pull` or a source
ZIP provides the same 24 small processed graphs and original-ID mappings.
No dataset download is required for normal use. See [data/README.md](../data/README.md)
for all sizes, exact counts, seeds, complete hashes, source conventions and
the Brightkite induced-selection procedure.

```bash
# Existing locked Python 3.11 environment; no private estimates are generated.
python scripts/prepare_real_world_graphs.py verify
python scripts/prepare_real_world_graphs.py verify --escape --brute-force
python -m pytest -q tests/test_graph_datasets.py
# Optional reconstruction: downloads only missing hash-pinned raw archives.
python scripts/prepare_real_world_graphs.py prepare --download
```

On macOS use the activated environment/GNU compiler setup above. New dataset
execution was tested on WSL2; macOS regeneration is not claimed as tested.
Graph/mapping bytes use deterministic ordering and UTF-8/LF. Hash verification
detects drift. Raw archives and execution evidence remain ignored; the two
approved processed directories and manifest are small versioned exceptions.
Preparation always requires actual ESCAPE agreement and independent brute force.
The same `.edges` files work with both private counting CLI commands.

`experiments/configs/four_clique_real_world.json` and
`experiments/configs/four_clique_baseline_2025.json` are future-only configs for
the existing experiment runner. They use the unchanged candidate/baseline budget
allocation at the same total epsilon, independent simulation coordinates and
the original exact K4 target. The existing summary's squared RMSE supplies MSE.
No benchmark was run during dataset preparation; obtain a new instruction before
running these configs. The baseline visits 3,921,225 four-sets per n=100 trial;
runtime feasibility remains unmeasured. No graph loader or privacy mechanism
change was needed.

### Historical experiment commands

These commands reproduce the established grids; **Phase 07 does not run new
utility experiments**. See [3-star experiments](EXPERIMENTS.md) and
[4-clique experiments](FOUR_CLIQUE_EXPERIMENTS.md) for the unchanged definitions.

```bash
python scripts/run_experiments.py run
python scripts/run_experiments.py verify --replay
python scripts/run_experiments.py plot
python scripts/run_four_clique_experiments.py run
python scripts/run_four_clique_experiments.py verify --replay
python scripts/run_four_clique_experiments.py plot
```

Run commands refuse to overwrite existing result directories. Use `--output`
with a new path, then the matching `--results` for verification/plots. Raw results
under `experiments/results/` and figures under `plots/` are ignored, so they must
be reproduced or transferred separately. Existing compact status summaries remain
tracked. Source/config/seed/lock provenance is retained. Timings vary by machine.

The authors' baseline notebooks are not called by these commands. The project's
4-clique baseline is an independent canonical six-factor debiased-RR implementation,
not a direct reproduction of their 4-cycle notebook. **No equivalent baseline
comparison for our private 3-star estimator has been completed.** Future work
requires an independently reviewed 3-star specialization, normalization and
edge-privacy convention, tests and a separately authorized comparison phase.

## Notebook environment and attribution

At the pinned revision there is no package, test suite or dependency lock:
`README.md`, `babarasi_rr_mse.ipynb` and `babarasi_square.ipynb` are the entire tree.
The README lists Python 3.9.12, NetworkX 3.2.1, Matplotlib 3.4.3 and NumPy 1.22.0.
Notebook cells additionally use standard-library `math`, `random`, `itertools`;
an interactive notebook frontend would be required to run them as notebooks.
Those historical versions are not a tested lock. Do not mix them into our Python
3.11 venv. This phase only reads the notebooks; it does not execute or install
their environment. Details and limitations are in [SOURCE_REVIEW](SOURCE_REVIEW.md#phase-07-baseline-inspection-and-portable-references).

## Updating and contributing

First inspect and preserve your own work. Then, from a clean main checkout:

```bash
git status --short
git pull --ff-only
git submodule update --init --recursive
bash scripts/bootstrap_references.sh --check-only
bash scripts/setup.sh
```

`git submodule update` follows the parent repository's pinned gitlinks; do not use
`--remote` for reproduction. Bootstrap refuses to change dirty source trees or an
already populated tree at the wrong revision. Review local changes before manually
updating. Do not reset or delete a collaborator's source changes to make setup pass.
Changing reference pins requires deliberate source review and updated manifest/hashes.

The Phase-7 files and gitlinks must be committed together by the owner; no commit
or push is performed by this phase. `git submodule add` stages `.gitmodules` and
three gitlinks automatically; ordinary source/doc changes still need staging.
Review `git diff` and `git diff --cached`, then use the exact file list in the
[checkpoint](status/checkpoints/07_repository_portability.md) before committing.

## Troubleshooting and offline verification

- **DNS/network failure:** bootstrap reports each failed reference and exits
  nonzero, continuing checks for the others. Check connectivity/proxy settings,
  then retry. Python setup can still run without references. Avoid retrying via
  destructive resets; inspect any partial Git submodule initialization first.
- **Dirty/wrong reference:** inspect `git -C third_party/<name> status` and `rev-parse
  HEAD`. Bootstrap will not discard changes or silently select another revision.
- **Missing `g++`:** install `build-essential`. Read `build/escape-pytest/compile.log`
  for actual compilation errors. Upstream warnings alone are not failed tests.
- **Python/venv mismatch:** select Python 3.11 with `PYTHON_BIN`; install matching
  venv support. Recreate only your disposable `.venv` after preserving any local
  configuration; do not use sudo pip or change system Python.
- **Stale path overrides:** unset `ESCAPE_ROOT KCORED_ROOT BASELINE_ROOT` to use
  bundled paths. Overrides are not silently ignored if invalid.
- **Headless plotting:** use `MPLBACKEND=Agg` and
  `MPLCONFIGDIR="$PWD/.cache/matplotlib"` if needed.

Prepare a wheelhouse while network access is available:

```bash
.venv/bin/python -m pip download --require-hashes -r requirements.lock -d build/wheelhouse
PIP_NO_INDEX=1 PIP_FIND_LINKS="$PWD/build/wheelhouse" bash scripts/setup.sh
```

Reference installation separately needs either existing verified checkouts or
network access. The offline wheelhouse does not contain Git sources. To repeat
our automated portability check (network for references, offline Python wheels):

```bash
.venv/bin/python scripts/check_portable_setup.py --output build/phase07/my-portability-check
```

This makes a disposable Git fixture with the current Git-visible files and pins,
clones it using `--recurse-submodules`, builds/extracts a ZIP-equivalent source
snapshot, bootstraps both twice, and runs setup/full pytest in two new venvs. The
fixture commit exists only in a temporary directory; main history/index are not
changed. Logs, input hashes and a summary are retained under the selected output.
`check_clean_setup.py` is the separate Python-only offline check without references.
Virtual environments, caches, binaries, notebook execution output and large
research artifacts must remain outside the main Git history.
