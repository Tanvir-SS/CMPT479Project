"""Five-stage P4 wiring, exact moment checks and focused seeded diagnostics."""

from dataclasses import asdict
from itertools import combinations, product
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import private_graphlets.four_path as protocol
import private_graphlets.triangle as triangle
from private_graphlets.four_clique import cap_from_reports, local_cap_report
from private_graphlets.four_clique_exact import ranks
from private_graphlets.four_path import (
    FourPathBudget, FourPathStreams, degree_product_estimate,
    estimate_four_paths_private, four_path_streams, local_degree_report,
    simulate_four_paths_private,
)
from private_graphlets.four_path_exact import count_four_paths
from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.noise import sample_degree_noise
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper
from private_graphlets.triangle_exact import count_triangles


BUDGET = FourPathBudget(degree=2., ordering=.5, rr=math.log(2), cap=1., count=2.)
FIXTURES = Path(__file__).resolve().parents[1] / 'data/fixtures'


def clique(n):
    return SimpleGraph.from_edges(n, combinations(range(n), 2))


def frozen(values):
    matrix = np.array(values, dtype=np.float64)
    matrix.flags.writeable = False
    return matrix


def closing_multiplicities(graph, order, cap):
    # NON-PRIVATE test-only oracle, independent of the selection/score kernels.
    position = {v: i for i, v in enumerate(order)}
    result = {pair: 0 for pair in combinations(range(graph.num_vertices), 2)}
    for v in order:
        selected = [w for w in order if position[w] > position[v] and w in graph.adjacency[v]][:cap]
        for a, b in combinations(selected, 2):
            result[tuple(sorted((a, b)))] += 1
    return result


def degree_variance(graph, epsilon_d, epsilon_r):
    # Analytic reference only, never part of a release or implementation fallback.
    t = [len(row)-1 for row in graph.adjacency]
    s = 8/epsilon_d**2
    h = rr_parameters(epsilon_r).variance
    g = [sum(t[u] for u in row) for row in graph.adjacency]
    return (s*sum(x*x for x in g) + s*s*graph.num_edges
            + h*sum((t[u]**2+s)*(t[v]**2+s) for u, v in combinations(range(len(t)), 2)))


@pytest.mark.parametrize('name', ['edgeless', 'path', 'cycle', 'diamond', 'clique', 'clique_with_isolates'])
def test_controlled_assembly_and_no_clipping(name, monkeypatch):
    graph = load_edge_list(FIXTURES / f'{name}.edges')
    # Deterministic injected noise is a wiring test, not a private release.
    monkeypatch.setattr(protocol, 'sample_degree_noise', lambda epsilon, *, size, rng: np.array(-3.25))
    monkeypatch.setattr(triangle, 'triangle_local_report', lambda *args: 7.5)
    run = simulate_four_paths_private(graph, budget=BUDGET, seed=23)
    t, r = run.transcript, run.result
    weights = rr_matrix(graph.num_vertices, t.rr_upper, BUDGET.rr)
    degrees = tuple(len(row)-3.25 for row in graph.adjacency)
    expected = sum(float(weights[u, v])*(degrees[u]-1)*(degrees[v]-1)
                   for u, v in combinations(range(graph.num_vertices), 2))
    assert t.noisy_degrees == degrees
    assert r.degree_product_estimate == pytest.approx(expected)
    assert r.triangle_estimate == 7.5*graph.num_vertices
    assert r.estimate == pytest.approx(expected-3*r.triangle_estimate)


def test_empty_graph():
    run = simulate_four_paths_private(clique(0), budget=BUDGET, seed=0)
    assert run.result.estimate == 0
    assert run.transcript.noisy_degrees == run.transcript.rr_upper == ()
    assert run.transcript.local_triangle_reports == ()


def test_degree_scale_client_boundary_and_stream(monkeypatch):
    graph = SimpleGraph.from_edges(5, [(0, 1), (1, 2)])
    streams = four_path_streams(12)
    original = protocol.sample_degree_noise
    calls = []
    def spy(epsilon, *, size, rng):
        calls.append((epsilon, size, rng))
        return original(epsilon, size=size, rng=rng)
    monkeypatch.setattr(protocol, 'sample_degree_noise', spy)
    run = simulate_four_paths_private(graph, budget=BUDGET, streams=streams)
    assert len(calls) == 5
    assert all(e == BUDGET.degree and size == () and rng is streams.degree for e, size, rng in calls)
    replay = four_path_streams(12)
    expected = tuple(len(row)+float(sample_degree_noise(BUDGET.degree, size=(), rng=replay.degree))
                     for row in graph.adjacency)
    assert run.transcript.noisy_degrees == expected
    assert run.result.degree_noise_scale == 2/BUDGET.degree
    assert not set(asdict(run.transcript)) & {'degrees', 'raw_degrees', 'noise', 'seed', 'rng'}

    class Noise:
        def laplace(self, location, scale, size):
            assert (location, scale, size) == (0., 1., ())
            return np.array(-5.125)
    assert local_degree_report(frozenset({1}), 2., Noise()) == -4.125


