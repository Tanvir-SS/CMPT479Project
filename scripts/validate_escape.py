"""Build ESCAPE and run all three-way exact comparisons plus a bounded diagnostic."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import networkx as nx
import numpy as np

from private_graphlets.escape import EscapeAdapter, EscapeError, build_count_four
from private_graphlets.escape_validation import compare_case, epsilon_diagnostic, validation_cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--escape-root", type=Path, help="ESCAPE source; defaults to ESCAPE_ROOT.")
    parser.add_argument("--build-dir", type=Path, default=Path("build/escape"))
    parser.add_argument("--output", type=Path, default=Path("build/phase03/validation.json"))
    parser.add_argument("--samples-output", type=Path,
                        default=Path("build/phase03/epsilon_samples.json"))
    args = parser.parse_args()
    report = {"schema_version": 1, "result_type": "nonprivate_synthetic_validation",
              "count_semantics": "non-induced", "status": "running", "comparisons": [],
              "software": {"python": platform.python_version(), "numpy": np.__version__,
                           "networkx": nx.__version__}}
    try:
        binary = build_count_four(args.escape_root, build_dir=args.build_dir)
        adapter = EscapeAdapter(binary)
        report["build"] = json.loads((args.build_dir / "build.json").read_text())
        report["executable_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        cases = validation_cases()
        for case in cases:
            row = compare_case(adapter, case)
            report["comparisons"].append(row)
            print(f"{'PASS' if row['all_agree'] else 'FAIL'} {case.name}: "
                  f"formula={row['formula_three_stars']} brute={row['bruteforce_three_stars']} "
                  f"ESCAPE={row['escape_three_stars']}")
        if not all(row["all_agree"] for row in report["comparisons"]):
            raise ValueError("exact reference disagreement; see comparison records")
        diagnostic, samples = epsilon_diagnostic(cases, report["comparisons"])
        report["epsilon_diagnostic"] = diagnostic
        args.samples_output.parent.mkdir(parents=True, exist_ok=True)
        args.samples_output.write_text(json.dumps({
            "result_type": "nonprivate_synthetic_simulation_samples", "runs": samples,
        }, indent=2, allow_nan=False) + "\n")
        if not diagnostic["passed"]:
            raise ValueError("controlled epsilon diagnostic failed; see recorded observations")
        report["status"] = "passed"
    except (EscapeError, ValueError, OSError, FloatingPointError) as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        print(f"ERROR: {exc}", file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"{len(report['comparisons'])} comparisons; status={report['status']}; report: {args.output}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
