# Checkpoint 04 — Experiments and independent mathematical review

Date: **2026-10-28** (America/Vancouver).
Outcome: **complete; stopped at the requested boundary**.

## Authorization and starting state

The user authorized a reproducible five-budget experiment grid for the existing
non-induced 3-star estimator, statistical analysis, plots, final verification
and review documents. This explicitly superseded the phase-03 experiment stop.
It did not authorize any 4-clique design or implementation. Neither was begun.

Read AGENTS.md, STATUS.md, all checkpoints 01–03, implementation, tests and
algorithm/privacy documentation. The worktree was clean at
`ea02371d0e38dc6ad4ebb1801a7fa112844bee81`. Changes remain local and uncommitted;
no commit or push was performed. Previous checkpoints and their evidence are
preserved. Required new source/configuration files are listed below, ready for
review/version control; generated outputs are intentionally ignored.

## Files and completed implementation

| File | Work |
|---|---|
| `experiments/configs/three_star_phase04.json` | Fixed 15 graph specifications, graph seeds, five budgets, 500 trials, master mechanism seed and representative plot graph. |
| `src/private_graphlets/experiments.py` | Config validation, graph generation, distinct trial RNGs, exact/ESCAPE checks, metrics, saved graphs/raw/aggregate CSVs, provenance, hash checking and exact replay. |
| `src/private_graphlets/experiment_plots.py` | Four full-range figures in PNG/PDF from saved data, input/output hashes and deterministic metadata. |
| `scripts/run_experiments.py` | `run`, `verify --replay` and `plot` commands. Refuses to overwrite existing run directories. |
| `scripts/analyze_experiments.py` | Regenerates compact accuracy summary; investigates the two observed variance-ratio extrema using fourth moments, quadrature and polynomial-expansion cross-checks. |
| `tests/test_experiments.py` | 27 tests for metrics, zero truth, stream replay/uniqueness, config, quadrature, whole pipeline, real reference calls, output corruption and plot regeneration. |
| `src/private_graphlets/cli.py` | Information-only phase label now phase 04. Private/exact CLI behavior is unchanged. |
| `MANIFEST.in` | Include experiment configuration JSON in source distribution; generated data/figures remain excluded. |
| `docs/EXPERIMENTS.md` | Setup, seeds, metric formulas, graphs, commands, actual results, plots and statistical limits. |
| `docs/ALGORITHMS.md`, `docs/PRIVACY_NOTES.md` | Readable pseudocode/complexity, exact protocol contract, every randomness source, budget allocations and independent-review questions. |
| `docs/status/REVIEW_PACKAGE.md` | Concise technical handoff, actual tests/findings, review file list and pending milestones. |
| `docs/status/STATUS.md`, this checkpoint, `docs/status/accuracy_04.json` | Current checklist, audit record and compact intentionally retained numerical evidence. |
| `AGENTS.md`, `README.md` | Explicit phase-04 stop and executable reproduction/review instructions. |
| `experiments/{README.md,configs/README.md,results/README.md}`, `plots/README.md`, `docs/ESCAPE_VALIDATION.md` | Current artifact guidance and integration-test count. |

The estimator, noise, graph validation and exact-counter sources were **not
modified**. Their bytes and the earlier checkpoint bytes match starting HEAD.
No correction was tuned, no negative estimate rounded/clipped/truncated, and
no trial removed. Private result records never acquire truth/degrees/seeds.

## Experimental design and raw evidence

The configuration was written before observing results. Three stars, three ER,
three BA, three SBM and three complete graphs span n=3–100. All graph specs and
seeds are in the JSON; all realized edges are saved. The zero-star K3 case tests
undefined relative error; the sparse ER/SBM cases retain six/three isolates.
Graph-generation seeds are 4101–4103, 4201–4203 and 4301–4303; stars/cliques
are deterministic. The fixed representative histogram graph is ba_n60_m2.

Budgets are **0.25, 0.5, 1, 2, 4**. Each of 75 cells has **500 trials**, total
**37,500**. The mechanism root seed is **202610280400**. For every trial, PCG64
is initialized via SeedSequence with unique zero-based `(graph_index,
epsilon_index,trial)` coordinates. This avoids reinitializing all trials with
one identical noise stream. Graph RNGs are separate. It is a simulation design,
not cryptographic randomness or a formal independence proof.

All 15 graph formula counts match actual ESCAPE output; brute force additionally
checks the three graphs with n<=12. The adapter executes the original size-4
binary and saves input/output/stdout/stderr, never substitutes our own count
for ESCAPE. All prior reference integration cases pass too.

