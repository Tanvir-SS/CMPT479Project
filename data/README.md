# Reproducible four-clique benchmark datasets

Phase 13 prepares **24 public graphs only**: four real-world graphs and twenty
new synthetic realizations following the baseline paper's graph parameters.
All were validated against the existing oriented exact counter, independent
four-set enumeration and actual ESCAPE C++ output. No private counting trial or
full benchmark was run on these data during preparation.

The project owner authorizes including these small processed datasets in this
academic repository. No new software/data license is assigned here. Raw archives
stay ignored. After the owner reviews, commits and pushes the listed files, both
collaborators obtain identical processed bytes through `git pull` or a GitHub ZIP;
this task does not commit or publish them automatically.

## Files and format

`processed/real_world/` and `processed/baseline_2025/` contain the `.edges` files
and one `.mapping.json` per graph. [graph_manifest.json](processed/graph_manifest.json)
is the machine-readable source of sizes, parameters, seeds, full SHA-256 hashes,
original counts/IDs, preprocessing, exact counts and saved native ESCAPE output.
Each graph starts with `n m`, then sorted integer pairs `u v` with `u<v`. IDs
are exactly the public universe `0..n-1`; the header preserves isolates. Each
edge occurs once; loops, directions and weights are discarded during preparation.
The existing project loader is unchanged. New strict canonical verification also
rejects duplicate, reversed or unsorted rows even though the general loader can
deduplicate them.

Mappings preserve original ID types (integer or string) with a record for every
vertex, including isolates. Original integers sort numerically; strings sort by
Unicode code point. Les Misérables names therefore map deterministically without
relying on NetworkX insertion order. Mapping files have their own hashes.

## Accepted datasets

Every exact K4 count below is a three-way agreement, counting four distinct
vertices with all six edges once. K4 induced/non-induced counts coincide, but
this equivalence does not extend to our other patterns. Filenames are relative
to `data/processed/`.

| Dataset | Vertices | Edges | Exact K4 | File |
|---|---:|---:|---:|---|
| karate | 34 | 78 | 11 | `real_world/karate.edges` |
| les_miserables | 77 | 254 | 639 | `real_world/les_miserables.edges` |
| dolphins | 62 | 159 | 27 | `real_world/dolphins.edges` |
| brightkite_50 | 50 | 97 | 18 | `real_world/brightkite_50.edges` |
| ba_n010 | 10 | 16 | 0 | `baseline_2025/ba_n010.edges` |
| ba_n020 | 20 | 64 | 10 | `baseline_2025/ba_n020.edges` |
| ba_n030 | 30 | 144 | 127 | `baseline_2025/ba_n030.edges` |
| ba_n040 | 40 | 256 | 275 | `baseline_2025/ba_n040.edges` |
| ba_n050 | 50 | 400 | 766 | `baseline_2025/ba_n050.edges` |
| ba_n060 | 60 | 576 | 2289 | `baseline_2025/ba_n060.edges` |
| ba_n070 | 70 | 784 | 3833 | `baseline_2025/ba_n070.edges` |
| ba_n080 | 80 | 1024 | 7046 | `baseline_2025/ba_n080.edges` |
| ba_n090 | 90 | 1296 | 12787 | `baseline_2025/ba_n090.edges` |
| ba_n100 | 100 | 1600 | 18198 | `baseline_2025/ba_n100.edges` |
| sbm_n010 | 10 | 6 | 0 | `baseline_2025/sbm_n010.edges` |
| sbm_n020 | 20 | 37 | 0 | `baseline_2025/sbm_n020.edges` |
| sbm_n030 | 30 | 70 | 0 | `baseline_2025/sbm_n030.edges` |
| sbm_n040 | 40 | 113 | 6 | `baseline_2025/sbm_n040.edges` |
| sbm_n050 | 50 | 190 | 6 | `baseline_2025/sbm_n050.edges` |
| sbm_n060 | 60 | 277 | 12 | `baseline_2025/sbm_n060.edges` |
| sbm_n070 | 70 | 368 | 43 | `baseline_2025/sbm_n070.edges` |
| sbm_n080 | 80 | 481 | 60 | `baseline_2025/sbm_n080.edges` |
| sbm_n090 | 90 | 590 | 51 | `baseline_2025/sbm_n090.edges` |
| sbm_n100 | 100 | 760 | 99 | `baseline_2025/sbm_n100.edges` |

