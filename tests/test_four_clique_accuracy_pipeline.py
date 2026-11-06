"""Small real-ESCAPE diagnostic round trip, replay, and artifact integrity checks."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from private_graphlets.four_clique import CliqueBudget, simulate_four_cliques


def runner():
    path = Path(__file__).resolve().parents[1]/'scripts/validate_four_clique_accuracy.py'
    spec = importlib.util.spec_from_file_location('accuracy_diagnostic_runner',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_diagnostic_randomness_domains_and_bounded_trial_validation(tmp_path):
    module = runner()
    values = {module.seed(domain,case,trial) for domain in (1,2,3)
              for case in range(4) for trial in range(32)}
    assert len(values) == 3*4*32
    with pytest.raises(ValueError,match='bounded diagnostic'):
        module.run_validation(tmp_path/'invalid',None,conditional_trials=1)
    assert not (tmp_path/'invalid').exists()
    assert module.reconcile_saved(tmp_path/'absent',tmp_path)['status'] == 'unavailable'


@pytest.mark.escape_integration
def test_small_diagnostic_saved_artifacts_replay_and_corruption(tmp_path,escape_adapter):
    module = runner()
    output = tmp_path/'diagnostic'
    manifest = module.run_validation(output,escape_adapter,conditional_trials=16,history_trials=8)
    assert manifest['graphs'] == 9 and manifest['exact_rows'] == 64
    assert manifest['conditional_trials'] == 64 and manifest['full_unconditional_trials'] == 24
    assert manifest['independent_history_predictions'] == 24
    assert module.verify_artifacts(output)['status'] == 'verified'
    with pytest.raises(FileExistsError):
        module.run_validation(output,escape_adapter,conditional_trials=16,history_trials=8)
    raw = pd.read_csv(output/'conditional_trials.csv',dtype={'seed':str},float_precision='round_trip')
    row = raw.iloc[0]
    budget = CliqueBudget(row.epsilon_R+row.epsilon_C,0,0,row.epsilon_R,row.epsilon_C)
    replay = simulate_four_cliques(module.named_graphs()[row.graph],budget.total,ordering='fixed',
        cap_mode='public',cap=3,public_order=range(4),budget=budget,seed=int(row.seed))
    assert replay.result.estimate == row.estimate
    predicted = pd.read_csv(output/'history_predictions.csv',dtype={'seed':str},float_precision='round_trip')
    full = pd.read_csv(output/'unconditional_trials.csv',dtype={'seed':str})
    assert not (set(raw.seed)&set(full.seed) or set(raw.seed)&set(predicted.seed) or set(full.seed)&set(predicted.seed))
    summaries = pd.read_csv(output/'unconditional_summary.csv',float_precision='round_trip')
    for summary in summaries.to_dict('records'):
        cell = predicted[predicted.case==summary['case']]
        assert summary['predicted_mse'] == pytest.approx(float(cell.mse.mean()))
        assert summary['predicted_clipping_bias_squared'] == pytest.approx(
            summary['squared_mean_conditional_bias']+summary['history_target_variance_ddof0'])
    native = json.loads((output/'escape_reference.json').read_text())
    assert len(native) == 9 and all(row['output'] and row['input'] for row in native)
    with (output/'conditional_trials.csv').open('a') as stream: stream.write('corrupted\n')
    with pytest.raises(ValueError,match='changed diagnostic artifact'):
        module.verify_artifacts(output)
