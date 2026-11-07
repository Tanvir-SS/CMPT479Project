"""NON-PRIVATE equal-nominal-budget P4 comparison. Private mechanisms unchanged."""
from dataclasses import asdict
import json
import math
from pathlib import Path
import resource
import shutil
from statistics import NormalDist
import sys
import tempfile
import time

import numpy as np
import pandas as pd

from private_graphlets import four_path_experiments as pilot
from private_graphlets import four_path_study as study
from private_graphlets.experiments import sha256, _provenance
from private_graphlets.four_clique_experiments import trial_seed
from private_graphlets.four_path import FourPathBudget
from private_graphlets.four_path_baseline_2025 import Baseline2025Budget, simulate_four_paths_baseline_2025
from private_graphlets.four_path_exact import count_four_paths
from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.randomized_response import rr_parameters
from private_graphlets.escape import parse_count_four_output


def baseline_variance(graph, epsilon):
    """Exact ideal centered-polynomial variance; NON-PRIVATE, n<=100.

    Integer coefficients, float64 final h polynomial. See comparison report
    for the three coefficient families. O(n^4) time, O(n^2) working memory.
    """
    if not isinstance(graph, SimpleGraph) or graph.num_vertices > 100:
        raise ValueError('variance requires SimpleGraph with n<=100')
    h = rr_parameters(epsilon).variance
    n = graph.num_vertices
    if n < 4:
        return 0.
    a = np.zeros((n,n), dtype=np.int64)
    for u,row in enumerate(graph.adjacency):
        for v in row: a[u,v] = 1
    d = a.sum(axis=1); s = a @ (d-1); common = a @ a
    first = 0
    for u in range(n):
        for v in range(u+1,n):
            x = int(a[u,v])
            c = (int(d[u])-x)*(int(d[v])-x)+int(s[u]+s[v])-x*int(d[u]+d[v]-2)-3*int(common[u,v])
            first += c*c
    second = 0
    for v in range(n):
        ends = np.array([u for u in range(n) if u != v])
        ii,jj = np.triu_indices(n-1,1); u,w = ends[ii],ends[jj]
        c = d[u]+d[w]-a[u,v]-a[w,v]-2*a[u,w]
        second += int(c @ c)
    # Each quadruple has three disjoint edge-pair matchings. Its coefficient is
    # the sum of the four possible bridge edges (the complement of the matching).
    for u in range(n):
        for v in range(u+1,n):
            ii,jj = np.triu_indices(n-v-1,1); w,z = ii+v+1,jj+v+1
            for c in (a[u,w]+a[u,z]+a[v,w]+a[v,z],
                      a[u,v]+a[u,z]+a[w,v]+a[w,z],
                      a[u,v]+a[u,w]+a[z,v]+a[z,w]):
                second += int(c @ c)
    third = 12*math.comb(n,4)
    value = math.fsum((first*h, second*h*h, third*h*h*h))
    if not math.isfinite(value): raise FloatingPointError('nonfinite ideal variance')
    return value


def validate_config(c):
    keys = {'schema_version','experiment_id','master_seed','trials','prediction_trials',
            'kcore','graphs','cells','historical_output','historical_manifest_sha256',
            'alpha','uncertainty_multiplier','max_relative_se'}
    if set(c) != keys or c['schema_version'] != 17:
        raise ValueError('invalid comparison schema')
    study._common(c)
    if c['alpha'] != .05: raise ValueError('predeclared alpha must be .05')
    if not 1 <= len(c['cells']) <= 26 or not 1 <= len(c['graphs']) <= 12:
        raise ValueError('comparison size limit')
    ids = [study._name(g['id']) for g in c['graphs']]
    if len(ids) != len(set(ids)): raise ValueError('duplicate graph')
    for g in c['graphs']: study.study_graph(g)
    names=[]
    for cell in c['cells']:
        if set(cell) != {'id','experiment','graph','allocation','budget','beta','baseline_epsilon'}:
            raise ValueError('invalid comparison cell')
        names.append(study._name(cell['id'])); study._name(cell['allocation'])
        if cell['experiment'] not in ('A','B','C') or cell['graph'] not in ids:
            raise ValueError('invalid graph/experiment')
        b=FourPathBudget(**cell['budget']); Baseline2025Budget(cell['baseline_epsilon'])
        if not math.isclose(b.total,cell['baseline_epsilon'],rel_tol=1e-14,abs_tol=0):
            raise ValueError('unequal total epsilon')
        study._beta(cell['beta'])
    if len(names)!=len(set(names)): raise ValueError('duplicate cell')
    return c


def load_config(path):
    return validate_config(json.loads(Path(path).read_text()))


