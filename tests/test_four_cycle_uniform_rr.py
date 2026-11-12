"""Targeted deterministic implementation checks; not an empirical DP proof."""

from collections import Counter
from dataclasses import asdict
from itertools import combinations
import json
from math import comb, exp, fsum
from pathlib import Path

import numpy as np
import pytest

from private_graphlets import four_cycle_uniform_rr as c4
from private_graphlets.four_cycle_exact import count_four_cycles
from private_graphlets.graph import SimpleGraph, load_edge_list

FIXTURES = Path(__file__).resolve().parents[1] / 'data/fixtures'
EXPECTED = json.loads((FIXTURES / 'expected_counts.json').read_text())['cases']


def indicator(graph, cycle):
    return int(all(v in graph.adjacency[u]
                   for u, v in zip(cycle, cycle[1:] + cycle[:1])))


@pytest.mark.parametrize('name', EXPECTED)
def test_exact_candidate_identity(name):
    graph = load_edge_list(FIXTURES / f'{name}.edges')
    cycles = [c for vs in combinations(range(graph.num_vertices), 4)
              for c in c4.cycle_orders(vs)]
    assert len(cycles) == len(set(cycles)) == 3 * comb(graph.num_vertices, 4)
    assert sum(indicator(graph, c) for c in cycles) == EXPECTED[name][3]
    assert count_four_cycles(graph) == EXPECTED[name][3]


def test_public_sampling_q_and_uniform_choice_mapping():
    # Controlled choices check that every four-set/three-way choice maps once;
    # no frequency-based Monte Carlo test of uniformity.
    vertices = iter(combinations(range(5), 4))
    class Choices:
        def choice(self, n, size, replace):
            assert (n, size, replace) == (5, 4, False)
            return next(vertices)
        def integers(self, high):
            assert high == 3
            return 2
    schedule = c4.public_schedule(5, Choices())
    assert schedule.cycles == ((0, 2, 1, 3), (0, 2, 1, 4))
    for n in (4, 5, 6, 10, 20):
        s = c4.public_schedule(n, np.random.default_rng(2601))
        assert len(s.cycles) == (n*n + 19)//20
        assert all(len(set(c)) == 4 for c in s.cycles)
        assert len(s.requests) == 2*len(s.cycles)
        assert sum(dict(s.participation).values()) == 4*len(s.cycles)
    assert c4.sample_count(10**10 + 1) == ((10**10 + 1)**2 + 19)//20


def fixed_schedule():
    return c4.schedule_from_cycles(5, [(0, 1, 2, 3)]*2 + [(0, 1, 2, 4)])


def test_participation_and_allocation():
    s = fixed_schedule()
    counts = dict(s.participation)
    assert counts == {(0, 1): 3, (1, 2): 3, (2, 3): 2, (0, 3): 2,
                      (0, 4): 1, (2, 4): 1}
    for i, cycle in enumerate(s.cycles):
        edges = Counter(c4._edge(u, v) for u, v in zip(cycle, cycle[1:]+cycle[:1]))
        requests = s.requests[2*i:2*i+2]
        assert Counter(e for r in requests for e in r.edges) == edges
        assert [r.slot for r in requests] == [0, 1]
    alphas = c4.allocate_privacy(s, 1.2)
    assert alphas == pytest.approx((.4, .6, .4, .6, .4, 1.2))
    assert sum(counts.values()) == 12
    for e in counts:
        assert fsum(a for r, a in zip(s.requests, alphas) if e in r.edges) <= 1.2 + 1e-15


@pytest.mark.parametrize('alpha', [1e-12, .1, 1., 4., 1000.])
def test_rr_debias_and_exact_moments(alpha):
    r, gap = c4.rr_parameters(alpha)
    assert r == pytest.approx(exp(-alpha)/(1+exp(-alpha)))
    y0, y1 = c4.debias(0, alpha), c4.debias(1, alpha)
    assert y0 == -r/gap and y1 == (1-r)/gap
    if .01 < alpha < 10:
        assert gap == pytest.approx(1-2*r)
        for x in (0, 1):
            p1 = r if x == 0 else 1-r
            mean = (1-p1)*y0 + p1*y1
            variance = (1-p1)*(y0-x)**2 + p1*(y1-x)**2
            assert mean == pytest.approx(x, abs=1e-13)
            assert variance == pytest.approx(exp(alpha)/(exp(alpha)-1)**2)


