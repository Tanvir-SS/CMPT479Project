"""Project information CLI; algorithm commands belong to later phases."""

import argparse
import json
import platform
from collections.abc import Sequence

from private_graphlets import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="private-graphlets",
        description="Privacy-preserving size-4 graph pattern research scaffold.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")
    info = commands.add_parser("info", help="Show project scope and setup status.")
    info.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    details = {
        "name": "private-graphlets",
        "version": __version__,
        "python": platform.python_version(),
        "phase": "01_setup_and_source_review",
        "count_semantics": "connected, undirected, non-induced, size-4",
        "patterns": ["3-star", "3-path", "tailed triangle", "4-cycle", "diamond", "4-clique"],
        "implemented_estimators": [],
    }
    if args.json:
        print(json.dumps(details, indent=2, sort_keys=True))
    else:
        print(f"{details['name']} {details['version']} (Python {details['python']})")
        print(f"Phase: {details['phase']}")
        print(f"Scope: {details['count_semantics']}")
        print("Private estimators: none implemented.")
    return 0
