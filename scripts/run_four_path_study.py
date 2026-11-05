"""Plan, run or verify the bounded NON-PRIVATE Phase 4B accuracy study."""
import argparse
import json
from pathlib import Path
from private_graphlets.escape import EscapeAdapter, build_count_four
from private_graphlets.four_path_study import load_config, workload, run_study, verify_study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan', 'run', 'verify'])
    parser.add_argument('--config', type=Path, default=Path('experiments/configs/four_path_phase13_accuracy.json'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/four_path_phase13_accuracy'))
    parser.add_argument('--replay', action='store_true')
    parser.add_argument('--escape-root', type=Path)
    args = parser.parse_args()
    if args.command == 'plan':
        result = workload(load_config(args.config))
    elif args.command == 'run':
        # Refuse existing paths before compilation or any other work.
        if args.output.exists():
            raise FileExistsError(args.output)
        executable = build_count_four(args.escape_root, build_dir='build/phase13/escape')
        result = run_study(args.config, args.output, EscapeAdapter(executable))
        result = {k: v for k, v in result.items() if k not in ['files_sha256', 'provenance']}
    else:
        result = verify_study(args.output, replay=args.replay)
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
