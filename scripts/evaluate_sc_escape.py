"""Separate, resumable non-private SC-ESCAPE evaluation: 24 smoke + 4,800 main.

Reuse Checkpoint 21's input/truth validation and seed encoding, never its estimator.
Every attempt is journaled; failed/uncertain attempts require review, not retries.
"""

import argparse
from datetime import datetime, timezone
import fcntl
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import time
import traceback

import numpy as np
import pandas as pd

import evaluate_four_path as prior
from private_graphlets.four_path_sc_escape import SCEscapeBudget, estimate_sc_escape
from private_graphlets.graph_datasets import PROJECT, digest
from private_graphlets.randomized_response import rr_parameters

atomic_json = prior.atomic_json
seed_for = prior.seed_for
coordinates = prior.coordinates
CONFIG = PROJECT / 'experiments/configs/four_path_sc_escape_six_datasets.json'
MAIN = PROJECT / 'experiments/results/four_path_sc_escape_six_datasets'
SMOKE = PROJECT / 'build/phase33/smoke'
FRACTIONS = {'degree': .1, 'rr': .2, 'product': .3, 'triangle': .3}
STAGES = {'epsilon_D': 'degree', 'epsilon_R': 'rr', 'epsilon_S': 'product', 'epsilon_T': 'triangle'}
SOURCE = ['four_path_sc_escape.py', 'randomized_response.py', 'noise.py', 'graph.py',
          'graph_datasets.py', 'escape.py', 'references.py']


def budget_for(epsilon):
    budget = SCEscapeBudget(**{k: epsilon*v for k, v in FRACTIONS.items()})
    if not math.isclose(budget.total, epsilon, rel_tol=1e-15):
        raise ValueError('budget accounting mismatch')
    if not 0 < rr_parameters(budget.rr).flip_probability < .5:
        raise ValueError('RR probability lost its signal')
    return budget


def load_inputs(smoke=False):
    # Read-only existing validation: pins/mappings/cache/native output, no recount.
    old, graphs, truth = prior.load_inputs(prior.DEFAULT_CONFIG)
    config = json.loads(CONFIG.read_text())
    expected_graphs = [{**g, 'public_max_degree': g['n']-1,
                        'bound_source': 'public_vertex_count_n_minus_1; no documented tighter public bound'}
                       for g in old['graphs']]
    if (config['graphs'] != expected_graphs or config['trials'] != 200
            or config['epsilons'] != [.5, 1., 2., 4.] or config['stage_fractions'] != FRACTIONS
            or config['master_seed'] != 202611223301 or config['method'] != 'sc_escape'
            or config['purpose'] != 'main' or config['variance_ddof'] != 0
            or config['seed_rule'] != '(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial'
            or config['stream_order'] != ['degree', 'rr', 'product', 'triangle']
            or config['budget_accounting'] != '2*degree+rr+product+triangle'):
        raise ValueError('fixed configuration changed')
    for graph, spec in zip(graphs, config['graphs']):
        if (graph.num_vertices, graph.num_edges) != (spec['n'], spec['m']):
            raise ValueError('graph dimensions changed')
        if any(len(row) > spec['public_max_degree'] for row in graph.adjacency):
            raise ValueError('public bound violated')
    for epsilon in config['epsilons']:
        budget_for(epsilon)
    if smoke:
        config.update(trials=1, master_seed=202611223300, purpose='smoke')
    return config, graphs, truth


def provenance():
    return {'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PROJECT, text=True).strip(),
            'python': sys.version, 'platform': platform.platform(), 'hardware': platform.machine(),
            'dependencies': {k: importlib.metadata.version(k) for k in ['numpy', 'pandas', 'networkx']},
            'runner_sha256': digest(Path(__file__)), 'input_validator_sha256': digest(Path(prior.__file__)),
            'config_sha256': digest(CONFIG), 'prior_config_sha256': digest(prior.DEFAULT_CONFIG),
            'mechanism_sha256': {name: digest(PROJECT/'src/private_graphlets'/name) for name in SOURCE},
            'truth_cache_sha256': digest(PROJECT/'experiments/results/p4_standardized_ground_truth/ground_truth.csv'),
            'dataset_manifest_sha256': digest(PROJECT/'data/processed/graph_manifest.json'),
            'reference_manifest_sha256': digest(PROJECT/'third_party/references.json'),
            'submodules': subprocess.check_output(['git', 'submodule', 'status'], cwd=PROJECT, text=True).strip()}


