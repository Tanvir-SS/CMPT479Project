"""Bounded NON-PRIVATE ideal-error validation; never overwrites Phase-6 artifacts."""

import argparse
from dataclasses import asdict
from fractions import Fraction
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess

import networkx as nx
import numpy as np
import pandas as pd

from private_graphlets.escape import EscapeAdapter, build_count_four
from private_graphlets.four_clique import (CliqueBudget, allocate_budget, cap_from_reports,
    local_cap_report, simulate_four_cliques, simulation_streams)
from private_graphlets.four_clique_accuracy import (baseline_error, cap_underestimate_probability,
    conditional_error, enumerate_rr_moments, retained_cliques_bruteforce)
from private_graphlets.four_clique_exact import count_four_cliques_bruteforce, ranks
from private_graphlets.four_clique_experiments import (experiment_graph, execute_trial,
    load_config, verify_results)
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import KCoreConfig, kcore_order

PROJECT = Path(__file__).resolve().parents[1]
MASTER_SEED = 2026110609


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seed(domain, case, trial):
    return (MASTER_SEED << 64) | (domain << 48) | (case << 32) | trial


def named_graphs():
    result = {'empty0': SimpleGraph.from_edges(0,[]), 'empty6':SimpleGraph.from_edges(6,[])}
    result.update({f'K{n}':SimpleGraph.from_edges(n,combinations(range(n),2)) for n in (4,5,8)})
    result['triangle'] = SimpleGraph.from_edges(6,combinations(range(3),2))
    result['book6'] = experiment_graph({'family':'book','centers':6})
    for name,p,s in [('sparse8',.2,900101),('dense8',.75,900102)]:
        result[name] = SimpleGraph.from_edges(8,nx.gnp_random_graph(8,p,seed=s).edges())
    return result


def sample_history(graph, epsilon, method, simulation_seed, config):
    """Sample ONLY the actual unchanged O/D stages for independent prediction."""
    b = allocate_budget(epsilon,method['ordering'],method['cap_mode'])
    ro, rd, _, _ = simulation_streams(simulation_seed)
    n = graph.num_vertices
    order = tuple(range(n))
    if n >= 4 and method['ordering'] == 'kcore':
        order = kcore_order(graph,b.ordering,ro,KCoreConfig(**config['kcore'])).order
    cap = method.get('cap',max(0,n-1))
    if n >= 4 and method['cap_mode']=='noisy':
        rank = ranks(order)
        reports = tuple(local_cap_report(v,row,rank,b.cap,rd) for v,row in enumerate(graph.adjacency))
        cap = cap_from_reports(reports,n,b.cap,config['beta'])
    return order, cap, b


def _se(values):
    values = np.asarray(values,dtype=float)
    return float(values.std(ddof=1)/math.sqrt(len(values)))


def _csv(rows,path):
    pd.DataFrame(rows).to_csv(path,index=False,float_format='%.17g')


