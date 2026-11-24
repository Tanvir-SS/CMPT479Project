# 34 — Three larger SNAP datasets

Completed 2026-11-23 (America/Vancouver). The new opt-in suite contains full
Email-Eu-core, Facebook combined and Wikispeedia article hyperlinks. The
[dataset guide](../../../data/README.md#larger-snap-graphs) records source URLs,
download commands, original and processed counts, isolates, density, maximum
degree, indexing and selection. All three input rosters matched the SNAP sizes.

## Exact native results

Each cell counts distinct non-induced subgraph copies on four distinct vertices.
ESCAPE's connected four-vertex entries 5 through 10 (zero-based) give the columns
below in order. The [manifest](../../../data/processed/snap_large/graph_manifest.json)
stores the full native output for each input.

| Graph | 3-star | 3-path | Tailed triangle | 4-cycle | Diamond | 4-clique |
|---|---:|---:|---:|---:|---:|---:|
| Email-Eu-core | 47,103,723 | 85,410,303 | 29,963,822 | 4,647,873 | 5,012,720 | 423,750 |
| Facebook | 727,318,426 | 1,055,326,189 | 703,783,680 | 144,023,053 | 228,787,050 | 30,004,668 |
| Wikispeedia | 2,523,415,733 | 1,815,716,842 | 407,244,381 | 42,483,328 | 34,146,161 | 1,868,968 |

## Commands and checks

- Downloaded the three linked archives with curl. The sandbox initially failed
  DNS resolution. The permitted downloads succeeded. SHA-256 pins are in the script and manifest.
- Ran `.venv/bin/python scripts/prepare_snap_large.py` in the project root.
  Each file round-tripped through `load_prepared_graph` with matching adjacency,
  dimensions, canonical serialization and SHA-256. Input record totals matched
  the published counts. Wikispeedia resolved every link against its article roster.
- The script built `build/phase34/escape/count_four` from bundled revision
  `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3`. It invoked the binary once on
  each processed edge list in a separate temporary directory and validated the
  17 lines of each `out.txt`. Headers reported 32,128, 176,468 and 213,074
  adjacency entries respectively, twice the processed edge totals.
- All three graphs exceed the existing Python ESCAPE adapter's 1,000-vertex
  limit. The scoped native commands completed within the configured memory
  and timeout limits. Counts can exceed signed 32-bit range.
- No new dependencies. Execution covered data compatibility and native ground
  truth only. No privacy trials, experiment runs, benchmarks or figures.

## Files and handoff

- `data/processed/snap_large/` contains three canonical edge lists,
  three original-ID mappings and the opt-in manifest. The three source archives
  are local under `data/raw/snap_large/`. Build provenance is local under
  `build/phase34/escape/`.
- `scripts/prepare_snap_large.py` reproduces the processed files and the manifest.
  `data/fixtures/expected_counts.json` adds a separate `snap_large` lookup.
- `.gitignore`, `README.md`, `data/README.md`, `docs/status/STATUS.md` and this
  checkpoint document or expose the suite. Future evaluations can explicitly
  select the new manifest. Existing six-dataset configurations retain their inputs.
