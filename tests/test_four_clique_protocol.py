"""Integrated protocol, private cap, baseline and public/private boundaries."""

from dataclasses import asdict
from itertools import combinations, product
import math

import numpy as np
import pytest

from private_graphlets.four_clique import (
    CliqueBudget, allocate_budget, cap_from_reports, conditional_sensitivity,
    local_cap_report, local_score, simulate_four_cliques,
)
from private_graphlets.four_clique_baseline import baseline_score, estimate_four_cliques_baseline
from private_graphlets.four_clique_exact import count_four_cliques, ranks, select_outgoing
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import ordering_budget_ledger
from private_graphlets.randomized_response import rr_matrix


def clique(n): return SimpleGraph.from_edges(n,combinations(range(n),2))


@pytest.mark.parametrize('ordering', ['fixed','kcore'])
@pytest.mark.parametrize('mode', ['public','noisy','uncapped'])
@pytest.mark.parametrize('epsilon',[0.5,4.0])
def test_full_protocol(ordering,mode,epsilon):
    kwargs={'ordering':ordering,'cap_mode':mode,'seed':600401}
    if mode=='public': kwargs['cap']=3
    run=simulate_four_cliques(clique(6),epsilon,**kwargs)
    assert run==simulate_four_cliques(clique(6),epsilon,**kwargs)
    t=run.transcript
    b=run.result.budget
    assert math.fsum((b.ordering,b.cap,b.rr,b.count))==pytest.approx(epsilon)
    assert len(t.rr_upper)==15 and len(t.local_reports)==6
    assert run.result.estimate==math.fsum(t.local_reports)
    assert run.result.local_noise_scale==conditional_sensitivity(t.cap,b.rr)/b.count
    assert len(t.cap_reports)==(6 if mode=='noisy' else 0)
    if ordering=='kcore':
        assert t.ordering.order==t.order
        assert all(value<=b.ordering/2+1e-14 for value in ordering_budget_ledger(t.ordering))
    else: assert t.ordering is None and t.order==tuple(range(6))
    record=asdict(t)
    assert set(record)=={'ordering','order','cap_reports','cap','rr_upper','local_reports'}
    assert not set(run.result.to_dict()) & {'degrees','max_out_degree','retained_count','seed','scores'}


def test_allocations_explicit():
    assert allocate_budget(4,'kcore','noisy')==CliqueBudget(4,1,1,1,1)
    assert allocate_budget(4,'kcore','public')==CliqueBudget(4,1,0,1.5,1.5)
    assert allocate_budget(3,'fixed','noisy')==CliqueBudget(3,0,1,1,1)


def test_cap_postprocessing_and_underestimation_enforced(monkeypatch):
    n=5
    epsilon_d=1
    beta=0.1
    margin=math.log(n/beta)
    reports=(-margin+2.5,)*n
    assert cap_from_reports(reports,n,epsilon_d,beta)==3
    assert cap_from_reports((-100.,)*n,n,epsilon_d,beta)==0
    assert cap_from_reports((100.,)*n,n,epsilon_d,beta)==4
    monkeypatch.setattr('private_graphlets.four_clique.local_cap_report',lambda *args:-100.)
    run=simulate_four_cliques(clique(5),4,cap_mode='noisy',seed=1)
    assert run.transcript.cap==0 and run.transcript.local_reports==(0.,)*5
    assert run.result.estimate==0 and count_four_cliques(clique(5))==5


def test_conditional_cap_degree_sensitivity_one():
    class ZeroNoise:
        def __init__(self): self.calls=[]
        def laplace(self,loc,scale): self.calls.append((loc,scale)); return 0
    rng=ZeroNoise()
    graph=SimpleGraph.from_edges(5,[(0,2),(1,4)])
    other=SimpleGraph.from_edges(5,[(0,2),(1,4),(0,1)])
    rank=ranks((2,1,4,0,3))
    a=[local_cap_report(v,row,rank,0.5,rng) for v,row in enumerate(graph.adjacency)]
    b=[local_cap_report(v,row,rank,0.5,rng) for v,row in enumerate(other.adjacency)]
    assert sum(abs(x-y) for x,y in zip(a,b))==1
    assert rng.calls==[(0,2.)]*10


def test_changed_edge_only_one_final_local_score_for_fixed_transcript():
    graph=clique(5)
    other=SimpleGraph.from_edges(5,[e for e in combinations(range(5),2) if e!=(0,1)])
    rank=ranks((1,3,2,4,0))
    weights=rr_matrix(5,(True,False)*5,math.log(2))
    scores=lambda g:[local_score(select_outgoing(v,row,rank,3),weights) for v,row in enumerate(g.adjacency)]
    a,b=scores(graph),scores(other)
    assert all(a[v]==b[v] for v in range(5) if v!=1)
    assert abs(a[1]-b[1])<=conditional_sensitivity(3,math.log(2))+1e-12


@pytest.mark.parametrize('kwargs',[
    {'ordering':'degree'}, {'ordering':'kcore','public_order':(0,1,2,3)},
    {'cap_mode':'public'}, {'cap_mode':'public','cap':-1},
    {'cap_mode':'public','cap':4}, {'cap_mode':'noisy','cap':2},
    {'beta':0}, {'beta':1}, {'beta':True}, {'seed':-1},
    {'budget':CliqueBudget(2,0,1,0.5,0.5)},
])
def test_invalid_protocol_options(kwargs):
    with pytest.raises(ValueError): simulate_four_cliques(clique(4),2,**kwargs)


def test_baseline_exact_expectation_all_four_vertex_graphs():
    eta=math.log(2)
    for truth in product((0,1),repeat=6):
        mean=0.
        for report in product((False,True),repeat=6):
            probability=math.prod((2 if r==a else 1)/3 for r,a in zip(report,truth))
            mean+=probability*baseline_score(rr_matrix(4,report,eta))
        assert mean==pytest.approx(math.prod(truth),abs=1e-12)


@pytest.mark.parametrize('truth', [0,1])
def test_baseline_sampled_mean(truth):
    graph=clique(4) if truth else SimpleGraph.from_edges(4,[])
    eta=2.
    tau=math.exp(eta)/math.expm1(eta)**2
    variance=(truth+tau)**6-truth
    samples=[estimate_four_cliques_baseline(graph,eta,seed=601000+i).estimate for i in range(6000)]
    assert abs(np.mean(samples)-truth)<6*math.sqrt(variance/len(samples))
    result=estimate_four_cliques_baseline(graph,eta,seed=5)
    assert result.budget==CliqueBudget(eta,0,0,eta,0) and result.local_noise_scale==0


def test_shared_rr_covariance_book_graph():
    # Exact second moment on the three shared closing reports, r=4 centers.
    r=4
    values=[]
    for report in product((0,1),repeat=3):
        probability=math.prod((2 if bit else 1)/3 for bit in report)
        values.append((probability,r*math.prod(3*bit-1 for bit in report)))
    mean=sum(p*x for p,x in values)
    variance=sum(p*(x-mean)**2 for p,x in values)
    assert mean==pytest.approx(4) and variance==pytest.approx(416)
