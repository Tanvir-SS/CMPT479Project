"""Independent deterministic checks of NON-PRIVATE ideal MSE calculations."""

from itertools import combinations, product
import math
from pathlib import Path

import numpy as np
import pytest

import private_graphlets.four_path_accuracy as accuracy
from private_graphlets.four_path import FourPathBudget, degree_product_estimate
from private_graphlets.four_path_accuracy import (
    closing_edge_multiplicities, conditional_four_path_mse, degree_product_variance,
    predicted_four_path_mse, retained_triangle_count, summarize_predictions,
)
from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.randomized_response import rr_matrix
from private_graphlets.triangle_exact import count_triangles


BUDGET = FourPathBudget(2., .5, math.log(2), 1., 2.)
FIXTURES = Path(__file__).resolve().parents[1]/'data/fixtures'


def graph_for(name):
    if name == 'isolates':
        return SimpleGraph.from_edges(4, [(0, 1), (1, 2), (0, 2)])
    return load_edge_list(FIXTURES/f'{name}.edges')


def independent_coefficients(graph, order, cap):
    # Direct pair/root membership tests, not select_outgoing or calculator helpers.
    position = {v: i for i, v in enumerate(order)}
    prefixes = {v: [w for w in order if position[w] > position[v]
                    and w in graph.adjacency[v]][:cap] for v in order}
    return {(a, b): sum(a in prefixes[v] and b in prefixes[v] for v in order)
            for a, b in combinations(range(graph.num_vertices), 2)}


@pytest.mark.parametrize('name', ['path', 'cycle', 'diamond', 'clique', 'isolates'])
@pytest.mark.parametrize('order', [(0, 1, 2, 3), (2, 0, 3, 1)])
@pytest.mark.parametrize('cap', [0, 1, 2, 3])
def test_conditional_mse_by_independent_moment_integration(name, order, cap):
    graph = graph_for(name)
    result = conditional_four_path_mse(graph, BUDGET, order, cap)
    pairs = list(combinations(range(4), 2))
    degrees = [len(row) for row in graph.adjacency]
    c = independent_coefficients(graph, order, cap)
    sparse = closing_edge_multiplicities(graph, order, cap)
    assert all(sparse.get(pair, 0) == value for pair, value in c.items())
    truth_bits = [b in graph.adjacency[a] for a, b in pairs]
    # Independent original P4 enumerator, avoids accuracy implementation's identities.
    from itertools import permutations
    truth = sum(b in graph.adjacency[a] and cc in graph.adjacency[b] and d in graph.adjacency[cc]
                for a, b, cc, d in permutations(range(4)))//2
    samples = []
    for bits in product((False, True), repeat=6):
        prob = math.prod((2 if r == x else 1)/3 for r, x in zip(bits, truth_bits))
        weights = rr_matrix(4, bits, BUDGET.rr)
        triangle_score = sum(c[pair]*float(weights[pair]) for pair in pairs)
        for signs in product((-1, 1), repeat=4):
            noisy = [d+sign*math.sqrt(2) for d, sign in zip(degrees, signs)]
            a = degree_product_estimate(noisy, weights)
            samples.append((prob/16, a, triangle_score, a-3*triangle_score-truth))
    mean_a = math.fsum(p*a for p, a, _, _ in samples)
    mean_t = math.fsum(p*t for p, _, t, _ in samples)
    var_a = math.fsum(p*(a-mean_a)**2 for p, a, _, _ in samples)
    cov = math.fsum(p*(a-mean_a)*(t-mean_t) for p, a, t, _ in samples)
    # eta=log(2): weight range 3. Independent count-noise contribution.
    scale = 0 if cap < 2 else (cap-1)*3/BUDGET.count
    laplace = 9*2*4*scale**2
    mse = math.fsum(p*e*e for p, _, _, e in samples)+laplace
    bias = math.fsum(p*e for p, _, _, e in samples)
    assert result.mse == pytest.approx(mse, rel=1e-12)
    assert result.bias == pytest.approx(bias, abs=1e-11)
    assert result.variance == pytest.approx(mse-bias*bias, rel=1e-12)
    assert result.shared_rr_covariance == pytest.approx(cov, abs=1e-11)
    assert degree_product_variance(graph, BUDGET) == pytest.approx(var_a, rel=1e-12)
    assert result.mse == pytest.approx(sum((result.degree_noise, result.rr_unadjusted,
        result.shared_rr_adjustment, result.triangle_laplace, result.truncation_squared_error)))
    assert result.rr_compact == pytest.approx(result.rr_unadjusted+result.shared_rr_adjustment)
    assert result.retained_triangles == retained_triangle_count(graph, order, cap)
    if cap == 3:
        assert result.missed_triangles == 0
    if cap <= 1:
        assert result.retained_triangles == result.triangle_laplace == result.shared_rr_covariance == 0
    if name == 'clique' and cap == 2:
        assert result.shared_rr_adjustment < 0
        assert result.mse != pytest.approx(result.mse-result.shared_rr_adjustment)


