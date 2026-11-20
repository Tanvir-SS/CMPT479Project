# Checkpoint 29 — supplied RR-only diamond integration

2026-11-19 (America/Vancouver). **COMPLETE.** The owner supplied an RR-only
diamond estimator and authorized compatibility integration with the existing RR
module and evaluation tooling. Existing algorithms must remain unchanged;
any genuinely necessary RR modification would require explanation first.
No such issue was found, and no RR modification or duplication was made.

## Scope, inspection and preservation

Read AGENTS, latest STATUS/checkpoint 28, current graph/noise/RR interfaces,
diamond exact/helper code, hybrid evaluation script and evaluation conventions.
Starting HEAD: `c5bfdbdfc77ace3490f97d019ff48b9b8b0b0be5`. The pre-existing
untracked `src/private_graphlets/three_star_projected.py` belongs to other work
and was preserved without edits. The existing RR signatures already match
the supplied calls; all epsilon can be passed directly to `sample_rr_upper`
and `rr_matrix` with no compatibility shim or additional edge reporting.

Before edits, recorded 314 pre-existing file hashes (including available historical
results/plots/baseline files and the unrelated untracked module) under
`build/phase29/preservation_before.json`. New files are listed below; only STATUS
is intentionally modified among pre-existing project files. Existing algorithms,
tests, evaluation scripts/configs, datasets, references and dependencies remain
unchanged. The old AGENTS task-25 stop is superseded by this explicit integration
request only; no historical AGENTS instruction/file was rewritten.

## Files and implementation correspondence

Created:

- `src/private_graphlets/diamond_rr_only.py` — supplied `diamond_polynomial`,
  `RROnlyDiamondResult`, `estimate_rr_only_diamonds`, using direct shared RR imports.
- `scripts/evaluate_diamond_rr_only.py` — separate check/run/verify entry point,
  full epsilon to RR, cached native truth, incremental SQLite, CSV metrics and
  resumable independent output directory.
- `tests/test_diamond_rr_only.py` — focused compatibility and evaluator tests.
- `docs/DIAMOND_RR_ONLY.md` — interfaces, commands, changes and actual checks.
- This checkpoint; updated `docs/status/STATUS.md` current checklist/history.

No evaluation script was provided alongside the pasted estimator. An optional
scope question was sent while implementing; the stated working default is the
existing six-dataset grid. The new script prepares that support without launching
the study. It has no imports from or changes to the hybrid evaluator.

The supplied vectorized polynomial, single-owner single-RR-table sampling and
full-epsilon allocation are retained. Pasted markup escapes were normalized into
Python. The new polynomial wrapper coerces float input, checks finite/exactly
symmetric zero-diagonal matrices and raises on numerical overflow; this prevents
silent integer-matrix overflow or invalid standalone inputs. Shared RR matrices
already satisfy those checks, so their estimator formula is unchanged. Valid
integral seeds are normalized to Python int. The supplied ideal privacy-model
label is retained with an added `experimental_unverified` status field to keep
research simulation distinct from executable DP certification.

## Commands and observed outcomes

```bash
.venv/bin/python -m pytest -q tests/test_diamond_rr_only.py > build/phase29/targeted_tests.log 2>&1
.venv/bin/python scripts/evaluate_diamond_rr_only.py check --seed 202611192901 > build/phase29/evaluation_preflight.json
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase29/references.json
git diff --check
git status --short
```

Focused tests: **26 passed in 0.99s**, zero failures/errors/skips. These check
the eight cached fixture counts (including diamond=1 and K4=6), an independent
explicit weighted polynomial, n=0..3, preservation of signed/fractional values,
read-only matrices, invalid matrices/epsilon/seeds, shared-function identity and
dispatch exactly once per stage at full epsilon, reproducibility and JSON fields.
The evaluator integration uses only two tiny edgeless fixture calls with one
first observation then one resumed observation; a completed resume adds zero.
It verifies CSV/SQLite metrics and undefined zero-truth relative errors, rejects
overwriting output and rejects changed resume seeds. Fixtures are isolated from
the actual six-dataset study and are not represented as native ESCAPE output.

Preflight reports six checked graphs and **4,800 planned, zero executed benchmark
trials**. Cached native diamond counts: 151/300/4544/245/217982/3093 in standard
graph order. Data/mapping hashes and sizes pass. The command makes no estimator
calls and creates no experiment output directory. All three bundled references
verify at their existing pins. Existing Python 3.11.16, NumPy 2.2.6 and pytest
8.3.5 were used; no package installation or lock change.

No command/test failure occurred. No fresh ESCAPE compilation/execution is
claimed; deterministic fixture expectations and cached native outputs were used.
Skipped deliberately: RR probability/statistical re-verification (already
verified per owner), exhaustive/privacy audits, full previous regression,
benchmark trials, plots, comparisons, optimization, commit or push.

## Limits and next step

The code remains a NumPy/floating-point research simulator; the ideal pure
edge-LDP label is not an executable privacy certification. Negative values are
not projected away. The evaluation script separates exact/seed metadata from
private result records and uses the whole epsilon for the pair table, not the
hybrid O/R/W split. Large dense matrices have quadratic memory and cubic work;
finite overflow is explicit. No accuracy or performance superiority is claimed.

The two fixture-call integration check validates persistence/dispatch behavior;
it is not a completed six-dataset evaluation. Actual RR-only study execution
requires a separate instruction. Existing historical work and the untracked
projected 3-star file remain untouched. **STOP after integration.**

## Owner budget clarification — same integration task

2026-11-19 (America/Vancouver). The delayed reply to the optional evaluation
question explicitly specifies epsilon .5/1/2, epsilon_RR=epsilon_total and zero
Laplace/ordering budgets. The module already implements this allocation, so
neither it nor the shared RR module changed. Updated only the new evaluation
script's epsilon grid/config metadata, corresponding tests, integration docs and
current STATUS. The earlier four-budget preflight above is historical evidence;
it did not run a benchmark. The current default plan is **6×3×200=3,600**, also
unexecuted. No benchmark execution instruction was inferred from clarification.

Each possible undirected pair still receives one existing-RR report at the
entire epsilon, including nonedges. Under the ideal one-edge neighboring model,
only one pair input changes; there is no division by the number of reports or
multiplication of the total cost by that number. Reconstruction remains only
post-processing, with no additional noise, budget optimization or output clipping.

Actual commands:

```bash
.venv/bin/python -m pytest -q tests/test_diamond_rr_only.py -k 'api_uses_existing_rr_once_at_full_epsilon or runner_metrics_and_preflight_without_estimator' > build/phase29/budget_clarification/tests.log 2>&1
.venv/bin/python scripts/evaluate_diamond_rr_only.py check --seed 202611192901 > build/phase29/budget_clarification/preflight.json
git diff --check
```

Observed **4 passed, 24 deselected in 0.41s**, no failures/skips. This verifies
shared-function dispatch at each requested epsilon and the input-only grid/budget
metadata. Preflight reports six valid inputs and 3,600 planned trials, with no
sampling or result directory. SHA256 comparison confirms all 39 protected source,
existing hybrid-runner and dependency files unchanged, including both diamond
estimators, shared RR and the unrelated projected 3-star work. Receipts reside
in `build/phase29/budget_clarification/`. No dependency changes, full regression,
probability re-audit, experiments, commit or push. **STOP.**
