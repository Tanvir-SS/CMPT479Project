"""Run, verify or plot the public synthetic 3-star accuracy experiment."""

import argparse
import json
import os
from pathlib import Path

from private_graphlets.escape import EscapeError, EscapeAdapter, build_count_four
from private_graphlets.experiments import run_experiment, verify_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Run all configured trials; requires real ESCAPE.")
    run.add_argument("--config", type=Path, default=Path("experiments/configs/three_star_phase04.json"))
    run.add_argument("--output", type=Path, default=Path("experiments/results/three_star_phase04"))
    run.add_argument("--escape-root", type=Path, help="ESCAPE source, or use ESCAPE_ROOT.")
    run.add_argument("--build-dir", type=Path, default=Path("build/phase04/escape"))
    verify = commands.add_parser("verify", help="Verify saved hashes and recompute every metric.")
    verify.add_argument("--results", type=Path, default=Path("experiments/results/three_star_phase04"))
    verify.add_argument("--replay", action="store_true", help="Replay every estimate exactly; timings vary.")
    plot = commands.add_parser("plot", help="Generate figures only from saved CSVs.")
    plot.add_argument("--results", type=Path, default=Path("experiments/results/three_star_phase04"))
    plot.add_argument("--output", type=Path, default=Path("plots/three_star_phase04"))
    args = parser.parse_args()
    try:
        if args.command == "run":
            if args.output.exists():
                raise ValueError(f"output already exists; choose a new --output: {args.output}")
            binary = build_count_four(args.escape_root, build_dir=args.build_dir)
            result = run_experiment(args.config, args.output, EscapeAdapter(binary))
            print(json.dumps({k: result[k] for k in ("status", "graphs", "cells", "trials", "pipeline_seconds")}))
        elif args.command == "verify":
            print(json.dumps(verify_results(args.results, replay=args.replay)))
        else:
            os.environ.setdefault("MPLCONFIGDIR", str(Path(".cache/matplotlib").resolve()))
            from private_graphlets.experiment_plots import plot_results
            result = plot_results(args.results, args.output)
            print(json.dumps({"plots": len(result["files_sha256"]), "output": str(args.output)}))
    except (EscapeError, OSError, ValueError, KeyError, AssertionError, FloatingPointError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