def conditions(c):
    return list(dict.fromkeys((x['graph'],float(x['baseline_epsilon'])) for x in c['cells']))


def candidate_config(c,i):
    result=study.cell_config(c,i)
    result['master_seed']=trial_seed(c['master_seed'],i,17,0,0)
    return result


def baseline_seed(c,i,t):
    return trial_seed(c['master_seed'],i,18,0,t)


def metrics(values, truth):
    values=np.asarray(values,dtype=float)
    if values.ndim!=1 or len(values)<2 or not np.isfinite(values).all():
        raise ValueError('need >=2 finite estimates')
    with np.errstate(over='raise',invalid='raise'):
        errors=values-truth; sq=errors**2
        mse=float(sq.mean()); se=float(sq.std(ddof=1)/math.sqrt(len(sq)))
        rmse=math.sqrt(mse)
        return dict(trials=len(values),mean=float(values.mean()),bias=float(errors.mean()),
                    variance=float(values.var(ddof=1)),mse=mse,rmse=rmse,se_mse=se,
                    rmse_se=se/(2*rmse) if rmse else 0.,relative_rmse=rmse/truth if truth else float('nan'))


def difference(a,b,count=26):
    delta=a['mse']-b['mse']; se=math.hypot(a['se_mse'],b['se_mse'])
    z=NormalDist().inv_cdf(1-.05/(2*count))
    low,high=delta-1.959963984540054*se,delta+1.959963984540054*se
    lo,hi=delta-z*se,delta+z*se
    return dict(mse_difference=delta,se_difference=se,ci95_low=low,ci95_high=high,
                simultaneous_low=lo,simultaneous_high=hi,
                mse_ratio=a['mse']/b['mse'] if b['mse']>0 else float('nan'),
                rmse_ratio=a['rmse']/b['rmse'] if b['rmse']>0 else float('nan'),
                observed_lower='candidate' if delta<0 else 'baseline' if delta>0 else 'tie',
                pointwise_excludes_zero=low>0 or high<0,
                adjusted_conclusion='baseline' if lo>0 else 'candidate' if hi<0 else 'inconclusive')


def historical_graphs(c):
    """Fail closed on missing/corrupt historical data; no silent regeneration."""
    root=Path(c['historical_output']); manifest=root/'manifest.json'
    if sha256(manifest)!=c['historical_manifest_sha256']: raise ValueError('historical manifest changed')
    m=json.loads(manifest.read_text())
    if m['status']!='complete' or study._inventory(root)!=m['files_sha256']:
        raise ValueError('historical inventory/hash mismatch')
    old=json.loads((root/'config.json').read_text()); graphs={}; evidence={}
    for spec in c['graphs']:
        matches=[x for x in old['cells'] if x['graph']==spec['id']]
        if spec not in old['graphs'] or not matches: raise ValueError('historical graph specification mismatch')
        p=root/'cells'/matches[0]['id']/'graphs'/f"{spec['id']}.edges"
        graph=load_edge_list(p)
        if graph!=study.study_graph(spec): raise ValueError('historical graph identity mismatch')
        info=json.loads((p.parent.parent/'graph_evaluation.json').read_text())[spec['id']]
        if count_four_paths(graph)!=info['exact_four_paths']: raise ValueError('historical truth mismatch')
        graphs[spec['id']]=graph
        evidence[spec['id']]={'source_path':str(p),'sha256':sha256(p),**info}
    # Exact budgets and beta must be the previously declared ones.
    for x in c['cells']:
        original={k:v for k,v in x.items() if k!='baseline_epsilon'}
        if original not in old['cells']: raise ValueError('changed historical comparison cell')
    return graphs,evidence


def summary(c,out):
    rows=[]; cs=conditions(c)
    for i,cell in enumerate(c['cells']):
        bid=cs.index((cell['graph'],float(cell['baseline_epsilon'])))
        a=pilot._read_csv(out/'candidate'/cell['id']/'evaluation_trials.csv')
        b=pilot._read_csv(out/'baseline'/f'b{bid:02d}'/'trials.csv')
        info=json.loads((out/'graph_manifest.json').read_text())[cell['graph']]
        am=metrics(a.estimate,info['exact_four_paths']); bm=metrics(b.estimate,info['exact_four_paths'])
        pred=pd.read_csv(out/'candidate'/cell['id']/'summary.csv').iloc[0]
        theory=json.loads((out/'baseline'/f'b{bid:02d}'/'theory.json').read_text())
        rows.append(dict(cell=cell['id'],experiment=cell['experiment'],graph=cell['graph'],
            allocation=cell['allocation'],epsilon=cell['baseline_epsilon'],baseline_condition=f'b{bid:02d}',
            n=info['n'],m=info['m'],truth=info['exact_four_paths'],
            **{'new_'+k:v for k,v in am.items()},**{'baseline_'+k:v for k,v in bm.items()},
            **difference(am,bm,len(c['cells'])),
            new_predicted_mse=pred.predicted_mse,new_prediction_se=pred.prediction_se,
            baseline_ideal_mse=theory['mse'],baseline_theory_seconds=theory['seconds'],
            new_seconds=float(a.mechanism_seconds.mean()),baseline_seconds=float(b.seconds.mean()),
            new_mean_missed=float(a.missed_triangles.mean()),
            new_truncation_frequency=float((a.missed_triangles>0).mean())))
    return pd.DataFrame(rows)


