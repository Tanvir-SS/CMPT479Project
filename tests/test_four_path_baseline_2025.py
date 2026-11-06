"""Independent normalization, RR laws/moments and native P4 target validation."""
from dataclasses import asdict
from itertools import combinations, permutations, product
import json
import math
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.four_path_exact import count_four_paths, count_four_paths_bruteforce
from private_graphlets.randomized_response import rr_matrix, rr_parameters, local_rr_row
from private_graphlets import four_path_baseline_2025 as baseline

PROJECT = Path(__file__).resolve().parents[1]
TRUTHS = dict(edgeless=0, star=0, path=1, tailed_triangle=2, cycle=4, diamond=6,
              clique=12, clique_with_isolates=12)


def adjacency(graph):
    return np.array([[float(v in row) for v in range(graph.num_vertices)] for row in graph.adjacency],
                    dtype=np.float64).reshape(graph.num_vertices, graph.num_vertices)


def literal(weights):
    return math.fsum(float(weights[a,b])*float(weights[b,c])*float(weights[c,d])
                     for a,b,c,d in permutations(range(len(weights)),4))/2


def path_sets(n):
    # Independent combinatorial oracle: edge sets of each unlabeled P4 copy.
    return {frozenset(tuple(sorted(e)) for e in ((a,b),(b,c),(c,d)))
            for a,b,c,d in permutations(range(n),4)}


def oracle_variance(graph, epsilon):
    # Expand polynomial in centered, independent unordered-pair noise. No call
    # to implementation's server formula or coefficients.
    coefficients = {}
    for path in path_sets(graph.num_vertices):
        for size in [1,2,3]:
            for selected in combinations(path,size):
                subset=frozenset(selected)
                remaining=path-subset
                coefficient=int(all(v in graph.adjacency[u] for u,v in remaining))
                coefficients[subset]=coefficients.get(subset,0)+coefficient
    h=math.exp(epsilon)/math.expm1(epsilon)**2
    return math.fsum(c*c*h**len(s) for s,c in coefficients.items())


@pytest.mark.parametrize('n',range(6))
def test_all_labeled_graphs_normalization(n):
    pairs=list(combinations(range(n),2))
    for mask in range(1<<len(pairs)):
        graph=SimpleGraph.from_edges(n,[e for i,e in enumerate(pairs) if mask>>i&1])
        w=adjacency(graph)
        truth=count_four_paths_bruteforce(graph)
        assert count_four_paths(graph)==truth
        assert literal(w)==truth
        assert baseline.four_path_weighted_sum(w)==truth


@pytest.mark.parametrize('n',[0,1,2,3,4,5,8])
def test_exact_algebra_on_signed_weights(n):
    rng=np.random.default_rng(160100+n)
    for _ in range(10):
        w=rng.normal(size=(n,n));w=np.triu(w,1);w=w+w.T
        before=w.copy()
        assert baseline.four_path_weighted_sum(w)==pytest.approx(literal(w),abs=1e-10)
        np.testing.assert_array_equal(w,before)


def test_all_n4_graphs_full_rr_expectation_variance_and_privacy():
    epsilon=math.log(2);q=1/3
    budget=baseline.Baseline2025Budget(epsilon)
    pairs=list(combinations(range(4),2));bits=list(product([False,True],repeat=6))
    scores=np.array([baseline.estimate_from_reports(4,b,budget).estimate for b in bits])
    assert any(scores<0) and any(abs(scores-np.round(scores))>1e-12) is False  # weights -1/2 here
    laws=[]
    for mask in range(64):
        truth_bits=[bool(mask>>i&1) for i in range(6)]
        graph=SimpleGraph.from_edges(4,[e for e,x in zip(pairs,truth_bits) if x])
        probabilities=np.array([math.prod(1-q if y==x else q for x,y in zip(truth_bits,b)) for b in bits])
        laws.append(probabilities)
        truth=count_four_paths_bruteforce(graph)
        assert probabilities.sum()==pytest.approx(1)
        assert float(probabilities@scores)==pytest.approx(truth,abs=1e-11)
        variance=float(probabilities@((scores-truth)**2))
        assert variance==pytest.approx(oracle_variance(graph,epsilon),rel=1e-12,abs=1e-10)
    for mask in range(64):
        for edge in range(6):
            ratio=laws[mask]/laws[mask^(1<<edge)]
            assert ratio.min()==pytest.approx(math.exp(-epsilon))
            assert ratio.max()==pytest.approx(math.exp(epsilon))
    # This is exact finite-law implementation evidence, not executable DP proof.


