"""Stage 4: fixed neighboring inputs and finite moment identities, not trials."""

from itertools import product
import math

import pytest

from private_graphlets import four_path_sc_escape as sc
from private_graphlets.graph import SimpleGraph
from private_graphlets.triangle_exact import count_triangles


BUDGET = sc.SCEscapeBudget(.4, .7, .6, .8)


class NoiseProbe:
    def __init__(self, standardized=0.):
        self.standardized = standardized
        self.scales = []

    def laplace(self, location, scale):
        assert location == 0.
        self.scales.append(scale)
        return scale * self.standardized


def packed_truth(graph):
    return tuple(j in row for i, row in enumerate(graph.adjacency) for j in range(i))


def centers_and_scales(graph, x, bits, bound):
    h = max(map(abs, x), default=0.)
    p = sc.rr_parameters(BUDGET.rr).flip_probability
    s_rng, t_rng = NoiseProbe(), NoiseProbe()
    s = tuple(sc.local_product_report(i, row, x, h, BUDGET.product, s_rng)
              for i, row in enumerate(graph.adjacency))
    t = tuple(sc.local_triangle_report(i, row, bits, p, bound / BUDGET.triangle, t_rng)
              for i, row in enumerate(graph.adjacency))
    return s, t, s_rng.scales, t_rng.scales


@pytest.mark.parametrize("bits", [(False,)*10, (True,)*10,
                                  (True, False, True, False, True, True, False, False, True, False)])
def test_fixed_transcript_neighbor_sensitivity_and_full_density_ratio(bits):
    edges = [(0, 1), (0, 3), (0, 4), (1, 4), (2, 3)]
    before = SimpleGraph.from_edges(5, edges)
    after = SimpleGraph.from_edges(5, edges + [(1, 3)])
    bound, x = 3, (-2., .5, 0., 3., -1.)
    assert max(map(len, after.adjacency)) == bound
    s0, t0, ss0, ts0 = centers_and_scales(before, x, bits, bound)
    s1, t1, ss1, ts1 = centers_and_scales(after, x, bits, bound)
    assert ss0 == ss1 and ts0 == ts1  # Same transcript => same noise scales.
    assert [i for i in range(5) if s0[i] != s1[i]] == [1, 3]
    assert all(t0[i] == t1[i] for i in (0, 1, 2, 4))
    for i in range(5):
        assert abs(s1[i] - s0[i]) <= abs(x[i]) * max(map(abs, x))
    # Adding lower neighbor 1 to row 3 creates exactly pairs (0,1),(1,2).
    p = sc.rr_parameters(BUDGET.rr).flip_probability
    assert t1[3] - t0[3] == pytest.approx(bits[0] + bits[2] - 2*p)
    assert abs(t1[3] - t0[3]) <= bound - 1
    assert s0[2] == s1[2] == ss0[2] == 0.  # Degenerate, data-independent report.
    d0, d1 = [len(row) for row in before.adjacency], [len(row) for row in after.adjacency]
    assert [i for i in range(5) if d0[i] != d1[i]] == [1, 3]
    truth0, truth1 = packed_truth(before), packed_truth(after)
    assert [i for i in range(10) if truth0[i] != truth1[i]] == [4]

    # Selected output values, in both tails. Exact Laplace log-density ratios
    # (equal conditional scales) plus the full independent RR table ratio.
    for direction in (-1, 1):
        degree_ratio = math.fsum((abs(x[i]+1-d1[i])-abs(x[i]+1-d0[i])) * BUDGET.degree
                                 for i in range(5))
        rr_ratio = math.fsum(math.log((1-p if bit == a else p) /
                                     (1-p if bit == b else p))
                             for bit, a, b in zip(bits, truth0, truth1))
        ratios = []
        for first, second, scales in ((s0, s1, ss0), (t0, t1, ts0)):
            ratio = 0.
            for a, b, scale in zip(first, second, scales):
                if scale == 0:
                    assert a == b
                    continue
                output = (max(a, b) if direction > 0 else min(a, b)) + direction*10*scale
                ratio += (abs(output-b) - abs(output-a)) / scale
            ratios.append(ratio)
        assert abs(degree_ratio) <= 2*BUDGET.degree + 1e-12
        assert abs(rr_ratio) <= BUDGET.rr + 1e-12
        assert abs(ratios[0]) <= BUDGET.product + 1e-12
        assert abs(ratios[1]) <= BUDGET.triangle + 1e-12
        assert abs(degree_ratio + rr_ratio + sum(ratios)) <= BUDGET.total + 1e-12


def test_triangle_bound_saturation_and_ignored_upper_neighbor():
    p, bound, vertex = sc.rr_parameters(BUDGET.rr).flip_probability, 3, 3
    for bit in (False, True):
        bits = (bit,)*10
        before = sc.local_triangle_report(vertex, frozenset({0, 1}), bits, p, 0., NoiseProbe())
        after = sc.local_triangle_report(vertex, frozenset({0, 1, 2}), bits, p, 0., NoiseProbe())
        upper = sc.local_triangle_report(vertex, frozenset({0, 1, 4}), bits, p, 0., NoiseProbe())
        assert after-before == pytest.approx((bound-1)*(int(bit)-p))
        assert upper == before


@pytest.mark.parametrize("edges", [[(0, 1), (1, 2), (2, 3)],
                                   [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3)]])
