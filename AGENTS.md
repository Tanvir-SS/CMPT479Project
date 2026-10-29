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
  `/home/tsshergi/DistributedLEDPGraphAlgos` unchanged. Read and hash them in place;
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
- Never silently continue past an explicitly requested stopping point. Phase 02
  explicitly authorizes exact and bias-corrected private non-induced 3-star
  counting, CLI and tests. **Stop once these are implemented and verified. Do
  not start ESCAPE integration, large experiments, 4-clique estimation or other
  private algorithms without a later explicit instruction.**
- Use Python 3.11 and `.venv`; keep code under `src/private_graphlets/`. Recreate
  with `bash scripts/setup.sh`; run `.venv/bin/python -m pytest -q`.
- Pin direct dependencies in `pyproject.toml`, regenerate the complete hashed
  `requirements.lock` deliberately, and document changes. Do not upgrade on
  normal setup. Keep build tools pinned and disable build isolation after the
  locked environment is installed.
- Keep data, generated plots, caches, build artifacts, and credentials out of Git.
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
