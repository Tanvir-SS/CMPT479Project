"""SC-ESCAPE two-round non-induced P4 research simulator.

Separate from the five-stage estimator. Public D_max is mandatory; no projection,
cap estimation, clipping or rounding. See docs/SC_ESCAPE_IMPLEMENTATION.md.
"""

from dataclasses import asdict, dataclass
from itertools import combinations
import math
from numbers import Integral

import numpy as np

from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import validate_epsilon
from private_graphlets.randomized_response import rr_parameters


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise FloatingPointError("SC-ESCAPE arithmetic exceeds finite float64 range")
    return value


def _sum(values) -> float:
    try:
        return _finite(math.fsum(values))
    except OverflowError as exc:
        raise FloatingPointError("SC-ESCAPE sum exceeds finite float64 range") from exc


def _laplace(scale: float, rng: np.random.Generator) -> float:
    """Zero scale is the exact point mass, never a substituted positive scale."""
    _finite(scale)
    if scale < 0:
        raise ValueError("Laplace scale must be nonnegative")
    return _finite(float(rng.laplace(0.0, scale)))


@dataclass(frozen=True)
class SCEscapeBudget:
    """Actual mechanism epsilons; total = 2*degree + rr + product + triangle."""

    degree: float
    rr: float
    product: float
    triangle: float

    def __post_init__(self):
        for name in ("degree", "rr", "product", "triangle"):
            object.__setattr__(self, name, validate_epsilon(getattr(self, name)))
        rr_parameters(self.rr)  # Reuse existing supported RR parameter range.
        if not math.isfinite(1.0 / self.degree):
            raise ValueError("degree noise scale exceeds finite float64 range")
        validate_epsilon(self.total)

    @property
    def total(self) -> float:
        try:
            return math.fsum((self.degree, self.degree, self.rr, self.product, self.triangle))
        except OverflowError as exc:
            raise ValueError("SC-ESCAPE total budget exceeds finite float64 range") from exc


@dataclass(frozen=True)
class SCEscapeStreams:
    """Four simulation streams; separate objects alone cannot certify independence."""

    degree: np.random.Generator
    rr: np.random.Generator
    product: np.random.Generator
    triangle: np.random.Generator

    def __post_init__(self):
        streams = (self.degree, self.rr, self.product, self.triangle)
        if any(not isinstance(rng, np.random.Generator) for rng in streams):
            raise ValueError("streams must be NumPy Generators")
        if len({id(rng.bit_generator) for rng in streams}) != 4:
            raise ValueError("four streams must not share a bit generator")


def sc_escape_streams(seed: int | None = None) -> SCEscapeStreams:
    """Stable SeedSequence domains: degree, RR, degree product, triangle."""
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0):
        raise ValueError("simulation seed must be a nonnegative integer")
    children = np.random.SeedSequence(None if seed is None else int(seed)).spawn(4)
    return SCEscapeStreams(*(np.random.default_rng(child) for child in children))


def local_degree_report(neighbors: frozenset[int], epsilon: float,
                        rng: np.random.Generator) -> float:
    """Client-local d_v + Lap(0, 1/epsilon_D), including isolated vertices."""
    return _finite(len(neighbors) + _laplace(1.0 / epsilon, rng))


def local_rr_lower_row(vertex: int, neighbors: frozenset[int], epsilon: float,
                       rng: np.random.Generator) -> tuple[bool, ...]:
    """Owner i reports all (i,j), j<i, including nonedges; public row length i."""
    p = rr_parameters(epsilon).flip_probability
    flips = rng.random(vertex) < p
    return tuple(bool((j in neighbors) ^ flip) for j, flip in enumerate(flips))


def local_product_report(vertex: int, neighbors: frozenset[int],
                         centered_degrees: tuple[float, ...], h: float,
                         epsilon: float, rng: np.random.Generator) -> float:
    """Client receives ALL degree reports; private neighbor selection stays local."""
    x = centered_degrees[vertex]
    contribution = _finite(x * _sum(centered_degrees[u] for u in sorted(neighbors)))
    sensitivity = _finite(abs(x) * h)
    if x != 0 and h > 0 and sensitivity == 0:
        raise FloatingPointError("positive product sensitivity underflowed")
    scale = _finite(2.0 * sensitivity / epsilon)
    if sensitivity > 0 and scale == 0:
        raise FloatingPointError("positive product noise scale underflowed")
    return _finite(contribution + _laplace(scale, rng))


