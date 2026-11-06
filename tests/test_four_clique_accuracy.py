"""Independent exact moments, retained targets and finite-n bounds; no empirical DP claim."""

from fractions import Fraction
from itertools import combinations, permutations, product
import math

import networkx as nx
import numpy as np
import pytest

from private_graphlets.four_clique import conditional_sensitivity, simulate_four_cliques
from private_graphlets.four_clique_accuracy import (
    baseline_error, baseline_variance_coefficients, cap_underestimate_probability,
    conditional_error, enumerate_rr_moments, evaluate_polynomial, ideal_count_sensitivity,
    ideal_rr_variance, retained_cliques_bruteforce, rr_upper_bound,
    rr_variance_coefficients, triangle_multiplicities,
)
from private_graphlets.four_clique_exact import count_four_cliques, count_four_cliques_bruteforce
from private_graphlets.graph import SimpleGraph


def clique(n): return SimpleGraph.from_edges(n, combinations(range(n),2))


def from_mask(n, mask):
    return SimpleGraph.from_edges(n,[e for i,e in enumerate(combinations(range(n),2)) if mask >> i & 1])


def book(r):
    leaves = tuple(range(r,r+3))
    return SimpleGraph.from_edges(r+3,[*combinations(leaves,2),*((v,w) for v in range(r) for w in leaves)])


@pytest.mark.parametrize('odds', [Fraction(5,4),2,3,20])
@pytest.mark.parametrize('adjacency', [0,1])
def test_single_pair_exact_moments(odds, adjacency):
    outcomes = [(Fraction(odds if bit == adjacency else 1,odds+1),
                 Fraction((odds+1)*bit-1,odds-1)) for bit in (0,1)]
    mean = sum(p*w for p,w in outcomes)
    variance = sum(p*(w-mean)**2 for p,w in outcomes)
    assert mean == adjacency
    assert variance == Fraction(odds,(odds-1)**2)
    assert ideal_rr_variance(math.log(odds)) == pytest.approx(float(variance))


def test_all_four_vertex_graphs_full_rr_tables_candidate_and_baseline():
    # 64 graphs x two independent counting paths x all 64 output tables.
    for mask in range(64):
        g = from_mask(4,mask)
        exact = enumerate_rr_moments(g,range(4),3)
        predicted = conditional_error(g,range(4),3,math.log(2),1.)
        assert exact.table_count == 64 and exact.enumerated_pair_count == 6
        assert exact.mean == predicted.retained_count == count_four_cliques_bruteforce(g)
        assert exact.variance == evaluate_polynomial(predicted.rr_coefficients,2)
        baseline = enumerate_rr_moments(g,range(4),3,baseline=True)
        assert baseline.mean == predicted.exact_count
        assert baseline.variance == evaluate_polynomial(baseline_variance_coefficients(g),2)


def test_all_graphs_through_five_orders_caps_retained_counts_and_bound():
    checks = 0
    for n in range(6):
        for mask in range(1 << math.comb(n,2)):
            g = from_mask(n,mask)
            orders = permutations(range(n)) if n <= 4 else (tuple(range(n)),tuple(reversed(range(n))))
            for order in orders:
                for cap in range(max(1,n)):
                    result = conditional_error(g,order,cap,math.log(2),1.)
                    assert result.retained_count == count_four_cliques(g,order,cap=cap)
                    assert 0 <= result.retained_count <= result.exact_count
                    assert result.exact_count == count_four_cliques_bruteforce(g)
                    assert result.rr_variance <= result.rr_variance_upper_bound
                    assert result.mse <= result.mse_upper_bound
                    assert result.sensitivity == pytest.approx(conditional_sensitivity(cap,math.log(2)))
                    checks += 1
    assert checks == 16538


def test_known_exact_values_and_cross_root_dependencies():
    k4 = conditional_error(clique(4),range(4),3,math.log(2),1.)
    assert (k4.rr_variance,k4.laplace_variance,k4.clipping_bias_squared,k4.mse) == (26.,1152.,0,1178.)
    k5 = conditional_error(clique(5),range(5),3,math.log(2),1.)
    assert k5.rr_coefficients == (8,6,2)
    assert (k5.retained_count,k5.rr_variance,k5.laplace_variance,k5.clipping_bias_squared,k5.mse) == (2,56.,1440.,9,1505.)
    assert enumerate_rr_moments(clique(5),range(5),3).variance == 56
    uncapped = conditional_error(clique(5),range(5),4,math.log(2),1.)
    assert uncapped.rr_coefficients == (39,21,7) and uncapped.rr_variance == 218
    g = book(6)
    assert triangle_multiplicities(g,range(9),3) == {(6,7,8):6}
    b = conditional_error(g,range(9),3,math.log(2),1.)
    assert (b.rr_variance,b.laplace_variance,b.mse) == (936.,2592.,3528.)
    marginal = enumerate_rr_moments(g,range(9),3,include_unused_pairs=False)
    assert marginal.enumerated_pair_count == 3 and marginal.full_pair_count == 36
    assert marginal.mean == 6 and marginal.variance == 936
    # Incorrect independent-root calculation gives 6*26=156, not 36*26.
    assert b.rr_variance != 6*26


def test_baseline_shared_three_edges_and_nonprivate_schema():
    prediction = baseline_error(clique(5),math.log(2))
    exact = enumerate_rr_moments(clique(5),range(5),4,baseline=True)
    assert exact.mean == 5 and exact.variance == 4160
    assert prediction['rr_variance'] == 4160  # includes 2*C(5,2)*26 covariance.
    assert prediction['result_type'] == 'nonprivate_ideal_error_evaluation'
    assert conditional_error(clique(4),range(4),3,1,1).to_dict()['result_type'].startswith('nonprivate')


