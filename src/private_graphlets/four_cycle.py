"""Balanced wedge-Laplace C4 research simulation (ideal protocol in docs).

Fixed public vertex universe; undirected edge adjacency. NumPy randomness and
floating-point arithmetic are NOT a production implementation of pure LEDP.
No seed, exact wedge, degree or adjacency is included in the returned transcript.
"""

from dataclasses import dataclass
from math import comb, fsum, isfinite, isqrt
from numbers import Integral

import numpy as np

from private_graphlets.graph import SimpleGraph


def padded_prime(n: int) -> int:
    """Smallest prime >= max(n, 5); also supports public universes below four."""
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    p = max(int(n), 5)
    while any(p % d == 0 for d in range(2, isqrt(p) + 1)):
        p += 1
    return p


def progression_blocks(p: int) -> tuple[tuple[int, ...], ...]:
    """Ordered occurrences, deliberately including repeated four-sets."""
    if padded_prime(p) != p:
        raise ValueError("p must be prime and at least five")
    return tuple(tuple((a + r * b) % p for r in range(4))
                 for a in range(p) for b in range(1, p))


def cycle_orders(vertices) -> tuple[tuple[int, ...], ...]:
    """The three undirected cycles on a four-set, each represented once."""
    u, v, w, x = sorted(vertices)
    return ((u, v, w, x), (u, v, x, w), (u, w, v, x))


@dataclass(frozen=True, slots=True)
class WedgeRequest:
    candidate: int
    slot: int
    endpoints: tuple[int, int]


@dataclass(frozen=True, slots=True)
class PublicSchedule:
    n: int
    p: int
    cycles: tuple[tuple[int, ...], ...]
    requests: tuple[tuple[WedgeRequest, ...], ...]


def public_schedule(n: int, rng: np.random.Generator) -> PublicSchedule:
    """Generate all requests before any adjacency access. One global permutation."""
    p = padded_prime(n)
    permutation = rng.permutation(p)
    blocks = progression_blocks(p)
    choices = rng.integers(0, 3, size=len(blocks))
    cycles = tuple(cycle_orders(tuple(int(permutation[v]) for v in block))[int(choice)]
                   for block, choice in zip(blocks, choices, strict=True))
    requests: list[list[WedgeRequest]] = [[] for _ in range(p)]
    for t, (a, b, c, d) in enumerate(cycles):
        requests[b].append(WedgeRequest(t, 0, (a, c)))
        requests[d].append(WedgeRequest(t, 1, (a, c)))
    return PublicSchedule(n, p, cycles, tuple(tuple(row) for row in requests))


def _local_wedges(neighbors: frozenset[int], requests: tuple[WedgeRequest, ...]):
    """LOCAL ONLY: one client's row; never send or attach these exact values."""
    return np.fromiter((int(a in neighbors and c in neighbors)
                        for request in requests for a, c in [request.endpoints]),
                       dtype=float, count=len(requests))


def _local_reports(neighbors, requests, scale, rng):
    # A separate iid draw for EVERY coordinate, including repeated wedges.
    return tuple(float(y) for y in
                 _local_wedges(neighbors, requests) + rng.laplace(0.0, scale, len(requests)))


def aggregate(schedule: PublicSchedule, reports: tuple[tuple[float, ...], ...]) -> float:
    """Server post-processing: accepts only public schedule and noisy reports."""
    if len(reports) != schedule.p:
        raise ValueError("one report vector per public vertex required")
    values = [[0.0, 0.0] for _ in schedule.cycles]
    for requests, row in zip(schedule.requests, reports, strict=True):
        for request, value in zip(requests, row, strict=True):
            values[request.candidate][request.slot] = value
    # Python integer combinatorics avoid fixed-width integer overflow.
    return (3 * comb(schedule.p, 4) / len(schedule.cycles)) * fsum(a * b for a, b in values)


@dataclass(frozen=True, slots=True)
class FourCycleRelease:
    estimate: float
    epsilon: float
    endpoint_epsilon: float
    sensitivity: int
    laplace_scale: float
    schedule: PublicSchedule
    reports: tuple[tuple[float, ...], ...]
    privacy_status: str = "ideal_protocol_research_simulation"


def simulate_four_cycles_private(
    graph: SimpleGraph, epsilon: float, *, seed: int | None = None,
    rng: np.random.Generator | None = None,
) -> FourCycleRelease:
    """One logical reporting round; no noiseless mode or graph-dependent selection.

    A seed or supplied Generator is research-only and must not be published as
    part of a protected transcript. Exact real-arithmetic privacy is analyzed
    separately from this floating-point simulator. Public n<4 is padded too;
    its target is zero, but the same randomized mechanism is still executed.
    """
    if isinstance(epsilon, bool) or not isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")
    scale = 24.0 / epsilon
    if not isfinite(scale) or scale <= 0 or epsilon / 2 == 0:
        raise ValueError("epsilon is outside the representable simulation range")
    if rng is not None and seed is not None:
        raise ValueError("supply either rng or seed, not both")
    if rng is not None and not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a NumPy Generator")
    rng = np.random.default_rng(seed) if rng is None else rng
    schedule = public_schedule(graph.num_vertices, rng)
    # Centralized orchestration models separate clients. The local function sees
    # only its own adjacency row. Dummies have public empty rows and fresh noise.
    reports = tuple(_local_reports(graph.adjacency[v] if v < graph.num_vertices
                                  else frozenset(), requests, scale, rng)
                    for v, requests in enumerate(schedule.requests))
    return FourCycleRelease(aggregate(schedule, reports), float(epsilon), epsilon / 2,
                            12, scale, schedule, reports)