def test_one_rr_same_object_and_no_standalone(monkeypatch):
    graph = clique(5)
    seen, calls = {}, dict(rr=0, matrix=0, order=0, cap=0)
    originals = {name: getattr(protocol, name) for name in
                 ('sample_rr_upper', 'rr_matrix', 'degree_product_estimate',
                  'estimate_triangles_from_rr', 'kcore_order', 'cap_from_reports')}
    def rr(*args):
        calls['rr'] += 1
        return originals['sample_rr_upper'](*args)
    def matrix(*args):
        calls['matrix'] += 1
        seen['weights'] = originals['rr_matrix'](*args)
        seen['copy'] = seen['weights'].copy()
        return seen['weights']
    def degree(degrees, weights):
        assert weights is seen['weights']
        seen['degree'] = weights
        return originals['degree_product_estimate'](degrees, weights)
    def component(graph, order, cap, weights, **kwargs):
        assert weights is seen['degree']
        assert kwargs['epsilon_rr'] == BUDGET.rr
        assert kwargs['epsilon_count'] == BUDGET.count
        return originals['estimate_triangles_from_rr'](graph, order, cap, weights, **kwargs)
    def ordering(*args):
        calls['order'] += 1
        return originals['kcore_order'](*args)
    def cap(*args):
        calls['cap'] += 1
        return originals['cap_from_reports'](*args)
    for name, fn in [('sample_rr_upper', rr), ('rr_matrix', matrix),
                     ('degree_product_estimate', degree), ('estimate_triangles_from_rr', component),
                     ('kcore_order', ordering), ('cap_from_reports', cap)]:
        monkeypatch.setattr(protocol, name, fn)
    def forbidden(*args, **kwargs):
        raise AssertionError('must not call standalone or resample earlier stages')
    for name in ('simulate_triangles_private', 'estimate_triangles_private', 'sample_rr_upper',
                 'kcore_order', 'local_cap_report', 'cap_from_reports'):
        monkeypatch.setattr(triangle, name, forbidden)
    run = simulate_four_paths_private(graph, budget=BUDGET, seed=9)
    assert calls == dict(rr=1, matrix=1, order=1, cap=1)
    assert len(run.transcript.rr_upper) == 10
    assert np.array_equal(seen['copy'], seen['weights']) and not seen['weights'].flags.writeable
    assert run.result.epsilon_total == sum(asdict(BUDGET).values())
    assert run.result.triangle_noise_scale == pytest.approx(triangle.triangle_sensitivity(run.transcript.cap, BUDGET.rr)/BUDGET.count)


def test_degree_product_all_pairs_no_graph_and_fractional_values():
    weights = rr_matrix(3, (False, True, False), BUDGET.rr)
    noisy = [-.5, 2.25, 0.]
    expected = sum(float(weights[u, v])*(noisy[u]-1)*(noisy[v]-1)
                   for u, v in combinations(range(3), 2))
    assert degree_product_estimate(noisy, weights) == expected
    # A false RR bit still contributes; no edge set can be consulted.
    assert degree_product_estimate([2., 2.], rr_matrix(2, (False,), BUDGET.rr)) < 0


