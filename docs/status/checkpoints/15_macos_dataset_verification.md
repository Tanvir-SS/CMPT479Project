# Checkpoint 15 — All graph datasets verified on macOS

Date: **2026-11-06 (America/Vancouver)**. **COMPLETE — verification only.**

## Git state and scope

Branch main, HEAD/origin/main both
`86f7ed3966e3a52268499379818f1abf89e4954b` (Real world Graph data).
Fetched origin/main; ahead/behind0/0, so no pull or branch update was necessary.
Existing uncommitted Phase4B README, STATUS, four_path_study.py, study report and
checkpoint14 were preserved. No stash/reset/commit/push was performed.
The initial sandbox fetch could not write .git/FETCH_HEAD; the approved retry
succeeded. Read AGENTS, TEAM_SETUP, data README, STATUS and current checkpoint.

## Platform and dependencies

Actual platform macOS27.0.1 (build26A434), Darwin arm64, Python3.11.9 in .venv.
GNU g++16.2.0 via .venv/bin/g++ compiled unchanged pinned ESCAPE successfully.
NumPy2.2.6, NetworkX3.4.2, pandas2.2.3, Matplotlib3.10.1, pytest8.3.5.
`pip check`: no broken requirements; only a nonfatal disabled-cache warning.
No dependencies installed/upgraded. GNU compiler source warnings were preserved.

All three references bootstrap/verify at exact pins, clean:
ESCAPE7ec2f93c524a0b47cdc8c639602e90d1c1fceff3;
Go b03da893ba1c38d3931708bac919562c5ab57963;
notebooks85eff6efa2b1d649ee238620a998ec7f1d305aac.

## Dataset verification

All24 expected graph files and their24 mappings are present, readable and tracked;
the manifest is tracked too. Every graph uses the unchanged loader and canonical
byte validation, which rejects duplicate/reversed duplicate edges rather than
silently accepting deduplication as validation. All IDs/mappings cover0..n−1;
no loops, invalid IDs or asymmetric adjacency. Header vertex counts preserve
isolates: sbm_n010 and sbm_n030 each have one, all others zero. Repeated loads
are identical. All graph/mapping hashes match the manifest; all49 files including
the manifest remain byte-identical after tests.

Fresh independent four-set brute force, maintained exact K4 and actual original
ESCAPE agree with every manifest K4 count. Exact P4 also agrees with fresh ESCAPE
on all24 graphs. Native input/output/stdout/stderr are saved per graph separately
under build/macos_dataset_verification/escape_NAME.json.

Compatibility checks call each actual P4, private K4 and six-factor baseline
entry point and intercept its first random stage after input validation. No
randomized graph trial is executed. All24 graph objects pass; all are within
existing size guards. Existing dataset tests also exercise hash-checked input
resolution from a different working directory without Linux absolute paths.
This establishes input compatibility, not baseline runtime or privacy guarantees.

File names below are NAME.edges under data/processed/real_world for the first
four, and data/processed/baseline_2025 for the twenty BA/SBM graphs.

