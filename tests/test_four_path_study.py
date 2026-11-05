"""Phase 4B bounded design, native evidence, statistics and artifact tests."""
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest

from private_graphlets import four_path_study as study
from private_graphlets import four_path_experiments as pilot
from private_graphlets.escape import EscapeAdapter, build_count_four

PROJECT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config_path(tmp_path):
    config = json.loads((PROJECT/'experiments/configs/four_path_phase13_smoke.json').read_text())
    # Retain all four experiment types, but use one small seeded ER instance.
    graph = dict(id='er30_n6', family='erdos_renyi', n=6, p=.3, seed=13)
    config['graphs'] = [graph]
    for c in config['cells']: c['graph'] = graph['id']
    path = tmp_path/'config.json'
    path.write_text(json.dumps(config))
    return path


@pytest.fixture(scope='module')
def adapter(tmp_path_factory):
    return EscapeAdapter(build_count_four(build_dir=tmp_path_factory.mktemp('study_escape')))


@pytest.mark.parametrize('key,value', [('trials',1),('trials',1001),('prediction_trials',501),
    ('prediction_trials',True),('master_seed',-1),('schema_version',1),
    ('max_relative_se',float('nan')),('max_relative_se',1),('experiment_id','../bad')])
def test_bad_top_config(config_path,key,value):
    c=json.loads(config_path.read_text()); c[key]=value; config_path.write_text(json.dumps(c))
    with pytest.raises(ValueError): study.load_config(config_path)


@pytest.mark.parametrize('mutation', ['size','probability','attachment','budget','beta','duplicate','order','cap'])
def test_bad_graph_cell_control(config_path,mutation):
    c=json.loads(config_path.read_text())
    if mutation=='size': c['graphs'][0]['n']=101
    if mutation=='probability': c['graphs'][0]['p']=1.2
    if mutation=='attachment': c['graphs'][0]=dict(id='er30_n6',family='barabasi_albert',n=6,m=6,seed=1)
    if mutation=='budget': c['cells'][0]['budget']['ordering']=1.1
    if mutation=='beta': c['cells'][0]['beta']=0
    if mutation=='duplicate': c['cells'].append(c['cells'][0])
    if mutation=='order': c['controls'][0]['order']=[0]*4
    if mutation=='cap': c['controls'][0]['cap']=-1
    config_path.write_text(json.dumps(c))
    with pytest.raises(ValueError): study.load_config(config_path)


def test_design_and_phase4a_limits(config_path):
    c=study.load_config(PROJECT/'experiments/configs/four_path_phase13_accuracy.json')
    assert study.workload(c)['full_trials']==18000
    assert study.workload(c)['prediction_histories']==12000
    assert len(c['cells'])==30
    for g in c['graphs']: assert study.study_graph(g)==study.study_graph(g)
    cc=study.cell_config(c,0)
    config_path.write_text(json.dumps(cc))
    assert study._load_cell(config_path)==cc
    with pytest.raises(ValueError): pilot.load_config(config_path)
    with pytest.raises(ValueError): pilot.experiment_graph(c['graphs'][8])
    seeds=[pilot.experiment_seed(study.cell_config(c,i)['master_seed'],0,s,t)
           for i in range(len(c['cells'])) for s in ['full','prediction'] for t in range(5)]
    assert len(set(seeds))==len(seeds)


def test_fixed_controls(config_path):
    c=study.load_config(config_path)
    rows=study.controls(c).set_index('control')
    assert rows.loc['K4_B1','missed_triangles']==4
    assert rows.loc['K4_B2','retained_triangles']==2
    assert rows.loc['K4_B2','bias']==6
    for r in rows.to_dict('records'):
        assert r['bias']==3*r['missed_triangles']
        assert r['mse']==pytest.approx(r['variance']+r['bias']**2)
        assert sum(r[k] for k in study.COMPONENTS)==pytest.approx(r['mse'])
        assert 'NOT_FULL_PROTOCOL' in r['scope']


def test_roundtrip_native_metrics_plots_replay(config_path,tmp_path,adapter):
    output=tmp_path/'study'
    manifest=study.run_study(config_path,output,adapter)
    assert manifest['status']=='complete'
    assert study.verify_study(output,replay=True)['replayed']
    assert len(list((output/'plots').glob('*.png')))==6
    assert len(list((output/'plots').glob('*.pdf')))==6
    assert all(p.stat().st_size>1000 for p in (output/'plots').iterdir())
    summary=pd.read_csv(output/'summary.csv',float_precision='round_trip')
    for r in summary.to_dict('records'):
        full=pilot._read_csv(output/'cells'/r['cell']/'evaluation_trials.csv')
        err=full.estimate-r['exact_four_paths']
        assert r['empirical_mse']==pytest.approx((err**2).mean())
        assert r['se_mse']==pytest.approx((err**2).std(ddof=1)/np.sqrt(len(err)))
        assert r['full_mean_squared_missed']==pytest.approx((full.missed_triangles**2).mean())
        assert r['full_truncation_bias']==pytest.approx(3*full.missed_triangles.mean())
        assert sum(r['mean_'+k] for k in study.COMPONENTS)==pytest.approx(r['predicted_mse'])
    with pytest.raises(FileExistsError): study.run_study(config_path,output,adapter)
    with pytest.raises(FileExistsError): study.plot_summary(summary,output/'plots')
    # Test missing, corrupt, and appended artifacts against independent copies.
    for name in ['summary.csv','fixed_controls.csv','escape/er30_n6.json','plots/truncation.png']:
        copy=tmp_path/('corrupt_'+name.replace('/','_'))
        shutil.copytree(output,copy)
        with (copy/name).open('ab') as f: f.write(b'corrupt')
        with pytest.raises(ValueError,match='hash'): study.verify_study(copy)
    # Release records retain the existing modeled-report schema, no evaluation fields.
    release=json.loads(next((output/'cells').glob('*/mechanism_outputs/*.jsonl')).read_text().splitlines()[0])
    assert set(release)=={'result','transcript'}
    assert not {'seed','missed_triangles','exact_four_paths'} & set(release['result'])


def test_zero_truth_relative_rmse(config_path,tmp_path,adapter):
    c=json.loads(config_path.read_text()); c['graphs'][0]['p']=0
    c['cells']=c['cells'][:1]; config_path.write_text(json.dumps(c))
    output=tmp_path/'zero'
    study.run_study(config_path,output,adapter)
    summary=pd.read_csv(output/'summary.csv')
    assert summary.exact_four_paths.iloc[0]==0
    assert pd.isna(summary.relative_rmse.iloc[0])
    assert not summary.relative_rmse_defined.iloc[0]
    assert study.verify_study(output,replay=True)['status']=='verified'
