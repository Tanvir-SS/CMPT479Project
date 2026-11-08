# Active processed datasets

The active collection contains exactly six canonical graphs and their original-ID
mappings: four real-world graphs and BA/SBM at n=100. The existing graph/mapping
bytes are unchanged. The 18 other synthetic graphs and mappings were removed
from this collection at the owner's request in phase 19.

`graph_manifest.json` retains each selected graph's original hashes, generation
parameters and verified ESCAPE evidence. The full original 24-graph provenance
is archived under `docs/status/phase13_dataset_provenance/`; completed historical
reports remain intact. Raw archives and experiment output remain Git-ignored.
Small correctness fixtures in `data/fixtures/` are preserved separately.
See [data instructions](../README.md) and [evaluation conventions](../../docs/EVALUATION_STANDARDS.md).
