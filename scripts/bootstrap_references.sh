#!/usr/bin/env bash
# No venv or scientific packages needed; never runs upstream setup scripts.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${BOOTSTRAP_PYTHON:-python3}" "$project_root/scripts/bootstrap_references.py" "$@"