def test_repeated_requests_use_fresh_coins():
    s = fixed_schedule()
    class Coins:
        calls = 0
        def random(self):
            self.calls += 1
            return 0.0 if self.calls % 2 else .999999
    rng = Coins()
    reports = [c4._local_report(frozenset((0, 2)), s.requests[0], 1., rng)
               for _ in range(4)]
    assert reports == [0, 1, 0, 1] and rng.calls == 4
    rng = Coins()
    assert [c4._local_report(frozenset(), s.requests[0], 1., rng)
            for _ in range(2)] == [1, 0]


def test_neighbors_both_endpoints_and_transcript():
    clique = load_edge_list(FIXTURES / 'clique.edges')
    diamond = load_edge_list(FIXTURES / 'diamond.edges')
    changed = {c4._edge(u, v) for u in range(4)
               for v in clique.adjacency[u] ^ diamond.adjacency[u]}
    assert len(changed) == 1
    edge = changed.pop()
    # Use all three public candidates to exercise both endpoints of the edge.
    s = c4.schedule_from_cycles(4, c4.cycle_orders(range(4)))
    alphas = c4.allocate_privacy(s, 1.)
    affected = [r for r in s.requests if edge in r.edges]
    assert {r.center for r in affected} == set(edge)
    assert fsum(a for r, a in zip(s.requests, alphas) if edge in r.edges) <= 1.
    for r in s.requests:
        def x(g):
            return all(v in g.adjacency[r.center] for v in r.endpoints)
        assert (x(clique) != x(diamond)) == (edge in r.edges)
    a = c4.simulate_four_cycles_private(clique, 1, seed=2602)
    b = c4.simulate_four_cycles_private(diamond, 1, seed=2602)
    assert a.schedule == b.schedule and a.alphas == b.alphas
    assert len(a.reports) == len(b.reports) == 2*c4.sample_count(4)
    assert set(asdict(a)) == {'estimate', 'epsilon', 'schedule', 'alphas', 'reports', 'privacy_status'}
    assert all(type(bit) is int and bit in (0, 1) for bit in a.reports)
    assert set(asdict(s)) == {'n', 'cycles', 'requests', 'participation'}
    assert set(asdict(s.requests[0])) == {'candidate', 'slot', 'center', 'endpoints'}
    assert a.estimate == c4.aggregate(a.schedule, a.alphas, a.reports)


def test_schedule_and_allocation_precede_adjacency(monkeypatch):
    events = []
    original = c4.allocate_privacy
    def allocate(s, e):
        result = original(s, e)
        events.append('allocated')
        return result
    monkeypatch.setattr(c4, 'allocate_privacy', allocate)
    class GuardedGraph:
        num_vertices = 4
        @property
        def adjacency(self):
            assert events == ['allocated']
            return (frozenset(),)*4
    c4.simulate_four_cycles_private(GuardedGraph(), 1, seed=2603)


def test_server_signed_estimate_and_small_universes():
    s = c4.schedule_from_cycles(4, [(0, 1, 2, 3)])
    alphas = c4.allocate_privacy(s, 1.)
    estimate = c4.aggregate(s, alphas, (0, 1))
    assert estimate == pytest.approx(3*c4.debias(0, 1)*c4.debias(1, 1))
    assert estimate < 0 and estimate != round(estimate)
    for n in range(4):
        release = c4.simulate_four_cycles_private(SimpleGraph.from_edges(n, []), 1, seed=2604)
        assert release.estimate == 0 and release.reports == release.alphas == ()
        assert release.schedule.cycles == ()
    with pytest.raises(ValueError):
        c4.aggregate(s, alphas, (1,))
    with pytest.raises(ValueError):
        c4.debias(2, 1)


@pytest.mark.parametrize('epsilon', [0, -1, True, float('inf'), float('nan'), 5e-324])
def test_invalid_privacy_range(epsilon):
    with pytest.raises(ValueError):
        c4.simulate_four_cycles_private(SimpleGraph.from_edges(4, []), epsilon, seed=2605)


def test_rng_contract():
    graph = SimpleGraph.from_edges(4, [])
    assert c4.simulate_four_cycles_private(graph, 1, seed=2606) == c4.simulate_four_cycles_private(
        graph, 1, rng=np.random.default_rng(2606))
    with pytest.raises(ValueError):
        c4.simulate_four_cycles_private(graph, 1, seed=1, rng=np.random.default_rng(1))
    with pytest.raises(TypeError):
        c4.simulate_four_cycles_private(graph, 1, rng=1)
