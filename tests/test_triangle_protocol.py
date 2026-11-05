"""Modified triangle protocol: deterministic math checks and simulation regressions."""

from dataclasses import asdict
from itertools import combinations, permutations, product
import math

import numpy as np
import pytest

import private_graphlets.triangle as protocol
from private_graphlets.four_clique import cap_from_reports, local_cap_report
from private_graphlets.four_clique_exact import ranks, select_outgoing
from private_graphlets.graph import SimpleGraph
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper
from private_graphlets.triangle_exact import count_triangles
from private_graphlets.triangle import (
    TriangleBudget, TriangleStreams, aggregate_triangle_reports,
    estimate_triangles_from_rr, estimate_triangles_private, simulate_triangles_private,
    triangle_local_report, triangle_local_score, triangle_sensitivity, triangle_streams,
)


ETA = math.log(2)
BUDGET = TriangleBudget(0.5, 1.0, ETA, 2.0)


def clique(n):
    return SimpleGraph.from_edges(n, combinations(range(n), 2))


def true_weights(graph):
    weights = np.zeros((graph.num_vertices, graph.num_vertices))
    for v, row in enumerate(graph.adjacency):
        for w in row:
            weights[v, w] = 1
    weights.flags.writeable = False
    return weights


def score(graph, order, cap, weights):
    rank = ranks(order)
    return sum(triangle_local_score(v, row, rank, cap, weights)
               for v, row in enumerate(graph.adjacency))


def retained(graph, order, cap):
    # Independent triple oracle: actual triangles whose earliest root retains
    # both other vertices. Does not call the local score or selection kernel.
    rank = ranks(order)
    total = 0
    for triple in combinations(range(graph.num_vertices), 3):
        if not all(b in graph.adjacency[a] for a, b in combinations(triple, 2)):
            continue
        root, a, b = sorted(triple, key=rank.__getitem__)
        prefix = sorted([w for w in graph.adjacency[root] if rank[w] > rank[root]],
                        key=rank.__getitem__)[:cap]
        total += a in prefix and b in prefix
    return total


@pytest.mark.parametrize('n,edges', [
    (0, []), (5, []), (3, [(0, 1), (1, 2), (0, 2)]),
    (4, list(combinations(range(4), 2))), (6, list(combinations(range(4), 2))),
    (4, [(0, 1), (0, 2), (0, 3), (1, 2)]),
])
def test_exact_local_scores(n, edges):
    graph = SimpleGraph.from_edges(n, edges)
    for order in (tuple(range(n)), tuple(reversed(range(n)))):
        for cap in range(max(1, n)):
            assert score(graph, order, cap, true_weights(graph)) == retained(graph, order, cap)
        assert score(graph, order, max(0, n-1), true_weights(graph)) == count_triangles(graph)
    if n == 4 and len(edges) == 6:
        assert score(graph, range(n), 2, true_weights(graph)) == 2 < count_triangles(graph)


def test_exhaustive_conditional_local_sensitivity():
    # Every n=4 ordering, root, incident list and single incident-edge change.
    # All 8 assignments of the root's 3 possible closing bits; other RR bits
    # and non-incident true edges do not enter this root's score. Every list is
    # realizable by a simple graph; masks include both change directions.
    n = 4
    for order in permutations(range(n)):
        rank = ranks(order)
        for root in range(n):
            others = [v for v in range(n) if v != root]
            pairs = list(combinations(others, 2))
            rows = [frozenset(v for i, v in enumerate(others) if mask & (1 << i))
                    for mask in range(8)]
            for bits in product((False, True), repeat=3):
                weights = np.zeros((n, n))
                p = rr_parameters(ETA)
                for (a, b), bit in zip(pairs, bits):
                    weights[a, b] = weights[b, a] = p.maximum if bit else -p.a
                for cap in range(n):
                    values = [triangle_local_score(root, row, rank, cap, weights) for row in rows]
                    for mask in range(8):
                        for i in range(3):
                            assert abs(values[mask] - values[mask ^ (1 << i)]) <= triangle_sensitivity(cap, ETA) + 1e-12


