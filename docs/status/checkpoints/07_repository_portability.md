# Checkpoint 07 — Repository portability and team collaboration

Date: **2026-11-05 (UTC)**. Outcome: **COMPLETE; stopped at the portability boundary**.
No mathematical mechanism, budget, sensitivity bound, orientation rule, experiment
configuration or saved research result was changed. No new utility experiment
was started. Existing bounded simulation tests ran as part of regression/setup.
No main-repository commit or push was performed.

## Starting state and authorization

Read the Phase-7 attachment, AGENTS.md, STATUS.md and latest checkpoint before
editing; inspected current source/setup/review documentation. Starting project
revision: `58f2fadd94329ad9ffb7282e12afee5bef5c816a` (`kcore d 4 clique trial`).
`git status --short --branch` showed a clean `main...origin/main` checkout. The
pre-edit suite passed **376 tests in 26.59s**, no failures/errors/skips, with the
original ESCAPE explicitly configured. Initial file/source hashes and Git state
were saved under ignored `build/phase07/` before changes.

The initial request made baseline bundling conditional on licensing. Inspection
found no license and initially selected a manual-reference fallback. During the
phase, the owner explicitly reported author permission for inclusion of **all
three** references in this academic repository and instructed adding the third
submodule. The final implementation follows that authorization. No license is
invented, and no private correspondence or personal information is published.
Scope beyond this academic repository still requires owner confirmation before
broader redistribution; it does not block the requested inclusion here.

## Actual references and integration

| Reference | Verified public upstream | Exact pinned commit | Integration |
|---|---|---|---|
| ESCAPE | `https://bitbucket.org/seshadhri/escape.git` | `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3` | `third_party/escape`, Git submodule, upstream Apache-2.0 |
| k-CoreD / EdgeOrientΔ | `https://github.com/mundrapranay/DistributedLEDPGraphAlgos.git` | `b03da893ba1c38d3931708bac919562c5ab57963` | `third_party/DistributedLEDPGraphAlgos`, Git submodule, upstream MIT |
| AISTATS baseline notebooks | `https://github.com/gcwsilver/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy.git` | `85eff6efa2b1d649ee238620a998ec7f1d305aac` | `third_party/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy`, Git submodule under reported academic-inclusion permission |

Original paths are `/home/tsshergi/<the respective directory name>`; all remain
unchanged and clean. The original Go remote is SSH
`git@github.com:mundrapranay/DistributedLEDPGraphAlgos.git`; the new public clone
URL uses HTTPS. All three public `git ls-remote` responses matched the inspected
HEADs. All three submodule checkouts are detached at the reviewed commits, with
matching gitlinks and clean tracked content. No original upstream file was copied
into our Python package or edited in either original or bundled checkout.

The baseline has only three tracked files: `README.md`, `babarasi_rr_mse.ipynb`,
`babarasi_square.ipynb`. Both notebooks were read as JSON, not executed. They
implement non-induced **4-cycle** examples, not all six patterns. The first
counts cycles before/after RR without debiasing or a repeated MSE experiment;
the second uses four adjusted edge weights over distinct permutations divided
by eight. Its preliminary true-count loop permits repeated vertices, a source
limitation documented in SOURCE_REVIEW. There is no reusable package/test suite
or locked environment. Historical notebook dependencies are recorded separately;
none was installed. Our independently implemented six-factor 4-clique baseline
is unchanged. The missing equivalent **3-star baseline comparison remains future
work**, not completed by including these notebooks.

## Completed portability behavior

- `.gitmodules` and three Git mode-160000 entries pin the references. The portable
  manifest records URLs, commits, whole tracked-tree digests and reviewed-file
  hashes. Historical `docs/references.json`, prior reports and experiment
  provenance retain their original bytes and paths.
- Shared resolution is explicit root > `ESCAPE_ROOT` / `KCORED_ROOT` /
  `BASELINE_ROOT` > `third_party/` under the project root. Relative overrides also
  anchor at that root, independently of cwd. Absolute overrides continue working;
  bad explicit choices never fall back. Go/notebook paths are inspection inputs,
  not dependencies of estimation.
- `bootstrap_references.sh` works before venv installation. It initializes pinned
  Git submodules or, in ZIP trees, stages public clones, detaches at exact commits,
  checks fingerprints and promotes complete sources. It refuses symlinks, dirty
  trees, nonempty non-repositories, wrong revisions, altered content and changed
  submodule URLs. It reports failures per reference and does not hide unavailable
  sources. No network is needed to recheck already installed sources.
