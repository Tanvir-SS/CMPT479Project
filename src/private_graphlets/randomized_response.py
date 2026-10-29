"""One-owner unordered-pair randomized response. NumPy research simulation only."""

from dataclasses import dataclass
import math

import numpy as np

from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import validate_epsilon


@dataclass(frozen=True)
class RRParameters:
    epsilon: float
    flip_probability: float
    a: float
    maximum: float
    variance: float


def rr_parameters(epsilon: float) -> RRParameters:
    epsilon = validate_epsilon(epsilon)
    # Avoid rounding a nonzero flip probability to an effectively deterministic
    # floating-point experiment at arbitrarily large epsilon. Public validation.
    if epsilon > 30:
        raise ValueError("RR simulation supports epsilon <= 30")
    a = 1.0 / math.expm1(epsilon)
    maximum = a + 1.0
    variance = a * maximum
    if not all(math.isfinite(x) for x in (a, maximum, variance)):
        raise ValueError("RR parameters exceed the finite float64 range")
    return RRParameters(epsilon, math.exp(-epsilon)/(1+math.exp(-epsilon)), a, maximum, variance)


def local_rr_row(n: int, vertex: int, neighbors: frozenset[int], epsilon: float,
                 rng: np.random.Generator) -> tuple[bool, ...]:
    """Client reports ONLY pairs (vertex,w) with w>vertex, including nonedges."""
    p = rr_parameters(epsilon).flip_probability
    flips = rng.random(n-vertex-1) < p
    return tuple(bool((w in neighbors) ^ flip)
                 for w, flip in zip(range(vertex+1, n), flips))


def sample_rr_upper(graph: SimpleGraph, epsilon: float,
                    rng: np.random.Generator) -> tuple[bool, ...]:
    """Simulator dispatches local calls; coordinator sees only the returned bits."""
    rr_parameters(epsilon)
    return tuple(bit for v, neighbors in enumerate(graph.adjacency)
                 for bit in local_rr_row(graph.num_vertices, v, neighbors, epsilon, rng))


def rr_matrix(n: int, reports: tuple[bool, ...], epsilon: float) -> np.ndarray:
    """Coordinator postprocessing of an upper-triangular table, mirrored once."""
    if len(reports) != n*(n-1)//2 or any(type(x) is not bool for x in reports):
        raise ValueError("expected one boolean RR report per unordered pair")
    params = rr_parameters(epsilon)
    result = np.zeros((n, n), dtype=float)
    indices = np.triu_indices(n, k=1)
    result[indices] = np.where(reports, params.maximum, -params.a)
    result[(indices[1], indices[0])] = result[indices]
    result.flags.writeable = False
    return result
