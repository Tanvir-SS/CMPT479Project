# Experiment configurations

`three_star_phase04.json` fixes 15 synthetic graphs, five epsilon values and
500 independent simulation streams per cell. Graph seeds and mechanism root
seed are separate. Copying or reordering this config defines a new run; preserve
the exact executed config and generated graph hashes. These are research
parameters, not recommended production privacy budgets.

The active K4 configuration is `four_clique_six_datasets.json`: six fixed inputs,
epsilon .5/1/2/4, 200 trials, master seed 202611081901, candidate kcore_noisy_cap
only, and equal O/D/R/C quarters. Run it with `scripts/evaluate_four_clique.py`.
The original dataset-preparation configurations were retired to
`docs/status/phase13_dataset_provenance/`. Completed Phase-6 and other-pattern
configurations remain historical and unchanged; they are not run in this task.
