# Active evaluation datasets

Phase 19 keeps exactly six existing graphs. Their edge lists and mappings were
not regenerated or modified. The other 18 processed BA/SBM graphs and mappings
have been removed from the active collection. Correctness fixtures under
`data/fixtures/`, including `expected_counts.json`, remain unchanged.

| Dataset | n | m | Exact K4 | File |
|---|---:|---:|---:|---|
| karate | 34 | 78 | 11 | `real_world/karate.edges` |
| les_miserables | 77 | 254 | 639 | `real_world/les_miserables.edges` |
| dolphins | 62 | 159 | 27 | `real_world/dolphins.edges` |
| brightkite_50 | 50 | 97 | 18 | `real_world/brightkite_50.edges` |
| ba_n100 | 100 | 1600 | 18198 | `baseline_2025/ba_n100.edges` |
| sbm_n100 | 100 | 760 | 99 | `baseline_2025/sbm_n100.edges` |

Paths above are relative to `data/processed/`. The authoritative
[manifest](processed/graph_manifest.json) includes full hashes, mapping hashes,
sources, preprocessing, seeds and previously verified native ESCAPE output.
K4 is counted once per unordered complete four-set; induced and non-induced
K4 agree, unlike several other graph patterns.

Each `.edges` file starts with `n m`, followed by sorted unique `u v` pairs with
`u<v` and public IDs `0..n-1`. The header preserves isolated vertices. Graphs
are simple and undirected. Mappings preserve original vertex IDs.

## Sources and fixed generation

- Karate and Les Misérables use NetworkX 3.4.2 built-in graphs; weights and
  attributes were removed, with deterministic ID mappings.
- Dolphins comes from the original Network Repository `dolphins.mtx` archive
  (62 vertices, 159 edges), normalized from 1-based IDs.
- Brightkite uses SNAP friendship edges, not locations. Seed 130050 selects
  start vertex 2044 in the largest component; sorted-neighbor FIFO BFS selects
  50 vertices, then all edges among them are retained. No seed search was used.
- BA-100 uses `barabasi_albert_graph(100,20,seed=130200,initial_graph=None)`.
- SBM-100 uses blocks `[50,50]`, probabilities `[[.25,.05],[.05,.25]]`,
  seed 130300, `directed=False`, `selfloops=False`, `sparse=True`.

The original full preparation instructions, provider attribution, raw-archive
hashes and 24-graph manifest are preserved in
[historical provenance](../docs/status/phase13_dataset_provenance/README.md).
No license is newly assigned. Raw archives remain ignored. The selected files
already passed native ESCAPE, oriented and brute-force checks in the completed
preparation phase. The new K4 study checks those saved native counts and input
hashes once at startup; it does not recount each randomized trial.

## Active study and reproduction

The independent script is `scripts/evaluate_four_clique.py`; its fixed config is
`experiments/configs/four_clique_six_datasets.json`. It runs only kcore_noisy_cap:
epsilon .5/1/2/4, 200 fresh trials per cell, equal O/D/R/C quarters. See
[future conventions](../docs/EVALUATION_STANDARDS.md) and
[study results/instructions](../docs/FOUR_CLIQUE_SIX_DATASETS.md).

```bash
.venv/bin/python scripts/evaluate_four_clique.py run
# After an interruption; committed trial rows are retained:
.venv/bin/python scripts/evaluate_four_clique.py run --resume
.venv/bin/python scripts/evaluate_four_clique.py verify
```

Optional dataset hash/canonical verification:
`.venv/bin/python scripts/prepare_real_world_graphs.py verify`.
The preparation utility now targets only these six graphs; do not regenerate
accepted inputs for the current evaluation. Historical preparation configs are
archived, not active. Generated estimates, SQLite checkpoints and CSVs are ignored.

## Selected graph hashes

| Dataset | SHA-256 |
|---|---|
| karate | `3403714da814b5efd462eefe5eef4bfe1867f3dae5a95fbc5386f8564d0dc48f` |
| les_miserables | `4628984d81b4c38a349c642ff845b4a63139757cbc50ece473bf2334c4494f99` |
| dolphins | `459a17a147d584572324d87cb35efd36c24b1d467e9fed002ff0cac2c9b0edac` |
| brightkite_50 | `41a65e36f66fd3aabe5487d39804e845bbf7b10604cd2e8457334a21eef81599` |
| ba_n100 | `071e36e4eb852fb5a24de4288612cb46a82b9327dc4983b7e6a36a70938d96fc` |
| sbm_n100 | `92668120947e166a58987ccbae0e327a2df19a1f0a7b03337c1530c07e4d9314` |
