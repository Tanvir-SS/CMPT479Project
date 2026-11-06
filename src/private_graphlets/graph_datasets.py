"""Deterministic NON-PRIVATE benchmark preparation; no privacy mechanisms run here."""

from collections import deque
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import urllib.request
import zipfile

import networkx as nx

from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.four_clique_exact import count_four_cliques, count_four_cliques_bruteforce
from private_graphlets.escape import parse_count_four_output

PROJECT = Path(__file__).resolve().parents[2]
NETWORKX_VERSION = '3.4.2'
BRIGHTKITE_SEED = 130050
BASELINE_PIN = '85eff6efa2b1d649ee238620a998ec7f1d305aac'
ESCAPE_PIN = '7ec2f93c524a0b47cdc8c639602e90d1c1fceff3'
RAW_SOURCES = {
    'dolphins.zip': {
        'url': 'https://nrvis.com/download/data/misc/dolphins.zip',
        'page': 'https://networkrepository.com/dolphins.php',
        'sha256': '9d34947ed4ac929e2f38e542f1a59efd364be2d0b1c624fe2de65826fc7ecdc3',
        'snapshot_date_utc': '2026-11-06',
    },
    'loc-brightkite_edges.txt.gz': {
        'url': 'https://snap.stanford.edu/data/loc-brightkite_edges.txt.gz',
        'page': 'https://snap.stanford.edu/data/loc-Brightkite.html',
        'sha256': '0714a1ff54225f49fae8bd228d807e6a2a7ee27b8ff3c60989cfd9d20089a229',
        'snapshot_date_utc': '2026-11-06',
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def write_identical_or_new(path: Path, content: bytes) -> None:
    """Idempotent; do not silently replace an existing different dataset/artifact."""
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f'existing file differs; preserve it and choose a new output root: {path}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def obtain_archive(raw_dir: Path, name: str, *, download: bool) -> Path:
    source = RAW_SOURCES[name]
    path = raw_dir/name
    if not path.exists():
        if not download:
            raise FileNotFoundError(f'{path} missing; use prepare --download or provide the pinned raw archive')
        raw_dir.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(source['url'], timeout=60) as response:
            blob = response.read(20_000_001)
        if len(blob)>20_000_000 or hashlib.sha256(blob).hexdigest()!=source['sha256']:
            raise ValueError(f'archive download does not match pinned content: {name}')
        write_identical_or_new(path, blob)
        metadata = {'url':source['url'], 'sha256':source['sha256'], 'bytes':len(blob),
                    'downloaded_at_utc':datetime.now(timezone.utc).isoformat()}
        write_identical_or_new(raw_dir/(name+'.download.json'), json_bytes(metadata))
    if digest(path)!=source['sha256']:
        raise ValueError(f'raw archive hash mismatch: {path}')
    return path


def parse_matrix_market(text: str) -> tuple[nx.Graph, dict]:
    """Coordinate matrix; preserve declared isolates, discard loops/weights/direction."""
    lines = iter(text.splitlines())
    header = next(lines, '').lower().split()
    if (len(header)!=5 or header[:3]!=['%%matrixmarket','matrix','coordinate']
            or header[3] not in {'pattern','integer','real'} or header[4] not in {'symmetric','general'}):
        raise ValueError('unsupported Matrix Market coordinate header')
    records = (line.split() for line in lines if line.strip() and not line.lstrip().startswith('%'))
    try:
        dimensions = next(records)
        if len(dimensions)!=3: raise ValueError('invalid dimensions')
        n, cols, expected = map(int, dimensions)
    except (StopIteration, ValueError) as exc:
        raise ValueError('missing/invalid Matrix Market dimensions') from exc
    if n<0 or cols!=n or expected<0: raise ValueError('expected nonnegative square matrix')
    graph = nx.Graph()
    graph.add_nodes_from(range(1,n+1))
    rows = loops = duplicates = 0
    for fields in records:
        if len(fields)!=(2 if header[3]=='pattern' else 3):
            raise ValueError('invalid Matrix Market record')
        u,v = map(int,fields[:2])
        if not (1<=u<=n and 1<=v<=n): raise ValueError('Matrix Market index out of range')
        rows += 1
        if u==v: loops += 1; continue
        if graph.has_edge(u,v): duplicates += 1
        graph.add_edge(u,v)
    if rows!=expected: raise ValueError('Matrix Market record count mismatch')
    return graph, {'declared_vertices':n, 'declared_records':expected, 'edge_records':rows,
                   'self_loops_removed':loops, 'duplicate_or_reverse_records_removed':duplicates,
                   'matrix_field':header[3], 'matrix_symmetry':header[4]}


def parse_friendship_edges(lines) -> tuple[nx.Graph, dict]:
    graph = nx.Graph()
    rows = loops = duplicates = 0
    for line in lines:
        fields = line.partition('#')[0].split()
        if not fields: continue
        if len(fields)!=2: raise ValueError('friendship edge list requires exactly two IDs')
        u,v = map(int,fields)
        if u<0 or v<0: raise ValueError('friendship IDs must be nonnegative')
        graph.add_nodes_from((u,v))
        rows += 1
        if u==v: loops += 1; continue
        if graph.has_edge(u,v): duplicates += 1
        graph.add_edge(u,v)
    return graph, {'edge_records':rows, 'self_loops_removed':loops,
                   'duplicate_or_reverse_records_removed':duplicates,
                   'vertex_set':'all IDs observed in the original friendship file; no header-derived invented IDs'}


def normalize_graph(graph: nx.Graph) -> tuple[SimpleGraph, list[dict], dict]:
    """Sort numeric/string original IDs; explicitly remove loops and duplicate arcs."""
    nodes = list(graph.nodes())
    if any(type(v) not in (int,str) for v in nodes):
        raise ValueError('benchmark original IDs must be integer or string labels')
    nodes.sort(key=lambda v: (0,v) if type(v) is int else (1,v))
    mapping = {original:i for i,original in enumerate(nodes)}
    edges = set()
    loops = duplicates = 0
    for u,v in graph.edges():
        if u==v: loops += 1; continue
        edge = tuple(sorted((mapping[u],mapping[v])))
        if edge in edges: duplicates += 1
        edges.add(edge)
    simple = SimpleGraph.from_edges(len(nodes),sorted(edges))
    rows = [{'original_id':v,'processed_id':mapping[v]} for v in nodes]
    return simple, rows, {'self_loops_removed':loops,'duplicate_or_reverse_edges_removed':duplicates,
                         'directions_ignored':graph.is_directed(), 'edge_attributes_discarded':True}


def canonical_bytes(graph: SimpleGraph) -> bytes:
    lines = [f'{graph.num_vertices} {graph.num_edges}\n']
    lines.extend(f'{u} {v}\n' for u,row in enumerate(graph.adjacency) for v in sorted(row) if u<v)
    return ''.join(lines).encode('ascii')


def load_canonical_graph(path: Path) -> SimpleGraph:
    graph = load_edge_list(path)  # Existing validator unchanged.
    if path.read_bytes()!=canonical_bytes(graph):
        raise ValueError(f'not a canonical sorted, unique, loop-free edge file: {path}')
    return graph


def sample_connected_induced(graph: nx.Graph, size=50, seed=BRIGHTKITE_SEED):
    """Largest component, seeded start, sorted-neighbor FIFO BFS; then induce."""
    if type(size) is not int or size<1 or type(seed) is not int or seed<0:
        raise ValueError('positive integer sample size and nonnegative integer seed required')
    if graph.is_directed() or graph.is_multigraph() or nx.number_of_selfloops(graph):
        raise ValueError('sampling requires a simple undirected loop-free source')
    if any(type(v) is not int for v in graph): raise ValueError('sampling requires integer original IDs')
    components = sorted((sorted(c) for c in nx.connected_components(graph)),key=lambda c:(-len(c),c))
    if not components or len(components[0])<size:
        raise ValueError('largest component has fewer than requested vertices; no disconnected fallback or fabricated edges')
    component = components[0]
    start = random.Random(seed).choice(component)
    discovered = [start]
    seen = {start}
    queue = deque([start])
    while queue and len(discovered)<size:
        vertex = queue.popleft()
        for neighbor in sorted(graph.neighbors(vertex)):
            if neighbor not in seen:
                seen.add(neighbor); discovered.append(neighbor); queue.append(neighbor)
                if len(discovered)==size: break
    if len(discovered)!=size: raise AssertionError('connected traversal did not fill sample')
    sampled = graph.subgraph(discovered).copy()  # ALL original edges on selected vertices.
    return sampled, {'seed':seed, 'rng':'random.Random (Python 3.11)', 'size':size,
        'component_rule':'largest connected component; ties by lexicographically sorted original integer IDs',
        'component_size':len(component), 'initial_original_vertex':start,
        'traversal':f'FIFO BFS; neighbors ascending original ID; mark on discovery; stop after {size} discoveries',
        'discovery_order':discovered, 'selected_original_vertices':sorted(discovered),
        'edge_rule':'induced subgraph AFTER vertex selection; keep every original selected-selected edge',
        'fallback':'fail if largest component too small; no restart, extra components, seed search or invented edges'}


def synthetic_specs():
    for family in ('ba','sbm'):
        for n in range(10,101,10):
            if family=='ba':
                yield {'id':f'ba_n{n:03d}','family':'barabasi_albert','generator':'networkx.barabasi_albert_graph',
                       'parameters':{'n':n,'m':n//5,'initial_graph':None},'seed':130100+n}
            else:
                yield {'id':f'sbm_n{n:03d}','family':'stochastic_block','generator':'networkx.stochastic_block_model',
                       'parameters':{'sizes':[n//2,n//2],'p':[[.25,.05],[.05,.25]],
                                     'directed':False,'selfloops':False,'sparse':True},'seed':130200+n}


def generate_synthetic(spec):
    if nx.__version__!=NETWORKX_VERSION:
        raise ValueError(f'regeneration requires pinned NetworkX {NETWORKX_VERSION}')
    functions = {'networkx.barabasi_albert_graph':nx.barabasi_albert_graph,
                 'networkx.stochastic_block_model':nx.stochastic_block_model}
    return functions[spec['generator']](**spec['parameters'], seed=spec['seed'])


def source_graphs(raw_dir: Path, *, download=False):
    """Yield input graph and stable provenance, never an estimator output."""
    if nx.__version__!=NETWORKX_VERSION: raise ValueError(f'requires NetworkX {NETWORKX_VERSION}')
    for name,function in [('karate',nx.karate_club_graph),('les_miserables',nx.les_miserables_graph)]:
        yield function(), {'id':name,'suite':'real_world','family':'social_network',
            'source':{'generator':f'networkx.{function.__name__}','networkx_version':nx.__version__},
            'parameters':{},'seed':None}
    path = obtain_archive(raw_dir,'dolphins.zip',download=download)
    with zipfile.ZipFile(path) as archive:
        graph, stats = parse_matrix_market(archive.read('dolphins.mtx').decode('utf-8'))
    if (len(graph),graph.number_of_edges())!=(62,159): raise ValueError('unexpected original Dolphins dimensions')
    yield graph, {'id':'dolphins','suite':'real_world','family':'social_network',
        'source':{**RAW_SOURCES[path.name],'archive':path.name,'member':'dolphins.mtx'},
        'parameters':{},'seed':None,'raw_parsing':stats}
    path = obtain_archive(raw_dir,'loc-brightkite_edges.txt.gz',download=download)
    with gzip.open(path,'rt',encoding='ascii') as stream: graph, stats = parse_friendship_edges(stream)
    if (len(graph),graph.number_of_edges())!=(58228,214078): raise ValueError('unexpected Brightkite friendship dimensions')
    sampled, selection = sample_connected_induced(graph)
    yield sampled, {'id':'brightkite_50','suite':'real_world','family':'induced_social_subgraph',
        'source':{**RAW_SOURCES[path.name],'archive':path.name},'parameters':{'sample_vertices':50},
        'seed':BRIGHTKITE_SEED,'raw_parsing':stats,'selection':selection,
        'original_vertices':len(graph),'original_edges':graph.number_of_edges()}
    for spec in synthetic_specs():
        yield generate_synthetic(spec), {'id':spec['id'],'suite':'baseline_2025','family':spec['family'],
            'source':{'generator':spec['generator'],'networkx_version':nx.__version__,
                      'paper':'https://arxiv.org/pdf/2505.12954','section':'6.1', 'reference_commit':BASELINE_PIN},
            'parameters':spec['parameters'],'seed':spec['seed']}


def prepare_datasets(raw_dir: Path, output: Path, adapter, *, download=False):
    """Require real ESCAPE agreement and brute force for every graph before acceptance."""
    records, evidence = [], []
    build = json.loads((adapter.executable.parent/'build.json').read_text())
    # Validate all content before writing accepted files/manifest.
    pending = []
    for source_graph, record in source_graphs(raw_dir,download=download):
        graph, mapping, preprocessing = normalize_graph(source_graph)
        expected = {'karate':(34,78),'dolphins':(62,159),'les_miserables':(77,254)}.get(record['id'])
        if expected and (graph.num_vertices,graph.num_edges)!=expected: raise ValueError('source size changed')
        relative = f"{record['suite']}/{record['id']}.edges"
        mapping_relative = f"{record['suite']}/{record['id']}.mapping.json"
        content, mapping_content = canonical_bytes(graph), json_bytes(mapping)
        forward = count_four_cliques(graph)
        brute = count_four_cliques_bruteforce(graph)
        native = adapter.run(graph)
        observed = native.counts.connected_four['4-clique']
        if not forward==brute==observed: raise AssertionError(f"three-way exact mismatch: {record['id']}")
        record = {**record,'original_vertices':record.get('original_vertices',len(source_graph)),
            'original_edges':record.get('original_edges',source_graph.number_of_edges()),
            'processed_vertices':graph.num_vertices,'processed_edges':graph.num_edges,
            'connected_components':nx.number_connected_components(nx.Graph(source_graph)),
            'isolated_vertices':sum(not row for row in graph.adjacency),
            'path':relative,'sha256':hashlib.sha256(content).hexdigest(),
            'mapping_path':mapping_relative,'mapping_sha256':hashlib.sha256(mapping_content).hexdigest(),
            'preprocessing':preprocessing,'exact_four_cliques':forward,
            'validation':{'status':'agreed','oriented_count':forward,'bruteforce_count':brute,
                          'escape_count':observed,'escape_output':native.output_text},
            'baseline_four_sets_per_trial':math.comb(graph.num_vertices,4)}
        records.append(record)
        evidence.append({'id':record['id'],'input':native.input_text,'output':native.output_text,
                         'stdout':native.stdout,'stderr':native.stderr})
        pending.extend([(output/relative,content),(output/mapping_relative,mapping_content)])
    manifest = {'schema_version':1,'dataset_suite':'four_clique_benchmarks_13',
        'count_semantics':'non-induced unlabeled K4; four distinct vertices with all six edges',
        'networkx_version':nx.__version__,'python_major_minor':'3.11',
        'permission':'Project owner reports provider authorization for this academic repository; no new license assigned.',
        'escape_reference':{'expected_bundled_commit':ESCAPE_PIN,
                            'actual_source_sha256':build['source_sha256']},'graphs':records}
    pending.append((output/'graph_manifest.json',json_bytes(manifest)))
    # Check all conflicts first; leave previous data untouched on a mismatch.
    for path,content in pending:
        if path.exists() and path.read_bytes()!=content: raise ValueError(f'existing dataset differs: {path}')
    for path,content in pending: write_identical_or_new(path,content)
    return manifest,evidence


def verify_datasets(output: Path, adapter=None, *, brute_force=False):
    manifest = json.loads((output/'graph_manifest.json').read_text())
    expected_ids = {'karate','dolphins','les_miserables','brightkite_50'}|{s['id'] for s in synthetic_specs()}
    ids = [r['id'] for r in manifest['graphs']]
    if len(ids)!=24 or set(ids)!=expected_ids: raise ValueError('incomplete or duplicate dataset manifest')
    counts = []
    for record in manifest['graphs']:
        path, mapping_path = output/record['path'], output/record['mapping_path']
        if digest(path)!=record['sha256'] or digest(mapping_path)!=record['mapping_sha256']:
            raise ValueError(f"dataset or mapping hash mismatch: {record['id']}")
        graph = load_canonical_graph(path)
        if (graph.num_vertices,graph.num_edges)!=(record['processed_vertices'],record['processed_edges']):
            raise ValueError('dataset dimensions do not match manifest')
        mapping = json.loads(mapping_path.read_text())
        if ([r['processed_id'] for r in mapping]!=list(range(graph.num_vertices))
                or len({(type(r['original_id']).__name__,r['original_id']) for r in mapping})!=graph.num_vertices):
            raise ValueError('invalid vertex mapping')
        truth = count_four_cliques(graph)
        saved = parse_count_four_output(record['validation']['escape_output'],
                    num_vertices=graph.num_vertices,num_edges=graph.num_edges).connected_four['4-clique']
        if not truth==record['exact_four_cliques']==saved==record['validation']['escape_count']==record['validation']['bruteforce_count']:
            raise ValueError('saved exact counts disagree')
        if brute_force and count_four_cliques_bruteforce(graph)!=truth: raise ValueError('fresh brute force disagrees')
        if adapter is not None and adapter.run(graph).counts.connected_four['4-clique']!=truth:
            raise ValueError('fresh ESCAPE disagrees')
        counts.append({'id':record['id'],'n':graph.num_vertices,'m':graph.num_edges,'four_cliques':truth})
    return {'status':'verified','graphs':len(counts),'fresh_escape':adapter is not None,
            'fresh_bruteforce':brute_force,'counts':counts}


def load_prepared_graph(spec: dict, *, project_root: Path | None=None) -> SimpleGraph:
    """Hash-checked file input for existing experiment components, rooted at checkout."""
    root = PROJECT if project_root is None else Path(project_root)
    path = Path(spec['path'])
    if path.is_absolute() or '..' in path.parts: raise ValueError('dataset paths must be project-relative')
    path = root/path
    if digest(path)!=spec['sha256']: raise ValueError(f'dataset hash mismatch: {path}')
    graph = load_canonical_graph(path)
    if (graph.num_vertices,graph.num_edges)!=(spec['n'],spec['m']): raise ValueError('configured dataset size mismatch')
    return graph


def future_configs(manifest: dict):
    for suite,master in [('real_world',202611061301),('baseline_2025',202611061302)]:
        records = [r for r in manifest['graphs'] if r['suite']==suite]
        yield f'four_clique_{suite}.json', {
            'schema_version':1,'experiment_id':f'four_clique_{suite}','trials':100,'master_seed':master,
            'epsilons':[.5,1.,2.,4.],'beta':.05,
            'kcore':{'psi':.5,'threshold_fraction':.5,'bias_factor':1},
            'representative_graph':records[0]['id'],
            'methods':[{'id':'baseline','kind':'baseline'},
                       {'id':'kcore_noisy_cap','kind':'oriented','ordering':'kcore','cap_mode':'noisy'}],
            'evaluation':{'target':'original exact K4 count','ground_truth':'ESCAPE + independent brute force',
                'metrics':{'mse':'summary.rmse ** 2','rmse':'summary.rmse','bias':'summary.bias'},
                'seed_rule':'existing trial_seed(master, graph_index, epsilon_index, method_index, trial)',
                'status':'prepared_only; no private benchmark executed during dataset preparation'},
            'graphs':[{'id':r['id'],'family':'prepared_edge_list','source_family':r['family'],
                       'path':f"data/processed/{r['path']}",'sha256':r['sha256'],
                       'n':r['processed_vertices'],'m':r['processed_edges'],
                       'expected_four_cliques':r['exact_four_cliques']} for r in records]}
