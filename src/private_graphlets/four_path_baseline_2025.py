"""AISTATS 2025 Algorithm 1: faithful independent non-induced P4 reconstruction.

Uses the authors' undirected C4 notebook's one-report-per-pair convention.
Exact P4-specific algebra replaces literal tuple enumeration; see the source gate
and privacy qualifications in docs/FOUR_PATH_BASELINE_2025.md. Research only.
"""
from dataclasses import asdict, dataclass
import math
import sys

import numpy as np

from private_graphlets.graph import SimpleGraph, _nonnegative_integer
from private_graphlets.randomized_response import rr_parameters, rr_matrix, sample_rr_upper


REFERENCE_REVISION = '85eff6efa2b1d649ee238620a998ec7f1d305aac'


def _size(n: int) -> int:
    n = _nonnegative_integer(n, 'num_vertices')
    if n > 100:
        raise ValueError('2025 P4 reconstruction supports at most 100 vertices')
    return n


def _arithmetic_guard(n: int, magnitude: float) -> None:
    # Conservative public bound on all intermediates/sum, before sampling in
    # the simulator. Avoid cubing a large float merely to detect overflow.
    if n >= 4 and magnitude > 0:
        bound = math.log(16) + 4*math.log(n+1) + 3*math.log(magnitude)
        if bound > math.log(sys.float_info.max)-2:
            raise ValueError('P4 arithmetic bound exceeds safe float64 range')


@dataclass(frozen=True)
class Baseline2025Budget:
    epsilon: float

    def __post_init__(self):
        rr_parameters(self.epsilon)


@dataclass(frozen=True)
class Baseline2025Result:
    estimate: float
    num_vertices: int
    epsilon: float

    def to_dict(self) -> dict:
        return {'schema_version': 1, 'result_type': 'experimental_private_estimate',
                'mechanism': 'aistats2025_algorithm1_p4', 'pattern': 'four_path',
                'target': 'noninduced_unlabeled_copies',
                'implementation': 'faithful_independent_reconstruction',
                'ownership': 'lower_public_id_one_report_per_pair',
                'privacy_status': 'experimental_unverified', 'simulation_only': True,
                'reference_revision': REFERENCE_REVISION, **asdict(self)}


@dataclass(frozen=True)
class Baseline2025Transcript:
    rr_upper: tuple[bool, ...]


@dataclass(frozen=True)
class Baseline2025Run:
    result: Baseline2025Result
    transcript: Baseline2025Transcript


def four_path_weighted_sum(weights: np.ndarray) -> float:
    """Server-only polynomial, equivalent to half the distinct ordered-tuple sum.

    Accepts arbitrary finite symmetric float64 weights with zero diagonal,
    including exact 0/1 matrices for NON-PRIVATE mathematical tests. No graph
    structure or pruning is accessed. Inputs are never mutated.
    """
    if (not isinstance(weights, np.ndarray) or weights.ndim != 2
            or weights.shape[0] != weights.shape[1] or weights.dtype != np.dtype('float64')):
        raise ValueError('expected square float64 weights')
    n = _size(weights.shape[0])
    if (not np.isfinite(weights).all() or not np.array_equal(weights, weights.T)
            or np.any(np.diag(weights) != 0)):
        raise ValueError('expected finite symmetric zero-diagonal weights')
    magnitude = float(np.max(np.abs(weights))) if n else 0.
    _arithmetic_guard(n, magnitude)
    if n < 4:
        return 0.
    try:
        rows = [math.fsum(float(x) for x in weights[b]) for b in range(n)]
        def terms():
            for b in range(n):
                for c in range(b+1, n):
                    middle = float(weights[b, c])
                    shared = math.fsum(float(weights[b, a])*float(weights[c, a]) for a in range(n))
                    yield middle*((rows[b]-middle)*(rows[c]-middle)-shared)
        value = math.fsum(terms())
    except OverflowError as exc:
        raise FloatingPointError('nonfinite P4 weighted arithmetic') from exc
    if not math.isfinite(value):
        raise FloatingPointError('nonfinite P4 weighted sum')
    return value


def estimate_from_reports(num_vertices: int, reports: tuple[bool, ...],
                          budget: Baseline2025Budget) -> Baseline2025Result:
    """Coordinator input is only public n/budget and privatized pair bits."""
    n = _size(num_vertices)
    if not isinstance(budget, Baseline2025Budget):
        raise ValueError('explicit Baseline2025Budget required')
    params = rr_parameters(budget.epsilon)
    _arithmetic_guard(n, params.maximum)
    estimate = four_path_weighted_sum(rr_matrix(n, reports, budget.epsilon))
    return Baseline2025Result(estimate, n, budget.epsilon)


def simulate_four_paths_baseline_2025(graph: SimpleGraph, *, budget: Baseline2025Budget,
                                       seed: int | None = None,
                                       rng: np.random.Generator | None = None) -> Baseline2025Run:
    """One RR query, then pure server postprocessing. No exact fallback or clipping."""
    if not isinstance(graph, SimpleGraph):
        raise ValueError('expected SimpleGraph')
    n = _size(graph.num_vertices)
    if not isinstance(budget, Baseline2025Budget):
        raise ValueError('explicit Baseline2025Budget required')
    _arithmetic_guard(n, rr_parameters(budget.epsilon).maximum)
    if seed is not None:
        seed = _nonnegative_integer(seed, 'seed')
    if seed is not None and rng is not None:
        raise ValueError('supply seed or rng, not both')
    if rng is None:
        rng = np.random.default_rng(seed)
    if not isinstance(rng, np.random.Generator):
        raise ValueError('expected NumPy Generator')
    reports = sample_rr_upper(graph, budget.epsilon, rng)
    result = estimate_from_reports(n, reports, budget)
    return Baseline2025Run(result, Baseline2025Transcript(reports))


def estimate_four_paths_baseline_2025(graph: SimpleGraph, *, budget: Baseline2025Budget,
                                       seed: int | None = None,
                                       rng: np.random.Generator | None = None) -> Baseline2025Result:
    """Aggregate-only convenience wrapper for the same mechanism."""
    return simulate_four_paths_baseline_2025(graph, budget=budget, seed=seed, rng=rng).result