- The Python environment and lock are unchanged. Existing setup remains idempotent;
  it does not bootstrap optional references automatically. Pytest auto-detects
  bundled ESCAPE, skips only absent/uninitialized unconfigured sources, and fails
  explicitly for configured or partial broken sources.
- The Python-only clean-setup utility now skips gitlink directories and clears
  reference overrides. The new portable-setup utility checks actual recursive
  cloning and ZIP bootstrap with public upstreams and new virtual environments.
- README and TEAM_SETUP cover prerequisites, clone/ZIP, reference roles/permission,
  path priority, estimation, baseline, exact validation, existing experiment
  reproduction, Git updates, offline installation and troubleshooting.

## Files changed

All Phase-7 changes are listed below. Submodules are gitlinks, not vendored files.

| Files | Purpose |
|---|---|
| `.gitmodules`; `third_party/escape`; `third_party/DistributedLEDPGraphAlgos`; `third_party/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy` | Three exact pinned submodules using public HTTPS URLs. |
| `third_party/references.json`, `third_party/README.md` | Portable pins/hashes, source roles, author-permission basis and bootstrap instructions. |
| `src/private_graphlets/references.py` | Shared checkout-relative path resolver; no algorithm dependencies. |
| `src/private_graphlets/escape.py` | Only reference-root resolution and configuration-error guidance changed. Build/count/parser/normalization/math are unchanged. |
| `scripts/_reference_tools.py`, `bootstrap_references.py`, `bootstrap_references.sh` | Pre-venv standard-library source integrity and safe Git/ZIP installation. |
| `scripts/reference_fingerprints.py` | All-three inspection and `--verify`, CLI/env/default resolution; retains `--escape`, `--ledp` aliases and historical `ledp` report key. |
| `scripts/check_portable_setup.py` | Reproducible temporary recursive-clone/ZIP/setup checks; no main history changes. |
| `scripts/check_clean_setup.py` | Handle gitlinks in Python-only snapshot setup; remove inherited reference paths. |
| `scripts/check_escape.py`, `validate_escape.py`, `run_experiments.py` | Help text describes new reference fallback; execution/experiment logic unchanged. |
| `tests/conftest.py` | Default bundled ESCAPE detection with explicit skip/failure rules. |
| `tests/test_escape.py` | Isolate missing-default test in a temporary project root; all existing assertions retained. |
| `tests/test_reference_portability.py` | 16 new tests: all-three path priority, cwd independence, pins/manifest safety, modified/wrong trees, atomic ZIP install/failure, symlink/nonrepo rejection, no-fetch/manual and submodule-index/URL guards. |
| `.gitignore`, `MANIFEST.in` | Ignore temporary reference downloads; package metadata/scripts/manifest, exclude actual third-party source and generated artifacts. |
| `README.md`, `AGENTS.md`, `docs/TEAM_SETUP.md` | Current installation/collaboration instructions, permission handling, Phase-7 scope and stop. |
| `docs/SOURCE_REVIEW.md`, `docs/ESCAPE_VALIDATION.md`, `docs/references_phase07.json` | Baseline source audit, current path/setup notes, read-only original fingerprints and public-access evidence. |
| `docs/status/STATUS.md`, `docs/status/portability_07.json`, this checkpoint | Current checklist, actual verification summary and complete execution handoff. |

No changes to `pyproject.toml`, `requirements.lock`, dependency constraints,
`scripts/setup.sh`, any mathematical algorithm module, any experiment module or
configuration, previous checkpoints, compact accuracy summaries or review packages.

## Commands and observed outcomes

Principal commands (project-root cwd unless stated):