def local_triangle_report(vertex: int, neighbors: frozenset[int],
                          rr_lower: tuple[bool, ...], p: float, scale: float,
                          rng: np.random.Generator) -> float:
    """Client receives full G'; t_i, s_i and actual neighbors are never returned."""
    lower = sorted(u for u in neighbors if u < vertex)
    # Packed lower triangle, row k has k entries; no dense graph copy or queries.
    t = sum(rr_lower[k * (k - 1) // 2 + j] for j, k in combinations(lower, 2))
    s = len(lower) * (len(lower) - 1) // 2
    return _finite(t - p * s + _laplace(scale, rng))


@dataclass(frozen=True)
class SCEscapeTranscript:
    noisy_degrees: tuple[float, ...]
    rr_lower: tuple[bool, ...]
    local_product_reports: tuple[float, ...]
    local_triangle_reports: tuple[float, ...]


@dataclass(frozen=True)
class SCEscapeResult:
    estimate: float
    degree_product_estimate: float
    triangle_estimate: float
    num_vertices: int
    public_max_degree: int
    budget: SCEscapeBudget

    @property
    def epsilon_total(self) -> float:
        return self.budget.total

    def to_dict(self) -> dict:
        return {"schema_version": 1, "result_type": "experimental_private_estimate",
                "mechanism": "sc_escape", "pattern": "4-path",
                "count_semantics": "non-induced_unlabeled", "target": "original_noninduced_P4",
                "simulation_only": True, "privacy_status": "experimental_unverified",
                "epsilon_total": self.epsilon_total, **asdict(self)}


@dataclass(frozen=True)
class SCEscapeRun:
    result: SCEscapeResult
    transcript: SCEscapeTranscript


def simulate_sc_escape(graph: SimpleGraph, *, budget: SCEscapeBudget,
                       public_max_degree: int, seed: int | None = None,
                       streams: SCEscapeStreams | None = None) -> SCEscapeRun:
    """Simulate two rounds on a fixed public vertex set with public degree bound.

    Input validation is offline, not an extra private release. All clients send
    fixed-size reports in each round and receive the same Round 1 transcript.
    The simulator holds private rows solely to dispatch client-local functions.
    """
    if not isinstance(graph, SimpleGraph):
        raise ValueError("expected SimpleGraph")
    if not isinstance(budget, SCEscapeBudget):
        raise ValueError("explicit SCEscapeBudget required")
    n = graph.num_vertices
    if n > 1000:
        raise ValueError("SC-ESCAPE simulator supports at most 1000 vertices")
    if (isinstance(public_max_degree, bool) or not isinstance(public_max_degree, Integral)
            or public_max_degree < 0):
        raise ValueError("public_max_degree must be an explicit nonnegative integer")
    bound = int(public_max_degree)
    if any(len(row) > bound for row in graph.adjacency):
        raise ValueError("input graph violates public_max_degree (offline validation)")
    try:
        triangle_scale = bound / budget.triangle
    except OverflowError as exc:
        raise ValueError("triangle noise scale exceeds finite float64 range") from exc
    if not math.isfinite(triangle_scale) or (bound > 0 and triangle_scale == 0):
        raise ValueError("triangle noise scale exceeds finite positive float64 range")
    if seed is not None and streams is not None:
        raise ValueError("supply seed or streams, not both")
    if streams is None:
        streams = sc_escape_streams(seed)
    elif not isinstance(streams, SCEscapeStreams):
        raise ValueError("expected SCEscapeStreams")

    # Round 1: independent degree and lower-triangular RR reports.
    degrees = tuple(local_degree_report(row, budget.degree, streams.degree)
                    for row in graph.adjacency)
    rr_lower = tuple(bit for v, row in enumerate(graph.adjacency)
                     for bit in local_rr_lower_row(v, row, budget.rr, streams.rr))
    centered = tuple(_finite(d - 1.0) for d in degrees)
    h = max(map(abs, centered), default=0.0)
    p = rr_parameters(budget.rr).flip_probability

    # Round 2: two independent local reports per vertex, even for empty rows.
    products = tuple(local_product_report(v, row, centered, h, budget.product, streams.product)
                     for v, row in enumerate(graph.adjacency))
    triangles = tuple(local_triangle_report(v, row, rr_lower, p, triangle_scale, streams.triangle)
                      for v, row in enumerate(graph.adjacency))
    a_hat = _finite(0.5 * _sum(products))
    # tanh(epsilon_R/2) = 1-2p, without subtractive cancellation at small epsilon.
    t_hat = _finite(_sum(triangles) / math.tanh(budget.rr / 2.0))
    estimate = _sum((a_hat, _finite(-3.0 * t_hat)))
    result = SCEscapeResult(estimate, a_hat, t_hat, n, bound, budget)
    return SCEscapeRun(result, SCEscapeTranscript(degrees, rr_lower, products, triangles))


def estimate_sc_escape(graph: SimpleGraph, *, budget: SCEscapeBudget,
                       public_max_degree: int, seed: int | None = None,
                       streams: SCEscapeStreams | None = None) -> SCEscapeResult:
    """Aggregate result only; seeds, raw degrees and exact truth are not attached."""
    return simulate_sc_escape(graph, budget=budget, public_max_degree=public_max_degree,
                              seed=seed, streams=streams).result
