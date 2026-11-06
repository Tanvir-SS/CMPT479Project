"""Prepare/verify public 4-clique datasets only; never run a private estimator."""

import argparse
import json
from pathlib import Path
import platform
import sys

from private_graphlets.escape import EscapeAdapter, EscapeError, build_count_four
from private_graphlets.graph_datasets import (PROJECT, prepare_datasets, verify_datasets,
    future_configs, json_bytes, write_identical_or_new, digest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','verify'])
    parser.add_argument('--download',action='store_true',help='Fetch missing hash-pinned raw archives (prepare only).')
    parser.add_argument('--raw-dir',type=Path,default=PROJECT/'data/raw/graph_benchmarks')
    parser.add_argument('--output',type=Path,default=PROJECT/'data/processed')
    parser.add_argument('--config-dir',type=Path,help='Write future configs; default experiments/configs only for standard output.')
    parser.add_argument('--escape-root',type=Path)
    parser.add_argument('--escape',action='store_true',help='Execute fresh ESCAPE in verify mode (prepare always executes it).')
    parser.add_argument('--brute-force',action='store_true',help='Fresh four-set enumeration in verify (prepare always does this).')
    parser.add_argument('--evidence',type=Path,help='Ignored execution evidence; defaults to build/phase13/dataset_COMMAND.json.')
    args = parser.parse_args()
    try:
        if args.command=='verify' and args.download: raise ValueError('--download is only for prepare')
        if args.config_dir is not None and args.output.resolve()!=(PROJECT/'data/processed').resolve():
            raise ValueError('future configs reference standard project paths; omit --config-dir for alternate output')
        if args.evidence is None:
            suffix = 'prepare' if args.command=='prepare' else f'verify_escape{int(args.escape)}_brute{int(args.brute_force)}'
            args.evidence = PROJECT/f'build/phase13/dataset_{suffix}.json'
        adapter = None
        if args.command=='prepare' or args.escape:
            adapter = EscapeAdapter(build_count_four(args.escape_root,build_dir=PROJECT/'build/phase13/escape'))
        if args.command=='prepare':
            manifest,native = prepare_datasets(args.raw_dir,args.output,adapter,download=args.download)
            config_dir = args.config_dir
            if config_dir is None and args.output.resolve()==(PROJECT/'data/processed').resolve():
                config_dir = PROJECT/'experiments/configs'
            if config_dir is not None:
                for name,config in future_configs(manifest): write_identical_or_new(config_dir/name,json_bytes(config))
            report = {'status':'verified','graphs':len(manifest['graphs']),'fresh_escape':True,'fresh_bruteforce':True,
                'manifest_sha256':digest(args.output/'graph_manifest.json'),
                'python':sys.version,'platform':platform.platform(),
                'escape_executable_sha256':digest(adapter.executable),
                'escape_build':json.loads((adapter.executable.parent/'build.json').read_text()),
                'native_comparisons':native}
        else:
            report = verify_datasets(args.output,adapter,brute_force=args.brute_force)
        # Runtime/platform-dependent evidence belongs in ignored build/, never the stable manifest.
        args.evidence.parent.mkdir(parents=True,exist_ok=True)
        if args.evidence.exists():
            if args.evidence.read_bytes()!=json_bytes(report):
                previous = json.loads(args.evidence.read_text())
                # Fresh execution times/compiler paths may differ on an idempotent
                # prepare. Preserve prior evidence only for this same accepted manifest.
                if (args.command!='prepare' or previous.get('status')!='verified'
                        or previous.get('manifest_sha256')!=report['manifest_sha256']):
                    raise ValueError('evidence exists and differs; use a new --evidence path')
                print('Preserved previous native evidence for the identical dataset manifest.',file=sys.stderr)
        else: args.evidence.write_bytes(json_bytes(report))
        print(json.dumps({k:report[k] for k in ('status','graphs','fresh_escape','fresh_bruteforce')}))
    except (OSError,ValueError,KeyError,AssertionError,EscapeError) as exc:
        parser.exit(1,f'ERROR: {exc}\n')


if __name__=='__main__': main()
