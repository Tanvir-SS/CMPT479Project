"""Optional reference checkout configuration; configured failures are never skipped."""

import os
from pathlib import Path

import pytest

from private_graphlets.escape import EscapeAdapter, build_count_four


def pytest_addoption(parser):
    parser.addoption("--escape-root", help="ESCAPE source root (or set ESCAPE_ROOT).")


@pytest.fixture(scope="session")
def escape_adapter(request):
    root = request.config.getoption("--escape-root") or os.environ.get("ESCAPE_ROOT")
    if not root:
        pytest.skip("ESCAPE not configured: set ESCAPE_ROOT or pass --escape-root")
    project = Path(__file__).resolve().parents[1]
    binary = build_count_four(root, build_dir=project / "build/escape-pytest")
    return EscapeAdapter(binary)