def run_comparison(config_path,out,adapter):
    c=load_config(config_path)
    if out.exists(): raise FileExistsError(out)
    graphs,evidence=historical_graphs(c)
    out.mkdir(parents=True); start=time.perf_counter()
    try:
        pilot._write_json(out/'config.json',c); pilot._write_json(out/'graph_manifest.json',evidence)
        (out/'graphs').mkdir(); (out/'escape').mkdir()
        for name,g in graphs.items():
            (out/'graphs'/f'{name}.edges').write_text(pilot._graph_text(g))
            native=adapter.run(g)
            if native.counts.connected_four['3-path']!=count_four_paths(g): raise ValueError('ESCAPE P4 mismatch')
            pilot._write_json(out/'escape'/f'{name}.json',asdict(native))
        pilot._write_json(out/'escape_provenance.json',{'binary_sha256':sha256(adapter.executable),
            'build':json.loads((adapter.executable.parent/'build.json').read_text())})
        for i,cell in enumerate(c['cells']):
            pilot._run_experiment(candidate_config(c,i),out/'candidate'/cell['id'],lambda spec:graphs[spec['id']])
            print(f'candidate {i+1}/{len(c["cells"])} {cell["id"]}',flush=True)
        for i,(name,epsilon) in enumerate(conditions(c)):
            directory=out/'baseline'/f'b{i:02d}'; directory.mkdir(parents=True)
            rows=[]; g=graphs[name]; t0=time.perf_counter(); variance=baseline_variance(g,epsilon)
            pilot._write_json(directory/'theory.json',{'mse':variance,'seconds':time.perf_counter()-t0,'scope':'nonprivate_exact_ideal_variance'})
            with (directory/'mechanism_outputs.jsonl').open('w') as stream:
                for t in range(c['trials']):
                    seed=baseline_seed(c,i,t); t0=time.perf_counter()
                    run=simulate_four_paths_baseline_2025(g,budget=Baseline2025Budget(epsilon),seed=seed)
                    elapsed=time.perf_counter()-t0
                    stream.write(json.dumps({'result':run.result.to_dict(),'transcript':asdict(run.transcript)},allow_nan=False)+'\n')
                    rows.append(dict(graph=name,epsilon=epsilon,trial=t,seed=str(seed),estimate=run.result.estimate,seconds=elapsed))
            pd.DataFrame(rows).to_csv(directory/'trials.csv',index=False,float_format='%.17g')
            print(f'baseline {i+1}/{len(conditions(c))} {name} epsilon={epsilon}',flush=True)
        summary(c,out).to_csv(out/'comparison_summary.csv',index=False,float_format='%.17g')
        historical=pd.read_csv(Path(c['historical_output'])/'summary.csv')
        historical[historical.experiment=='D2'].to_csv(out/'historical_truncation.csv',index=False,float_format='%.17g')
        # Preserve diagnostics as historical observations, not fresh trials.
        (out/'historical_fixed_controls.csv').write_bytes((Path(c['historical_output'])/'fixed_controls.csv').read_bytes())
        plot_summary(pd.read_csv(out/'comparison_summary.csv'),out/'plots')
        manifest=dict(status='complete',result_type='nonprivate_synthetic_comparison',
            candidate_cells=len(c['cells']),baseline_conditions=len(conditions(c)),
            candidate_trials=len(c['cells'])*c['trials'],baseline_trials=len(conditions(c))*c['trials'],
            prediction_histories=len(c['cells'])*c['prediction_trials'],pipeline_seconds=time.perf_counter()-start,
            process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
            provenance=_provenance(),files_sha256=study._inventory(out))
        manifest['provenance']['source_sha256']['scripts/run_four_path_comparison.py']=sha256(pilot.PROJECT/'scripts/run_four_path_comparison.py')
        manifest['artifact_bytes']=sum((out/p).stat().st_size for p in manifest['files_sha256'])
        pilot._write_json(out/'manifest.json',manifest)
        return {k:v for k,v in manifest.items() if k not in ('files_sha256','provenance')}
    except Exception as exc:
        pilot._write_json(out/'failure.json',{'status':'failed','error':str(exc)})
        raise


