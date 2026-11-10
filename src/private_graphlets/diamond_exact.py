"""NON-PRIVATE diamond oracle, separate from all private protocol execution."""

from math import comb

from private_graphlets.graph import SimpleGraph


def count_diamonds(graph: SimpleGraph) -> int:
    """Sum C(|N(a) intersect N(b)|,2) over actual edges a<b.

    Counts non-induced unlabeled edge-subgraphs: a K4 contains six diamonds.
    Python integers avoid fixed-width counting overflow.
    """
    return sum(comb(len(neighbors & graph.adjacency[b]), 2)
               for a, neighbors in enumerate(graph.adjacency) for b in neighbors if a < b)
