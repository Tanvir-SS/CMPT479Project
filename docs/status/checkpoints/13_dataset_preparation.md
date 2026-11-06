# Checkpoint 13 — Real-world and baseline-compatible graph datasets

Date: **2026-11-06 (UTC)**. Outcome: **COMPLETE; dataset preparation only.**
Starting revision: `99d542abe4aa81b448b9859561af703605259fd5`, clean working tree.
No commit, push, branch, reference update, full private comparison or optimization
was performed. This newly authorized dataset request supersedes the completed
Phases 8–9 stop only for its stated scope; it is not Phase-10 optimization.
Checkpoint 13 follows the repository's highest existing numbered report (12),
preserving the overlapping historical macOS/P4 and four-clique checkpoints.

## Inspection and source decisions

Read AGENTS, README, TEAM_SETUP, STATUS, and the relevant four-clique checkpoints
06,08,09 before editing. Inspected graph loader, exact/candidate/baseline APIs,
ESCAPE format/build/safety guards, existing configuration/run/replay paths,
dataset layout/ignore rules, packaging and pinned baseline notebooks. No graph
loader compatibility defect was found; it is unchanged.

Consulted the actual [baseline paper Section6.1](https://arxiv.org/pdf/2505.12954),
the [specified Dolphins page](https://networkrepository.com/dolphins.php) and
[SNAP Brightkite friendship page](https://snap.stanford.edu/data/loc-Brightkite.html).
Paper BA attachment is n/5; SBM has two equal blocks and .25/.05 probabilities.
The first cell of pinned `babarasi_rr_mse.ipynb` sets n=20,m=2 despite its n/5
comment, whereas `babarasi_square.ipynb` sets n=100,m=20. Both active graph calls
are unseeded SBM; BA is commented out. Follow the written paper, m=n//5, for
these divisible-by-five sizes. Preserve NetworkX3.4.2's default BA initial star
on m+1 vertices; document that the paper does not specify the initial graph.
The notebooks cite a different historical NetworkX version and do not supply
original graph seeds. These are new realizations, not the authors' exact graphs
or a reproduction of their 4-cycle experimental results. No notebook was run.

Owner permission for these datasets and checked-in small processed snapshots
was already explicit. No additional licensing review or permission request was
performed; no new license or private correspondence was published.

## Preparation and actual findings

All 24 accepted graphs are canonical simple undirected `.edges` files with an
`n m` header and sorted unique u<v rows. Node counts retain isolates. Preparation
removes duplicate/reverse edges, loops, weights/directions and other attributes;
original typed IDs map deterministically to consecutive IDs. All 24 have separate
mapping files and hashes. Sizes, exact counts, seeds and full hashes are listed
in [data/README.md](../../../data/README.md) and the machine-readable
[manifest](../../../data/processed/graph_manifest.json).

- Karate and Les Misérables use the pinned NetworkX built-ins: 34/78 and 77/254
  vertices/edges, with exact K4 counts **11** and **639** respectively.
- Dolphins is the linked original Lusseau archive, `dolphins.mtx`, 62 vertices,
  159 unique undirected edges and **27** K4s; map original IDs1..62 to0..61.
- Full SNAP friendship input has **58,228** observed IDs and **428,156** records,
  which deduplicate to **214,078** undirected edges; zero loops. Check-ins were
  not downloaded. The largest component contains **56,739** vertices.
- Brightkite seed **130050** was fixed before inspecting clique counts. Choose
  a start with `random.Random(seed).choice(sorted(largest_component))`, then FIFO
  BFS with ascending neighbors and mark-on-discovery, stopping at50 vertices.
  Ties between largest components use lexicographically sorted original IDs.
  The observed start is **2044**. Only after fixing this set, induce every original
  selected-selected edge, then relabel in ascending original-ID order. The result
  is connected, **50 vertices,97 edges,18 K4s**. No seed search/structural adjustment
  occurred. A too-small largest component fails; no disconnected fallback.
- Ten BA graphs use n=10,20,...,100, m=n//5, seed=130100+n, initial_graph=None.
- Ten SBM graphs use equal n//2 blocks, p=[[.25,.05],[.05,.25]], directed=False,
  selfloops=False, sparse=True, seed=130200+n. SBM n10 and n30 each retain an
  isolate. Several graphs have zero K4s; those graphs were retained unchanged.

All 24 original exact K4 counts agree among the unchanged oriented counter,
independent brute-force four-set enumeration and actual ESCAPE C++. Raw native
input/output/stdout/stderr and compiler provenance are stored separately in
ignored build evidence; stable native count output is embedded in the manifest.
No Python count is labeled as an ESCAPE observation. All graphs are at most100
vertices, below the existing ESCAPE1000 and baseline100 limits; no guard bypass.

Raw archives downloaded on2026-11-06 UTC:

| Archive | Bytes | SHA-256 |
|---|---:|---|
| dolphins.zip | 1491 | `9d34947ed4ac929e2f38e542f1a59efd364be2d0b1c624fe2de65826fc7ecdc3` |
| loc-brightkite_edges.txt.gz | 1364607 | `0714a1ff54225f49fae8bd228d807e6a2a7ee27b8ff3c60989cfd9d20089a229` |

Initial sandbox urllib download failed with DNS resolution error. The authorized
network retry fetched the actual public archives successfully. The browser tool
could inspect the Dolphins page but could not display application/zip; this was
not a dataset substitution. Raw archives and retrieval-time sidecars stay ignored
under `data/raw/graph_benchmarks/`. Future downloads enforce these exact hashes;
upstream drift is an explicit failure, never silently accepted.

## Code and future configuration integration

New `graph_datasets.py` handles raw format parsing, canonicalization, normalization,
seeded induced BFS selection, version-pinned generation, exact validation,
idempotent writing/hash verification and portable file input. It invokes no
private mechanism. `scripts/prepare_real_world_graphs.py` offers `prepare` and
`verify`; prepare always requires actual ESCAPE and brute force. Default verify
checks hashes, canonical structure, Python truth and saved native counts, and
explicitly reports that it did not perform a fresh ESCAPE run. `--escape` and
`--brute-force` request fresh execution. Existing different data/configs fail;
identical bytes are retained. Runtime-dependent evidence stays under build/.

The only edit to existing Python source is the experiment adapter's new
`prepared_edge_list` branch and a distinct future file-evaluation type label.
Both methods receive the same hash-checked graph object. Existing graph generation,
private mechanism calls, budget defaults, metric calculations and old run/replay
paths are unchanged; the Phase-6 configuration/results are untouched.

Two new configurations use the existing schema/runner:

| Configuration | Graphs | Future privacy master seed |
|---|---:|---:|
| `four_clique_real_world.json` | 4 | 202611061301 |
| `four_clique_baseline_2025.json` | 20 | 202611061302 |

Both specify100 eventual trials per graph/epsilon/method; epsilon [.5,1,2,4];
kcore/noisy candidate with O=D=R=C=epsilon/4; baseline R=epsilon only. Existing
psi=.5, threshold_fraction=.5, bias_factor=1, beta=.05 remain unchanged. Exact
ESCAPE is the ground-truth stage, not a private method. Bias/RMSE use the original
K4 count, with retained targets separate. MSE is the existing summary's rmse^2;
that derivation is explicit in config metadata rather than altering historical
CSV schemas. Relative error remains undefined at zero truth.

Tests validate all19,200 planned seed coordinates are distinct across these
configs; they **do not execute those trials**. The 100-vertex baseline would
visit3,921,225 four-sets per trial,1,568,490,000 over400 baseline trials for one
graph. Large cases need a future measured feasibility pilot. No private-runtime
measurement or successful scalability claim is made here.

## Commands and actual validation

Existing environment: Python3.11.16, NetworkX3.4.2 and the unchanged pinned lock,
Linux/WSL2 x86_64. No dependency was installed/upgraded. GNU g++ builds read-only
ESCAPE into project build/. macOS ARM64 was **not available for new execution**;
portable paths/encoding/seeded procedures and checked-in byte hashes are provided.

```bash
.venv/bin/python scripts/prepare_real_world_graphs.py prepare
.venv/bin/python -m pytest -q tests/test_graph_datasets.py \
  --junitxml=build/phase13/dataset-tests.xml
.venv/bin/python scripts/prepare_real_world_graphs.py prepare \
  --output build/phase13/regenerated --evidence build/phase13/regeneration.json
.venv/bin/python scripts/prepare_real_world_graphs.py verify
.venv/bin/python scripts/prepare_real_world_graphs.py verify --escape --brute-force
.venv/bin/python -m pytest -q --junitxml=build/phase13/full.xml
.venv/bin/python -m pytest --collect-only -q -m escape_integration
.venv/bin/python scripts/check_escape.py
.venv/bin/python scripts/reference_fingerprints.py --verify
.venv/bin/python scripts/reference_fingerprints.py \
  --escape /home/tsshergi/escape --ledp /home/tsshergi/DistributedLEDPGraphAlgos \
  --baseline /home/tsshergi/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy --verify
.venv/bin/python -m build --no-isolation
# Per-file CLI command, executed for every manifest record (24):
.venv/bin/private-graphlets exact-four-cliques data/processed/real_world/karate.edges

git diff --check
git status --short
git submodule status
```

The two initial archives were obtained with urllib from the URLs and hashes
recorded above; the reproducible download entry point is now
`prepare --download`. Preparation/regeneration stdout, JUnit XML, CLI command
arrays/results, source snapshots and preservation checks are in `build/phase13/`.

| Check | Actual result |
|---|---|
| New dataset tests | **76 passed in12.90s**; no failures/errors/skips. |
| Full regression | **821 passed in51.47s**; no failures/errors/skips. |
| ESCAPE coverage | All24 new graphs executed in preparation and integration tests; the full suite includes85 marked ESCAPE cases. Collection-only command identifies membership, not an additional test run. |
| Standalone prior ESCAPE fixture check | **8 passed**, all six connected pattern columns. |
| Fresh full regeneration | All49 graph/mapping/manifest artifacts byte-identical; total174,456 bytes. No differing file overwritten. |
| Independent Brightkite archive scan | All97 processed edges exactly match original edges on the mapped50-vertex set. |
| Verification CLI | Hash-only and fresh ESCAPE+brute-force modes both verify24 graphs, accurately labeling fresh checks. |
| Per-dataset existing exact CLI | **24 passed**, counts equal manifest/ESCAPE. |
| Build/package check | Source archive and wheel built; all49 dataset artifacts included byte-identically in source archive, no raw archives bundled. |
| Reference checks | All3 bundled submodules and all3 original external checkouts verify unchanged fingerprints/pins. |

No test assertion/tolerance was weakened and no test failed in this phase.
The resolved sandbox DNS failure is separate from the passing test results.
Existing upstream compiler warnings remain in build logs; no third-party patch
was made. Existing pytest does run its previously authorized bounded mechanism
tests, but no dataset-specific private trials or full comparison were added/run.

## Reproducibility and preservation evidence

- `data/processed/graph_manifest.json`: full sources, versions, parameters, seeds,
  sizes/counts, preprocessing, mappings/hashes and actual native count output.
- `build/phase13/dataset_validation.json`: initial native execution evidence.
- `build/phase13/regeneration.json`, `reproducibility.json`: second generation,
  identical bytes and independent full-source induced-edge check.
- `build/phase13/dataset_verify_escape0_brute0.json` and
  `dataset_verify_escape1_brute1.json`: precisely labeled verification outcomes.
- `build/phase13/cli-exact.json`: all24 installed exact-CLI commands/results.
- `build/phase13/before.json`, `preservation.json`, `references.json`,
  `original-references.json`, test XML/logs: source/artifact integrity and checks.

`.gitignore` admits only the two approved directories' edge lists/mappings and
manifest; raw archives, unrelated processed data, caches, virtual environments,
build/experiment output remain ignored. MANIFEST.in includes the small approved
data in source archives. No files are staged/committed or pushed. Both collaborators
will obtain the same data through Git only after the owner's later commit/push.

Existing fixtures, all previous experiment configs/results/plots, privacy/MSE
proofs, mechanism source and historical checkpoints retain their starting hashes.
The old STATUS body is preserved as history. All three reference pins are unchanged:
ESCAPE `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3`, Go
`b03da893ba1c38d3931708bac919562c5ab57963`, baseline
`85eff6efa2b1d649ee238620a998ec7f1d305aac`.

**STOP.** All24 graphs are ready as inputs for a future explicitly authorized
comparison; baseline runtime and macOS regeneration remain unmeasured here.
No privacy proof, estimator change, sensitivity change, allocation tuning,
optimization or full experimental sweep is part of this checkpoint.

## Complete file inventory

The following inventory includes this report; all other pre-existing files are
preserved. Each approved dataset has both an edge list and a mapping.

Modified existing files:

- `.gitignore`
- `AGENTS.md`
- `MANIFEST.in`
- `README.md`
- `data/README.md`
- `data/processed/README.md`
- `docs/TEAM_SETUP.md`
- `docs/status/STATUS.md`
- `src/private_graphlets/four_clique_experiments.py`

New files:

- `data/processed/baseline_2025/ba_n010.edges`
- `data/processed/baseline_2025/ba_n010.mapping.json`
- `data/processed/baseline_2025/ba_n020.edges`
- `data/processed/baseline_2025/ba_n020.mapping.json`
- `data/processed/baseline_2025/ba_n030.edges`
- `data/processed/baseline_2025/ba_n030.mapping.json`
- `data/processed/baseline_2025/ba_n040.edges`
- `data/processed/baseline_2025/ba_n040.mapping.json`
- `data/processed/baseline_2025/ba_n050.edges`
- `data/processed/baseline_2025/ba_n050.mapping.json`
- `data/processed/baseline_2025/ba_n060.edges`
- `data/processed/baseline_2025/ba_n060.mapping.json`
- `data/processed/baseline_2025/ba_n070.edges`
- `data/processed/baseline_2025/ba_n070.mapping.json`
- `data/processed/baseline_2025/ba_n080.edges`
- `data/processed/baseline_2025/ba_n080.mapping.json`
- `data/processed/baseline_2025/ba_n090.edges`
- `data/processed/baseline_2025/ba_n090.mapping.json`
- `data/processed/baseline_2025/ba_n100.edges`
- `data/processed/baseline_2025/ba_n100.mapping.json`
- `data/processed/baseline_2025/sbm_n010.edges`
- `data/processed/baseline_2025/sbm_n010.mapping.json`
- `data/processed/baseline_2025/sbm_n020.edges`
- `data/processed/baseline_2025/sbm_n020.mapping.json`
- `data/processed/baseline_2025/sbm_n030.edges`
- `data/processed/baseline_2025/sbm_n030.mapping.json`
- `data/processed/baseline_2025/sbm_n040.edges`
- `data/processed/baseline_2025/sbm_n040.mapping.json`
- `data/processed/baseline_2025/sbm_n050.edges`
- `data/processed/baseline_2025/sbm_n050.mapping.json`
- `data/processed/baseline_2025/sbm_n060.edges`
- `data/processed/baseline_2025/sbm_n060.mapping.json`
- `data/processed/baseline_2025/sbm_n070.edges`
- `data/processed/baseline_2025/sbm_n070.mapping.json`
- `data/processed/baseline_2025/sbm_n080.edges`
- `data/processed/baseline_2025/sbm_n080.mapping.json`
- `data/processed/baseline_2025/sbm_n090.edges`
- `data/processed/baseline_2025/sbm_n090.mapping.json`
- `data/processed/baseline_2025/sbm_n100.edges`
- `data/processed/baseline_2025/sbm_n100.mapping.json`
- `data/processed/graph_manifest.json`
- `data/processed/real_world/brightkite_50.edges`
- `data/processed/real_world/brightkite_50.mapping.json`
- `data/processed/real_world/dolphins.edges`
- `data/processed/real_world/dolphins.mapping.json`
- `data/processed/real_world/karate.edges`
- `data/processed/real_world/karate.mapping.json`
- `data/processed/real_world/les_miserables.edges`
- `data/processed/real_world/les_miserables.mapping.json`
- `docs/status/checkpoints/13_dataset_preparation.md`
- `experiments/configs/four_clique_baseline_2025.json`
- `experiments/configs/four_clique_real_world.json`
- `scripts/prepare_real_world_graphs.py`
- `src/private_graphlets/graph_datasets.py`
- `tests/test_graph_datasets.py`
