#!/usr/bin/env bash
# Maintainer operation: deliberately resolves dependencies; normal setup does not.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
export PIP_CACHE_DIR="$project_root/.cache/pip"
export PIP_TOOLS_CACHE_DIR="$project_root/.cache/pip-tools"
export CUSTOM_COMPILE_COMMAND="bash scripts/lock_dependencies.sh"
.venv/bin/python -m piptools compile \
    --extra dev --generate-hashes --resolver backtracking --strip-extras \
    --constraint requirements-constraints.txt \
    --allow-unsafe --no-emit-index-url --no-emit-trusted-host \
    --output-file requirements.lock pyproject.toml
