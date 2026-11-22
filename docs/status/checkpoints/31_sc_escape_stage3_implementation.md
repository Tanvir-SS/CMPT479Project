# Checkpoint 31 — SC-ESCAPE Stage 3 implementation

2026-11-22 (America/Vancouver). **Stage 3 COMPLETE; STOP before Stage 4/5.**
Starting revision: `24239de210d69c47a1fdc945536d6095eecdb646`; starting
`git status --short` was empty. The explicit pasted SC-ESCAPE task authorizes
this separate implementation and small checks beyond historical phase stops.
It does not authorize a standardized evaluation or new baseline work.

## Completed work and files

Created:

- `src/private_graphlets/four_path_sc_escape.py`: validated four-parameter budget;
  four reproducible independent simulation streams; client-local degree, lower-RR,
  degree-product and triangle reports; two-round driver, transcript and aggregate
  result APIs. Public D_max is mandatory and validated without estimating it.
- `tests/test_four_path_sc_escape.py`: 46 focused cases covering the supplied
  identity and report mechanisms, bounds, serialization and repeatability.
- `docs/SC_ESCAPE_IMPLEMENTATION.md`: API example, equations, public degree domain,
  budget accounting, transcript/schedule boundaries, costs and limitations.
- `docs/status/checkpoints/31_sc_escape_stage3_implementation.md`: this record.

Modified: `docs/status/STATUS.md`, prepending the current phase checklist while
preserving all historical status text. No existing algorithm/test/runner was
modified. No dataset, fixture, manifest, dependency, ground-truth cache, prior
result, reference source or pin was changed. No commit, staging or push.

## Implementation decisions

The supplied estimator is implemented without clipping, rounding, cap selection,
private D_max, budget optimization or changes to the old five-stage estimator.
Actual total epsilon is `2*degree + rr + product + triangle`, derived from the
four explicit parameters, with no independent nominal total to become stale.

Reused `SimpleGraph`, `validate_epsilon` and `rr_parameters`. Existing degree-noise
utilities use 2/epsilon, whereas this task requires 1/epsilon_D, so the new local
degree function samples the specified scale directly. Existing RR uses upper-row
ownership by the smaller ID; the new lower-row sampler uses the same shared
probability calculation and assigns each unordered pair to its larger ID.
There is exactly one report per pair, including nonedges, and no change to shared
RR code. The packed lower table is broadcast in full, not fetched using private
neighbor queries. The product component similarly receives all degree reports.

Round 2 product scale is exactly `2*abs(dhat_v-1)*H/epsilon_S`; triangle scale is
the supplied `D_max/epsilon_T`, even for a loose bound. `tanh(epsilon_R/2)` is used
for the mathematically identical denominator 1−2p. Isolated vertices participate;
zero sensitivity has zero-scale noise. Arithmetic failures raise errors without
retrying or changing estimates. No implementation/specification conflict was found
in these targeted checks; no general correctness/privacy certification is inferred.

## Commands and observed outcomes

Executed from `/Users/harrygupta/CMPT479Project`:

```bash
.venv/bin/python --version
.venv/bin/python -m pytest -q tests/test_four_path_sc_escape.py
.venv/bin/python scripts/reference_fingerprints.py --verify
.venv/bin/python -m pytest -q tests/test_four_path_sc_escape.py
git rev-parse HEAD
git diff --check
git status --short
git diff --name-only
```

- Python: **3.11.9**, existing `.venv`; no installation or dependency changes.
- First targeted run: **46 passed in 0.23s**, exit 0, no failures/errors/skips.
- Reference command: exit 0; all three bundled references available, clean and
  verified against pinned commits, tracked-tree hashes and reviewed-file hashes.
  ESCAPE: 82 tracked files; k-CoreD: 127; notebook reference: 3. No upstream build,
  setup or experiment was run; `/home/tsshergi` originals were not used.
- Added an explicit positive-sensitivity-underflow guard and an assertion to the
  existing numeric test, then reran only the same test file: **46 passed in
  0.06s**, exit 0, no failures/errors/skips.
