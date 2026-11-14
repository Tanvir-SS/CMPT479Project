"""Non-private evaluation records: seeds/truth are not private releases."""
import argparse
import csv
import hashlib
import io
import json
import math
import platform
import subprocess
import sys
from pathlib import Path
import numpy as np
from build import ROOT, BUILD, sha
from convert import OUT, CONFIG, write_graph
BASE=Path(__file__).resolve().parent
FIELDS=['graph','method','epsilon','trial','seed','estimate','exact_count','runtime_seconds']

def dump(name, value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')

def fingerprint():
    paths=[BUILD/'wlocal', CONFIG, OUT/'conversion.json', ROOT/'experiments/results/four_cycle_uniform_rr_six_datasets/summary.csv']
    paths += sorted(BASE.glob('*.py')) + [BASE/'driver.cpp'] + sorted((ROOT/'WLocal4Cycle').glob('*'))
    paths += sorted((OUT/'inputs').glob('*.csv'))
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()}

def execute(graph, eps, seeds, sanitize=False):
    cmd=[str(BUILD/('wlocal_sanitize' if sanitize else 'wlocal')),str(graph),str(eps)]
    run=subprocess.run(cmd,input=''.join(f'{s}\n' for s in seeds),text=True,capture_output=True,check=True)
    lines=run.stdout.splitlines()
    exact=int(lines[0].split(',')[1])
    rows=[(int(s),float(x),float(t)) for s,x,t in csv.reader(lines[1:])]
    assert [r[0] for r in rows]==seeds and all(math.isfinite(r[1]) for r in rows)
    return exact,rows

def validate():
    assert not (OUT/'validation.json').exists(), 'Validation already exists; do not silently repeat trials.'
    fixture=OUT/'c4.csv'; write_graph(fixture,4,[(0,1),(0,3),(1,2),(2,3)])
    results=[]
    # Predeclared independent ranges; 20k C4 and 5k pinned validation trials.
    for name,p,ntruth,start,num in [('one_c4',fixture,1,100000,20000),('karate',OUT/'inputs/karate.csv',154,200000,5000)]:
        exact,rows=execute(p,4,list(range(start,start+num)))
        assert exact==ntruth
        x=np.array([r[1] for r in rows]); se=float(x.std(ddof=1)/math.sqrt(num))
        z=abs(float(x.mean())-exact)/se
        assert z<4, (name,z)
        if name=='one_c4': assert abs(float(x.mean())-1)<.05
        with (OUT/f'validation_{name}.csv').open('w') as f:
            w=csv.writer(f); w.writerow(['seed','estimate','runtime_seconds']); w.writerows(rows)
        results.append(dict(graph=name,trials=num,epsilon=4,exact_count=exact,mean=float(x.mean()),standard_error=se,z=z,first_200_mean=float(x[:200].mean())))
    replays=[]
    for g in json.loads(CONFIG.read_text())['graphs']:
        p=OUT/'inputs'/f"{g['id']}.csv"; seeds=list(range(300000,300005))
        exact,rows=execute(p,.5,seeds,True)
        exact2,rows2=execute(p,.5,seeds)
        assert exact==exact2==g['expected_c4']
        assert [r[:2] for r in rows]==[r[:2] for r in rows2]
        assert len({r[1] for r in rows})>1
        replays.append(g['id'])
    dump('validation.json',dict(statistical_checks=results,sanitizer_and_replay=replays,fingerprint=fingerprint(),criterion='predeclared abs(z)<4; C4 absolute mean error<.05; descriptive consistency, not proof'))
    print(json.dumps(results,indent=2))

def coordinates():
    config=json.loads(CONFIG.read_text())
    for gi,g in enumerate(config['graphs']):
        assert sha(ROOT/g['path'])==g['sha256']
        for ei,eps in enumerate(config['epsilons']):
            for trial in range(200):
                yield g,eps,trial,28000000+gi*100000+ei*1000+trial

def read_rows():
    p=OUT/'trials.csv'
    return list(csv.DictReader(p.open())) if p.exists() else []

def check_rows(rows,complete=False):
    expected={(g['id'],float(e),t):(g,s) for g,e,t,s in coordinates()}
    seen=set()
    for r in rows:
        key=r['graph'],float(r['epsilon']),int(r['trial'])
        assert key not in seen; seen.add(key)
        g,s=expected[key]
        assert int(r['seed'])==s and int(r['exact_count'])==g['expected_c4']
        assert r['method']=='authors_wlocal_c4' and math.isfinite(float(r['estimate']))
        assert math.isfinite(float(r['runtime_seconds'])) and float(r['runtime_seconds'])>=0
    if complete: assert len(seen)==4800
    return seen

