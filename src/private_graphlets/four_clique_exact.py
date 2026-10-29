"""NON-PRIVATE four-clique oracles and deterministic orientation utilities."""

from itertools import combinations
from collections.abc import Iterable, Sequence

from private_graphlets.graph import SimpleGraph, _nonnegative_integer


def validate_order(n: int, order: Sequence[int] | None = None) -> tuple[int, ...]:
    result = tuple(range(n)) if order is None else tuple(order)
    for vertex in result:
        _nonnegative_integer(vertex, "order vertex")
    if len(result) != n or set(result) != set(range(n)):
        raise ValueError("order must be a permutation of the public vertex set")
    return result


def ranks(order: Sequence[int]) -> tuple[int, ...]:
    order = validate_order(len(order), order)
    result = [0] * len(order)
    for i, v in enumerate(order):
        result[v] = i
    return tuple(result)


def validate_cap(cap: int, n: int) -> int:
    cap = _nonnegative_integer(cap, "cap")
    if cap > max(0, n - 1):
        raise ValueError("cap must not exceed n-1 (or zero for empty graphs)")
    return cap


def select_outgoing(vertex: int, neighbors: Iterable[int], rank: Sequence[int],
                    cap: int) -> tuple[int, ...]:
    """Local operation: only this vertex's incident list is needed; never release it."""
    return tuple(sorted((w for w in neighbors if rank[vertex] < rank[w]),
                        key=rank.__getitem__)[:cap])


def count_four_cliques(graph: SimpleGraph, order: Sequence[int] | None = None,
                       *, cap: int | None = None) -> int:
    """Exact forward-triple count; with a cap this is the retained-clique target."""
    rank = ranks(validate_order(graph.num_vertices, order))
    cap = max(0, graph.num_vertices-1) if cap is None else validate_cap(cap, graph.num_vertices)
    total = 0
    for v, neighbors in enumerate(graph.adjacency):
        selected = select_outgoing(v, neighbors, rank, cap)
        for a, b, c in combinations(selected, 3):
            total += b in graph.adjacency[a] and c in graph.adjacency[a] and c in graph.adjacency[b]
    return total


def count_four_cliques_bruteforce(graph: SimpleGraph) -> int:
    """Independent four-vertex enumeration, checking all six required edges."""
    return sum(all(v in graph.adjacency[u] for u, v in combinations(vertices, 2))
               for vertices in combinations(range(graph.num_vertices), 4))
