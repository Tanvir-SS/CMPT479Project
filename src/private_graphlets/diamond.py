"""Hybrid diamond-counting research simulator; NOT certified executable LEDP.

Only the private ordering, all-pair RR bits and full noisy wedge vectors cross
the modeled client boundary. NumPy seeds/state and exact local data never do.
See docs/DIAMOND_IMPLEMENTATION.md and docs/DIAMOND_PRIVACY_AUDIT.md.
"""

from dataclasses import asdict, dataclass
from itertools import combinations
import math

import numpy as np

from private_graphlets.four_clique_exact import ranks, select_outgoing, validate_order
from private_graphlets.graph import SimpleGraph, _nonnegative_integer
from private_graphlets.kcore import KCoreConfig, KCoreTranscript, kcore_order
from private_graphlets.noise import validate_epsilon
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper


@dataclass(frozen=True, slots=True)
class DiamondBudget:
    total: float
    ordering: float
    rr: float
    wedge: float

    def __post_init__(self):
        for name in ("total", "ordering", "rr", "wedge"):
            object.__setattr__(self, name, validate_epsilon(getattr(self, name)))
        # No approximate-sum tolerance; this remains a floating-point simulator,
        # not a certification of exact real-arithmetic budget representations.
        if math.fsum((self.ordering, self.rr, self.wedge)) != self.total:
            raise ValueError("O/R/W allocations must sum to total epsilon (math.fsum)")
        if self.ordering > 1:
            raise ValueError("k-CoreD requires ordering epsilon <= 1; use an explicit budget")
        rr_parameters(self.rr)


def allocate_budget(epsilon: float) -> DiamondBudget:
    """Equal thirds only; never silently redistribute an unsupported allocation."""
    epsilon = validate_epsilon(epsilon)
    return DiamondBudget(epsilon, epsilon / 3, epsilon / 3, epsilon / 3)


def _validate_cap(cap: int) -> int:
    cap = _nonnegative_integer(cap, "cap")
    if cap < 2:
        raise ValueError("public cap B must be at least 2")
    return cap


@dataclass(frozen=True, slots=True)
class HybridParameters:
    sensitivity: int
    scale: float
    rr_product_variance_bound: float
    wedge_variance: float
    rr_weight: float


def hybrid_parameters(cap: int, epsilon_rr: float, epsilon_wedge: float) -> HybridParameters:
    """Public parameters only: v, VR=2v+v², VW=2b², lambda=VW/(VR+VW)."""
    sensitivity = 2 * (_validate_cap(cap) - 1)
    scale = sensitivity / validate_epsilon(epsilon_wedge)
    v = rr_parameters(epsilon_rr).variance
    vr = 2 * v + v * v
    vw = 2 * scale * scale
    if not all(math.isfinite(x) and x > 0 for x in (scale, vr, vw)):
        raise ValueError("hybrid parameters exceed the finite positive float64 range")
    # Scale the ratio to avoid overflow in VR+VW; algebraically identical.
    weight = 1 / (1 + vr / vw) if vr <= vw else (vw / vr) / (1 + vw / vr)
    if not 0 < weight < 1:
        raise ValueError("hybrid weight is not representable strictly between zero and one")
    return HybridParameters(sensitivity, scale, vr, vw, weight)


def wedge_requests(order: tuple[int, ...]) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Full schedule from released order; rows indexed by ID, pairs in ID order.

    There are C(n,3) coordinates, regardless of the actual graph or cap.
    """
    rank = ranks(order)
    return tuple(tuple(combinations((v for v in range(len(order)) if rank[c] < rank[v]), 2))
                 for c in range(len(order)))


def _local_wedge_indicators(vertex, neighbors, rank, cap, requests):
    """LOCAL ONLY. Never include the selected set or these indicators in releases."""
    selected = frozenset(select_outgoing(vertex, neighbors, rank, cap))
    return np.fromiter((int(a in selected and b in selected) for a, b in requests),
                       dtype=float, count=len(requests))


def local_wedge_reports(vertex, neighbors, rank, cap, requests, scale, rng):
    """One client's entire fixed vector, including zeros, with iid coordinate noise."""
    values = _local_wedge_indicators(vertex, neighbors, rank, cap, requests)
    reports = values + rng.laplace(0.0, scale, size=len(requests))
    if not np.all(np.isfinite(reports)):
        raise FloatingPointError("noisy wedge report exceeds float64")
    return tuple(float(y) for y in reports)


