# Checkpoint 06 — Full four-clique research implementation

Date: **2026-10-29** (America/Vancouver).
Outcome: **Stages A–E complete; stopped for independent mathematical review**.

## Scope, starting state and preserved work

The user supplied a Phase-6 request combining fixed-order validation, actual
k-CoreD integration/audit, full-protocol composition, the general debiased-RR
baseline, preliminary experiments and review documentation. It explicitly
authorized continuing past Stage A without another permission request.
This superseded the Phase-5 design-only stop for the stated scope.

Started from clean commit `396f9215ac1c97b54e3717f4acf56f95442ae743`. Read the
attachment, AGENTS.md, STATUS.md, Phase-5 design/checkpoint, privacy/source notes,
phase-04 review package and reference fingerprints before implementation.
No other pattern, expanded experiment phase, commit or push was performed.
All changes remain local for review/version control.

The private 3-star mechanism, graph/noise/exact implementations, experiment
pipeline and existing tests are unchanged. CLI additions preserve those commands;
the informational phase and experimental-estimator metadata are updated.
Historical checkpoint/report bytes are preserved. The existing 3-star result
manifest and metrics verify successfully: 15 graphs, 75 cells, 37,500 trials.
Privacy notes gain a separate Phase-6 addendum; their earlier review discussion
is explicitly historical. The user's pre-existing README edit was preserved.

## Completed components and files

| Files | Work |
|---|---|
| `src/private_graphlets/four_clique_exact.py` | Exact forward-triple and independent four-set counters, strict orders/ranks, stable capped selection. |
| `src/private_graphlets/randomized_response.py` | Stable RR parameters; client-local one-owner reports for all pairs; immutable mirrored weight matrix. |
| `src/private_graphlets/four_clique.py` | Budget validation/allocation, separate RNG domains, private cap, weighted local scoring/sensitivity, client-side Laplace reports, complete modeled transcript and aggregate-only API. |
| `src/private_graphlets/kcore.py` | Attributed port of actual noised threshold/level protocol, synchronous updates, fixed ID ties, transcript budget audit, explicitly separate noiseless non-private oracle. |
| `src/private_graphlets/four_clique_baseline.py` | Canonical undirected six-factor debiased RR, spending the same total epsilon. |
| `src/private_graphlets/four_clique_experiments.py` | Small synthetic comparisons, actual ESCAPE output/provenance, retained targets, all metrics, full replay and CSV-derived plots. |
| `src/private_graphlets/cli.py` | Exact/candidate/baseline commands; existing 3-star behavior retained. |
| `tests/test_four_clique_core.py`, `test_kcore.py`, `test_four_clique_protocol.py`, `test_four_clique_experiments.py` | 120 new tests; none of the 256 earlier tests was weakened or edited. |
| `experiments/configs/four_clique_phase06.json` | Fixed graph seeds, trial coordinates, budgets, methods and parameters. |
| `scripts/run_four_clique_experiments.py`, `scripts/analyze_four_clique_experiments.py` | Run/verify/replay/plot and regenerate compact observed findings. |
| `THIRD_PARTY_NOTICES.md`, `MANIFEST.in`, `pyproject.toml` | Preserve the Go MIT notice in source and wheel artifacts; no dependency changes. |
| `docs/FOUR_CLIQUE_IMPLEMENTATION.md`, `KCORED_INTEGRATION.md`, `FOUR_CLIQUE_EXPERIMENTS.md` | Implemented behavior, source/privacy audit, actual observations, limitations and reproduction. |
| `docs/status/REVIEW_PACKAGE_06.md`, `STATUS.md`, `accuracy_06.json`, this checkpoint | Independent-review handoff, current checklist, compact evidence and execution record. |
| `docs/status/checkpoints/06a_fixed_order_internal.md`, `06b_kcore_internal.md` | Required internal checkpoints after fixed-order validation and private-ordering integration. |
| `README.md`, `AGENTS.md`, `docs/PRIVACY_NOTES.md` | Current commands, permanent scope/stop, and full-protocol accounting addendum. |

## k-CoreD audit and implementation decisions

The original sources remain at ESCAPE commit
`7ec2f93c524a0b47cdc8c639602e90d1c1fceff3` and Go commit
`b03da893ba1c38d3931708bac919562c5ab57963`. The port retains Go's threshold
transformation, group/round formulas, same-level queries, geometric target law,
positive bias, synchronous updates and permanent stopping. It explicitly
publishes each noised threshold, uses `(final_level,public_ID)` ties throughout,
replaces the sampler with documented NumPy simulation, and fixes small-n/isolates
and error handling. A separate non-private oracle cannot be selected by the
private API. No silent exact-degree/degeneracy substitution occurs.

