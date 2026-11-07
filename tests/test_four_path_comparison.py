"""Equal-budget design, independent ideal variance, artifact and replay tests."""
from itertools import combinations
import json
import math
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest

from private_graphlets import four_path_comparison as cmp
from private_graphlets import four_path_study as study
from private_graphlets import four_path_experiments as pilot
from private_graphlets.experiments import sha256
from private_graphlets.escape import EscapeAdapter, build_count_four
from private_graphlets.graph import SimpleGraph, load_edge_list
from test_four_path_baseline_2025 import oracle_variance

PROJECT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('n',range(6))
def test_exact_variance_against_independent_expansion(n):
    pairs=list(combinations(range(n),2))
    for mask in range(1<<len(pairs)):
        g=SimpleGraph.from_edges(n,[e for i,e in enumerate(pairs) if mask>>i&1])
        assert cmp.baseline_variance(g,1.3)==pytest.approx(oracle_variance(g,1.3),rel=2e-13,abs=1e-12)


@pytest.mark.parametrize('name',['path','cycle','diamond','clique','clique_with_isolates','star','edgeless','tailed_triangle'])
def test_fixture_variance(name):
    g=load_edge_list(PROJECT/'data/fixtures'/f'{name}.edges')
    for epsilon in (1,4,6.5,8):
        assert cmp.baseline_variance(g,epsilon)==pytest.approx(oracle_variance(g,epsilon))


def test_metrics_and_independent_uncertainty():
    a=cmp.metrics([0,2,4],1); b=cmp.metrics([0,1,2],1)
    assert a['mse']==pytest.approx(11/3)
    assert a['bias']==1; assert a['variance']==4
    assert a['se_mse']==pytest.approx(np.std([1,1,9],ddof=1)/math.sqrt(3))
    d=cmp.difference(a,b)
    assert d['mse_difference']==3
    assert d['mse_ratio']==pytest.approx(5.5)
    assert d['se_difference']==pytest.approx(math.hypot(a['se_mse'],b['se_mse']))
    assert d['ci95_low']==pytest.approx(3-1.959963984540054*d['se_difference'])
    assert d['simultaneous_low']<d['ci95_low']
    assert math.isnan(cmp.metrics([0,1],0)['relative_rmse'])
    assert math.isnan(cmp.difference(a,cmp.metrics([1,1],1))['mse_ratio'])


@pytest.mark.parametrize('values',[[1],[float('nan'),1],[float('inf'),0],[[1,2],[3,4]]])
def test_nonfinite_metrics(values):
    with pytest.raises(ValueError): cmp.metrics(values,1)


def design():
    return cmp.load_config(PROJECT/'experiments/configs/four_path_phase17_comparison.json')


def test_design_shared_baseline_and_seed_independence():
    c=design()
    assert len(c['cells'])==26 and len(cmp.conditions(c))==20
    seeds=[]
    for i in range(26):
        cc=cmp.candidate_config(c,i)
        for stream in ('full','prediction'):
            seeds += [pilot.experiment_seed(cc['master_seed'],0,stream,t) for t in range(3)]
    seeds += [cmp.baseline_seed(c,i,t) for i in range(20) for t in range(3)]
    assert len(seeds)==len(set(seeds))
    for graph in ('er30_n50','ba4_n50'):
        selected=[x for x in c['cells'] if x['graph']==graph and x['baseline_epsilon']==4]
        assert len(selected)==4  # B epsilon4 plus three C allocations, one baseline


@pytest.mark.parametrize('mutation',['epsilon','size','trials','prediction','seed','beta','budget','duplicate','alpha','nan'])
def test_invalid_config(mutation):
    c=design()
    if mutation=='epsilon': c['cells'][0]['baseline_epsilon']=1
    if mutation=='size': c['graphs'][0]['n']=101
    if mutation=='trials': c['trials']=1
    if mutation=='prediction': c['prediction_trials']=501
    if mutation=='seed': c['master_seed']=-1
    if mutation=='beta': c['cells'][0]['beta']=0
    if mutation=='budget': c['cells'][0]['budget']['ordering']=2
    if mutation=='duplicate': c['cells'][1]['id']=c['cells'][0]['id']
    if mutation=='alpha': c['alpha']=.1
    if mutation=='nan': c['cells'][0]['baseline_epsilon']=float('nan')
    with pytest.raises(ValueError): cmp.validate_config(c)


def test_variance_guards():
    with pytest.raises(ValueError): cmp.baseline_variance(SimpleGraph.from_edges(101,[]),1)
    with pytest.raises(ValueError): cmp.baseline_variance(SimpleGraph.from_edges(4,[]),31)


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    return EscapeAdapter(build_count_four(build_dir=tmp_path_factory.mktemp('comparison_escape')))