@pytest.mark.parametrize('name',TRUTHS)
def test_fixture_expectation_by_three_coin_marginals(name):
    g=load_edge_list(PROJECT/f'data/fixtures/{name}.edges');epsilon=1.3
    q=1/(1+math.exp(epsilon));hi=math.exp(epsilon)/math.expm1(epsilon);lo=-1/math.expm1(epsilon)
    expected=0.
    for path in path_sets(g.num_vertices):
        edges=sorted(path);truth=[v in g.adjacency[u] for u,v in edges]
        for bits in product([False,True],repeat=3):
            probability=math.prod(1-q if x==y else q for x,y in zip(truth,bits))
            expected+=probability*math.prod(hi if b else lo for b in bits)
    assert expected==pytest.approx(TRUTHS[name],abs=1e-10)


@pytest.mark.parametrize('name',TRUTHS)
def test_bounded_seeded_mean_against_independent_variance(name):
    g=load_edge_list(PROJECT/f'data/fixtures/{name}.edges')
    epsilon=2.;budget=baseline.Baseline2025Budget(epsilon)
    ntrials=3000;seed=160500+list(TRUTHS).index(name)
    rng=np.random.default_rng(seed)
    values=np.array([baseline.simulate_four_paths_baseline_2025(g,budget=budget,rng=rng).result.estimate
                     for _ in range(ntrials)])
    truth=TRUTHS[name];variance=oracle_variance(g,epsilon);se=math.sqrt(variance/ntrials)
    error=float(values.mean())-truth
    assert abs(error)<=6*se  # fixed seed/count/6 analytic-SE tolerance, before execution
    evidence=PROJECT/'build/phase16/moments';evidence.mkdir(parents=True,exist_ok=True)
    (evidence/f'{name}.json').write_text(json.dumps(dict(graph=name,trials=ntrials,seed=seed,epsilon=epsilon,
        truth=truth,mean=float(values.mean()),ideal_variance=variance,mean_standard_error=se,
        standardized_mean_error=error/se,threshold=6),indent=2)+'\n')


@pytest.mark.escape_integration
@pytest.mark.parametrize('name',TRUTHS)
def test_mathematical_target_against_actual_escape(escape_adapter,name):
    g=load_edge_list(PROJECT/f'data/fixtures/{name}.edges');native=escape_adapter.run(g)
    score=baseline.four_path_weighted_sum(adjacency(g))
    evidence=PROJECT/'build/phase16/escape';evidence.mkdir(parents=True,exist_ok=True)
    (evidence/f'{name}.json').write_text(json.dumps({'native':asdict(native),'polynomial_target':score,
       'python_exact':count_four_paths(g)},indent=2)+'\n')
    assert score==count_four_paths(g)==native.counts.connected_four['3-path']==TRUTHS[name]


def test_one_owner_local_randomizer_and_report_only_server():
    class FixedRandom:
        def random(self,size):
            assert size==3
            return np.array([0.,.9,.9])
    assert local_rr_row(4,0,frozenset({1,3}),math.log(2),FixedRandom())==(False,False,True)
    g=SimpleGraph.from_edges(4,[(0,1)])
    reports=(True,False,False,True,True,False)
    with patch.object(baseline,'sample_rr_upper',return_value=reports) as sampler:
        run=baseline.simulate_four_paths_baseline_2025(g,budget=baseline.Baseline2025Budget(1),seed=42)
        assert sampler.call_count==1
    expected=literal(rr_matrix(4,reports,1))
    assert run.result.estimate==pytest.approx(expected)
    assert run.transcript.rr_upper is reports
    assert set(asdict(run.transcript))=={'rr_upper'}
    assert set(asdict(run.result))=={'estimate','num_vertices','epsilon'}
    assert run.result.to_dict()['implementation']=='faithful_independent_reconstruction'
    assert not {'seed','edges','degrees','exact_count'} & set(run.result.to_dict())


