# Permanent project instructions

This is the CMPT 479/982 research project **Privacy-Preserving Counting of Size-4
Graph Patterns Using Low-Out-Degree Orientations**. Read `docs/status/STATUS.md`
and its latest checkpoint before changing the project.

- Prioritize mathematical correctness and reproducible experiments over speed.
- Never invent test results or experimental findings. Record exact commands,
  observed outcomes, skipped checks, failures, and limitations separately.
- Never claim a formal differential privacy proof from empirical testing.
  Sensitivity, adjacency model, composition, and all released transcripts need
  mathematical analysis. The reference code is not proof of our implementation.
- Keep `/home/tsshergi/escape` and
  `/home/tsshergi/DistributedLEDPGraphAlgos` and
  `/home/tsshergi/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy` unchanged. Read and hash them in place;
  compile into `build/` or use isolated copies. Never run an upstream setup,
  partitioning, cleanup, or experiment script against the original checkout.
- Distinguish **non-induced** counts from induced counts, embeddings, and vertex
  sets. Our targets are connected simple undirected patterns on four distinct
  vertices: 3-star, 3-path, tailed triangle, 4-cycle, diamond, and 4-clique.
- Keep `docs/status/STATUS.md` current, including a current phase checklist.
  Create a numbered `docs/status/checkpoints/NN_description.md` for every phase;
  preserve earlier checkpoints. Record completed work, files, commands,
  dependencies, actual tests, findings, issues, and next steps.
- Update documentation whenever algorithm assumptions or implementations change.
- Never silently continue past an explicitly requested stopping point. The
  current phase 13 request authorizes dataset preparation/validation only:
  four public real-world graphs, twenty paper-compatible synthetic graphs,
  provenance, future configs, exact checks and documentation. Preserve existing
  privacy mechanisms, proofs, budgets, Phase-6 configuration and saved results.
  **Stop after dataset validation; no private sweep, optimization, Phase-10
  optimization work, commit or push.** Earlier phases and checkpoints remain
  historical; this request supersedes their completed stopping points only
  within the explicitly authorized dataset scope.
- All three references are pinned submodules under `third_party/`. Keep their
  sources unchanged too. Use `bash scripts/bootstrap_references.sh`, never
  `git submodule update --remote` for reproduction. Preserve exact gitlinks and
  `third_party/references.json`; review pin changes deliberately.
- Baseline inclusion is authorized by the project owner's report of author
  permission for this academic repository (2026-11-05). No license was found at
  its pin and none is assigned here. Do not publish private correspondence;
  confirm permission scope before broader redistribution. The two notebooks
  demonstrate 4-cycles, not all six patterns. They are not imported by our package.
- Reference resolution is explicit argument > `ESCAPE_ROOT` / `KCORED_ROOT` /
  `BASELINE_ROOT` > project-relative `third_party/` checkout. Never silently
  replace a configured source. Fingerprint all three; preserve historical
  path/revision provenance. Go and notebook environments are not Python runtime
  dependencies. Future 3-star baseline comparison remains unimplemented.
- Use Python 3.11 and `.venv`; keep code under `src/private_graphlets/`. Recreate
  with `bash scripts/setup.sh`; run `.venv/bin/python -m pytest -q`.
- Pin direct dependencies in `pyproject.toml`, regenerate the complete hashed
  `requirements.lock` deliberately, and document changes. Do not upgrade on
  normal setup. Keep build tools pinned and disable build isolation after the
  locked environment is installed.
- Keep raw data, generated plots, caches, build artifacts, and credentials out of Git.
  The owner explicitly approves the small phase-13 processed benchmark graphs,
  mappings and manifest under data/processed/ for version control. Keep those
  bytes deterministic; never replace a source archive whose pinned hash changed.
  Preserve small synthetic fixtures and provenance. Specify seeds explicitly in
  future simulation runs, but do not treat seeded PRNGs as production DP noise.
- Check graph validation, isolated vertices, ordering consistency, duplicate-edge
  handling, integer overflow, and normalization before trusting count comparisons.
- The 3-star simulator uses exactly `b=2/epsilon` and
  `Y*(Y-1)*(Y-2)/6 - b**2*(Y-1)`. Do not tune its correction, clip, truncate or
  round negative results to improve empirical accuracy. Include isolated vertices.
- Keep private result records separate from non-private exact evaluation. Never
  attach raw degrees, exact edge/count data, seeds or RNG state to private records.
  The vertex set is assumed fixed and public. Both seeded and unseeded NumPy
  sampling are research simulations, not cryptographically secure mechanisms.
- Formal privacy and accuracy proofs remain subject to independent review.
  Treat deferred work as deferred, not completed; preserve historical checkpoints.
- Use bundled ESCAPE by default, or override with `ESCAPE_ROOT` / `--escape-root`.
  Run integration tests against actual source; an absent-source skip is not a
  passed comparison.
  Preserve actual ESCAPE output and provenance separately from Python counters.
  The adapter pads graphs below four vertices with isolates and accepts at most
  1,000 vertices. Do not silently bypass its precision/scope guards.
- The 4-clique prototype is `experimental_unverified`. Keep noised k-CoreD,
  public fixed order and non-private oracle labels distinct; never substitute
  one silently. Use `(private_level, public_ID)` throughout the orientation.
- Preserve one RR report per unordered pair, independent stage randomness,
  prefix cap selection, replacement-aware sensitivity and client-side count
  noise. Track original and retained-clique targets separately in synthetic
  evaluation. Do not claim low-out-degree utility or executable LEDP from tests.
