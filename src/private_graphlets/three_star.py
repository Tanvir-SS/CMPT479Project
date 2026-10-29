"""The specified bias-corrected local-degree 3-star mechanism simulation."""

from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import laplace_scale, make_rng, sample_degree_noise, validate_epsilon


@dataclass(frozen=True, slots=True)
class PrivateThreeStarResult:
    """Aggregate release and public parameters only; no degree/ground-truth data."""

    estimate: float
    epsilon: float
    laplace_scale: float
    num_vertices: int

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible experiment record; seed/state must be recorded separately."""
        return {
            "schema_version": 1,
            "result_type": "private_estimate",
            "mechanism": "laplace_degree_corrected_three_star",
            "pattern": "3-star",
            "count_semantics": "non-induced",
            "estimate": self.estimate,
            "epsilon": self.epsilon,
            "laplace_scale": self.laplace_scale,
            "num_vertices": self.num_vertices,
            "simulation_only": True,
        }


def corrected_local_stars(
    noisy_degree: ArrayLike, scale: float
) -> NDArray[np.float64] | np.float64:
    """Evaluate Y(Y-1)(Y-2)/6 - b^2(Y-1), without clipping or rounding.

    Accepts a scalar or an array of already-noisy degrees. This is postprocessing,
    not a local randomizer by itself. Scalar input produces a NumPy scalar.
    """
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("Laplace scale must be finite and positive")
    values = np.asarray(noisy_degree, dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise ValueError("noisy degrees must be finite")
    with np.errstate(over="raise", invalid="raise", under="ignore"):
        # Multiplication avoids Python's OverflowError and uses NumPy's checked arithmetic.
        scale_squared = np.float64(scale) ** 2
        if scale_squared == 0:
            raise FloatingPointError("squared Laplace scale underflows float64")
        result = (
            values * (values - 1.0) * (values - 2.0) / 6.0
            - scale_squared * (values - 1.0)
        )
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("corrected estimate exceeds the finite float64 range")
    return result


def estimate_three_stars(
    graph: SimpleGraph,
    epsilon: float,
    *,
    seed: int | None = None,
    rng: np.random.Generator | None = None,
) -> PrivateThreeStarResult:
    """Simulate independent per-vertex reports and release their corrected sum.

    Use a seed for replay, or a persistent Generator for repeated trials, never
    both. NumPy randomness (seeded or not) is not cryptographically secure.
    Isolated vertices also report. The fixed vertex set is assumed public.
    """
    epsilon = validate_epsilon(epsilon)
    scale = laplace_scale(epsilon)
    if seed is not None and rng is not None:
        raise ValueError("provide either a simulation seed or rng, not both")
    if rng is None:
        rng = make_rng(seed)
    degrees = np.fromiter(map(len, graph.adjacency), dtype=np.float64, count=graph.num_vertices)
    with np.errstate(over="raise", invalid="raise"):
        reports = degrees + sample_degree_noise(epsilon, size=graph.num_vertices, rng=rng)
    local_estimates = corrected_local_stars(reports, scale)
    try:
        estimate = math.fsum(local_estimates)
    except OverflowError as exc:
        raise FloatingPointError("aggregate estimate exceeds the finite float64 range") from exc
    if not math.isfinite(estimate):
        raise FloatingPointError("aggregate estimate exceeds the finite float64 range")
    return PrivateThreeStarResult(estimate, epsilon, scale, graph.num_vertices)
