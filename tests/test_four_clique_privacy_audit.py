"""Finite code-to-proof checks. Neither likelihood algebra nor tests certify executable DP."""

from dataclasses import asdict
from fractions import Fraction
from itertools import combinations, permutations, product
import math

import numpy as np
import pytest

from private_graphlets.four_clique import (
    CliqueBudget, allocate_budget, cap_from_reports, conditional_sensitivity,
    local_cap_report, local_count_report, local_score, simulate_four_cliques,
)
from private_graphlets.four_clique_exact import ranks, select_outgoing
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import KCoreConfig, kcore_order, ordering_budget_ledger
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper


def graph_from_mask(n, mask):
    return SimpleGraph.from_edges(n, [edge for i, edge in enumerate(combinations(range(n), 2))
                                     if mask >> i & 1])


def test_full_score_vector_all_four_vertex_graphs_orders_and_rr_tables():
    """294,912 neighboring-vector checks, not just one local root function."""
    n = 4
    edges = list(combinations(range(n), 2))
    graphs = [graph_from_mask(n, mask) for mask in range(64)]
    checks = 0
    for order in permutations(range(n)):
        rank = ranks(order)
        selected = [[select_outgoing(v, row, rank, 3) for v, row in enumerate(g.adjacency)]
                    for g in graphs]
        for bits in product((False, True), repeat=6):
            weights = rr_matrix(n, bits, math.log(2))
            scores = [tuple(local_score(s, weights) for s in sets) for sets in selected]
            for mask in range(64):
                for i, (u, v) in enumerate(edges):
                    if mask >> i & 1:
                        continue
                    differences = [abs(a-b) for a, b in zip(scores[mask], scores[mask | (1 << i)])]
                    owner = u if rank[u] < rank[v] else v
                    assert all(d == 0 for w, d in enumerate(differences) if w != owner)
                    assert sum(differences) <= 12  # M=2,a=1,Delta_3=12, exact integer values.
                    checks += 1
    assert checks == 294_912


def test_replacement_whole_vector_and_inverse_deletion():
    # Fixed rank: adding 0--1 replaces 4 in root 0's first three neighbors.
    before = SimpleGraph.from_edges(5, [(0, 2), (0, 3), (0, 4), (1, 2), (1, 3)])
    after = SimpleGraph.from_edges(5, [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3)])
    maximum = 0
    for bits in product((False, True), repeat=10):
        weights = rr_matrix(5, bits, math.log(2))
        scores = [tuple(local_score(select_outgoing(v, row, range(5), 3), weights)
                        for v, row in enumerate(g.adjacency)) for g in (before, after)]
        differences = tuple(b-a for a, b in zip(*scores))
        assert differences[1:] == (0.,) * 4
        maximum = max(maximum, abs(differences[0]))
        assert sum(map(abs, differences)) <= 12
        assert sum(abs(a-b) for a, b in zip(*scores)) <= 12  # reverse deletion
    assert maximum == 12  # naive M^3=8 would be insufficient.


@pytest.mark.parametrize('cap', [0, 1, 2])
def test_zero_sensitivity_keeps_fixed_zero_reports_without_count_draws(cap):
    class NoDraw:
        def laplace(self, *args):
            pytest.fail('zero sensitivity must not sample count noise')
    graph = graph_from_mask(4, 63)
    w = rr_matrix(4, (True,) * 6, 1.)
    assert conditional_sensitivity(cap, 1.) == 0
    assert [local_count_report(v, row, range(4), cap, w, 0., NoDraw())
            for v, row in enumerate(graph.adjacency)] == [0.] * 4
    run = simulate_four_cliques(graph, 2, cap_mode='public', cap=cap, seed=8001)
    assert run.transcript.local_reports == (0.,) * 4
    assert len(run.transcript.rr_upper) == 6  # RR still occurs when n>=4.


def test_threshold_limited_schedule_and_permanent_stopping(monkeypatch):
    thresholds = iter((1, 4, 2, 3))
    monkeypatch.setattr('private_graphlets.kcore.degree_threshold', lambda *args: next(thresholds))
    calls = []
    def promotion(neighbors, levels, r, parameter, cutoff, rng):
        calls.append((r, parameter, levels))
        return int(not (parameter == .5/8 and r == 1))
    monkeypatch.setattr('private_graphlets.kcore.promotion_bit', promotion)
    t = kcore_order(graph_from_mask(4, 63), 1, np.random.default_rng(8002))
    assert len(calls) == 8  # per-vertex counts 1,2,2,3, each at most its threshold.
    assert t.promotions == ((1,1,1,1), (0,0,1,1), (0,0,0,1), (0,0,0,0))
    assert t.levels == (1,1,2,3) and t.order == (0,1,2,3)
    assert ordering_budget_ledger(t) == (.5, .375, .5, .5)
    for r in range(4):
        assert len({levels for round_, _, levels in calls if round_ == r}) <= 1


def test_ideal_geometric_threshold_bit_likelihoods_exact():
    # q=exp(-s)=1/2. P[Z>=k] for the symmetric integer geometric law.
    def survival(k):
        q = Fraction(1, 2)
        return q**k/(1+q) if k >= 1 else 1-q**(1-k)/(1+q)
    for count in range(6):
        for cutoff_minus_bias in range(-12, 13):
            a = survival(cutoff_minus_bias-count+1)
            b = survival(cutoff_minus_bias-(count+1)+1)
            for pa, pb in ((a,b), (1-a,1-b)):
                assert Fraction(1,2) <= pa/pb <= 2