- `git rev-parse HEAD` gave the revision above. Before status/checkpoint edits,
  `git diff --name-only` was empty and status listed only the three newly created
  implementation/test/document files. The final diff/status check is recorded
  below; prior tracked algorithms and reference pins remain unchanged.

Final `git diff --check`, `git diff --stat` and `git status --short` succeeded:
only STATUS had tracked changes (27 added lines), alongside the four new files
listed above. An inline `.venv/bin/python -` file-format check read those four
new UTF-8 files and asserted `text.endswith('\n')` and
`all(line.rstrip() == line for line in text.splitlines())`; all passed. This was
a source/document whitespace check, not another algorithm execution.

The eight fixture checks use the supplied degree identity, the existing independent
ordered-quadruple oracle and cached `data/fixtures/expected_counts.json` P4 column.
They also run the new local algebra with test-only exact degree/adjacency inputs
and zero substituted noise. These are **not new native ESCAPE comparisons**.
Other cases verify the RR threshold and owner for six unordered pairs, all three
Laplace scales, two possible closing-edge reports for a triangle expectation,
budgets, seeds/stream separation, empty universes, isolates, duplicate edges,
fixed scheduling, record field allowlists and preservation of −0.25.
No large graph enumeration or Monte Carlo accuracy study occurred.

Read-only preparation included AGENTS, STATUS, checkpoint 30, existing estimator,
graph/noise/RR modules, tests, dependency pins, reference helpers and evaluation
standards. Algorithm 3 was checked against the
[USENIX 2021 primary paper](https://www.usenix.org/system/files/sec21-imola.pdf);
its lower-neighbor centered wedge calculation and public-bound noise scale match
the requested triangle component. No external code was downloaded or imported.

## Tooling failures, skipped work and limitations

No test failed. Initial read-only discovery had three harmless path/glob misses:
`rg --files -g AGENTS.md -g '*checkpoint*' docs .agents` reported absent `.agents`;
`rg -n 'Milestone|Stage 3|SC-ESCAPE|Separate.Component|fingerprint' docs scripts/verify* src/private_graphlets/references.py`
was rejected by zsh because `scripts/verify*` matched nothing;
`cat scripts/check_references.py` reported no such file. Subsequent `rg --files
scripts` located the actual `reference_fingerprints.py`, which passed. None of
these probes mutated project files or ran an experiment.

Deliberately not run: full/historical regression suites, native ESCAPE builds or
truth recomputation, exhaustive sensitivity audits, six-dataset or 200-trial
experiments, Stage 4 verification, Stage 5 evaluation, MSE studies, baselines,
budget optimization, data generation or plotting. No skipped test was counted
as a pass. No empirical performance/accuracy finding is asserted.

The public-bound validity check is an offline precondition, not a private report.
The ideal adjacency domain is fixed public vertices and graphs satisfying the
same public D_max. Source code separates client-local computation and reports,
but execution is a single-process research simulation, with no network isolation
or timing-side-channel defense. NumPy/float randomness is not cryptographically
secure or certified DP. Numeric errors, finite precision and externally observable
failure behavior remain deployment concerns. Caller-supplied generators must be
independently initialized; distinct bit-generator objects alone cannot ensure it.
The existing RR epsilon≤30 and new n≤1000 research guards are documented.

The task reports Stage 1–2 design/privacy/MSE work as complete; full SC-ESCAPE
proof documents were not found under that name locally. This implementation uses
the supplied equations and does not certify those proofs. No blocking discrepancy
was identified in this limited implementation review. Formal privacy and accuracy
still require independent review, with explicit coverage of all released messages.

## Next step and stopping point

Stage 3 is ready for separately requested Stage 4 verification. Review the
implementation against the full Stage 1–2 derivations then, including transcript
composition and numerical qualifications. Stage 5 remains untouched; it will
require its own approved fixed configuration and incremental evaluation runner.
**STOP. No further verification phase or evaluation is authorized by this task.**
