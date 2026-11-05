"""Complete non-induced P4 research simulator; experimental_unverified.

Five separately randomized stages; one RR table shared with the unchanged
triangle component. No exact-evaluation data enter the result/transcript.
See docs/FOUR_PATH_IMPLEMENTATION.md for assumptions and truncation bias.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
import math
from numbers import Integral

import numpy as np

from private_graphlets.four_clique import cap_from_reports, local_cap_report
from private_graphlets.four_clique_exact import ranks
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import KCoreConfig, KCoreTranscript, kcore_order
from private_graphlets.noise import laplace_scale, sample_degree_noise, validate_epsilon
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper
from private_graphlets.triangle import estimate_triangles_from_rr


@dataclass(frozen=True)
class FourPathBudget:
    degree: float
    ordering: float
    rr: float
    cap: float
    count: float

    def __post_init__(self):
        for value in (self.degree, self.ordering, self.rr, self.cap, self.count):
            validate_epsilon(value)
        laplace_scale(self.degree)
        if self.ordering > 1:
            raise ValueError("k-CoreD ordering epsilon must be <=1")
        rr_parameters(self.rr)
        validate_epsilon(self.total)

    @property
    def total(self) -> float:
        try:
            return math.fsum((self.degree, self.ordering, self.rr, self.cap, self.count))
        except OverflowError as exc:
            raise ValueError("total four-path budget exceeds finite float64 range") from exc


@dataclass(frozen=True)
class FourPathStreams:
    """Simulation inputs only. Distinct objects do not certify independence."""
    degree: np.random.Generator
    ordering: np.random.Generator
    cap: np.random.Generator
    rr: np.random.Generator
    count: np.random.Generator

    def __post_init__(self):
        streams = (self.degree, self.ordering, self.cap, self.rr, self.count)
        if any(not isinstance(rng, np.random.Generator) for rng in streams):
            raise ValueError("streams must be NumPy Generators")
        if len({id(rng.bit_generator) for rng in streams}) != 5:
            raise ValueError("five stage streams must not share a bit generator")


def four_path_streams(seed: int | None = None) -> FourPathStreams:
    """Stable SeedSequence domains: degree, ordering, cap, RR, count."""
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0):
        raise ValueError("simulation seed must be a nonnegative integer")
    children = np.random.SeedSequence(None if seed is None else int(seed)).spawn(5)
    return FourPathStreams(*(np.random.default_rng(child) for child in children))


def local_degree_report(neighbors: frozenset[int], epsilon_degree: float,
                        rng: np.random.Generator) -> float:
    """Client-local degree plus one independent Laplace(0,2/epsilon_D) draw."""
    report = len(neighbors) + float(sample_degree_noise(epsilon_degree, size=(), rng=rng))
    if not math.isfinite(report):
        raise FloatingPointError("noisy degree report exceeds finite float64 range")
    return report


def degree_product_estimate(noisy_degrees: Sequence[float], weights: np.ndarray) -> float:
    """Postprocess releases only: sum W_uv*(dhat_u-1)*(dhat_v-1) for ALL u<v.

    No graph argument or edge filtering. Accept finite real degree reports and
    an immutable symmetric float64 table with zero diagonal. The full driver
    constructs canonical RR weights; this generic postprocessor checks numerical
    shape/contract, not a privacy parameter or origin of the input releases.
    """
    degrees = np.asarray(noisy_degrees)
    if degrees.ndim != 1 or degrees.dtype.kind not in 'iuf' or not np.all(np.isfinite(degrees)):
        raise ValueError("noisy degrees must be a one-dimensional finite real sequence")
    n = len(degrees)
    if (not isinstance(weights, np.ndarray) or weights.shape != (n, n)
            or weights.dtype != np.dtype('float64') or weights.flags.writeable
            or not np.all(np.isfinite(weights))):
        raise ValueError("expected immutable finite n-by-n float64 weights")
    if not np.array_equal(weights, weights.T) or np.any(np.diag(weights) != 0):
        raise ValueError("weights must be symmetric with zero diagonal")
    centered = tuple(float(value) - 1.0 for value in degrees)
    if any(not math.isfinite(value) for value in centered):
        raise FloatingPointError("centered degree exceeds finite float64 range")
    def terms():
        for u in range(n):
            for v in range(u+1, n):
                term = float(weights[u, v]) * centered[u] * centered[v]
                if not math.isfinite(term):
                    raise FloatingPointError("degree product exceeds finite float64 range")
                yield term
    try:
        value = math.fsum(terms())
    except OverflowError as exc:
        raise FloatingPointError("degree-product sum exceeds finite float64 range") from exc
    if not math.isfinite(value):
        raise FloatingPointError("degree-product estimate exceeds finite float64 range")
    return value


@dataclass(frozen=True)
class FourPathResult:
    estimate: float
    degree_product_estimate: float
    triangle_estimate: float
    num_vertices: int
    released_cap: int
    budget: FourPathBudget
    degree_noise_scale: float
    triangle_noise_scale: float
    beta: float

    @property
    def epsilon_total(self) -> float:
        return self.budget.total

    def to_dict(self) -> dict:
        return {"schema_version": 1, "result_type": "experimental_private_estimate",
                "mechanism": "shared_rr_degree_product_minus_triangles",
                "pattern": "4-path", "count_semantics": "non-induced_unlabeled",
                "target": "original_noninduced_P4", "truncation_bias_possible": True,
                "simulation_only": True, "privacy_status": "experimental_unverified",
                "ordering_type": "kcore_private_simulation",
                "epsilon_total": self.epsilon_total, **asdict(self)}


@dataclass(frozen=True)
class FourPathTranscript:
    noisy_degrees: tuple[float, ...]
    ordering: KCoreTranscript
    order: tuple[int, ...]
    cap_reports: tuple[float, ...]
    cap: int
    rr_upper: tuple[bool, ...]
    local_triangle_reports: tuple[float, ...]


@dataclass(frozen=True)
class FourPathRun:
    result: FourPathResult
    transcript: FourPathTranscript


def simulate_four_paths_private(graph: SimpleGraph, *, budget: FourPathBudget,
                                seed: int | None = None, streams: FourPathStreams | None = None,
                                beta: float = 0.05, kcore_config: KCoreConfig | None = None
                                ) -> FourPathRun:
    """Five-stage simulator; uses the Phase 2 reusable component, never standalone."""
    if not isinstance(graph, SimpleGraph):
        raise ValueError("expected SimpleGraph")
    n = graph.num_vertices
    if n > 1000:
        raise ValueError("dense four-path simulator supports at most 1000 vertices")
    if not isinstance(budget, FourPathBudget):
        raise ValueError("explicit FourPathBudget required")
    if isinstance(beta, bool) or not isinstance(beta, (int, float)) or not 0 < beta < 1:
        raise ValueError("beta must be strictly between zero and one")
    if seed is not None and streams is not None:
        raise ValueError("supply seed or streams, not both")
    if streams is None:
        streams = four_path_streams(seed)
    elif not isinstance(streams, FourPathStreams):
        raise ValueError("expected FourPathStreams")
    degrees = tuple(local_degree_report(row, budget.degree, streams.degree)
                    for row in graph.adjacency)
    ordering = kcore_order(graph, budget.ordering, streams.ordering, kcore_config)
    order = ordering.order
    rank = ranks(order)
    caps = tuple(local_cap_report(v, row, rank, budget.cap, streams.cap)
                 for v, row in enumerate(graph.adjacency))
    cap = cap_from_reports(caps, n, budget.cap, beta)
    reports = sample_rr_upper(graph, budget.rr, streams.rr)
    weights = rr_matrix(n, reports, budget.rr)
    product_estimate = degree_product_estimate(degrees, weights)
    triangle = estimate_triangles_from_rr(graph, order, cap, weights,
                                         epsilon_rr=budget.rr, epsilon_count=budget.count,
                                         rng=streams.count)
    try:
        estimate = math.fsum((product_estimate, -3.0 * triangle.result.estimate))
    except OverflowError as exc:
        raise FloatingPointError("four-path estimate exceeds finite float64 range") from exc
    if not math.isfinite(estimate):
        raise FloatingPointError("four-path estimate exceeds finite float64 range")
    result = FourPathResult(estimate, product_estimate, triangle.result.estimate, n, cap,
                            budget, laplace_scale(budget.degree),
                            triangle.result.local_noise_scale, beta)
    return FourPathRun(result, FourPathTranscript(degrees, ordering, order, caps, cap,
                                                 reports, triangle.transcript.local_reports))


def estimate_four_paths_private(graph: SimpleGraph, *, budget: FourPathBudget,
                                seed: int | None = None, streams: FourPathStreams | None = None,
                                beta: float = 0.05, kcore_config: KCoreConfig | None = None
                                ) -> FourPathResult:
    """Aggregate/public metadata only; exact evaluation belongs in separate tools."""
    return simulate_four_paths_private(graph, budget=budget, seed=seed, streams=streams,
                                       beta=beta, kcore_config=kcore_config).result
