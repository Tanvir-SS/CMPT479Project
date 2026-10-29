"""Stage A: exact identities, RR, conditional sensitivity and local reports."""

from dataclasses import asdict
from fractions import Fraction
from itertools import combinations, permutations, product
import json
import math

import numpy as np
import pytest

from private_graphlets.four_clique import (
    CliqueBudget, allocate_budget, conditional_sensitivity, estimate_four_cliques,
    local_count_report, local_score, simulate_four_cliques, simulation_streams,
)
from private_graphlets.four_clique_exact import (
    count_four_cliques, count_four_cliques_bruteforce, ranks, select_outgoing, validate_order,
)
from private_graphlets.graph import SimpleGraph
from private_graphlets.randomized_response import local_rr_row, rr_matrix, rr_parameters, sample_rr_upper


def clique(n):
    return SimpleGraph.from_edges(n, combinations(range(n),2))


@pytest.mark.parametrize("n", range(8))
def test_complete_counts(n):
    graph=clique(n)
    assert count_four_cliques(graph)==count_four_cliques_bruteforce(graph)==math.comb(n,4)
    assert count_four_cliques(graph,tuple(reversed(range(n))))==math.comb(n,4)


def test_all_graphs_through_five_and_small_permutations():
    for n in range(6):
        edges=list(combinations(range(n),2))
        for mask in range(1<<len(edges)):
            graph=SimpleGraph.from_edges(n,[edge for i,edge in enumerate(edges) if mask>>i&1])
            truth=count_four_cliques_bruteforce(graph)
            orders=permutations(range(n)) if n<=4 else (tuple(range(n)),tuple(reversed(range(n))))
            for order in orders:
                assert count_four_cliques(graph,order)==truth


@pytest.mark.parametrize("order", [(0,0,2),(0,1),(0,1,3),(0,True,2)])
def test_invalid_order(order):
    with pytest.raises(ValueError): validate_order(3,order)


def test_orientation_and_cap_targets():
    order=(2,0,4,1,3)
    rank=ranks(order)
    graph=clique(5)
    out=[select_outgoing(v,row,rank,4) for v,row in enumerate(graph.adjacency)]
    for u,v in combinations(range(5),2):
        assert (v in out[u]) != (u in out[v])
    for cap,expected in [(2,0),(3,2),(4,5)]:
        assert count_four_cliques(graph,cap=cap)==expected
    assert count_four_cliques(SimpleGraph.from_edges(8,combinations(range(4),2)))==1


@pytest.mark.parametrize("epsilon", [0,-1,float('nan'),float('inf'),True,'1',31,1e-310])
def test_rr_invalid(epsilon):
    with pytest.raises(ValueError): rr_parameters(epsilon)


class RecordingUniform:
    def __init__(self): self.sizes=[]
    def random(self,size):
        self.sizes.append(size)
        return np.ones(size)*0.9


def test_one_report_per_owned_pair_and_mirroring():
    rng=RecordingUniform()
    graph=SimpleGraph.from_edges(5,[(0,1),(1,4)])
    report=sample_rr_upper(graph,1,rng)
    assert len(report)==10 and rng.sizes==[4,3,2,1,0]
    assert report==(True,False,False,False,False,False,True,False,False,False)
    weights=rr_matrix(5,report,1)
    assert np.array_equal(weights,weights.T) and not np.any(weights.diagonal())
    assert not weights.flags.writeable


def test_rr_means_and_pair_independence():
    trials=200_000
    rng=np.random.default_rng(600101)
    params=rr_parameters(0.7)
    bits=np.array(local_rr_row(2*trials+1,0,frozenset(range(1,trials+1)),0.7,rng))
    w=np.where(bits,params.maximum,-params.a)
    first,second=w[:trials]-1,w[trials:]
    for residual in (first,second):
        assert abs(residual.mean())<6*math.sqrt(params.variance/trials)
    # Independent reports: Var[(W-A)(W'-A')]=tau^2, not fitted from observations.
    assert abs(np.mean(first*second))<6*params.variance/math.sqrt(trials)


@pytest.mark.parametrize("truth", list(product((0,1),repeat=3)))
def test_product_expectation_exact_and_sampled(truth):
    eta=math.log(2)
    expectation=Fraction(0)
    for report in product((0,1),repeat=3):
        probability=math.prod(Fraction(2 if r==a else 1,3) for r,a in zip(report,truth))
        expectation+=probability*math.prod(3*r-1 for r in report)
    assert expectation==math.prod(truth)
    graph=SimpleGraph.from_edges(3,[edge for edge,a in zip(combinations(range(3),2),truth) if a])
    rng=np.random.default_rng(600102+sum(a*2**i for i,a in enumerate(truth)))
    samples=[]
    for _ in range(6000):
        reports=sample_rr_upper(graph,eta,rng)
        samples.append(math.prod(3*r-1 for r in reports))
    variance=math.prod(a+2 for a in truth)-math.prod(truth)
    assert abs(np.mean(samples)-math.prod(truth))<6*math.sqrt(variance/len(samples))


