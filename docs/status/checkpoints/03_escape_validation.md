# Checkpoint 03 — ESCAPE integration and validation

Date: **2026-10-28** (America/Vancouver).
Outcome: **complete; stopped at the requested boundary**.

## Authorized scope and starting state

The user explicitly authorized ESCAPE integration after phase 02: inspect/build
the real size-4 executable, implement a reusable adapter, compare three exact
methods on small synthetic graphs, and check private estimates at a few epsilon
values. This supersedes the earlier ESCAPE stopping restriction for this scope
only. No full epsilon grid, large dataset run, new private algorithm, orientation
implementation or private 4-clique development was begun.

Read AGENTS.md, STATUS.md, checkpoints 01 and 02, SOURCE_REVIEW.md and existing
implementations/tests before changes. Started from a clean worktree at
`7c917674a12b2c8739317e5b44bccbb9ca253a88` (`3 star counting`). Changes remain
local and uncommitted; no commit or push was performed. Earlier checkpoints,
graph/exact/noise/estimator implementations and the dependency lock are preserved.

## Completed work and files

| File | Change |
|---|---|
| `src/private_graphlets/escape.py` | Configurable source resolution, isolated direct C++ build with hashes/logs, canonical input normalization, strict 17-line parser, typed failures, `EscapeAdapter.run` and `count_three_stars`. |
| `src/private_graphlets/escape_validation.py` | 24 deterministic small cases, separately labeled three-way comparisons, two-graph controlled epsilon diagnostic. |
| `scripts/validate_escape.py` | Build/run command, real output/provenance report, failure status and nonzero exit, separate raw simulation samples. |
| `scripts/check_escape.py` | Original eight-fixture command now uses the reusable adapter; retains `--source` alias and supports `--escape-root`/environment. |
| `tests/conftest.py` | Pytest root option/environment and session build fixture; skips only when unconfigured. |
| `tests/test_escape.py` | 58 unit cases: canonicalization, parser, signed zero, scope, roots, compile/execution failures, timeouts, missing/stale/unreadable output and cleanup. Stubs are unit fixtures only. |
| `tests/test_escape_integration.py` | 33 real tests: 24 three-way cases, 8 original six-column fixtures and 4 concurrent invocations in one test. |
| `pyproject.toml` | Register `escape_integration` marker; dependency pins unchanged. |
| `src/private_graphlets/cli.py` | Info phase identifier updated; existing private/exact behavior unchanged. |
| `README.md`, `docs/ESCAPE_VALIDATION.md` | Reproduction, API, source protocol, normalization, actual counts/statistics and limitations. |
| `AGENTS.md` | Phase-03 authorization/stop, configurable ESCAPE and evidence rules. |
| `docs/ALGORITHMS.md`, `docs/PRIVACY_NOTES.md`, `docs/SOURCE_REVIEW.md`, `experiments/README.md` | Current phase links and explicit non-private evaluation boundary; mathematical specification unchanged. |
| `docs/status/STATUS.md`, this checkpoint, `docs/status/validation_03.json` | Current checklist, execution record and actual structured evidence. |

Ignored artifacts: binaries and build provenance in `build/escape/`,
`build/escape-pytest/`, `build/reference-checks/escape/`; logs, raw simulation
samples, failed-run evidence and distribution artifacts under `build/phase03/`.
The small tracked validation JSON intentionally retains synthetic graph inputs,
raw ESCAPE output/stdout/stderr, each separately named count and diagnostic
summaries. It is explicitly non-private evaluation, never a private release.

## Source findings and build

Reviewed upstream README, Makefile/common.mk, executable Makefile,
`exe/count_four.cpp`, `GraphIO.cpp`, `Escape/GetAllCounts.h`,
`Escape/FourVertex.h` and wrapper behavior. ESCAPE commit remains
`7ec2f93c524a0b47cdc8c639602e90d1c1fceff3`.

The original README uses `make` and the Python wrapper. We compile the four
original translation units directly with g++ C++11, `-O2 -Wall`, avoiding the
upstream `-lc++` setting. Compilation writes only into project build directories.
No upstream Makefile/setup/wrapper was executed, and no source was patched.
The actual argv, compiler version, source hashes, binary hash, return code and
warning count are in `build.json` and the saved validation report.

Input is `n m` plus one row per unique undirected edge; the loader inserts both
directions and lacks robust duplicate/loop/range checks. We validate before
serialization. Graphs with fewer than four vertices get additional isolates;
connected four-vertex counts are preserved. All cases invoke the binary,
including zero vertices after normalization. Other pattern columns correspond
to the normalized graph, not necessarily the original.

`count_four` writes `out.txt` in cwd: `n`, **2m**, four three-vertex counts,
eleven four-vertex counts. Connected patterns occupy lines 12–17 in the order
star, path, tailed triangle, cycle, diamond, clique. `getAllFour` writes
non-induced counts even though a comment mentions induced conversion. No induced
wrapper conversion is used. `easyFourCounter` independently implements the same
degree identity as our formula; enumeration is a different counting procedure.

K4 returned `[4,12,12,3,6,1]`, K5 `[20,60,60,15,30,5]`. Their 3-star values
4 and 20 (versus zero induced stars) verify the intended semantics. Existing
upstream clique columns were read, not reimplemented as a new estimator.

## Commands and actual outcomes

Read-only inspection used `git status --short`, `git rev-parse HEAD`, `rg`,
`cat` and `sed` on project/reference sources, instructions, tests and build files.
Edits used patch tools; one documentation patch failed its context check and
was reapplied with corrected context before any files in that patch changed.

Substantive commands run from the project (logging wrappers omitted where they
do not change command behavior):

