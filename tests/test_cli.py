"""Installed CLI behavior, JSON separation and failures."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from private_graphlets.cli import main
from private_graphlets.three_star import estimate_three_stars
from private_graphlets.graph import load_edge_list


@pytest.fixture
def graph_path(tmp_path):
    path = tmp_path / "star with isolates.edges"
    path.write_text("6 3\n0 1\n0 2\n0 3\n")
    return path


def run_cli(*args):
    return subprocess.run([str(Path(sys.executable).parent / "private-graphlets"), *map(str, args)],
                          cwd="/tmp", capture_output=True, text=True)


def test_private_cli_json_and_replay(graph_path):
    args = ("estimate-three-stars", graph_path, "--epsilon", "2", "--seed", "71")
    first = run_cli(*args)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    assert first.stdout == run_cli(*args).stdout
    record = json.loads(first.stdout)
    expected = estimate_three_stars(load_edge_list(graph_path), 2, seed=71).to_dict()
    software = record.pop("software")
    assert software["numpy"]
    assert record == expected
    assert not {"count", "degrees", "true_degrees", "exact_count", "num_edges", "seed", "noise"} & record.keys()


def test_exact_cli_is_separate(graph_path):
    result = run_cli("exact-three-stars", graph_path)
    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["result_type"] == "exact_ground_truth"
    assert record["count"] == 1
    assert "estimate" not in record
    assert "epsilon" not in record


def test_private_path_never_calls_exact_counter(graph_path, monkeypatch, capsys):
    import private_graphlets.exact
    def forbidden(*args):
        raise AssertionError("exact counting was invoked by private command")
    monkeypatch.setattr(private_graphlets.exact, "count_three_stars", forbidden)
    assert main(["estimate-three-stars", str(graph_path), "--epsilon", "1", "--seed", "7"]) == 0
    assert json.loads(capsys.readouterr().out)["result_type"] == "private_estimate"


@pytest.mark.parametrize("epsilon", ["0", "-1", "nan", "inf", "-inf", "nope", "1e-200"])
def test_cli_invalid_epsilon_or_numeric_failure(graph_path, epsilon):
    result = run_cli("estimate-three-stars", graph_path, f"--epsilon={epsilon}")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_requires_epsilon_and_valid_seed(graph_path):
    assert run_cli("estimate-three-stars", graph_path).returncode == 2
    assert run_cli("estimate-three-stars", graph_path, "--epsilon", "1", "--seed", "-1").returncode == 2
    result = run_cli("estimate-three-stars", graph_path, "--epsilon", "1")
    assert result.returncode == 0
    assert json.loads(result.stdout)["simulation_only"] is True


def test_cli_bad_graph_fails_without_output(tmp_path):
    path = tmp_path / "loop.edges"
    path.write_text("4 1\n0 0\n")
    result = run_cli("estimate-three-stars", path, "--epsilon", "1")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "self-loop" in result.stderr
    assert run_cli("exact-three-stars", tmp_path / "missing").returncode == 2
