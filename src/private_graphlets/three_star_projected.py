"""Paper-style capped 3-star counting with optional tighter sensitivity.

Research simulation only; NumPy's RNG is not cryptographically secure.

Based on Imola, Murakami, Chaudhuri (USENIX Security 2021), Algorithm 1.
The 'paper' sensitivity matches their conservative C(B,2). 'tight' uses
C(B-1,2), the exact scalar sensitivity for C(min(degree,B),3).
For whole-undirected-edge LEDP, each endpoint is allocated epsilon/2,
so the local Laplace scale is 2*sensitivity/epsilon.

B is assumed to be a PUBLIC cap fixed before examining this graph, or a
previously released DP value whose own privacy budget is separately charged.
This module does not privately select B.
"""

from dataclasses import dataclass
from itertools import combinations
import math
from numbers import Integral
from typing import Iterator

import numpy as np

from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import make_rng, validate_epsilon


@dataclass(frozen=True, slots=True)
class PrivateProjectedThreeStarResult:
    estimate: float
    epsilon: float
    laplace_scale: float
    num_vertices: int
    degree_cap: int
    sensitivity: int
    sensitivity_mode: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "result_type": "private_estimate",
            "mechanism": "local_laplace_projected_three_star",
            "pattern": "3-star",
            "count_semantics": "non-induced",
            "estimate": self.estimate,
            "epsilon": self.epsilon,
            "laplace_scale": self.laplace_scale,
            "num_vertices": self.num_vertices,
            "degree_cap": self.degree_cap,
            "sensitivity": self.sensitivity,
            "sensitivity_mode": self.sensitivity_mode,
            "privacy_model": "ideal_undirected_edge_LEDP",
            "simulation_only": True,
        }


def validate_public_degree_cap(graph: SimpleGraph, cap: int) -> int:
    if isinstance(cap, bool) or not isinstance(cap, Integral):
        raise ValueError("degree_cap must be a public nonnegative integer")
    cap = int(cap)
    if cap < 0 or cap > max(0, graph.num_vertices - 1):
        raise ValueError("degree_cap must lie in [0, max(0, n-1)]")
    return cap


def clipped_three_star_sensitivity(cap: int, mode: str = "tight") -> int:
    """Sensitivity of a LOCAL scalar star count under one incident-edge change.

    'paper' uses C(B,2) (conservative, paper Algorithm 1).
    'tight' uses C(B-1,2) (exact for C(min(d,B),3)).
    """
    if isinstance(cap, bool) or not isinstance(cap, Integral) or cap < 0:
        raise ValueError("cap must be a nonnegative integer")
    if mode == "tight":
        return math.comb(cap - 1, 2) if cap >= 3 else 0
    if mode == "paper":
        return math.comb(cap, 2) if cap >= 2 else 0
    raise ValueError("sensitivity_mode must be 'paper' or 'tight'")


def retained_star_neighbors(graph: SimpleGraph, vertex: int, degree_cap: int) -> tuple[int, ...]:
    """LOCAL ONLY: public-ID deterministic neighbor projection for future diamond.

    Do not release this tuple: it exposes actual edges. If a changed edge
    causes a retained-neighbor replacement, two retained IDs can change;
    the diamond local-score sensitivity must account for this.
    """
    cap = validate_public_degree_cap(graph, degree_cap)
    if isinstance(vertex, bool) or not isinstance(vertex, Integral) or not 0 <= vertex < graph.num_vertices:
        raise ValueError("vertex must be a valid public vertex ID")
    return tuple(sorted(graph.adjacency[int(vertex)])[:cap])


def retained_star_triples(graph: SimpleGraph, vertex: int, degree_cap: int) -> Iterator[tuple[int, int, int]]:
    """LOCAL ONLY: candidates for star-based diamond score; never transmit."""
    yield from combinations(retained_star_neighbors(graph, vertex, degree_cap), 3)


def estimate_three_stars_projected(
    graph: SimpleGraph,
    epsilon: float,
    degree_cap: int,
    *,
    sensitivity_mode: str = "tight",
    seed: int | None = None,
    rng: np.random.Generator | None = None,
) -> PrivateProjectedThreeStarResult:
    """Estimate non-induced 3-stars via Laplace-noised capped local counts.

    The paper uses mode='paper'. Mode='tight' preserves the same ideal
    edge privacy accounting but lowers sensitivity for scalar star counting.
    Clipping introduces downward bias for the ORIGINAL, uncapped graph count.
    The output and to_dict expose no per-node degrees or reports.
    """
    epsilon = validate_epsilon(epsilon)
    degree_cap = validate_public_degree_cap(graph, degree_cap)
    sensitivity = clipped_three_star_sensitivity(degree_cap, sensitivity_mode)
    if seed is not None and rng is not None:
        raise ValueError("provide either seed or rng, not both")
    if rng is None:
        rng = make_rng(seed)

    # Whole-edge privacy: the changed undirected edge touches two local reports.
    scale = 2.0 * sensitivity / epsilon
    if not math.isfinite(scale):
        raise ValueError("Laplace scale exceeds the finite float64 range")

    # For a 3-star, only the clipped DEGREE matters; no neighbor identities
    # need to be computed, and random projection would give the same count.
    local_degrees = (min(len(adj), degree_cap) for adj in graph.adjacency)
    local_counts = (math.comb(d, 3) if d >= 3 else 0 for d in local_degrees)

    if sensitivity == 0:
        # Every local count is identically zero; there is no information to leak.
        aggregate = 0.0
    else:
        noise = rng.laplace(loc=0.0, scale=scale, size=graph.num_vertices)
        if not np.all(np.isfinite(noise)):
            raise FloatingPointError("nonfinite Laplace draw")
        try:
            aggregate = math.fsum(float(count) + float(z) for count, z in zip(local_counts, noise))
        except OverflowError as exc:
            raise FloatingPointError("private count overflow") from exc
    if not math.isfinite(aggregate):
        raise FloatingPointError("nonfinite private estimate")
    return PrivateProjectedThreeStarResult(
        aggregate, epsilon, scale, graph.num_vertices,
        degree_cap, sensitivity, sensitivity_mode,
    )
