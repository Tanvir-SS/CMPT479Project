"""Dataset-only provenance, canonicalization, deterministic sampling and exact checks."""

from itertools import combinations
import json
from pathlib import Path
import random
import shutil

import networkx as nx
import pytest

from private_graphlets.graph import load_edge_list
from private_graphlets.four_clique import allocate_budget
from private_graphlets.four_clique_exact import count_four_cliques, count_four_cliques_bruteforce
from private_graphlets import four_clique_experiments as experiments
from private_graphlets.graph_datasets import (
    PROJECT, BRIGHTKITE_SEED, RAW_SOURCES, canonical_bytes, digest, future_configs,
    generate_synthetic, json_bytes, load_canonical_graph, load_prepared_graph,
    normalize_graph, obtain_archive, parse_friendship_edges, parse_matrix_market,
    sample_connected_induced, synthetic_specs, verify_datasets, write_identical_or_new,
)

PROCESSED = PROJECT/'data/processed'
MANIFEST = json.loads((PROCESSED/'graph_manifest.json').read_text())
RECORDS = MANIFEST['graphs']


@pytest.mark.parametrize('record',RECORDS,ids=lambda r:r['id'])
def test_canonical_files_hashes_counts_and_component_inputs(record, monkeypatch):
    path = PROCESSED/record['path']
    g = load_canonical_graph(path)
    assert (g.num_vertices,g.num_edges)==(record['processed_vertices'],record['processed_edges'])
    assert digest(path)==record['sha256']
    assert path.read_bytes()==canonical_bytes(g) and b'\r' not in path.read_bytes()
    assert count_four_cliques(g)==record['exact_four_cliques']
    spec = next(s for _,c in future_configs(MANIFEST) for s in c['graphs'] if s['id']==record['id'])
    monkeypatch.chdir(path.parent)  # Project-relative resolution must not depend on cwd.
    assert experiments.experiment_graph(spec)==load_prepared_graph(spec)==load_edge_list(path)==g
    seen=[]
    class ReachedPrivateBoundary(Exception): pass
    def capture(graph,*args,**kwargs):
        seen.append(graph)
        raise ReachedPrivateBoundary
    monkeypatch.setattr(experiments,'simulate_baseline',capture)
    monkeypatch.setattr(experiments,'simulate_four_cliques',capture)
    for method in ({'kind':'baseline'},{'kind':'oriented','ordering':'kcore','cap_mode':'noisy'}):
        with pytest.raises(ReachedPrivateBoundary):
            experiments.execute_trial(g,1,method,123,{'beta':.05,'kcore':{}})
    assert seen[0] is seen[1] is g  # Neither backend sampled a privacy trial.


