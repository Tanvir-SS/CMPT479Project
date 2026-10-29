# Plots

Use Matplotlib's `Agg` backend on headless Ubuntu/WSL (`MPLBACKEND=Agg`). Generated
plots are ignored; keep scripts, input provenance and plot parameters in version
control. Phase 04 PNG/PDF figures are under `three_star_phase04/`. Recreate
directly from saved CSVs using `.venv/bin/python scripts/run_experiments.py plot`.
`plot_manifest.json` records input and figure hashes. No data are sampled or
manually adjusted during plotting. See `docs/EXPERIMENTS.md` for interpretation.
