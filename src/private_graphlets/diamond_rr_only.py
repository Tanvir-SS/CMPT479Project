"""One-round, one-owner debiased-RR non-induced diamond research simulator.

Each unordered pair (u,v), including nonedges, is randomized once by min(u,v)
through the existing randomized_response module. The server evaluates the
supplied diamond polynomial without Laplace noise, degrees or raw adjacency.
The pure edge-LDP label describes the ideal model, not certified NumPy/float
execution. Simulation seeds are not cryptographically secure deployment noise.
"""

from dataclasses import asdict, dataclass
import math
from numbers import Integral

import numpy as np

from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import validate_epsilon
from private_graphlets.randomized_response import sample_rr_upper, rr_matrix


def diamond_polynomial(weights: np.ndarray) -> float:
    """Sum W_ab * W_ac W_bc W_ad W_bd over a<b and c<d outside {a,b}.

    W@W and (W*W)@(W*W) give the sum and sum of squares of common-neighbor
    products in O(n³) time/O(n²) storage. Input W must have a zero diagonal;
    neither the input nor its read-only RR matrix is modified. Signed estimates
    are preserved. This is post-processing, not itself a private randomizer.
    """
    # Float arithmetic also supports adjacency matrices in offline exact checks
    # without integer matmul overflow. Actual rr_matrix output is already float64.
    weights = np.asarray(weights, dtype=float)
    if weights.ndim != 2 or weights.shape[0] != weights.shape[1]:
        raise ValueError("expected square weight matrix")
    if not np.all(np.isfinite(weights)):
        raise ValueError("weights must be finite")
    if not np.array_equal(weights, weights.T) or np.any(np.diag(weights) != 0):
        raise ValueError("weights must be symmetric with zero diagonal")
    with np.errstate(over="raise", invalid="raise"):
        wedge_sum = weights @ weights
        squares = weights * weights
        wedge_squares = squares @ squares
        contributions = 0.5 * weights * (wedge_sum * wedge_sum - wedge_squares)
        estimate = float(np.sum(np.triu(contributions, k=1)))
    if not math.isfinite(estimate):
        raise FloatingPointError("nonfinite RR-only diamond estimate")
    return estimate


@dataclass(frozen=True, slots=True)
class RROnlyDiamondResult:
    estimate: float
    epsilon: float
    num_vertices: int
    pattern: str = "diamond"
    count_semantics: str = "non-induced_unlabeled"
    privacy_model: str = "ideal_pure_edge_LDP_one_owner"
    privacy_status: str = "experimental_unverified"

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_rr_only_diamonds(
    graph: SimpleGraph, epsilon: float, *, seed: int | None = None,
) -> RROnlyDiamondResult:
    """Use the entire epsilon for the existing one-owner RR table, exactly once."""
    epsilon = validate_epsilon(epsilon)
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0):
        raise ValueError("seed must be nonnegative integer")
    rng = np.random.default_rng(None if seed is None else int(seed))
    bits = sample_rr_upper(graph, epsilon, rng)
    weights = rr_matrix(graph.num_vertices, bits, epsilon)
    return RROnlyDiamondResult(diamond_polynomial(weights), epsilon, graph.num_vertices)