@pytest.mark.parametrize('spec',list(synthetic_specs()),ids=lambda s:s['id'])
def test_synthetic_generator_seeds_and_published_parameters(spec):
    n=int(spec['id'][-3:])
    seed=spec['seed']
    if spec['family']=='barabasi_albert':
        assert seed==130100+n and spec['parameters']=={'n':n,'m':n//5,'initial_graph':None}
        independent=nx.barabasi_albert_graph(n,n//5,seed=seed)
        assert independent.number_of_edges()==(n//5)*(n-n//5)
    else:
        assert seed==130200+n
        assert spec['parameters']=={'sizes':[n//2,n//2],'p':[[.25,.05],[.05,.25]],'directed':False,'selfloops':False,'sparse':True}
        independent=nx.stochastic_block_model([n//2,n//2],[[.25,.05],[.05,.25]],seed=seed)
    first=normalize_graph(generate_synthetic(spec))[0]
    assert first==normalize_graph(independent)[0]==normalize_graph(generate_synthetic(spec))[0]
    assert canonical_bytes(first)==(PROCESSED/f"baseline_2025/{spec['id']}.edges").read_bytes()


@pytest.mark.parametrize('name,function,n,m',[
    ('karate',nx.karate_club_graph,34,78),('les_miserables',nx.les_miserables_graph,77,254)])
def test_builtin_real_world_sources_and_original_mapping(name,function,n,m):
    source=function()
    g,mapping,_=normalize_graph(source)
    assert (g.num_vertices,g.num_edges)==(n,m)
    assert canonical_bytes(g)==(PROCESSED/f'real_world/{name}.edges').read_bytes()
    assert json_bytes(mapping)==(PROCESSED/f'real_world/{name}.mapping.json').read_bytes()


def test_matrix_market_coordinates_isolates_weights_loops_duplicates():
    graph,stats=parse_matrix_market('%%MatrixMarket matrix coordinate real general\n% comment\n5 5 4\n1 2 9.3\n2 1 4\n3 3 2\n4 2 1\n')
    result,mapping,_=normalize_graph(graph)
    assert result.num_vertices==5 and result.num_edges==2 and not result.adjacency[4]
    assert stats['self_loops_removed']==1 and stats['duplicate_or_reverse_records_removed']==1
    assert mapping[0]=={'original_id':1,'processed_id':0}
    for text in ['bad','%%MatrixMarket matrix coordinate pattern symmetric\n2 2 2\n1 2\n',
                 '%%MatrixMarket matrix coordinate pattern symmetric\n2 2 1\n1 3\n']:
        with pytest.raises(ValueError): parse_matrix_market(text)


def test_friendship_and_multigraph_normalization_preserve_isolates():
    graph,stats=parse_friendship_edges(['# comment','9 2','2 9','7 7'])
    assert set(graph)=={2,7,9} and graph.number_of_edges()==1
    assert stats['self_loops_removed']==stats['duplicate_or_reverse_records_removed']==1
    multi=nx.MultiDiGraph();multi.add_nodes_from([4,2,1,3])
    multi.add_edges_from([(1,2),(2,1),(1,2),(3,3)])
    result,mapping,changes=normalize_graph(multi)
    assert result.num_vertices==4 and result.num_edges==1
    assert changes['self_loops_removed']==1 and changes['duplicate_or_reverse_edges_removed']==2
    assert result.adjacency[2]==result.adjacency[3]==frozenset()
    assert [r['original_id'] for r in mapping]==[1,2,3,4]
    with pytest.raises(ValueError): parse_friendship_edges(['0 1 2'])


def test_bfs_induced_selection_is_insertion_order_independent_and_has_no_retry():
    source=nx.complete_graph(7)
    source.add_edge(100,101)
    reverse=nx.Graph();reverse.add_nodes_from(reversed(list(source)));reverse.add_edges_from(reversed(list(source.edges())))
    a,meta=sample_connected_induced(source,size=4,seed=130050)
    b,other=sample_connected_induced(reverse,size=4,seed=130050)
    assert meta==other and set(a.edges())==set(b.edges())
    assert meta['initial_original_vertex']==random.Random(130050).choice(list(range(7)))
    assert a.number_of_edges()==6  # An induced K4, not only three BFS tree edges.
    assert nx.is_connected(a) and set(a)==set(meta['discovery_order'])
    assert set(frozenset(e) for e in a.edges())=={frozenset(e) for e in source.edges() if set(e)<=set(a)}
    with pytest.raises(ValueError,match='no disconnected fallback'):
        sample_connected_induced(nx.disjoint_union(nx.path_graph(3),nx.path_graph(3)),size=4)


def test_manifest_verification_and_hash_corruption(tmp_path):
    assert verify_datasets(PROCESSED)['graphs']==6
    target=tmp_path/'copy';shutil.copytree(PROCESSED,target)
    path=target/RECORDS[0]['path']
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='hash mismatch'): verify_datasets(target)
    with pytest.raises(ValueError,match='canonical'): load_canonical_graph(path)
    before=path.read_bytes()
    with pytest.raises(ValueError,match='existing file differs'): write_identical_or_new(path,b'changed')
    assert path.read_bytes()==before
    write_identical_or_new(path,before)


def test_archive_pins_and_load_spec_fail_closed(tmp_path):
    with pytest.raises(FileNotFoundError): obtain_archive(tmp_path,'dolphins.zip',download=False)
    (tmp_path/'dolphins.zip').write_bytes(b'corruption')
    with pytest.raises(ValueError,match='hash mismatch'): obtain_archive(tmp_path,'dolphins.zip',download=False)
    config=next(future_configs(MANIFEST))[1]
    spec=dict(config['graphs'][0],sha256='0'*64)
    with pytest.raises(ValueError,match='hash mismatch'): load_prepared_graph(spec)
    spec['path']='../outside'
    with pytest.raises(ValueError,match='project-relative'): load_prepared_graph(spec)


def test_future_config_compatibility_same_budget_and_disjoint_random_seeds():
    all_seeds=set()
    for filename,expected in future_configs(MANIFEST):
        config=experiments.load_config(PROJECT/'experiments/configs'/filename)
        assert config==expected and config['trials']==200
        assert config['epsilons']==[.5,1,2,4]
        for gi,spec in enumerate(config['graphs']):
            graph=experiments.experiment_graph(spec)
            assert graph.num_vertices<=100
            for ei,epsilon in enumerate(config['epsilons']):
                budget=allocate_budget(epsilon,'kcore','noisy')
                assert (budget.ordering,budget.cap,budget.rr,budget.count)==(epsilon/4,)*4
                assert config['methods']==[{'id':'kcore_noisy_cap','kind':'oriented','ordering':'kcore','cap_mode':'noisy'}]
                for mi in range(1):
                    for trial in range(config['trials']):
                        seed=experiments.trial_seed(config['master_seed'],gi,ei,mi,trial)
                        assert seed not in all_seeds
                        all_seeds.add(seed)
    assert len(all_seeds)==6*4*200  # Coordinates only; no estimates generated.
    assert len({s['seed'] for s in synthetic_specs()})==2
    assert BRIGHTKITE_SEED not in {s['seed'] for s in synthetic_specs()}


@pytest.mark.escape_integration
@pytest.mark.parametrize('record',RECORDS,ids=lambda r:r['id'])
def test_all_prepared_datasets_against_real_escape_and_bruteforce(escape_adapter,record):
    graph=load_canonical_graph(PROCESSED/record['path'])
    native=escape_adapter.run(graph)
    assert native.counts.connected_four['4-clique']==count_four_cliques_bruteforce(graph)==count_four_cliques(graph)==record['exact_four_cliques']
    assert native.input_text.encode('ascii')==canonical_bytes(graph)