@pytest.fixture
def tiny(tmp_path,native):
    old=json.loads((PROJECT/'experiments/configs/four_path_phase13_smoke.json').read_text())
    old['graphs']=[dict(id='g',family='erdos_renyi',n=5,p=.4,seed=171)]
    old['cells']=old['cells'][:3]
    for i,x in enumerate(old['cells']):
        x.update(id=f'cell{i}',graph='g',experiment='ABC'[i],budget=old['cells'][0]['budget'].copy())
    p=tmp_path/'old.json'; p.write_text(json.dumps(old))
    root=tmp_path/'history';study.run_study(p,root,native)
    c=design();c['graphs']=old['graphs'];c['cells']=[dict(x,baseline_epsilon=6.5) for x in old['cells']]
    c.update(trials=3,prediction_trials=3,historical_output=str(root),historical_manifest_sha256=sha256(root/'manifest.json'))
    p=tmp_path/'comparison.json';p.write_text(json.dumps(c))
    return p


def test_roundtrip_native_replay_shared_baseline(tiny,tmp_path,native):
    out=tmp_path/'result'
    m=cmp.run_comparison(tiny,out,native)
    assert m['candidate_trials']==9 and m['baseline_trials']==3
    assert cmp.verify_comparison(out,replay=True)['distinct_seeds']==21
    frame=pd.read_csv(out/'comparison_summary.csv')
    assert frame.baseline_condition.nunique()==1
    assert set(frame.baseline_trials)=={3}
    assert frame.baseline_mse.nunique()==1
    assert len(list((out/'plots').glob('*.png')))==7
    assert len(list((out/'plots').glob('*.pdf')))==7
    original_trials=sha256(out/'baseline/b00/trials.csv')
    assert cmp.replot_comparison(out)['trial_data_changed'] is False
    assert sha256(out/'baseline/b00/trials.csv')==original_trials
    assert cmp.verify_comparison(out)['status']=='verified'
    with pytest.raises(FileExistsError):cmp.run_comparison(tiny,out,native)
    for filename in ['comparison_summary.csv','baseline/b00/trials.csv','graphs/g.edges']:
        copy=tmp_path/filename.replace('/','_');shutil.copytree(out,copy)
        with (copy/filename).open('a') as stream:stream.write('corrupt')
        with pytest.raises(ValueError,match='hash'):cmp.verify_comparison(copy)
    release=json.loads((out/'baseline/b00/mechanism_outputs.jsonl').read_text().splitlines()[0])
    assert set(release)=={'result','transcript'}
    assert not {'seed','truth','mse','seconds'} & set(release['result'])


def test_historical_corruption_and_changed_budget(tiny):
    c=cmp.load_config(tiny)
    cmp.historical_graphs(c)
    c['cells'][0]['beta']=.1
    with pytest.raises(ValueError,match='historical comparison'):cmp.historical_graphs(c)
    c=cmp.load_config(tiny)
    with (Path(c['historical_output'])/'summary.csv').open('a') as f:f.write('corruption')
    with pytest.raises(ValueError,match='historical inventory'):cmp.historical_graphs(c)


def test_directional_rules_and_shared_difference_covariance():
    low=dict(mse=1.,rmse=1.,se_mse=.01)
    high=dict(mse=100.,rmse=10.,se_mse=.1)
    assert cmp.difference(low,high)['adjusted_conclusion']=='candidate'
    assert cmp.difference(high,low)['adjusted_conclusion']=='baseline'
    assert cmp.difference(low,low)['adjusted_conclusion']=='inconclusive'
    # For D1=A1-B and D2=A2-B, Cov(D1,D2)=Var(B). It cancels
    # from Var(D1-D2); never add two baseline variances for allocation contrasts.
    s1,s2,sb=2.,3.,5.
    assert (s1*s1+sb*sb)+(s2*s2+sb*sb)-2*sb*sb==s1*s1+s2*s2


def test_complete_graph_n100_variance_is_finite():
    g=SimpleGraph.from_edges(100,combinations(range(100),2))
    h=math.exp(6.5)/math.expm1(6.5)**2
    # Each edge is in 6*C(n-2,2) paths. Adjacent pair has 2(n-3)
    # extensions; disjoint pair has four. All coefficients known independently.
    n=100
    expected=(math.comb(n,2)*(6*math.comb(n-2,2))**2*h
              +(n*math.comb(n-1,2)*(2*(n-3))**2+3*math.comb(n,4)*16)*h*h
              +12*math.comb(n,4)*h**3)
    assert cmp.baseline_variance(g,6.5)==pytest.approx(expected,rel=1e-14)