def test_replacement_attains_range_bound():
    # Before: prefix {2,3}; adding 1 replaces 3, giving {1,2}.
    weights = rr_matrix(4, (False, False, False, True, False, False), ETA)
    before = triangle_local_score(0, frozenset({2, 3}), (0, 1, 2, 3), 2, weights)
    after = triangle_local_score(0, frozenset({1, 2, 3}), (0, 1, 2, 3), 2, weights)
    assert before == pytest.approx(-1)
    assert after == pytest.approx(2)
    assert after-before == pytest.approx(triangle_sensitivity(2, ETA))
    assert after-before > rr_parameters(ETA).maximum


def test_only_earlier_endpoint_changes_under_fixed_transcript():
    n = 4
    pairs = list(combinations(range(n), 2))
    weights = rr_matrix(n, (True, False, True, False, True, False), ETA)
    for order in permutations(range(n)):
        rank = ranks(order)
        for mask in range(64):
            graph = SimpleGraph.from_edges(n, [e for i, e in enumerate(pairs) if mask & (1 << i)])
            for i, (a, b) in enumerate(pairs):
                other = SimpleGraph.from_edges(n, [e for j, e in enumerate(pairs)
                                                   if (mask ^ (1 << i)) & (1 << j)])
                owner = min((a, b), key=rank.__getitem__)
                for cap in range(n):
                    for v in range(n):
                        if v != owner:
                            assert select_outgoing(v, graph.adjacency[v], rank, cap) == select_outgoing(v, other.adjacency[v], rank, cap)
                    change = abs(score(graph, order, cap, weights)-score(other, order, cap, weights))
                    assert change <= triangle_sensitivity(cap, ETA)+1e-12


class RecordingNoise:
    def __init__(self, value=-10.0):
        self.value = value
        self.calls = []

    def laplace(self, location, scale):
        self.calls.append((location, scale))
        return self.value


def test_noise_before_aggregation_and_reuse(monkeypatch):
    graph = clique(4)
    streams = triangle_streams(55)
    bits = sample_rr_upper(graph, ETA, streams.rr)
    weights = rr_matrix(4, bits, ETA)
    before = weights.copy()
    rr_state = streams.rr.bit_generator.state
    def forbidden(*args, **kwargs):
        raise AssertionError('component must not rerun earlier stages')
    for name in ('sample_rr_upper', 'kcore_order', 'local_cap_report', 'cap_from_reports'):
        monkeypatch.setattr(protocol, name, forbidden)
    noise = RecordingNoise()
    run = estimate_triangles_from_rr(graph, (3, 1, 0, 2), 2, weights,
                                     epsilon_rr=ETA, epsilon_count=2, rng=noise)
    expected = tuple(triangle_local_score(v, row, ranks((3, 1, 0, 2)), 2, weights)-10
                     for v, row in enumerate(graph.adjacency))
    assert run.transcript.local_reports == expected
    assert noise.calls == [(0, triangle_sensitivity(2, ETA)/2)]*4
    assert run.result.estimate == sum(expected) < 0
    assert run.result.to_dict()['additional_epsilon'] == 2
    assert run.result.to_dict()['accounting_scope'] == 'count_only_given_previous_releases'
    assert np.array_equal(before, weights) and not weights.flags.writeable
    assert streams.rr.bit_generator.state == rr_state


@pytest.mark.parametrize('cap', [0, 1])
def test_zero_sensitivity_no_noise(cap):
    graph = clique(3)
    weights = rr_matrix(3, (True,)*3, ETA)
    noise = RecordingNoise()
    run = estimate_triangles_from_rr(graph, range(3), cap, weights,
                                     epsilon_rr=ETA, epsilon_count=1, rng=noise)
    assert run.transcript.local_reports == (0.0,)*3
    assert run.result.estimate == run.result.local_noise_scale == 0
    assert noise.calls == []


def test_all_rr_assignments_conditional_expectation():
    n = 4
    pairs = list(combinations(range(n), 2))
    reports = list(product((False, True), repeat=6))
    matrices = [rr_matrix(n, bits, ETA) for bits in reports]
    for mask in range(64):
        truth = tuple(bool(mask & (1 << i)) for i in range(6))
        graph = SimpleGraph.from_edges(n, [e for e, bit in zip(pairs, truth) if bit])
        probabilities = [math.prod((2 if r == t else 1)/3 for r, t in zip(bits, truth))
                         for bits in reports]
        for order in ((0, 1, 2, 3), (2, 0, 3, 1)):
            for cap in range(4):
                mean = math.fsum(p*score(graph, order, cap, w)
                                 for p, w in zip(probabilities, matrices))
                assert mean == pytest.approx(retained(graph, order, cap), abs=1e-12)
                if cap == 3:
                    assert mean == pytest.approx(count_triangles(graph), abs=1e-12)