def verify_comparison(out,replay=False):
    m=json.loads((out/'manifest.json').read_text())
    if m['status']!='complete' or (out/'failure.json').exists(): raise ValueError('incomplete comparison')
    if study._inventory(out)!=m['files_sha256']: raise ValueError('comparison inventory/hash mismatch')
    c=load_config(out/'config.json'); graphs,info=historical_graphs(c)
    if info!=json.loads((out/'graph_manifest.json').read_text()): raise ValueError('graph manifest mismatch')
    all_seeds=set()
    for name,g in graphs.items():
        if load_edge_list(out/'graphs'/f'{name}.edges')!=g: raise ValueError('graph mismatch')
        native=json.loads((out/'escape'/f'{name}.json').read_text())
        counts=parse_count_four_output(native['output_text'],num_vertices=g.num_vertices,num_edges=g.num_edges)
        if counts.connected_four['3-path']!=count_four_paths(g): raise ValueError('native mismatch')
    for i,cell in enumerate(c['cells']):
        directory=out/'candidate'/cell['id']
        if study._load_cell(directory/'config.json')!=candidate_config(c,i): raise ValueError('candidate config mismatch')
        pilot._verify_results(directory,study._load_cell,lambda spec:graphs[spec['id']],replay=replay)
        for file in ('evaluation_trials.csv','prediction_trials.csv'):
            seeds=list(pilot._read_csv(directory/file).seed)
            if len(set(seeds))!=len(seeds) or all_seeds.intersection(seeds): raise ValueError('seed collision')
            all_seeds.update(seeds)
    for i,(name,epsilon) in enumerate(conditions(c)):
        directory=out/'baseline'/f'b{i:02d}'; rows=pilot._read_csv(directory/'trials.csv')
        expected=[(name,epsilon,t,str(baseline_seed(c,i,t))) for t in range(c['trials'])]
        if list(rows[['graph','epsilon','trial','seed']].itertuples(index=False,name=None))!=expected: raise ValueError('baseline coordinates mismatch')
        if all_seeds.intersection(rows.seed): raise ValueError('seed collision')
        all_seeds.update(rows.seed)
        if baseline_variance(graphs[name],epsilon)!=json.loads((directory/'theory.json').read_text())['mse']: raise ValueError('variance mismatch')
        with (directory/'mechanism_outputs.jsonl').open() as stream:
            for row in rows.to_dict('records'):
                release=json.loads(stream.readline())
                if release['result']['estimate']!=row['estimate']: raise ValueError('estimate mismatch')
                if replay:
                    run=simulate_four_paths_baseline_2025(graphs[name],budget=Baseline2025Budget(epsilon),seed=int(row['seed']))
                    actual={'result':run.result.to_dict(),'transcript':asdict(run.transcript)}
                    if json.loads(json.dumps(actual))!=release: raise ValueError('baseline replay mismatch')
            if stream.readline(): raise ValueError('extra baseline release')
    actual=pd.read_csv(out/'comparison_summary.csv',float_precision='round_trip')
    pd.testing.assert_frame_equal(actual,summary(c,out),check_dtype=False,rtol=1e-12,atol=1e-12)
    return dict(status='verified',replayed=replay,candidate_trials=m['candidate_trials'],baseline_trials=m['baseline_trials'],prediction_histories=m['prediction_histories'],distinct_seeds=len(all_seeds))


