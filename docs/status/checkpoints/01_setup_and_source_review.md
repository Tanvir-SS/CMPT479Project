# Checkpoint 01 — Setup and source review

Date: **2026-10-28** (America/Vancouver).
Outcome: **complete; stopped at the user-requested boundary**.

## Authorized scope and completed work

Prepared `/home/tsshergi/CMPT479Project` for reproducible CMPT 479/982 research,
reviewed both supplied source repositories, and verified setup and reference
interfaces. Implemented an information-only CLI and smoke tests. **No private
3-star estimator, other private algorithm, or private experiment was started.**

The working directory already contained Git metadata with an unborn `main`
branch and origin `git@github.com:Tanvir-SS/CMPT479Project.git`, plus protected
environment metadata directories. Existing Git configuration was preserved.
Project files have not been committed or pushed. No system package installation
was needed; all Python installs were confined to project/temporary virtual
environments. Source inspection and checks left both external repositories clean.

## Files and directories created

| Files | Purpose |
|---|---|
| `README.md` | Ubuntu/WSL, clone/setup, CLI, tests, dependency updates, offline recreation, reference checks and scope. |
| `AGENTS.md` | Permanent mathematical, reproducibility, reporting, source preservation and stopping-point rules. |
| `pyproject.toml`, `.python-version`, `.gitignore`, `MANIFEST.in` | Python 3.11 packaging, dependency pins, pytest configuration, artifact exclusions and source-distribution contents. |
| `requirements.lock`, `requirements-constraints.txt` | Full hash-checked lock and explicit Matplotlib/parser compatibility constraint. |
| `src/private_graphlets/{__init__,__main__,cli}.py` | Installable package, module entry point and `private-graphlets info [--json]`. |
| `tests/test_smoke.py` | Installed CLI/module/version checks and NumPy/NetworkX/pandas/headless Matplotlib integration. |
| `scripts/{setup,lock_dependencies}.sh` | Repeatable installation and deliberate lock regeneration. |
| `scripts/check_clean_setup.py` | Fresh temporary offline environment check from Git-visible source files. |
| `scripts/check_escape.py` | External C++ compilation and eight hand-counted reference checks; no new counting algorithm. |
| `scripts/reference_fingerprints.py` | Read-only commit/status and source-content hashing. |
| `data/fixtures/*.edges`, `expected_counts.json`, `README.md` | Eight synthetic graphs and independently hand-derived expected connected counts. |
| `data/README.md`, `data/{raw,processed}/README.md` | Data placement and provenance rules. |
| `experiments/README.md`, `experiments/{configs,results}/README.md`, `plots/README.md` | Reserved future research directories and reproducibility guidance. |
| `docs/SOURCE_REVIEW.md`, `docs/references.json` | Function-level source review, mathematics, concerns, pinned source provenance. |
| `docs/status/STATUS.md`, this checkpoint, `docs/status/environment_01.json` | Current phase checklist, execution record and machine-readable installed versions. |

Ignored local artifacts: `.venv/`, `.cache/`, `build/`, `dist/`, editable package
metadata and Python/test caches. No external source files were copied into
`src/private_graphlets/`. The isolated Go archive is under ignored `build/`.

## Environment and installed dependencies

Verified environment: Ubuntu **22.04.3 LTS**, WSL2 x86_64, CPython **3.11.16**,
g++ **11.4.0**, Go **1.26.4**, Git **2.34.1**. System `python3` is 3.10.12 and was
not changed. `python3.11 -m pip` was initially unavailable outside a venv;
`python3.11 -m venv .venv` succeeded and supplied pip 24.0, later replaced by
the locked pip version inside `.venv`.

Final installed dependencies (25; all match `requirements.lock`):

```text
build==1.2.2.post1       click==8.5.0             contourpy==1.3.3
cycler==0.12.1          fonttools==4.68.0        iniconfig==2.3.1
kiwisolver==1.5.1       matplotlib==3.10.1       networkx==3.4.2
numpy==2.2.6            packaging==26.3         pandas==2.2.3
pillow==13.0.0          pip==25.1.1             pip-tools==7.5.0
pluggy==1.7.0           pyparsing==3.2.3        pyproject-hooks==1.3.3
pytest==8.3.5           python-dateutil==3.0.0   pytz==2026.5
setuptools==80.9.0      six==1.17.0             tzdata==2026.6
wheel==0.45.1
```

Project distribution: `private-graphlets==0.1.0` installed editable. The bootstrap
resolver initially installed build 1.6.1; installing the final lock replaced it
with 1.2.2.post1. The first lock used pyparsing 3.3.3; it was changed to 3.2.3
after the observed smoke-test failure. No other package upgrades are implicit
in normal setup. The complete hashes are in the lock, whose SHA-256 is
`ffbb7a1cbe39daaaecba70d68bdd163d5e8e27bbf3a39f17a47f6e13fff6ed4f`.