The results directory contains **21 files**: 15 original graph edge lists,
config, graphs.csv, trials.csv, summary.csv, escape_reference.json and manifest.
CSV floats use round-trippable representations; verification regenerated every
estimate exactly. Aggregates are calculated from the saved CSVs and verified
again from raw trials. SD uses sample variance with ddof=1; MAE/RMSE use T in
their error moments. Bias is the signed sample mean error. Relative bias/MAE/
RMSE divide by truth only when positive; zero-truth fields are blank/NaN.

The first run completed in **2.438598s**. After the informational CLI phase label
was finalized, the initial run was moved to ignored `build/phase04/initial-run`
and a clean second run created the canonical results directory. It completed
in **3.597833s** under concurrent verification load. Every non-timing CSV field
is exactly identical; these are **the same 37,500 observations replayed**, not
75,000 independent trials. No seeds/configuration changed between runs.

Final per-mechanism times sum to **1.867899s**, mean **49.81 microseconds**. These
measure only the estimator API, excluding RNG construction, generation, ESCAPE
and file work. Pipeline time excludes compilation, initial config/provenance
preparation, plots and replay. The environment was shared with tests/builds;
neither timing is a controlled benchmark or distributed runtime.

## Actual findings

- Observed RMSE decreases with epsilon on **all 15 graphs**. Relative accuracy
  is far worse for low true counts: at epsilon 4, relative RMSE is 0.737217
  for star_n5, 0.689991 for sparse ER n30, and 0.016009 for ER n100. Graph sizes,
  density and degree distributions vary together, so no causal family ranking
  or graph-population generalization is claimed.
- Maximum absolute mean z-score is **2.281724** (complete_n10, epsilon 4).
  Three of 75 cells exceed 2 analytic SE; none exceeds 3 or 6. Finite-sample
  mean error is not proof of systematic bias or exact unbiasedness.
- Sample/ideal variance ratios span **0.279039–1.681334**. The extrema are
  complete_n3 and star_n5 at epsilon 1. An explicitly post-hoc investigation
  used seven-node Gauss–Laguerre quadrature for fourth central moments, checked
  against direct polynomial expansion through degree 12. Relative SE of sample
  variance is **97.4%** and **71.6%** for these cases, with observed deviations
  -0.740174 and +0.952049 of those SEs. This quantifies noisy variance estimation
  at 500 trials under the ideal model; it is not an exact confidence statement
  or a formal theorem about the finite-precision simulator.
- **6,882 negative estimates** are retained. **Five** K3 cells have undefined
  relative metrics. No outlier deletion, smoothing of data, clipping, seed
  selection or formula change was performed.

The complete graph/count table and selected RMSE values are in EXPERIMENTS.md.
All 75 metric rows remain in summary.csv, all estimates in trials.csv. The
analysis script regenerates `docs/status/accuracy_04.json` directly from them.

## Commands run and checks

Read-only inspection used `cat`, `rg`, `git status --short`, `git rev-parse HEAD`
and comparisons with `git show HEAD:<path>`. Main commands, from the project:

```bash
mkdir -p build/phase04
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q tests/test_experiments.py
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python scripts/run_experiments.py run
.venv/bin/python scripts/run_experiments.py verify --replay
.venv/bin/python scripts/run_experiments.py plot

# After preserving the first run under build/phase04/initial-run, repeat run.
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python scripts/run_experiments.py run
PIP_NO_INDEX=1 ESCAPE_ROOT=/home/tsshergi/escape bash scripts/setup.sh
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q -m escape_integration
.venv/bin/python scripts/run_experiments.py verify --replay
.venv/bin/python scripts/run_experiments.py plot
.venv/bin/python scripts/run_experiments.py plot --output build/phase04/regenerated-plots
.venv/bin/python scripts/analyze_experiments.py --output docs/status/accuracy_04.json

.venv/bin/private-graphlets estimate-three-stars data/fixtures/star.edges --epsilon 2 --seed 123
.venv/bin/private-graphlets exact-three-stars data/fixtures/star.edges
.venv/bin/private-graphlets info --json
git diff --check
.venv/bin/python -m build --no-isolation --outdir build/phase04/dist
```

Long-running command output was retained with `set -o pipefail` and `tee` in
`build/phase04/{experiment.log,experiment-final.log,setup-and-tests.log,escape-tests.log}`.
The setup script performs hash-locked dependency checking, editable project
installation without isolation, `pip check`, the full `python -m pytest -q`,
and CLI info. Existing dependencies were already satisfied; the offline flag
required no network access. CLI examples returned private estimate
**2.2168852600487927** and separate exact truth **1** for the star fixture.

Additional inline Python checks:

