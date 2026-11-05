"""Portability/safety checks; temporary toy repositories are not research sources."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from private_graphlets.references import REFERENCE_PATHS, reference_path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'scripts'))
from _reference_tools import fingerprint, git, load_manifest, verify_tree
from bootstrap_references import install_reference, check_submodule_pin, is_project_git


@pytest.mark.parametrize('name', REFERENCE_PATHS)
def test_priority_and_cwd_independence(name, monkeypatch, tmp_path):
    env, dirname = REFERENCE_PATHS[name]
    monkeypatch.delenv(env, raising=False)
    monkeypatch.setattr('private_graphlets.references.project_root', lambda: tmp_path)
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert reference_path(name) == tmp_path / 'third_party' / dirname
    monkeypatch.setenv(env, 'relative-source')
    assert reference_path(name) == tmp_path / 'relative-source'
    assert reference_path(name, 'explicit') == tmp_path / 'explicit'
    assert reference_path(name, elsewhere) == elsewhere
    monkeypatch.setenv(env, '')
    with pytest.raises(ValueError, match='empty'):
        reference_path(name)
    assert reference_path(name, elsewhere) == elsewhere


def test_real_manifest_layout():
    rows = load_manifest(PROJECT)
    for name, (_, dirname) in REFERENCE_PATHS.items():
        assert rows[name]['path'] == f'third_party/{dirname}'
    assert rows['baseline']['integration'] == 'submodule'
    assert rows['baseline']['commit'] == '85eff6efa2b1d649ee238620a998ec7f1d305aac'
    for name in ('escape', 'kcored', 'baseline'):
        for key in ('url', 'path'):
            assert git(PROJECT, 'config', '-f', '.gitmodules', '--get', f'submodule.{name}.{key}') == rows[name][key]


@pytest.fixture
def toy(tmp_path):
    root = tmp_path / 'toy'
    root.mkdir()
    git(root, 'init', '-q')
    (root / 'source.txt').write_text('reference fixture\n')
    git(root, 'add', 'source.txt')
    git(root, '-c', 'user.name=Test Fixture', '-c', 'user.email=fixture@example.invalid',
        '-c', 'commit.gpgsign=false', 'commit', '-qm', 'temporary unit-test fixture')
    git(root, 'remote', 'add', 'origin', 'https://example.invalid/toy.git')
    fp = fingerprint(root, ['source.txt'])
    row = {**fp, 'path': 'third_party/toy', 'url': fp['origin'], 'integration': 'submodule'}
    return root, row


def test_modified_and_untracked_trees_are_never_overwritten(tmp_path, toy):
    source, row = toy
    project = tmp_path / 'project'
    target = project / row['path']
    target.parent.mkdir(parents=True)
    shutil.copytree(source, target)
    assert install_reference(project, 'toy', row, check_only=False, timeout=5).startswith('VERIFIED')
    (target / 'source.txt').write_text('local work')
    with pytest.raises(ValueError, match='modified'):
        install_reference(project, 'toy', row, check_only=False, timeout=5)
    assert (target / 'source.txt').read_text() == 'local work'
    (target / 'source.txt').write_text('reference fixture\n')
    (target / 'extra.txt').write_text('untracked work')
    with pytest.raises(ValueError, match='modified'):
        install_reference(project, 'toy', row, check_only=False, timeout=5)
    assert (target / 'extra.txt').read_text() == 'untracked work'


def test_wrong_revision_or_content_is_not_replaced(toy):
    source, row = toy
    with pytest.raises(ValueError, match='commit differs'):
        verify_tree(source, {**row, 'commit': '0' * 40})
    with pytest.raises(ValueError, match='tracked_tree_sha256 differs'):
        verify_tree(source, {**row, 'tracked_tree_sha256': 'bad'})


def test_not_a_reference_git_root(tmp_path, toy):
    root, row = toy
    child = root / 'child'
    child.mkdir()
    with pytest.raises(ValueError, match='standalone'):
        fingerprint(child, [])


def test_zip_bootstrap_is_atomic_and_idempotent(tmp_path, toy, monkeypatch):
    source, row = toy
    project = tmp_path / 'zip copy'
    project.mkdir()
    calls = []
    def fake_clone(command, *, timeout):
        calls.append(command)
        shutil.copytree(source, Path(command[-1]))
    monkeypatch.setattr('bootstrap_references.run', fake_clone)
    assert 'ZIP checkout' in install_reference(project, 'toy', row, check_only=False, timeout=5)
    assert install_reference(project, 'toy', row, check_only=False, timeout=5).startswith('VERIFIED')
    assert len(calls) == 1
    assert not list((project / 'third_party').glob('.bootstrap-*'))


def test_failed_network_leaves_no_partial_zip_checkout(tmp_path, toy, monkeypatch):
    _, row = toy
    def offline(command, *, timeout):
        raise subprocess.CalledProcessError(128, command, stderr='network unavailable')
    monkeypatch.setattr('bootstrap_references.run', offline)
    with pytest.raises(subprocess.CalledProcessError):
        install_reference(tmp_path, 'toy', row, check_only=False, timeout=5)
    assert not (tmp_path / row['path']).exists()
    assert not list((tmp_path / 'third_party').glob('.bootstrap-*'))


def test_manual_reference_is_never_fetched(tmp_path, toy, monkeypatch):
    _, row = toy
    def unexpected(*args, **kwargs):
        pytest.fail('manual reference must not cause a download')
    monkeypatch.setattr('bootstrap_references.run', unexpected)
    assert install_reference(tmp_path, 'baseline', {**row, 'integration': 'manual'},
                             check_only=False, timeout=5).startswith('MANUAL')


def test_nonempty_nonrepo_and_symlink_are_refused(tmp_path, toy):
    source, row = toy
    target = tmp_path / row['path']
    target.parent.mkdir()
    target.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        install_reference(tmp_path, 'toy', row, check_only=False, timeout=5)
    target.unlink()
    target.mkdir()
    (target / 'important.txt').write_text('keep')
    with pytest.raises(subprocess.CalledProcessError):
        install_reference(tmp_path, 'toy', row, check_only=False, timeout=5)
    assert (target / 'important.txt').read_text() == 'keep'


def test_check_only_cannot_download(tmp_path, toy):
    _, row = toy
    with pytest.raises(ValueError, match='missing'):
        install_reference(tmp_path, 'toy', row, check_only=True, timeout=5)
    assert not (tmp_path / 'third_party').exists()


def test_git_bootstrap_requires_correct_gitlink(tmp_path, toy):
    source, row = toy
    project = tmp_path / 'superproject'
    project.mkdir()
    git(project, 'init', '-q')
    assert is_project_git(project)
    with pytest.raises(ValueError, match='Git index'):
        check_submodule_pin(project, 'toy', row)
    git(project, 'update-index', '--add', '--cacheinfo', f"160000,{row['commit']},{row['path']}")
    for key in ('path', 'url'):
        git(project, 'config', '-f', '.gitmodules', f'submodule.toy.{key}', row[key])
    check_submodule_pin(project, 'toy', row)
    git(project, 'config', 'submodule.toy.url', 'https://example.invalid/different')
    with pytest.raises(ValueError, match='local submodule URL'):
        check_submodule_pin(project, 'toy', row)


@pytest.mark.parametrize('badpath', ['../escape', '/tmp/escape', 'third_party/../escape'])
def test_manifest_rejects_unsafe_paths(tmp_path, badpath):
    content = json.loads((PROJECT / 'third_party/references.json').read_text())
    content['references']['escape']['path'] = badpath
    (tmp_path / 'third_party').mkdir()
    (tmp_path / 'third_party/references.json').write_text(json.dumps(content))
    with pytest.raises(ValueError, match='unsafe'):
        load_manifest(tmp_path)