Go's existing `go.mod`/`go.sum` resolved the following dependencies into the
project's local Go cache, without changing either original repository:
`github.com/google/differential-privacy/go/v2 v2.1.0`,
`github.com/dgravesa/go-parallel v0.6.0`, `gopkg.in/yaml.v2 v2.4.0`,
`golang.org/x/exp v0.0.0-20240416160154-fe59bbe5cc7f`,
`github.com/golang/glog v1.1.1`, and `gonum.org/v1/gonum v0.12.0`.

## Commands run and observed results

Read-only discovery used `pwd`, `ls -la`, `rg --files`, `rg -n`, `nl -ba`, `sed`,
and `cat` on the supplied code, READMEs, build files and licenses. Checked parent
instruction paths; no applicable preexisting project `AGENTS.md` was found.
Used `git status --short`, `git rev-parse HEAD` and `git remote -v` in the project
and references. The project HEAD lookup correctly failed because no commit yet
exists. Checked `python3 --version`, `python3.11 --version`, `go version`,
`g++ --version`, `git --version`, `uname -a` and `/etc/os-release`.

The substantive setup/verification commands, run from the project unless noted:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir pip==25.1.1 setuptools==80.9.0 wheel==0.45.1 pip-tools==7.5.0
bash scripts/lock_dependencies.sh
.venv/bin/python scripts/reference_fingerprints.py > docs/references.json
.venv/bin/python scripts/check_escape.py
bash scripts/setup.sh
# After diagnosing the parser warning and adding its compatibility constraint:
bash scripts/lock_dependencies.sh
bash scripts/setup.sh
.venv/bin/python -m build --no-isolation
PIP_CACHE_DIR="$PWD/.cache/pip" .venv/bin/python -m pip download --disable-pip-version-check --require-hashes -r requirements.lock -d build/wheelhouse
.venv/bin/python scripts/check_clean_setup.py
```

`setup.sh` executes hash-checked lock installation, an editable install with
`--no-deps --no-build-isolation`, `pip check`, `python -m pytest -q` and the CLI.
Initial sandbox network restrictions blocked pip/Go DNS access. Repeating the
downloads through the authorized network-enabled execution path succeeded.
No auto-review rejection or unresolved permission block occurred.

The ESCAPE script ran this compile command (absolute paths in the actual log):

```bash
g++ -std=c++11 -O2 -Wall -I /home/tsshergi/escape \
  /home/tsshergi/escape/exe/count_four.cpp \
  /home/tsshergi/escape/Graph.cpp /home/tsshergi/escape/GraphIO.cpp \
  /home/tsshergi/escape/TriangleProgram.cpp \
  -o build/reference-checks/escape/count_four
