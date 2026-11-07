"""Read completed Phase 5B summaries and emit non-private report tables."""
import json
import math
from pathlib import Path

import pandas as pd


def table(frame,columns):
    def fmt(x):
        if isinstance(x,float): return f'{x:.6g}'
        return str(x)
    return '\n'.join(['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|',
                     *['| '+' | '.join(fmt(x) for x in row)+' |' for row in frame[columns].itertuples(index=False,name=None)]])


def main():
    root=Path('experiments/results/four_path_phase17_comparison')
    s=pd.read_csv(root/'comparison_summary.csv',float_precision='round_trip')
    if len(s)!=26:raise ValueError('expected complete 26-cell study')
    baseline=s.drop_duplicates('baseline_condition')
    newz=(s.new_mse-s.new_predicted_mse)/(s.new_se_mse**2+s.new_prediction_se**2)**.5
    basez=(baseline.baseline_mse-baseline.baseline_ideal_mse)/baseline.baseline_se_mse
    facts=dict(observed_lower=s.observed_lower.value_counts().to_dict(),
        adjusted_conclusion=s.adjusted_conclusion.value_counts().to_dict(),
        ratio_min=float(s.mse_ratio.min()),ratio_max=float(s.mse_ratio.max()),
        max_candidate_prediction_z=float(newz.abs().max()),
        max_baseline_prediction_z=float(basez.abs().max()),
        max_full_truncation_frequency=float(s.new_truncation_frequency.max()),
        candidate_seconds=float((s.new_seconds*s.new_trials).sum()),
        baseline_seconds=float((baseline.baseline_seconds*baseline.baseline_trials).sum()),
        baseline_analytical_seconds=float(baseline.baseline_theory_seconds.sum()),
        bonferroni_z=__import__('statistics').NormalDist().inv_cdf(1-.05/52),
        runtime_ratio_min=float((s.baseline_seconds/s.new_seconds).min()),
        runtime_ratio_max=float((s.baseline_seconds/s.new_seconds).max()))
    allocation=[]
    for graph,g in s[s.experiment=='C'].groupby('graph'):
        best=g.loc[g.new_mse.idxmin()]
        for r in g.itertuples():
            if r.cell==best.cell:continue
            diff=float(best.new_mse-r.new_mse)
            se=math.hypot(best.new_se_mse,r.new_se_mse)
            allocation.append(dict(graph=graph,observed_best=best.allocation,other=r.allocation,
                difference=diff,se=se,z=diff/se,scope='exploratory_selected_minimum_not_independent_confirmation'))
    facts['allocation_contrasts']=allocation
    out=Path('build/phase17/analysis.json')
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(facts,indent=2)+'\n')
    sections=[('All cells: empirical error and exact target',['cell','epsilon','truth','new_mse','baseline_mse','new_rmse','baseline_rmse','mse_ratio']),
              ('Uncertainty and directional interpretation',['cell','mse_difference','se_difference','ci95_low','ci95_high','simultaneous_low','simultaneous_high','adjusted_conclusion']),
              ('Bias, variance and relative error',['cell','new_mean','baseline_mean','new_bias','baseline_bias','new_variance','baseline_variance','new_relative_rmse','baseline_relative_rmse']),
              ('Analytical predictions and centralized runtime',['cell','new_predicted_mse','new_prediction_se','baseline_ideal_mse','new_seconds','baseline_seconds'])]
    text='\n\n'.join('### '+title+'\n\n'+table(s,cols) for title,cols in sections)+'\n'
    Path('build/phase17/report-tables.md').write_text(text)
    print(json.dumps(facts,indent=2))


if __name__=='__main__':main()