def reconcile_saved(results, output):
    if not (results/'manifest.json').is_file():
        return {'status':'unavailable','reason':'ignored Phase-6 artifacts are not present; no benchmark rerun'}
    verified = verify_results(results)
    config = load_config(results/'config.json')
    if config != load_config(PROJECT/'experiments/configs/four_clique_phase06.json'):
        raise ValueError('saved and current Phase-6 configurations differ')
    raw = pd.read_csv(results/'trials.csv',dtype={'seed':str},float_precision='round_trip')
    saved_summary = pd.read_csv(results/'summary.csv',float_precision='round_trip')
    refs = {row['graph']:row for row in json.loads((results/'escape_reference.json').read_text())}
    chosen = raw[raw.graph.isin(['empty6','K4','K8','book6','er_dense14']) & raw.epsilon.isin([1.,4.])]
    summaries, replay_count = [],0
    for (name,eps,method_id), cell in chosen.groupby(['graph','epsilon','method'],sort=False):
        gi,mi = int(cell.graph_index.iloc[0]),int(cell.method_index.iloc[0])
        graph, method = experiment_graph(config['graphs'][gi]),config['methods'][mi]
        truth = count_four_cliques_bruteforce(graph)
        assert truth == refs[name]['escape_count'] == int(cell.exact_count.iloc[0])
        assert graph.num_vertices == int(cell.n.iloc[0]) and graph.num_edges == int(cell.m.iloc[0])
        components = []
        fixed = baseline_error(graph,eps) if method['kind']=='baseline' else None
        for i,row in enumerate(cell.to_dict('records')):
            actual_seed = int(row['seed'])
            assert math.isclose(sum(row[k] for k in ('epsilon_O','epsilon_D','epsilon_R','epsilon_C')),eps,rel_tol=1e-14)
            if i<3:
                replayed = execute_trial(graph,eps,method,actual_seed,config)
                assert all(replayed[k] == row[k] for k in replayed if k!='runtime_seconds')
                replay_count += 1
            if fixed is not None:
                components.append((fixed['rr_variance'],0.,0.,0.,truth))
                assert (row['epsilon_O'],row['epsilon_D'],row['epsilon_R'],row['epsilon_C']) == (0,0,eps,0)
            else:
                order,cap,b = sample_history(graph,eps,method,actual_seed,config)
                prediction = conditional_error(graph,order,cap,b.rr,b.count)
                assert cap == row['cap'] and prediction.retained_count == row['retained_count']
                assert prediction.exact_count == row['uncapped_count']
                assert tuple(row[k] for k in ('epsilon_O','epsilon_D','epsilon_R','epsilon_C')) == (b.ordering,b.cap,b.rr,b.count)
                components.append((prediction.rr_variance,prediction.laplace_variance,
                    prediction.clipping_bias_squared,prediction.conditional_bias,prediction.retained_count))
        c = np.asarray(components,dtype=float)
        totals = c[:,:3].sum(axis=1)
        old = saved_summary[(saved_summary.graph==name)&(saved_summary.epsilon==eps)&(saved_summary.method==method_id)].iloc[0]
        summaries.append({'graph':name,'epsilon':eps,'method':method_id,'exact_count':truth,
            'saved_trials':len(cell),'historical_observed_rmse':float(old.rmse),
            'historical_empirical_bias':float(old.bias),'historical_sample_variance':float(old.variance),
            'predicted_rr_variance':float(c[:,0].mean()),'predicted_laplace_variance':float(c[:,1].mean()),
            'predicted_squared_conditional_bias':float(c[:,2].mean()),
            'predicted_squared_mean_bias':float(c[:,3].mean()**2),
            'realized_history_target_variance_ddof0':float(c[:,4].var(ddof=0)),
            'conditional_mse_mean_over_saved_histories':float(totals.mean()),
            'history_prediction_mse_se':_se(totals),
            'predicted_rmse_from_history_mean_mse':float(math.sqrt(totals.mean())),
            'dominant_component':('RR','Laplace','clipping')[int(np.argmax(c[:,:3].mean(axis=0)))],
            'prediction_scope':'exact_baseline' if fixed is not None else 'mean_of_exact_conditional_values_over_100_saved_histories'})
    _csv(summaries,output/'phase06_reconciliation.csv')
    return {'status':'verified_selected','original_verification':verified,'cells':len(summaries),
            'selected_estimates_replayed':replay_count,'source_manifest_sha256':sha(results/'manifest.json'),
            'source_trials_sha256':sha(results/'trials.csv'),'source_summary_sha256':sha(results/'summary.csv')}


