"""Figures derived only from saved experiment CSVs; no new mechanism samples."""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from private_graphlets.experiments import sha256, verify_results


FAMILY_LABELS = {"star": "Star", "erdos_renyi": "Erdős–Rényi",
                 "barabasi_albert": "Barabási–Albert", "stochastic_block": "Stochastic block",
                 "complete": "Complete"}


def plot_results(results: Path, output: Path) -> dict:
    """Save PNG/PDF artifacts, with full-range estimates including negative tails."""
    verify_results(results)
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    config = json.loads((results / "config.json").read_text())
    summary = pd.read_csv(results / "summary.csv", float_precision="round_trip")
    raw = pd.read_csv(results / "trials.csv", float_precision="round_trip")
    output.mkdir(parents=True, exist_ok=True)
    artifacts = []

    def save(fig, name):
        for extension in ("png", "pdf"):
            path = output / f"{name}.{extension}"
            metadata = {"CreationDate": None, "ModDate": None} if extension == "pdf" else None
            fig.savefig(path, dpi=160, bbox_inches="tight", metadata=metadata)
            artifacts.append(path)
        plt.close(fig)

    with plt.rc_context({"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10}):
        families = list(dict.fromkeys(summary.family))
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), layout="constrained")
        for axis, family in zip(axes.flat, families):
            for name, group in summary[summary.family == family].groupby("graph_id", sort=False):
                group = group.sort_values("epsilon")
                axis.plot(group.epsilon, group.rmse, "o-", label=name)
            axis.set(xscale="log", yscale="log", xlabel="Privacy budget ε", ylabel="RMSE (star count)",
                     title=FAMILY_LABELS[family])
            axis.set_xticks(config["epsilons"], [str(x) for x in config["epsilons"]])
            axis.grid(alpha=0.3, which="both")
            axis.legend(fontsize=8)
        for axis in list(axes.flat)[len(families):]:
            axis.set_visible(False)
        fig.suptitle(f"Non-induced 3-star accuracy: RMSE over {config['trials']} trials per cell")
        save(fig, "rmse_vs_epsilon")

        epsilons = config["epsilons"]
        columns = min(3, len(epsilons))
        rows = math.ceil(len(epsilons) / columns)
        fig, axes = plt.subplots(rows, columns, figsize=(15, 4*rows), squeeze=False, layout="constrained")
        for axis, epsilon in zip(axes.flat, epsilons):
            group = summary[summary.epsilon == epsilon]
            for family in families:
                selected = group[group.family == family]
                axis.errorbar(selected.exact_three_stars, selected.mean_estimate,
                              yerr=2*selected.analytic_mean_se, fmt="o", capsize=2,
                              label=FAMILY_LABELS[family], alpha=0.8)
            maximum = max(1, float(group.exact_three_stars.max()))
            axis.plot([0, maximum], [0, maximum], "k--", linewidth=1, label="Mean = exact")
            axis.set(xscale="symlog", yscale="symlog", xlabel="Exact non-induced 3-star count",
                     ylabel="Mean estimated count", title=f"ε = {epsilon:g}")
            axis.grid(alpha=0.25)
        axes.flat[0].legend(fontsize=8)
        for axis in list(axes.flat)[len(epsilons):]:
            axis.set_visible(False)
        fig.suptitle("Mean estimates vs exact counts — bars: ±2 analytic Monte Carlo SE\n"
                     "Symmetric log axes preserve zero/negative values; bars are not guaranteed confidence intervals")
        save(fig, "mean_vs_exact")

        representative = config["representative_graph"]
        truth = int(summary[summary.graph_id == representative].exact_three_stars.iloc[0])
        fig, axes = plt.subplots(1, len(epsilons), figsize=(4*len(epsilons), 4.5),
                                 squeeze=False, layout="constrained")
        for axis, epsilon in zip(axes.flat, epsilons):
            values = raw[(raw.graph_id == representative) & (raw.epsilon == epsilon)].estimate
            axis.hist(values, bins=40, alpha=0.8, color="steelblue", label="All trials")
            axis.axvline(truth, color="black", linestyle="--", label=f"Exact = {truth}")
            axis.set(xlabel="Estimated non-induced 3-star count", ylabel="Trials", title=f"ε = {epsilon:g}")
            axis.ticklabel_format(axis="x", style="sci", scilimits=(-3, 3))
        axes.flat[0].legend(fontsize=8)
        fig.suptitle(f"Estimate distributions: {representative} — full range; independent axis limits")
        save(fig, "estimate_distributions")

        ratios = summary.pivot(index="graph_id", columns="epsilon", values="variance_ratio")
        ratios = ratios.reindex(index=[g["id"] for g in config["graphs"]], columns=epsilons)
        logarithms = np.log2(ratios.to_numpy())
        bound = max(0.25, float(np.abs(logarithms).max()))
        fig, axis = plt.subplots(figsize=(9, max(5, 0.38*len(ratios))), layout="constrained")
        artist = axis.imshow(logarithms, aspect="auto", cmap="coolwarm", vmin=-bound, vmax=bound)
        axis.set_xticks(range(len(epsilons)), [str(x) for x in epsilons])
        axis.set_yticks(range(len(ratios)), ratios.index)
        axis.set(xlabel="Privacy budget ε", ylabel="Graph",
                 title="Empirical sample variance / ideal-noise variance\n"
                       "Values near 1 agree; finite trials can miss rare cubic tails")
        for i in range(len(ratios)):
            for j in range(len(epsilons)):
                axis.text(j, i, f"{ratios.iloc[i,j]:.2f}", ha="center", va="center", fontsize=8)
        fig.colorbar(artist, ax=axis, label="log₂(variance ratio)")
        save(fig, "variance_ratio")

    manifest = {"result_type": "nonprivate_figures_from_saved_data",
                "input_sha256": {name: sha256(results / name) for name in ("config.json", "trials.csv", "summary.csv")},
                "files_sha256": {path.name: sha256(path) for path in artifacts}}
    (output / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
