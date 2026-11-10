"""Single hybrid diamond simulation; no exact diagnostics or experiment sweep."""

import argparse
import json
from pathlib import Path

from private_graphlets.diamond import DiamondBudget, estimate_diamonds
from private_graphlets.graph import load_edge_list


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path, help="Simple undirected n m edge-list file")
    parser.add_argument("--epsilon", required=True, type=float)
    parser.add_argument("--cap", required=True, type=int, help="Public fixed B >= 2")
    parser.add_argument("--budget", nargs=3, type=float, metavar=("O", "R", "W"),
                        help="Positive allocations summing to epsilon; O<=1 (default equal thirds)")
    parser.add_argument("--seed", type=int, help="Research simulation only, not deployment randomness")
    args = parser.parse_args(argv)
    try:
        budget = None if args.budget is None else DiamondBudget(args.epsilon, *args.budget)
        result = estimate_diamonds(load_edge_list(args.graph), args.epsilon, cap=args.cap,
                                   budget=budget, seed=args.seed)
        print(json.dumps(result.to_dict(), sort_keys=True, allow_nan=False))
    except (ValueError, OSError, OverflowError, FloatingPointError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
