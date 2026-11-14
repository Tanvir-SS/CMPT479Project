"""Build isolated author source; supplied WLocal4Cycle files remain unchanged."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
BUILD = ROOT / 'build/wlocal'
PINS = {'stats': 'f8dcb15ae51cce7142b239805745a0de56aa509f',
        'gcem': '012ae73c6d0a2cb09ffe86475f5c6fba3926e200'}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    for name, pin in PINS.items():
        dest = BUILD / name
        if not dest.exists():
            subprocess.run(['git', 'clone', f'https://github.com/kthohr/{name}.git', str(dest)], check=True)
            subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', pin], check=True)
        actual = subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip()
        assert actual == pin, (name, actual)
    source = ROOT / 'WLocal4Cycle'
    for name in ['SubgraphShuffle.cpp', 'MemoryOperation.h', 'mt19937ar.h']:
        shutil.copyfile(source / name, BUILD / name)
    original = (source / 'SubgraphShuffle.cpp').read_text()
    before, target = original.split('void CalcShuffleCy4(', 1)
    assert target.count('for(i=0;i<NodeNum;i+=2)') == 1
    patched = before + 'void CalcShuffleCy4(' + target.replace('for(i=0;i<NodeNum;i+=2)', 'for(i=0;i+1<NodeNum;i+=2)', 1)
    (BUILD / 'SubgraphShuffle.cpp').write_text(patched)
    header = (BUILD / 'MemoryOperation.h').read_text().replace('#include <malloc.h>', '// stdlib.h already declares calloc/free (portable to macOS)')
    header = header.replace('if (source == NULL)', 'if (*source == NULL)')
    (BUILD / 'MemoryOperation.h').write_text(header)
    patches = ''.join(difflib.unified_diff(original.splitlines(True), patched.splitlines(True), fromfile='original/SubgraphShuffle.cpp', tofile='build/SubgraphShuffle.cpp'))
    patches += ''.join(difflib.unified_diff((source/'MemoryOperation.h').read_text().splitlines(True), header.splitlines(True), fromfile='original/MemoryOperation.h', tofile='build/MemoryOperation.h'))
    (BASE / 'source.patch').write_text(patches)
    if not (BUILD / 'include').exists():
        (BUILD / 'include').symlink_to(BUILD / 'stats/include', target_is_directory=True)
    shutil.copyfile(source / 'Makefile.txt', BUILD / 'Makefile')
    flags = f'-O3 -std=c++11 -isystem {BUILD}/gcem/include -MMD'
    commands = [['make', '-C', str(BUILD), f'CXXFLAGS={flags}', 'CXX=c++', 'CC=c++'],
                ['c++', '-O3', '-std=c++11', '-I', str(BUILD), '-isystem', str(BUILD/'gcem/include'), str(BASE/'driver.cpp'), '-o', str(BUILD/'wlocal')],
                ['c++', '-O1', '-g', '-std=c++11', '-fsanitize=address,undefined', '-I', str(BUILD), '-isystem', str(BUILD/'gcem/include'), str(BASE/'driver.cpp'), '-o', str(BUILD/'wlocal_sanitize')]]
    for cmd in commands:
        subprocess.run(cmd, check=True)
    provenance = {'pins': PINS, 'commands': commands, 'compiler': subprocess.check_output(['c++','--version'], text=True), 'original_sources': {p.name:sha(p) for p in source.iterdir() if p.is_file()}, 'executables': {p.name:sha(p) for p in [BUILD/'wlocal', BUILD/'SubgraphShuffle']}}
    (BUILD/'build.json').write_text(json.dumps(provenance, indent=2)+'\n')

if __name__ == '__main__':
    main()
