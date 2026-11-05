"""Exact P4/triangle identities, independent enumeration and native ESCAPE."""

from itertools import combinations
import json
from math import comb
from pathlib import Path

import pytest

from private_graphlets.four_path_exact import count_four_paths, count_four_paths_bruteforce
from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.triangle_exact import count_triangles


PROJECT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT / "data/fixtures"
EXPECTED = json.loads((FIXTURES / "expected_counts.json").read_text())
TRIANGLES = {"edgeless": 0, "star": 0, "path": 0, "tailed_triangle": 1,
             "cycle": 0, "diamond": 2, "clique": 4, "clique_with_isolates": 4}


@pytest.mark.parametrize("name", TRIANGLES)
def test_named_fixtures_and_immutability(name):
    graph = load_edge_list(FIXTURES / f"{name}.edges")
    before = graph.adjacency
    expected = EXPECTED["cases"][name][EXPECTED["order"].index("3-path")]
    for _ in range(2):
        for counter, truth in ((count_four_paths, expected),
                               (count_four_paths_bruteforce, expected),
                               (count_triangles, TRIANGLES[name])):
            result = counter(graph)
            assert type(result) is int
            assert result == truth
    assert graph.adjacency is before
    assert graph == load_edge_list(FIXTURES / f"{name}.edges")


@pytest.mark.parametrize("n", range(6))
def test_every_labeled_graph_through_five_vertices(n):
    pairs = list(combinations(range(n), 2))
    for mask in range(1 << len(pairs)):
        graph = SimpleGraph.from_edges(n, [edge for i, edge in enumerate(pairs)
                                           if mask & (1 << i)])
        assert count_four_paths(graph) == count_four_paths_bruteforce(graph), (n, mask)
        triangles = sum(
            b in graph.adjacency[a] and c in graph.adjacency[a] and c in graph.adjacency[b]
            for a, b, c in combinations(range(n), 3)
        )
        assert count_triangles(graph) == triangles, (n, mask)


@pytest.mark.parametrize("name", TRIANGLES)
def test_isolates_and_relabeling(name):
    graph = load_edge_list(FIXTURES / f"{name}.edges")
    edges = [(u, v) for u, row in enumerate(graph.adjacency) for v in row if u < v]
    padded = SimpleGraph.from_edges(graph.num_vertices + 3, edges)
    relabeled = SimpleGraph.from_edges(graph.num_vertices,
                                     [(graph.num_vertices-1-u, graph.num_vertices-1-v)
                                      for u, v in edges])
    for counter in (count_four_paths, count_four_paths_bruteforce, count_triangles):
        assert counter(graph) == counter(padded) == counter(relabeled)


def test_noninduced_paths_and_reversal_normalization():
    edges = [(0, 1), (1, 2), (2, 3)]
    for extra, expected in (([], 1), ([(0, 3)], 4),
                            ([(0, 3), (0, 2), (1, 3)], 12)):
        graph = SimpleGraph.from_edges(4, edges + extra)
        assert count_four_paths(graph) == count_four_paths_bruteforce(graph) == expected


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 5, 8])
def test_complete_graphs(n):
    graph = SimpleGraph.from_edges(n, combinations(range(n), 2))
    assert count_triangles(graph) == comb(n, 3)
    assert count_four_paths(graph) == count_four_paths_bruteforce(graph) == 12 * comb(n, 4)


@pytest.mark.escape_integration
@pytest.mark.parametrize("name", TRIANGLES)
def test_exact_counters_against_escape(escape_adapter, name):
    graph = load_edge_list(FIXTURES / f"{name}.edges")
    run = escape_adapter.run(graph)
    formula = count_four_paths(graph)
    brute = count_four_paths_bruteforce(graph)
    triangles = count_triangles(graph)
    # Keep native evidence separate from Python results, including on mismatch.
    evidence = PROJECT / "build/phase09/escape"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / f"{name}.json").write_text(json.dumps({
        "input_text": run.input_text, "output_text": run.output_text,
        "stdout": run.stdout, "stderr": run.stderr,
        "executable": str(escape_adapter.executable),
        "build_manifest": "build/escape-pytest/build.json",
        "python_four_paths": formula, "python_bruteforce": brute,
        "python_triangles": triangles,
        "escape_four_paths": run.counts.connected_four["3-path"],
        "escape_triangles": run.counts.three_vertex[3],
    }, indent=2) + "\n")
    assert formula == brute == run.counts.connected_four["3-path"]
    assert triangles == run.counts.three_vertex[3]
