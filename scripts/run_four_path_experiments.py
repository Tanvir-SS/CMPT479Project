"""Run or verify the bounded NON-PRIVATE Phase 4A MSE validation study."""
import argparse
import json
from pathlib import Path
from private_graphlets.four_path_experiments import run_experiment, verify_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run')
    run.add_argument('--config', type=Path, default=Path('experiments/configs/four_path_phase12_validation.json'))
    run.add_argument('--output', type=Path, default=Path('experiments/results/four_path_phase12_validation'))
    verify = commands.add_parser('verify')
    verify.add_argument('--results', type=Path, default=Path('experiments/results/four_path_phase12_validation'))
    verify.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'run':
            result = run_experiment(args.config, args.output)
            result = {k: result[k] for k in ('status', 'graphs', 'full_trials', 'prediction_trials', 'pipeline_seconds')}
        else:
            result = verify_results(args.results, replay=args.replay)
        print(json.dumps(result, allow_nan=False))
    except (ValueError, OSError, KeyError, TypeError, AssertionError, FloatingPointError, OverflowError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