```bash
mkdir -p build/phase07
git status --short --branch
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q \
  --junitxml=build/phase07/before.xml > build/phase07/before.log 2>&1

# Read-only inspection: git rev-parse, remote -v, status --porcelain, ls-files;
# JSON parsing of notebook cells; hash every original tracked file.
git ls-remote https://bitbucket.org/seshadhri/escape.git
git ls-remote https://github.com/mundrapranay/DistributedLEDPGraphAlgos.git
git ls-remote https://github.com/gcwsilver/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy.git

git submodule add --name escape https://bitbucket.org/seshadhri/escape.git third_party/escape
git submodule add --name kcored https://github.com/mundrapranay/DistributedLEDPGraphAlgos.git third_party/DistributedLEDPGraphAlgos
git submodule add --name baseline https://github.com/gcwsilver/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy.git third_party/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy
# Each new submodule was checked out --detach at the exact commit in the table.
bash scripts/bootstrap_references.sh
.venv/bin/python scripts/reference_fingerprints.py --verify

.venv/bin/python -m pytest -q tests/test_reference_portability.py tests/test_escape.py \
  --junitxml=build/phase07/portability.xml > build/phase07/portability.log 2>&1
.venv/bin/python -m pytest -q --junitxml=build/phase07/after.xml > build/phase07/after.log 2>&1
ESCAPE_ROOT=/definitely/not-a-reference .venv/bin/python -m pytest -q -m escape_integration \
  --escape-root=/home/tsshergi/escape --junitxml=build/phase07/override_fixed.xml \
  > build/phase07/override_fixed.log 2>&1

.venv/bin/python scripts/check_portable_setup.py --output build/phase07/portable-check \
  > build/phase07/portable-check.log 2>&1
.venv/bin/python scripts/check_clean_setup.py > build/phase07/python_only_setup.log 2>&1
.venv/bin/python scripts/check_escape.py > build/phase07/exact_fixtures.log 2>&1
.venv/bin/python scripts/run_experiments.py verify > build/phase07/three_star_results.log 2>&1
.venv/bin/python scripts/run_four_clique_experiments.py verify > build/phase07/four_clique_results.log 2>&1
.venv/bin/python scripts/reference_fingerprints.py --verify \
  --escape-root /home/tsshergi/escape --kcored-root /home/tsshergi/DistributedLEDPGraphAlgos \
  --baseline-root /home/tsshergi/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy \
  > build/phase07/original_references_after.json

.venv/bin/python -m build --no-isolation > build/phase07/package.log 2>&1
git diff --check
git diff --cached --check
bash -n scripts/bootstrap_references.sh scripts/setup.sh
```

| Check | Actual result |
|---|---|
| Before edits, full suite using original ESCAPE | **376 passed in 26.59s**, no skips/failures. |
| Focused adapter/portability tests (initial two-submodule stage) | **74 passed in 0.83s**; subsequent full tests include revised three-submodule assertions. |
| Full suite, no path overrides, bundled ESCAPE | **392 passed in 28.53s**, no skips/failures; includes **43** real ESCAPE cases. |
| CLI override wins over invalid `ESCAPE_ROOT` | **43 passed, 349 deselected in 19.46s** using original ESCAPE. |
| Fresh recursive Git clone and locked setup | **392 passed in 31.94s**; all three public upstream pins fetched; repeated bootstrap verifies without changing them. |
| ZIP-equivalent extraction and locked setup | **392 passed in 31.39s**; all three public upstream pins fetched; repeated bootstrap verifies without changing them. |
| Fresh Python-only setup, references absent | **349 passed, 43 explicitly skipped in 18.61s**; estimator remains usable. These skips are not labeled ESCAPE passes. |
| Default-location exact ESCAPE fixture command | **8/8** hand-counted graphs agree in all six connected columns; raw output saved separately. |
| Five README/TEAM CLI commands | Exact star=1, exact K4=1; existing private star, k-CoreD clique and independent RR baseline commands succeed with epsilon=2, seed=123. |
| Existing 3-star saved-output verifier | **15 graphs, 75 cells, 37,500 saved trials verified**; no rerun/replay/new trials. |
| Existing 4-clique saved-output verifier | **8 graphs, 160 cells, 16,000 saved trials verified**; no rerun/replay/new trials. |
| Original source integrity | **212/212 tracked files** unchanged: 82 ESCAPE, 127 Go, 3 baseline; all original trees clean. |
| Algorithm/config/results/plot/data preservation | All **87 protected preexisting files** byte-identical; only adapter path resolution changed within existing package files. |
| Packaging and syntax/whitespace | Wheel/sdist build and content checks pass; no upstream source, venv, binaries or generated results included. Shell syntax and both staged/unstaged whitespace checks pass. |

Fresh setup details: a temporary Git fixture contains the current Git-visible
files and exact gitlinks; `git clone --no-local --recurse-submodules` clones that
fixture and fetches the reference HTTPS remotes. A ZIP of the same main files,
with neither `.git` nor reference contents, exercises the archive path. Both
use genuinely new `.venv` directories, Python **3.11.16**, and hash-verified wheels
from the existing wheelhouse. The temporary fixture commit is deleted with the
test directory; no commit is made in the project. Main GitHub Phase-7 clone/ZIP
publication cannot be tested before the owner commits and pushes these changes;
the tested local snapshot has the same file/submodule semantics. The test logs
and exact snapshot hashes are retained under `build/phase07/portable-check/`.
Minor later documentation edits do not alter the tested installation code.