def test_baseline_one_shared_edge_and_rational_fourth_moments():
    # K6: 15 four-sets, 60 unordered pairs sharing 3 vertices, 45 sharing 2.
    assert baseline_error(clique(6),math.log(2))['rr_variance'] == 15*728+2*(60*26+45*2)
    moments = enumerate_rr_moments(clique(4),range(4),3,odds=Fraction(5,4))
    assert moments.mean == 1 and moments.variance == 21**3-1
    assert moments.fourth_central >= moments.variance**2
    with pytest.raises(ValueError): enumerate_rr_moments(clique(4),range(4),3,odds=1)


def test_triangles_without_cliques_and_absent_shared_edge_covariance():
    # K5 missing one edge contains nonclique closing triples, yet positive covariance.
    g = SimpleGraph.from_edges(5,[e for e in combinations(range(5),2) if e != (3,4)])
    m = enumerate_rr_moments(g,range(5),4)
    prediction = conditional_error(g,range(5),4,math.log(2),1)
    assert m.mean == prediction.exact_count and m.variance == prediction.rr_variance
    triangle = SimpleGraph.from_edges(5,[(0,1),(0,2),(1,2)])
    p = conditional_error(triangle,range(5),4,1,1)
    assert p.rr_expectation == p.exact_count == 0 and p.rr_variance == 0
    assert p.laplace_variance > 0


def test_private_cap_exact_tail_includes_ceiling():
    p = cap_underestimate_probability(clique(4),range(4),math.log(2),.5)
    assert p['probability'] == pytest.approx(1/16384)
    assert p['single_max_bound'] == pytest.approx(1/32)
    assert p['probability'] <= p['multiple_max_bound'] <= p['single_max_bound'] < .5/2
    assert p['original_count_squared_loss_bound'] == p['probability']
    assert cap_underestimate_probability(from_mask(6,0),range(6),1,.05)['probability'] == 0
    assert cap_underestimate_probability(clique(3),range(3),1,.05)['probability'] == 0


def test_squared_conditional_bias_is_not_squared_mean_bias():
    values = [conditional_error(clique(5),range(5),cap,1,1) for cap in (2,4)]
    expected_square = sum(v.clipping_bias_squared for v in values)/2
    squared_mean = (sum(v.conditional_bias for v in values)/2)**2
    assert expected_square == 12.5 and squared_mean == 6.25
    assert expected_square-squared_mean == np.var([v.retained_count for v in values])


@pytest.mark.parametrize('eta', [1e-4, .1, 1., 30.])
def test_sensitivity_and_bound_stability(eta):
    for cap in (0,1,2,3,7):
        assert ideal_count_sensitivity(cap,eta) == pytest.approx(conditional_sensitivity(cap,eta),rel=1e-14)
        prediction = conditional_error(clique(8),range(8),cap,eta,1.)
        assert math.isfinite(prediction.mse) and prediction.mse <= prediction.mse_upper_bound


@pytest.mark.parametrize('bad', [0.,-1.,float('nan'),float('inf'),True,31.,1e-310])
def test_analytical_rr_invalid(bad):
    with pytest.raises(ValueError): ideal_rr_variance(bad)


def test_invalid_analysis_inputs_and_sampling_independence(monkeypatch):
    for module, name in [('four_clique','local_score'),('four_clique','conditional_sensitivity'),
                         ('randomized_response','rr_parameters')]:
        monkeypatch.setattr(f'private_graphlets.{module}.{name}',lambda *a,**k: pytest.fail('calculator called mechanism'))
    assert conditional_error(clique(4),range(4),3,math.log(2),1).mse == 1178
    for order, cap in [((0,0,2,3),3),(range(4),True),(range(4),4),(range(4),-1)]:
        with pytest.raises(ValueError): conditional_error(clique(4),order,cap,1,1)
    with pytest.raises(ValueError): conditional_error(clique(21),range(21),3,1,1)
    with pytest.raises(ValueError): conditional_error(clique(4),range(4),3,1,0)
    with pytest.raises(ValueError): enumerate_rr_moments(clique(6),range(6),5)


@pytest.mark.escape_integration
@pytest.mark.parametrize('kind', ['empty0','empty6','K4','K5','K8','triangle','book6','sparse','dense'])
def test_named_exact_and_retained_cases_against_escape(escape_adapter, kind):
    if kind.startswith('empty'): g = SimpleGraph.from_edges(int(kind[5:]),[])
    elif kind.startswith('K'): g = clique(int(kind[1:]))
    elif kind=='triangle': g = SimpleGraph.from_edges(6,combinations(range(3),2))
    elif kind=='book6': g = book(6)
    else:
        sampled = nx.gnp_random_graph(8,.2 if kind=='sparse' else .75,seed=900101 if kind=='sparse' else 900102)
        g = SimpleGraph.from_edges(8,sampled.edges())
    truth = escape_adapter.run(g).counts.connected_four['4-clique']
    for order in (tuple(range(g.num_vertices)),tuple(reversed(range(g.num_vertices)))):
        for cap in range(max(1,g.num_vertices)):
            original, retained = retained_cliques_bruteforce(g,order,cap)
            assert original == truth == count_four_cliques_bruteforce(g)
            assert retained == count_four_cliques(g,order,cap=cap)
