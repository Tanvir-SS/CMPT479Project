"""Bounded, NON-PRIVATE validation on public synthetic graphs only."""

from dataclasses import dataclass
import hashlib
import math

import networkx as nx
import numpy as np

from private_graphlets.escape import EscapeAdapter
from private_graphlets.exact import count_three_stars, count_three_stars_bruteforce
from private_graphlets.graph import SimpleGraph
from private_graphlets.three_star import estimate_three_stars


@dataclass(frozen=True)
class ValidationCase:
    name: str
    graph: SimpleGraph
    parameters: dict[str, object]


def validation_cases() -> list[ValidationCase]:
    """24 preselected cases; generator seeds are separate from private records."""
    named = [
        ("edgeless_6", nx.empty_graph(6)),
        ("star_3", nx.star_graph(3)),
        ("star_4", nx.star_graph(4)),
        ("K4", nx.complete_graph(4)),
        ("K5", nx.complete_graph(5)),
        ("path_7", nx.path_graph(7)),
        ("overlapping_stars", nx.Graph([(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)])),
        ("disjoint_stars_and_isolates", nx.disjoint_union(nx.star_graph(3), nx.star_graph(3))),
        ("zero_vertices", nx.empty_graph(0)),
        ("one_isolate", nx.empty_graph(1)),
        ("single_edge", nx.path_graph(2)),
        ("triangle", nx.complete_graph(3)),
    ]
    named[7][1].add_nodes_from([8, 9])
    cases = [ValidationCase(name, SimpleGraph.from_edges(g.number_of_nodes(), g.edges()),
                            {"family": "named", "name": name}) for name, g in named]
    for seed in (11, 29, 47):
        for p in (0.2, 0.6):
            graph = nx.gnp_random_graph(10, p, seed=seed)
            cases.append(ValidationCase(
                f"ER_n10_p{p}_seed{seed}", SimpleGraph.from_edges(10, graph.edges()),
                {"family": "Erdos-Renyi", "n": 10, "p": p, "seed": seed},
            ))
        for m in (1, 2):
            graph = nx.barabasi_albert_graph(12, m, seed=seed)
            cases.append(ValidationCase(
                f"BA_n12_m{m}_seed{seed}", SimpleGraph.from_edges(12, graph.edges()),
                {"family": "Barabasi-Albert", "n": 12, "m": m, "seed": seed},
            ))
    return cases


def compare_case(adapter: EscapeAdapter, case: ValidationCase) -> dict[str, object]:
    """Retain actual ESCAPE file/stdout evidence alongside separately named counters."""
    run = adapter.run(case.graph)
    formula = count_three_stars(case.graph)
    brute = count_three_stars_bruteforce(case.graph)
    escape = run.counts.three_stars
    return {
        "name": case.name, "parameters": case.parameters,
        "num_vertices": case.graph.num_vertices, "num_edges": case.graph.num_edges,
        "normalized_num_vertices": run.counts.num_vertices,
        "added_isolates": run.counts.num_vertices - case.graph.num_vertices,
        "input_text": run.input_text,
        "input_sha256": hashlib.sha256(run.input_text.encode("ascii")).hexdigest(),
        "formula_three_stars": formula, "bruteforce_three_stars": brute,
        "escape_three_stars": escape, "all_agree": formula == brute == escape,
        "escape_connected_four": run.counts.connected_four,
        "escape_output_text": run.output_text,
        "escape_stdout": run.stdout, "escape_stderr": run.stderr,
        "escape_returncode": 0,
    }


def _local_variance(degree: int, scale: float) -> float:
    # Moment identity checked independently by quadrature in test_statistics.py.
    t = degree - 1
    a = (3 * t**2 - 1) / 6
    return 2 * a**2 * scale**2 + (7 * t**2 - 2 / 3) * scale**4 + 14 * scale**6


def epsilon_diagnostic(
    cases: list[ValidationCase], comparisons: list[dict[str, object]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Only two graphs x three epsilons x 3,000 trials, using the public estimator.

    Six analytic standard errors check means. Decreasing empirical MSE is a
    descriptive check for these fixed runs, not a universal monotonicity claim.
    No private release record is augmented with ground truth or seed data.
    """
    trials = 3_000
    summaries, samples = [], []
    for case_index, name in enumerate(("star_4", "K5")):
        case = next(c for c in cases if c.name == name)
        comparison = next(c for c in comparisons if c["name"] == name)
        if not comparison["all_agree"]:
            raise ValueError("epsilon diagnostic requires agreeing exact references")
        truth = comparison["escape_three_stars"]
        for epsilon_index, epsilon in enumerate((1.0, 2.0, 4.0)):
            seed = 2026102804 + 10 * case_index + epsilon_index
            rng = np.random.default_rng(seed)
            values = np.array([estimate_three_stars(case.graph, epsilon, rng=rng).estimate
                               for _ in range(trials)])
            variance = sum(_local_variance(len(row), 2 / epsilon) for row in case.graph.adjacency)
            standard_error = math.sqrt(variance / trials)
            mean = float(values.mean())
            z = (mean - truth) / standard_error
            summaries.append({
                "graph": name, "epsilon": epsilon, "laplace_scale": 2 / epsilon,
                "simulation_seed": seed, "trials": trials,
                "escape_ground_truth": truth, "mean_estimate": mean,
                "empirical_variance": float(values.var(ddof=1)),
                "empirical_mse": float(np.mean((values - truth)**2)),
                "analytic_variance": variance, "analytic_mean_standard_error": standard_error,
                "mean_z": z, "mean_within_six_se": abs(z) < 6,
                "negative_estimates": int(np.count_nonzero(values < 0)),
            })
            samples.append({"graph": name, "epsilon": epsilon, "simulation_seed": seed,
                            "estimates": values.tolist()})
    decreasing = {}
    for name in ("star_4", "K5"):
        rows = [row for row in summaries if row["graph"] == name]
        decreasing[name] = all(a["empirical_mse"] > b["empirical_mse"]
                               for a, b in zip(rows, rows[1:]))
    return {
        "result_type": "nonprivate_synthetic_evaluation", "simulation_only": True,
        "scope": "small controlled diagnostic, not full epsilon experiment grid",
        "mean_tolerance_standard_errors": 6, "rows": summaries,
        "empirical_mse_decreases": decreasing,
        "passed": all(row["mean_within_six_se"] for row in summaries) and all(decreasing.values()),
    }, samples
