# Checkpoint 20 — standardized P4 ground truth

2026-11-08 (America/Vancouver). **COMPLETE. Stop after preparation.**

Scope: the owner's Milestone 3 dataset preparation request only; no repeated
design, privacy analysis, Phase 4B/5B study or private evaluation. Read AGENTS,
STATUS, checkpoint 19, EVALUATION_STANDARDS, TEAM_SETUP and graph_manifest.
Initial `git status --short` was clean.

## Verified exact counts

Counts are non-induced, unlabeled three-edge paths on four distinct vertices.
Additional host edges are allowed; a path and its reversal count once.
The existing Python counter uses sum over middle edges of
`(d(u)-1)*(d(v)-1) - 3*T` (triangle correction applied to the total).
Fresh native ESCAPE results use `connected_four['3-path']`, not K4 values.

| Dataset | Category | Vertices | Edges | Python P4 | ESCAPE P4 |
|---|---|---:|---:|---:|---:|
| karate | real_world | 34 | 78 | 2371 | 2371 |
| dolphins | real_world | 62 | 159 | 5023 | 5023 |
| les_miserables | real_world | 77 | 254 | 26784 | 26784 |
| brightkite_50 | real_world | 50 | 97 | 5404 | 5404 |
| ba_n100 | baseline_2025 | 100 | 1600 | 2043892 | 2043892 |
| sbm_n100 | baseline_2025 | 100 | 760 | 166236 | 166236 |

All six files exist, match manifest SHA-256, parse successfully, and match
declared vertex/edge counts. Checked canonical sorted unique u<v records,
endpoint bounds, no loops/reverse duplicates, and manifest isolate counts (zero
for all six). The parser preserves the declared vertex set. Python uses arbitrary
precision integers; native results pass the existing adapter's <=1000-vertex,
integrality and <2^53 guards. All target counts are nonnegative integers.

## Saved files and dependencies

- `experiments/results/p4_standardized_ground_truth/ground_truth.csv`: lightweight
  cache with identifier, category, n, m, path, full SHA-256, both P4 counts and
  verification status. This is non-private evaluation truth.
- Same directory: six `*.escape.json` files containing actual native input,
  output, stdout and stderr, separately from Python results; `provenance.json`
  contains build/source/binary hashes, Python version, input preservation hashes
  and counter/preparation-script hashes.
- `build/phase20/prepare_p4_truth.py`: exact-only one-shot verification script.
  Refuses an existing output directory; future recounts require a fresh output
  location. Existing outputs are never overwritten by this script.
- `build/phase20/escape/`: native executable, build manifest, compile command/log.
- `docs/status/STATUS.md` and this new checkpoint: current completion record.

Generated cache/build files remain ignored under existing repository conventions;
transfer them separately if needed. No dependency installation or upgrade.
Used Python 3.11.9 and the existing GNU compiler via `.venv/bin` PATH. All three
reference fingerprints verified at their existing pins; native build source hashes
also match the original graph manifest. Reference sources were read in place and
compiled outside their checkout using the existing adapter.

## Actual commands and outcomes

Executed from repository root:

```bash
.venv/bin/python scripts/reference_fingerprints.py --verify
.venv/bin/python --version
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python build/phase20/prepare_p4_truth.py
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_four_path_exact.py -k "exact_counters_against_escape or noninduced_paths_and_reversal_normalization"
git diff --check
git status --short
```

- Fingerprints: all three available, clean and verified; exit 0.
- Preparation: exit 0; six integer exact comparisons agree. Before/after hashes
  confirm all 13 inputs (six graphs, six mappings, original manifest) unchanged.
- Focused tests: **9 passed, 29 deselected in 1.80s**, no failures or skips;
  includes eight real-native fixture comparisons and non-induced normalization.
- No missing datasets, hash discrepancies, parsing failures or provenance issues.

Full historical regression, dataset regeneration, private trials, standardized
4,800-trial evaluation, plots and prior accuracy studies were intentionally not
run. No private estimator, budget/mechanism, third-party source or existing
experiment output was modified. This exact-count verification makes no new
privacy claim. No commit or push. No next phase is started; future evaluation
requires a separate instruction and should validate input hashes before cache use.