@pytest.mark.parametrize('name', ['path', 'cycle', 'diamond', 'clique'])
@pytest.mark.parametrize('cap', [1, 2, 3])
def test_deterministic_laplace_moments_rr_expectation_variance_covariance(name, cap):
    graph = load_edge_list(FIXTURES / f'{name}.edges')
    n = graph.num_vertices
    assert n == 4
    order = (2, 0, 3, 1)
    rank = ranks(order)
    pairs = list(combinations(range(n), 2))
    truth = [v in graph.adjacency[u] for u, v in pairs]
    degrees = [len(row) for row in graph.adjacency]
    t = [d-1 for d in degrees]
    epsilon_d, eta = 2., math.log(2)
    s, h = 8/epsilon_d**2, rr_parameters(eta).variance
    coefficients = closing_multiplicities(graph, order, cap)
    retained = sum(coefficients[pair] for pair, bit in zip(pairs, truth) if bit)
    exact_a = sum(t[u]*t[v] for (u, v), bit in zip(pairs, truth) if bit)
    assert exact_a-3*count_triangles(graph) == count_four_paths(graph)
    values = []
    # This two-node product rule matches Laplace moments through degree two
    # per variable, which suffices for A, A^2, and A*T. It is not a Laplace sampler.
    for bits in product((False, True), repeat=len(pairs)):
        probability = math.prod((2 if r == x else 1)/3 for r, x in zip(bits, truth))
        weights = rr_matrix(n, bits, eta)
        triangle_score = sum(triangle.triangle_local_score(v, row, rank, cap, weights)
                             for v, row in enumerate(graph.adjacency))
        for signs in product((-1, 1), repeat=n):
            noisy = [d + sign*math.sqrt(s) for d, sign in zip(degrees, signs)]
            a = degree_product_estimate(noisy, weights)
            values.append((probability/(2**n), a, triangle_score))
    mean_a = math.fsum(p*a for p, a, _ in values)
    mean_t = math.fsum(p*tval for p, _, tval in values)
    var_a = math.fsum(p*(a-mean_a)**2 for p, a, _ in values)
    covariance = math.fsum(p*(a-mean_a)*(tv-mean_t) for p, a, tv in values)
    expected_cov = h*sum(coefficients[u, v]*t[u]*t[v] for u, v in pairs)
    assert mean_a == pytest.approx(exact_a, abs=1e-11)
    assert mean_t == pytest.approx(retained, abs=1e-11)
    assert var_a == pytest.approx(degree_variance(graph, epsilon_d, eta), rel=1e-12)
    assert covariance == pytest.approx(expected_cov, abs=1e-10)
    final_mean = math.fsum(p*(a-3*tv) for p, a, tv in values)
    assert final_mean == pytest.approx(count_four_paths(graph)+3*(count_triangles(graph)-retained), abs=1e-10)
    scale = triangle.triangle_sensitivity(cap, eta)/BUDGET.count
    var_t = h*sum(c*c for c in coefficients.values()) + 2*n*scale**2
    final_variance = math.fsum(p*(a-3*tv-final_mean)**2 for p, a, tv in values) + 9*2*n*scale**2
    assert final_variance == pytest.approx(var_a+9*var_t-6*expected_cov, rel=1e-12)
    if cap == 3:
        assert retained == count_triangles(graph)
    if name == 'clique' and cap == 2:
        assert retained == 2 and final_mean == pytest.approx(18)  # P4=12, bias=6
        assert covariance > 0


def test_seeded_degree_product_mean_with_analytic_tolerance():
    graph = clique(4)
    streams = four_path_streams(110301)
    count = 5000
    values = []
    for _ in range(count):
        degrees = tuple(local_degree_report(row, BUDGET.degree, streams.degree) for row in graph.adjacency)
        weights = rr_matrix(4, sample_rr_upper(graph, BUDGET.rr, streams.rr), BUDGET.rr)
        values.append(degree_product_estimate(degrees, weights))
    exact_a = count_four_paths(graph)+3*count_triangles(graph)
    variance = degree_variance(graph, BUDGET.degree, BUDGET.rr)
    assert abs(np.mean(values)-exact_a) < 6*math.sqrt(variance/count)


def test_replay_transcript_schema_and_order_cap_consistency():
    graph = SimpleGraph.from_edges(7, combinations(range(4), 2))
    run = simulate_four_paths_private(graph, budget=BUDGET, seed=44)
    assert run == simulate_four_paths_private(graph, budget=BUDGET, seed=44)
    assert run.result == estimate_four_paths_private(graph, budget=BUDGET, seed=44)
    t = run.transcript
    assert set(asdict(t)) == {'noisy_degrees', 'ordering', 'order', 'cap_reports', 'cap', 'rr_upper', 'local_triangle_reports'}
    assert set(asdict(run.result)) == {'estimate', 'degree_product_estimate', 'triangle_estimate',
        'num_vertices', 'released_cap', 'budget', 'degree_noise_scale', 'triangle_noise_scale', 'beta'}
    assert set(asdict(t.ordering)) == {'thresholds', 'promotions', 'levels', 'epsilon',
        'threshold_fraction', 'levels_per_group', 'nominal_round_limit', 'ordering_type', 'privacy_status'}
    assert t.order == tuple(sorted(range(7), key=lambda v: (t.ordering.levels[v], v)))
    streams = four_path_streams(44)
    caps = tuple(local_cap_report(v, row, ranks(t.order), BUDGET.cap, streams.cap)
                 for v, row in enumerate(graph.adjacency))
    assert t.cap_reports == caps
    assert t.cap == cap_from_reports(caps, 7, BUDGET.cap, .05)
    assert t.rr_upper == sample_rr_upper(graph, BUDGET.rr, streams.rr)
    assert run.result.to_dict()['target'] == 'original_noninduced_P4'
    assert run.result.to_dict()['privacy_status'] == 'experimental_unverified'


@pytest.mark.parametrize('name', ['degree', 'ordering', 'cap', 'rr', 'count'])
def test_stream_domains(name):
    a, b = four_path_streams(123), four_path_streams(123)
    getattr(a, name).random(17)
    for other in ('degree', 'ordering', 'cap', 'rr', 'count'):
        if other != name:
            assert np.array_equal(getattr(a, other).random(12), getattr(b, other).random(12))