The source audit and the primary [PVLDB paper](https://www.vldb.org/pvldb/vol18/p4199-mundra.pdf)
were consulted for initial degree sensitivity, geometric distributions,
threshold/promotion reports, adaptive stopping and endpoint composition.
The explicit transcript supports a proposed ideal argument spending O per
ordering, D per cap, R per pair table and C per locally noised scores. The
port is **experimental_unverified**: executable privacy, numerical tail behavior,
all side channels and the adapted low-out-degree utility theorem remain unresolved.
We did not invent a proof or hide the source/paper parameter differences.

For full noisy-cap mode, budgets are equal quarters. For k-CoreD public/uncapped
mode, O=min(e/3,1), D=0 and R=C=(e-O)/2; this keeps ordering epsilon<=1.
Fixed modes and baseline redistribute explicitly, with totals equal to e.
Baseline uses six adjusted pair weights and no further noise. It is inspired by
[AISTATS 2025 Algorithm 1](https://arxiv.org/pdf/2505.12954), with canonical
unordered-pair ownership under our undirected-edge convention, not a claim of
reproducing the authors' notebook.

## Commands and observed tests

All commands ran from the project directory in the existing Python 3.11 venv.
The initial internal stage commands are preserved in notes 06a/06b. Main checks:

```bash
mkdir -p build/phase06
.venv/bin/python scripts/reference_fingerprints.py > build/phase06/references-before.json

ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q \
  tests/test_four_clique_core.py tests/test_kcore.py tests/test_four_clique_protocol.py \
  --junitxml=build/phase06/integrated.xml > build/phase06/integrated.log 2>&1

# Initial full check; one CSV dtype mismatch was diagnosed below.
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q \
  --junitxml=build/phase06/full.xml > build/phase06/full.log 2>&1
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q \
  tests/test_four_clique_experiments.py --junitxml=build/phase06/experiment_tests.xml \
  > build/phase06/experiment_tests.log 2>&1

# Final suite after CSV fix and complete reference provenance.
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q \
  --junitxml=build/phase06/pytest.xml > build/phase06/pytest.log 2>&1
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python scripts/check_four_clique_design.py \
  --output build/phase06/design_recheck.json \
  --summary build/phase06/design_recheck_summary.json > build/phase06/design_recheck.log 2>&1

.venv/bin/python scripts/reference_fingerprints.py > build/phase06/references-after.json
.venv/bin/python scripts/run_experiments.py verify > build/phase06/three_star_preservation.log 2>&1
git diff --check
```

| Check | Actual outcome |
|---|---|
| Fixed-order internal stage | **50 passed in 6.54s**. |
| k-CoreD internal stage | **25 passed in 0.19s**. |
| Integrated mechanism/baseline tests | **106 passed in 8.14s**. |
| Initial full suite | **1 failed, 375 passed in 21.30s**: CSV dtype inference for `cap_mean`, not a numerical result mismatch. |
| Corrected pipeline/CLI tests | **14 passed in 9.50s**. |
| Corrected full suite | **376 passed in 27.41s**, no failures/skips. |
| Final full suite after provenance addition | **376 passed in 28.54s**, no failures/errors/skips. |
| Marked ESCAPE cases in full suite | **43 passed**: original 34, eight new clique cases and one new full pipeline case. |
| Phase-5 exact recheck | **1,112 graph comparisons, 124,542 ordering checks, 10,240 finite sensitivity checks passed**. |
| Existing 3-star artifact verification | **15 graphs / 75 cells / 37,500 trials verified**; no data regenerated or altered. |
| External integrity | **82 ESCAPE + 127 Go tracked file fingerprints unchanged**, clean worktrees. |

The CSV fix permits an integer-valued mean to deserialize as integer instead
of float; it still compares every recomputed value/column with the existing
numeric tolerance. No estimator, seed, statistical tolerance or observed value
was changed to pass a test. An exploratory `rg` path for upstream `configs/`
did not exist; the actual source/driver files supplied the required information.
One `pip check` invocation warned about the unwritable default external cache;
using the project's cache removed the warning. No permission blocker occurred.

## Experiment execution, replay and plots

```bash
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python scripts/run_four_clique_experiments.py run \
  > build/phase06/experiment_run.log 2>&1
.venv/bin/python scripts/run_four_clique_experiments.py verify --replay \
  > build/phase06/replay.log 2>&1
.venv/bin/python scripts/run_four_clique_experiments.py plot > build/phase06/plots.log 2>&1

# Full rerun after adding executable hash and complete ESCAPE build provenance:
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python scripts/run_four_clique_experiments.py run \
  --output build/phase06/reproduction_final > build/phase06/reproduction_run.log 2>&1
```

Inline Python compared **every non-timing field** in both trial and summary
CSVs with exact equality: all match. It preserved the initial result directory
as `build/phase06/initial_experiment_run` and moved the reproduced run to the
canonical `experiments/results/four_clique_phase06/`. This is replay of the same
16,000 observations, not 32,000 independent trials. Initial/final pipeline
times were 11.296029s and 12.689841s under concurrent verification load.

```bash
.venv/bin/python scripts/run_four_clique_experiments.py verify --replay \
  > build/phase06/replay_final.log 2>&1
.venv/bin/python scripts/run_four_clique_experiments.py plot > build/phase06/plots_final.log 2>&1
.venv/bin/python scripts/run_four_clique_experiments.py plot \
  --output build/phase06/regenerated_plots > build/phase06/plot_regeneration.log 2>&1
.venv/bin/python scripts/analyze_four_clique_experiments.py --output docs/status/accuracy_06.json
```

Canonical outputs: **8 graphs, 160 cells, 16,000 trials**, all estimates and
non-timing diagnostics replay exactly. Eight PNG/PDF plots regenerate from
saved CSVs with identical hashes. The RMSE figure was visually inspected for
readability. Raw outputs/plots are ignored; compact `accuracy_06.json` is
intentional review evidence. Original graph generation seeds and independent
trial/stream construction are in the config and experiment report.

Observed findings: each oriented method has higher observed RMSE than baseline
on all 32 graph–epsilon comparisons. The full noisy-cap version reaches n-1
in 92.0625% of its trials and clips no true outgoing set in this run. Public
cap 3 loses many true cliques: K8 retains 5 of 70. All 7,326 negative estimates
are preserved; 60 zero-truth cells have undefined relative RMSE. Baseline RR
tails are poorly resolved at 100 trials in some settings; for empty6 at epsilon
4, ideal SD 2.6587690e-5 exceeds observed RMSE 6.4216166e-8 substantially.
No general statistically established improvement or ranking is claimed.

## Environment, packaging and final audit

No third-party dependency changed; Python **3.11.16**, the existing pins and
lock were retained. Lock SHA-256:
`ffbb7a1cbe39daaaecba70d68bdd163d5e8e27bbf3a39f17a47f6e13fff6ed4f`.
The project's own editable metadata was reinstalled offline after adding the
license-file declaration. Packaging commands:

```bash
PIP_NO_INDEX=1 PIP_CACHE_DIR="$PWD/.cache/pip" .venv/bin/python -m pip install \
  --no-deps --no-build-isolation -e . > build/phase06/editable-install.log 2>&1
PIP_CACHE_DIR="$PWD/.cache/pip" .venv/bin/python -m pip check
.venv/bin/python -m build --no-isolation > build/phase06/package-build.log 2>&1
# Repeated once the review documents were complete:
.venv/bin/python -m build --no-isolation > build/phase06/package-build-final.log 2>&1
```

`pip check` reports no broken requirements. Wheel/source builds succeed; the
wheel includes `dist-info/licenses/THIRD_PARTY_NOTICES.md`. Existing setup and
lock commands remain valid; no new dependency justified regenerating the lock
or recreating the venv. Five exact/candidate/baseline README CLI examples were
executed successfully and saved in `build/phase06/cli_checks.json`. Exact K4=1;
private records omit seeds and true edge counts.

Read-only audits compare original test/checkpoint bytes and external reference
fingerprints, verify saved hashes/plot regeneration, check Markdown targets and
whitespace, and confirm generated results, virtual environments and binaries
are ignored by Git. No external tracked file or original 3-star data changed.
The final package build includes the completed reports and all new source files.
The final audit passed **55 local Markdown links**, balanced code fences,
whitespace, source/executable provenance hashes, artifact ignores and all eight
regenerated plot hashes. Wheel/source inspection confirms the new modules,
license notice, tests, configuration and review reports are included, with no
virtual environment, generated experiment data or build artifacts. A source
search found no hardcoded personal paths in the new reusable modules/scripts.

## Remaining limitations and stopping point

The k-CoreD integration works as a noised research protocol; its complete
executable privacy proof remains unresolved. The proposed ideal transcript
accounting must undergo independent review, including numeric randomizers,
adaptive interaction, error/timing transcripts and client isolation. The port's
low-out-degree utility theorem is not established. Cap bias, correlated closing
reports, dense communication and small-sample tail uncertainty remain material.
No unresolved observed test failure remains; that is not proof of bug absence.

Give the independent researcher [REVIEW_PACKAGE_06.md](../REVIEW_PACKAGE_06.md)
and its exact file/artifact list. No further algorithm modification, enlarged
grid, other graph pattern or new research phase was begun. **STOP; await explicit
follow-up after review.**