def test_random_history_average_requires_second_moment():
    graph = graph_for('clique')
    rows = [conditional_four_path_mse(graph, BUDGET, range(4), cap) for cap in (1, 3)]
    summary = summarize_predictions(rows)
    assert summary['predicted_mse'] == (rows[0].mse+rows[1].mse)/2
    assert summary['mean_truncation_squared_error'] == 72
    assert summary['squared_mean_bias'] == 36
    assert summary['between_history_variance'] == 36
    assert summary['predicted_mse'] == pytest.approx(summary['mean_conditional_variance']+72)


def test_predictor_samples_histories_only_and_replays(monkeypatch):
    graph = graph_for('diamond')
    import private_graphlets.four_path as full
    def forbidden(*args, **kwargs):
        raise AssertionError('prediction must not sample degrees/RR/count')
    for name in ('simulate_four_paths_private', 'sample_degree_noise', 'sample_rr_upper', 'rr_matrix'):
        monkeypatch.setattr(full, name, forbidden)
    result = predicted_four_path_mse(graph, BUDGET, seeds=[13, 17, 21, 29])
    assert result == predicted_four_path_mse(graph, BUDGET, seeds=[13, 17, 21, 29])
    assert result['result_type'] == 'nonprivate_monte_carlo_prediction'
    assert result['predicted_mse'] > 0


def test_predictor_averages_actual_independent_histories(monkeypatch):
    graph = graph_for('clique')
    calls = []
    def sample(graph, budget, *, seed, **kwargs):
        calls.append(seed)
        return (0, 1, 2, 3), 1 if seed == 10 else 3
    monkeypatch.setattr(accuracy, 'sample_order_cap', sample)
    result = predicted_four_path_mse(graph, BUDGET, seeds=[10, 20])
    assert calls == [10, 20]
    assert result['mean_truncation_squared_error'] == 72
    assert result['mean_missed_triangles'] == 2
    assert result['truncation_frequency'] == .5


@pytest.mark.parametrize('n', [0, 1, 2])
def test_empty_and_small(n):
    graph = SimpleGraph.from_edges(n, [])
    result = conditional_four_path_mse(graph, BUDGET, range(n), max(0, n-1))
    assert result.original_triangles == result.retained_triangles == 0
    assert result.mse >= 0 and math.isfinite(result.mse)


@pytest.mark.parametrize('order,cap', [([0, 0, 2, 3], 2), (range(4), -1), (range(4), 4), (range(4), True)])
def test_invalid_history(order, cap):
    with pytest.raises(ValueError): conditional_four_path_mse(graph_for('clique'), BUDGET, order, cap)


def test_numeric_and_prediction_input_guards():
    with pytest.raises(FloatingPointError):
        degree_product_variance(graph_for('clique'), FourPathBudget(1e-200, .5, 1, 1, 2))
    with pytest.raises(ValueError): predicted_four_path_mse(graph_for('clique'), BUDGET, seeds=[1, 1])
    with pytest.raises(ValueError): predicted_four_path_mse(graph_for('clique'), BUDGET, seeds=[1])
    with pytest.raises(ValueError): accuracy.sample_order_cap(graph_for('clique'), BUDGET, seed=True)


def test_private_paths_do_not_import_evaluation():
    root = Path(__file__).resolve().parents[1]/'src/private_graphlets'
    for name in ('four_path.py', 'triangle.py', 'noise.py', 'kcore.py', 'randomized_response.py'):
        assert 'four_path_accuracy' not in (root/name).read_text()
        assert 'four_path_experiments' not in (root/name).read_text()
