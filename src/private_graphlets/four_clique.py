"""Candidate four-clique local-report protocol; experimental, unverified simulator.

Local functions take one incident list. The driver owns the graph to simulate
clients; this is not a secure distributed deployment. Only noised messages enter
ProtocolTranscript. Exact diagnostic data must be computed separately.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from itertools import combinations
import math
from numbers import Integral

import numpy as np

from private_graphlets.four_clique_exact import ranks, select_outgoing, validate_cap, validate_order
from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import validate_epsilon
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper


@dataclass(frozen=True)
class CliqueBudget:
    total: float
    ordering: float
    cap: float
    rr: float
    count: float

    def __post_init__(self):
        validate_epsilon(self.total)
        for name in ("ordering", "cap", "rr", "count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("budget allocations must be finite nonnegative numbers")
        if not math.isclose(math.fsum((self.ordering, self.cap, self.rr, self.count)),
                            self.total, rel_tol=1e-14, abs_tol=0):
            raise ValueError("budget allocations must sum to total epsilon")
        validate_epsilon(self.rr)


def allocate_budget(epsilon: float, ordering: str, cap_mode: str) -> CliqueBudget:
    epsilon = validate_epsilon(epsilon)
    if ordering not in {"fixed", "kcore"} or cap_mode not in {"public", "noisy", "uncapped"}:
        raise ValueError("unknown ordering or cap mode")
    stages = 2 + (ordering == "kcore") + (cap_mode == "noisy")
    part = epsilon/stages
    if ordering == "kcore" and cap_mode != "noisy":
        # Stay in the paper's epsilon_O<=1 regime. Redistribution is public and
        # explicit; for total<=3 these are thirds, otherwise O=1 and R=C.
        order_part=min(part,1.0)
        return CliqueBudget(epsilon,order_part,0.0,(epsilon-order_part)/2,(epsilon-order_part)/2)
    return CliqueBudget(epsilon, part if ordering == "kcore" else 0.0,
                        part if cap_mode == "noisy" else 0.0, part, part)


def simulation_streams(seed: int | None) -> tuple[np.random.Generator, ...]:
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0):
        raise ValueError("simulation seed must be a nonnegative integer")
    # Fixed domain assignment: ordering, cap, RR, count; unused stages do not
    # change later streams. Seeds/states are never added to released records.
    return tuple(np.random.default_rng(child) for child in np.random.SeedSequence(
        None if seed is None else int(seed)).spawn(4))


def conditional_sensitivity(cap: int, epsilon_rr: float) -> float:
    if isinstance(cap, bool) or not isinstance(cap, Integral) or cap < 0:
        raise ValueError("cap must be a nonnegative integer")
    p = rr_parameters(epsilon_rr)
    value = 0.0 if cap < 3 else math.comb(int(cap)-1, 2)*p.maximum**2*(p.maximum+p.a)
    if not math.isfinite(value):
        raise ValueError("sensitivity exceeds finite float64 range")
    return value


def local_score(selected: Sequence[int], weights: np.ndarray) -> float:
    with np.errstate(over="raise", invalid="raise"):
        value = math.fsum(float(weights[a,b]*weights[a,c]*weights[b,c])
                          for a,b,c in combinations(selected, 3))
    if not math.isfinite(value):
        raise FloatingPointError("local score exceeds finite float64 range")
    return value


def local_count_report(vertex: int, neighbors: frozenset[int], rank: Sequence[int],
                       cap: int, weights: np.ndarray, scale: float,
                       rng: np.random.Generator) -> float:
    """Client computes and noises its score BEFORE returning a message."""
    if cap < 3:
        return 0.0
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("count-noise scale must be finite and positive")
    score = local_score(select_outgoing(vertex, neighbors, rank, cap), weights)
    report = score + float(rng.laplace(0, scale))
    if not math.isfinite(report):
        raise FloatingPointError("local report exceeds finite float64 range")
    return report


def local_cap_report(vertex: int, neighbors: frozenset[int], rank: Sequence[int],
                      epsilon_cap: float, rng: np.random.Generator) -> float:
    """One affected endpoint conditional on a fixed total order: sensitivity 1."""
    scale=1/validate_epsilon(epsilon_cap)
    if not math.isfinite(scale):
        raise ValueError("cap-noise scale exceeds float64")
    value=sum(rank[vertex]<rank[w] for w in neighbors)+float(rng.laplace(0,scale))
    if not math.isfinite(value):
        raise FloatingPointError("cap report exceeds finite float64 range")
    return value


def cap_from_reports(reports: Sequence[float], n: int, epsilon_cap: float, beta: float) -> int:
    if isinstance(beta,bool) or not isinstance(beta,(int,float)) or not 0<beta<1:
        raise ValueError("beta must be strictly between zero and one")
    epsilon_cap=validate_epsilon(epsilon_cap)
    if len(reports)!=n or any(not math.isfinite(x) for x in reports):
        raise ValueError("one finite cap report per public vertex is required")
    if n==0: return 0
    bound=max(reports)+(math.log(n)-math.log(beta))/epsilon_cap
    if not math.isfinite(bound):
        raise FloatingPointError("noisy cap bound exceeds float64")
    return min(n-1,max(0,math.ceil(bound)))


@dataclass(frozen=True)
class CliqueResult:
    estimate: float
    num_vertices: int
    ordering_type: str
    cap_mode: str
    released_cap: int | None
    budget: CliqueBudget
    local_noise_scale: float
    mechanism: str = "oriented_rr_four_clique"

    def to_dict(self) -> dict:
        return {"schema_version": 1, "result_type": "experimental_private_estimate",
                "pattern": "4-clique", "count_semantics": "non-induced_unlabeled",
                "simulation_only": True, "privacy_status": "experimental_unverified",
                **asdict(self)}


@dataclass(frozen=True)
class ProtocolTranscript:
    """Coordinator-visible messages only. No scores, degrees or selected lists."""
    ordering: object | None
    order: tuple[int, ...]
    cap_reports: tuple[float, ...]
    cap: int
    rr_upper: tuple[bool, ...]
    local_reports: tuple[float, ...]


@dataclass(frozen=True)
class CliqueRun:
    result: CliqueResult
    transcript: ProtocolTranscript


def simulate_four_cliques(graph: SimpleGraph, epsilon: float, *,
                          ordering: str = "fixed", cap_mode: str = "uncapped",
                          cap: int | None = None, public_order: Sequence[int] | None = None,
                          seed: int | None = None, budget: CliqueBudget | None = None,
                          beta: float = 0.05, kcore_config=None) -> CliqueRun:
    """Full research protocol with explicit local-report transcript; no exact data."""
    epsilon = validate_epsilon(epsilon)
    expected = allocate_budget(epsilon, ordering, cap_mode)
    budget = expected if budget is None else budget
    if not math.isclose(budget.total, epsilon, rel_tol=1e-14, abs_tol=0):
        raise ValueError("budget total differs from requested epsilon")
    if (budget.ordering > 0) != (ordering == "kcore") or (budget.cap > 0) != (cap_mode == "noisy"):
        raise ValueError("budget allocations do not match active stages")
    validate_epsilon(budget.count)
    rr_parameters(budget.rr)
    if isinstance(beta,bool) or not isinstance(beta,(int,float)) or not 0<beta<1:
        raise ValueError("beta must be strictly between zero and one")
    n = graph.num_vertices
    if n>1000:
        raise ValueError("dense four-clique simulator supports at most 1000 vertices")
    if ordering=="kcore" and public_order is not None:
        raise ValueError("a public order cannot replace private k-CoreD levels")
    order = validate_order(n, public_order)
    if cap_mode == "public":
        if cap is None:
            raise ValueError("public-cap mode requires a cap")
        cap = validate_cap(cap, n)
    else:
        if cap is not None:
            raise ValueError("cap is supplied only in public-cap mode")
        cap = max(0, n-1)
    rng_order, rng_cap, rng_rr, rng_count = simulation_streams(seed)
    ordering_type="kcore_private_simulation" if ordering=="kcore" else "fixed_public"
    if n < 4:
        result = CliqueResult(0.0,n,ordering_type,cap_mode,cap,budget,0.0)
        return CliqueRun(result,ProtocolTranscript(None,order,(),cap,(),()))
    order_transcript=None
    if ordering=="kcore":
        from private_graphlets.kcore import kcore_order
        order_transcript=kcore_order(graph,budget.ordering,rng_order,kcore_config)
        order=order_transcript.order
    rank=ranks(order)
    cap_reports=()
    if cap_mode=="noisy":
        cap_reports=tuple(local_cap_report(v,row,rank,budget.cap,rng_cap)
                          for v,row in enumerate(graph.adjacency))
        cap=cap_from_reports(cap_reports,n,budget.cap,beta)
    sensitivity = conditional_sensitivity(cap, budget.rr)
    scale = sensitivity / budget.count
    reports = sample_rr_upper(graph, budget.rr, rng_rr)
    weights = rr_matrix(n, reports, budget.rr)
    local = tuple(local_count_report(v, neighbors, rank, cap, weights, scale, rng_count)
                  for v, neighbors in enumerate(graph.adjacency))
    total=math.fsum(local)
    if not math.isfinite(total):
        raise FloatingPointError("aggregate exceeds finite float64 range")
    result = CliqueResult(total,n,ordering_type,cap_mode,cap,budget,scale)
    return CliqueRun(result,ProtocolTranscript(order_transcript,order,cap_reports,cap,reports,local))


def estimate_four_cliques(graph: SimpleGraph, epsilon: float, **kwargs) -> CliqueResult:
    """Aggregate-only API; exact evaluation and transcript inspection are separate."""
    return simulate_four_cliques(graph, epsilon, **kwargs).result