def validate_provenance(output):
    if json.loads((output/'provenance.json').read_text()) != provenance():
        raise ValueError('source/environment provenance differs; refuse resume/verification')


def identity(config, coordinate):
    gi, ei, trial = coordinate
    spec, epsilon = config['graphs'][gi], config['epsilons'][ei]
    budget = budget_for(epsilon)
    return {'graph': spec['id'], 'n': spec['n'], 'm': spec['m'],
            'graph_index': gi, 'epsilon_index': ei, 'trial': trial,
            'trial_id': f"{config['purpose']}:{gi}:{ei}:{trial}", 'method': 'sc_escape',
            'epsilon': epsilon, 'epsilon_total': budget.total,
            **{k: getattr(budget, v) for k, v in STAGES.items()},
            'public_max_degree': spec['public_max_degree'], 'bound_source': spec['bound_source'],
            'seed': str(seed_for(config['master_seed'], gi, ei, trial)),
            'exact_count': spec['expected_p4'], 'privacy_status': 'experimental_unverified'}


def read_rows(db, config):
    stored = db.execute('SELECT ordinal,payload FROM trials ORDER BY ordinal').fetchall()
    jobs, rows = coordinates(config), []
    if len(stored) > len(jobs):
        raise ValueError('too many rows')
    for i, (ordinal, payload) in enumerate(stored):
        row = json.loads(payload)
        expected = identity(config, jobs[i])
        if ordinal != i or any(row.get(k) != v for k, v in expected.items()):
            raise ValueError('saved coordinates/configuration/seed mismatch')
        for key in ['estimate', 'degree_product_estimate', 'triangle_estimate', 'runtime_seconds']:
            if not math.isfinite(row[key]):
                raise ValueError('nonfinite saved output')
        if row['runtime_seconds'] < 0 or not math.isclose(row['estimate'],
                math.fsum((row['degree_product_estimate'], -3*row['triangle_estimate'])),
                rel_tol=1e-15, abs_tol=1e-12):
            raise ValueError('runtime/aggregation mismatch')
        rows.append(row)
    attempts = db.execute('SELECT ordinal,status FROM attempts ORDER BY ordinal').fetchall()
    complete = [ordinal for ordinal, status in attempts if status == 'complete']
    if complete != list(range(len(rows))):
        raise ValueError('attempt journal disagrees with saved results')
    if len({row['seed'] for row in rows}) != len(rows):
        raise ValueError('duplicate seed')
    return rows