def run(limit):
    valid=json.loads((OUT/'validation.json').read_text())
    assert valid['fingerprint']==fingerprint(), 'Changed validated sources/config/inputs'
    rows=read_rows(); seen=check_rows(rows)
    first=not (OUT/'trials.csv').exists()
    with (OUT/'trials.csv').open('a',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        if first: writer.writeheader(); f.flush()
        added=0
        for g,eps,trial,seed in coordinates():
            if (g['id'],eps,trial) in seen: continue
            if limit is not None and added>=limit: break
            truth,[(s,x,t)]=execute(OUT/'inputs'/f"{g['id']}.csv",eps,[seed])
            assert truth==g['expected_c4']
            writer.writerow(dict(zip(FIELDS,[g['id'],'authors_wlocal_c4',eps,trial,s,x,truth,t])))
            f.flush(); added+=1
    print(f'{len(seen)+added}/4800 saved; {added} new trials')

def summaries(rows):
    answer=[]
    for gi,g in enumerate(json.loads(CONFIG.read_text())['graphs']):
        for eps in [.5,1.,2.,4.]:
            cell=[r for r in rows if r['graph']==g['id'] and float(r['epsilon'])==eps]
            x=np.array([float(r['estimate']) for r in cell]); k=g['expected_c4']; err=x-k
            mse=float(np.mean(err**2)); bias=float(x.mean()-k); variance=float(x.var(ddof=0))
            assert math.isclose(mse,variance+bias*bias,rel_tol=1e-12)
            answer.append(dict(graph=g['id'],epsilon=eps,method='authors_wlocal_c4',trials=len(x),exact_count=k,mean_estimate=float(x.mean()),bias=bias,mse=mse,rmse=math.sqrt(mse),variance=variance,variance_ddof=0,mae=float(np.mean(abs(err))),relative_rmse=math.sqrt(mse)/k,negative_estimates=int(sum(x<0)),negative_percentage=float(np.mean(x<0)*100),runtime_total_seconds=sum(float(r['runtime_seconds']) for r in cell)))
    return answer

def write_csv(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def analyze(verify=False):
    assert json.loads((OUT/'validation.json').read_text())['fingerprint']==fingerprint()
    rows=read_rows(); check_rows(rows,True); summary=summaries(rows)
    old=list(csv.DictReader((ROOT/'experiments/results/four_cycle_uniform_rr_six_datasets/summary.csv').open()))
    comparison=[]
    for r in summary:
        [ours]=[s for s in old if s['graph']==r['graph'] and float(s['epsilon'])==r['epsilon']]
        assert int(ours['trials'])==200 and int(ours['exact_count'])==r['exact_count']
        comparison.append(dict(graph=r['graph'],epsilon=r['epsilon'],true_c4=r['exact_count'],our_rmse=float(ours['rmse']),wlocal_rmse=r['rmse'],rmse_ratio=float(ours['rmse'])/r['rmse'],our_undirected_edge_epsilon=r['epsilon'],wlocal_undirected_edge_epsilon_bound=2*r['epsilon']))
    for name,table in [('summary.csv',summary),('comparison.csv',comparison)]:
        if verify:
            saved=list(csv.DictReader((OUT/name).open()))
            assert saved==[{k:str(v) for k,v in r.items()} for r in table]
        else: write_csv(name,table)
    if verify:
        manifest=json.loads((OUT/'artifacts.json').read_text())
        for name,h in manifest.items(): assert sha(OUT/name)==h
        print('PASS: 4800 unique coordinates/seeds; 24 cells x 200; all metrics, ratios and hashes verified.')
    else:
        dump('configuration.json',dict(trials=4800,epsilons=[.5,1,2,4],per_cell=200,pairs='floor(n/2)',seed_rule='28000000 + graph_index*100000 + epsilon_index*1000 + trial',private_release=False,ratio='Our RMSE / WLocal RMSE',python=sys.version,platform=platform.platform(),fingerprint=fingerprint(),build=json.loads((BUILD/'build.json').read_text())))
        dump('artifacts.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name not in ['artifacts.json','verification.log']})
        print('Saved 24-cell summaries and comparison.')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['validate','run','analyze','verify']); ap.add_argument('--max-new-trials',type=int)
    args=ap.parse_args()
    if args.action=='validate': validate()
    elif args.action=='run': run(args.max_new_trials)
    else: analyze(args.action=='verify')
