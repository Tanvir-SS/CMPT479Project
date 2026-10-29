"""Compile read-only ESCAPE sources and verify hand-counted synthetic fixtures.

This checks the reference executable's interface, not any private estimator.
"""

import argparse
from decimal import Decimal
import json
from pathlib import Path
import subprocess


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=project.parent / "escape")
    args = parser.parse_args()
    source = args.source.resolve()
    build = project / "build/reference-checks/escape"
    build.mkdir(parents=True, exist_ok=True)
    executable = build / "count_four"
    command = [
        "g++", "-std=c++11", "-O2", "-Wall", "-I", str(source),
        str(source / "exe/count_four.cpp"), str(source / "Graph.cpp"),
        str(source / "GraphIO.cpp"), str(source / "TriangleProgram.cpp"),
        "-o", str(executable),
    ]
    (build / "compile-command.json").write_text(json.dumps(command, indent=2) + "\n")
    with (build / "compile.log").open("w") as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)

    fixtures = project / "data/fixtures"
    cases = json.loads((fixtures / "expected_counts.json").read_text())["cases"]
    results = []
    for name, expected in cases.items():
        run_dir = build / name
        run_dir.mkdir(exist_ok=True)
        graph = fixtures / f"{name}.edges"
        with (run_dir / "stdout.log").open("w") as log:
            subprocess.run([str(executable), str(graph)], cwd=run_dir, check=True,
                           stdout=log, stderr=subprocess.STDOUT, timeout=30)
        raw = (run_dir / "out.txt").read_text().splitlines()
        if len(raw) != 17:
            raise RuntimeError(f"{name}: expected 17 output lines, got {len(raw)}")
        n, m = map(int, graph.read_text().splitlines()[0].split())
        if [int(raw[0]), int(raw[1])] != [n, 2 * m]:
            raise RuntimeError(f"{name}: unexpected n, 2m header: {raw[:2]}")
        counts = [Decimal(value) for value in raw[11:17]]
        if counts != list(map(Decimal, expected)):
            raise RuntimeError(f"{name}: expected {expected}, got {counts}")
        results.append({"fixture": name, "counts": [int(value) for value in counts]})
        print(f"PASS {name}: {[int(value) for value in counts]}")
    (build / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"{len(results)} ESCAPE fixtures passed; artifacts: {build}")


if __name__ == "__main__":
    main()
