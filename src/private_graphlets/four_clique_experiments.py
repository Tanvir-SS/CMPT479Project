"""NON-PRIVATE public-synthetic phase-06 evaluation, replay and plotting."""

from dataclasses import asdict
from itertools import combinations
import json
import math
from pathlib import Path
import time

import networkx as nx
import numpy as np
import pandas as pd

from private_graphlets.escape import EscapeAdapter, parse_count_four_output
from private_graphlets.experiments import generate_graph, sha256, _provenance
from private_graphlets.four_clique import allocate_budget, simulate_four_cliques
from private_graphlets.four_clique_baseline import simulate_baseline
from private_graphlets.four_clique_exact import count_four_cliques, count_four_cliques_bruteforce, ranks
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import KCoreConfig, nonprivate_kcore_oracle
from private_graphlets.noise import validate_epsilon


def load_config(path: Path) -> dict:
    config=json.loads(path.read_text())
    if config['schema_version']!=1 or not 2<=config['trials']<=500 or type(config['trials']) is not int:
        raise ValueError('phase-06 requires 2..500 trials')
    if type(config['master_seed']) is not int or config['master_seed']<0:
        raise ValueError('master_seed must be a nonnegative integer')
    KCoreConfig(**config['kcore'])
    if not 0<config['beta']<1: raise ValueError('beta must be in (0,1)')
    for name in ('graphs','methods'):
        values=config[name]
        if not values or len({x['id'] for x in values})!=len(values):
            raise ValueError(f'{name} need unique IDs')
        if any(not x['id'].replace('_','').isalnum() for x in values):
            raise ValueError('IDs must be alphanumeric with underscores')
    if not config['epsilons'] or len(set(config['epsilons']))!=len(config['epsilons']):
        raise ValueError('epsilons must be nonempty and unique')
    for eps in config['epsilons']:
        validate_epsilon(eps)
        for method in config['methods']:
            if method['kind']=='oriented':
                budget=allocate_budget(eps,method['ordering'],method['cap_mode'])
                if budget.ordering>1: raise ValueError('k-CoreD epsilon_O exceeds 1')
            elif method['kind']!='baseline': raise ValueError('unknown method kind')
    return config


def experiment_graph(spec: dict) -> SimpleGraph:
    if spec['family']=='book':
        centers=spec['centers']
        if type(centers) is not int or not 1<=centers<=97:
            raise ValueError('book centers must be in 1..97')
        # Centers first, common closing triangle last: stresses shared RR reports.
        leaves=range(centers,centers+3)
        graph=SimpleGraph.from_edges(centers+3,[*combinations(leaves,2),
            *((v,w) for v in range(centers) for w in leaves)])
    else: graph=generate_graph(spec)
    if graph.num_vertices>100: raise ValueError('baseline comparison supports n<=100')
    return graph


def trial_seed(master: int, gi: int, ei: int, mi: int, trial: int) -> int:
    if any(not 0<=v<65536 for v in (gi,ei,mi,trial)):
        raise ValueError('trial coordinates exceed their 16-bit domains')
    return (master<<64)|(gi<<48)|(ei<<32)|(mi<<16)|trial


def execute_trial(graph: SimpleGraph, epsilon: float, method: dict, seed: int, config: dict) -> dict:
    """Exact diagnostics are added ONLY here, never inside a private result."""
    start=time.perf_counter()
    if method['kind']=='baseline':
        result,_=simulate_baseline(graph,epsilon,seed=seed)
        order=tuple(range(graph.num_vertices))
        cap=graph.num_vertices-1
        rounds=0
    else:
        run=simulate_four_cliques(graph,epsilon,ordering=method['ordering'],
            cap_mode=method['cap_mode'],cap=method.get('cap'),seed=seed,beta=config['beta'],
            kcore_config=KCoreConfig(**config['kcore']))
        result=run.result
        order,cap=run.transcript.order,run.transcript.cap
        rounds=0 if run.transcript.ordering is None else len(run.transcript.ordering.promotions)
    seconds=time.perf_counter()-start
    rank=ranks(order)
    outdegrees=[sum(rank[v]<rank[w] for w in row) for v,row in enumerate(graph.adjacency)]
    retained=count_four_cliques(graph,order,cap=cap)
    # An uncapped exact identity check on EVERY realized ordering, not just one seed.
    uncapped=count_four_cliques(graph,order)
    return {'estimate':result.estimate,'retained_count':retained,'uncapped_count':uncapped,
            'cap':cap,'max_out_degree':max(outdegrees,default=0),
            'clipped_vertices':sum(d>cap for d in outdegrees),'ordering_rounds':rounds,
            'ordering_type':result.ordering_type,'cap_mode':result.cap_mode,
            'epsilon_O':result.budget.ordering,'epsilon_D':result.budget.cap,
            'epsilon_R':result.budget.rr,'epsilon_C':result.budget.count,
            'local_noise_scale':result.local_noise_scale,'runtime_seconds':seconds,
            'privacy_status':result.to_dict()['privacy_status']}


