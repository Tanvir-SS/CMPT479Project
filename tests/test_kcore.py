"""Private-level port, full transcript accounting and explicit non-private control."""

from dataclasses import asdict
from itertools import combinations
import math

import numpy as np
import pytest

from private_graphlets.four_clique_exact import count_four_cliques, count_four_cliques_bruteforce
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import (
    KCoreConfig, degree_threshold, kcore_order, nonprivate_kcore_oracle,
    ordering_budget_ledger, promotion_bit, symmetric_geometric,
)


@pytest.mark.parametrize('parameter',[0.05,0.3,1.0])
def test_geometric_law(parameter):
    n=120_000
    values=np.array(symmetric_geometric(parameter,np.random.default_rng(600301),n),dtype=float)
    q=math.exp(-parameter)
    variance=2*q/(1-q)**2
    assert abs(values.mean())<6*math.sqrt(variance/n)
    # Fourth moment of the symmetric geometric distribution.
    fourth=2*q*(1+10*q+q*q)/(1-q)**4
    assert abs(np.mean(values**2)-variance)<6*math.sqrt((fourth-variance**2)/n)
    for k in [-2,-1,0,1,2]:
        probability=(1-q)/(1+q)*q**abs(k)
        assert abs(np.mean(values==k)-probability)<6*math.sqrt(probability*(1-probability)/n)


@pytest.mark.parametrize('epsilon',[0,-1,float('nan'),float('inf'),True,1.1])
def test_ordering_epsilon_domain(epsilon):
    with pytest.raises(ValueError):
        kcore_order(SimpleGraph.from_edges(4,[]),epsilon,np.random.default_rng(0))


@pytest.mark.parametrize('config',[{'psi':0},{'psi':1},{'psi':float('nan')},
                                  {'threshold_fraction':0},{'threshold_fraction':1},
                                  {'bias_factor':-1},{'bias_factor':True}])
def test_config_validation(config):
    with pytest.raises(ValueError): KCoreConfig(**config)


def test_threshold_and_round_trace_with_zero_noise(monkeypatch):
    # Retain deterministic Go bias transformations; zero noise is injection for
    # a source-formula check, not a claimed private randomizer.
    monkeypatch.setattr('private_graphlets.kcore.symmetric_geometric',lambda parameter,rng:0)
    # lambda1=.5; floor(2*exp(.5)/expm1(1))=1, so degree 3 -> shifted 3.
    assert degree_threshold(3,0.5,1.0,1,None)==3
    assert degree_threshold(0,0.5,1.0,1,None)==1
    graph=SimpleGraph.from_edges(4,combinations(range(4),2))
    result=kcore_order(graph,1,np.random.default_rng(1))
    # L=ceil(log_1.5(4))/4=1; every threshold is 3. Positive level bias
    # makes all vertices promote three times, then they stop at threshold.
    assert result.thresholds==(3,3,3,3)
    assert result.promotions==((1,1,1,1),)*3
    assert result.levels==(3,3,3,3) and result.order==(0,1,2,3)
    assert ordering_budget_ledger(result)==(0.5,)*4


def test_local_promotion_uses_snapshot_only(monkeypatch):
    monkeypatch.setattr('private_graphlets.kcore.symmetric_geometric',lambda parameter,rng:0)
    # At s=1, int(bias)=0; exactly two same-level neighbors beats cutoff 1.
    assert promotion_bit(frozenset([1,2,3]),(0,0,0,1),0,1,1,None)==1
    assert promotion_bit(frozenset([1,2,3]),(0,0,1,1),0,1,1,None)==0


@pytest.mark.parametrize('n',[0,1,2,5,12])
def test_transcript_budget_and_noise_free_correctness(n):
    graph=SimpleGraph.from_edges(n,combinations(range(n),2))
    for seed in range(10):
        transcript=kcore_order(graph,0.5,np.random.default_rng(seed))
        assert transcript==kcore_order(graph,0.5,np.random.default_rng(seed))
        assert sorted(transcript.order)==list(range(n))
        assert all(len(bits)==n and set(bits)<={0,1} for bits in transcript.promotions)
        assert transcript.levels==tuple(sum(bits[v] for bits in transcript.promotions) for v in range(n))
        assert all(level<=threshold for level,threshold in zip(transcript.levels,transcript.thresholds))
        assert all(value<=0.25+1e-14 for value in ordering_budget_ledger(transcript))
        assert count_four_cliques(graph,transcript.order)==count_four_cliques_bruteforce(graph)
        assert not set(asdict(transcript)) & {'neighbors','adjacency','degrees','counts','seed'}
    oracle=nonprivate_kcore_oracle(graph)
    assert oracle.ordering_type=='nonprivate_kcore_oracle'
    assert count_four_cliques(graph,oracle.order)==count_four_cliques_bruteforce(graph)
    with pytest.raises(ValueError): ordering_budget_ledger(oracle)


def test_private_order_changes_with_noise_and_never_falls_back():
    graph=SimpleGraph.from_edges(8,combinations(range(6),2))
    transcripts=[kcore_order(graph,0.5,np.random.default_rng(i)) for i in range(30)]
    assert len({t.thresholds for t in transcripts})>1
    assert len({t.order for t in transcripts})>1
    assert all(t.ordering_type=='kcore_private_simulation' for t in transcripts)


def test_geometric_neighbor_likelihood_bound_exact_grid():
    s=0.3
    for z in range(-40,41):
        # Ideal infinite-support PMF, a mathematical check distinct from sampler tests.
        log_ratio=-s*abs(z)+s*abs(z-1)
        assert abs(log_ratio)<=s+1e-14