@pytest.mark.parametrize('cap', [2, 3])
def test_seeded_mean_with_analytic_standard_error(cap):
    graph = clique(4)
    eta, epsilon_count = 1.0, 2.0
    streams = triangle_streams(100+cap)
    count = 3000
    values = []
    # Independent pair RR variance, but weights can be shared by multiple roots.
    multiplicities = {pair: 0 for pair in combinations(range(4), 2)}
    for v in range(4):
        for pair in combinations(tuple(range(v+1, 4))[:cap], 2):
            multiplicities[pair] += 1
    variance = rr_parameters(eta).variance * sum(c*c for c in multiplicities.values())
    scale = triangle_sensitivity(cap, eta)/epsilon_count
    variance += 2*4*scale**2
    for _ in range(count):
        weights = rr_matrix(4, sample_rr_upper(graph, eta, streams.rr), eta)
        run = estimate_triangles_from_rr(graph, range(4), cap, weights,
                                         epsilon_rr=eta, epsilon_count=epsilon_count,
                                         rng=streams.count)
        values.append(run.result.estimate)
    assert abs(np.mean(values)-retained(graph, range(4), cap)) < 6*math.sqrt(variance/count)


@pytest.mark.parametrize('n', [0, 1, 2, 3, 6])
def test_standalone_replay_schema_and_stage_correspondence(n):
    graph = clique(n)
    run = simulate_triangles_private(graph, budget=BUDGET, seed=91)
    assert run == simulate_triangles_private(graph, budget=BUDGET, seed=91)
    assert run.result == estimate_triangles_private(graph, budget=BUDGET, seed=91)
    t = run.transcript
    assert t.order == tuple(sorted(range(n), key=lambda v: (t.ordering.levels[v], v)))
    assert len(t.rr_upper) == n*(n-1)//2 and len(t.local_reports) == n
    assert 0 <= t.cap <= max(0, n-1)
    assert run.result.to_dict()['epsilon_total'] == BUDGET.total
    assert set(asdict(t)) == {'ordering', 'order', 'cap_reports', 'cap', 'rr_upper', 'local_reports'}
    assert set(asdict(run.result)) == {'estimate', 'num_vertices', 'released_cap', 'budget', 'local_noise_scale', 'beta'}
    assert set(asdict(t.ordering)) == {'thresholds', 'promotions', 'levels', 'epsilon',
        'threshold_fraction', 'levels_per_group', 'nominal_round_limit', 'ordering_type', 'privacy_status'}
    # Reproduce stages independently under the SAME order, without exposing truth.
    streams = triangle_streams(91)
    expected_rr = sample_rr_upper(graph, BUDGET.rr, streams.rr)
    assert t.rr_upper == expected_rr
    expected_cap = tuple(local_cap_report(v, row, ranks(t.order), BUDGET.cap, streams.cap)
                         for v, row in enumerate(graph.adjacency))
    assert t.cap_reports == expected_cap
    assert t.cap == cap_from_reports(expected_cap, n, BUDGET.cap, .05)


def test_stream_independence_and_single_rr_call(monkeypatch):
    graph = clique(6)
    one, two = triangle_streams(12), triangle_streams(12)
    two.count.random(50)
    calls = []
    original = protocol.sample_rr_upper
    def spy(*args):
        calls.append(1)
        return original(*args)
    monkeypatch.setattr(protocol, 'sample_rr_upper', spy)
    a = simulate_triangles_private(graph, budget=BUDGET, streams=one)
    b = simulate_triangles_private(graph, budget=BUDGET, streams=two)
    assert len(calls) == 2  # one per standalone invocation
    assert a.transcript.ordering == b.transcript.ordering
    assert a.transcript.cap_reports == b.transcript.cap_reports
    assert a.transcript.rr_upper == b.transcript.rr_upper
    assert a.transcript.local_reports != b.transcript.local_reports
    rng = np.random.default_rng(3)
    with pytest.raises(ValueError):
        TriangleStreams(rng, rng, rng, rng)


