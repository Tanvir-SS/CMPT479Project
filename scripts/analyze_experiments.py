"""Regenerate a compact NON-PRIVATE accuracy handoff from saved experiment data."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from private_graphlets.experiments import generate_graph, sha256, verify_results
from private_graphlets.three_star import corrected_local_stars


def variance_precision(graph, epsilon, trials, observed_variance):
    """Ideal fourth moments by quadrature, checked against polynomial expansion.

    The central error is cubic, so its fourth power has degree 12. Seven-node
    Gauss-Laguerre quadrature integrates each one-sided polynomial exactly in
    real arithmetic; floating-point agreement is a numerical cross-check only.
    """
    b = 2/epsilon
    nodes, weights = np.polynomial.laguerre.laggauss(7)
    variances, fourth = [], []
    for neighbors in graph.adjacency:
        degree = len(neighbors)
        t = degree - 1
        a = (3*t*t - 1)/6
        plus = corrected_local_stars(degree + b*nodes, b) - math.comb(degree, 3)
        minus = corrected_local_stars(degree - b*nodes, b) - math.comb(degree, 3)
        v = float(np.dot(weights, (plus**2 + minus**2)/2))
        m4 = float(np.dot(weights, (plus**4 + minus**4)/2))
        coefficients = np.polynomial.polynomial.polypow([-t*b*b, a-b*b, t/2, 1/6], 4)
        expanded = math.fsum(float(c)*math.factorial(k)*b**k
                             for k, c in enumerate(coefficients) if k % 2 == 0)
        if not math.isclose(m4, expanded, rel_tol=2e-11):
            raise ValueError("fourth-moment quadrature and expansion disagree")
        variances.append(v)
        fourth.append(m4)
    variance = math.fsum(variances)
    mu4 = math.fsum(m4 - 3*v*v for m4, v in zip(fourth, variances)) + 3*variance**2
    standard_error = math.sqrt((mu4 - (trials-3)/(trials-1)*variance**2)/trials)
    return {"ideal_variance": variance, "ideal_fourth_central_moment": mu4,
            "sample_variance_standard_error": standard_error,
            "sample_variance_relative_se": standard_error/variance,
            "observed_variance_z": (observed_variance-variance)/standard_error,
            "quadrature_expansion_agree": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("experiments/results/three_star_phase04"))
    parser.add_argument("--output", type=Path, default=Path("build/phase04/accuracy.json"))
    args = parser.parse_args()
    verification = verify_results(args.results)
    config = json.loads((args.results / "config.json").read_text())
    graphs = pd.read_csv(args.results / "graphs.csv", float_precision="round_trip")
    summary = pd.read_csv(args.results / "summary.csv", float_precision="round_trip")
    raw = pd.read_csv(args.results / "trials.csv", float_precision="round_trip")
    extrema = []
    for label, index in (("minimum", summary.variance_ratio.idxmin()),
                         ("maximum", summary.variance_ratio.idxmax())):
        row = summary.loc[index]
        graph = generate_graph(next(g for g in config["graphs"] if g["id"] == row.graph_id))
        extrema.append({"selection": label, "graph_id": row.graph_id, "epsilon": float(row.epsilon),
                        "observed_variance": float(row.sample_variance),
                        "variance_ratio": float(row.variance_ratio),
                        **variance_precision(graph, float(row.epsilon), int(row.trials), float(row.sample_variance))})
    # These extrema are explicitly post-hoc diagnostics; no estimates are changed.
    report = {
        "schema_version": 1, "result_type": "nonprivate_accuracy_review", "verification": verification,
        "results_path": str(args.results), "analysis_source_sha256": sha256(Path(__file__)),
        "input_sha256": {name: sha256(args.results/name) for name in
                         ("config.json", "graphs.csv", "trials.csv", "summary.csv", "manifest.json")},
        "graph_counts": graphs[["graph_id", "num_vertices", "num_edges", "exact_three_stars"]].to_dict("records"),
        "max_absolute_mean_z": float(summary.bias_z.abs().max()),
        "mean_deviations_above_2_se": int((summary.bias_z.abs()>2).sum()),
        "mean_deviations_above_3_se": int((summary.bias_z.abs()>3).sum()),
        "negative_estimates": int((raw.estimate<0).sum()),
        "undefined_relative_cells": int(summary.relative_rmse.isna().sum()),
        "graphs_with_monotonically_decreasing_observed_rmse": sum(
            bool(np.all(np.diff(group.sort_values("epsilon").rmse)<0))
            for _, group in summary.groupby("graph_id")),
        "variance_ratio_extremes_posthoc": extrema,
        "pipeline_seconds": json.loads((args.results/"manifest.json").read_text())["pipeline_seconds"],
        "mechanism_seconds_total": float(raw.mechanism_seconds.sum()),
        "mechanism_seconds_mean": float(raw.mechanism_seconds.mean()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Saved accuracy review: {args.output}; {len(summary)} cells, {len(raw)} trials")


if __name__ == "__main__":
    main()
