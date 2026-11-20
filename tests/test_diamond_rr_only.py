"""Focused integration checks for the supplied polynomial; no RR re-audit."""

from itertools import combinations
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from private_graphlets import diamond_rr_only as rr_diamond
from private_graphlets import randomized_response as shared_rr
from private_graphlets.graph import SimpleGraph, load_edge_list

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data/fixtures"
EXPECTED = json.loads((FIXTURES / "expected_counts.json").read_text())["cases"]


def explicit_polynomial(w):
    n = len(w)
    return sum(w[a,b]*w[a,c]*w[b,c]*w[a,d]*w[b,d]
               for a,b in combinations(range(n), 2)
               for c,d in combinations([v for v in range(n) if v not in (a,b)], 2))


@pytest.mark.parametrize("name", EXPECTED)
def test_exact_fixture_polynomial(name):
    graph = load_edge_list(FIXTURES / f"{name}.edges")
    w = np.array([[int(v in row) for v in range(graph.num_vertices)] for row in graph.adjacency])
    assert rr_diamond.diamond_polynomial(w) == explicit_polynomial(w) == EXPECTED[name][4]


@pytest.mark.parametrize("n", range(4))
def test_small_public_universes(n):
    # Still exercises the supplied shared RR path; no added small-n shortcut.
    result = rr_diamond.estimate_rr_only_diamonds(SimpleGraph.from_edges(n, []), 1, seed=2900+n)
    assert result.estimate == pytest.approx(0, abs=1e-14)
    assert result.num_vertices == n


def test_weighted_identity_and_negative_fractional_readonly_input():
    rng = np.random.default_rng(2904)
    w = rng.normal(size=(6,6))
    w = np.triu(w, 1)
    w += w.T
    w.flags.writeable = False
    before = w.copy()
    assert rr_diamond.diamond_polynomial(w) == pytest.approx(explicit_polynomial(w), abs=1e-12)
    np.testing.assert_array_equal(w, before)
    negative = np.full((4,4), -.5)
    np.fill_diagonal(negative, 0)
    assert rr_diamond.diamond_polynomial(negative) == -6/32


@pytest.mark.parametrize("epsilon", [.5, 1., 2.])
def test_api_uses_existing_rr_once_at_full_epsilon(monkeypatch, epsilon):
    assert rr_diamond.sample_rr_upper is shared_rr.sample_rr_upper
    assert rr_diamond.rr_matrix is shared_rr.rr_matrix
    graph = load_edge_list(FIXTURES / "diamond.edges")
    expected_rng = np.random.default_rng(2905)
    bits = shared_rr.sample_rr_upper(graph, epsilon, expected_rng)
    expected = rr_diamond.diamond_polynomial(shared_rr.rr_matrix(graph.num_vertices, bits, epsilon))
    calls = []
    def sample(g, epsilon, rng):
        calls.append(("sample", epsilon))
        return shared_rr.sample_rr_upper(g, epsilon, rng)
    def matrix(n, reports, epsilon):
        calls.append(("matrix", epsilon))
        assert reports == bits
        return shared_rr.rr_matrix(n, reports, epsilon)
    monkeypatch.setattr(rr_diamond, "sample_rr_upper", sample)
    monkeypatch.setattr(rr_diamond, "rr_matrix", matrix)
    result = rr_diamond.estimate_rr_only_diamonds(graph, epsilon, seed=np.int64(2905))
    assert calls == [("sample", epsilon), ("matrix", epsilon)]
    assert result.estimate == expected
    assert result == rr_diamond.estimate_rr_only_diamonds(graph, epsilon, seed=2905)
    assert set(result.to_dict()) == {"estimate", "epsilon", "num_vertices", "pattern",
                                     "count_semantics", "privacy_model", "privacy_status"}
    assert result.privacy_status == "experimental_unverified"
    json.dumps(result.to_dict(), allow_nan=False)


@pytest.mark.parametrize("epsilon", [0, -1, True, float("nan"), float("inf"), 31])
def test_invalid_epsilon_and_shared_supported_range(epsilon):
    with pytest.raises(ValueError):
        rr_diamond.estimate_rr_only_diamonds(SimpleGraph.from_edges(4, []), epsilon, seed=1)


