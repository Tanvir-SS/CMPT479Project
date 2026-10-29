"""Non-private ground-truth counters, separate from mechanism releases."""

from itertools import combinations
from math import comb

from private_graphlets.graph import SimpleGraph


def count_three_stars(graph: SimpleGraph) -> int:
    """Count non-induced K1,3 copies by sum_v C(d(v), 3), using Python integers."""
    return sum(comb(len(neighbors), 3) for neighbors in graph.adjacency)


def count_three_stars_bruteforce(graph: SimpleGraph) -> int:
    """Independent small-graph oracle: enumerate 4-sets and each possible center.

    Test the three required edges directly, without degree/binomial identities.
    Extra leaf edges are ignored. Runtime is O(n^4); intended only for tiny graphs.
    """
    count = 0
    for vertices in combinations(range(graph.num_vertices), 4):
        for center in vertices:
            if all(leaf in graph.adjacency[center] for leaf in vertices if leaf != center):
                count += 1
    return count
