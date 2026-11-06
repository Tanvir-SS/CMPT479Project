"""NON-PRIVATE Phase 4B study orchestration; unchanged five-stage mechanism.

Reuses Phase 4A trial, aggregation, artifact and replay engines. Configuration
limits here are independent of the preserved Phase 4A public entry points.
"""
from dataclasses import asdict
import json
import math
from pathlib import Path
import re
import resource
import sys
import time

import numpy as np
import pandas as pd

from private_graphlets.escape import EscapeAdapter, parse_count_four_output
from private_graphlets.experiments import generate_graph, sha256, _provenance
from private_graphlets.four_clique_experiments import trial_seed
from private_graphlets.four_path import FourPathBudget
from private_graphlets.four_path_accuracy import conditional_four_path_mse
from private_graphlets.four_path_exact import count_four_paths
from private_graphlets.triangle_exact import count_triangles
from private_graphlets.kcore import KCoreConfig
from private_graphlets import four_path_experiments as pilot

COMPONENTS = ['degree_noise', 'rr_unadjusted', 'shared_rr_adjustment',
              'triangle_laplace', 'truncation_squared_error']


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('unsafe identifier')
    return value


def study_graph(spec):
    if spec.get('family') not in ('erdos_renyi', 'barabasi_albert', 'complete'):
        raise ValueError('unsupported Phase 4B graph family')
    if type(spec.get('n')) is not int or not 4 <= spec['n'] <= 100:
        raise ValueError('Phase 4B requires 4<=n<=100')
    return generate_graph(spec)


def _common(config):
    for key, limit in [('trials', 1000), ('prediction_trials', 500)]:
        if type(config[key]) is not int or not 2 <= config[key] <= limit:
            raise ValueError(f'invalid {key}')
    if type(config['master_seed']) is not int or config['master_seed'] < 0:
        raise ValueError('invalid master_seed')
    _name(config['experiment_id'])
    KCoreConfig(**config['kcore'])
    for key in ['uncertainty_multiplier', 'max_relative_se']:
        v = config[key]
        if type(v) not in (int, float) or not math.isfinite(v) or v <= 0:
            raise ValueError(f'invalid {key}')
    if config['max_relative_se'] >= 1:
        raise ValueError('max_relative_se must be below one')


