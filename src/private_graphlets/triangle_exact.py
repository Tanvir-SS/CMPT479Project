"""Non-private exact triangle counting on validated simple undirected graphs."""

from private_graphlets.graph import SimpleGraph


def count_triangles(graph: SimpleGraph) -> int:
    """Count each triangle once, at its unique vertex ordering u < v < w.

    With expected constant-time set membership, work is
    O(n + m + sum_{uv in E} min(d(u), d(v))); worst case O(n^3).
    A temporary intersection uses O(maximum degree) auxiliary space.
    Counts use Python integers; adjacency is never modified.
    """
    total = 0
    for u, neighbors in enumerate(graph.adjacency):
        for v in neighbors:
            if u < v:
                total += sum(w > v for w in neighbors & graph.adjacency[v])
    return total