`check_clean_setup.py` separately proves that missing references do not prevent
basic Python setup. `pip check` succeeds in all fresh environments. Dependency
pins were not installed/upgraded in the working venv; fresh venvs install the
same existing lock. Lock SHA-256:
`ffbb7a1cbe39daaaecba70d68bdd163d5e8e27bbf3a39f17a47f6e13fff6ed4f`.

## Problems encountered and resolution

1. Restricted-network Git calls initially failed with DNS resolution errors for
   GitHub/Bitbucket. Authorized network-capable retries succeeded for all three
   public remotes; no credentials or invented URLs were used. No unresolved
   accessibility blocker remains from these tests.
2. The baseline had no license file. The owner explicitly authorized inclusion
   after reporting author permission; it is a third submodule with that limited
   permission provenance, not a newly licensed or silently copied package.
3. The first explicit pytest override used a separate absolute argument:
   `--escape-root /home/tsshergi/escape`. Pytest selected `/home/tsshergi` as root
   before loading this project's local option and exited **4** with “unrecognized
   arguments”. No tests ran in that failed invocation. Using
   `--escape-root=/home/tsshergi/escape` fixes discovery; 43 cases pass. Current
   instructions use the equals form. Script/API overrides are unaffected.
4. Gitlink directories would break the older file-copy setup utility. It now
   excludes directories and tests Python-only setup explicitly. A separate runner
   verifies the complete recursive clone and ZIP behavior.

5. The first final hash audit included generated `src/*.egg-info/` metadata in
   its protected-source list. Packaging correctly regenerated README/package
   metadata, causing that audit assertion to fail. The audit now distinguishes
   ignored generated metadata from source/data; all 87 actual protected files
   remain byte-identical. No algorithm or result was repaired or changed.

No correctness assertion, statistical tolerance or expected research value was
weakened. Existing missing-default adapter assertions were retained and isolated
from the newly populated real checkout with a temporary root. No algorithm or
experimental finding was modified to pass tests.

## Files to commit and owner commands

`git submodule add` has staged `.gitmodules` and the three gitlinks. Other changes
remain unstaged/untracked for review. Generated evidence is intentionally ignored.
After reviewing the complete diff, the owner can run:

```bash
git status --short
git diff
git diff --cached --submodule=short
git add .gitignore .gitmodules AGENTS.md MANIFEST.in README.md third_party \
  src/private_graphlets/references.py src/private_graphlets/escape.py \
  scripts/_reference_tools.py scripts/bootstrap_references.py scripts/bootstrap_references.sh \
  scripts/check_portable_setup.py scripts/check_clean_setup.py scripts/reference_fingerprints.py \
  scripts/check_escape.py scripts/validate_escape.py scripts/run_experiments.py \
  tests/conftest.py tests/test_escape.py tests/test_reference_portability.py \
  docs/TEAM_SETUP.md docs/SOURCE_REVIEW.md docs/ESCAPE_VALIDATION.md docs/references_phase07.json \
  docs/status/STATUS.md docs/status/portability_07.json docs/status/checkpoints/07_repository_portability.md
git diff --cached --check
git diff --cached --stat
git submodule status
git commit -m "Make reference setup portable for team collaboration"
git push --recurse-submodules=check origin main
```

Do not force-add generated artifacts or files inside submodules. Check that Git
shows three mode-160000 entries instead of thousands of vendored source files.
No command in this block was run to commit or push the main repository.

## Remaining work and stop

- The owner must review, commit and push before the partner can download Phase 07
  from GitHub. Raw research artifacts remain ignored; reproduce or transfer them
  separately as already documented.
- Author-permission scope beyond this academic inclusion is not recorded. Confirm
  before broader redistribution; do not infer an open-source license for notebooks.
- Formal executable privacy/utility review remains as recorded in Phase 06.
  Portability tests do not resolve any mathematical proof obligation.
- Future equivalent 3-star baseline implementation/comparison requires separate
  authorization. Notebook availability does not supply it automatically.

**STOP. No privacy verification phase, algorithm optimization, new counting
pattern, utility experiment or automatic commit/push follows this checkpoint.**