def summarize(rows):
    records = []
    if not rows:
        return pd.DataFrame()
    for _, cell in pd.DataFrame(rows).groupby(['graph_index', 'epsilon_index'], sort=True):
        first = cell.iloc[0]
        x = cell.estimate.to_numpy(dtype=float)
        error = x - first.exact_count
        mse, variance, bias = float(np.mean(error**2)), float(np.var(x, ddof=0)), float(np.mean(error))
        if not math.isclose(mse, variance+bias*bias, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError('population MSE identity failed')
        records.append({'graph': first.graph, 'n': int(first.n), 'm': int(first.m),
                        'method': 'sc_escape', 'epsilon': first.epsilon, 'trials': len(cell),
                        'exact_count': int(first.exact_count), 'public_max_degree': int(first.public_max_degree),
                        **{k: first[k] for k in STAGES}, 'mean_estimate': float(np.mean(x)),
                        'bias': bias, 'variance': variance, 'variance_ddof': 0, 'mse': mse,
                        'rmse': math.sqrt(mse), 'mae': float(np.mean(np.abs(error))),
                        'mean_relative_error': float(np.mean(np.abs(error)))/first.exact_count if first.exact_count else math.nan,
                        'relative_rmse': math.sqrt(mse)/first.exact_count if first.exact_count else math.nan,
                        'mean_runtime_seconds': float(cell.runtime_seconds.mean()),
                        'runtime_total_seconds': float(cell.runtime_seconds.sum()),
                        'negative_estimates': int((x < 0).sum()),
                        'fractional_estimates': int((x != np.trunc(x)).sum())})
    return pd.DataFrame(records)


def export(db, config, output):
    rows = read_rows(db, config)
    for name, frame in [('trials.csv', pd.DataFrame(rows)), ('summary.csv', summarize(rows))]:
        temporary = output/(name+'.tmp')
        frame.to_csv(temporary, index=False, float_format='%.17g')
        temporary.replace(output/name)
    problems = [{'ordinal': i, 'status': status, 'details': json.loads(payload)} for i, status, payload in
                db.execute("SELECT ordinal,status,payload FROM attempts WHERE status!='complete' ORDER BY ordinal")]
    atomic_json(output/'failures.json', problems)
    target = len(coordinates(config))
    status = 'blocked' if problems else ('complete' if len(rows) == target else 'partial')
    result = {'status': status, 'completed_trials': len(rows), 'target_trials': target,
              'remaining_trials': target-len(rows), 'failed_or_uncertain_attempts': len(problems),
              'updated_utc': datetime.now(timezone.utc).isoformat(),
              'result_type': 'nonprivate_public_graph_evaluation',
              'files_sha256': {name: digest(output/name) for name in
                               ['config.json', 'provenance.json', 'escape_ground_truth.json',
                                'trials.csv', 'summary.csv', 'failures.json']}}
    atomic_json(output/'manifest.json', result)
    return result


def run(output, smoke=False, resume=False, max_new_trials=None):
    if max_new_trials is not None and max_new_trials < 1:
        raise ValueError('max-new-trials must be positive')
    config, graphs, truth = load_inputs(smoke)
    exists = output.exists()
    if exists and not resume:
        raise FileExistsError('output exists; use --resume')
    if not exists:
        output.mkdir(parents=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if exists:
            if json.loads((output/'config.json').read_text()) != config:
                raise ValueError('resume configuration differs')
            validate_provenance(output)
            if json.loads((output/'escape_ground_truth.json').read_text()) != truth:
                raise ValueError('truth differs')
        else:
            atomic_json(output/'config.json', config)
            atomic_json(output/'provenance.json', provenance())
            atomic_json(output/'escape_ground_truth.json', truth)
        with sqlite3.connect(output/'trials.sqlite3', timeout=0) as db:
            db.execute('CREATE TABLE IF NOT EXISTS trials (ordinal INTEGER PRIMARY KEY,payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS attempts (ordinal INTEGER PRIMARY KEY,status TEXT NOT NULL,payload TEXT NOT NULL)')
            db.commit()
            saved = read_rows(db, config)
            if db.execute("SELECT COUNT(*) FROM attempts WHERE status!='complete'").fetchone()[0]:
                export(db, config, output)
                raise RuntimeError('failed/uncertain attempt preserved; no automatic retry')
            start, jobs = len(saved), coordinates(config)
            stop = len(jobs) if max_new_trials is None else min(len(jobs), start+max_new_trials)
            try:
                for ordinal in range(start, stop):
                    gi, ei, trial = jobs[ordinal]
                    row = identity(config, jobs[ordinal])
                    db.execute('INSERT INTO attempts VALUES (?,?,?)',
                               (ordinal, 'started', json.dumps(row, allow_nan=False)))
                    db.commit()
                    try:
                        budget = budget_for(row['epsilon'])
                        begin = time.perf_counter()
                        result = estimate_sc_escape(graphs[gi], budget=budget,
                                                    public_max_degree=row['public_max_degree'], seed=int(row['seed']))
                        elapsed = time.perf_counter()-begin
                        if result.budget != budget or result.public_max_degree != row['public_max_degree']:
                            raise AssertionError('estimator configuration mismatch')
                        row.update(estimate=result.estimate, degree_product_estimate=result.degree_product_estimate,
                                   triangle_estimate=result.triangle_estimate, runtime_seconds=elapsed)
                        payload = json.dumps(row, allow_nan=False)
                        db.execute('INSERT INTO trials VALUES (?,?)', (ordinal, payload))
                        db.execute("UPDATE attempts SET status='complete',payload=? WHERE ordinal=?", (payload, ordinal))
                        db.commit()
                    except BaseException as exc:
                        db.rollback()
                        failure = {**identity(config, jobs[ordinal]), 'error_type': type(exc).__name__,
                                   'error': str(exc), 'traceback': traceback.format_exc()}
                        db.execute("UPDATE attempts SET status='failed',payload=? WHERE ordinal=?",
                                   (json.dumps(failure), ordinal))
                        db.commit()
                        raise
                    if trial == config['trials']-1:
                        state = export(db, config, output)
                        print(json.dumps({k: state[k] for k in ['status', 'completed_trials', 'remaining_trials']}), flush=True)
            finally:
                state = export(db, config, output)
            return {**state, 'new_trials_this_invocation': stop-start}


def verify(output, smoke=False):
    config, _, truth = load_inputs(smoke)
    if json.loads((output/'config.json').read_text()) != config:
        raise ValueError('saved configuration mismatch')
    validate_provenance(output)
    if json.loads((output/'escape_ground_truth.json').read_text()) != truth:
        raise ValueError('saved truth mismatch')
    manifest = json.loads((output/'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        if digest(output/name) != expected:
            raise ValueError('artifact hash changed')
    with sqlite3.connect(f'file:{output}/trials.sqlite3?mode=ro', uri=True) as db:
        rows = read_rows(db, config)
        failures = db.execute("SELECT COUNT(*) FROM attempts WHERE status!='complete'").fetchone()[0]
    if not rows:
        raise ValueError('no completed rows to verify')
    raw = pd.read_csv(output/'trials.csv', dtype={'seed': str}, float_precision='round_trip')
    pd.testing.assert_frame_equal(raw, pd.DataFrame(rows), check_dtype=False, check_exact=True)
    summary = pd.read_csv(output/'summary.csv', float_precision='round_trip')
    pd.testing.assert_frame_equal(summary, summarize(rows), check_dtype=False, rtol=1e-12, atol=1e-12)
    expected_status = 'blocked' if failures else ('complete' if len(rows) == len(coordinates(config)) else 'partial')
    if (manifest['completed_trials'] != len(rows) or manifest['status'] != expected_status
            or manifest['failed_or_uncertain_attempts'] != failures
            or manifest['remaining_trials'] != len(coordinates(config))-len(rows)):
        raise ValueError('manifest totals mismatch')
    result = {'status': 'verified', 'study_status': expected_status, 'trials': len(rows),
              'cells': len(summary), 'remaining_trials': len(coordinates(config))-len(rows),
              'failed_or_uncertain_attempts': failures, 'population_variance_identity': True,
              'verification_mode': 'saved_records_only_no_estimator_replay'}
    atomic_json(output/'verification.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'run', 'verify'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--max-new-trials', type=int)
    args = parser.parse_args()
    output = args.output or (SMOKE if args.smoke else MAIN)
    if args.command == 'check':
        config, _, truth = load_inputs(args.smoke)
        result = {'planned_trials': len(coordinates(config)), 'graphs': config['graphs'],
                  'budgets': [{'epsilon': eps, **{k: getattr(budget_for(eps), v) for k, v in STAGES.items()}}
                              for eps in config['epsilons']], 'truth': [r['exact_count'] for r in truth]}
    elif args.command == 'verify':
        result = verify(output, args.smoke)
    else:
        result = run(output, args.smoke, args.resume, args.max_new_trials)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
