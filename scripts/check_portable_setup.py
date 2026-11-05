"""Check the working-tree snapshot in a fresh recursive local clone and ZIP.

Never commits or pushes the main repository. A disposable Git fixture
represents unpublished files, without committing anything in the main repository.
Both copies fetch authorized references from their actual HTTPS upstreams, create
new venvs, and install the unchanged lock from a predownloaded wheelhouse.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from _reference_tools import load_manifest

PROJECT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=PROJECT / 'build/phase07/portable-check')
    parser.add_argument('--wheelhouse', type=Path, default=PROJECT / 'build/wheelhouse')
    args = parser.parse_args()
    output, wheelhouse = args.output.resolve(), args.wheelhouse.resolve()
    if output.exists():
        raise SystemExit('Output already exists; choose a new --output (previous evidence is preserved).')
    if not wheelhouse.is_dir():
        raise SystemExit('Prepare build/wheelhouse using the README pip download command first.')
    output.mkdir(parents=True)
    names = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=PROJECT,
    ).decode().split('\0')
    files = sorted({name for name in names if name and (PROJECT / name).is_file()})
    if any(name.startswith('third_party/') and name not in ('third_party/README.md', 'third_party/references.json')
           for name in files):
        raise SystemExit('Unexpected vendored reference files; inspect the source snapshot.')
    hashes = {name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() for name in files}
    manifest = load_manifest(PROJECT)
    summary = {'status': 'running', 'snapshot': 'temporary Git fixture of working tree; no main-repo commit/push',
               'project_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PROJECT, text=True).strip(),
               'source_sha256': hashes, 'checks': {}}
    env = os.environ.copy()
    for key in ('VIRTUAL_ENV', 'PYTHONPATH', 'PYTHONHOME', 'ESCAPE_ROOT', 'KCORED_ROOT', 'BASELINE_ROOT'):
        env.pop(key, None)
    env.update(PIP_NO_INDEX='1', PIP_FIND_LINKS=str(wheelhouse), GIT_TERMINAL_PROMPT='0')

    def run(label, command, cwd):
        log_path = output / f'{label}.log'
        print(f'CHECK {label}', flush=True)
        with log_path.open('w') as log:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f'{label} failed ({result.returncode}); see {log_path}')
        return log_path

    try:
        with tempfile.TemporaryDirectory(prefix='cmpt479-phase07-') as temp:
            temporary = Path(temp)
            fixture = temporary / 'snapshot'
            fixture.mkdir()
            run('fixture-init', ['git', 'init', '-q', str(fixture)], temporary)
            for name in files:
                target = fixture / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PROJECT / name, target)
            run('fixture-add', ['git', 'add', '--all'], fixture)
            for row in manifest.values():
                if row['integration'] == 'submodule':
                    run('fixture-index-' + Path(row['path']).name,
                        ['git', 'update-index', '--add', '--cacheinfo',
                         f"160000,{row['commit']},{row['path']}"], fixture)
            # Synthetic test fixture only; never creates a commit in PROJECT.
            run('fixture-commit', ['git', '-c', 'user.name=Portability Test Fixture',
                '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
                'commit', '-qm', 'Disposable portability test snapshot'], fixture)
            summary['temporary_fixture_commit'] = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=fixture, text=True).strip()
            clone = temporary / 'clone'
            run('clone', ['git', 'clone', '--no-local', '--recurse-submodules',
                         str(fixture), str(clone)], temporary)
            archive = output / 'source-snapshot.zip'
            with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
                for name in files:
                    zipped.write(PROJECT / name, 'project/' + name)
            with zipfile.ZipFile(archive) as zipped:
                zipped.extractall(temporary / 'zip')  # Only paths generated above.
            zip_root = temporary / 'zip/project'
            for label, root in (('clone', clone), ('zip', zip_root)):
                for name, digest in hashes.items():
                    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
                # Invoke from outside the project to test root discovery.
                run(label + '-bootstrap', ['bash', str(root / 'scripts/bootstrap_references.sh')], temporary)
                run(label + '-bootstrap-again', ['bash', str(root / 'scripts/bootstrap_references.sh')], temporary)
                run(label + '-setup', ['bash', str(root / 'scripts/setup.sh')], temporary)
                run(label + '-fingerprints', [str(root / '.venv/bin/python'),
                    str(root / 'scripts/reference_fingerprints.py'), '--verify'], temporary)
                if label == 'clone':
                    run('clone-submodules', ['git', 'submodule', 'status'], root)
                run(label + '-exact', [str(root / '.venv/bin/private-graphlets'),
                    'exact-three-stars', str(root / 'data/fixtures/star.edges')], temporary)
                summary['checks'][label] = {'status': 'passed', 'bootstrap_runs': 2,
                    'setup': 'new Python 3.11 .venv; locked offline wheels; full pytest incl. ESCAPE',
                    'source_snapshot_verified': True}
            summary['status'] = 'passed'
    except Exception as exc:
        summary['status'] = 'failed'
        summary['error'] = str(exc)
        raise
    finally:
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f'Recursive clone and ZIP-snapshot checks passed: {output}')


if __name__ == '__main__':
    main()
