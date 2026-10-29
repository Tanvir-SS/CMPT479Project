"""Fixed-seed Monte Carlo checks with six analytic standard-error tolerances.

These are diagnostics of the implementation, not formal proofs of independence,
unbiasedness, or differential privacy. See docs/ALGORITHMS.md for moments.
"""

from itertools import combinations
from math import comb, sqrt

import numpy as np
import pytest

from private_graphlets.exact import count_three_stars_bruteforce
from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import make_rng, sample_degree_noise
from private_graphlets.three_star import corrected_local_stars, estimate_three_stars


STANDARD_ERRORS = 6.0


def assert_mean(observed, expected, standard_error, label):
    z = (observed - expected) / standard_error
    print(f"{label}: observed={observed:.9g}, expected={expected:.9g}, SE={standard_error:.6g}, z={z:.4f}")
    assert abs(z) < STANDARD_ERRORS, label


def local_variance(degree, scale):
    # Independent derivation from E[Z^(2k)]=(2k)! b^(2k).
    t = degree - 1
    a = (3 * t**2 - 1) / 6
    return 2 * a**2 * scale**2 + (7 * t**2 - 2 / 3) * scale**4 + 14 * scale**6


@pytest.mark.parametrize("epsilon", [0.5, 2.0, 8.0])
def test_noise_moments_and_independence_diagnostics(epsilon):
    n = 200_000
    b = 2 / epsilon
    samples = sample_degree_noise(epsilon, size=(n, 2), rng=make_rng(2026102801))
    x, y = samples.T
    assert_mean(x.mean(), 0, sqrt(2 * b**2 / n), f"noise mean eps={epsilon}")
    # Exact variance of the unbiased sample variance (ddof=1).
    variance_se = sqrt((24 * b**4 - (n - 3) / (n - 1) * 4 * b**4) / n)
    assert_mean(x.var(ddof=1), 2 * b**2, variance_se, f"noise variance eps={epsilon}")
    assert_mean(np.mean(x * y), 0, 2 * b**2 / sqrt(n), f"noise cross moment eps={epsilon}")
    # Also detect dependence invisible to a signed covariance test.
    assert_mean(np.mean(x**2 * y**2), 4 * b**4, sqrt(560 * b**8 / n),
                f"squared noise cross moment eps={epsilon}")
    assert_mean(np.mean((x > 0) & (y > 0)), 0.25, sqrt(0.25 * 0.75 / n),
                f"joint signs eps={epsilon}")


@pytest.mark.parametrize("scale", [0.25, 1.0, 2.5])
def test_variance_formula_against_quadrature(scale):
    nodes, weights = np.polynomial.laguerre.laggauss(4)
    for degree in (0, 1, 2, 3, 7):
        mean = comb(degree, 3)
        positive = corrected_local_stars(degree + scale * nodes, scale) - mean
        negative = corrected_local_stars(degree - scale * nodes, scale) - mean
        integrated_variance = np.dot(weights, (positive**2 + negative**2) / 2)
        assert integrated_variance == pytest.approx(local_variance(degree, scale), rel=2e-12)


@pytest.mark.parametrize("epsilon", [0.8, 2.0, 8.0])
def test_empirical_polynomial_unbiasedness(epsilon):
    n = 200_000
    b = 2 / epsilon
    degrees = np.array([0, 1, 2, 3, 4, 9])
    reports = degrees + sample_degree_noise(epsilon, size=(n, len(degrees)), rng=make_rng(2026102802))
    estimates = corrected_local_stars(reports, b)
    for column, degree in enumerate(degrees):
        assert_mean(estimates[:, column].mean(), comb(int(degree), 3),
                    sqrt(local_variance(degree, b) / n), f"local d={degree} eps={epsilon}")


GRAPHS = [
    ("isolates", SimpleGraph.from_edges(4, [])),
    ("star", SimpleGraph.from_edges(5, [(0, v) for v in range(1, 5)])),
    ("K4", SimpleGraph.from_edges(4, combinations(range(4), 2))),
    ("overlap_and_isolates", SimpleGraph.from_edges(8, [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)])),
]


@pytest.mark.parametrize("name,graph", GRAPHS, ids=[name for name, _ in GRAPHS])
@pytest.mark.parametrize("epsilon", [0.8, 4.0])
def test_empirical_graph_unbiasedness(name, graph, epsilon):
    n = 12_000
    rng = make_rng(2026102803)
    # Exercise the public estimator on EVERY trial, rather than only its polynomial.
    estimates = np.array([estimate_three_stars(graph, epsilon, rng=rng).estimate for _ in range(n)])
    truth = count_three_stars_bruteforce(graph)
    variance = sum(local_variance(len(row), 2 / epsilon) for row in graph.adjacency)
    assert_mean(estimates.mean(), truth, sqrt(variance / n), f"graph {name} eps={epsilon}")
