"""Compare degree counts with a structurally independent four-vertex oracle."""

from itertools import combinations

import pytest

from private_graphlets.exact import count_three_stars, count_three_stars_bruteforce
from private_graphlets.graph import SimpleGraph


CASES = [
    ("empty", 0, [], 0),
    ("isolates", 7, [], 0),
    ("P4", 4, [(0, 1), (1, 2), (2, 3)], 0),
    ("K3", 3, list(combinations(range(3), 2)), 0),
    ("K1,3", 4, [(0, i) for i in range(1, 4)], 1),
    ("K1,4", 5, [(0, i) for i in range(1, 5)], 4),
    ("K4", 4, list(combinations(range(4), 2)), 4),
    ("K5", 5, list(combinations(range(5), 2)), 20),
    ("adjacent_centers", 6, [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5)], 2),
    ("K2,4", 6, [(u, v) for u in range(2) for v in range(2, 6)], 8),
    ("wheel", 5, [(0, i) for i in range(1, 5)] + [(1, 2), (2, 3), (3, 4), (4, 1)], 8),
    ("K4_star_isolates", 10, list(combinations(range(4), 2)) + [(4, 5), (4, 6), (4, 7)], 5),
]


@pytest.mark.parametrize("name,n,edges,expected", CASES, ids=[case[0] for case in CASES])
def test_known_counts(name, n, edges, expected):
    graph = SimpleGraph.from_edges(n, edges)
    assert count_three_stars(graph) == expected
    assert count_three_stars_bruteforce(graph) == expected
    assert type(count_three_stars(graph)) is int
    reversed_labels = SimpleGraph.from_edges(n, [(n - 1 - u, n - 1 - v) for u, v in edges])
    assert count_three_stars(reversed_labels) == expected


@pytest.mark.parametrize("n", range(6))
def test_every_labeled_simple_graph_through_five_vertices(n):
    pairs = list(combinations(range(n), 2))
    for mask in range(1 << len(pairs)):
        graph = SimpleGraph.from_edges(n, [edge for i, edge in enumerate(pairs) if mask & (1 << i)])
        assert count_three_stars(graph) == count_three_stars_bruteforce(graph), (n, mask)


def test_leaf_edges_do_not_invalidate_noninduced_star():
    star = SimpleGraph.from_edges(4, [(0, 1), (0, 2), (0, 3)])
    tail = SimpleGraph.from_edges(4, [(0, 1), (0, 2), (0, 3), (1, 2)])
    clique = SimpleGraph.from_edges(4, combinations(range(4), 2))
    assert [count_three_stars(g) for g in (star, tail, clique)] == [1, 1, 4]
