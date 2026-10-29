# Experiments

Phase 04 evaluates 15 synthetic graphs (five families, 3–100 vertices) at epsilon
0.25/0.5/1/2/4 with 500 trials per cell. Run `scripts/run_experiments.py` and
consult `docs/EXPERIMENTS.md`. Earlier bounded phase-02 tests and the phase-03
diagnostic remain reproducible separately. No large real-world dataset study
has been run. Configurations belong
in `configs/`, generated outputs in `results/`. Every run must record the project
commit, source/data hashes, Python and dependency versions, seed, graph semantics,
privacy parameters and budget split, clipping/orientation assumptions, repetitions,
timing method, and command. Preserve raw estimates, including negative ones;
document any postprocessing separately. This is non-private evaluation metadata:
do not attach seeds, data hashes, exact truth or raw degrees to private releases.
Simulation seeds do not establish DP.