## Real-world sources and transformations

- **Karate:** `networkx.karate_club_graph()` in NetworkX 3.4.2; 34 nodes, 78
  edges. Drop weights/club attributes; original integer IDs remain unchanged.
- **Dolphins:** the D. Lusseau 2003 Doubtful Sound social graph from
  [Network Repository](https://networkrepository.com/dolphins.php), downloaded
  from [its linked archive](https://nrvis.com/download/data/misc/dolphins.zip).
  Parse the original `dolphins.mtx` member: Matrix Market coordinate pattern
  symmetric, declared 62x62 with 159 records. It has 62 vertices, 159 unique
  undirected edges, no loops/duplicate records. Map its 1-based IDs to 0..61.
  This is the specified original graph, not a similarly named replacement.
  Attribution: Lusseau's dolphin network; Rossi and Ahmed, *The Network Data
  Repository with Interactive Graph Analytics and Visualization*, AAAI 2015.
- **Les Misérables:** `networkx.les_miserables_graph()` in NetworkX 3.4.2;
  77 named characters, 254 edges. Drop coappearance weights and retain all
  vertices. Preserve character-to-integer mapping separately.
- **Brightkite:** [SNAP friendship network](https://snap.stanford.edu/data/loc-Brightkite.html),
  specifically `loc-brightkite_edges.txt.gz`, **not check-ins/locations**.
  The file has 428,156 records representing 214,078 distinct undirected edges
  on 58,228 observed vertex IDs; 214,078 reverse/duplicate records collapse,
  no loops are removed. Do not invent additional IDs from a maximum ID range.
  Attribution: Cho, Myers and Leskovec, *Friendship and Mobility*, KDD 2011.

Raw archive snapshots were downloaded and hash-pinned on **2026-11-06 UTC**.
The snapshot date in the manifest identifies the initially verified bytes;
new actual retrieval timestamps are stored only in ignored raw download sidecars.
The preparation code rejects a changed hash instead of accepting upstream drift.

| Raw archive | SHA-256 |
|---|---|
| `dolphins.zip` | `9d34947ed4ac929e2f38e542f1a59efd364be2d0b1c624fe2de65826fc7ecdc3` |
| `loc-brightkite_edges.txt.gz` | `0714a1ff54225f49fae8bd228d807e6a2a7ee27b8ff3c60989cfd9d20089a229` |

### Brightkite selection: fixed before observing its clique count

1. Normalize the friendship graph to a simple undirected graph, preserving all
   observed original vertices.
2. Choose the largest connected component; ties use the lexicographically
   smallest sorted list of original integer IDs. Its size here is **56,739**.
3. Use a fresh Python 3.11 `random.Random(130050)` to choose uniformly from that
   component's ascending ID list. The observed starting vertex is **2044**.
4. Run FIFO BFS, visiting each vertex's neighbors in ascending original ID order.
   Mark vertices on discovery; stop immediately after the 50th discovery.
5. Fix that vertex set, then retain **every** original selected-selected edge.
   This is an induced subgraph, not a BFS spanning tree. Relabel selected original
   IDs in ascending order to 0..49. The full discovery order and selected IDs are
   in the manifest; the inverse mapping is in `brightkite_50.mapping.json`.
6. Fail if the largest component has fewer than 50 vertices. There is no restart,
   joining of components, seed search, added edge or clique-count-dependent choice.

The result is **50 vertices, 97 edges and 18 exact K4s**. It is connected.
A connected-neighborhood sample is biased toward local social structure and is
not claimed to represent the full network statistically. A zero-clique result
would also have been retained. Full Brightkite is not passed to ESCAPE or the
baseline; only the 50-vertex sample is evaluated.

## Paper-compatible synthetic generation

The [2025 paper, Section 6.1](https://arxiv.org/pdf/2505.12954), specifies sizes
10,20,...,100, BA attachment n/5, and two equal SBM blocks with probabilities
.25 within/.05 between. We use those graph parameters, not the paper's random
realizations, experimental targets or reported results.

- BA: `nx.barabasi_albert_graph(n, m=n//5, seed=130100+n, initial_graph=None)`.
  Every allowed n is divisible by 5, so no rounding ambiguity remains. NetworkX
  **3.4.2** starts from a star on m+1 vertices when `initial_graph=None`; the
  resulting edge count is m*(n-m). The paper does not specify that initial graph.
- SBM: `nx.stochastic_block_model([n//2,n//2], [[.25,.05],[.05,.25]],
  seed=130200+n, directed=False, selfloops=False, sparse=True)`. Default consecutive
  node labels are used. These n are all even; isolates are preserved.
- All twenty graph seeds are distinct, fixed and independent of the Brightkite
  sampling seed and future privacy-mechanism seed coordinates. They select new
  research realizations; reproducible PRNG streams are not secure DP randomness.

The pinned baseline repository is at
`85eff6efa2b1d649ee238620a998ec7f1d305aac`. Both notebooks' first code cells use
SBM with `round(n/2)` blocks and the probabilities above; BA is commented out.
`babarasi_square.ipynb` sets n=100,m=20. However `babarasi_rr_mse.ipynb` sets
n=20,m=2 despite its n/5 comment: m would be 4 under the paper. **We use the
paper's n//5 convention**, and do not copy that conflicting literal. Neither
notebook specifies a graph seed in those calls. Their README cites NetworkX
3.2.1; we keep this project's locked 3.4.2 and explicit defaults. The notebooks
are 4-cycle examples and are not executed or assumed to cover all patterns.

## Prepare, regenerate and verify

From the project root with the existing locked Python 3.11 environment:

```bash
# Existing checked-in graphs: no raw download or compiler needed for this check.
.venv/bin/python scripts/prepare_real_world_graphs.py verify

# Rebuild/execute real ESCAPE and independently enumerate every four-set.
.venv/bin/python scripts/prepare_real_world_graphs.py verify --escape --brute-force

# Fetch ONLY missing pinned archives, prepare all graphs and future configs.
# An existing identical graph/manifest/config is retained; differing content fails.
.venv/bin/python scripts/prepare_real_world_graphs.py prepare --download

# Offline re-creation from cached raw inputs into an isolated directory.
.venv/bin/python scripts/prepare_real_world_graphs.py prepare \
  --output build/phase13/recreated --evidence build/phase13/recreated-evidence.json
.venv/bin/python scripts/prepare_real_world_graphs.py verify --output build/phase13/recreated

.venv/bin/python -m pytest -q tests/test_graph_datasets.py
.venv/bin/python -m pytest -q
```

Default raw directory: `data/raw/graph_benchmarks/`. Override with `--raw-dir`.
Default outputs and relative reference paths use the project root, not personal
WSL paths. `--escape-root`, then `ESCAPE_ROOT`, then `third_party/escape` select
the reference. Preparation always requires actual ESCAPE and brute-force agreement;
missing or broken references fail rather than produce a falsely validated manifest.
Normal `verify` checks canonical files, graph/mapping hashes, counts and saved
native output; its JSON explicitly says `fresh_escape:false`. `verify --escape`
performs a fresh native comparison. No skips are reported as passed comparisons.

Compiler artifacts and full native input/output/stdout/stderr evidence are in
ignored `build/phase13/`. Stable native `out.txt` count output is also embedded
in the tracked manifest for independent parsing. Runtime/compiler/platform
metadata are kept out of the deterministic manifest. `--evidence` chooses a
separate execution record; an idempotent preparation preserves previous evidence
for the same accepted manifest. Preparation rejects any conflicting existing
processed file/config. It never edits old experimental results or fixtures.

A Git checkout/GitHub source ZIP supplies graphs and mappings without downloads.
Source archives include these small benchmarks too. Raw archives, build logs,
`.venv`, caches and experimental outputs remain ignored. Python wheels do not
bundle research data; run dataset scripts from the repository/source tree.

On macOS, activate the existing environment and select GNU g++ as described in
[TEAM_SETUP](../docs/TEAM_SETUP.md#macos-prerequisites-and-current-verification).
Calling `.venv/bin/python` alone does not alter compiler PATH. The data format,
UTF-8/LF mappings, sorted traversal and seeded NetworkX generation are platform
independent in design. **The checked-in24 graphs were verified on Apple Silicon macOS on2026-11-06**:
all hashes and fresh ESCAPE/exact K4/P4 checks passed, along with76 dataset tests
and821 full tests. See [checkpoint15](../docs/status/checkpoints/15_macos_dataset_verification.md).
Full raw-data regeneration on macOS was not performed; compare manifest hashes
after regeneration on another platform. No new dependency
or submodule update is needed.

Load without running a privacy mechanism:

```python
from private_graphlets.graph import load_edge_list
from private_graphlets.four_clique_exact import count_four_cliques
G = load_edge_list('data/processed/real_world/karate.edges')
assert (G.num_vertices, G.num_edges, count_four_cliques(G)) == (34, 78, 11)
```

Both private CLI commands accept the same `.edges` path through this unchanged
loader. Tests intercept their experiment boundaries to verify identical graph
objects without executing private trials on the prepared datasets.

## Future comparisons: configured, not executed

- `experiments/configs/four_clique_real_world.json`: four real-world graphs;
  privacy master seed **202611061301**.
- `experiments/configs/four_clique_baseline_2025.json`: twenty synthetic graphs;
  privacy master seed **202611061302**.

Both follow the existing runner's schema: 100 eventual trials per graph/budget/
method; total epsilon [.5,1,2,4]; beta=.05; psi=.5; threshold fraction=.5;
bias factor=1. Methods are `kcore_noisy_cap` and `baseline`. Candidate allocations
remain O=D=R=C=epsilon/4; baseline uses R=epsilon, others zero. Ground truth is
fresh ESCAPE agreeing with independent exact enumeration, on the **same hash-pinned
file** for both methods. No performance guard or safety limit is bypassed.

The existing `trial_seed(master,graph_index,epsilon_index,method_index,trial)`
assigns distinct simulation coordinates across graphs, budgets, methods, trials
and the two masters. This task checks all 19,200 future seed coordinates without
executing them. The original exact count is the target for bias/RMSE. Existing
summary output has `rmse` and `bias`; **MSE is `rmse**2`**, recorded explicitly in
the configs' evaluation metadata. No historical metric schema is changed.
Original-versus-retained targets remain separate. Zero true counts make relative
RMSE undefined, not zero; the existing runner retains that behavior.

Only after an explicit future experiment instruction, commands will be:

```bash
.venv/bin/python scripts/run_four_clique_experiments.py run \
  --config experiments/configs/four_clique_real_world.json \
  --output experiments/results/four_clique_real_world
.venv/bin/python scripts/run_four_clique_experiments.py run \
  --config experiments/configs/four_clique_baseline_2025.json \
  --output experiments/results/four_clique_baseline_2025
```

These commands **were not run**. The existing experiment adapter adds only
hash-checked file input and labels future file-based evaluation appropriately;
its scoring, privacy defaults and metric calculations are unchanged. The Phase-6
config and saved results remain untouched.

The baseline visits C(n,4) four-sets per trial irrespective of sparsity. At n=100,
that is **3,921,225** products, or **1,568,490,000** across 400 baseline trials for
one graph. Both n=100 graphs, n=80/90 graphs and Les Misérables (n=77) warrant a
future measured feasibility pilot before a full sweep. All fit the current n<=100
baseline and n<=1000 ESCAPE guards, but passing a guard is not evidence of practical
runtime. No private runtime/scalability measurements were made in this phase.

## Seeds and full processed-file hashes

The manifest is authoritative; this table is generated from it. `—` means no
random graph generator. Mapping hashes are included in the manifest.

| Dataset | Graph/sampling seed | Processed-file SHA-256 |
|---|---:|---|
| karate | — | `3403714da814b5efd462eefe5eef4bfe1867f3dae5a95fbc5386f8564d0dc48f` |
| les_miserables | — | `4628984d81b4c38a349c642ff845b4a63139757cbc50ece473bf2334c4494f99` |
| dolphins | — | `459a17a147d584572324d87cb35efd36c24b1d467e9fed002ff0cac2c9b0edac` |
| brightkite_50 | 130050 | `41a65e36f66fd3aabe5487d39804e845bbf7b10604cd2e8457334a21eef81599` |
| ba_n010 | 130110 | `3a83cfde4a9d0270c1260ebbffc03d35047cc671586695d65e3eabe7f531a979` |
| ba_n020 | 130120 | `306ad9900f20c77a0f784724b541a6879f77e7d465ff422b0e3e4183e15c5962` |
| ba_n030 | 130130 | `02cebd37818cf8a3462c2aef7b7170eafc8840717494dc5f2c66703c76493cf0` |
| ba_n040 | 130140 | `8e06ff1c8b3329f71ec34fc100a7a52665c7000f6c3d2738aa563d62d11d5e2e` |
| ba_n050 | 130150 | `e21eeb60a1b7ee4390deb6e6b25db5bc5922f4929b0891c841df3597d97ab531` |
| ba_n060 | 130160 | `be080752fe8d55b136ec6de497e08292b82f4ea4870b9ad6e66ca1791a584f5c` |
| ba_n070 | 130170 | `2e72cdc10f9c92af0c3db2af77927a19263df6697285ea143149c4aaeeb6ac59` |
| ba_n080 | 130180 | `1b6458056326e674c38092e35e1ce419682e5fef19df25067ec1644852c2d8a1` |
| ba_n090 | 130190 | `aec9276193ca4c43caaff139baf9384340c42be69ffd777c3f32382a124f4787` |
| ba_n100 | 130200 | `071e36e4eb852fb5a24de4288612cb46a82b9327dc4983b7e6a36a70938d96fc` |
| sbm_n010 | 130210 | `9b8959dc73c7f8ee2a0a606d4ddf1ce0b0e4e2f8c73f785dd6939316a9b5ff88` |
| sbm_n020 | 130220 | `18bb5bbf2b56618fa5935b19b3eb3f53924a5b1fb3e92a0ea919303b46d53f1a` |
| sbm_n030 | 130230 | `227e2cee3a7996221d37b3c7b3db47284f106ecee6a6e2763e731e10345a0220` |
| sbm_n040 | 130240 | `1440062e1500cc4b961196bfe792bc2ed64ed0747e30538bc89c6a196cce6347` |
| sbm_n050 | 130250 | `b3e7158284012ad3f223d943646825c9d75d53cea0c25bf997a1bf4e3c02273e` |
| sbm_n060 | 130260 | `3313e4a04c7c6d23ff1ca33b52be14e42854db6aaeef2bae220848d60601a990` |
| sbm_n070 | 130270 | `92b1dec34ee4c9621d38c390712b5285ebd436781a7118b42819b148912643fe` |
| sbm_n080 | 130280 | `e0e7c12f07fe700cbfc0109f44d3525b6c9538cdba5e18a86be081b533e4359f` |
| sbm_n090 | 130290 | `e36f63aaab22fe07603058be2f46ef8acbadecd134f96d55398228aaa125088e` |
| sbm_n100 | 130300 | `92668120947e166a58987ccbae0e327a2df19a1f0a7b03337c1530c07e4d9314` |

See [STATUS](../docs/status/STATUS.md) and
[checkpoint 13](../docs/status/checkpoints/13_dataset_preparation.md) for actual
commands, checks, source preservation and limitations. **Stop after dataset
preparation and exact validation; no private comparison is authorized here.**
