"""Focused specification checks, not an empirical DP proof."""

from collections import Counter
from dataclasses import asdict
from fractions import Fraction
from itertools import combinations, permutations
import json
from math import comb
from pathlib import Path

import numpy as np
import pytest

from private_graphlets import four_cycle as c4
from private_graphlets.four_cycle_exact import count_four_cycles
from private_graphlets.graph import SimpleGraph, load_edge_list

FIXTURES = Path(__file__).resolve().parents[1] / 'data/fixtures'
EXPECTED = json.loads((FIXTURES / 'expected_counts.json').read_text())['cases']


def nonprivate_indicator(graph, cycle):
    """Test-only noiseless local computation, never a mechanism option."""
    a, b, c, d = cycle
    rows = graph.adjacency + (frozenset(),) * (max(cycle) + 1 - graph.num_vertices)
    left = c4._local_wedges(rows[b], (c4.WedgeRequest(0, 0, (a, c)),))[0]
    right = c4._local_wedges(rows[d], (c4.WedgeRequest(0, 1, (a, c)),))[0]
    return int(left * right)


@pytest.mark.parametrize('p', [5, 7, 11, 13])
def test_balance_and_variance_moments(p):
    blocks = c4.progression_blocks(p)
    q = p * (p - 1)
    assert len(blocks) == q and all(len(set(b)) == 4 for b in blocks)
    pairs = Counter(pair for b in blocks for pair in combinations(sorted(b), 2))
    triples = Counter(triple for b in blocks for triple in combinations(sorted(b), 3))
    assert set(pairs.values()) == {12} and len(pairs) == comb(p, 2)
    assert max(triples.values()) <= 24
    assert len({frozenset(b) for b in blocks}) < q
    overlaps = Counter(len(set(a) & set(b)) for a in blocks for b in blocks)
    for r in range(3):
        lhs = sum(count * comb(t, r) for t, count in overlaps.items())
        assert lhs == Fraction(q*q*comb(4, r)**2, comb(p, r))
    assert overlaps[3] + overlaps[4] <= 96*q


@pytest.mark.parametrize('name', EXPECTED)
def test_fixture_count_and_analytical_sampling_mean(name):
    graph = load_edge_list(FIXTURES / f'{name}.edges')
    p = c4.padded_prime(graph.num_vertices)
    total = sum(nonprivate_indicator(graph, cycle)
                for vertices in combinations(range(p), 4) for cycle in c4.cycle_orders(vertices))
    assert total == count_four_cycles(graph) == EXPECTED[name][3]
    # A uniform permutation sends any ordered four-distinct block to each
    # ordered injection equally often: (p-4)! completions. Each cycle marginal
    # is 1/[3*C(p,4)]. Integrate cycle choice exactly, not Monte Carlo.
    marginal = Fraction(total, 3*comb(p, 4))
    assert Fraction(3*comb(p, 4), p*(p-1)) * p*(p-1) * marginal == total


def test_exhaustive_global_permutations():
    graph = load_edge_list(FIXTURES / 'cycle.edges')
    blocks = c4.progression_blocks(5)
    summed = 0
    for permutation in permutations(range(5)):
        summed += sum(nonprivate_indicator(graph, cycle)
                      for block in blocks
                      for cycle in c4.cycle_orders(tuple(permutation[v] for v in block)))
    assert Fraction(3*comb(5, 4), len(blocks)) * Fraction(summed, 120*3) == 1


