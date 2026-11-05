"""NON-PRIVATE Phase 4A fixture/synthetic evaluation, artifact integrity and replay.

Mechanism-only JSONL is separate from seeded exact diagnostics. The complete
experiment is NOT a private release, even though it stores modeled releases.
"""

from dataclasses import asdict
import json
import math
from pathlib import Path
import re
import time

import numpy as np
import pandas as pd

from private_graphlets.experiments import generate_graph, sha256, _provenance
from private_graphlets.four_clique_experiments import trial_seed
from private_graphlets.four_path import FourPathBudget, simulate_four_paths_private
from private_graphlets.four_path_accuracy import (
    ConditionalMSE, conditional_four_path_mse, sample_order_cap, summarize_predictions,
)
from private_graphlets.four_path_exact import count_four_paths
from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.kcore import KCoreConfig
from private_graphlets.triangle_exact import count_triangles


PROJECT = Path(__file__).resolve().parents[2]


def experiment_graph(spec: dict) -> SimpleGraph:
    if spec.get('family') == 'fixture':
        if set(spec) != {'id', 'family', 'name'} or spec['name'] not in {
            'path', 'cycle', 'diamond', 'clique', 'clique_with_isolates', 'star', 'edgeless', 'tailed_triangle'}:
            raise ValueError('unknown fixture or fixture keys')
        graph = load_edge_list(PROJECT/'data/fixtures'/f"{spec['name']}.edges")
    else:
        graph = generate_graph(spec)
    if graph.num_vertices > 30:
        raise ValueError('Phase 4A validation is restricted to n<=30')
    return graph


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text())
    keys = {'schema_version', 'experiment_id', 'master_seed', 'trials', 'prediction_trials',
            'budget', 'beta', 'kcore', 'graphs', 'uncertainty_multiplier', 'max_relative_se'}
    if not isinstance(config, dict) or set(config) != keys or config['schema_version'] != 1:
        raise ValueError('invalid Phase 4A config schema')
    for key in ('trials', 'prediction_trials'):
        if type(config[key]) is not int or not 2 <= config[key] <= 500:
            raise ValueError('Phase 4A requires 2..500 trials per stream')
    if type(config['master_seed']) is not int or config['master_seed'] < 0:
        raise ValueError('master_seed must be a nonnegative integer')
    if not isinstance(config['experiment_id'], str) or not re.fullmatch(r'[A-Za-z0-9_-]+', config['experiment_id']):
        raise ValueError('unsafe experiment ID')
    FourPathBudget(**config['budget'])
    KCoreConfig(**config['kcore'])
    for key in ('beta', 'max_relative_se', 'uncertainty_multiplier'):
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f'invalid {key}')
    if config['beta'] >= 1 or config['max_relative_se'] >= 1:
        raise ValueError('beta and max_relative_se must be below one')
    graphs = config['graphs']
    if not isinstance(graphs, list) or not 1 <= len(graphs) <= 10:
        raise ValueError('Phase 4A requires 1..10 small graphs')
    ids = [spec['id'] for spec in graphs]
    if len(set(ids)) != len(ids) or any(not isinstance(x, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', x) for x in ids):
        raise ValueError('graph IDs must be unique safe names')
    for spec in graphs:
        experiment_graph(spec)
    return config


def experiment_seed(master: int, graph_index: int, stream: str, trial: int) -> int:
    """Reuse existing injective coordinate seeds; prediction/full have disjoint domains."""
    if stream not in ('prediction', 'full'):
        raise ValueError('unknown experiment stream')
    return trial_seed(master, graph_index, 0 if stream == 'prediction' else 1, 0, trial)


def prediction_trial(graph: SimpleGraph, budget: FourPathBudget, seed: int, config: dict):
    start = time.perf_counter()
    order, cap = sample_order_cap(graph, budget, seed=seed, beta=config['beta'],
                                 kcore_config=KCoreConfig(**config['kcore']))
    sample_seconds = time.perf_counter()-start
    start = time.perf_counter()
    result = conditional_four_path_mse(graph, budget, order, cap)
    return result, order, sample_seconds, time.perf_counter()-start


def full_trial(graph: SimpleGraph, budget: FourPathBudget, seed: int, config: dict):
    start = time.perf_counter()
    run = simulate_four_paths_private(graph, budget=budget, seed=seed, beta=config['beta'],
                                      kcore_config=KCoreConfig(**config['kcore']))
    mechanism_seconds = time.perf_counter()-start
    start = time.perf_counter()
    diagnostics = conditional_four_path_mse(graph, budget, run.transcript.order, run.transcript.cap)
    release = {'result': run.result.to_dict(), 'transcript': asdict(run.transcript)}
    return release, diagnostics, mechanism_seconds, time.perf_counter()-start


def aggregate(full: pd.DataFrame, prediction: pd.DataFrame, graphs: dict, config: dict) -> pd.DataFrame:
    rows = []
    for spec in config['graphs']:
        name = spec['id']
        cell = full[full.graph == name]
        pc = prediction[prediction.graph == name]
        truth = graphs[name]['exact_four_paths']
        estimates = cell.estimate.to_numpy(dtype=float)
        with np.errstate(over='raise', invalid='raise'):
            errors = estimates-truth
            squared = errors**2
            empirical = float(squared.mean())
            se = float(squared.std(ddof=1)/math.sqrt(len(squared)))
        predicted = summarize_predictions([ConditionalMSE(**{key: row[key] for key in ConditionalMSE.__dataclass_fields__})
                                           for row in pc.to_dict('records')])
        pmse = predicted['predicted_mse']
        combined = math.hypot(se, predicted['prediction_se'])
        discrepancy = empirical-pmse
        relative = discrepancy/pmse if pmse else 0.0 if not empirical else None
        precise = pmse > 0 and combined/pmse <= config['max_relative_se']
        within = abs(discrepancy) <= config['uncertainty_multiplier']*combined
        conclusion = ('discrepancy_detected' if not within else
                      'inconclusive_precision' if not precise else 'no_discrepancy_detected')
        row = {'graph': name, **graphs[name], 'trials': len(cell),
               'mean_estimate': float(estimates.mean()), 'empirical_bias': float(errors.mean()),
               'empirical_variance': float(estimates.var(ddof=1)), 'empirical_mse': empirical,
               'empirical_rmse': math.sqrt(empirical), 'se_mse': se,
               **{k: v for k, v in predicted.items() if k != 'result_type'},
               'mse_discrepancy': discrepancy, 'combined_se': combined,
               'relative_discrepancy': relative,
               'within_predeclared_tolerance': within, 'precision_adequate': precise,
               'conclusion': conclusion,
               'full_mean_missed_triangles': float(cell.missed_triangles.mean()),
               'full_truncation_frequency': float((cell.missed_triangles > 0).mean()),
               'mechanism_seconds': float(cell.mechanism_seconds.sum()),
               'full_diagnostic_seconds': float(cell.diagnostic_seconds.sum()),
               'prediction_sampling_seconds': float(pc.sampling_seconds.sum()),
               'prediction_analytical_seconds': float(pc.analytical_seconds.sum())}
        if any(isinstance(value, (float, np.floating)) and not math.isfinite(value) for value in row.values()):
            raise FloatingPointError('nonfinite experiment metric')
        rows.append(row)
    return pd.DataFrame(rows)


def _read_csv(path):
    return pd.read_csv(path, dtype={'seed': str}, float_precision='round_trip')


def _write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')


def _graph_text(graph):
    return '\n'.join([f'{graph.num_vertices} {graph.num_edges}',
                      *(f'{u} {v}' for u, row in enumerate(graph.adjacency) for v in sorted(row) if u < v)])+'\n'


def run_experiment(config_path: Path, output: Path) -> dict:
    return _run_experiment(load_config(config_path), output, experiment_graph)


def _run_experiment(config: dict, output: Path, graph_factory) -> dict:
    """Shared engine; callers must validate their own phase-specific config."""
    budget = FourPathBudget(**config['budget'])
    output.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    try:
        (output/'graphs').mkdir()
        (output/'mechanism_outputs').mkdir()
        _write_json(output/'config.json', config)
        full, prediction, graph_info = [], [], {}
        for gi, spec in enumerate(config['graphs']):
            graph = graph_factory(spec)
            name = spec['id']
            (output/'graphs'/f'{name}.edges').write_text(_graph_text(graph))
            graph_info[name] = {'n': graph.num_vertices, 'm': graph.num_edges,
                                'exact_four_paths': count_four_paths(graph),
                                'exact_triangles': count_triangles(graph)}
            for trial in range(config['prediction_trials']):
                seed = experiment_seed(config['master_seed'], gi, 'prediction', trial)
                result, order, sample_time, analytic_time = prediction_trial(graph, budget, seed, config)
                prediction.append({'graph': name, 'graph_index': gi, 'trial': trial, 'seed': str(seed),
                                   'order': json.dumps(order), **asdict(result),
                                   'sampling_seconds': sample_time, 'analytical_seconds': analytic_time})
            with (output/'mechanism_outputs'/f'{name}.jsonl').open('w') as stream:
                for trial in range(config['trials']):
                    seed = experiment_seed(config['master_seed'], gi, 'full', trial)
                    release, diagnostic, elapsed, diagnostic_time = full_trial(graph, budget, seed, config)
                    stream.write(json.dumps(release, allow_nan=False)+'\n')
                    full.append({'graph': name, 'graph_index': gi, 'trial': trial, 'seed': str(seed),
                                 'estimate': release['result']['estimate'],
                                 'retained_triangles': diagnostic.retained_triangles,
                                 'missed_triangles': diagnostic.missed_triangles,
                                 'mechanism_seconds': elapsed, 'diagnostic_seconds': diagnostic_time})
        _write_json(output/'graph_evaluation.json', graph_info)
        pd.DataFrame(full).to_csv(output/'evaluation_trials.csv', index=False, float_format='%.17g')
        pd.DataFrame(prediction).to_csv(output/'prediction_trials.csv', index=False, float_format='%.17g')
        aggregate(_read_csv(output/'evaluation_trials.csv'), _read_csv(output/'prediction_trials.csv'),
                  graph_info, config).to_csv(output/'summary.csv', index=False, float_format='%.17g')
        provenance = _provenance()
        provenance['source_sha256']['scripts/run_four_path_experiments.py'] = sha256(PROJECT/'scripts/run_four_path_experiments.py')
        manifest = {'status': 'complete', 'result_type': 'nonprivate_synthetic_evaluation',
                    'experiment_id': config['experiment_id'], 'graphs': len(graph_info),
                    'full_trials': len(full), 'prediction_trials': len(prediction),
                    'pipeline_seconds': time.perf_counter()-start, 'provenance': provenance,
                    'reference_manifest_sha256': sha256(PROJECT/'third_party/references.json'),
                    'schemas': {'mechanism_outputs': 'modeled private result/transcript ONLY; no seeds or exact diagnostics',
                                'evaluation_trials.csv': 'NON-PRIVATE seeded evaluation diagnostics',
                                'prediction_trials.csv': 'NON-PRIVATE conditional analytical predictions',
                                'graph_evaluation.json': 'NON-PRIVATE exact graph counts',
                                'summary.csv': 'NON-PRIVATE evaluation metrics'},
                    'files_sha256': {str(p.relative_to(output)): sha256(p)
                                     for p in sorted(output.rglob('*')) if p.is_file()}}
        _write_json(output/'manifest.json', manifest)
        return manifest
    except Exception as exc:
        _write_json(output/'failure.json', {'status': 'failed', 'error': str(exc)})
        raise


def verify_results(output: Path, *, replay: bool = False) -> dict:
    return _verify_results(output, load_config, experiment_graph, replay=replay)


def _verify_results(output: Path, config_loader, graph_factory, *, replay: bool = False) -> dict:
    """Shared integrity/replay engine with phase-specific validation."""
    manifest = json.loads((output/'manifest.json').read_text())
    if manifest['status'] != 'complete' or (output/'failure.json').exists():
        raise ValueError('incomplete/failed experiment')
    actual_files = {str(p.relative_to(output)) for p in output.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    if set(manifest['files_sha256']) != actual_files:
        raise ValueError('artifact inventory mismatch')
    for name, digest in manifest['files_sha256'].items():
        if sha256(output/name) != digest:
            raise ValueError(f'hash mismatch: {name}')
    config = config_loader(output/'config.json')
    info = json.loads((output/'graph_evaluation.json').read_text())
    full = _read_csv(output/'evaluation_trials.csv')
    prediction = _read_csv(output/'prediction_trials.csv')
    summary = pd.read_csv(output/'summary.csv', float_precision='round_trip')
    budget = FourPathBudget(**config['budget'])
    for data, domain, count in ((full, 'full', config['trials']), (prediction, 'prediction', config['prediction_trials'])):
        expected = [(s['id'], gi, ti, str(experiment_seed(config['master_seed'], gi, domain, ti)))
                    for gi, s in enumerate(config['graphs']) for ti in range(count)]
        if list(data[['graph', 'graph_index', 'trial', 'seed']].itertuples(index=False, name=None)) != expected:
            raise ValueError('trial coordinates/seed mismatch')
    if set(full.seed) & set(prediction.seed):
        raise ValueError('prediction/full seed domains overlap')
    pd.testing.assert_frame_equal(summary, aggregate(full, prediction, info, config),
                                  check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)
    for gi, spec in enumerate(config['graphs']):
        name = spec['id']
        graph = load_edge_list(output/'graphs'/f'{name}.edges')
        if graph != graph_factory(spec):
            raise ValueError('saved graph differs from configuration')
        expected_info = {'n': graph.num_vertices, 'm': graph.num_edges,
                         'exact_four_paths': count_four_paths(graph), 'exact_triangles': count_triangles(graph)}
        if info[name] != expected_info:
            raise ValueError('exact graph evaluation mismatch')
        rows = full[full.graph == name].to_dict('records')
        with (output/'mechanism_outputs'/f'{name}.jsonl').open() as stream:
            for row in rows:
                line = stream.readline()
                if not line:
                    raise ValueError('mechanism record count mismatch')
                release = json.loads(line)
                if release['result']['estimate'] != row['estimate']:
                    raise ValueError('mechanism/evaluation estimate mismatch')
                t = release['transcript']
                diagnostics = conditional_four_path_mse(graph, budget, t['order'], t['cap'])
                if diagnostics.missed_triangles != row['missed_triangles'] or diagnostics.retained_triangles != row['retained_triangles']:
                    raise ValueError('full diagnostic mismatch')
                if replay:
                    actual, _, _, _ = full_trial(graph, budget, int(row['seed']), config)
                    if json.loads(json.dumps(actual)) != release:
                        raise ValueError('full mechanism replay mismatch')
            if stream.readline():
                raise ValueError('mechanism record count mismatch')
        for row in prediction[prediction.graph == name].to_dict('records'):
            order = json.loads(row['order'])
            actual = conditional_four_path_mse(graph, budget, order, int(row['cap']))
            for key, value in asdict(actual).items():
                if value != row[key]:
                    raise ValueError(f'prediction analytical mismatch: {key}')
            if replay:
                sampled, cap = sample_order_cap(graph, budget, seed=int(row['seed']), beta=config['beta'],
                                                kcore_config=KCoreConfig(**config['kcore']))
                if list(sampled) != order or cap != row['cap']:
                    raise ValueError('prediction history replay mismatch')
    return {'status': 'verified', 'graphs': len(info), 'full_trials': len(full),
            'prediction_trials': len(prediction), 'replayed': replay}