def plot_summary(frame,out):
    import matplotlib
    matplotlib.use('Agg',force=True)
    from matplotlib import pyplot as plt
    out.mkdir(parents=True,exist_ok=False)
    def save(fig,name):
        fig.tight_layout()
        for ext in ('png','pdf'):
            fig.savefig(out/f'{name}.{ext}',dpi=160,metadata={'CreationDate':None,'ModDate':None} if ext=='pdf' else None)
        plt.close(fig)
    a=frame[frame.experiment=='A'].copy(); a['series']=a.graph.str.replace(r'_n[0-9]+$','',regex=True)
    for metric,name,ylabel in [('rmse','rmse_vs_size','RMSE (P4 copies)'),('relative_rmse','relative_rmse_vs_size','Relative RMSE'),('seconds','runtime_vs_size','Mean simulator seconds')]:
        fig,axes=plt.subplots(2,2,figsize=(10,7))
        for ax,(family,g) in zip(axes.flat,a.groupby('series')):
            g=g.sort_values('n')
            for prefix,label in [('new','Candidate'),('baseline','2025 baseline')]:
                err=g[prefix+'_rmse_se'] if metric=='rmse' else g[prefix+'_rmse_se']/g.truth.replace(0,np.nan) if metric=='relative_rmse' else None
                ax.errorbar(g.n,g[prefix+'_'+metric],yerr=err,marker='o',capsize=3,label=label)
            ax.set(title=family,xlabel='Vertices n',ylabel=ylabel,yscale='log'); ax.legend(fontsize=8); ax.grid(alpha=.2)
        fig.suptitle('Total epsilon = 6.5; centralized simulator means' if metric=='seconds'
                     else 'Total epsilon = 6.5; error bars +/-1 SE (delta RMSE)')
        save(fig,name)
    for exp,name,title in [('B','mse_vs_epsilon','Fixed allocation fractions; total epsilon on x-axis'),('C','allocation_sensitivity','Total epsilon = 4; same baseline series reused')]:
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        for ax,(graph,g) in zip(axes,frame[frame.experiment==exp].groupby('graph')):
            g=g.sort_values('epsilon') if exp=='B' else g
            x=g.epsilon if exp=='B' else np.arange(len(g))
            for prefix,label in [('new','Candidate'),('baseline','2025 baseline')]:
                ax.errorbar(x,g[prefix+'_mse'],yerr=g[prefix+'_se_mse'],marker='o',capsize=3,label=label)
            if exp=='C': ax.set_xticks(x,g.allocation,rotation=15)
            ax.set(title=graph,ylabel='MSE (P4 copies squared)',xlabel='Total epsilon' if exp=='B' else 'Allocation',yscale='log'); ax.legend(fontsize=8); ax.grid(alpha=.2)
        fig.suptitle(title+'; +/-1 SE'); save(fig,name)
    fig,ax=plt.subplots(figsize=(8,4))
    for family,g in a.groupby('series'):
        g=g.sort_values('n')
        se=g.mse_ratio*np.sqrt((g.new_se_mse/g.new_mse)**2+(g.baseline_se_mse/g.baseline_mse)**2)
        ax.errorbar(g.n,g.mse_ratio,yerr=se,marker='o',capsize=3,label=family)
    ax.axhline(1,color='black',ls='--'); ax.set(xlabel='Vertices n',ylabel='Candidate MSE / baseline MSE',yscale='log',title='Total epsilon = 6.5; ratio bars +/-1 delta SE'); ax.legend(); save(fig,'mse_ratio_vs_size')
    fig,ax=plt.subplots(figsize=(11,8)); y=np.arange(len(frame))
    # Standardized difference intervals preserve sign, avoiding unreadable raw scales.
    ax.errorbar(frame.mse_difference/frame.se_difference,y,xerr=1.959963984540054,fmt='o',capsize=2)
    z=NormalDist().inv_cdf(1-.05/(2*len(frame)))
    ax.axvline(0,color='black'); ax.axvline(z,ls='--',color='grey'); ax.axvline(-z,ls='--',color='grey')
    ax.set_yticks(y,[f'{r.cell} (eps={r.epsilon:g})' for r in frame.itertuples()],fontsize=7)
    ax.set(xlabel='(Candidate MSE - baseline MSE) / SE difference',title='Positive favors baseline; bars pointwise 95%; dashed Bonferroni thresholds')
    save(fig,'comparison_summary')


def replot_comparison(out):
    """Regenerate figures only; retain original run provenance and audit revision."""
    manifest=json.loads((out/'manifest.json').read_text())
    if manifest['status']!='complete' or study._inventory(out)!=manifest['files_sha256']:
        raise ValueError('cannot replot incomplete/corrupt comparison')
    revision={'prior_manifest_sha256':sha256(out/'manifest.json'),
              'plot_source_sha256':sha256(Path(__file__)),
              'operation':'regenerate figures only; trial data unchanged'}
    with tempfile.TemporaryDirectory(prefix='p4-comparison-plots-') as temporary:
        generated=Path(temporary)/'plots'
        plot_summary(pd.read_csv(out/'comparison_summary.csv'),generated)
        for p in generated.iterdir(): shutil.copyfile(p,out/'plots'/p.name)
    manifest.setdefault('postprocessing',[]).append(revision)
    manifest['files_sha256']=study._inventory(out)
    manifest['artifact_bytes']=sum((out/p).stat().st_size for p in manifest['files_sha256'])
    pilot._write_json(out/'manifest.json',manifest)
    return {'status':'replotted','trial_data_changed':False}
