"""Compile read-only ESCAPE sources and verify hand-counted synthetic fixtures.

This checks the reference executable's interface, not any private estimator.
"""

import argparse
import json
from pathlib import Path

from private_graphlets.escape import EscapeAdapter, build_count_four
from private_graphlets.graph import load_edge_list


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--escape-root", "--source", dest="escape_root", type=Path,
                        help="ESCAPE source (defaults to ESCAPE_ROOT); --source is an alias.")
    args = parser.parse_args()
    build = project / "build/reference-checks/escape"
    adapter = EscapeAdapter(build_count_four(args.escape_root, build_dir=build))

    fixtures = project / "data/fixtures"
    cases = json.loads((fixtures / "expected_counts.json").read_text())["cases"]
    results = []
    for name, expected in cases.items():
        run = adapter.run(load_edge_list(fixtures / f"{name}.edges"))
        counts = list(run.counts.connected_four.values())
        if counts != expected:
            raise RuntimeError(f"{name}: expected {expected}, got {counts}")
        results.append({"fixture": name, "escape_counts": counts,
                        "escape_output_text": run.output_text,
                        "escape_stdout": run.stdout, "escape_stderr": run.stderr})
        print(f"PASS {name}: {counts}")
    (build / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"{len(results)} ESCAPE fixtures passed; artifacts: {build}")


if __name__ == "__main__":
    main()