```bash
.venv/bin/python -m pytest -q tests/test_escape.py
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python scripts/validate_escape.py --output docs/status/validation_03.json
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q

# Explicit-root and legacy-alias paths were also exercised:
.venv/bin/python scripts/validate_escape.py --escape-root /home/tsshergi/escape --output docs/status/validation_03.json
.venv/bin/python scripts/check_escape.py --source /home/tsshergi/escape
env -u ESCAPE_ROOT .venv/bin/python -m pytest -q tests/test_escape_integration.py

.venv/bin/python -m pip check
sha256sum requirements.lock
.venv/bin/python -m private_graphlets info --json
.venv/bin/python -m build --no-isolation --outdir build/phase03/dist
git diff --check
```

Final configured tests and both comparison commands used `set -o pipefail` with
`tee` to retain `build/phase03/pytest.log`, `validation.log` and
`legacy-fixtures.log`. The packaging command was captured to `package-build.log`.
The builder's expanded g++ command is documented in ESCAPE_VALIDATION.md; its
argv includes absolute reference paths and a temporary output under build/.

| Check | Observed result |
|---|---|
| Initial adapter unit tests | **51 passed in 0.50s**. |
| Initial full suite | **222 passed in 11.35s**, configured real ESCAPE. |
| Initial comparison script | **24/24 exact matches**, six diagnostic means and both MSE trends passed. |
| After stricter decimal syntax validation | **4 failed, 224 passed in 11.83s**: signed zero rejected on edgeless inputs. Comparison script exited 1 with zero completed cases; legacy script passed seven fixtures then failed on edgeless. |
| Corrected final full suite | **229 passed in 13.80s**, no failures/errors/skips. |
| Corrected comparison script | **24/24 exact matches**, status `passed`, exit 0. |
| Corrected legacy fixture script | **8/8 six-column matches**, exit 0. |
| Optional unconfigured integration suite | **33 skipped in 0.22s**, explicitly because ESCAPE was unconfigured. Not counted as passed comparisons. |
| C++ compilation | Exit 0, g++ **11.4.0**, **160 upstream warnings** per build. |
| Dependency consistency | `No broken requirements found.` Lock and 25 dependency pins unchanged. |
| Packaging | Wheel and source archive built successfully with no build isolation. |
| External source integrity | 82 ESCAPE and 127 Go tracked files match recorded fingerprints; both clean. |

The signed-zero regression was introduced when tightening syntax to reject
underscores/exponents. ESCAPE prints `-0.000000` for a disconnected count on an
edgeless graph. The corrected parser accepts signed decimal syntax, then
requires a nonnegative integral numeric value. Signed zero becomes integer
zero; any strictly negative count fails. A dedicated regression test covers it.
This change does not clip/round any private estimate. Failed-run records remain
in ignored `pytest-signed-zero-failure.log`, `validation-signed-zero-failure.json`
and `legacy-signed-zero-failure.log` under `build/phase03/`.

## Bounded diagnostic results

The 24-case suite has 12 named/boundary cases, 6 ER cases (n=10, p=0.2/0.6)
and 6 BA cases (n=12, m=1/2), using graph seeds 11, 29, 47. Cases include all
requested named graphs, overlap, disconnected components, isolates, and n=0–3
normalization. Repeated fixture/concurrency calls are not counted as additional
cases in this total. Full per-case counts appear in ESCAPE_VALIDATION.md/JSON.

Private checks preselected K1,4 and K5, epsilon 1/2/4, 3,000 trials each:
**18,000 total**, using six separately recorded seeds. Each trial calls the
existing public estimator with an advancing NumPy Generator. Truth is the real
ESCAPE count after three-way agreement. No mechanism code/formula was changed.
All six means are within six analytic standard errors; maximum absolute
standardized deviation **1.759120**. Empirical MSE decreases as epsilon rises:

- K1,4: **4416.817937 → 169.066680 → 14.567210**.
- K5: **8468.006126 → 546.175430 → 68.412908**.

Raw estimates, including negatives, remain in
`build/phase03/epsilon_samples.json`; summary moments are in validation_03.json.
These observations support expected behavior in the selected runs. They are not
formal unbiasedness/accuracy/privacy proofs, confidence guarantees for all
graphs, or a full epsilon experiment grid.

## Dependencies, limitations and next steps

No dependencies were installed or upgraded. Existing CPython **3.11.16**,
NumPy **2.2.6**, NetworkX **3.4.2**, pytest **8.3.5** and the phase-01 lock were
used. Lock SHA-256 remains
`ffbb7a1cbe39daaaecba70d68bdd163d5e8e27bbf3a39f17a47f6e13fff6ed4f`.
`pip check` emitted a harmless unwritable home-cache warning and disabled that
cache; it found no broken requirements. No permissions escalation was needed.

The adapter intentionally caps inputs at 1,000 vertices and rejects counts
at/above 2**53; behavioral cases have at most 12 vertices. This does not certify
all upstream arithmetic, performance, other compilers or other ESCAPE revisions.
Warnings, upstream allocation leaks and numeric limitations remain unchanged;
process isolation bounds per-run lifetimes. No sanitizer or large-graph study
was performed. Normalized disconnected/three-vertex columns need care.

NumPy noise is simulation-only. The privacy model, endpoint budget accounting,
finite precision, repeated-release composition and formal accuracy questions
still require independent mathematical review. Reports expose exact synthetic
data and must never be represented as private releases for protected inputs.

**STOP.** Await explicit phase-04 authorization before full privacy experiments,
large datasets, ESCAPE extensions or 4-clique development. Create the next
numbered checkpoint and update STATUS.md only when that phase is authorized.
