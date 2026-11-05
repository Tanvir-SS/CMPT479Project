"""Optional reference checkout configuration; configured failures are never skipped."""

import os
from pathlib import Path

import pytest

from private_graphlets.escape import EscapeAdapter, build_count_four
from private_graphlets.references import reference_path


def pytest_addoption(parser):
    parser.addoption("--escape-root", help="ESCAPE source: explicit > ESCAPE_ROOT > third_party/escape.")


@pytest.fixture(scope="session")
def escape_adapter(request):
    explicit = request.config.getoption("--escape-root")
    root = reference_path("escape", explicit)
    # Missing/empty uninitialized submodules are optional. Configured or partial
    # checkouts must fail explicitly, never hide a broken reference behind a skip.
    configured = explicit is not None or "ESCAPE_ROOT" in os.environ
    if not configured and (not root.exists() or (root.is_dir() and not any(root.iterdir()))):
        pytest.skip("ESCAPE absent: run bash scripts/bootstrap_references.sh or set ESCAPE_ROOT")
    project = Path(__file__).resolve().parents[1]
    binary = build_count_four(root, build_dir=project / "build/escape-pytest")
    return EscapeAdapter(binary)
