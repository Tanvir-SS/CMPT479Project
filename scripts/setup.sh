#!/usr/bin/env bash
# Run from any directory. Never changes the system Python installation.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
python_bin="${PYTHON_BIN:-python3.11}"
"$python_bin" -c 'import sys; assert sys.version_info[:2] == (3, 11), "Python 3.11 is required"'
if [[ ! -d .venv ]]; then
    "$python_bin" -m venv .venv
fi
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 11), "Existing .venv must use Python 3.11"'
export PIP_CACHE_DIR="$project_root/.cache/pip"
export MPLCONFIGDIR="$project_root/.cache/matplotlib"
export MPLBACKEND=Agg
.venv/bin/python -m pip install --disable-pip-version-check --require-hashes -r requirements.lock
.venv/bin/python -m pip install --disable-pip-version-check --no-deps --no-build-isolation -e .
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
.venv/bin/private-graphlets info