def test_degree_polynomial_mean_and_variance_with_shared_degrees(edges):
    graph = SimpleGraph.from_edges(4, edges)
    a = tuple(len(row)-1 for row in graph.adjacency)
    sigma = math.sqrt(2)/BUDGET.degree
    # 16 exact moment cubature nodes, NOT draws or simulated Laplace trials.
    # The squared multilinear polynomial has exponent <=2 per variable, so
    # independent +/-sigma reproduces all required Laplace moments exactly.
    values = []
    for signs in product((-1, 1), repeat=4):
        x = tuple(ai + sign*sigma for ai, sign in zip(a, signs))
        values.append(.5*sum(sc.local_product_report(i, row, x, max(map(abs, x)),
                                                     BUDGET.product, NoiseProbe())
                             for i, row in enumerate(graph.adjacency)))
    mean = math.fsum(values)/len(values)
    expected = sum(a[u]*a[v] for u, v in edges)
    coefficients = [sum(a[u] for u in row) for row in graph.adjacency]
    variance = sigma**2 * sum(c*c for c in coefficients) + len(edges)*sigma**4
    assert mean == pytest.approx(expected, abs=1e-12)
    assert math.fsum((value-mean)**2 for value in values)/len(values) == pytest.approx(variance)


@pytest.mark.parametrize("closing_edge", [False, True])
def test_triangle_shared_rr_covariance_and_unbiasedness(closing_edge):
    edges = [(0, 2), (1, 2), (0, 3), (1, 3)] + ([(0, 1)] if closing_edge else [])
    graph = SimpleGraph.from_edges(4, edges)
    p, q = sc.rr_parameters(BUDGET.rr).flip_probability, math.tanh(BUDGET.rr/2)
    values = []
    for bit in (False, True):
        bits = (bit, False, False, False, False, False)
        values.append(sum(sc.local_triangle_report(i, row, bits, p, 0., NoiseProbe())
                          for i, row in enumerate(graph.adjacency))/q)
    probability_one = 1-p if closing_edge else p
    weights = [1-probability_one, probability_one]
    mean = sum(w*v for w, v in zip(weights, values))
    variance = sum(w*(v-mean)**2 for w, v in zip(weights, values))
    assert mean == pytest.approx(count_triangles(graph), abs=1e-12)
    assert variance == pytest.approx(4*p*(1-p)/q**2)  # c_01=2, not two independent bits.
    assert variance > 2*p*(1-p)/q**2


def test_conditional_noise_variances_include_half_and_triangle_debiasing():
    graph = SimpleGraph.from_edges(3, [(0, 1), (1, 2)])
    x, bound = (-2., .5, 3.), 2
    h, p, q = 3., sc.rr_parameters(BUDGET.rr).flip_probability, math.tanh(BUDGET.rr/2)
    products, triangles = [], []
    for signs in product((-1, 1), repeat=3):
        # Match mean=0 and variance=2 of unit Laplace; no RNG or Monte Carlo.
        products.append(.5*sum(sc.local_product_report(i, row, x, h, BUDGET.product,
                                                       NoiseProbe(signs[i]*math.sqrt(2)))
                               for i, row in enumerate(graph.adjacency)))
        triangles.append(sum(sc.local_triangle_report(i, row, (False,)*3, p,
                                                      bound/BUDGET.triangle,
                                                      NoiseProbe(signs[i]*math.sqrt(2)))
                             for i, row in enumerate(graph.adjacency))/q)
    def variance(values):
        mean = math.fsum(values)/len(values)
        return math.fsum((v-mean)**2 for v in values)/len(values)
    assert variance(products) == pytest.approx(2*h*h*sum(v*v for v in x)/BUDGET.product**2)
    assert variance(triangles) == pytest.approx(2*3*bound**2/BUDGET.triangle**2/q**2)


def test_zero_degree_bound_still_has_degree_product_noise():
    # Exact one-vertex Laplace moment quadrature through degree four:
    # P(Z=0)=5/6 and P(Z=+/-sqrt(12)b)=1/12, with b=1/epsilon_D.
    # There are no edges, so all error comes from the product release noise.
    epsilon_d, epsilon_s = 10., .6
    nodes = [(0., 5/6), (-math.sqrt(12)/epsilon_d, 1/12), (math.sqrt(12)/epsilon_d, 1/12)]
    variance = 0.
    for z, probability in nodes:
        x, rng = (z-1.,), NoiseProbe()
        assert sc.local_product_report(0, frozenset(), x, abs(x[0]), epsilon_s, rng) == 0.
        variance += probability * .25 * 2 * rng.scales[0]**2
    exact = 2/epsilon_s**2 * (1 + 12/epsilon_d**2 + 24/epsilon_d**4)
    assert variance == pytest.approx(exact)
    assert variance > 2/epsilon_s**2  # Does not vanish as epsilon_D grows.


def test_characterize_tiny_rr_budget_rounding_limitation():
    # Known unresolved numeric limitation, NOT an assertion of unbiasedness.
    # The public API accepts this epsilon; floating p loses its edge signal.
    budget = sc.SCEscapeBudget(.4, 1e-20, .6, .8)
    p, q = sc.rr_parameters(budget.rr).flip_probability, math.tanh(budget.rr/2)
    assert p == .5 and q > 0
    outputs = [sc.local_triangle_report(2, frozenset({0, 1}), (bit, False, False),
                                        p, 0., NoiseProbe())/q for bit in (False, True)]
    assert .5*outputs[0] + .5*outputs[1] == 0.  # True closing edge would give T=1.


