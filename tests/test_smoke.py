"""Verify installation and entry points outside the repository directory."""

import json
from pathlib import Path
import subprocess
import sys

from private_graphlets import __version__


def test_module_info(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "private_graphlets", "info", "--json"],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
    info = json.loads(result.stdout)
    assert info["version"] == __version__
    assert info["python"].startswith("3.11.")
    assert info["implemented_estimators"] == ["3-star"]
    assert "non-induced" in info["count_semantics"]
    assert len(info["patterns"]) == 6


def test_installed_console_help(tmp_path):
    command = Path(sys.executable).parent / "private-graphlets"
    result = subprocess.run(
        [str(command), "--help"], cwd=tmp_path,
        check=True, capture_output=True, text=True,
    )
    assert "info" in result.stdout
    assert "research simulations" in result.stdout


def test_version(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "private_graphlets", "--version"],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
    assert result.stdout.strip() == f"private-graphlets {__version__}"


def test_scientific_dependencies_and_headless_plot(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    import matplotlib
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt
    import networkx as nx
    import numpy as np
    import pandas as pd

    graph = nx.path_graph(4)
    frame = pd.DataFrame({"degree": np.array([d for _, d in graph.degree()])})
    assert frame["degree"].sum() == 6
    figure, axis = plt.subplots()
    axis.plot(frame["degree"].to_numpy())
    output = tmp_path / "smoke.png"
    figure.savefig(output)
    plt.close(figure)
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
