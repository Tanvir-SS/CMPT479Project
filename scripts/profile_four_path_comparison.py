"""Bounded NON-PRIVATE stage/memory diagnostic; separate from primary trial timing."""
import cProfile
from dataclasses import asdict
import json
from pathlib import Path
import pstats
import time
import tracemalloc

from private_graphlets.four_path_comparison import load_config,historical_graphs
from private_graphlets.four_path import FourPathBudget,simulate_four_paths_private
from private_graphlets.four_path_baseline_2025 import Baseline2025Budget,simulate_four_paths_baseline_2025
from private_graphlets.kcore import KCoreConfig


def main():
    c=load_config(Path('experiments/configs/four_path_phase17_comparison.json'))
    graphs,_=historical_graphs(c); rows=[]
    for n in (20,50,100):
        name=f'er30_n{n}';g=graphs[name]
        cell=next(x for x in c['cells'] if x['graph']==name and x['experiment']=='A')
        for method in ('candidate','baseline'):
            def call(seed):
                if method=='candidate':
                    return simulate_four_paths_private(g,budget=FourPathBudget(**cell['budget']),seed=seed,
                        beta=cell['beta'],kcore_config=KCoreConfig(**c['kcore']))
                return simulate_four_paths_baseline_2025(g,budget=Baseline2025Budget(cell['baseline_epsilon']),seed=seed)
            profiler=cProfile.Profile();profiler.enable()
            for t in range(3): call(171900+n*10+t)
            profiler.disable()
            selected={'local_degree_report','kcore_order','local_cap_report','cap_from_reports',
                      'sample_rr_upper','rr_matrix','degree_product_estimate','estimate_triangles_from_rr','four_path_weighted_sum'}
            stages={}
            for (file,line,function),(primitive,calls,own,cumulative,callers) in pstats.Stats(profiler).stats.items():
                if function in selected and 'private_graphlets' in file:
                    stages[function]={'calls':calls,'inclusive_seconds_per_trial':cumulative/3}
            # Different seed, separate invocation: do not mix tracing into primary timings.
            tracemalloc.start();start=time.perf_counter();run=call(172900+n)
            traced_seconds=time.perf_counter()-start
            current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            rows.append(dict(graph=name,n=n,method=method,profile_trials=3,
                stages=stages,traced_peak_bytes=peak,traced_retained_bytes=current,
                traced_seconds=traced_seconds,
                transcript_json_bytes=len(json.dumps(asdict(run.transcript)).encode())))
    output=Path('build/phase17/profile.json')
    if output.exists():raise FileExistsError(output)
    output.write_text(json.dumps({'scope':'NON_PRIVATE_INSTRUMENTED_DIAGNOSTIC_NOT_PRIMARY_TIMING',
        'profile_seed_rule':'171900+n*10+t, t=0..2','memory_seed_rule':'172900+n',
        'memory_scope':'tracemalloc Python-tracked incremental allocations; graph preloaded, not full RSS',
        'rows':rows},indent=2)+'\n')
    print(output)


if __name__=='__main__':main()