def test_exhaustive_cap_replacement_sensitivity():
    eta=math.log(2)
    pairs=list(combinations(range(1,5),2))
    for reports in product((False,True),repeat=6):
        weights=np.zeros((5,5))
        for (a,b),r in zip(pairs,reports): weights[a,b]=weights[b,a]=3*r-1
        for mask in range(16):
            old={v for v in range(1,5) if mask>>(v-1)&1}
            for new in set(range(1,5))-old:
                for cap in range(5):
                    before=local_score(sorted(old)[:cap],weights)
                    after=local_score(sorted(old|{new})[:cap],weights)
                    assert abs(after-before)<=conditional_sensitivity(cap,eta)+1e-12
                    assert abs(before-after)<=conditional_sensitivity(cap,eta)+1e-12
    weights=np.zeros((5,5))
    for u,v in [(2,3),(1,2),(1,3),(3,4)]: weights[u,v]=weights[v,u]=2
    weights[2,4]=weights[4,2]=-1
    assert local_score((1,2,3),weights)-local_score((2,3,4),weights)==12
    assert conditional_sensitivity(3,eta)==pytest.approx(12)


class LaplaceSpy:
    def __init__(self): self.calls=[]
    def laplace(self,location,scale):
        self.calls.append((location,scale))
        return -100.0


def test_noise_before_report_and_fixed_schedule():
    rng=LaplaceSpy()
    weights=np.ones((5,5))-np.eye(5)
    assert local_count_report(0,frozenset((1,2,3)),range(5),4,weights,7,rng)==-99
    assert local_count_report(4,frozenset(),range(5),4,weights,7,rng)==-100
    assert rng.calls==[(0,7),(0,7)]
    assert local_count_report(0,frozenset((1,2)),range(5),2,weights,0,rng)==0
    assert len(rng.calls)==2


def test_release_schema_reproducibility_and_scale():
    one=simulate_four_cliques(clique(5),2,seed=600104)
    two=simulate_four_cliques(clique(5),2,seed=600104)
    assert one==two
    assert one!=simulate_four_cliques(clique(5),2,seed=600105)
    assert len(one.transcript.local_reports)==5 and len(one.transcript.rr_upper)==10
    assert one.result.local_noise_scale==conditional_sensitivity(4,1)/1
    assert one.result.estimate==math.fsum(one.transcript.local_reports)
    fields=set(one.result.to_dict())|set(asdict(one.transcript))
    assert not fields & {'degrees','adjacency','neighbors','exact_count','seed','rng_state','scores'}
    json.dumps(one.result.to_dict(),allow_nan=False)


def test_budget_and_domain_separation():
    for mode in ('public','uncapped'):
        b=allocate_budget(2,'fixed',mode)
        assert b==CliqueBudget(2,0,0,1,1)
    with pytest.raises(ValueError): CliqueBudget(2,0,0,1,2)
    with pytest.raises(ValueError): estimate_four_cliques(clique(4),2,budget=CliqueBudget(3,0,0,1,2))
    streams=simulation_streams(600106)
    first=[r.random(10) for r in streams]
    assert all(not np.array_equal(a,b) for a,b in combinations(first,2))
    assert all(np.array_equal(a,r.random(10)) for a,r in zip(first,simulation_streams(600106)))


@pytest.mark.parametrize("graph", [clique(4),SimpleGraph.from_edges(4,[])])
def test_uncapped_graph_mean_with_analytic_se(graph):
    ntrials=6000
    epsilon=4
    budget=allocate_budget(epsilon,'fixed','uncapped')
    params=rr_parameters(budget.rr)
    truth=count_four_cliques_bruteforce(graph)
    rr_variance=(1+params.variance)**3-1 if truth else 0
    scale=conditional_sensitivity(3,budget.rr)/budget.count
    variance=rr_variance+2*4*scale**2
    estimates=[estimate_four_cliques(graph,epsilon,seed=600200+i).estimate for i in range(ntrials)]
    assert abs(np.mean(estimates)-truth)<6*math.sqrt(variance/ntrials)
    assert min(estimates)<0


@pytest.mark.parametrize("n", range(4))
def test_public_small_n_zero(n):
    result=simulate_four_cliques(clique(n),1,seed=1)
    assert result.result.estimate==0 and result.transcript.local_reports==()


@pytest.mark.escape_integration
@pytest.mark.parametrize("n",range(8))
def test_exact_against_escape(escape_adapter,n):
    graph=clique(n)
    observed=escape_adapter.run(graph).counts.connected_four['4-clique']
    assert observed==count_four_cliques(graph)==count_four_cliques_bruteforce(graph)
