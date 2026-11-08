"""Independent, non-private evaluation of the existing five-stage P4 simulator.

Six pinned datasets, fixed D/O/R/M/C allocation, 200 trials/cell. SQLite commits each
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
from private_graphlets.four_path import FourPathBudget,simulate_four_paths_private
from private_graphlets.graph_datasets import PROJECT,digest,json_bytes,load_prepared_graph
from private_graphlets.kcore import KCoreConfig

EXPECTED={'karate':2371,'dolphins':5023,'les_miserables':26784,'brightkite_50':5404,'ba_n100':2043892,'sbm_n100':166236}
FRACTIONS={'degree':.30,'ordering':.10,'rr':.25,'cap':.15,'count':.20}
STAGES={'epsilon_D':'degree','epsilon_O':'ordering','epsilon_R':'rr','epsilon_M':'cap','epsilon_C':'count'}
DEFAULT_CONFIG=PROJECT/'experiments/configs/four_path_six_datasets.json'
MECHANISMS=['four_path.py','triangle.py','four_clique.py','kcore.py','randomized_response.py','noise.py','four_clique_exact.py','graph.py']


def atomic_json(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_bytes(json_bytes(value));temporary.replace(path)


def seed_for(master,gi,ei,trial):
    return (master<<64)|(gi<<48)|(ei<<32)|trial


def load_inputs(path,smoke=False):
    c=json.loads(path.read_text())
    if type(c['master_seed']) is not int or c['master_seed']<0:raise ValueError('invalid simulation master seed')
    if (c['trials']!=200 or c['epsilons']!=[.5,1,2,4]
        or c['method']!='modified_edgeorientdelta_p4'
        or c['stage_fractions']!=FRACTIONS
        or c['kcore']!={'psi':.5,'threshold_fraction':.5,'bias_factor':1} or c['beta']!=.05):
        raise ValueError('preserve the fixed evaluation settings')
    manifest=json.loads((PROJECT/'data/processed/graph_manifest.json').read_text())
    lookup={r['id']:r for r in manifest['graphs']}
    if set(lookup)!=set(EXPECTED) or len(c['graphs'])!=6 or {s['id'] for s in c['graphs']}!=set(EXPECTED):
        raise ValueError('exactly the six selected datasets are required')
    cache=PROJECT/'experiments/results/p4_standardized_ground_truth/ground_truth.csv'
    if not cache.is_file():
        raise FileNotFoundError('Checkpoint 20 cache missing; reconstruct using native ESCAPE before running')
    cached=pd.read_csv(cache).set_index('dataset')
    if len(cached)!=6 or set(cached.index)!=set(EXPECTED):raise ValueError('invalid truth cache')
    inputs=[];truth=[]
    for spec in c['graphs']:
        record=lookup[spec['id']];g=load_prepared_graph(spec);row=cached.loc[spec['id']]
        if (record['sha256']!=spec['sha256'] or row.sha256!=spec['sha256']
            or row.graph_path!=spec['path'] or row.vertices!=g.num_vertices or row.edges!=g.num_edges
            or spec['path']!='data/processed/'+record['path']
            or (record['processed_vertices'],record['processed_edges'])!=(g.num_vertices,g.num_edges)
            or digest(PROJECT/'data/processed'/record['mapping_path'])!=record['mapping_sha256']):
            raise ValueError('dataset provenance changed')
        native=parse_count_four_output(record['validation']['escape_output'],num_vertices=g.num_vertices,num_edges=g.num_edges).connected_four['3-path']
        if not native==row.exact_python_p4==row.exact_escape_p4==spec['expected_p4']==EXPECTED[spec['id']] or row.verification_status!='verified':
            raise ValueError('Checkpoint 20/native P4 truth disagrees')
        inputs.append(g);truth.append({'graph':spec['id'],'sha256':spec['sha256'],'exact_count':native,
            'escape_output':record['validation']['escape_output'],'reference':manifest['escape_reference']})
    for eps in c['epsilons']:
        budget=FourPathBudget(**{k:eps*v for k,v in FRACTIONS.items()})
        if not math.isclose(budget.total,eps,rel_tol=1e-15):raise ValueError('allocation sum mismatch')
    KCoreConfig(**c['kcore'])
    if smoke:c.update(trials=2,master_seed=202611082100,purpose='smoke_only_not_main_results')
    return c,inputs,truth


def provenance():
    return {'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT,text=True).strip(),
        'python':sys.version,'platform':platform.platform(),
        'dependencies':{k:importlib.metadata.version(k) for k in ['numpy','networkx','pandas']},
        'runner_sha256':digest(Path(__file__)),
        'truth_cache_sha256':digest(PROJECT/'experiments/results/p4_standardized_ground_truth/ground_truth.csv'),
        'hardware':platform.machine(),
        'reference_manifest_sha256':digest(PROJECT/'third_party/references.json'),
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
        if row['exact_count']!=spec['expected_p4'] or row['epsilon']!=eps:raise ValueError('saved truth/budget mismatch')
        if any(row[k]!=eps*FRACTIONS[v] for k,v in STAGES.items()):raise ValueError('stage allocation mismatch')
        if row['method']!='modified_edgeorientdelta_p4' or not math.isfinite(row['runtime_seconds']) or row['runtime_seconds']<0:raise ValueError('invalid method/runtime')
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
            'method':'modified_edgeorientdelta_p4','trials':len(cell),'exact_count':int(first.exact_count),
            **{k:first[k] for k in STAGES},
            'mean_estimate':float(np.mean(x)),'mse':mse,'rmse':math.sqrt(mse),'bias':bias,
            'variance':variance,'variance_ddof':0,'mae':float(np.mean(np.abs(error))),
            'relative_rmse':math.sqrt(mse)/abs(first.exact_count) if first.exact_count else math.nan,
            'mse_se':float(np.std(error**2,ddof=1)/math.sqrt(len(x))) if len(x)>1 else math.nan,
            'mean_runtime_seconds':float(cell.runtime_seconds.mean()),
            'runtime_total_seconds':float(cell.runtime_seconds.sum()),
            'negative_estimates':int((x<0).sum())})
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
        for key in ['runner_sha256','mechanism_sha256','dataset_manifest_sha256','dependencies','submodules','truth_cache_sha256','reference_manifest_sha256']:
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
                seed=seed_for(c['master_seed'],gi,ei,t)
                budget=FourPathBudget(**{k:eps*v for k,v in FRACTIONS.items()})
                kconfig=KCoreConfig(**c['kcore'])
                begin=time.perf_counter()
                result=simulate_four_paths_private(g,seed=seed,budget=budget,beta=c['beta'],kcore_config=kconfig)
                seconds=time.perf_counter()-begin
                if result.result.budget!=budget:raise AssertionError('simulator returned a different allocation')
                row={'graph':spec['id'],'n':g.num_vertices,'m':g.num_edges,'graph_index':gi,'epsilon_index':ei,'trial':t,
                    'method':'modified_edgeorientdelta_p4','epsilon':eps,
                    **{k:getattr(budget,v) for k,v in STAGES.items()},
                    'seed':str(seed),'estimate':result.result.estimate,
                    'exact_count':truth[gi]['exact_count'],'runtime_seconds':seconds,
                    'privacy_status':'experimental_unverified'}
                db.execute('INSERT INTO trials VALUES (?,?)',(i,json.dumps(row,allow_nan=False)));db.commit()
                if t==c['trials']-1:
                    print(json.dumps(export(db,c,output)),flush=True)
            state=export(db,c,output);state['new_trials_this_invocation']=stop-start;return state


def verify(output):
    c=json.loads((output/'config.json').read_text());manifest=json.loads((output/'manifest.json').read_text())
    for name,value in manifest['files_sha256'].items():
        if digest(output/name)!=value:raise ValueError('saved artifact hash changed')
    with sqlite3.connect(f'file:{output}/trials.sqlite3?mode=ro',uri=True) as db:rows=read_rows(db,c)
    smoke=c.get('purpose')=='smoke_only_not_main_results'
    checked,_,truth=load_inputs(DEFAULT_CONFIG,smoke)
    if checked!=c:raise ValueError('saved/current configuration mismatch')
    if json.loads((output/'escape_ground_truth.json').read_text())!=truth:raise ValueError('truth evidence mismatch')
    current=provenance();old=json.loads((output/'provenance.json').read_text())
    for key in ['runner_sha256','mechanism_sha256','dataset_manifest_sha256','dependencies','submodules','truth_cache_sha256','reference_manifest_sha256']:
        if current[key]!=old[key]:raise ValueError(f'verification provenance differs: {key}')
    if len({r['seed'] for r in rows})!=len(rows):raise ValueError('duplicate seed')
    raw=pd.read_csv(output/'trials.csv',dtype={'seed':str},float_precision='round_trip')
    pd.testing.assert_frame_equal(raw,pd.DataFrame(rows),check_dtype=False,check_exact=True)
    summary=pd.read_csv(output/'summary.csv',float_precision='round_trip')
    pd.testing.assert_frame_equal(summary,summarize(rows),check_dtype=False,rtol=1e-12,atol=1e-12)
    if len(rows)!=manifest['completed_trials']:raise ValueError('saved count mismatch')
    result={'status':'verified','study_status':manifest['status'],'trials':len(rows),'cells':len(summary),
            'remaining_trials':len(coordinates(c))-len(rows),'population_variance_identity':True}
    atomic_json(output/'verification.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['run','verify']);p.add_argument('--config',type=Path,default=DEFAULT_CONFIG)
    p.add_argument('--output',type=Path);p.add_argument('--smoke',action='store_true');p.add_argument('--resume',action='store_true')
    p.add_argument('--max-new-trials',type=int)
    a=p.parse_args();output=a.output or PROJECT/('build/phase21/smoke' if a.smoke else 'experiments/results/four_path_six_datasets')
    result=verify(output) if a.command=='verify' else run(a.config,output,smoke=a.smoke,resume=a.resume,max_new_trials=a.max_new_trials)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