def test_neighbor_sensitivity_and_public_schedule():
    clique = load_edge_list(FIXTURES / 'clique.edges')
    diamond = load_edge_list(FIXTURES / 'diamond.edges')
    schedule = c4.public_schedule(4, np.random.default_rng(2201))
    # Every possible edge deletion, including the clique/diamond fixture pair.
    neighbors = [diamond] + [SimpleGraph.from_edges(4, [e for e in combinations(range(4), 2) if e != edge])
                            for edge in combinations(range(4), 2)]
    for graph in neighbors:
        affected = {v for v in range(4) if graph.adjacency[v] != clique.adjacency[v]}
        for v, requests in enumerate(schedule.requests):
            before = c4._local_wedges(clique.adjacency[v] if v < 4 else frozenset(), requests)
            after = c4._local_wedges(graph.adjacency[v] if v < 4 else frozenset(), requests)
            assert np.abs(before - after).sum() <= (12 if v in affected else 0)
    a = c4.simulate_four_cycles_private(clique, 1, seed=2201)
    b = c4.simulate_four_cycles_private(diamond, 1, seed=2201)
    assert a.schedule == b.schedule
    assert tuple(map(len, a.reports)) == tuple(map(len, b.reports))
    assert set(asdict(a)) == {'estimate', 'epsilon', 'endpoint_epsilon', 'sensitivity',
                            'laplace_scale', 'schedule', 'reports', 'privacy_status'}
    assert a.estimate == c4.aggregate(a.schedule, a.reports)


@pytest.mark.parametrize('epsilon', [.5, 1, 2, 4])
def test_fresh_noise_and_budget(epsilon, monkeypatch):
    graph = load_edge_list(FIXTURES / 'clique_with_isolates.edges')
    observed = []
    original = c4._local_reports
    def record(neighbors, requests, scale, rng):
        observed.append((len(requests), scale))
        return original(neighbors, requests, scale, rng)
    monkeypatch.setattr(c4, '_local_reports', record)
    release = c4.simulate_four_cycles_private(graph, epsilon, seed=2202)
    assert release.epsilon == epsilon and release.endpoint_epsilon == epsilon/2
    assert release.sensitivity == 12 and release.laplace_scale == 24/epsilon
    assert sum(n for n, _ in observed) == 2*7*6
    assert all(scale == 24/epsilon for _, scale in observed)
    # Independently replay the primitive noise draws after public scheduling.
    rng = np.random.default_rng(2202)
    assert c4.public_schedule(6, rng) == release.schedule
    noises = []
    for v, (requests, reports) in enumerate(zip(release.schedule.requests, release.reports)):
        exact = c4._local_wedges(graph.adjacency[v] if v < 6 else frozenset(), requests)
        noise = rng.laplace(0, 24/epsilon, len(requests))
        np.testing.assert_array_equal(reports, exact + noise)
        noises.extend(noise)
    assert len(set(noises)) == 84  # fixed-seed occurrence regression, not independence proof


def test_corners_and_signed_aggregation():
    for n, p in [(0, 5), (1, 5), (4, 5), (5, 5), (6, 7), (7, 7)]:
        graph = SimpleGraph.from_edges(n, [])
        result = c4.simulate_four_cycles_private(graph, 1, seed=2203)
        assert result.schedule.p == p and count_four_cycles(graph) == 0
        assert len(result.schedule.cycles) == p*(p-1)
    schedule = c4.public_schedule(4, np.random.default_rng(2204))
    reports = tuple(tuple(-1e100 if r.slot == 0 else 1.0 for r in row)
                    for row in schedule.requests)
    assert c4.aggregate(schedule, reports) == pytest.approx(-15e100)
    for epsilon in [0, -1, float('inf'), float('nan')]:
        with pytest.raises(ValueError):
            c4.simulate_four_cycles_private(SimpleGraph.from_edges(4, []), epsilon, seed=1)


def test_runner_population_metrics():
    # Two controlled observations test nonzero variance; smoke cells have one.
    import importlib.util
    path = FIXTURES.parents[1] / 'scripts/evaluate_four_cycle.py'
    spec = importlib.util.spec_from_file_location('evaluate_c4', path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    rows = [dict(graph_index=0, epsilon_index=0, graph='controlled', n=4, m=4,
                 epsilon=1, exact_count=1, estimate=x, runtime_seconds=.1,
                 epsilon_endpoint_1=.5, epsilon_endpoint_2=.5) for x in [-1, 5]]
    result = runner.summarize(rows).iloc[0]
    assert result.mse == 10 and result.bias == 1 and result.variance == 9
    assert result.variance_ddof == 0 and result.mae == 3
    assert result.relative_rmse == result.rmse == pytest.approx(10**.5)
    assert result.negative_estimates == 1 and result.runtime_total_seconds == .2
