"""Non-private non-induced P4 counters (ESCAPE's three-edge '3-path')."""

from itertools import permutations

from private_graphlets.graph import SimpleGraph
from private_graphlets.triangle_exact import count_triangles


def count_four_paths(graph: SimpleGraph) -> int:
    """Count undirected paths on four distinct vertices using exact integers.

    Each middle edge contributes (d(u)-1)(d(v)-1). Coincident outer
    vertices contribute once per triangle edge, so subtract 3*T.
    Additional host edges are allowed. Work is O(n+m) plus triangle counting;
    auxiliary space is O(n) including degrees and temporary intersections.
    """
    degrees = tuple(len(neighbors) for neighbors in graph.adjacency)
    products = sum(
        (degrees[u] - 1) * (degrees[v] - 1)
        for u, neighbors in enumerate(graph.adjacency)
        for v in neighbors if u < v
    )
    return products - 3 * count_triangles(graph)


def count_four_paths_bruteforce(graph: SimpleGraph) -> int:
    """Small-graph oracle: enumerate distinct ordered quadruples, divide by two.

    Checks only the three path edges, independently of degrees and triangles.
    Reversal is the only duplicate representation of each undirected path.
    Expected O(n^4) work; O(n) iterator storage, without materializing paths.
    """
    adjacency = graph.adjacency
    directed = sum(
        b in adjacency[a] and c in adjacency[b] and d in adjacency[c]
        for a, b, c, d in permutations(range(graph.num_vertices), 4)
    )
    return directed // 2
