# Phase 06 internal note B — k-CoreD port

2026-10-29. Internal milestone; continue to full-protocol tests and experiments.

Added `src/private_graphlets/kcore.py`, `tests/test_kcore.py` and upstream MIT
attribution in `THIRD_PARTY_NOTICES.md`. The port follows the supplied Go degree
threshold transformation, round/group constants, synchronous same-level queries,
geometric noise, bias terms and permanent stopping. It outputs final levels;
the order is `(level, public ID)`. No non-private fallback is available.

Differences: Python integer arithmetic, NumPy research noise, explicitly public
per-vertex noisy thresholds instead of worker maxima, corrected small-n/isolate
handling, validated public parameters and explicit numeric errors. A separate
`nonprivate_kcore_oracle` disables noise/bias and cannot be selected by the
private estimation API. The ideal conditional ledger bounds each endpoint's
threshold plus promotion budget by epsilon_O/2. Executable privacy and the
paper's low-out-degree utility bound remain unverified.

Executed:

```bash
.venv/bin/python -m pytest -q tests/test_kcore.py \
  --junitxml=build/phase06/stage_b.xml > build/phase06/stage_b.log 2>&1
```

**25 passed in 0.19s**, no failures/skips. Covered geometric PMF/moments,
zero-noise injected source-formula trace, synchronous local counts, transcript
reconstruction, per-vertex budget limits, replay, private-order variability,
parameter validation and separately labeled noiseless oracle counts.

The source lookup initially queried a nonexistent `configs/` directory; `rg`
reported that path missing while finding the experiment-driver settings. No
source file was modified. No dependence on upstream config/driver files was
introduced. Full source correspondence, remaining assumptions and transcript
accounting are recorded in `docs/KCORED_INTEGRATION.md` in the final checkpoint.
