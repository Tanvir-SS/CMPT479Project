# Experiments

Only bounded, seeded Monte Carlo checks on tiny synthetic graphs have been run:
phase 02 automated tests and phase 03's two-graph, three-epsilon diagnostic
(3,000 trials per cell). The latter is reproduced by `scripts/validate_escape.py`
and documented in `docs/ESCAPE_VALIDATION.md`. No full epsilon grid or large
dataset utility experiments have been implemented or run. Future configurations belong
in `configs/`, generated outputs in `results/`. Every run must record the project
commit, source/data hashes, Python and dependency versions, seed, graph semantics,
privacy parameters and budget split, clipping/orientation assumptions, repetitions,
timing method, and command. Preserve raw estimates, including negative ones;
document any postprocessing separately. This is non-private evaluation metadata:
do not attach seeds, data hashes, exact truth or raw degrees to private releases.
Simulation seeds do not establish DP.