@pytest.mark.parametrize('ordering', ['fixed', 'kcore'])
@pytest.mark.parametrize('mode', ['public', 'noisy', 'uncapped'])
def test_neighboring_full_transcripts_modes_and_budget(ordering, mode):
    options = dict(ordering=ordering, cap_mode=mode, seed=8003)
    if mode == 'public':
        options['cap'] = 3
    for mask in (62, 63):
        graph = graph_from_mask(4, mask)
        run = simulate_four_cliques(graph, 4., **options)
        assert run == simulate_four_cliques(graph, 4., **options)
        b = run.result.budget
        assert b == allocate_budget(4., ordering, mode)
        assert math.fsum((b.ordering,b.cap,b.rr,b.count)) == 4.
        t = run.transcript
        assert sorted(t.order) == list(range(4))
        if ordering == 'kcore':
            assert t.order == tuple(sorted(range(4), key=lambda v: (t.ordering.levels[v], v)))
            assert all(x <= b.ordering/2 for x in ordering_budget_ledger(t.ordering))
        assert len(t.cap_reports) == (4 if mode == 'noisy' else 0)
        assert len(t.local_reports) == 4 and len(t.rr_upper) == 6
        assert run.result.local_noise_scale == conditional_sensitivity(t.cap, b.rr)/b.count
        forbidden = {'adjacency','degrees','neighbors','selected','seed','scores','rng_state'}
        assert not forbidden.intersection(asdict(t))
        assert not forbidden.intersection(run.result.to_dict())


def test_known_fixed_seed_is_a_deterministic_disclosure_counterexample():
    a = simulate_four_cliques(graph_from_mask(4, 62), 4, ordering='kcore', cap_mode='noisy', seed=8004)
    b = simulate_four_cliques(graph_from_mask(4, 63), 4, ordering='kcore', cap_mode='noisy', seed=8004)
    assert a.transcript.rr_upper[0] != b.transcript.rr_upper[0]
    assert a.transcript.rr_upper[1:] == b.transcript.rr_upper[1:]
    # Conditional on this public seed, the differing RR bit has probability 1
    # versus 0. This is not a finite-epsilon DP mechanism. No empirical DP claim.


def test_all_pair_reporting_has_no_adjacency_dependent_message_schedule():
    class UniformSpy:
        def __init__(self): self.sizes = []
        def random(self, n):
            self.sizes.append(n)
            return np.full(n, .99)
    for mask in range(64):
        rng = UniformSpy()
        reports = sample_rr_upper(graph_from_mask(4, mask), 1., rng)
        assert rng.sizes == [3,2,1,0] and len(reports) == 6


@pytest.mark.parametrize('eta', [1e-4, .5, 30.])
def test_extreme_supported_rr_and_local_noise(eta):
    p = rr_parameters(eta)
    assert math.isfinite(p.variance) and p.variance > 0
    assert p.maximum-p.a == pytest.approx(1)
    result = simulate_four_cliques(graph_from_mask(4, 63), 2*eta, seed=8005)
    assert math.isfinite(result.result.estimate)
    assert result.result.local_noise_scale == conditional_sensitivity(3, eta)/eta


@pytest.mark.parametrize('bad', [0., -1., float('nan'), float('inf'), True, 1e-310])
def test_invalid_privacy_values_rejected(bad):
    with pytest.raises((ValueError, OverflowError)):
        simulate_four_cliques(graph_from_mask(4, 63), bad)


def test_cap_rounding_boundary_and_vector_sensitivity():
    n, beta, eps = 5, .05, 1.
    h = (math.log(n)-math.log(beta))/eps
    # With dmax=3, underestimation requires max Q+h<=2, not merely <3.
    assert cap_from_reports((2-h-.01,)*n, n, eps, beta) == 2
    assert cap_from_reports((2-h+.01,)*n, n, eps, beta) == 3
    class Zero:
        def laplace(self, loc, scale):
            assert scale == 1/eps
            return 0.
    for order in permutations(range(4)):
        rank = ranks(order)
        for mask in range(64):
            graph = graph_from_mask(4, mask)
            q = [local_cap_report(v,row,rank,eps,Zero()) for v,row in enumerate(graph.adjacency)]
            for i in range(6):
                other = graph_from_mask(4, mask ^ (1 << i))
                qp = [local_cap_report(v,row,rank,eps,Zero()) for v,row in enumerate(other.adjacency)]
                assert sum(abs(a-b) for a,b in zip(q,qp)) == 1


def test_simulator_budget_tolerance_and_geometric_tail_guard_are_documented_limits():
    # Record observed executable limitations, without weakening an algorithm test.
    b = CliqueBudget(2,0,0,1,1+1e-14)
    assert math.fsum((b.rr,b.count)) > b.total
    with pytest.raises(ValueError, match='geometric simulation parameter'):
        kcore_order(graph_from_mask(4,0), 4e-10, np.random.default_rng(8))
