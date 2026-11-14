"""Strict lossless conversion of the six pinned graphs to author CSV format."""
import json
from pathlib import Path
from build import ROOT, sha
BASE = Path(__file__).resolve().parent
OUT = BASE/'outputs'
CONFIG = ROOT/'experiments/configs/four_cycle_uniform_rr_six_datasets.json'

def count_c4(n, edges):
    adj = [set() for _ in range(n)]
    for u,v in edges:
        adj[u].add(v); adj[v].add(u)
    total = sum(len(adj[u]&adj[v])*(len(adj[u]&adj[v])-1)//2 for u in range(n) for v in range(u+1,n))
    assert total % 2 == 0
    return total//2

def write_graph(path, n, edges):
    path.write_text('nodes\n'+str(n)+'\nsource,target\n'+''.join(f'{u},{v}\n' for u,v in edges))

def main():
    OUT.mkdir(exist_ok=True)
    (OUT/'inputs').mkdir(exist_ok=True)
    config = json.loads(CONFIG.read_text())
    cache = json.loads((ROOT/'experiments/results/four_cycle_uniform_rr_six_datasets/escape_ground_truth.json').read_text())
    records=[]
    for g, truth in zip(config['graphs'], cache, strict=True):
        p=ROOT/g['path']
        assert sha(p)==g['sha256']
        lines=p.read_text().splitlines()
        n,m=map(int, lines[0].split())
        edges=[tuple(map(int, s.split())) for s in lines[1:]]
        assert (n,m)==(g['n'],g['m']) and len(edges)==m
        assert edges==sorted(set(edges)) and all(0<=u<v<n for u,v in edges)
        dest=OUT/'inputs'/f"{g['id']}.csv"
        write_graph(dest,n,edges)
        back=[tuple(map(int,s.split(','))) for s in dest.read_text().splitlines()[3:]]
        assert back==edges and int(dest.read_text().splitlines()[1])==n
        exact=count_c4(n,back)
        assert truth['graph']==g['id'] and truth['sha256']==g['sha256']
        assert exact==g['expected_c4']==truth['exact_count']
        records.append(dict(g, converted_sha256=sha(dest), exact_count=exact))
    (OUT/'conversion.json').write_text(json.dumps(records,indent=2)+'\n')
    (OUT/'escape_ground_truth.json').write_text(json.dumps(cache,indent=2)+'\n')
    print('Six lossless conversions match cached ESCAPE C4 truth.')

if __name__=='__main__': main()
