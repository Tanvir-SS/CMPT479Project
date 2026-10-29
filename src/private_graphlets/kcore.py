"""Experimental Python port of k-CoreD's threshold/level protocol.

Adapted from DistributedLEDPGraphAlgos (MIT, Pranay Mundra, 2024), commit
b03da893ba1c38d3931708bac919562c5ab57963. See THIRD_PARTY_NOTICES.md and
docs/KCORED_INTEGRATION.md for attribution, differences and unresolved guarantees.
"""

from dataclasses import dataclass
import math

import numpy as np

from private_graphlets.graph import SimpleGraph, _nonnegative_integer
from private_graphlets.noise import validate_epsilon


@dataclass(frozen=True)
class KCoreConfig:
    psi: float = 0.5
    threshold_fraction: float = 0.5
    bias_factor: int = 1

    def __post_init__(self):
        for name in ("psi", "threshold_fraction"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int,float)) or not 0 < value < 1:
                raise ValueError(f"{name} must be strictly between zero and one")
        _nonnegative_integer(self.bias_factor,"bias_factor")


@dataclass(frozen=True)
class KCoreTranscript:
    """Thresholds/promotion bits are the full releases; levels are postprocessing."""
    thresholds: tuple[int, ...]
    promotions: tuple[tuple[int, ...], ...]
    levels: tuple[int, ...]
    epsilon: float
    threshold_fraction: float
    levels_per_group: float
    nominal_round_limit: int
    ordering_type: str = "kcore_private_simulation"
    privacy_status: str = "experimental_unverified"

    @property
    def order(self) -> tuple[int, ...]:
        return tuple(sorted(range(len(self.levels)),key=lambda v:(self.levels[v],v)))


def symmetric_geometric(parameter: float, rng: np.random.Generator, size=None):
    """Difference of two independent Geom(1-exp(-s)) variables.

    Ideal PMF is tanh(s/2)*exp(-s*abs(k)), identical to the Go target law.
    NumPy sampling/finite integer range are not a certified DP implementation.
    """
    s = validate_epsilon(parameter)
    if not 1e-10 <= s <= 30:
        raise ValueError("geometric simulation parameter must be in [1e-10,30]")
    probability = -math.expm1(-s)
    first = rng.geometric(probability,size=size)
    second = rng.geometric(probability,size=size)
    # Cast scalar to Python int BEFORE subtraction; vector casts prevent wrap.
    if size is None:
        return int(first)-int(second)
    return np.asarray(first,dtype=object)-np.asarray(second,dtype=object)


def degree_threshold(degree: int, lambda1: float, levels_per_group: float,
                     bias_factor: int, rng: np.random.Generator) -> int:
    """Client-local noised degree -> threshold; raw/noisy degree is not returned."""
    value = degree + symmetric_geometric(lambda1/2,rng)
    correction = bias_factor*2*math.exp(lambda1)/math.expm1(2*lambda1)
    # Match the Go integer conversion (truncate toward zero) before subtraction.
    shifted = value-int(min(correction,value))+1
    return int(math.ceil(math.log2(shifted))*levels_per_group)+1


def promotion_bit(neighbors: frozenset[int], levels: tuple[int, ...], round_index: int,
                   parameter: float, cutoff: int, rng: np.random.Generator) -> int:
    """Client-local same-level count -> one bit, never a raw count message."""
    count = sum(levels[w]==round_index for w in neighbors)
    noise = symmetric_geometric(parameter,rng)
    bias = int(6*math.exp(parameter)/math.expm1(2*parameter)**3)
    return int(count+noise+bias > cutoff)


