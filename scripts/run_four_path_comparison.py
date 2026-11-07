"""Run/verify the bounded NON-PRIVATE equal-budget P4 comparison."""
import argparse
import json
from pathlib import Path
from private_graphlets.four_path_comparison import load_config, conditions, run_comparison, verify_comparison, replot_comparison
from private_graphlets.escape import EscapeAdapter, build_count_four


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['plan','run','verify','plot'])
    p.add_argument('--config',type=Path,default=Path('experiments/configs/four_path_phase17_comparison.json'))
    p.add_argument('--output',type=Path,default=Path('experiments/results/four_path_phase17_comparison'))
    p.add_argument('--replay',action='store_true')
    a=p.parse_args()
    if a.command=='plan':
        c=load_config(a.config)
        result=dict(candidate_cells=len(c['cells']),baseline_conditions=len(conditions(c)),
                    candidate_trials=len(c['cells'])*c['trials'],baseline_trials=len(conditions(c))*c['trials'],
                    prediction_histories=len(c['cells'])*c['prediction_trials'])
    elif a.command=='run':
        if a.output.exists(): raise FileExistsError(a.output)
        adapter=EscapeAdapter(build_count_four(build_dir='build/phase17/escape'))
        result=run_comparison(a.config,a.output,adapter)
    elif a.command=='plot': result=replot_comparison(a.output)
    else: result=verify_comparison(a.output,a.replay)
    print(json.dumps(result,allow_nan=False))


if __name__=='__main__': main()
