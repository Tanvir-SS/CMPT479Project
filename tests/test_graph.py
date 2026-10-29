"""Format and graph-invariant checks, including duplicates and isolates."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from private_graphlets.graph import SimpleGraph, load_edge_list, parse_edge_list


def parse(text):
    return parse_edge_list(text.splitlines())


def test_deduplication_and_isolates(tmp_path):
    path = tmp_path / "graph.edges"
    path.write_text("# public n, unique m\n\n5 2\n0 1\n1 0 # duplicate\n0 1\n2 1\n")
    graph = load_edge_list(path)
    assert graph.num_vertices == 5
    assert graph.num_edges == 2
    assert graph.adjacency == (frozenset({1}), frozenset({0, 2}), frozenset({1}),
                               frozenset(), frozenset())
    assert graph == SimpleGraph.from_edges(5, [(1, 2), (1, 0), (2, 1)])


@pytest.mark.parametrize("n", [0, 1, 7])
def test_edgeless_graphs(n):
    graph = parse(f"{n} 0\n")
    assert graph.num_vertices == n
    assert graph.num_edges == 0
    assert all(not row for row in graph.adjacency)


@pytest.mark.parametrize("text, message", [
    ("", "missing"), ("# nothing\n", "missing"),
    ("4\n", "two integers"), ("4 0 extra\n", "two integers"),
    ("4.0 0\n", "two integers"), ("n m\n", "two integers"),
    ("-1 0\n", "nonnegative"), ("4 -1\n", "nonnegative"),
    ("2 2\n", "maximum"), ("4 1\n0\n", "two integers"),
    ("4 1\n0 1 2\n", "two integers"), ("4 1\n0 nope\n", "two integers"),
    ("4 1\n0 1.0\n", "two integers"), ("4 1\n0 4\n", "outside"),
    ("4 1\n-1 0\n", "outside"), ("4 1\n0 0\n", "self-loop"),
    ("4 1\n", "does not match"), ("4 0\n0 1\n", "does not match"),
    ("4 2\n0 1\n1 0\n", "does not match"), ("0 0\n0 1\n", "outside"),
])
def test_invalid_files(text, message):
    with pytest.raises(ValueError, match=message):
        parse(text)


@pytest.mark.parametrize("n, edges", [
    (-1, []), (1.5, []), (True, []), (2, [(True, 1)]),
    (2, [(0, 1.0)]), (2, [(0, 2)]), (2, [(-1, 0)]), (2, [(1, 1)]),
])
def test_invalid_construction(n, edges):
    with pytest.raises(ValueError):
        SimpleGraph.from_edges(n, edges)


@pytest.mark.parametrize("adjacency", [({1}, set()), ({0},), ({2}, set()), ({True}, set())])
def test_direct_adjacency_validated(adjacency):
    with pytest.raises(ValueError):
        SimpleGraph(adjacency)


def test_immutable_graph_copies_mutable_input():
    rows = [{1}, {0}]
    graph = SimpleGraph(rows)
    rows[0].clear()
    assert graph.adjacency[0] == frozenset({1})
    with pytest.raises(FrozenInstanceError):
        graph.adjacency = ()


def test_numpy_integer_ids():
    graph = SimpleGraph.from_edges(np.int64(3), [(np.int64(0), np.int64(1))])
    assert graph.num_edges == 1


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_edge_list(tmp_path / "missing.edges")