@pytest.mark.parametrize("seed", [-1, True, 1.5])
def test_invalid_seed(seed):
    with pytest.raises(ValueError):
        rr_diamond.estimate_rr_only_diamonds(SimpleGraph.from_edges(4, []), 1, seed=seed)


def test_invalid_weight_matrices_and_finite_overflow():
    for w in (np.ones((2,3)), np.eye(2), np.array([[0., 1.], [1.000001, 0.]]),
              np.array([[0., float("inf")], [float("inf"), 0.]])):
        with pytest.raises(ValueError):
            rr_diamond.diamond_polynomial(w)
    w = np.full((4,4), 1e100)
    np.fill_diagonal(w, 0)
    with pytest.raises(FloatingPointError):
        rr_diamond.diamond_polynomial(w)


def runner_module():
    spec = importlib.util.spec_from_file_location("evaluate_rr_diamond", ROOT / "scripts/evaluate_diamond_rr_only.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_fixture_resume_csv_budget_and_output_isolation(tmp_path, monkeypatch):
    runner = runner_module()
    graph = SimpleGraph.from_edges(4, [])
    # Two tiny fixture calls only, never label these as benchmark/ESCAPE data.
    monkeypatch.setattr(runner, "GRAPH_IDS", ("test_empty_fixture",))
    monkeypatch.setattr(runner, "EPSILONS", (1.,))
    monkeypatch.setattr(runner, "load_inputs", lambda: ([graph], [dict(graph="test_empty_fixture", n=4, m=0, exact_count=0)]))
    calls = []
    def estimate(g, epsilon, *, seed):
        calls.append((epsilon, seed))
        return rr_diamond.estimate_rr_only_diamonds(g, epsilon, seed=seed)
    monkeypatch.setattr(runner, "estimate_rr_only_diamonds", estimate)
    config = runner.configuration(2, 2906)
    output = tmp_path / "rr_diamond"
    first = runner.run(output, config, max_new_trials=1)
    assert first["completed_trials"] == 1 and first["status"] == "partial"
    assert runner.verify(output)["study_status"] == "partial"
    with pytest.raises(FileExistsError):
        runner.run(output, config)
    assert runner.run(output, config, resume=True)["new_trials_this_invocation"] == 1
    assert runner.run(output, config, resume=True)["new_trials_this_invocation"] == 0
    assert len(calls) == 2 and calls[0][0] == calls[1][0] == 1.
    assert calls[0][1] != calls[1][1]
    assert runner.verify(output) == dict(status="verified", study_status="complete", trials=2, remaining_trials=0)
    rows = runner.pd.read_csv(output / "trials.csv", dtype={"seed": str}, float_precision="round_trip")
    assert (rows.epsilon_rr == rows.epsilon).all()
    assert not {"cap", "epsilon_ordering", "epsilon_wedge"}.intersection(rows.columns)
    assert runner.pd.read_csv(output / "summary.csv").relative_rmse.isna().all()
    with pytest.raises(ValueError, match="config differs"):
        runner.run(output, runner.configuration(2, 2907), resume=True)


def test_runner_metrics_and_preflight_without_estimator(monkeypatch, capsys):
    runner = runner_module()
    common = dict(graph_index=0, epsilon_index=0, graph="test", n=4, m=5, epsilon=1, exact_count=1, runtime_seconds=.5)
    summary = runner.summarize([{**common, "estimate": -1.}, {**common, "estimate": 3.}]).iloc[0]
    assert summary.mean_estimate == 1 and summary.bias == 0 and summary.variance == summary.mse == 4
    assert summary.rmse == summary.mae == summary.mean_relative_error == summary.relative_rmse == 2
    def forbidden(*args, **kwargs):
        pytest.fail("check must not execute the estimator")
    monkeypatch.setattr(runner, "estimate_rr_only_diamonds", forbidden)
    assert runner.main(["check", "--seed", "2908"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["graphs"] == 6 and result["planned_trials"] == 3600
    assert result["config"]["epsilons"] == [.5, 1., 2.]
    assert result["config"]["epsilon_rr"] == "total_epsilon"
    assert result["config"]["epsilon_laplace"] == result["config"]["epsilon_ordering"] == 0.
    assert result["diamond_truth"] == dict(karate=151, dolphins=300, les_miserables=4544,
                                            brightkite_50=245, ba_n100=217982, sbm_n100=3093)
