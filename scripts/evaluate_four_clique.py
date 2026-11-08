"""Independent, non-private evaluation of the existing K4 kcore/noisy-cap simulator.

Six pinned datasets, equal O/D/R/C quarters, 200 trials/cell. SQLite commits each
observation before proceeding; CSVs are exported per completed cell and on stop.
No baseline, exact enumeration, prediction experiment, bootstrap or plotting.
"""
import argparse
from datetime import datetime,timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import time
import fcntl

import numpy as np
import pandas as pd
from private_graphlets.escape import parse_count_four_output
from private_graphlets.four_clique import CliqueBudget,simulate_four_cliques
from private_graphlets.graph_datasets import PROJECT,digest,json_bytes,load_prepared_graph
from private_graphlets.kcore import KCoreConfig

EXPECTED={'karate':11,'dolphins':27,'les_miserables':639,'brightkite_50':18,'ba_n100':18198,'sbm_n100':99}
DEFAULT_CONFIG=PROJECT/'experiments/configs/four_clique_six_datasets.json'
MECHANISMS=['four_clique.py','kcore.py','randomized_response.py','noise.py','four_clique_exact.py','graph.py']


def atomic_json(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_bytes(json_bytes(value));temporary.replace(path)


def seed_for(master,gi,ei,trial):
    return (master<<64)|(gi<<48)|(ei<<32)|trial


def load_inputs(path,smoke=False):
    c=json.loads(path.read_text())
    if type(c['master_seed']) is not int or c['master_seed']<0:raise ValueError('invalid simulation master seed')
    if (c['trials']!=200 or c['epsilons']!=[.5,1,2,4]
        or c['methods']!=[{'id':'kcore_noisy_cap','kind':'oriented','ordering':'kcore','cap_mode':'noisy'}]
        or c['stage_fractions']!={'ordering':.25,'cap':.25,'rr':.25,'count':.25}
        or c['kcore']!={'psi':.5,'threshold_fraction':.5,'bias_factor':1} or c['beta']!=.05):
        raise ValueError('preserve the fixed evaluation settings')
    manifest=json.loads((PROJECT/'data/processed/graph_manifest.json').read_text())
    lookup={r['id']:r for r in manifest['graphs']}
    if set(lookup)!=set(EXPECTED) or len(c['graphs'])!=6 or {s['id'] for s in c['graphs']}!=set(EXPECTED):
        raise ValueError('exactly the six selected datasets are required')
    inputs=[];truth=[]
    for spec in c['graphs']:
        record=lookup[spec['id']];g=load_prepared_graph(spec)
        if record['sha256']!=spec['sha256'] or digest(PROJECT/'data/processed'/record['mapping_path'])!=record['mapping_sha256']:
            raise ValueError('dataset provenance changed')
        native=parse_count_four_output(record['validation']['escape_output'],num_vertices=g.num_vertices,num_edges=g.num_edges).connected_four['4-clique']
        if not native==record['exact_four_cliques']==spec['expected_four_cliques']==EXPECTED[spec['id']]:
            raise ValueError('saved native ESCAPE ground truth disagrees')
        inputs.append(g);truth.append({'graph':spec['id'],'sha256':spec['sha256'],'exact_count':native,
            'escape_output':record['validation']['escape_output'],'reference':manifest['escape_reference']})
    if smoke:c.update(trials=2,master_seed=202611081900,purpose='smoke_only_not_main_results')
    return c,inputs,truth


def provenance():
    return {'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT,text=True).strip(),
        'python':sys.version,'platform':platform.platform(),
        'dependencies':{k:importlib.metadata.version(k) for k in ['numpy','networkx','pandas']},
        'runner_sha256':digest(Path(__file__)),
        'mechanism_sha256':{n:digest(PROJECT/'src/private_graphlets'/n) for n in MECHANISMS},
        'dataset_manifest_sha256':digest(PROJECT/'data/processed/graph_manifest.json'),
        'submodules':subprocess.check_output(['git','submodule','status'],cwd=PROJECT,text=True).strip()}


def coordinates(c):
    return [(gi,ei,t) for gi in range(6) for ei in range(4) for t in range(c['trials'])]


def read_rows(db,c):
    stored=db.execute('SELECT ordinal,payload FROM trials ORDER BY ordinal').fetchall();rows=[]
    expected=coordinates(c)
    if len(stored)>len(expected):raise ValueError('too many saved trials')
    for i,(ordinal,payload) in enumerate(stored):
        row=json.loads(payload);gi,ei,t=expected[i];eps=c['epsilons'][ei];spec=c['graphs'][gi]
        if ordinal!=i or (row['graph_index'],row['epsilon_index'],row['trial'])!=(gi,ei,t):raise ValueError('invalid saved prefix')
        if row['seed']!=str(seed_for(c['master_seed'],gi,ei,t)) or row['graph']!=spec['id']:raise ValueError('saved seed/graph mismatch')
        if row['exact_count']!=spec['expected_four_cliques'] or row['epsilon']!=eps:raise ValueError('saved truth/budget mismatch')
        if tuple(row[k] for k in ['epsilon_O','epsilon_D','epsilon_R','epsilon_C'])!=(eps/4,)*4:raise ValueError('stage allocation mismatch')
        if not math.isfinite(row['estimate']):raise ValueError('nonfinite saved estimate')
        rows.append(row)
    return rows


def summarize(rows):
    records=[]
    if not rows:return pd.DataFrame()
    for (_, _),cell in pd.DataFrame(rows).groupby(['graph_index','epsilon_index'],sort=True):
        first=cell.iloc[0];x=cell.estimate.to_numpy(dtype=float);error=x-first.exact_count
        mse=float(np.mean(error**2));variance=float(np.var(x,ddof=0));bias=float(np.mean(error))
        if not math.isclose(mse,variance+bias*bias,rel_tol=1e-12,abs_tol=1e-12):raise AssertionError('population MSE identity failed')
        records.append({'graph':first.graph,'n':int(first.n),'m':int(first.m),'epsilon':first.epsilon,
            'method':'kcore_noisy_cap','trials':len(cell),'exact_count':int(first.exact_count),
            **{k:first[k] for k in ['epsilon_O','epsilon_D','epsilon_R','epsilon_C']},
            'mean_estimate':float(np.mean(x)),'mse':mse,'rmse':math.sqrt(mse),'bias':bias,
            'variance':variance,'variance_ddof':0,'mae':float(np.mean(np.abs(error))),
            'relative_rmse':math.sqrt(mse)/first.exact_count if first.exact_count else math.nan,
            'runtime_mean_seconds':float(cell.runtime_seconds.mean()),'runtime_total_seconds':float(cell.runtime_seconds.sum()),
            'diagnostic_mean_seconds':float(cell.diagnostic_seconds.mean()),'negative_estimates':int((x<0).sum()),
            'cap_mean':float(cell.cap.mean()),'cap_min':int(cell.cap.min()),'cap_max':int(cell.cap.max()),
            'cap_saturation_fraction':float(cell.cap_saturated.mean()),'max_out_degree_mean':float(cell.max_out_degree.mean()),
            'clipped_vertices_mean':float(cell.clipped_vertices.mean()),
            'discarded_outgoing_edges_mean':float(cell.discarded_outgoing_edges.mean())})
    return pd.DataFrame(records)


def export(db,c,output):
    rows=read_rows(db,c)
    for name,frame in [('trials.csv',pd.DataFrame(rows)),('summary.csv',summarize(rows))]:
        tmp=output/(name+'.tmp');frame.to_csv(tmp,index=False,float_format='%.17g');tmp.replace(output/name)
    status='complete' if len(rows)==len(coordinates(c)) else 'partial'
    state={'status':status,'completed_trials':len(rows),'target_trials':len(coordinates(c)),
        'remaining_trials':len(coordinates(c))-len(rows),'updated_utc':datetime.now(timezone.utc).isoformat(),
        'result_type':'nonprivate_public_graph_evaluation','files_sha256':{
            name:digest(output/name) for name in ['config.json','provenance.json','escape_ground_truth.json','trials.csv','summary.csv']}}
    atomic_json(output/'manifest.json',state);return state


def run(config_path,output,*,smoke=False,resume=False,max_new_trials=None):
    if max_new_trials is not None and max_new_trials<1:raise ValueError('max-new-trials must be positive')
    c,graphs,truth=load_inputs(config_path,smoke);current=provenance()
    if output.exists():
        if not resume:raise FileExistsError('output exists; use --resume to continue saved coordinates')
        if json.loads((output/'config.json').read_text())!=c:raise ValueError('resume configuration differs')
        old=json.loads((output/'provenance.json').read_text())
        for key in ['runner_sha256','mechanism_sha256','dataset_manifest_sha256','dependencies','submodules']:
            if current[key]!=old[key]:raise ValueError(f'resume provenance differs: {key}')
    else:
        output.mkdir(parents=True)
        atomic_json(output/'config.json',c);atomic_json(output/'provenance.json',current)
        atomic_json(output/'escape_ground_truth.json',truth)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with sqlite3.connect(output/'trials.sqlite3',timeout=0) as db:
            db.execute('CREATE TABLE IF NOT EXISTS trials (ordinal INTEGER PRIMARY KEY, payload TEXT NOT NULL)');db.commit()
            saved=read_rows(db,c);start=len(saved);jobs=coordinates(c)
            stop=len(jobs) if max_new_trials is None else min(len(jobs),start+max_new_trials)
            for i in range(start,stop):
                gi,ei,t=jobs[i];g=graphs[gi];spec=c['graphs'][gi];eps=c['epsilons'][ei]
                seed=seed_for(c['master_seed'],gi,ei,t);budget=CliqueBudget(eps,eps/4,eps/4,eps/4,eps/4)
                begin=time.perf_counter()
                result=simulate_four_cliques(g,eps,ordering='kcore',cap_mode='noisy',seed=seed,
                    budget=budget,beta=c['beta'],kcore_config=KCoreConfig(**c['kcore']))
                seconds=time.perf_counter()-begin;diag=time.perf_counter()
                if result.result.budget!=budget:raise AssertionError('simulator returned a different allocation')
                rank={v:j for j,v in enumerate(result.transcript.order)}
                q=[sum(rank[v]<rank[w] for w in neighbors) for v,neighbors in enumerate(g.adjacency)]
                cap=result.transcript.cap
                row={'graph':spec['id'],'n':g.num_vertices,'m':g.num_edges,'graph_index':gi,'epsilon_index':ei,'trial':t,
                    'method':'kcore_noisy_cap','epsilon':eps,'epsilon_O':budget.ordering,'epsilon_D':budget.cap,
                    'epsilon_R':budget.rr,'epsilon_C':budget.count,'seed':str(seed),'estimate':result.result.estimate,
                    'exact_count':truth[gi]['exact_count'],'runtime_seconds':seconds,'cap':cap,
                    'cap_saturated':int(cap==g.num_vertices-1),'max_out_degree':max(q,default=0),
                    'clipped_vertices':sum(d>cap for d in q),'discarded_outgoing_edges':sum(max(0,d-cap) for d in q),
                    'ordering_rounds':len(result.transcript.ordering.promotions),
                    'local_noise_scale':result.result.local_noise_scale,'privacy_status':'experimental_unverified',
                    'diagnostic_seconds':time.perf_counter()-diag}
                db.execute('INSERT INTO trials VALUES (?,?)',(i,json.dumps(row,allow_nan=False)));db.commit()
                if t==c['trials']-1:
                    print(json.dumps(export(db,c,output)),flush=True)
            state=export(db,c,output);state['new_trials_this_invocation']=stop-start;return state


def verify(output):
    c=json.loads((output/'config.json').read_text());manifest=json.loads((output/'manifest.json').read_text())
    for name,value in manifest['files_sha256'].items():
        if digest(output/name)!=value:raise ValueError('saved artifact hash changed')
    with sqlite3.connect(f'file:{output}/trials.sqlite3?mode=ro',uri=True) as db:rows=read_rows(db,c)
    raw=pd.read_csv(output/'trials.csv',dtype={'seed':str},float_precision='round_trip')
    pd.testing.assert_frame_equal(raw,pd.DataFrame(rows),check_dtype=False,check_exact=True)
    summary=pd.read_csv(output/'summary.csv',float_precision='round_trip')
    pd.testing.assert_frame_equal(summary,summarize(rows),check_dtype=False,rtol=1e-12,atol=1e-12)
    if len(rows)!=manifest['completed_trials']:raise ValueError('saved count mismatch')
    return {'status':'verified','study_status':manifest['status'],'trials':len(rows),'cells':len(summary),
            'remaining_trials':len(coordinates(c))-len(rows),'population_variance_identity':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['run','verify']);p.add_argument('--config',type=Path,default=DEFAULT_CONFIG)
    p.add_argument('--output',type=Path);p.add_argument('--smoke',action='store_true');p.add_argument('--resume',action='store_true')
    p.add_argument('--max-new-trials',type=int)
    a=p.parse_args();output=a.output or PROJECT/('build/phase19/smoke' if a.smoke else 'experiments/results/four_clique_six_datasets')
    result=verify(output) if a.command=='verify' else run(a.config,output,smoke=a.smoke,resume=a.resume,max_new_trials=a.max_new_trials)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