def aggregate(raw: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for (graph,epsilon,method),cell in raw.groupby(['graph','epsilon','method'],sort=False):
        truth=int(cell.exact_count.iloc[0])
        values=cell.estimate.to_numpy(dtype=float)
        errors=values-truth
        retained=cell.retained_count.to_numpy(dtype=float)
        variance=float(values.var(ddof=1))
        rmse=math.sqrt(float(np.mean(errors**2)))
        rows.append({'graph':graph,'epsilon':epsilon,'method':method,
            'n':int(cell.n.iloc[0]),'m':int(cell.m.iloc[0]),'degeneracy':int(cell.degeneracy.iloc[0]),
            'exact_count':truth,'trials':len(values),'mean_estimate':float(values.mean()),
            'bias':float(errors.mean()),'variance':variance,'standard_deviation':math.sqrt(variance),
            'mae':float(np.mean(np.abs(errors))),'rmse':rmse,
            'relative_rmse':rmse/truth if truth else math.nan,
            'mean_retained_count':float(retained.mean()),'retained_target_bias':float(retained.mean()-truth),
            'mean_error_to_retained':float(np.mean(values-retained)),
            'rmse_to_retained':float(np.sqrt(np.mean((values-retained)**2))),
            'empirical_mean_se':math.sqrt(variance/len(values)),
            'cap_min':int(cell.cap.min()),'cap_max':int(cell.cap.max()),'cap_mean':float(cell.cap.mean()),
            'max_out_degree_mean':float(cell.max_out_degree.mean()),
            'clipped_trial_fraction':float(np.mean(cell.clipped_vertices>0)),
            'negative_trials':int(np.count_nonzero(values<0)),
            'runtime_seconds':float(cell.runtime_seconds.sum()),
            **{key:cell[key].iloc[0] for key in ['ordering_type','cap_mode','epsilon_O','epsilon_D','epsilon_R','epsilon_C','privacy_status']}})
    return pd.DataFrame(rows)


def run_experiment(config_path: Path, output: Path, adapter: EscapeAdapter) -> dict:
    config=load_config(config_path)
    output.mkdir(parents=True,exist_ok=False)
    (output/'graphs').mkdir()
    (output/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    rows=[]
    references=[]
    start=time.perf_counter()
    try:
        for gi,spec in enumerate(config['graphs']):
            graph=experiment_graph(spec)
            run=adapter.run(graph)
            truth=count_four_cliques_bruteforce(graph)
            observed=run.counts.connected_four['4-clique']
            oracle=nonprivate_kcore_oracle(graph)
            if not truth==observed==count_four_cliques(graph)==count_four_cliques(graph,oracle.order):
                raise AssertionError('independent exact counts disagree')
            n=graph.num_vertices
            nxgraph=nx.Graph()
            nxgraph.add_nodes_from(range(n))
            nxgraph.add_edges_from((v,w) for v,row in enumerate(graph.adjacency) for w in row if v<w)
            degeneracy=max(nx.core_number(nxgraph).values(),default=0)
            (output/'graphs'/f"{spec['id']}.edges").write_text(run.input_text)
            references.append({'graph':spec['id'],'n':n,'m':graph.num_edges,'degeneracy':degeneracy,
                'escape_count':observed,'bruteforce_count':truth,'oriented_count':count_four_cliques(graph),
                'noiseless_kcore_oracle_count':count_four_cliques(graph,oracle.order),
                'input':run.input_text,'output':run.output_text,'stdout':run.stdout,'stderr':run.stderr})
            for ei,epsilon in enumerate(config['epsilons']):
                for mi,method in enumerate(config['methods']):
                    for trial in range(config['trials']):
                        seed=trial_seed(config['master_seed'],gi,ei,mi,trial)
                        row=execute_trial(graph,epsilon,method,seed,config)
                        if row['uncapped_count']!=truth: raise AssertionError('realized order count mismatch')
                        rows.append({'graph':spec['id'],'family':spec['family'],'graph_index':gi,
                            'epsilon':epsilon,'epsilon_index':ei,'method':method['id'],'method_index':mi,
                            'trial':trial,'seed':str(seed),'n':n,'m':graph.num_edges,'degeneracy':degeneracy,
                            'exact_count':truth,**row})
        pd.DataFrame(rows).to_csv(output/'trials.csv',index=False,float_format='%.17g')
        # Aggregate the actual saved CSV, which is also the sole plot input.
        raw=pd.read_csv(output/'trials.csv',dtype={'seed':str},float_precision='round_trip')
        aggregate(raw).to_csv(output/'summary.csv',index=False,float_format='%.17g')
        (output/'escape_reference.json').write_text(json.dumps(references,indent=2)+'\n')
        provenance=_provenance()
        project=Path(__file__).resolve().parents[2]
        provenance['source_sha256']['scripts/run_four_clique_experiments.py']=sha256(project/'scripts/run_four_clique_experiments.py')
        manifest={'status':'complete','result_type':'nonprivate_synthetic_evaluation',
            'privacy_status':'experimental_unverified','graphs':len(references),
            'cells':len(config['graphs'])*len(config['epsilons'])*len(config['methods']),
            'trials':len(rows),'pipeline_seconds':time.perf_counter()-start,
            'escape_executable_sha256':sha256(adapter.executable),
            'escape_build':json.loads((adapter.executable.parent/'build.json').read_text())
                if (adapter.executable.parent/'build.json').exists() else None,
            'provenance':provenance,'files_sha256':{str(p.relative_to(output)):sha256(p)
                for p in sorted(output.rglob('*')) if p.is_file()}}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        return manifest
    except Exception as exc:
        (output/'failure.json').write_text(json.dumps({'status':'failed','error':str(exc)}))
        raise


def verify_results(output: Path, *, replay: bool=False) -> dict:
    manifest=json.loads((output/'manifest.json').read_text())
    if manifest['status']!='complete': raise ValueError('incomplete run')
    for name,digest in manifest['files_sha256'].items():
        if sha256(output/name)!=digest: raise ValueError(f'hash mismatch: {name}')
    config=load_config(output/'config.json')
    raw=pd.read_csv(output/'trials.csv',dtype={'seed':str},float_precision='round_trip')
    summary=pd.read_csv(output/'summary.csv',float_precision='round_trip')
    expected_rows=len(config['graphs'])*len(config['epsilons'])*len(config['methods'])*config['trials']
    if len(raw)!=expected_rows or raw.seed.duplicated().any(): raise ValueError('incorrect or duplicated trials')
    # CSV does not preserve dtype: a mean of exactly 3 may be read as int64.
    # Compare all values/columns, permitting only that representation difference.
    pd.testing.assert_frame_equal(summary,aggregate(raw),check_exact=False,
                                  check_dtype=False,rtol=1e-13,atol=0)
    references=json.loads((output/'escape_reference.json').read_text())
    for row in references:
        observed=parse_count_four_output(row['output'],num_vertices=max(4,row['n']),num_edges=row['m']).connected_four['4-clique']
        if observed!=row['escape_count'] or observed!=row['bruteforce_count']:
            raise ValueError('saved ESCAPE count mismatch')
    if replay:
        graphs=[experiment_graph(spec) for spec in config['graphs']]
        for row in raw.to_dict('records'):
            seed=trial_seed(config['master_seed'],row['graph_index'],row['epsilon_index'],row['method_index'],row['trial'])
            if int(row['seed'])!=seed: raise ValueError('seed coordinate mismatch')
            actual=execute_trial(graphs[row['graph_index']],row['epsilon'],config['methods'][row['method_index']],seed,config)
            for key,value in actual.items():
                if key!='runtime_seconds' and value!=row[key]:
                    raise ValueError(f'replay mismatch: {row["graph"]}/{row["method"]}/{row["trial"]}/{key}')
    return {'status':'verified','graphs':len(references),'cells':len(summary),'trials':len(raw),'replayed':replay}


def plot_results(results: Path, output: Path) -> dict:
    verify_results(results)
    import matplotlib
    matplotlib.use('Agg',force=True)
    from matplotlib import pyplot as plt
    raw=pd.read_csv(results/'trials.csv',dtype={'seed':str},float_precision='round_trip')
    summary=pd.read_csv(results/'summary.csv',float_precision='round_trip')
    config=load_config(results/'config.json')
    output.mkdir(parents=True,exist_ok=True)
    files=[]
    def save(fig,name):
        fig.tight_layout()
        for ext in ('png','pdf'):
            path=output/f'{name}.{ext}'
            metadata={'Software':'private-graphlets'} if ext=='png' else {'CreationDate':None,'ModDate':None}
            fig.savefig(path,dpi=150,metadata=metadata)
            files.append(path)
        plt.close(fig)
    names=list(summary.graph.unique())
    fig,axes=plt.subplots(math.ceil(len(names)/2),2,figsize=(12,3.4*math.ceil(len(names)/2)),squeeze=False)
    for ax,name in zip(axes.flat,names):
        for method,group in summary[summary.graph==name].groupby('method',sort=False):
            ax.plot(group.epsilon,group.rmse,marker='o',label=method)
        ax.set(title=f'{name}: error against original K4 count',xlabel='Total edge epsilon',ylabel='RMSE')
        ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=7)
    for ax in list(axes.flat)[len(names):]: ax.set_visible(False)
    save(fig,'rmse_vs_epsilon')
    fig,ax=plt.subplots(figsize=(9,6))
    for method,group in summary[summary.epsilon==max(config['epsilons'])].groupby('method',sort=False):
        ax.scatter(group.exact_count,group.mean_estimate,label=method)
    limit=summary.exact_count.max()
    ax.plot([0,limit],[0,limit],'k--',label='Exact mean target')
    ax.set(xlabel='Exact original K4 count',ylabel='Mean estimate (symmetric log)',
           title=f'Mean estimates at epsilon={max(config["epsilons"])}; {config["trials"]} trials per setting')
    ax.set_yscale('symlog'); ax.legend(fontsize=8); ax.grid(alpha=.25)
    save(fig,'mean_vs_exact')
    representative=config['representative_graph']
    selected=raw[(raw.graph==representative)&(raw.epsilon==max(config['epsilons']))]
    fig,axes=plt.subplots(len(config['methods']),1,figsize=(10,2.5*len(config['methods'])),squeeze=False)
    for ax,(method,group) in zip(axes.flat,selected.groupby('method',sort=False)):
        ax.hist(group.estimate,bins=25,alpha=.75)
        ax.axvline(group.exact_count.iloc[0],color='black',linestyle='--',label='Original exact count')
        ax.axvline(group.retained_count.mean(),color='red',linestyle=':',label='Mean retained target')
        ax.set(title=f'{representative} / {method}; epsilon={max(config["epsilons"])}',xlabel='Estimate (all values retained)',ylabel='Trials')
        ax.legend(fontsize=8)
    save(fig,'estimate_distributions')
    fig,ax=plt.subplots(figsize=(10,5))
    subset=summary[(summary.epsilon==max(config['epsilons'])) & (summary.exact_count>0)]
    for method,group in subset.groupby('method',sort=False):
        ax.scatter(group.degeneracy,group.mean_retained_count/group.exact_count,label=method)
    ax.set(title='Retained-clique target at the largest tested epsilon',xlabel='Exact degeneracy (synthetic evaluation)',ylabel='Mean retained / original count')
    ax.legend(fontsize=8); ax.grid(alpha=.25)
    save(fig,'retained_targets')
    manifest={'input_sha256':{name:sha256(results/name) for name in ('trials.csv','summary.csv','config.json')},
              'files_sha256':{p.name:sha256(p) for p in files}}
    (output/'plot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
