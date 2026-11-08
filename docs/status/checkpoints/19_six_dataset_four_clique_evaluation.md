# Checkpoint 19 — dataset cleanup and candidate-only K4 evaluation

2026-11-08 UTC. **COMPLETE. Stop after this task; no commit or push.**

The owner's replacement request cancels unfinished Phase 18. Inspected Git diff,
AGENTS, STATUS and checkpoint18 before changing files; no blanket reset.
Removed only the abandoned evaluation's scripts/modules/config/test, unfinished
reports, result/prediction directories, plots and build artifacts. Restored the
inspected Phase 18-only README/experiment-report edits before adding new scoped
instructions. The cancellation remains recorded in checkpoint18.

Removed 18 processed BA/SBM graphs (n10–90) and their 18 mappings. Retained all six
requested edge lists/mappings unchanged and preserved data/fixtures. Archived
unchanged original manifest/data instructions/two future configs under
`docs/status/phase13_dataset_provenance/`; retired those configs from active use.
Cleanup inventory: `build/phase19/cleanup.json`.

Only dataset-selection/config generation in graph_datasets.py changes; private
algorithms, proofs, dependencies, Phase6 results and unrelated work are preserved.
Existing dataset-test expectations now reflect six inputs and one candidate config.
No full regression suite, proof audit, baseline or old experiment was run in this
replacement task. No plots or analytical-history experiment are generated.

Added `docs/EVALUATION_STANDARDS.md` (documentation only for future patterns),
`experiments/configs/four_clique_six_datasets.json` and the independent
`scripts/evaluate_four_clique.py`. The script commits each trial to SQLite and
exports CSVs per completed cell. Resume validates source/config/input hashes and
seed coordinates. No repeated exact counting or expensive clique diagnostics.

Main master seed 202611081901 is fresh; smoke master 202611081900 is separate.
Both use `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`.
Private O/D/R/C budgets are explicitly epsilon/4, with unchanged beta .05 and
kcore defaults. Statistics use direct MSE, population variance (`ddof=0`), bias,
RMSE, MAE, relative RMSE and runtime. Negative/non-integer values remain intact.
Outgoing-edge/vertex truncation diagnostics are not labeled clique loss.

Brief smoke: saved 3 trials, resumed 45, verified all 48 observations across six
inputs/four budgets. CSV/SQLite values, seeds, quarter allocations and population
MSE=variance+bias² identity agree. Saved native ESCAPE truth is parsed and checked
at startup; no native rebuild/recount was required.

Commands executed:

```bash
.venv/bin/python scripts/evaluate_four_clique.py run --smoke --max-new-trials 3
.venv/bin/python scripts/evaluate_four_clique.py run --smoke --resume
.venv/bin/python scripts/evaluate_four_clique.py verify --smoke
.venv/bin/python scripts/evaluate_four_clique.py run
```

The main run completed all **4,800/4,800 fresh observations**, 24 cells with 200
trials each; no remaining work or interrupted main cell. Full artifact verification
passed: all CSV values match SQLite, seeds are unique, stage budgets are fixed
quarters, saved hashes match and population metrics recompute correctly.

```bash
.venv/bin/python scripts/evaluate_four_clique.py verify
git diff --check
```

Observed RMSE decreases with epsilon for all six graphs, but remains large
relative to truth. At epsilon4, RMSE is 4333.83 (Karate), 7406.26 (Dolphins),
12412.12 (Les Misérables), 5252.71 (Brightkite), 67616.32 (BA100), 25676.32 (SBM100).
The precise CSV values are authoritative. All 2,436 negative estimates are kept.
Cap saturation occurred 1415/4800 times; no outgoing-edge truncation was observed.
No exact retained-clique recount was performed. Summed mechanism time 76.806352s;
separate inexpensive diagnostics 0.617039s. SQLite/CSV overhead is excluded from
these per-call timings. No new accuracy/privacy guarantee is claimed.

Preservation check: 269 prior snapshot files inspected; only authorized cleanup,
selection/configuration and documentation changes. All 54 pre-existing saved
result/plot files remain unchanged. Six graph/mapping records exactly match the
archived manifest and hashes. Eighteen graphs plus 18 mappings are retired.
Private mechanism/proof/dependency/fixture bytes and all three reference pins are
unchanged. Archived Phase13 documents/configs retain their original hashes.
Git HEAD remains 8771b225570bf6097a49b61c1695d4d338fbebb6; no staged changes,
commit or push. `git diff --check` passed.

No dependency was installed. No full pytest suite was rerun, in accordance with
the request for brief verification only. Existing dataset-test assertions were
updated for six files and the candidate-only 200-trial config, but the broader
suite remains explicitly unrun in this phase. The smoke and saved-output checks
are not substitutes for formal executable privacy certification.

## Deliverables and records

- `scripts/evaluate_four_clique.py`: independent resumable candidate-only runner.
- `experiments/configs/four_clique_six_datasets.json`: fixed setup/fresh seeds.
- `docs/EVALUATION_STANDARDS.md`: future conventions only; no future-pattern code.
- `docs/FOUR_CLIQUE_SIX_DATASETS.md`: concise results and reproduction commands.
- `experiments/results/four_clique_six_datasets/`: ignored SQLite, trials/summary
  CSVs, configuration, source/environment/native-truth provenance and manifest.
- `build/phase19/`: cleanup inventory, partial/resumed smoke logs, main-run log,
  smoke/full verification receipts, preservation receipt and small result summary.
- `docs/status/phase13_dataset_provenance/`: original manifest, data documentation
  and two retired future configs; completed historical reports remain untouched.

Updated AGENTS, README, TEAM_SETUP, data documentation, active manifest,
config documentation, graph_datasets.py selection/config generation and its
existing dataset tests. The historical FOUR_CLIQUE_EXPERIMENTS report retains
its original body with a short new link. STATUS reflects completion; checkpoint18
records cancellation. Removed abandoned phase18 files are listed in cleanup.json.

Further evaluation, tuning or other patterns require a new instruction. Stop.

