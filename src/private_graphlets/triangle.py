"""Modified EdgeOrientDelta research simulator; experimental_unverified.

Path A consumes an already released order/cap/RR table and charges only count.
Path B runs private k-CoreD, cap, one RR transcript and Path A. No exact truth
or raw local scores enter either transcript. See docs/TRIANGLE_PROTOCOL.md.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from itertools import combinations
import math

import numpy as np

from private_graphlets.four_clique import cap_from_reports, local_cap_report, simulation_streams
from private_graphlets.four_clique_exact import ranks, select_outgoing, validate_cap, validate_order
from private_graphlets.graph import SimpleGraph, _nonnegative_integer
from private_graphlets.kcore import KCoreConfig, KCoreTranscript, kcore_order
from private_graphlets.noise import validate_epsilon
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper


@dataclass(frozen=True)
class TriangleBudget:
    ordering: float
    cap: float
    rr: float
    count: float

    def __post_init__(self):
        for value in (self.ordering, self.cap, self.rr, self.count):
            validate_epsilon(value)
        if self.ordering > 1:
            raise ValueError("k-CoreD ordering epsilon must be <=1")
        rr_parameters(self.rr)
        validate_epsilon(self.total)

    @property
    def total(self) -> float:
        try:
            return math.fsum((self.ordering, self.cap, self.rr, self.count))
        except OverflowError as exc:
            raise ValueError("total triangle budget exceeds finite float64 range") from exc


@dataclass(frozen=True)
class TriangleStreams:
    """Simulation inputs only; never include generators in a release."""
    ordering: np.random.Generator
    cap: np.random.Generator
    rr: np.random.Generator
    count: np.random.Generator

    def __post_init__(self):
        streams = (self.ordering, self.cap, self.rr, self.count)
        if any(not isinstance(rng, np.random.Generator) for rng in streams):
            raise ValueError("streams must be NumPy Generators")
        if len({id(rng.bit_generator) for rng in streams}) != 4:
            raise ValueError("stage streams must not share a bit generator")


def triangle_streams(seed: int | None = None) -> TriangleStreams:
    """Stable named ordering/cap/RR/count domains; caller owns stream state."""
    return TriangleStreams(*simulation_streams(seed))


def triangle_sensitivity(cap: int, epsilon_rr: float) -> float:
    """Fixed-transcript replacement-aware bound, not executable DP certification."""
    cap = _nonnegative_integer(cap, "cap")
    p = rr_parameters(epsilon_rr)
    value = 0.0 if cap <= 1 else (cap - 1) * (p.maximum + p.a)
    if not math.isfinite(value):
        raise ValueError("triangle sensitivity exceeds finite float64 range")
    return value


def _noise_scale(cap: int, epsilon_rr: float, epsilon_count: float) -> float:
    epsilon_count = validate_epsilon(epsilon_count)
    sensitivity = triangle_sensitivity(cap, epsilon_rr)
    scale = sensitivity / epsilon_count
    if not math.isfinite(scale) or (sensitivity > 0 and scale <= 0):
        raise ValueError("triangle noise scale must be finite and positive when sensitivity is nonzero")
    return scale


def triangle_local_score(vertex: int, neighbors: frozenset[int], rank: Sequence[int],
                         cap: int, weights: np.ndarray) -> float:
    """Sensitive local computation: NEVER release this value without noise.

    Low-level kernel, like the clique kernels: caller supplies one validated
    incident list and validated public rank/cap/table. Path A validates public
    context once, not once per client. No randomization or graph lookup occurs.
    """
    selected = select_outgoing(vertex, neighbors, rank, cap)
    value = math.fsum(float(weights[a, b]) for a, b in combinations(selected, 2))
    if not math.isfinite(value):
        raise FloatingPointError("triangle score exceeds finite float64 range")
    return value


def triangle_local_report(vertex: int, neighbors: frozenset[int], rank: Sequence[int],
                          cap: int, weights: np.ndarray, epsilon_rr: float,
                          epsilon_count: float, rng: np.random.Generator) -> float:
    """Validated-context client kernel: add noise BEFORE returning a message.

    For B>=2 even zero-score clients send noisy reports. For B<=1 the score is
    identically zero for all private lists, so return zero without a draw.
    """
    scale = _noise_scale(cap, epsilon_rr, epsilon_count)
    if cap <= 1:
        return 0.0
    report = triangle_local_score(vertex, neighbors, rank, cap, weights) + float(rng.laplace(0, scale))
    if not math.isfinite(report):
        raise FloatingPointError("triangle report exceeds finite float64 range")
    return report


def aggregate_triangle_reports(reports: Sequence[float]) -> float:
    """Coordinator postprocessing of already-noised reports; never clips."""
    if any(not math.isfinite(x) for x in reports):
        raise ValueError("triangle reports must be finite")
    value = math.fsum(reports)
    if not math.isfinite(value):
        raise FloatingPointError("triangle aggregate exceeds finite float64 range")
    return value


def _validate_weights(weights: np.ndarray, n: int, epsilon_rr: float) -> None:
    p = rr_parameters(epsilon_rr)
    if (not isinstance(weights, np.ndarray) or weights.shape != (n, n)
            or weights.dtype != np.dtype('float64') or weights.flags.writeable):
        raise ValueError("expected an immutable n-by-n float64 RR matrix")
    if not np.array_equal(weights, weights.T) or np.any(np.diag(weights) != 0):
        raise ValueError("RR matrix must be symmetric with zero diagonal")
    for v in range(n):
        row = weights[v, v+1:]
        if not np.all((row == p.maximum) | (row == -p.a)):
            raise ValueError("RR weights must match the supplied epsilon_rr")


def _validate_graph(graph: SimpleGraph) -> int:
    if not isinstance(graph, SimpleGraph):
        raise ValueError("expected SimpleGraph")
    if graph.num_vertices > 1000:
        raise ValueError("dense triangle simulator supports at most 1000 vertices")
    return graph.num_vertices


@dataclass(frozen=True)
class TriangleComponentResult:
    estimate: float
    num_vertices: int
    cap: int
    epsilon_rr: float  # Provenance of a PREVIOUS release, not an extra charge.
    epsilon_count: float
    local_noise_scale: float

    def to_dict(self) -> dict:
        return {"schema_version": 1, "result_type": "experimental_private_component",
                "pattern": "triangle", "target": "retained_triangles",
                "simulation_only": True, "privacy_status": "experimental_unverified",
                "accounting_scope": "count_only_given_previous_releases",
                "additional_epsilon": self.epsilon_count, **asdict(self)}


@dataclass(frozen=True)
class TriangleComponentTranscript:
    order: tuple[int, ...]
    cap: int
    local_reports: tuple[float, ...]


@dataclass(frozen=True)
class TriangleComponentRun:
    result: TriangleComponentResult
    transcript: TriangleComponentTranscript


def estimate_triangles_from_rr(graph: SimpleGraph, order: Sequence[int], cap: int,
                               weights: np.ndarray, *, epsilon_rr: float,
                               epsilon_count: float, rng: np.random.Generator
                               ) -> TriangleComponentRun:
    """Path A: consume previous releases; only the supplied COUNT RNG advances.

    Caller is responsible for provenance/accounting of order, cap and RR and
    their independence requirements. A permutation alone cannot certify that
    its construction was private. No prior-stage mechanism is called here.
    """
    n = _validate_graph(graph)
    order = validate_order(n, order)
    cap = validate_cap(cap, n)
    _validate_weights(weights, n, epsilon_rr)
    scale = _noise_scale(cap, epsilon_rr, epsilon_count)
    rank = ranks(order)
    reports = tuple(triangle_local_report(v, row, rank, cap, weights, epsilon_rr,
                                         epsilon_count, rng)
                    for v, row in enumerate(graph.adjacency))
    result = TriangleComponentResult(aggregate_triangle_reports(reports), n, cap,
                                     epsilon_rr, epsilon_count, scale)
    return TriangleComponentRun(result, TriangleComponentTranscript(order, cap, reports))


@dataclass(frozen=True)
class TriangleResult:
    estimate: float
    num_vertices: int
    released_cap: int
    budget: TriangleBudget
    local_noise_scale: float
    beta: float

    def to_dict(self) -> dict:
        return {"schema_version": 1, "result_type": "experimental_private_estimate",
                "mechanism": "modified_edgeorient_triangle", "pattern": "triangle",
                "target": "retained_triangles", "ordering_type": "kcore_private_simulation",
                "simulation_only": True, "privacy_status": "experimental_unverified",
                "epsilon_total": self.budget.total, **asdict(self)}


@dataclass(frozen=True)
class TriangleTranscript:
    ordering: KCoreTranscript
    order: tuple[int, ...]
    cap_reports: tuple[float, ...]
    cap: int
    rr_upper: tuple[bool, ...]
    local_reports: tuple[float, ...]


@dataclass(frozen=True)
class TriangleRun:
    result: TriangleResult
    transcript: TriangleTranscript


def simulate_triangles_private(graph: SimpleGraph, *, budget: TriangleBudget,
                               seed: int | None = None, streams: TriangleStreams | None = None,
                               beta: float = 0.05, kcore_config: KCoreConfig | None = None
                               ) -> TriangleRun:
    """Path B: private ordering/cap, exactly one RR transcript, then Path A."""
    n = _validate_graph(graph)
    if not isinstance(budget, TriangleBudget):
        raise ValueError("explicit TriangleBudget required")
    if isinstance(beta, bool) or not isinstance(beta, (int, float)) or not 0 < beta < 1:
        raise ValueError("beta must be strictly between zero and one")
    if streams is not None and seed is not None:
        raise ValueError("supply seed or streams, not both")
    if streams is None:
        streams = triangle_streams(seed)
    elif not isinstance(streams, TriangleStreams):
        raise ValueError("expected TriangleStreams")
    ordering = kcore_order(graph, budget.ordering, streams.ordering, kcore_config)
    order = ordering.order
    rank = ranks(order)
    caps = tuple(local_cap_report(v, row, rank, budget.cap, streams.cap)
                 for v, row in enumerate(graph.adjacency))
    cap = cap_from_reports(caps, n, budget.cap, beta)
    reports = sample_rr_upper(graph, budget.rr, streams.rr)
    weights = rr_matrix(n, reports, budget.rr)
    component = estimate_triangles_from_rr(graph, order, cap, weights,
                                          epsilon_rr=budget.rr, epsilon_count=budget.count,
                                          rng=streams.count)
    result = TriangleResult(component.result.estimate, n, cap, budget,
                            component.result.local_noise_scale, beta)
    return TriangleRun(result, TriangleTranscript(ordering, order, caps, cap, reports,
                                                 component.transcript.local_reports))


def estimate_triangles_private(graph: SimpleGraph, *, budget: TriangleBudget,
                               seed: int | None = None, streams: TriangleStreams | None = None,
                               beta: float = 0.05, kcore_config: KCoreConfig | None = None
                               ) -> TriangleResult:
    """Aggregate-only Path B convenience API; no exact diagnostic fields."""
    return simulate_triangles_private(graph, budget=budget, seed=seed, streams=streams,
                                      beta=beta, kcore_config=kcore_config).result
