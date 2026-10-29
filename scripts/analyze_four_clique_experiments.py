"""Regenerate compact NON-PRIVATE phase-06 observations from verified saved CSVs."""

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from private_graphlets.experiments import sha256
from private_graphlets.four_clique_experiments import verify_results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,default=Path('experiments/results/four_clique_phase06'))
    parser.add_argument('--output',type=Path,default=Path('build/phase06/accuracy_summary.json'))
    args=parser.parse_args()
    verified=verify_results(args.results)
    summary=pd.read_csv(args.results/'summary.csv',float_precision='round_trip')
    raw=pd.read_csv(args.results/'trials.csv',dtype={'seed':str},float_precision='round_trip')
    pivot=summary.pivot(index=['graph','epsilon'],columns='method',values='rmse')
    comparisons={}
    for method in pivot.columns:
        if method=='baseline': continue
        ratio=pivot[method]/pivot.baseline
        comparisons[method]={'lower_observed_rmse_cells':int((ratio<1).sum()),'cells':len(ratio),
                             'ratio_min':float(ratio.min()),'ratio_median':float(ratio.median()),
                             'ratio_max':float(ratio.max())}
    noisy=raw[raw.method=='kcore_noisy_cap']
    epsilon=float(summary.epsilon.max())
    empty=summary[(summary.graph=='empty6')&(summary.method=='baseline')&(summary.epsilon==epsilon)]
    tail_diagnostic=None
    if len(empty):
        n=int(empty.n.iloc[0])
        tau=math.exp(epsilon)/math.expm1(epsilon)**2
        tail_diagnostic={'graph':'empty6','epsilon':epsilon,
            'ideal_baseline_sd':math.sqrt(math.comb(n,4)*tau**6),
            'observed_baseline_rmse':float(empty.rmse.iloc[0]),
            'interpretation':'100 trials may miss rare high-weight RR products; not an exact variance estimate'}
    result={'result_type':'nonprivate_synthetic_evaluation','privacy_status':'experimental_unverified',
        **verified,'graph_counts':summary[['graph','n','m','degeneracy','exact_count']].drop_duplicates().to_dict('records'),
        'comparisons_against_baseline':comparisons,
        'negative_estimates':int((raw.estimate<0).sum()),
        'undefined_relative_cells':int(summary.relative_rmse.isna().sum()),
        'noisy_cap_full_fraction':float((noisy.cap==noisy.n-1).mean()),
        'noisy_cap_clipped_trials':int((noisy.clipped_vertices>0).sum()),
        'rmse_at_largest_epsilon':pivot.xs(epsilon,level='epsilon').reset_index().to_dict('records'),
        'tail_diagnostic':tail_diagnostic,
        'input_sha256':{name:sha256(args.results/name) for name in ('config.json','trials.csv','summary.csv','manifest.json')},
        'analysis_script_sha256':sha256(Path(__file__))}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':str(args.output),'cells':verified['cells'],'trials':verified['trials']}))


if __name__=='__main__': main()
