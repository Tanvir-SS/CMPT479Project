"""Finite mechanism checks supplement reasoning; they do not prove executable DP."""

from dataclasses import asdict
from itertools import combinations, permutations, product
import math

import numpy as np
import pytest

from private_graphlets import diamond as d
from private_graphlets.four_clique_exact import ranks, select_outgoing
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import ordering_budget_ledger
from private_graphlets.randomized_response import local_rr_row, rr_matrix, rr_parameters, sample_rr_upper


def graph_mask(n, mask):
    return SimpleGraph.from_edges(n, [e for i, e in enumerate(combinations(range(n), 2)) if mask >> i & 1])


@pytest.mark.parametrize("n", [4, 5])
def test_exhaustive_neighbor_vector_sensitivity_fixed_order(n):
    edges = tuple(combinations(range(n), 2))
    graphs = [graph_mask(n, mask) for mask in range(1 << len(edges))]
    orders = tuple(permutations(range(n))) if n == 4 else (tuple(range(n)), tuple(reversed(range(n))))
    checks = 0
    for order in orders:
        rank = ranks(order)
        requests = d.wedge_requests(order)
        owners = [v for v, row in enumerate(requests) for _ in row]
        for cap in sorted({2, 3, n - 1}):
            vectors = np.array([np.concatenate([d._local_wedge_indicators(v, row, rank, cap, requests[v])
                                               for v, row in enumerate(g.adjacency)]) for g in graphs])
            for mask in range(len(graphs)):
                for i, (u, v) in enumerate(edges):
                    difference = abs(vectors[mask] - vectors[mask ^ (1 << i)])
                    earlier = min((u, v), key=rank.__getitem__)
                    assert difference.sum() <= 2 * (cap - 1)
                    assert all(change == 0 for change, owner in zip(difference, owners) if owner != earlier)
                    checks += 1
    # Includes every addition AND inverse deletion, both rank orientations.
    assert checks == (18_432 if n == 4 else 61_440)


@pytest.mark.parametrize("cap", [2, 3])
def test_replacement_attains_bound_and_ideal_laplace_density_ratio(cap):
    n = cap + 2
    order = tuple(range(n))
    before = frozenset(range(2, n))
    after = before | {1}
    requests = d.wedge_requests(order)[0]
    x = d._local_wedge_indicators(0, before, order, cap, requests)
    xp = d._local_wedge_indicators(0, after, order, cap, requests)
    assert select_outgoing(0, before, order, cap) == tuple(range(2, n))
    assert select_outgoing(0, after, order, cap) == tuple(range(1, n - 1))
    assert abs(x - xp).sum() == 2 * (cap - 1)
    epsilon_w = .75
    scale = 2 * (cap - 1) / epsilon_w
    for y in (x, xp, np.linspace(-2, 2, len(x))):
        log_ratio = (abs(y-xp).sum() - abs(y-x).sum()) / scale
        assert abs(log_ratio) <= epsilon_w + 1e-14  # both directions of ideal density


def test_cap_selection_uses_rank_prefix_not_ids_and_never_exceeds_cap():
    graph = graph_mask(5, 1023)
    for order in permutations(range(5)):
        rank = ranks(order)
        for cap in (2, 3, 4):
            for v, row in enumerate(graph.adjacency):
                selected = select_outgoing(v, row, rank, cap)
                outgoing = tuple(w for w in order if w in row and rank[v] < rank[w])
                assert selected == outgoing[:cap] and len(selected) <= cap
                if cap == 4:
                    assert selected == outgoing


def test_rr_one_public_owner_all_pairs_and_exact_binary_likelihoods():
    class UniformSpy:
        def __init__(self, value):
            self.value, self.sizes = value, []
        def random(self, size):
            self.sizes.append(size)
            return np.full(size, self.value)
    for mask in range(64):
        for uniform in (0., .999):  # flipping and retaining each edge/nonedge
            spy = UniformSpy(uniform)
            reports = sample_rr_upper(graph_mask(4, mask), 1, spy)
            assert spy.sizes == [3, 2, 1, 0] and len(reports) == 6
            assert reports == tuple(bool(mask >> i & 1) ^ (uniform == 0.) for i in range(6))
    for epsilon in (.1, 1., 4.):
        p = rr_parameters(epsilon)
        for truth, bit in product((0, 1), repeat=2):
            probability = (1-p.flip_probability) if truth == bit else p.flip_probability
            neighbor_probability = p.flip_probability if truth == bit else 1-p.flip_probability
            assert abs(math.log(probability / neighbor_probability)) == pytest.approx(epsilon)
        for truth in (0, 1):
            probabilities = [p.flip_probability if truth else 1-p.flip_probability,
                             1-p.flip_probability if truth else p.flip_probability]
            values = [-p.a, p.maximum]
            assert sum(q*w for q,w in zip(probabilities, values)) == pytest.approx(truth, abs=1e-14)
            assert sum(q*(w-truth)**2 for q,w in zip(probabilities, values)) == pytest.approx(p.variance)


def test_wedge_schedule_all_coordinates_including_zero_and_independent_draws():
    class LaplaceSpy:
        def __init__(self): self.calls = []
        def laplace(self, loc, scale, size):
            self.calls.append((loc, scale, size))
            return np.arange(size, dtype=float) + .25
    order = (2, 0, 3, 1)
    requests = d.wedge_requests(order)
    assert sum(map(len, requests)) == math.comb(4, 3)
    for mask in range(64):
        graph = graph_mask(4, mask)
        spy = LaplaceSpy()
        for v, row in enumerate(graph.adjacency):
            reports = d.local_wedge_reports(v, row, ranks(order), 2, requests[v], 4., spy)
            exact = d._local_wedge_indicators(v, row, ranks(order), 2, requests[v])
            np.testing.assert_array_equal(reports, exact + np.arange(len(requests[v])) + .25)
        assert spy.calls == [(0., 4., len(row)) for row in requests]
    # Empty graphs have all-zero local vectors but still send every coordinate.
    assert any(len(row) > 0 for row in requests)


