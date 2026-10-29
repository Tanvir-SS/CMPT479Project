"""Deterministic noise contract and parameter checks."""

from unittest.mock import Mock

import numpy as np
import pytest

from private_graphlets.noise import laplace_scale, make_rng, sample_degree_noise, validate_epsilon


@pytest.mark.parametrize("epsilon", [0.1, 0.5, 1, 2, 10, np.float64(4)])
def test_correct_laplace_scale(epsilon):
    rng = Mock()
    rng.laplace.return_value = np.zeros(7)
    assert laplace_scale(epsilon) == 2.0 / epsilon
    sample_degree_noise(epsilon, size=7, rng=rng)
    rng.laplace.assert_called_once_with(0.0, 2.0 / epsilon, size=7)


INVALID_EPSILONS = [0, -1, -0.0, float("nan"), float("inf"), -float("inf"), True, "1", None]


@pytest.mark.parametrize("epsilon", INVALID_EPSILONS)
def test_invalid_epsilon(epsilon):
    for function in (validate_epsilon, laplace_scale):
        with pytest.raises(ValueError, match="epsilon"):
            function(epsilon)
    rng = Mock()
    with pytest.raises(ValueError, match="epsilon"):
        sample_degree_noise(epsilon, size=2, rng=rng)
    rng.laplace.assert_not_called()


@pytest.mark.parametrize("seed", [-1, 1.5, True, "7"])
def test_invalid_seed(seed):
    with pytest.raises(ValueError, match="seed"):
        make_rng(seed)


def test_seed_reproducibility_and_generator_advancement():
    rng = make_rng(42)
    first = sample_degree_noise(2, size=(10, 2), rng=rng)
    second = sample_degree_noise(2, size=(10, 2), rng=rng)
    replay = sample_degree_noise(2, size=(10, 2), rng=make_rng(42))
    np.testing.assert_array_equal(first, replay)
    assert not np.array_equal(first, second)
    assert not np.array_equal(first[:, 0], first[:, 1])
    assert sample_degree_noise(1, size=0, rng=rng).shape == (0,)


def test_unseeded_generator_and_numpy_integer_seed():
    assert isinstance(make_rng(), np.random.Generator)
    np.testing.assert_array_equal(make_rng(np.int64(7)).random(4), make_rng(7).random(4))


def test_numerical_failures_are_explicit():
    with pytest.raises(ValueError, match="float64"):
        laplace_scale(5e-324)
    rng = Mock()
    rng.laplace.return_value = np.array([float("inf")])
    with pytest.raises(FloatingPointError):
        sample_degree_noise(1, size=1, rng=rng)
