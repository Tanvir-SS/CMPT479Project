"""CLI boundaries and reproducible public-synthetic experiment artifacts."""

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from private_graphlets.four_clique_experiments import (
    aggregate, experiment_graph, load_config, plot_results, run_experiment,
    trial_seed, verify_results,
)


@pytest.mark.parametrize('command,args',[
    ('exact-four-cliques',[]),
    ('baseline-four-cliques',['--epsilon','2','--seed','12']),
    ('estimate-four-cliques',['--epsilon','2','--seed','12']),
    ('estimate-four-cliques',['--epsilon','2','--seed','12','--ordering','fixed','--cap-mode','uncapped']),
    ('estimate-four-cliques',['--epsilon','4','--seed','12','--cap-mode','public','--cap','3']),
])
def test_installed_four_clique_commands(tmp_path,command,args):
    path=tmp_path/'K4.edges'
    path.write_text('4 6\n0 1\n0 2\n0 3\n1 2\n1 3\n2 3\n')
    proc=subprocess.run([sys.executable,'-m','private_graphlets',command,str(path),*args],
                        cwd=tmp_path,text=True,capture_output=True,check=True)
    value=json.loads(proc.stdout)
    assert value['pattern']=='4-clique'
    if command.startswith('exact'): assert value['count']==1
    else:
        assert value['privacy_status']=='experimental_unverified'
        assert not set(value)&{'degrees','seed','count','num_edges','max_out_degree','retained_count','rr_upper'}


@pytest.mark.parametrize('args',[
    ['--epsilon','0'], ['--epsilon','2','--cap-mode','public'],
    ['--epsilon','2','--ordering','degree'],
    ['--epsilon','2','--budget','1','1','1','1'],
    ['--epsilon','2','--public-order','0,1,2,3'],
])
def test_cli_rejects_invalid_options(tmp_path,args):
    path=tmp_path/'empty.edges';path.write_text('4 0\n')
    result=subprocess.run([sys.executable,'-m','private_graphlets','estimate-four-cliques',str(path),*args],
                          text=True,capture_output=True)
    assert result.returncode==2 and not result.stdout


def test_injective_trial_coordinates():
    seeds={trial_seed(600,gi,ei,mi,t) for gi in range(3) for ei in range(4) for mi in range(5) for t in range(20)}
    assert len(seeds)==1200
    with pytest.raises(ValueError): trial_seed(600,0,0,0,65536)


def test_metrics_distinguish_original_and_retained_targets():
    common={'graph':'g','epsilon':1,'method':'m','n':5,'m':10,'degeneracy':4,
            'exact_count':5,'retained_count':2,'cap':3,'max_out_degree':4,'clipped_vertices':1,
            'runtime_seconds':.01,'ordering_type':'fixed_public','cap_mode':'public',
            'epsilon_O':0,'epsilon_D':0,'epsilon_R':.5,'epsilon_C':.5,'privacy_status':'experimental_unverified'}
    row=aggregate(pd.DataFrame([{**common,'estimate':1},{**common,'estimate':3}])).iloc[0]
    assert row.mean_estimate==2 and row.bias==-3 and row.retained_target_bias==-3
    assert row.mean_error_to_retained==0 and row.variance==2
    assert row.rmse==pytest.approx(np.sqrt(10))
    raw=pd.DataFrame([{**common,'exact_count':0,'estimate':1},{**common,'exact_count':0,'estimate':3}])
    assert np.isnan(aggregate(raw).relative_rmse.iloc[0])


@pytest.mark.escape_integration
def test_full_pipeline_replay_plots_and_corruption(tmp_path,escape_adapter,monkeypatch):
    source=Path(__file__).resolve().parents[1]/'experiments/configs/four_clique_phase06.json'
    config=load_config(source)
    config['graphs']=[{'id':'K4','family':'complete','n':4},
                      {'id':'book2','family':'book','centers':2}]
    config['representative_graph']='K4'
    config['epsilons']=[1,4]
    config['trials']=3
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    output=tmp_path/'results'
    manifest=run_experiment(path,output,escape_adapter)
    assert manifest['graphs']==2 and manifest['cells']==20 and manifest['trials']==60
    assert verify_results(output,replay=True)['replayed']
    with pytest.raises(FileExistsError): run_experiment(path,output,escape_adapter)
    monkeypatch.setenv('MPLCONFIGDIR',str(tmp_path/'mpl'))
    a=plot_results(output,tmp_path/'plot1')
    b=plot_results(output,tmp_path/'plot2')
    assert len(a['files_sha256'])==8 and a==b
    with (output/'trials.csv').open('a') as stream: stream.write('corrupt\n')
    with pytest.raises(ValueError,match='hash mismatch'): verify_results(output)


def test_book_has_expected_cliques():
    from private_graphlets.four_clique_exact import count_four_cliques_bruteforce
    assert count_four_cliques_bruteforce(experiment_graph({'family':'book','centers':6}))==6
