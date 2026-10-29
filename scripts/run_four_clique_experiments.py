"""Run/replay/plot the small, NON-PRIVATE synthetic 4-clique comparison."""

import argparse
import json
import os
from pathlib import Path

from private_graphlets.escape import EscapeAdapter, EscapeError, build_count_four
from private_graphlets.four_clique_experiments import run_experiment, verify_results, plot_results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run')
    run.add_argument('--config',type=Path,default=Path('experiments/configs/four_clique_phase06.json'))
    run.add_argument('--output',type=Path,default=Path('experiments/results/four_clique_phase06'))
    run.add_argument('--escape-root',type=Path)
    run.add_argument('--build-dir',type=Path,default=Path('build/phase06/escape'))
    verify=sub.add_parser('verify')
    verify.add_argument('--results',type=Path,default=Path('experiments/results/four_clique_phase06'))
    verify.add_argument('--replay',action='store_true')
    plot=sub.add_parser('plot')
    plot.add_argument('--results',type=Path,default=Path('experiments/results/four_clique_phase06'))
    plot.add_argument('--output',type=Path,default=Path('plots/four_clique_phase06'))
    args=parser.parse_args()
    try:
        if args.command=='run':
            if args.output.exists(): raise ValueError('output already exists; use a new directory')
            adapter=EscapeAdapter(build_count_four(args.escape_root,build_dir=args.build_dir))
            result=run_experiment(args.config,args.output,adapter)
            print(json.dumps({k:result[k] for k in ('status','graphs','cells','trials','pipeline_seconds')}))
        elif args.command=='verify': print(json.dumps(verify_results(args.results,replay=args.replay)))
        else:
            os.environ.setdefault('MPLCONFIGDIR',str(Path('.cache/matplotlib').resolve()))
            result=plot_results(args.results,args.output)
            print(json.dumps({'plots':len(result['files_sha256']),'output':str(args.output)}))
    except (ValueError,OSError,KeyError,AssertionError,EscapeError,FloatingPointError,OverflowError) as exc:
        parser.exit(1,f'ERROR: {exc}\n')


if __name__=='__main__': main()