def _reconstruct_diamonds(order, weights, wedge_reports, rr_weight) -> float:
    """Graph-free arithmetic kernel, also used by strictly test-only exact oracles.

    Do not interpret arbitrary inputs (e.g. raw indicators in tests) as private.
    """
    order = validate_order(len(order), order)
    n = len(order)
    weights = np.asarray(weights, dtype=float)
    if (weights.shape != (n, n) or not np.all(np.isfinite(weights))
            or not np.array_equal(weights, weights.T) or np.any(weights.diagonal() != 0)):
        raise ValueError("weights must be a finite symmetric n-by-n table with zero diagonal")
    if not math.isfinite(rr_weight) or not 0 < rr_weight < 1:
        raise ValueError("RR weight must be strictly between zero and one")
    requests = wedge_requests(order)
    if len(wedge_reports) != n:
        raise ValueError("one complete wedge-report row per vertex required")
    lookup = []
    for pairs, row in zip(requests, wedge_reports, strict=True):
        if len(row) != len(pairs) or any(not math.isfinite(y) for y in row):
            raise ValueError("invalid or incomplete wedge-report row")
        lookup.append(dict(zip(pairs, row, strict=True)))
    terms = []
    for a, b in combinations(range(n), 2):
        common = []
        for c in range(n):
            if c == a or c == b:
                continue
            rr_product = float(weights[a, c]) * float(weights[b, c])
            value = (rr_weight * rr_product + (1 - rr_weight) * lookup[c][a, b]
                     if (a, b) in lookup[c] else rr_product)
            common.append(value)
        # A pair of distinct common neighbors; NOT choose(sum(common), 2).
        total = math.fsum(common)
        pairs = (total * total - math.fsum(x * x for x in common)) / 2
        terms.append(float(weights[a, b]) * pairs)
    estimate = math.fsum(terms)
    if not math.isfinite(estimate):
        raise FloatingPointError("diamond reconstruction exceeds float64")
    return estimate


@dataclass(frozen=True, slots=True)
class DiamondTranscript:
    budget: DiamondBudget
    cap: int
    ordering: KCoreTranscript
    rr_upper: tuple[bool, ...]
    wedge_reports: tuple[tuple[float, ...], ...]


def aggregate_diamonds(transcript: DiamondTranscript) -> float:
    """Coordinator consumes ONLY privatized messages and public parameters."""
    if (transcript.ordering.ordering_type != "kcore_private_simulation"
            or transcript.ordering.epsilon != transcript.budget.ordering):
        raise ValueError("expected the private k-CoreD transcript at the allocated budget")
    order = transcript.ordering.order
    parameters = hybrid_parameters(transcript.cap, transcript.budget.rr, transcript.budget.wedge)
    return _reconstruct_diamonds(order, rr_matrix(len(order), transcript.rr_upper,
                                                transcript.budget.rr),
                                transcript.wedge_reports, parameters.rr_weight)


@dataclass(frozen=True, slots=True)
class DiamondResult:
    estimate: float
    budget: DiamondBudget
    cap: int
    wedge_noise_scale: float
    rr_weight: float
    pattern: str = "diamond"
    count_semantics: str = "non-induced_unlabeled"
    result_type: str = "private_estimate_simulation"
    privacy_status: str = "experimental_unverified"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DiamondSimulation:
    result: DiamondResult
    transcript: DiamondTranscript


def _simulation_streams(seed):
    if seed is not None:
        seed = _nonnegative_integer(seed, "simulation seed")
    # Fixed domains O, R, W. A different number of draws in O cannot shift R/W.
    return tuple(np.random.default_rng(child) for child in np.random.SeedSequence(seed).spawn(3))


def simulate_diamonds(graph: SimpleGraph, epsilon: float, *, cap: int,
                      budget: DiamondBudget | None = None, seed: int | None = None,
                      kcore_config: KCoreConfig | None = None) -> DiamondSimulation:
    """Run the specified three-stage protocol; no public-order or noiseless switch.

    All graph sizes use the same reporting stages (empty vectors are permitted).
    B may exceed n-1; its declared noise scale remains 2(B-1)/epsilon_W.
    """
    epsilon = validate_epsilon(epsilon)
    budget = allocate_budget(epsilon) if budget is None else budget
    if not isinstance(budget, DiamondBudget) or budget.total != epsilon:
        raise ValueError("budget total must equal requested epsilon")
    cap = _validate_cap(cap)
    parameters = hybrid_parameters(cap, budget.rr, budget.wedge)
    ordering_rng, rr_rng, wedge_rng = _simulation_streams(seed)
    ordering = kcore_order(graph, budget.ordering, ordering_rng, kcore_config)
    rr_upper = sample_rr_upper(graph, budget.rr, rr_rng)
    rank = ranks(ordering.order)
    requests = wedge_requests(ordering.order)
    reports = tuple(local_wedge_reports(v, row, rank, cap, requests[v], parameters.scale, wedge_rng)
                    for v, row in enumerate(graph.adjacency))
    transcript = DiamondTranscript(budget, cap, ordering, rr_upper, reports)
    result = DiamondResult(aggregate_diamonds(transcript), budget, cap,
                           parameters.scale, parameters.rr_weight)
    return DiamondSimulation(result, transcript)


def estimate_diamonds(graph: SimpleGraph, epsilon: float, *, cap: int,
                      budget: DiamondBudget | None = None, seed: int | None = None,
                      kcore_config: KCoreConfig | None = None) -> DiamondResult:
    """Aggregate-only research API; no exact diagnostics or seeds in the result."""
    return simulate_diamonds(graph, epsilon, cap=cap, budget=budget, seed=seed,
                             kcore_config=kcore_config).result
