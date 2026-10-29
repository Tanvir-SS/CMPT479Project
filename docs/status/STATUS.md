# Project status

Updated: **2026-10-28** (America/Vancouver).

**Current phase: 01 — Setup and source review COMPLETE. STOP POINT REACHED.**
The environment, package scaffold, documentation, reference review and initial
checks are complete. No private estimator or private experiment is implemented.
Do not start the private 3-star estimator without an explicit later instruction.

## Current phase checklist

- [x] Inspect ESCAPE's six connected non-induced counts, orientation, and formats.
- [x] Inspect k-CoreD / EdgeOrientΔ levels, RR, noise, coordinator and aggregation.
- [x] Document mathematical identities, code-to-paper differences and source issues.
- [x] Create the `src/private_graphlets/` package, CLI and research directories.
- [x] Create Python 3.11 `.venv`, pinned dependencies, hashed lock and setup scripts.
- [x] Configure pytest and verify the installed CLI and scientific stack.
- [x] Verify clean offline recreation in a fresh temporary environment.
- [x] Compile ESCAPE externally and check eight hand-counted fixtures.
- [x] Compile/check the Go code in an isolated archive of the pinned source.
- [x] Document Ubuntu/WSL setup and establish permanent `AGENTS.md` instructions.
- [x] Record source fingerprints, environment versions and checkpoint 01.
- [x] Verify both external reference repositories remain unchanged.
- [x] Stop at the requested boundary; private 3-star estimation remains unstarted.

## Validation and limitations

- Main Python setup: **4 passed in 0.99s**; dependency check succeeded.
- Fresh offline environment: **4 passed in 0.95s**; dependency check succeeded.
- ESCAPE: **8/8** fixture vectors matched; compiled with upstream warnings.
- Go: `go test ./...` and `go build ./...` succeeded; all five packages report
  **no test files**. No Go accuracy or privacy validation was performed.
- Wheel and source distribution build succeeded. All **25** installed locked
  dependency versions match; exact versions are in [environment_01.json](environment_01.json).
- Reference fingerprints matched before/after checks and both Git worktrees are
  clean. Project files are local and uncommitted; the existing `main` branch has
  no commits, and nothing was pushed.

The first Python test run exposed a Matplotlib/pyparsing incompatibility under
warnings-as-errors; pyparsing 3.2.3 resolved it. Reference issues remain documented,
including Go's inconsistent tie orientation, driver parameter overrides, clipping
and sensitivity questions, and ESCAPE's numeric/input limitations. There is no
formal DP proof or empirical research result for this project yet.

## Reports and next phase

- [Checkpoint 01: setup and source review](checkpoints/01_setup_and_source_review.md)
- [Source review](../SOURCE_REVIEW.md)
- [Reference commits and hashes](../references.json)
- [Reproduction instructions](../../README.md)

Await the next explicit scope. Suggested future prerequisites are a precise LEDP
model and count specification, a consistent orientation contract, exact small-graph
oracles, and mathematical derivations before any private implementation. These
are suggestions only, not active work. For each authorized future phase create
`checkpoints/02_<phase>.md` (then 03, 04, …) and update this checklist and summary.
