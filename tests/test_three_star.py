"""Mechanism, release boundary, and polynomial regression tests."""

from dataclasses import asdict
import json
from math import comb
from unittest.mock import Mock

import numpy as np
import pytest

from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import make_rng
from private_graphlets.three_star import corrected_local_stars, estimate_three_stars


def test_polynomial_values_and_unbounded_negative_output():
    # Hand-calculated with b=2, including nonintegral and negative reports.
    reports = [-1, -0.5, 0, 1, 2, 3, 4]
    expected = [7, 5.6875, 4, 0, -4, -7, -8]
    np.testing.assert_array_equal(corrected_local_stars(reports, 2), expected)
    assert corrected_local_stars(3.0, 2) == -7


def test_full_pipeline_scale_isolates_and_release_boundary():
    # Zero noise is a deterministic probe of plumbing, not an unbiasedness test.
    graph = SimpleGraph.from_edges(6, [(0, 1), (0, 2), (0, 3)])
    rng = Mock()
    rng.laplace.return_value = np.zeros(6)
    result = estimate_three_stars(graph, 1.0, rng=rng)
    rng.laplace.assert_called_once_with(0.0, 2.0, size=6)
    # Center contributes -7, leaves 0, and two isolated vertices contribute 4 each.
    assert result.estimate == 1.0
    assert set(asdict(result)) == {"estimate", "epsilon", "laplace_scale", "num_vertices"}
    release = result.to_dict()
    assert set(release) == {
        "schema_version", "result_type", "mechanism", "pattern", "count_semantics",
        "estimate", "epsilon", "laplace_scale", "num_vertices", "simulation_only",
    }
    assert release["result_type"] == "private_estimate"
    json.dumps(release, allow_nan=False)


def test_negative_estimate_not_clipped_or_rounded():
    rng = Mock()
    rng.laplace.return_value = np.array([0.25, 0.0, 0.0, 0.0])
    graph = SimpleGraph.from_edges(4, [(0, 1), (0, 2), (0, 3)])
    result = estimate_three_stars(graph, 1.0, rng=rng)
    assert result.estimate == -7.4765625


def test_seeded_results_and_edge_order_invariance():
    graph = SimpleGraph.from_edges(5, [(0, 2), (1, 2), (2, 3)])
    duplicate_rows = SimpleGraph.from_edges(5, [(3, 2), (2, 1), (2, 0), (0, 2)])
    first = estimate_three_stars(graph, 2.0, seed=761)
    assert first == estimate_three_stars(graph, 2.0, seed=761)
    assert first == estimate_three_stars(duplicate_rows, 2.0, seed=761)
    assert first == estimate_three_stars(graph, 2.0, rng=make_rng(761))
    assert first != estimate_three_stars(graph, 2.0, seed=762)
    rng = make_rng(761)
    assert estimate_three_stars(graph, 2.0, rng=rng) != estimate_three_stars(graph, 2.0, rng=rng)


def test_empty_graph_release():
    assert estimate_three_stars(SimpleGraph.from_edges(0, []), 1, seed=0).estimate == 0.0


@pytest.mark.parametrize("epsilon", [0, -2, float("nan"), float("inf"), -float("inf"), True])
def test_estimator_rejects_epsilon_before_sampling(epsilon):
    rng = Mock()
    with pytest.raises(ValueError, match="epsilon"):
        estimate_three_stars(SimpleGraph.from_edges(0, []), epsilon, rng=rng)
    rng.laplace.assert_not_called()


def test_seed_and_rng_mutually_exclusive():
    with pytest.raises(ValueError, match="either"):
        estimate_three_stars(SimpleGraph.from_edges(1, []), 1, seed=3, rng=make_rng(3))


@pytest.mark.parametrize("scale", [0, -1, float("inf"), float("nan")])
def test_invalid_correction_scale(scale):
    with pytest.raises(ValueError, match="scale"):
        corrected_local_stars([1], scale)


@pytest.mark.parametrize("report", [float("inf"), float("nan"), -float("inf")])
def test_invalid_report(report):
    with pytest.raises(ValueError, match="finite"):
        corrected_local_stars(report, 1)


@pytest.mark.parametrize("epsilon", [1e-200, 1e308])
def test_extreme_parameters_fail_without_releasing_infinity(epsilon):
    with pytest.raises(FloatingPointError):
        estimate_three_stars(SimpleGraph.from_edges(1, []), epsilon, seed=1)


def test_polynomial_overflow_not_silently_replaced():
    with pytest.raises(FloatingPointError):
        corrected_local_stars(1e200, 1)


@pytest.mark.parametrize("scale", [0.25, 1.0, 2.5])
def test_correction_expectation_by_polynomial_quadrature(scale):
    # Four-point Gauss-Laguerre integrates e^-x times degree <= 7 exactly
    # (up to float error). Symmetrization supplies Laplace(0,b) moments.
    nodes, weights = np.polynomial.laguerre.laggauss(4)
    for degree in (0, 1, 2, 3, 4, 9):
        plus = corrected_local_stars(degree + scale * nodes, scale)
        minus = corrected_local_stars(degree - scale * nodes, scale)
        mean = np.dot(weights, (plus + minus) / 2)
        assert mean == pytest.approx(comb(degree, 3), abs=2e-12, rel=2e-12)