| Dataset | n | m | K4 | P4 | Hash | ESCAPE | K4 input | P4 input | Baseline input |
|---|---:|---:|---:|---:|---|---|---|---|---|
| karate | 34 | 78 | 11 | 2371 | yes | yes | yes | yes | yes |
| les_miserables | 77 | 254 | 639 | 26784 | yes | yes | yes | yes | yes |
| dolphins | 62 | 159 | 27 | 5023 | yes | yes | yes | yes | yes |
| brightkite_50 | 50 | 97 | 18 | 5404 | yes | yes | yes | yes | yes |
| ba_n010 | 10 | 16 | 0 | 122 | yes | yes | yes | yes | yes |
| ba_n020 | 20 | 64 | 10 | 2361 | yes | yes | yes | yes | yes |
| ba_n030 | 30 | 144 | 127 | 14933 | yes | yes | yes | yes | yes |
| ba_n040 | 40 | 256 | 275 | 44866 | yes | yes | yes | yes | yes |
| ba_n050 | 50 | 400 | 766 | 117162 | yes | yes | yes | yes | yes |
| ba_n060 | 60 | 576 | 2289 | 258357 | yes | yes | yes | yes | yes |
| ba_n070 | 70 | 784 | 3833 | 469815 | yes | yes | yes | yes | yes |
| ba_n080 | 80 | 1024 | 7046 | 813858 | yes | yes | yes | yes | yes |
| ba_n090 | 90 | 1296 | 12787 | 1363317 | yes | yes | yes | yes | yes |
| ba_n100 | 100 | 1600 | 18198 | 2043892 | yes | yes | yes | yes | yes |
| sbm_n010 | 10 | 6 | 0 | 1 | yes | yes | yes | yes | yes |
| sbm_n020 | 20 | 37 | 0 | 350 | yes | yes | yes | yes | yes |
| sbm_n030 | 30 | 70 | 0 | 1160 | yes | yes | yes | yes | yes |
| sbm_n040 | 40 | 113 | 6 | 3756 | yes | yes | yes | yes | yes |
| sbm_n050 | 50 | 190 | 6 | 9778 | yes | yes | yes | yes | yes |
| sbm_n060 | 60 | 277 | 12 | 21173 | yes | yes | yes | yes | yes |
| sbm_n070 | 70 | 368 | 43 | 37582 | yes | yes | yes | yes | yes |
| sbm_n080 | 80 | 481 | 60 | 65484 | yes | yes | yes | yes | yes |
| sbm_n090 | 90 | 590 | 51 | 94368 | yes | yes | yes | yes | yes |
| sbm_n100 | 100 | 760 | 99 | 166236 | yes | yes | yes | yes | yes |

## Commands and observed outcomes

```bash
git status --short
git branch --show-current
git log -1 --oneline
git fetch origin main
git rev-parse HEAD origin/main
git rev-list --left-right --count HEAD...origin/main
bash scripts/bootstrap_references.sh
uname -sm
sw_vers
.venv/bin/python --version
.venv/bin/python -m pip check
.venv/bin/g++ --version
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python scripts/prepare_real_world_graphs.py verify --escape --brute-force --evidence build/macos_dataset_verification/native.json
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_graph_datasets.py --junitxml=build/macos_dataset_verification/datasets.xml
.venv/bin/python build/macos_dataset_verification/check_interfaces.py
MPLCONFIGDIR="$PWD/build/phase13/matplotlib" PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q --junitxml=build/macos_dataset_verification/full.xml
git submodule status
.venv/bin/python scripts/reference_fingerprints.py --verify > build/macos_dataset_verification/references.json
git ls-files --error-unmatch data/processed/graph_manifest.json
git diff --check
```

The saved check_interfaces.py additionally runs git ls-files --error-unmatch
for each graph/mapping, verifies canonical structure/hash/repeated loads, tests
the three input boundaries, counts P4/K4 and preserves native ESCAPE evidence.
Before/after hashes are saved as before.json and preservation.json in the same
ignored evidence directory; interfaces.json records versions and all24 results.

Dataset script:24 graphs verified, fresh_escape=true, fresh_bruteforce=true.
Separate dataset suite: **76 passed in6.40s**. Full regression: **821 passed
in30.92s**. Both have zero failures/errors/skips. All3 reference fingerprints
verified, whitespace check passed. No unresolved failure or missing dataset.
The existing suite's bounded mechanism tests run as usual; no private sweep or
prepared-dataset private trial was launched.

## Changes and limits

Only documentation changed for this verification: this checkpoint, STATUS,
TEAM_SETUP and data/README macOS verification notes. Build evidence is ignored.
Research algorithms, budgets, configs, processed data, mappings, manifest, locks,
reference sources and prior results are unchanged. Existing Phase4B uncommitted
changes remain. No source archives downloaded and no processed dataset regenerated
or replaced. Tests do regenerate seeded synthetic graphs in memory for comparison;
full raw Brightkite/Dolphins reconstruction was not requested or performed.

All requested current-checkout success criteria passed on this Apple Silicon Mac.
No executable privacy proof or large-scale performance claim follows from these
input/exact/test checks. **Stop after verification; no commit or push.**