def test_stage_routing_independent_streams_and_full_transcript_only(monkeypatch):
    graph = graph_mask(5, 1023)
    budget = d.DiamondBudget(3, .5, 1., 1.5)
    calls = []
    original_order, original_rr, original_wedges = d.kcore_order, d.sample_rr_upper, d.local_wedge_reports
    def order_spy(graph, epsilon, rng, config):
        calls.append(("O", epsilon, rng))
        return original_order(graph, epsilon, rng, config)
    def rr_spy(graph, epsilon, rng):
        calls.append(("R", epsilon, rng))
        return original_rr(graph, epsilon, rng)
    def wedge_spy(vertex, neighbors, rank, cap, requests, scale, rng):
        calls.append(("W", scale, rng))
        return original_wedges(vertex, neighbors, rank, cap, requests, scale, rng)
    monkeypatch.setattr(d, "kcore_order", order_spy)
    monkeypatch.setattr(d, "sample_rr_upper", rr_spy)
    monkeypatch.setattr(d, "local_wedge_reports", wedge_spy)
    run = d.simulate_diamonds(graph, 3, cap=3, budget=budget, seed=2470)
    assert [name for name, _, _ in calls] == ["O", "R"] + ["W"] * 5
    assert [value for _, value, _ in calls] == [.5, 1.] + [4/1.5] * 5
    assert len({id(rng) for _, _, rng in calls}) == 3
    t = run.transcript
    assert t.ordering.order == tuple(sorted(range(5), key=lambda v: (t.ordering.levels[v], v)))
    assert t.ordering.promotions and t.ordering.thresholds
    assert all(e <= budget.ordering / 2 for e in ordering_budget_ledger(t.ordering))
    assert set(asdict(t)) == {"budget", "cap", "ordering", "rr_upper", "wedge_reports"}
    assert set(asdict(t.ordering)) == {"thresholds", "promotions", "levels", "epsilon", "threshold_fraction",
                                     "levels_per_group", "nominal_round_limit", "ordering_type", "privacy_status"}
    assert set(run.result.to_dict()) == {"estimate", "budget", "cap", "wedge_noise_scale", "rr_weight",
                                        "pattern", "count_semantics", "result_type", "privacy_status"}
    # Independently replay all W coordinates; no O/R draw consumption shifts them.
    wedge_rng = d._simulation_streams(2470)[2]
    for v, requests in enumerate(d.wedge_requests(t.ordering.order)):
        x = d._local_wedge_indicators(v, graph.adjacency[v], ranks(t.ordering.order), 3, requests)
        np.testing.assert_array_equal(t.wedge_reports[v], x + wedge_rng.laplace(0, 4/1.5, len(x)))
    def forbidden(*args, **kwargs):
        pytest.fail("aggregation queried graph-local/randomization code")
    for name in ("kcore_order", "sample_rr_upper", "local_wedge_reports", "_local_wedge_indicators", "_simulation_streams"):
        monkeypatch.setattr(d, name, forbidden)
    assert d.aggregate_diamonds(t) == run.result.estimate


def test_dependency_bound_counts_shared_random_reports_including_self():
    for n in (4, 5, 6, 7):
        order = tuple(reversed(range(n)))
        rank = ranks(order)
        dependencies = []
        for a,b in combinations(range(n), 2):
            for c,e in combinations(set(range(n)) - {a,b}, 2):
                used = {("R", *sorted(edge)) for edge in ((a,b),(a,c),(b,c),(a,e),(b,e))}
                used |= {("W", v, a, b) for v in (c,e) if rank[v] < min(rank[a],rank[b])}
                dependencies.append(used)
        assert len(dependencies) == math.comb(n,2)*math.comb(n-2,2)
        bound = 25*math.comb(n-2,2) + 2*(n-3)
        assert max(sum(bool(row & other) for other in dependencies) for row in dependencies) <= bound


def test_single_contribution_variance_bound_all_binary_means_and_clipping():
    for epsilon in (.25, 1., 4.):
        p = d.hybrid_parameters(2, epsilon, epsilon)
        v = rr_parameters(epsilon).variance
        worst = (1+v)**5 - 1
        for central, ac, bc, ae, be in product((0,1), repeat=5):
            for hybrid_c, hybrid_e in product((False, True), repeat=2):
                for retain_c, retain_e in product((False, True), repeat=2):
                    means, variances = [], []
                    for x,y,hybrid,retain in ((ac,bc,hybrid_c,retain_c),(ae,be,hybrid_e,retain_e)):
                        mean, variance = x*y, v*(x+y)+v*v
                        if hybrid:
                            mean *= p.rr_weight + (1-p.rr_weight)*retain
                            variance = p.rr_weight**2*variance + (1-p.rr_weight)**2*p.wedge_variance
                        means.append(mean); variances.append(variance)
                    m1,m2 = means
                    s1,s2 = variances
                    variance = (central+v)*(s1+m1*m1)*(s2+m2*m2)-central*m1*m1*m2*m2
                    assert variance <= worst*(1+1e-13)