def run_validation(output, adapter, *, conditional_trials=4096, history_trials=1024, historical_results=None):
    if any(type(n) is not int or not 2 <= n <= 20_000 for n in (conditional_trials,history_trials)):
        raise ValueError('bounded diagnostic trial counts must be integers in [2,20000]')
    output.mkdir(parents=True,exist_ok=False)
    graphs = named_graphs()
    config = {'master_seed':MASTER_SEED,'conditional_trials':conditional_trials,'history_trials':history_trials,
        'seed_coordinates':'(master<<64)|(domain<<48)|(case<<32)|trial; conditional=1,full=2,prediction=3',
        'conditional_cases':[{'graph':'K4','odds':'2','count':1.}, {'graph':'K5','odds':'2','count':1.},
                             {'graph':'book6','odds':'2','count':1.}, {'graph':'K4','odds':'5/4','count':.25}],
        'history_cases':[{'graph':'K5','epsilon':4.,'cap_mode':'noisy'},
                         {'graph':'book6','epsilon':4.,'cap_mode':'noisy'},
                         {'graph':'book6','epsilon':4.,'cap_mode':'public','cap':3}],
        'kcore':{'psi':.5,'threshold_fraction':.5,'bias_factor':1},'beta':.05,
        'consistency_se_multiplier':6,'small_graph_generation':'sparse8 G(n=8,p=.2,seed900101); dense8 G(n=8,p=.75,seed900102)'}
    (output/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    try:
        exact_rows, evidence = [],[]
        for name,graph in graphs.items():
            native = adapter.run(graph)
            truth = native.counts.connected_four['4-clique']
            assert truth == count_four_cliques_bruteforce(graph)
            evidence.append({'graph':name,'escape_count':truth,'input':native.input_text,
                'output':native.output_text,'stdout':native.stdout,'stderr':native.stderr})
            for label,order in [('ID',tuple(range(graph.num_vertices))),('reverse',tuple(reversed(range(graph.num_vertices))))]:
                for cap in sorted({0,min(2,max(0,graph.num_vertices-1)),min(3,max(0,graph.num_vertices-1)),max(0,graph.num_vertices-1)}):
                    prediction = conditional_error(graph,order,cap,math.log(2),1.)
                    assert prediction.exact_count == truth
                    exact_rows.append({'graph':name,'order':label,**prediction.to_dict()})
        _csv(exact_rows,output/'exact_diagnostics.csv')
        (output/'escape_reference.json').write_text(json.dumps(evidence,indent=2)+'\n')
        conditional_rows, conditional_summary = [],[]
        for case,spec in enumerate(config['conditional_cases']):
            graph = graphs[spec['graph']]
            order,cap = tuple(range(graph.num_vertices)),3
            odds = Fraction(spec['odds']); eta = math.log(float(odds)); count = spec['count']
            b = CliqueBudget(eta+count,0,0,eta,count)
            prediction = conditional_error(graph,order,cap,eta,count)
            exact = enumerate_rr_moments(graph,order,cap,odds=odds,include_unused_pairs=graph.num_vertices<=5)
            assert float(exact.variance) == prediction.rr_variance or math.isclose(float(exact.variance),prediction.rr_variance,rel_tol=1e-13)
            for trial in range(conditional_trials):
                s = seed(1,case,trial)
                run = simulate_four_cliques(graph,b.total,ordering='fixed',cap_mode='public',cap=cap,
                                             public_order=order,budget=b,seed=s)
                conditional_rows.append({'case':case,'graph':spec['graph'],'trial':trial,'seed':str(s),
                    'estimate':run.result.estimate,'exact_count':prediction.exact_count,
                    'retained_count':prediction.retained_count,'epsilon_R':eta,'epsilon_C':count})
            values = np.array([r['estimate'] for r in conditional_rows if r['case']==case])
            variance = prediction.rr_variance+prediction.laplace_variance
            scale = prediction.sensitivity/count
            fourth = float(exact.fourth_central)+6*prediction.rr_variance*prediction.laplace_variance+12*graph.num_vertices*(graph.num_vertices+1)*scale**4
            bias = prediction.conditional_bias
            fourth_error = fourth+4*bias*float(exact.third_central)+6*bias*bias*variance+bias**4
            mean_se = math.sqrt(variance/conditional_trials)
            variance_se = math.sqrt((fourth-(conditional_trials-3)/(conditional_trials-1)*variance**2)/conditional_trials)
            mse_se = math.sqrt((fourth_error-prediction.mse**2)/conditional_trials)
            empirical_mse = float(np.mean((values-prediction.exact_count)**2))
            conditional_summary.append({'case':case,'graph':spec['graph'],'trials':conditional_trials,
                'rr_odds':str(odds),'epsilon_R':eta,'epsilon_C':count,'predicted_mean':prediction.retained_count,
                'observed_mean':float(values.mean()),'analytic_mean_se':mean_se,
                'predicted_variance':variance,'observed_variance_ddof1':float(values.var(ddof=1)),
                'analytic_variance_se':variance_se,'predicted_mse':prediction.mse,'observed_mse':empirical_mse,
                'analytic_mse_se':mse_se,'mean_z':float((values.mean()-prediction.retained_count)/mean_se),
                'variance_z':float((values.var(ddof=1)-variance)/variance_se),
                'mse_z':(empirical_mse-prediction.mse)/mse_se,
                'rr_enumerated_tables':exact.table_count,'rr_enumerated_pairs':exact.enumerated_pair_count,
                'rr_full_pairs':exact.full_pair_count})
        _csv(conditional_rows,output/'conditional_trials.csv'); _csv(conditional_summary,output/'conditional_summary.csv')
        full_rows, prediction_rows, history_summary = [],[],[]
        for case,spec in enumerate(config['history_cases']):
            graph = graphs[spec['graph']]
            method = {'ordering':'kcore','cap_mode':spec['cap_mode']}
            if 'cap' in spec: method['cap']=spec['cap']
            truth = count_four_cliques_bruteforce(graph)
            for trial in range(history_trials):
                s = seed(2,case,trial)
                run = simulate_four_cliques(graph,spec['epsilon'],**method,seed=s,beta=config['beta'],kcore_config=KCoreConfig(**config['kcore']))
                retained = retained_cliques_bruteforce(graph,run.transcript.order,run.transcript.cap)[1]
                full_rows.append({'case':case,'graph':spec['graph'],'trial':trial,'seed':str(s),'estimate':run.result.estimate,
                    'exact_count':truth,'retained_count':retained,'cap':run.transcript.cap,'order':json.dumps(run.transcript.order)})
                prediction_seed = seed(3,case,trial)
                order,cap,b = sample_history(graph,spec['epsilon'],method,prediction_seed,config)
                prediction = conditional_error(graph,order,cap,b.rr,b.count)
                prediction_rows.append({'case':case,'graph':spec['graph'],'trial':trial,'seed':str(prediction_seed),
                    'order':json.dumps(order),**prediction.to_dict()})
            full = pd.DataFrame([r for r in full_rows if r['case']==case])
            pred = pd.DataFrame([r for r in prediction_rows if r['case']==case])
            squared_error = (full.estimate-truth)**2
            combined_se = math.hypot(_se(squared_error),_se(pred.mse))
            row = {'case':case,'graph':spec['graph'],'cap_mode':spec['cap_mode'],'epsilon':spec['epsilon'],
                'full_trials':history_trials,'prediction_trials':history_trials,'observed_mean':float(full.estimate.mean()),
                'observed_bias':float(full.estimate.mean()-truth),'observed_variance_ddof1':float(full.estimate.var(ddof=1)),
                'observed_mse':float(squared_error.mean()),'observed_mse_se':_se(squared_error),
                'predicted_mse':float(pred.mse.mean()),'prediction_mse_se':_se(pred.mse),'combined_mse_se':combined_se,
                'mse_discrepancy_z':float((squared_error.mean()-pred.mse.mean())/combined_se),
                'mean_conditional_bias':float(pred.conditional_bias.mean()),
                'squared_mean_conditional_bias':float(pred.conditional_bias.mean()**2),
                'history_target_variance_ddof0':float(pred.retained_count.var(ddof=0)),
                'distinct_prediction_orders':int(pred.order.nunique()),'distinct_prediction_caps':int(pred.cap.nunique()),
                'prediction_clipping_fraction':float(np.mean(pred.clipping_bias_squared>0))}
            row.update({f'predicted_{k}':float(pred[k].mean()) for k in ('rr_variance','laplace_variance','clipping_bias_squared')})
            history_summary.append(row)
        _csv(full_rows,output/'unconditional_trials.csv'); _csv(prediction_rows,output/'history_predictions.csv')
        _csv(history_summary,output/'unconditional_summary.csv')
        cap_rows = [{'graph':name,**cap_underestimate_probability(g,tuple(range(g.num_vertices)),1.,.05)} for name,g in graphs.items()]
        _csv(cap_rows,output/'cap_tails.csv')
        reconciliation = reconcile_saved(historical_results,output) if historical_results is not None else {'status':'not_requested'}
        warning = [r['case'] for r in conditional_summary if max(abs(r[k]) for k in ('mean_z','variance_z','mse_z'))>6]
        history_warning = [r['case'] for r in history_summary if abs(r['mse_discrepancy_z'])>6]
        # Diagnostics record discrepancies instead of misclassifying formulas via noisy tests.
        report = {'status':'complete','result_type':'nonprivate_ideal_error_validation','graphs':len(graphs),
            'exact_rows':len(exact_rows),'conditional_cases':len(conditional_summary),'history_cases':len(history_summary),
            'conditional_trials':len(conditional_rows),'full_unconditional_trials':len(full_rows),
            'independent_history_predictions':len(prediction_rows),'conditional_attention_cases':warning,
            'unconditional_attention_cases':history_warning,'historical_reconciliation':reconciliation,
            'platform':platform.platform(),'python':platform.python_version(),'numpy':np.__version__,
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PROJECT,text=True).strip(),
            'source_sha256':{str(p.relative_to(PROJECT)):sha(p) for p in [Path(__file__).resolve(),
                PROJECT/'src/private_graphlets/four_clique_accuracy.py',PROJECT/'src/private_graphlets/four_clique.py',
                PROJECT/'src/private_graphlets/kcore.py',PROJECT/'src/private_graphlets/randomized_response.py',
                PROJECT/'src/private_graphlets/four_clique_baseline.py',PROJECT/'experiments/configs/four_clique_phase06.json',PROJECT/'requirements.lock']},
            'escape_executable_sha256':sha(adapter.executable),
            'escape_build':json.loads((adapter.executable.parent/'build.json').read_text()),
            'files_sha256':{p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
        (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        return report
    except Exception as exc:
        (output/'failure.json').write_text(json.dumps({'status':'failed','error':str(exc)})+'\n')
        raise


def verify_artifacts(output):
    report = json.loads((output/'manifest.json').read_text())
    if report['status']!='complete' or (output/'failure.json').exists(): raise ValueError('incomplete diagnostic')
    for name,digest in report['files_sha256'].items():
        if sha(output/name)!=digest: raise ValueError(f'changed diagnostic artifact: {name}')
    config = json.loads((output/'config.json').read_text())
    for filename,summary_name in [('conditional_trials.csv','conditional_summary.csv'),('unconditional_trials.csv','unconditional_summary.csv')]:
        raw = pd.read_csv(output/filename,dtype={'seed':str},float_precision='round_trip')
        summary = pd.read_csv(output/summary_name,float_precision='round_trip')
        assert not raw.seed.duplicated().any()
        for row in summary.to_dict('records'):
            cell = raw[raw.case==row['case']]
            mse = float(np.mean((cell.estimate-cell.exact_count)**2))
            assert math.isclose(mse,row['observed_mse'],rel_tol=1e-13,abs_tol=1e-13)
    predicted = pd.read_csv(output/'history_predictions.csv',float_precision='round_trip',dtype={'seed':str})
    assert np.allclose(predicted.mse,predicted.rr_variance+predicted.laplace_variance+predicted.clipping_bias_squared,rtol=1e-14)
    assert not set(predicted.seed)&set(raw.seed)
    return {'status':'verified','graphs':report['graphs'],'artifact_count':len(report['files_sha256'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['run','verify'])
    parser.add_argument('--output',type=Path,default=PROJECT/'build/phase09/validation')
    parser.add_argument('--escape-root',type=Path)
    parser.add_argument('--conditional-trials',type=int,default=4096)
    parser.add_argument('--history-trials',type=int,default=1024)
    parser.add_argument('--historical-results',type=Path,default=PROJECT/'experiments/results/four_clique_phase06')
    args = parser.parse_args()
    if args.command=='verify':
        print(json.dumps(verify_artifacts(args.output))); return
    if args.output.exists(): parser.error('output exists; choose a new --output')
    adapter = EscapeAdapter(build_count_four(args.escape_root,build_dir=args.output.parent/'escape-accuracy'))
    report = run_validation(args.output,adapter,conditional_trials=args.conditional_trials,
        history_trials=args.history_trials,historical_results=args.historical_results)
    print(json.dumps({k:report[k] for k in ('status','graphs','conditional_trials','full_unconditional_trials','independent_history_predictions','conditional_attention_cases','unconditional_attention_cases')}))


if __name__=='__main__': main()