def _beta(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value < 1:
        raise ValueError('invalid beta')


def load_config(path: Path) -> dict:
    c = json.loads(path.read_text())
    keys = {'schema_version', 'experiment_id', 'master_seed', 'trials', 'prediction_trials',
            'kcore', 'uncertainty_multiplier', 'max_relative_se', 'graphs', 'cells', 'controls'}
    if not isinstance(c, dict) or set(c) != keys or c['schema_version'] != 13:
        raise ValueError('invalid Phase 4B schema')
    _common(c)
    if not 1 <= len(c['graphs']) <= 16 or not 1 <= len(c['cells']) <= 40:
        raise ValueError('study exceeds graph/cell limits')
    ids = [_name(g['id']) for g in c['graphs']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate graph')
    graphs = {g['id']: study_graph(g) for g in c['graphs']}
    names = []
    for cell in c['cells']:
        if set(cell) != {'id', 'experiment', 'graph', 'allocation', 'budget', 'beta'}:
            raise ValueError('invalid cell keys')
        names.append(_name(cell['id']))
        _name(cell['allocation'])
        if cell['experiment'] not in ('A', 'B', 'C', 'D2') or cell['graph'] not in graphs:
            raise ValueError('invalid experiment or graph')
        FourPathBudget(**cell['budget'])
        _beta(cell['beta'])
    if len(names) != len(set(names)):
        raise ValueError('duplicate cell')
    if not isinstance(c['controls'], list) or not 1 <= len(c['controls']) <= 20:
        raise ValueError('invalid controls')
    controls(c)  # Validate order/cap/budget with the existing analytical API.
    return c


def controls(config):
    rows = []
    for spec in config['controls']:
        if set(spec) != {'id', 'n', 'order', 'cap', 'budget'}:
            raise ValueError('invalid control keys')
        _name(spec['id'])
        graph = study_graph({'id': spec['id'], 'family': 'complete', 'n': spec['n']})
        result = conditional_four_path_mse(graph, FourPathBudget(**spec['budget']), spec['order'], spec['cap'])
        rows.append({'control': spec['id'], 'n': spec['n'], 'order': json.dumps(spec['order']),
                     'scope': 'NON_PRIVATE_FIXED_HISTORY_NOT_FULL_PROTOCOL', **asdict(result)})
    if len({r['control'] for r in rows}) != len(rows):
        raise ValueError('duplicate control')
    return pd.DataFrame(rows)


def cell_config(config, index):
    cell = config['cells'][index]
    return {'schema_version': 13, 'experiment_id': cell['id'],
            'master_seed': trial_seed(config['master_seed'], index, 13, 0, 0),
            **{k: config[k] for k in ('trials', 'prediction_trials', 'kcore',
                                      'uncertainty_multiplier', 'max_relative_se')},
            'budget': cell['budget'], 'beta': cell['beta'],
            'graphs': [next(g for g in config['graphs'] if g['id'] == cell['graph'])]}


def _load_cell(path):
    c = json.loads(path.read_text())
    keys = {'schema_version', 'experiment_id', 'master_seed', 'trials', 'prediction_trials',
            'budget', 'beta', 'kcore', 'graphs', 'uncertainty_multiplier', 'max_relative_se'}
    if set(c) != keys or c['schema_version'] != 13 or len(c['graphs']) != 1:
        raise ValueError('invalid Phase 4B cell schema')
    _common(c)
    FourPathBudget(**c['budget'])
    _beta(c['beta'])
    study_graph(c['graphs'][0])
    return c


def workload(config):
    return {'graphs': len(config['graphs']), 'cells': len(config['cells']),
            'full_trials': len(config['cells'])*config['trials'],
            'prediction_histories': len(config['cells'])*config['prediction_trials'],
            'largest_n': max(g['n'] for g in config['graphs']),
            'memory_model': 'one streamed transcript plus per-cell trial/history data; O(n^2+nr+F+Pn)'}


def summarize_cell(directory, cell, graph):
    row = pd.read_csv(directory/'summary.csv', float_precision='round_trip').iloc[0].to_dict()
    full = pilot._read_csv(directory/'evaluation_trials.csv')
    pred = pilot._read_csv(directory/'prediction_trials.csv')
    truth = row['exact_four_paths']
    rmse = row['empirical_rmse']
    row.update(cell=cell['id'], experiment=cell['experiment'], allocation=cell['allocation'],
               epsilon=FourPathBudget(**cell['budget']).total, beta=cell['beta'],
               maximum_degree=max(map(len, graph.adjacency), default=0),
               relative_rmse=rmse/truth if truth else float("nan"),
               relative_rmse_defined=bool(truth),
               rmse_se=row['se_mse']/(2*rmse) if rmse else 0.,
               full_mean_squared_missed=float((full.missed_triangles**2).mean()),
               full_truncation_bias=3*float(full.missed_triangles.mean()),
               prediction_mean_squared_missed=float((pred.missed_triangles**2).mean()),
               mechanism_mean_seconds=float(full.mechanism_seconds.mean()),
               mechanism_median_seconds=float(full.mechanism_seconds.median()),
               analytical_mean_seconds=float(pred.analytical_seconds.mean()),
               analytical_median_seconds=float(pred.analytical_seconds.median()),
               prediction_sampling_mean_seconds=float(pred.sampling_seconds.mean()),
               prediction_sampling_median_seconds=float(pred.sampling_seconds.median()))
    row.update({f'epsilon_{k}': v for k, v in cell['budget'].items()})
    total = math.fsum(row['mean_'+k] for k in COMPONENTS)
    if not math.isclose(total, row['predicted_mse'], rel_tol=1e-12, abs_tol=1e-9):
        raise ValueError('MSE component reconstruction failed')
    row['covariance_reduction_fraction'] = -row['mean_shared_rr_adjustment']/(row['predicted_mse']-row['mean_shared_rr_adjustment'])
    return row


def _inventory(output):
    return {str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob('*'))
            if p.is_file() and p != output/'manifest.json'}


def run_study(config_path: Path, output: Path, adapter: EscapeAdapter) -> dict:
    config = load_config(config_path)
    output.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    try:
        pilot._write_json(output/'config.json', config)
        (output/'escape').mkdir()
        graph_map = {}
        for spec in config['graphs']:
            graph = study_graph(spec)
            graph_map[spec['id']] = graph
            native = adapter.run(graph)
            if native.counts.connected_four['3-path'] != count_four_paths(graph) or native.counts.three_vertex[3] != count_triangles(graph):
                raise ValueError(f'ESCAPE mismatch: {spec["id"]}')
            pilot._write_json(output/'escape'/f'{spec["id"]}.json', asdict(native))
        # Preserve raw native evidence for the fixed controls too.
        for n in sorted({c['n'] for c in config['controls']}):
            graph = study_graph({'id': f'control{n}', 'family': 'complete', 'n': n})
            native = adapter.run(graph)
            if native.counts.connected_four['3-path'] != count_four_paths(graph) or native.counts.three_vertex[3] != count_triangles(graph):
                raise ValueError('ESCAPE control mismatch')
            pilot._write_json(output/'escape'/f'control{n}.json', asdict(native))
        provenance = {'binary_sha256': sha256(adapter.executable),
                      'reference_manifest_sha256': sha256(pilot.PROJECT/'third_party/references.json')}
        build_manifest = adapter.executable.parent/'build.json'
        if build_manifest.exists():
            provenance['build'] = json.loads(build_manifest.read_text())
        pilot._write_json(output/'escape_provenance.json', provenance)
        controls(config).to_csv(output/'fixed_controls.csv', index=False, float_format='%.17g')
        rows = []
        for index, cell in enumerate(config['cells']):
            cc = cell_config(config, index)
            directory = output/'cells'/cell['id']
            pilot._run_experiment(cc, directory, study_graph)
            rows.append(summarize_cell(directory, cell, graph_map[cell['graph']]))
            print(f'completed {index+1}/{len(config["cells"])}: {cell["id"]}', flush=True)
        summary = pd.DataFrame(rows)
        summary.to_csv(output/'summary.csv', index=False, float_format='%.17g')
        plot_summary(summary, output/'plots')
        elapsed = time.perf_counter()-start
        components = sum(float(summary[k].sum()) for k in ['mechanism_seconds', 'full_diagnostic_seconds',
                         'prediction_sampling_seconds', 'prediction_analytical_seconds'])
        source = _provenance()
        source['source_sha256']['scripts/run_four_path_study.py'] = sha256(pilot.PROJECT/'scripts/run_four_path_study.py')
        manifest = {'status': 'complete', 'result_type': 'nonprivate_synthetic_study',
                    **workload(config), 'pipeline_seconds': elapsed,
                    'orchestration_io_escape_plot_seconds': elapsed-components,
                    'process_peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024),
                    'provenance': source, 'files_sha256': _inventory(output)}
        manifest['artifact_bytes_excluding_root_manifest'] = sum((output/p).stat().st_size for p in manifest['files_sha256'])
        pilot._write_json(output/'manifest.json', manifest)
        return manifest
    except Exception as exc:
        pilot._write_json(output/'failure.json', {'status': 'failed', 'error': str(exc)})
        raise


def verify_study(output: Path, *, replay=False) -> dict:
    manifest = json.loads((output/'manifest.json').read_text())
    if manifest['status'] != 'complete' or (output/'failure.json').exists():
        raise ValueError('incomplete study')
    if _inventory(output) != manifest['files_sha256']:
        raise ValueError('study inventory/hash mismatch')
    config = load_config(output/'config.json')
    rows = []
    for index, cell in enumerate(config['cells']):
        directory = output/'cells'/cell['id']
        if _load_cell(directory/'config.json') != cell_config(config, index):
            raise ValueError('cell config differs from study')
        pilot._verify_results(directory, _load_cell, study_graph, replay=replay)
        rows.append(summarize_cell(directory, cell, study_graph(next(g for g in config['graphs'] if g['id'] == cell['graph']))))
    expected = pd.DataFrame(rows)
    actual = pd.read_csv(output/'summary.csv', float_precision='round_trip')
    # CSV represents undefined metrics as NaN; normalize recomputed None values
    # to that same representation before comparison (no numeric tolerance change).
    expected = expected.where(expected.notna(), float("nan"))
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False, rtol=1e-12, atol=1e-12)
    pd.testing.assert_frame_equal(pd.read_csv(output/'fixed_controls.csv', float_precision='round_trip'),
                                  controls(config), check_dtype=False, rtol=1e-12, atol=1e-12)
    native_graphs = {g['id']: study_graph(g) for g in config['graphs']}
    native_graphs.update({f'control{n}': study_graph({'id': f'control{n}', 'family': 'complete', 'n': n})
                         for n in {c['n'] for c in config['controls']}})
    for name, graph in native_graphs.items():
        saved = json.loads((output/'escape'/f'{name}.json').read_text())
        native = parse_count_four_output(saved['output_text'], num_vertices=graph.num_vertices, num_edges=graph.num_edges)
        if native.connected_four['3-path'] != count_four_paths(graph) or native.three_vertex[3] != count_triangles(graph):
            raise ValueError('ESCAPE saved evidence mismatch')
    return {'status': 'verified', **workload(config), 'replayed': replay}


