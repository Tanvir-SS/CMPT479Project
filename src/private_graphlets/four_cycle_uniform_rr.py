"""Uniform candidate C4 sampling with participation-adjusted RR.

Research simulator only. Public IDs are 0..n-1. The released transcript contains
public requests and randomized bits, never local wedge values or RNG state.
"""

from collections import Counter
from dataclasses import dataclass
from math import comb, exp, expm1, fsum, isfinite
from numbers import Integral

import numpy as np

from private_graphlets.graph import SimpleGraph


def sample_count(n: int) -> int:
    """Exact ceil(0.05*n*n); n<4 uses the public zero-result shortcut."""
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 0:
        raise ValueError('n must be a nonnegative integer')
    return (int(n) ** 2 + 19) // 20 if n >= 4 else 0


def cycle_orders(vertices) -> tuple[tuple[int, ...], ...]:
    """Canonical rotation/reversal representatives of the three cycles."""
    vertices = tuple(vertices)
    if len(vertices) != 4 or len(set(vertices)) != 4:
        raise ValueError('four distinct vertices required')
    a, b, c, d = sorted(vertices)
    return ((a, b, c, d), (a, b, d, c), (a, c, b, d))


def _edge(u, v):
    return (min(u, v), max(u, v))


@dataclass(frozen=True, slots=True)
class WedgeRequest:
    candidate: int
    slot: int
    center: int
    endpoints: tuple[int, int]

    @property
    def edges(self):
        return tuple(_edge(self.center, v) for v in self.endpoints)


@dataclass(frozen=True, slots=True)
class PublicSchedule:
    n: int
    cycles: tuple[tuple[int, ...], ...]
    requests: tuple[WedgeRequest, ...]  # candidate-major, slots 0 then 1
    participation: tuple[tuple[tuple[int, int], int], ...]  # absent pairs have K=0


def schedule_from_cycles(n: int, cycles) -> PublicSchedule:
    """Public deterministic request construction; retains every occurrence.

    Low-level helper for fixed-schedule checks; the estimator always samples q.
    Callers must never select a schedule based on private graph information.
    """
    sample_count(n)
    cycles = tuple(tuple(c) for c in cycles)
    requests = []
    counts = Counter()
    for t, cycle in enumerate(cycles):
        if any(isinstance(v, bool) or not isinstance(v, Integral) or not 0 <= v < n
               for v in cycle) or cycle not in cycle_orders(cycle):
            raise ValueError('invalid canonical cycle')
        a, b, c, d = cycle
        for slot, center in enumerate((b, d)):
            request = WedgeRequest(t, slot, center, (a, c))
            requests.append(request)
            counts.update(request.edges)
    return PublicSchedule(int(n), cycles, tuple(requests), tuple(sorted(counts.items())))


def public_schedule(n: int, rng: np.random.Generator) -> PublicSchedule:
    """IID uniform four-sets and cycle choices, with replacement across samples."""
    cycles = []
    for _ in range(sample_count(n)):
        vertices = tuple(int(v) for v in rng.choice(n, size=4, replace=False))
        cycles.append(cycle_orders(vertices)[int(rng.integers(3))])
    return schedule_from_cycles(n, cycles)


def _positive(value):
    if isinstance(value, bool) or not isfinite(value) or value <= 0:
        raise ValueError('privacy parameter must be finite and positive')


def rr_parameters(alpha: float) -> tuple[float, float]:
    """Return flip probability r and stable debiasing gap 1-2r."""
    _positive(alpha)
    z = exp(-alpha)
    gap = -expm1(-alpha) / (1.0 + z)
    if gap == 0 or not isfinite(1.0 / gap):
        raise ValueError('alpha outside representable simulation range')
    return z / (1.0 + z), gap


def allocate_privacy(schedule: PublicSchedule, epsilon: float) -> tuple[float, ...]:
    """epsilon/max(K_e1,K_e2), never a global maximum or endpoint split."""
    _positive(epsilon)
    counts = dict(schedule.participation)
    alphas = tuple(float(epsilon) / max(counts[e] for e in request.edges)
                   for request in schedule.requests)
    for alpha in alphas:
        rr_parameters(alpha)  # public-only numerical checks before local access
    return alphas


def _local_report(neighbors, request: WedgeRequest, alpha, rng) -> int:
    """Client-local adjacency row in, ONE randomized bit out; fresh draw per call."""
    a, c = request.endpoints
    x = int(a in neighbors and c in neighbors)
    r, _ = rr_parameters(alpha)
    return x ^ int(rng.random() < r)


def debias(report: int, alpha: float) -> float:
    if report not in (0, 1):
        raise ValueError('RR reports must be binary')
    r, gap = rr_parameters(alpha)
    return (report - r) / gap


def aggregate(schedule: PublicSchedule, alphas, reports) -> float:
    """Server-only postprocessing: no graph argument or private intermediates."""
    if len(reports) != len(schedule.requests) or len(alphas) != len(reports):
        raise ValueError('exactly one alpha and RR bit per request required')
    if schedule.n < 4:
        return 0.0
    if not schedule.cycles:
        raise ValueError('nonempty schedule required for n>=4')
    values = [debias(r, a) for r, a in zip(reports, alphas, strict=True)]
    estimate = (3 * comb(schedule.n, 4) / len(schedule.cycles)) * fsum(
        values[i] * values[i + 1] for i in range(0, len(values), 2))
    if not isfinite(estimate):
        raise OverflowError('estimate exceeds floating-point simulation range')
    return estimate


@dataclass(frozen=True, slots=True)
class FourCycleRelease:
    estimate: float
    epsilon: float
    schedule: PublicSchedule
    alphas: tuple[float, ...]
    reports: tuple[int, ...]
    privacy_status: str = 'ideal_protocol_research_simulation'


def simulate_four_cycles_private(
    graph: SimpleGraph, epsilon: float, *, seed: int | None = None,
    rng: np.random.Generator | None = None,
) -> FourCycleRelease:
    """One round; optional seed OR Generator is simulation-only, never released.

    Sequential draws model independent public sampling and private RR coins in
    the ideal protocol; NumPy is not a cryptographic random source.
    """
    _positive(epsilon)
    if seed is not None and rng is not None:
        raise ValueError('supply either seed or rng, not both')
    if rng is not None and not isinstance(rng, np.random.Generator):
        raise TypeError('rng must be a NumPy Generator')
    rng = np.random.default_rng(seed) if rng is None else rng
    schedule = public_schedule(graph.num_vertices, rng)
    alphas = allocate_privacy(schedule, epsilon)
    reports = tuple(_local_report(graph.adjacency[r.center], r, alpha, rng)
                    for r, alpha in zip(schedule.requests, alphas, strict=True))
    return FourCycleRelease(aggregate(schedule, alphas, reports), float(epsilon),
                            schedule, alphas, reports)
