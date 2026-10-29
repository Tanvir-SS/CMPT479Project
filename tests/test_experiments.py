"""Metric definitions, reproducibility, experiment evidence and saved-data plots."""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from private_graphlets.exact import count_three_stars
from private_graphlets.experiments import (
    aggregate_trials, generate_graph, ideal_graph_variance, load_config,
    run_experiment, summarize, trial_rng, verify_results,
)
from private_graphlets.three_star import corrected_local_stars


CONFIG_PATH = Path(__file__).resolve().parents[1] / "experiments/configs/three_star_phase04.json"


def tiny_config():
    config = json.loads(CONFIG_PATH.read_text())
    config.update(trials=5, epsilons=[0.5, 2.0], representative_graph="complete_n3")
    config["graphs"] = [config["graphs"][0], config["graphs"][12]]
    return config


def test_metric_definitions_with_hand_computed_values():
    result = summarize([-1, 1, 3], truth=1, runtimes=[0.1, 0.2, 0.3], analytic_variance=4)
    assert result["mean_estimate"] == 1
    assert result["empirical_bias"] == 0
    assert result["sample_std"] == 2
    assert result["sample_variance"] == 4
    assert result["mae"] == pytest.approx(4/3)
    assert result["rmse"] == pytest.approx(math.sqrt(8/3))
    assert result["relative_mae"] == result["mae"]
    assert result["relative_rmse"] == result["rmse"]
    assert result["negative_trials"] == 1
    assert result["mechanism_seconds_total"] == pytest.approx(0.6)
    assert result["analytic_mean_se"] == pytest.approx(math.sqrt(4/3))


def test_bias_and_mse_variance_identity():
    result = summarize([-4, 3, 10, 19], truth=5, runtimes=[0]*4, analytic_variance=2)
    assert result["empirical_bias"] == 2
    assert result["relative_bias"] == 0.4
    assert result["rmse"]**2 == pytest.approx(3/4*result["sample_variance"] + result["empirical_bias"]**2)


def test_zero_truth_has_undefined_relative_metrics():
    result = summarize([-3, 1], truth=0, runtimes=[0, 0], analytic_variance=10)
    assert not result["relative_error_defined"]
    for name in ("relative_bias", "relative_mae", "relative_rmse"):
        assert math.isnan(result[name])
    assert result["mae"] == 2
    assert result["empirical_bias"] == -1


@pytest.mark.parametrize("values,timings", [([1], [0]), ([1, math.nan], [0, 0]),
                                          ([1, 2], [-1, 0]), ([1, 2], [0]),
                                          ([1, math.inf], [0, 0])])
def test_invalid_trials_are_not_silently_dropped(values, timings):
    with pytest.raises(ValueError):
        summarize(values, 0, timings, 1)


def test_independent_stream_keys_and_exact_replay():
    keys = [(g, e, t) for g in range(3) for e in range(5) for t in range(500)]
    first = [tuple(trial_rng(202610280400, *key).random(2)) for key in keys]
    assert len(set(first)) == len(keys)
    key = (2, 4, 499)
    np.testing.assert_array_equal(trial_rng(7, *key).laplace(size=50), trial_rng(7, *key).laplace(size=50))
    assert not np.array_equal(trial_rng(7, *key).random(5), trial_rng(8, *key).random(5))


def test_frozen_configuration_covers_scope():
    config = load_config(CONFIG_PATH)
    assert config["epsilons"] == [0.25, 0.5, 1, 2, 4]
    assert config["trials"] == 500
    assert len(config["graphs"]) == 15
    assert {g["family"] for g in config["graphs"]} == {
        "star", "erdos_renyi", "barabasi_albert", "stochastic_block", "complete"}
    for spec in config["graphs"]:
        graph = generate_graph(spec)
        assert graph == generate_graph(spec)
        assert graph.num_vertices <= 100
    assert count_three_stars(generate_graph(config["graphs"][12])) == 0


@pytest.mark.parametrize("change", ["epsilon_zero", "duplicate_epsilon", "missing_graph_seed",
                                    "duplicate_id", "unsafe_id", "trials", "asymmetric_sbm",
                                    "probability", "unknown_key", "oversize", "bad_m"])
def test_bad_config_rejected(tmp_path, change):
    config = json.loads(CONFIG_PATH.read_text())
    if change == "epsilon_zero":
        config["epsilons"][0] = 0
    elif change == "duplicate_epsilon":
        config["epsilons"].append(config["epsilons"][0])
    elif change == "missing_graph_seed":
        del config["graphs"][3]["seed"]
    elif change == "duplicate_id":
        config["graphs"][1]["id"] = config["graphs"][0]["id"]
    elif change == "unsafe_id":
        config["graphs"][0]["id"] = "../escape"
    elif change == "trials":
        config["trials"] = 1
    elif change == "asymmetric_sbm":
        config["graphs"][9]["p"][0][1] = 0.2
    elif change == "probability":
        config["graphs"][3]["p"] = 1.1
    elif change == "unknown_key":
        config["silent_clip"] = True
    elif change == "oversize":
        config["graphs"][0]["n"] = 1001
    else:
        config["graphs"][6]["m"] = 30
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError):
        load_config(path)


@pytest.mark.parametrize("epsilon", [0.25, 0.5, 1, 2, 4])
def test_analytic_variance_against_independent_quadrature(epsilon):
    graph = generate_graph({"id": "star", "family": "star", "n": 9})
    b = 2/epsilon
    nodes, weights = np.polynomial.laguerre.laggauss(4)
    integral = 0
    for neighbors in graph.adjacency:
        d = len(neighbors)
        plus = corrected_local_stars(d + b*nodes, b) - math.comb(d, 3)
        minus = corrected_local_stars(d - b*nodes, b) - math.comb(d, 3)
        integral += np.dot(weights, (plus**2 + minus**2)/2)
    assert ideal_graph_variance(graph, epsilon) == pytest.approx(integral, rel=2e-12)


@pytest.mark.escape_integration
def test_saved_pipeline_replay_metrics_plots_and_corruption(tmp_path, escape_adapter, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(tiny_config()))
    output = tmp_path / "results"
    run_experiment(config_path, output, escape_adapter)
    verification = verify_results(output, replay=True)
    assert verification["trials"] == 20
    summary = pd.read_csv(output / "summary.csv")
    assert summary[summary.exact_three_stars == 0].relative_rmse.isna().all()
    with pytest.raises(FileExistsError):
        run_experiment(config_path, output, escape_adapter)
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    from private_graphlets.experiment_plots import plot_results
    first = plot_results(output, tmp_path / "plots1")
    second = plot_results(output, tmp_path / "plots2")
    assert first == second
    assert len(first["files_sha256"]) == 8
    # Exact metric recomputation catches absent trials before any averaging.
    raw = pd.read_csv(output / "trials.csv")
    graphs = pd.read_csv(output / "graphs.csv")
    with pytest.raises(ValueError, match="trial count"):
        aggregate_trials(raw.iloc[:-1], graphs, tiny_config())
    with (output / "trials.csv").open("a") as stream:
        stream.write("tampered\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_results(output)