def test_degree_stream_cannot_change_other_transcripts():
    a, b = four_path_streams(45), four_path_streams(45)
    a.degree.random(10)
    x = simulate_four_paths_private(clique(5), budget=BUDGET, streams=a).transcript
    y = simulate_four_paths_private(clique(5), budget=BUDGET, streams=b).transcript
    assert x.noisy_degrees != y.noisy_degrees
    for field in ('ordering', 'order', 'cap_reports', 'cap', 'rr_upper', 'local_triangle_reports'):
        assert getattr(x, field) == getattr(y, field)


def test_aliased_streams_rejected():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError): FourPathStreams(rng, rng, rng, rng, rng)
    streams = four_path_streams(1)
    alias = np.random.Generator(streams.degree.bit_generator)
    with pytest.raises(ValueError):
        FourPathStreams(streams.degree, alias, streams.cap, streams.rr, streams.count)


@pytest.mark.parametrize('field', ['degree', 'ordering', 'rr', 'cap', 'count'])
@pytest.mark.parametrize('bad', [0, -1, True, '1', float('nan'), float('inf')])
def test_invalid_budget(field, bad):
    values = asdict(BUDGET)
    values[field] = bad
    with pytest.raises(ValueError): FourPathBudget(**values)


@pytest.mark.parametrize('values', [dict(ordering=1.01), dict(rr=31), dict(degree=1e-320),
    dict(degree=1e308, cap=1e308), dict(rr=1e-200)])
def test_unsupported_budget(values):
    fields = asdict(BUDGET)
    fields.update(values)
    with pytest.raises(ValueError): FourPathBudget(**fields)


@pytest.mark.parametrize('degrees', [[1., float('nan')], [float('inf'), 0], [[1., 2.]], ['1', '2'], [True, False]])
def test_invalid_noisy_degrees(degrees):
    with pytest.raises(ValueError): degree_product_estimate(degrees, frozen([[0, 1], [1, 0]]))


@pytest.mark.parametrize('kind', ['shape', 'mutable', 'nan', 'diagonal', 'asymmetric', 'dtype'])
def test_invalid_weight_table(kind):
    w = np.array([[0., 1.], [1., 0.]])
    if kind == 'shape': w = w[:1, :1]
    if kind == 'nan': w[0, 1] = float('nan')
    if kind == 'diagonal': w[0, 0] = 1
    if kind == 'asymmetric': w[1, 0] = -1
    if kind == 'dtype': w = w.astype(np.float32)
    if kind != 'mutable': w.flags.writeable = False
    with pytest.raises(ValueError): degree_product_estimate([1., 2.], w)


def test_nonfinite_arithmetic_no_fallback(monkeypatch):
    with pytest.raises(FloatingPointError):
        degree_product_estimate([1e308, 1e308], frozen([[0, 1], [1, 0]]))
    monkeypatch.setattr(protocol, 'sample_degree_noise', lambda *args, **kwargs: np.array(float('inf')))
    with pytest.raises(FloatingPointError):
        simulate_four_paths_private(clique(3), budget=BUDGET, seed=1)


def test_final_overflow_and_negative_estimate(monkeypatch):
    monkeypatch.setattr(protocol, 'degree_product_estimate', lambda *args: -.25)
    def component(*args, **kwargs):
        return SimpleNamespace(result=SimpleNamespace(estimate=1.25, local_noise_scale=1.),
                               transcript=SimpleNamespace(local_reports=(1.25,)))
    monkeypatch.setattr(protocol, 'estimate_triangles_from_rr', component)
    assert estimate_four_paths_private(clique(3), budget=BUDGET, seed=1).estimate == -4.
    monkeypatch.setattr(protocol, 'degree_product_estimate', lambda *args: float('inf'))
    with pytest.raises(FloatingPointError):
        estimate_four_paths_private(clique(3), budget=BUDGET, seed=1)


@pytest.mark.parametrize('kwargs', [{'seed': True}, {'seed': -1}, {'beta': 0}, {'beta': float('nan')},
                                  {'beta': True}, {'seed': 1, 'streams': four_path_streams(1)}])
def test_invalid_options(kwargs):
    with pytest.raises(ValueError): simulate_four_paths_private(clique(3), budget=BUDGET, **kwargs)


def test_small_supported_parameters_and_scope():
    budget = FourPathBudget(.01, .01, .01, .01, .01)
    result = estimate_four_paths_private(clique(4), budget=budget, seed=4)
    assert math.isfinite(result.estimate)
    assert result.budget == budget
    with pytest.raises(ValueError):
        simulate_four_paths_private(SimpleGraph.from_edges(1001, []), budget=BUDGET)
    with pytest.raises(ValueError): simulate_four_paths_private(clique(3), budget=None)
