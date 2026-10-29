"""Separate commands for private mechanism simulations and exact evaluation."""

import argparse
import json
import platform
from pathlib import Path
from collections.abc import Sequence

import numpy as np

from private_graphlets import __version__
from private_graphlets.graph import load_edge_list
from private_graphlets.three_star import estimate_three_stars


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="private-graphlets",
        description="Privacy-preserving size-4 graph pattern research simulations.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")
    info = commands.add_parser("info", help="Show project scope and setup status.")
    info.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    private = commands.add_parser(
        "estimate-three-stars", help="Simulate the corrected Laplace 3-star estimator (JSON)."
    )
    private.add_argument("graph", type=Path, help="Edge-list path with an n m header.")
    private.add_argument("--epsilon", type=float, required=True, help="Total edge-level epsilon > 0.")
    private.add_argument(
        "--seed", type=int, help="Optional nonnegative simulation seed; not cryptographic randomness."
    )
    exact = commands.add_parser(
        "exact-three-stars", help="Compute NON-PRIVATE exact ground truth (JSON)."
    )
    exact.add_argument("graph", type=Path, help="Edge-list path with an n m header.")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    if args.command in {"estimate-three-stars", "exact-three-stars"}:
        try:
            graph = load_edge_list(args.graph)
            if args.command == "estimate-three-stars":
                result = estimate_three_stars(graph, args.epsilon, seed=args.seed).to_dict()
            else:
                # Exact evaluation is deliberately absent from the private execution path.
                from private_graphlets.exact import count_three_stars
                result = {
                    "schema_version": 1,
                    "result_type": "exact_ground_truth",
                    "pattern": "3-star",
                    "count_semantics": "non-induced",
                    "count": count_three_stars(graph),
                    "num_vertices": graph.num_vertices,
                    "num_edges": graph.num_edges,
                }
            result["software"] = {
                "private_graphlets": __version__, "python": platform.python_version(),
                "numpy": np.__version__,
            }
            print(json.dumps(result, sort_keys=True, allow_nan=False))
        except (ValueError, OSError, UnicodeError, FloatingPointError) as exc:
            parser.error(str(exc))
        return 0

    details = {
        "name": "private-graphlets",
        "version": __version__,
        "python": platform.python_version(),
        "phase": "04_experiments_and_review",
        "count_semantics": "connected, undirected, non-induced, size-4",
        "patterns": ["3-star", "3-path", "tailed triangle", "4-cycle", "diamond", "4-clique"],
        "implemented_estimators": ["3-star"],
    }
    if args.json:
        print(json.dumps(details, indent=2, sort_keys=True))
    else:
        print(f"{details['name']} {details['version']} (Python {details['python']})")
        print(f"Phase: {details['phase']}")
        print(f"Scope: {details['count_semantics']}")
        print("Private estimators: bias-corrected Laplace 3-star (research simulation).")
    return 0
