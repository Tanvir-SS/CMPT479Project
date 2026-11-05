"""Read-only fingerprints of all three references; --verify checks pinned content."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from private_graphlets.references import reference_path

# Also support importing fingerprint from this script for read-only audits.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _reference_tools import fingerprint, load_manifest, verify_tree


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    manifest = load_manifest(project)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--escape-root', '--escape', dest='escape', type=Path)
    parser.add_argument('--kcored-root', '--ledp', dest='kcored', type=Path)
    parser.add_argument('--baseline-root', '--baseline', dest='baseline', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = {}
    failed = False
    for name, row in manifest.items():
        key = 'ledp' if name == 'kcored' else name  # Preserve historical report key.
        try:
            path = reference_path(name, getattr(args, name))
            env = {'escape': 'ESCAPE_ROOT', 'kcored': 'KCORED_ROOT', 'baseline': 'BASELINE_ROOT'}[name]
            import os
            configured = getattr(args, name) is not None or env in os.environ
            empty = not path.exists() or (path.is_dir() and not any(path.iterdir()))
            if empty and row['integration'] == 'manual' and not configured:
                result[key] = {'path_at_review': str(path), 'status': 'optional_manual_reference_absent',
                               'expected_commit': row['commit'], 'available': False}
                continue
            data = verify_tree(path, row) if args.verify else fingerprint(path, list(row['reviewed_file_sha256']))
            result[key] = {**data, 'available': True, 'verified': args.verify}
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            result[key] = {'status': 'error', 'error': str(exc), 'available': False}
            failed = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
