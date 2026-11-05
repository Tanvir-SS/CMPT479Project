"""Bounded non-private evaluation infrastructure, integrity and deterministic replay."""

import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from private_graphlets.four_path_experiments import (
    aggregate, experiment_seed, load_config, run_experiment, verify_results,
)


PROJECT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config_path(tmp_path):
    config = json.loads((PROJECT/'experiments/configs/four_path_phase12_validation.json').read_text())
    config['trials'] = config['prediction_trials'] = 3
    config['graphs'] = [config['graphs'][0], config['graphs'][-1]]
    path = tmp_path/'config.json'
    path.write_text(json.dumps(config))
    return path


def test_round_trip_schema_metrics_and_replay(config_path, tmp_path):
    output = tmp_path/'result'
    manifest = run_experiment(config_path, output)
    assert manifest['result_type'] == 'nonprivate_synthetic_evaluation'
    assert manifest['full_trials'] == manifest['prediction_trials'] == 6
    assert verify_results(output, replay=True) == {'status': 'verified', 'graphs': 2,
        'full_trials': 6, 'prediction_trials': 6, 'replayed': True}
    full = pd.read_csv(output/'evaluation_trials.csv', dtype={'seed': str}, float_precision='round_trip')
    pred = pd.read_csv(output/'prediction_trials.csv', dtype={'seed': str}, float_precision='round_trip')
    assert not set(full.seed) & set(pred.seed)
    summary = pd.read_csv(output/'summary.csv', float_precision='round_trip')
    assert (summary.empirical_mse >= 0).all() and (summary.se_mse >= 0).all()
    for path in (output/'mechanism_outputs').glob('*.jsonl'):
        for line in path.read_text().splitlines():
            release = json.loads(line)
            assert set(release) == {'result', 'transcript'}
            assert set(release['transcript']) == {'noisy_degrees', 'ordering', 'order', 'cap_reports',
                'cap', 'rr_upper', 'local_triangle_reports'}
            assert not {'seed', 'exact_four_paths', 'missed_triangles', 'mse'} & set(release['result'])
    with pytest.raises(FileExistsError): run_experiment(config_path, output)
    # Repeated independent run is deterministic apart from recorded timings/provenance.
    second = tmp_path/'second'
    run_experiment(config_path, second)
    for path in (output/'mechanism_outputs').glob('*'):
        assert path.read_bytes() == (second/'mechanism_outputs'/path.name).read_bytes()
    again = pd.read_csv(second/'prediction_trials.csv', dtype={'seed': str}, float_precision='round_trip')
    pd.testing.assert_frame_equal(pred.drop(columns=['sampling_seconds', 'analytical_seconds']),
                                  again.drop(columns=['sampling_seconds', 'analytical_seconds']))


@pytest.mark.parametrize('file', ['config.json', 'summary.csv', 'prediction_trials.csv',
                                 'evaluation_trials.csv', 'graphs/path.edges', 'mechanism_outputs/path.jsonl'])
def test_hash_corruption_detected(config_path, tmp_path, file):
    output = tmp_path/'result'
    run_experiment(config_path, output)
    with (output/file).open('a') as stream: stream.write('corrupted')
    with pytest.raises(ValueError, match='hash mismatch'): verify_results(output)


def test_missing_artifact_detected(config_path, tmp_path):
    output = tmp_path/'result'
    run_experiment(config_path, output)
    (output/'summary.csv').unlink()
    with pytest.raises(ValueError, match='inventory'): verify_results(output)


@pytest.mark.parametrize('key,value', [('trials', 1), ('trials', 501), ('prediction_trials', True),
    ('master_seed', -1), ('beta', True), ('beta', 1), ('uncertainty_multiplier', 0),
    ('max_relative_se', float('nan')), ('experiment_id', '../bad')])
def test_invalid_config(config_path, key, value):
    config = json.loads(config_path.read_text())
    config[key] = value
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError): load_config(config_path)


def test_seed_domains():
    seeds = [experiment_seed(91, g, s, t) for g in range(4)
             for s in ('full', 'prediction') for t in range(300)]
    assert len(set(seeds)) == len(seeds)
    assert experiment_seed(91, 2, 'full', 4) == experiment_seed(91, 2, 'full', 4)
    with pytest.raises(ValueError): experiment_seed(1, 0, 'bad', 0)


def test_script_run_and_verify(config_path, tmp_path):
    output = tmp_path/'cli'
    script = PROJECT/'scripts/run_four_path_experiments.py'
    ran = subprocess.run([sys.executable, str(script), 'run', '--config', str(config_path),
                          '--output', str(output)], capture_output=True, text=True)
    assert ran.returncode == 0, ran.stderr
    verified = subprocess.run([sys.executable, str(script), 'verify', '--results', str(output),
                               '--replay'], capture_output=True, text=True)
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)['replayed']


def test_metrics_uncertainty_is_not_tuned(config_path, tmp_path):
    output = tmp_path/'run'
    run_experiment(config_path, output)
    config = load_config(config_path)
    full = pd.read_csv(output/'evaluation_trials.csv', float_precision='round_trip')
    pred = pd.read_csv(output/'prediction_trials.csv', float_precision='round_trip')
    info = json.loads((output/'graph_evaluation.json').read_text())
    summary = aggregate(full, pred, info, config)
    for row in summary.to_dict('records'):
        errors = full.loc[full.graph == row['graph'], 'estimate']-info[row['graph']]['exact_four_paths']
        assert row['empirical_mse'] == pytest.approx((errors**2).mean())
        assert row['se_mse'] == pytest.approx((errors**2).std(ddof=1)/(len(errors)**.5))
        assert row['within_predeclared_tolerance'] == (abs(row['mse_discrepancy']) <= config['uncertainty_multiplier']*row['combined_se'])
