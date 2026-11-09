"""NON-PRIVATE C4 evaluation helper; never part of a mechanism transcript."""

from itertools import combinations
from math import comb

from private_graphlets.graph import SimpleGraph


def count_four_cycles(graph: SimpleGraph) -> int:
    """Each pair of common neighbors closes a cycle; two opposite pairs/cycle.

    Python integer arithmetic; extra chords are allowed (K4 contributes three).
    """
    return sum(comb(len(graph.adjacency[u] & graph.adjacency[v]), 2)
               for u, v in combinations(range(graph.num_vertices), 2)) // 2