@pytest.mark.parametrize('field', ['ordering', 'cap', 'rr', 'count'])
@pytest.mark.parametrize('bad', [0, -1, float('nan'), float('inf'), True, '1'])
def test_invalid_budgets(field, bad):
    values = dict(ordering=.5, cap=1., rr=1., count=1.)
    values[field] = bad
    with pytest.raises(ValueError):
        TriangleBudget(**values)


@pytest.mark.parametrize('kwargs', [{'ordering': 1.1}, {'rr': 31}])
def test_unsupported_budgets(kwargs):
    values = dict(ordering=.5, cap=1., rr=1., count=1.)
    values.update(kwargs)
    with pytest.raises(ValueError):
        TriangleBudget(**values)


@pytest.mark.parametrize('bad', [-1, True, 1.5])
def test_invalid_sensitivity_cap(bad):
    with pytest.raises(ValueError):
        triangle_sensitivity(bad, ETA)


@pytest.mark.parametrize('change', ['mutable', 'shape', 'asymmetric', 'diagonal', 'nan', 'wrong_epsilon', 'dtype'])
def test_invalid_rr_context(change):
    weights = rr_matrix(3, (True, False, True), ETA).copy()
    eta = ETA
    if change == 'shape': weights = weights[:2, :2]
    if change == 'asymmetric': weights[0, 1] = -1
    if change == 'diagonal': weights[0, 0] = 2
    if change == 'nan': weights[0, 1] = float('nan')
    if change == 'wrong_epsilon': eta = 1.
    if change == 'dtype': weights = weights.astype(np.float32)
    if change != 'mutable': weights.flags.writeable = False
    with pytest.raises(ValueError):
        estimate_triangles_from_rr(clique(3), range(3), 2, weights,
                                   epsilon_rr=eta, epsilon_count=1, rng=np.random.default_rng(0))


@pytest.mark.parametrize('order,cap,count', [([0, 0, 2], 2, 1), ([0, 1, 2], 3, 1),
    ([0, 1, 2], -1, 1), ([0, 1, 2], 2, 0), ([0, 1, 2], 2, 1e-320)])
def test_invalid_component_parameters(order, cap, count):
    with pytest.raises(ValueError):
        estimate_triangles_from_rr(clique(3), order, cap, rr_matrix(3, (True,)*3, ETA),
                                   epsilon_rr=ETA, epsilon_count=count, rng=np.random.default_rng(0))


def test_nonfinite_noise_and_aggregation_rejected():
    with pytest.raises(FloatingPointError):
        triangle_local_report(0, frozenset({1, 2}), (0, 1, 2), 2,
                              rr_matrix(3, (True,)*3, ETA), ETA, 1, RecordingNoise(float('inf')))
    with pytest.raises(ValueError): aggregate_triangle_reports([float('nan')])
    assert aggregate_triangle_reports([-2., -3.]) == -5


def test_scope_and_budget_overflow_guards():
    with pytest.raises(ValueError):
        TriangleBudget(.5, 1e308, 1., 1e308)
    with pytest.raises(ValueError):
        simulate_triangles_private(SimpleGraph.from_edges(1001, []), budget=BUDGET)
    with pytest.raises(ValueError):
        simulate_triangles_private(clique(3), budget=None)


def test_private_cap_underestimate_is_enforced(monkeypatch):
    monkeypatch.setattr(protocol, 'cap_from_reports', lambda *args: 1)
    run = simulate_triangles_private(clique(5), budget=BUDGET, seed=7)
    assert run.transcript.cap == 1
    assert run.transcript.local_reports == (0.0,)*5
    assert run.result.estimate == 0
    assert count_triangles(clique(5)) == 10  # separate non-private evaluation


@pytest.mark.parametrize('kwargs', [{'beta': 0}, {'beta': True}, {'beta': float('nan')},
    {'seed': -1}, {'seed': True}, {'seed': 2, 'streams': triangle_streams(2)}])
def test_invalid_standalone_parameters(kwargs):
    with pytest.raises(ValueError):
        simulate_triangles_private(clique(3), budget=BUDGET, **kwargs)