def _run_levels(graph: SimpleGraph, epsilon: float, rng: np.random.Generator,
                config: KCoreConfig, *, oracle: bool) -> KCoreTranscript:
    epsilon=validate_epsilon(epsilon)
    if epsilon>1:
        raise ValueError("k-CoreD ordering epsilon must be <=1 in the paper's parameter regime")
    n=graph.num_vertices
    if n<2:
        return KCoreTranscript((0,)*n,(),(0,)*n,epsilon,config.threshold_fraction,1,0,
                               "nonprivate_kcore_oracle" if oracle else "kcore_private_simulation")
    logn=math.log(n)/math.log1p(config.psi)
    group=math.ceil(logn)/4
    limit=max(0,math.ceil(4*logn**1.2)-2)
    if not math.isfinite(group) or limit>100_000:
        raise ValueError("public k-CoreD round limit exceeds simulator scope")
    lambda1=epsilon*config.threshold_fraction
    lambda2=epsilon*(1-config.threshold_fraction)
    # Prevalidate the smallest possible per-round parameter on this bounded
    # simulator domain. Further range failures are explicit, not silent fallbacks.
    if not oracle:
        symmetric_parameter=lambda1/2
        if symmetric_parameter<1e-10:
            raise ValueError("ordering epsilon too small for geometric simulation")
    thresholds=tuple(
        int(math.ceil(math.log2(max(1,len(row))))*group)+1 if oracle else
        degree_threshold(len(row),lambda1,group,config.bias_factor,rng)
        for row in graph.adjacency)
    # Unlike the Go worker maximum, we explicitly expose each noised threshold.
    # This is postprocessing of the same charged degree reports and permits an
    # unambiguous conditional budget ledger for every subsequent history.
    levels=[0]*n
    active=[True]*n
    messages=[]
    for r in range(min(limit,max(thresholds))):
        before=tuple(levels)  # synchronous barrier: never read this round's updates
        cutoff=int((1+config.psi)**math.floor(r/group))
        bits=[]
        for v,row in enumerate(graph.adjacency):
            if r>=thresholds[v]: active[v]=False
            bit=0
            if active[v] and before[v]==r:
                if oracle:
                    bit=int(sum(before[w]==r for w in row)>cutoff)
                else:
                    bit=promotion_bit(row,before,r,lambda2/(2*thresholds[v]),cutoff,rng)
                if not bit: active[v]=False
            bits.append(bit)
        messages.append(tuple(bits))
        levels=[level+bit for level,bit in zip(levels,bits)]
    return KCoreTranscript(thresholds,tuple(messages),tuple(levels),epsilon,
                           config.threshold_fraction,group,limit,
                           "nonprivate_kcore_oracle" if oracle else "kcore_private_simulation")


def kcore_order(graph: SimpleGraph, epsilon: float, rng: np.random.Generator,
                 config: KCoreConfig | None = None) -> KCoreTranscript:
    """Noised k-CoreD levels, never a degree/degeneracy fallback."""
    return _run_levels(graph,epsilon,rng,config or KCoreConfig(),oracle=False)


def nonprivate_kcore_oracle(graph: SimpleGraph, config: KCoreConfig | None = None) -> KCoreTranscript:
    """NON-PRIVATE, noise/bias-disabled control; not accepted by the private API."""
    return _run_levels(graph,1,np.random.default_rng(0),config or KCoreConfig(),oracle=True)


def ordering_budget_ledger(transcript: KCoreTranscript) -> tuple[float, ...]:
    """Conservative per-vertex expenditure, computed only from released messages."""
    if transcript.ordering_type!="kcore_private_simulation":
        raise ValueError("a non-private oracle has no privacy budget ledger")
    n=len(transcript.levels)
    used=[0]*n
    levels=[0]*n
    for r,bits in enumerate(transcript.promotions):
        for v in range(n):
            if r<transcript.thresholds[v] and levels[v]==r:
                used[v]+=1
        levels=[a+b for a,b in zip(levels,bits)]
    eps1=transcript.epsilon*transcript.threshold_fraction
    eps2=transcript.epsilon*(1-transcript.threshold_fraction)
    return tuple(0.0 if t==0 else eps1/2+q*eps2/(2*t)
                 for t,q in zip(transcript.thresholds,used))
