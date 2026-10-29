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
    exact4 = commands.add_parser("exact-four-cliques", help="NON-PRIVATE exact K4 count.")
    exact4.add_argument("graph",type=Path)
    estimate4 = commands.add_parser("estimate-four-cliques",help="Experimental K4 local-report simulation.")
    estimate4.add_argument("graph",type=Path)
    estimate4.add_argument("--epsilon",type=float,required=True)
    estimate4.add_argument("--seed",type=int,help="Simulation seed; never a production DP seed.")
    estimate4.add_argument("--ordering",choices=["fixed","kcore"],default="kcore")
    estimate4.add_argument("--cap-mode",choices=["noisy","public","uncapped"],default="noisy")
    estimate4.add_argument("--cap",type=int)
    estimate4.add_argument("--beta",type=float,default=0.05)
    estimate4.add_argument("--public-order",help="Comma-separated public IDs, fixed ordering only.")
    estimate4.add_argument("--budget",nargs=4,type=float,metavar=("O","D","R","C"))
    estimate4.add_argument("--psi",type=float,default=0.5)
    estimate4.add_argument("--threshold-fraction",type=float,default=0.5)
    estimate4.add_argument("--bias-factor",type=int,default=1)
    baseline4 = commands.add_parser("baseline-four-cliques",help="Canonical six-factor debiased-RR simulation.")
    baseline4.add_argument("graph",type=Path)
    baseline4.add_argument("--epsilon",type=float,required=True)
    baseline4.add_argument("--seed",type=int)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    if args.command in {"exact-four-cliques","estimate-four-cliques","baseline-four-cliques"}:
        try:
            graph=load_edge_list(args.graph)
            if args.command=="exact-four-cliques":
                from private_graphlets.four_clique_exact import count_four_cliques
                result={"schema_version":1,"result_type":"exact_ground_truth","pattern":"4-clique",
                        "count_semantics":"non-induced_unlabeled","count":count_four_cliques(graph),
                        "num_vertices":graph.num_vertices,"num_edges":graph.num_edges}
            elif args.command=="baseline-four-cliques":
                from private_graphlets.four_clique_baseline import estimate_four_cliques_baseline
                result=estimate_four_cliques_baseline(graph,args.epsilon,seed=args.seed).to_dict()
            else:
                from private_graphlets.four_clique import CliqueBudget, estimate_four_cliques
                from private_graphlets.kcore import KCoreConfig
                budget=None if args.budget is None else CliqueBudget(args.epsilon,*args.budget)
                order=None if args.public_order is None else tuple(map(int,args.public_order.split(',')))
                result=estimate_four_cliques(graph,args.epsilon,ordering=args.ordering,cap_mode=args.cap_mode,
                    cap=args.cap,seed=args.seed,budget=budget,beta=args.beta,public_order=order,
                    kcore_config=KCoreConfig(args.psi,args.threshold_fraction,args.bias_factor)).to_dict()
            print(json.dumps(result,sort_keys=True,allow_nan=False))
        except (ValueError,OSError,UnicodeError,FloatingPointError,OverflowError) as exc:
            parser.error(str(exc))
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
        "phase": "06_full_four_clique_implementation",
        "count_semantics": "connected, undirected, non-induced, size-4",
        "patterns": ["3-star", "3-path", "tailed triangle", "4-cycle", "diamond", "4-clique"],
        "implemented_estimators": ["3-star"],
        "experimental_estimators": ["4-clique"],
    }
    if args.json:
        print(json.dumps(details, indent=2, sort_keys=True))
    else:
        print(f"{details['name']} {details['version']} (Python {details['python']})")
        print(f"Phase: {details['phase']}")
        print(f"Scope: {details['count_semantics']}")
        print("Private estimators: bias-corrected Laplace 3-star (research simulation).")
        print("Experimental: k-CoreD / fixed-order 4-clique and six-factor RR baseline (unverified).")
    return 0
