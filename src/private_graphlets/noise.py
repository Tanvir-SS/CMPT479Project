"""Laplace sampling for research simulations, not cryptographic deployment."""

import math
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray


def validate_epsilon(epsilon: float) -> float:
    """Require a finite positive real scalar (not a bool or numeric string)."""
    if isinstance(epsilon, bool) or not isinstance(epsilon, Real):
        raise ValueError("epsilon must be a finite positive real number")
    try:
        value = float(epsilon)
    except OverflowError as exc:
        raise ValueError("epsilon must be a finite positive real number") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError("epsilon must be a finite positive real number")
    return value


def laplace_scale(epsilon: float) -> float:
    """Return exactly 2/epsilon: one epsilon/2 report per incident endpoint."""
    scale = 2.0 / validate_epsilon(epsilon)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("2/epsilon is outside the finite positive float64 range")
    return scale


def make_rng(seed: int | None = None) -> np.random.Generator:
    """Create a fresh NumPy Generator; never reset it between vertices/trials."""
    if seed is not None:
        if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
            raise ValueError("simulation seed must be a nonnegative integer")
        seed = int(seed)
    return np.random.default_rng(seed)


def sample_degree_noise(
    epsilon: float, *, size: int | tuple[int, ...], rng: np.random.Generator
) -> NDArray[np.float64]:
    """Draw one fresh Laplace(0, 2/epsilon) sample per requested array entry."""
    noise = rng.laplace(0.0, laplace_scale(epsilon), size=size)
    if not np.all(np.isfinite(noise)):
        raise FloatingPointError("Laplace samples exceed the finite float64 range")
    return noise