def plot_summary(summary, output):
    """Descriptive figures; bars are +/-1 SE, RMSE SE uses delta approximation."""
    import matplotlib
    matplotlib.use('Agg', force=True)
    from matplotlib import pyplot as plt
    output.mkdir(parents=True, exist_ok=False)
    def save(fig, name):
        fig.tight_layout()
        for ext in ['png', 'pdf']:
            metadata = {'Software': 'private-graphlets'} if ext == 'png' else {'CreationDate': None, 'ModDate': None}
            fig.savefig(output/f'{name}.{ext}', dpi=150, metadata=metadata)
        plt.close(fig)
    for relative in [False, True]:
        fig, ax = plt.subplots(figsize=(8, 5))
        a = summary[summary.experiment == 'A'].copy()
        # Config IDs have a stable suffix identifying a family/parameter series.
        a['series'] = a.graph.str.replace(r'_n[0-9]+$', '', regex=True)
        for name, group in a.groupby('series', sort=False):
            group = group.sort_values('n')
            denom = group.exact_four_paths.replace(0, np.nan) if relative else 1
            ax.errorbar(group.n, group.empirical_rmse/denom, yerr=group.rmse_se/denom, marker='o', capsize=3, label=f'{name}: empirical')
            ax.plot(group.n, np.sqrt(group.predicted_mse)/denom, '--', alpha=.7, label=f'{name}: predicted')
        ax.set(xlabel='Vertices n', ylabel='Relative RMSE' if relative else 'RMSE (P4 copies)', yscale='log', title='Graph size: empirical +/-1 SE; predicted dashed')
        ax.legend(fontsize=7, ncol=2); ax.grid(alpha=.25)
        save(fig, 'relative_rmse_vs_size' if relative else 'rmse_vs_size')
    for experiment, name, title in [('B', 'mse_vs_epsilon', 'Fixed allocation fractions'), ('C', 'mse_by_allocation', 'Equal total epsilon = 4')]:
        subset = summary[summary.experiment == experiment]
        fig, axes = plt.subplots(1, max(1, subset.graph.nunique()), figsize=(11, 4), squeeze=False)
        for ax, (graph, group) in zip(axes.flat, subset.groupby('graph', sort=False)):
            x = group.epsilon if experiment == 'B' else np.arange(len(group))
            ax.errorbar(x, group.empirical_mse, yerr=group.se_mse, fmt='o', capsize=3, label='Empirical +/-1 SE')
            ax.errorbar(x, group.predicted_mse, yerr=group.prediction_se, fmt='x', capsize=3, label='Predicted +/-1 SE')
            if experiment == 'C': ax.set_xticks(x, group.allocation, rotation=20)
            ax.set(title=graph, xlabel='Total epsilon' if experiment == 'B' else 'Allocation', ylabel='MSE (copies squared)', yscale='log')
            ax.legend(fontsize=7); ax.grid(alpha=.25)
        fig.suptitle(title)
        save(fig, name)
    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(summary))
    # Signed fractions deliberately retained; no misleading positive stacked pie.
    for key in COMPONENTS:
        ax.plot(x, summary['mean_'+key]/summary.predicted_mse, '.', label=key)
    ax.axhline(0, color='black', lw=.6)
    ax.set_xticks(x, summary.cell, rotation=90, fontsize=6)
    ax.set(ylabel='Signed component / predicted MSE', title='Analytical decomposition (signed covariance retained)')
    ax.legend(fontsize=7, ncol=3)
    save(fig, 'mse_components')
    d = summary[summary.experiment == 'D2']
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    x = np.arange(len(d))
    for ax, full_key, pred_key, title in [(axes[0], 'full_truncation_frequency', 'truncation_frequency', 'Fraction with missed triangles'),
                                         (axes[1], 'full_mean_missed_triangles', 'mean_missed_triangles', 'Mean missed triangles')]:
        ax.bar(x-.18, d[full_key], .36, label='Full protocol histories')
        ax.bar(x+.18, d[pred_key], .36, label='Independent prediction histories')
        ax.set_xticks(x, d.cell, rotation=25, fontsize=7)
        ax.set(title=title); ax.legend(fontsize=7)
    save(fig, 'truncation')
