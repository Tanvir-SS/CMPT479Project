"""Print read-only Git/source fingerprints for the two external references."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


REVIEWED = {
    "escape": [
        "Escape/FourVertex.h", "Escape/Digraph.h", "Escape/GetAllCounts.h",
        "exe/count_four.cpp", "Escape/Triadic.h", "Escape/Conversion.h",
        "Escape/Graph.h", "Graph.cpp", "GraphIO.cpp", "common.mk",
        "wrappers/subgraph_counts.py", "LICENSE",
    ],
    "ledp": [
        "algorithms/kcore-ldp.go", "algorithms/triangle-counting-ldp.go",
        "algorithms/rr-baseline.go", "algorithms/rr-triangle-count.go",
        "data-structures/lds.go", "data-structures/graph.go", "noise/geometric.go",
        "noise/noise.go", "experiments/experiments.go", "cmd/main.go",
        "scripts/graph_partitioner.py", "go.mod", "go.sum", "LICENSE",
    ],
}


def fingerprint(path: Path, reviewed: list[str]) -> dict:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(path), *args])

    names = sorted(git("ls-files", "-z").decode().split("\0")[:-1])
    tree = hashlib.sha256()
    for name in names:
        digest = hashlib.sha256((path / name).read_bytes()).hexdigest()
        tree.update(f"{name}\0{digest}\n".encode())
    return {
        "path_at_review": str(path.resolve()),
        "commit": git("rev-parse", "HEAD").decode().strip(),
        "origin": git("remote", "get-url", "origin").decode().strip(),
        "status_porcelain": git("status", "--porcelain", "--untracked-files=all").decode(),
        "tracked_file_count": len(names),
        "tracked_tree_sha256": tree.hexdigest(),
        "reviewed_file_sha256": {
            name: hashlib.sha256((path / name).read_bytes()).hexdigest()
            for name in reviewed
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parent = Path(__file__).resolve().parents[2]
    parser.add_argument("--escape", type=Path, default=parent / "escape")
    parser.add_argument("--ledp", type=Path, default=parent / "DistributedLEDPGraphAlgos")
    args = parser.parse_args()
    result = {
        name: fingerprint(getattr(args, name), files)
        for name, files in REVIEWED.items()
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
