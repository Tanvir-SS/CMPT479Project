# Phase 06 internal note A — Fixed-order component

2026-10-29. This is an internal checkpoint, **not a stopping point**.
Phase-06 authorization explicitly requires continuing to k-CoreD integration.

Added `four_clique_exact.py`, `randomized_response.py`, `four_clique.py` and
`tests/test_four_clique_core.py`. Implemented independent exact/oriented counts,
one-owner pair RR, stable prefix caps, the phase-05 replacement sensitivity,
client-side Laplace reports, explicit budgets, separate RNG domains and a
coordinator transcript without raw degrees/neighbors/scores.

Executed:

```bash
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q \
  tests/test_four_clique_core.py --junitxml=build/phase06/stage_a.xml \
  > build/phase06/stage_a.log 2>&1
```

**50 passed in 6.54s**, no failures/skips. Includes all 1,100 labeled graphs
through five vertices, eight real ESCAPE comparisons, finite sensitivity
enumeration, RR product algebra/statistics and analytic-SE graph-mean checks.
Six-SE tolerances were specified before running. No seed or threshold tuning.
There is no DP conclusion from these tests. Private ordering/cap are connected
in subsequent internal stages; the public-order path is already verified.

No dependency changes. Starting project HEAD:
`396f9215ac1c97b54e3717f4acf56f95442ae743`. Both external source fingerprints
are saved in `build/phase06/references-before.json` before implementation.