def test_reproducible_streams_and_fractional_negative_output():
    g=SimpleGraph.from_edges(5,[(0,1),(1,2)])
    b=baseline.Baseline2025Budget(1)
    first=baseline.simulate_four_paths_baseline_2025(g,budget=b,seed=17)
    assert first==baseline.simulate_four_paths_baseline_2025(g,budget=b,seed=17)
    assert first.result==baseline.estimate_four_paths_baseline_2025(g,budget=b,seed=17)
    assert first==baseline.simulate_four_paths_baseline_2025(g,budget=b,rng=np.random.default_rng(17))
    negative=baseline.estimate_from_reports(4,(False,)*6,b).estimate
    assert negative<0 and negative!=round(negative)


@pytest.mark.parametrize('epsilon',[0,-1,True,float('nan'),float('inf'),31,1e-200])
def test_bad_epsilon(epsilon):
    with pytest.raises(ValueError): baseline.Baseline2025Budget(epsilon)


@pytest.mark.parametrize('kind',['shape','dtype','nan','infinity','asymmetry','diagonal','huge','oversize'])
def test_bad_weights(kind):
    w=np.zeros((4,4),dtype=np.float64)
    if kind=='shape': w=np.zeros((4,3))
    if kind=='dtype': w=w.astype(int)
    if kind=='nan': w[0,1]=w[1,0]=float('nan')
    if kind=='infinity': w[0,1]=w[1,0]=float('inf')
    if kind=='asymmetry': w[0,1]=1
    if kind=='diagonal': w[0,0]=1
    if kind=='huge': w[0,1]=w[1,0]=1e200
    if kind=='oversize': w=np.zeros((101,101))
    with pytest.raises(ValueError): baseline.four_path_weighted_sum(w)


def test_invalid_inputs_and_pre_sampling_overflow_guard():
    b=baseline.Baseline2025Budget(1);g=SimpleGraph.from_edges(4,[])
    for kwargs in [{'seed':True},{'seed':-1},{'rng':object()}, {'seed':1,'rng':np.random.default_rng(1)}]:
        with pytest.raises(ValueError): baseline.simulate_four_paths_baseline_2025(g,budget=b,**kwargs)
    with pytest.raises(ValueError): baseline.simulate_four_paths_baseline_2025(object(),budget=b)
    with pytest.raises(ValueError): baseline.simulate_four_paths_baseline_2025(g,budget=1)
    with pytest.raises(ValueError): baseline.simulate_four_paths_baseline_2025(SimpleGraph.from_edges(101,[]),budget=b)
    for n,reports,budget in [(True,(),b),(4,(),b),(4,(1,)*6,b),(4,(False,)*6,1)]:
        with pytest.raises(ValueError): baseline.estimate_from_reports(n,reports,budget)
    with patch.object(baseline,'sample_rr_upper',side_effect=AssertionError('must not sample')):
        with pytest.raises(ValueError,match='arithmetic'):
            baseline.simulate_four_paths_baseline_2025(g,budget=baseline.Baseline2025Budget(1e-103))


def test_dense_public_limit_and_isolates():
    # No randomized trial; deterministic formula at the supported size boundary.
    w=np.ones((100,100));np.fill_diagonal(w,0)
    assert baseline.four_path_weighted_sum(w)==12*math.comb(100,4)
    for n in range(4):
        run=baseline.simulate_four_paths_baseline_2025(SimpleGraph.from_edges(n,[]),budget=baseline.Baseline2025Budget(1),seed=1)
        assert run.result.estimate==0
        assert len(run.transcript.rr_upper)==n*(n-1)//2