```

It then invoked the compiled binary on each fixture in its own working directory,
checked `n,2m`, checked 17 output lines, and compared connected count lines 12–17
using `Decimal` against integer expectations. The original Makefile and wrapper
were inspected but not run. No libc++ or other C++ dependency was installed.

For Go, created and checked an isolated source archive:

```bash
mkdir -p build/reference-checks/go-source
git -C /home/tsshergi/DistributedLEDPGraphAlgos archive b03da893ba1c38d3931708bac919562c5ab57963 | tar -x -C build/reference-checks/go-source
export GOCACHE="$PWD/.cache/go-build"
export GOMODCACHE="$PWD/.cache/go-mod"
export GOPATH="$PWD/.cache/go"
export GOTOOLCHAIN=local
(cd build/reference-checks/go-source && go test ./...)
(cd build/reference-checks/go-source && go build ./...)
```

Both final Go commands exited **0**. `go test` printed `[no test files]` for
`algorithms`, `cmd`, `data-structures`, `experiments` and `noise`. This is build
evidence only; no benchmark, private graph run, or upstream experiment driver
was executed. Go's original setup/cleanup scripts were not executed.

Additional checks used installed package metadata to compare all 25 versions
against the lock and write `environment_01.json`; fingerprints were recomputed
and compared byte-for-byte to `docs/references.json`. `pip freeze --all` was
also inspected, but warned that it could not identify the editable project's
VCS revision because HEAD does not exist. It was **not** used as the dependency
lock; pip-tools and installed distribution metadata provide the recorded pins.

Final documentation/package checks ran `bash -n scripts/setup.sh
scripts/lock_dependencies.sh`, rebuilt the wheel/source archive after adding
`MANIFEST.in` and status files, and inspected `private-graphlets info --json`.
A local-file audit found valid relative Markdown links and no trailing whitespace
across 39 project files. Recomputed fingerprints matched all 82 tracked ESCAPE
files and 127 tracked Go-reference files, with empty Git porcelain output for
both. The installed-version and lock-hash checks also passed.

### Actual test outcomes

| Check | Actual result | Evidence / scope |
|---|---|---|
| Initial Python setup | **1 failed, 3 passed in 0.36s** | pyparsing 3.3.3 raised `PyparsingDeprecationWarning: 'oneOf' deprecated` through Matplotlib, treated as an error. |
| Corrected Python setup | **4 passed in 0.99s** | `build/setup.log`; no warning suppression added. |
| `pip check` | **No broken requirements found.** | Both main and fresh setups. |
| Fresh offline setup | **4 passed in 0.95s** | `build/reproduction-check.log`; new temporary copy and venv, invoked outside project directory, no network index. |
| ESCAPE fixtures | **8/8 matched** | Table below and `build/reference-checks/escape/results.json`. |
| C++ compile | **Exit 0; 160 upstream warnings** | `build/reference-checks/escape/compile.log`; includes `%lld`/`int64_t` mismatches and unused variables. |
| Go test/build | **Exit 0**, five packages, **no test files** | `build/reference-checks/go-test-network-enabled.log`, `go-build.log`. |
| Package build | **Wheel and source archive built** | `build/package-build.log`, `dist/`; packaging check, not a publication. |
| Installed dependency pins | **25/25 exact matches** | `docs/status/environment_01.json`. |
| External source integrity | **Fingerprints unchanged; clean worktrees** | `docs/references.json`; tracked content hashes and porcelain state. |

CLI smoke tests run subprocesses from a temporary directory, checking installed
entry points rather than relying on source-directory imports. The scientific
smoke test imports all four libraries and writes a PNG using `Agg`; that image
is a test artifact, not a research plot.

ESCAPE actual vectors, ordered star/path/tail/cycle/diamond/clique:

| Fixture | Expected and observed |
|---|---|
| `star.edges` | `1, 0, 0, 0, 0, 0` |
| `path.edges` | `0, 1, 0, 0, 0, 0` |
| `tailed_triangle.edges` | `1, 2, 1, 0, 0, 0` |
| `cycle.edges` | `0, 4, 0, 1, 0, 0` |
| `diamond.edges` | `2, 6, 4, 1, 1, 0` |
| `clique.edges` | `4, 12, 12, 3, 6, 1` |
| `clique_with_isolates.edges` | `4, 12, 12, 3, 6, 1` |
| `edgeless.edges` | `0, 0, 0, 0, 0, 0` |

These are finite interface/regression checks, not exhaustive correctness or
large-graph performance evidence. The edgeless fixture has four vertices.

## Source findings

Full explanations, line references, mathematics and limitations are in
[SOURCE_REVIEW.md](../../SOURCE_REVIEW.md). Key findings:

- ESCAPE's `easyFourCounter` computes stars, paths, tails and diamonds;
  `fourCycleCounter` and `fourCliqueCounter` complete the six.
  `getAllFour` stores them in indices 5–10 of an 11-count non-induced array.
- `count_four` relabels by exact degree/ID, builds a degree-ordered DAG, sorts
  adjacency by ID and writes 17 lines. Its second output line is `2m`. This is
  separate from the optional induced conversion in the Python wrapper.
- Reviewed the degree/triangle identities and induced-to-non-induced conversion
  matrix. Exact degree orientation is not private and is not degeneracy peeling.
- Go's private levels use noisy degree-derived round caps, noisy same-level
  neighbor counts, promotion bits and coordinator barriers. The triangle path
  releases RR adjacency, computes a noisy out-degree bound, and sums locally
  noised weighted outgoing-wedge counts.
- Verified RR's elementary debiasing relationship on paper, and documented the
  actual API budget flow. No proof of total privacy composition is claimed.
- Go equal-level neighbors are selected by independent coins at each endpoint
  and are resampled for later stages, unlike a consistent total order. The
  all-equal-level triangle has analytic expected outgoing-wedge multiplicity
  `3/4` without clipping; this is a deduction from the code, not an experiment.
- The Go driver overrides YAML epsilon with 1.0, uses factor 0.8 and an absolute
  author's result path. Noise/bias switches are not consistently respected.

## Known issues and remaining limitations

- Resolved locally: network access restrictions for initial downloads and the
  Matplotlib/parser compatibility failure. Project caches live under `.cache/`.
- ESCAPE retains upstream warnings, weak input checks, integer/float precision
  limits, scratch-allocation leaks, and a potential final-removal bounds issue
  in the unused degeneracy routine. No external source fixes were made.
- The Go implementation retains inconsistent ties, possible clipping bias,
  unverified weighted-query sensitivity, missing input/parameter checks,
  empty-partition channel deadlock risk, dense quadratic state, and mixed random
  sources without a seed/replay interface. The separate RR k-core baseline
  mistakes matrix values for neighbor IDs. Details are source findings, not
  broad claims based on the compile checks.
- No full research datasets, paper-result reproduction, sanitizers, exhaustive
  graph enumeration, Go runtime/race tests, or formal privacy proof were run.
- Normal setup is hash-locked for Python 3.11 on Ubuntu/Linux; other platforms
  and floating point backends are not claimed to be bitwise equivalent.
- This phase leaves local files ready for review. A student can clone and use
  them once the project owner publishes a commit; no remote push was requested.

## Next steps — deferred, not started

Wait for explicit authorization of the next phase. First establish the precise
LEDP neighboring relation, edge/report ownership, count normalization, public
assumptions and a consistent total order. Then plan exact small-graph oracles
and derive estimator correctness, clipping effects, sensitivity, privacy
composition and variance before implementation. **Do not begin the private
3-star estimator as part of this checkpoint.** Create checkpoint 02 and update
`docs/status/STATUS.md` when a later phase is authorized.