- Recomputed all 25 installed-version pins and unchanged requirements.lock hash.
- Recomputed both external references with `scripts.reference_fingerprints` and
  compared to docs/references.json; saved `build/phase04/references-after.json`.
- Compared mechanism/counter sources and checkpoints 01–03 against HEAD.
- Compared first/second trials.csv, graphs.csv and all non-timing summary fields
  with `pandas.testing.assert_frame_equal(..., check_exact=True)`.
- Compared all current execution-source hashes against the final run manifest.
- Verified every figure hash across the original run, replay and independent
  plot regeneration; inspected all four PNGs visually for legibility/ranges.
- Inspected the private source for clipping/rounding/truncation calls; none.
- Used `git ls-files` and `git check-ignore` to check artifact exclusions.
- Inspected the wheel/source archive, Markdown links and trailing whitespace;
  created a separate local review archive from an explicit source/data allowlist.

### Actual outcomes

| Check | Observed outcome |
|---|---|
| New experiment tests | **27 passed in 10.18s**. |
| Full WSL setup/test command | **256 passed in 15.15s**, no failed/errored/skipped tests. |
| Explicit real integration tests | **34 passed, 222 deselected in 10.04s**. Deselected Python tests passed in the full run. |
| Complete experiment | **15 graphs, 75 cells, 37,500 trials**, 500/cell; all exact references agree. |
| Full estimate replay | **37,500/37,500 identical**; no runtime identity expected. |
| Independent full pipeline replay | Graphs, estimates and all non-timing aggregates match exactly. |
| Metrics and artifact hashes | Every saved record/aggregate verified; all manifest execution-source hashes match. |
| Figure regeneration | **8/8** PNG/PDF files identical by SHA-256; four figures visually inspected. |
| Fourth-moment diagnostic | Quadrature agrees with independent polynomial expansion for all degrees in both selected cases. |
| Dependency check | No broken requirements; **25/25** pins match. |
| External integrity | **82 ESCAPE / 127 Go** tracked-file hashes match; clean worktrees. |
| Generated artifact exclusions | **21 result files + 9 plot files** ignored; no generated outputs in Git index. |

No implementation/test failure occurred in phase 04. No statistical thresholds
or seeds were adjusted after viewing results. No tests were skipped in the
configured final suite. Real datasets, secure deployment, distributed timings,
sanitizers and formal proofs were not attempted. No approval escalation or
permission blocker occurred.

## Reproducibility, package and dependency state

No third-party dependency was added/upgraded. CPython **3.11.16**, NumPy **2.2.6**,
NetworkX **3.4.2**, pandas **2.2.3**, Matplotlib **3.10.1**, pytest **8.3.5** and
g++ **11.4.0** were used. The existing 25-pin lock SHA-256 remains
`ffbb7a1cbe39daaaecba70d68bdd163d5e8e27bbf3a39f17a47f6e13fff6ed4f`.
The editable project was reinstalled at its existing version 0.1.0; use source
hashes/revision, not version alone, to identify this phase.

Generated results and figures are ignored. The small accuracy_04.json evidence
file is intentionally retained in docs. Config JSON is included in the source
archive; the wheel contains experiment/plot modules, and scripts/config/docs
are provided by the source archive. External C++ sources are described/pinned,
not vendored. New source/config/docs remain local uncommitted files listed above;
they must accompany any future publication/commit for reproducibility.

Local handoff: **`build/phase04/review_package.tar.gz`** and SHA-256 sidecar.
The archive includes the explicit review source/config/test/docs set and the
actual result/plot directories, while excluding Git metadata, virtualenvs,
caches, binaries, credentials and unrelated build artifacts. No files were sent
to another person or external service. The reviewer checklist is in
REVIEW_PACKAGE.md; README/EXPERIMENTS.md explain recreation from a clone.

## Known limitations and stop

The simulator is not a cryptographically secure LEDP deployment. It has no
local-client isolation, transport or privacy ledger. Fixed public vertices,
two-endpoint composition, ideal-noise unbiasedness/variance, finite-precision
sampling, failures and runtime transcripts still need independent review.
Reference warnings/limitations are unchanged (160 compiler warnings). The
adapter's 1000-vertex/2**53 guards do not certify all upstream computations.
One realization per graph specification and 500 trials cannot establish
family-wide utility or precise tail behavior. No empirical result proves DP.

Milestone 3's rubric was not supplied: pending work is mathematical review,
resolution of the documented questions, and agreement on an explicitly
authorized next scope. The final project still needs its approved coverage,
reviewed claims, representative dataset studies and final report/artifact bundle.
Other pattern algorithms remain unstarted. **STOP here. Do not design or
implement 4-clique or proceed without an explicit follow-up instruction.**
