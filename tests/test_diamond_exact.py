"""Independent exact and native checks; all unprotected oracles stay in tests."""

from dataclasses import asdict
from itertools import combinations
import json
from math import comb
from pathlib import Path

import numpy as np
import pytest

from private_graphlets import diamond as d
from private_graphlets.diamond_exact import count_diamonds
from private_graphlets.four_clique_exact import ranks
from private_graphlets.graph import SimpleGraph, load_edge_list

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data/fixtures"
EXPECTED = json.loads((FIXTURES / "expected_counts.json").read_text())["cases"]


def brute_force(graph):
    """Four-set enumeration; six choices of degree-three central pair, extra edge allowed."""
    total = 0
    for vertices in combinations(range(graph.num_vertices), 4):
        for a, b in combinations(vertices, 2):
            outer = set(vertices) - {a, b}
            total += (b in graph.adjacency[a]
                      and all(c in graph.adjacency[a] and c in graph.adjacency[b] for c in outer))
    return total


def noiseless_inputs(graph, order, cap):
    """Strictly test-only; no deterministic/no-noise option exists in the mechanism."""
    weights = np.array([[float(b in row) for b in range(graph.num_vertices)]
                        for row in graph.adjacency]).reshape(graph.num_vertices, graph.num_vertices)
    requests = d.wedge_requests(order)
    reports = tuple(tuple(d._local_wedge_indicators(v, row, ranks(order), cap, requests[v]))
                    for v, row in enumerate(graph.adjacency))
    return weights, reports


def check_native(graph, name, escape_adapter):
    native = escape_adapter.run(graph)
    folder = ROOT / "build/phase24/native"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps(asdict(native), indent=2) + "\n")
    truth = native.counts.connected_four["diamond"]
    assert count_diamonds(graph) == brute_force(graph) == truth
    orders = [tuple(range(graph.num_vertices)), tuple(reversed(range(graph.num_vertices))),
              tuple(int(v) for v in np.random.default_rng(2401).permutation(graph.num_vertices))]
    for order in orders:
        for weight in (.125, .5, .875):
            weights, reports = noiseless_inputs(graph, order, max(2, graph.num_vertices - 1))
            assert d._reconstruct_diamonds(order, weights, reports, weight) == truth
    return truth


@pytest.mark.escape_integration
@pytest.mark.parametrize("name", EXPECTED)
def test_eight_fixtures_against_native_and_deterministic_reconstruction(name, escape_adapter):
    graph = load_edge_list(FIXTURES / f"{name}.edges")
    assert check_native(graph, name, escape_adapter) == EXPECTED[name][4]


@pytest.mark.escape_integration
@pytest.mark.parametrize("seed", range(6))
def test_small_seeded_graphs_against_native(seed, escape_adapter):
    n = 4 + seed % 5
    rng = np.random.default_rng(2410 + seed)
    graph = SimpleGraph.from_edges(n, [e for e in combinations(range(n), 2) if rng.random() < .55])
    check_native(graph, f"random_{seed}", escape_adapter)


@pytest.mark.parametrize("outer", range(7))
def test_book_graph(outer):
    graph = SimpleGraph.from_edges(outer + 2, [(0, 1)] + [(v, u) for v in range(2, outer + 2)
                                                       for u in (0, 1)])
    assert count_diamonds(graph) == brute_force(graph) == comb(outer, 2)


def test_exhaustive_four_vertex_graphs_and_empty_universes():
    edges = tuple(combinations(range(4), 2))
    for mask in range(64):
        graph = SimpleGraph.from_edges(4, [e for i, e in enumerate(edges) if mask >> i & 1])
        assert count_diamonds(graph) == brute_force(graph)
    for n in range(4):
        graph = SimpleGraph.from_edges(n, [])
        assert count_diamonds(graph) == 0
        w, y = noiseless_inputs(graph, tuple(range(n)), 2)
        assert d._reconstruct_diamonds(tuple(range(n)), w, y, .5) == 0


def test_hybrid_clipping_target_is_fractional_not_retained_diamond_count():
    graph = load_edge_list(FIXTURES / "clique.edges")
    for cap in (2, 3):  # n-1=3
        weights, reports = noiseless_inputs(graph, (0, 1, 2, 3), cap)
        value = d._reconstruct_diamonds((0, 1, 2, 3), weights, reports, .25)
        assert value == (4.5 if cap == 2 else 6)
    # Both outer common-neighbor wedges clipped: a particular diamond gets lambda².
    clique5 = SimpleGraph.from_edges(5, combinations(range(5), 2))
    weights, reports = noiseless_inputs(clique5, tuple(range(5)), 2)
    assert reports[0][d.wedge_requests(tuple(range(5)))[0].index((3, 4))] == 0
    assert reports[1][d.wedge_requests(tuple(range(5)))[1].index((3, 4))] == 0
    for cap in (2, 3, 4):
        weights, reports = noiseless_inputs(clique5, tuple(range(5)), cap)
        value = d._reconstruct_diamonds(tuple(range(5)), weights, reports, .25)
        # Independent central-edge/outer-pair target with explicit per-wedge weights.
        selected = {v: set(range(v + 1, 5)) & set(range(v + 1, v + cap + 1)) for v in range(5)}
        expected = 0
        for a, b in combinations(range(5), 2):
            for c, e in combinations(set(range(5)) - {a, b}, 2):
                factors = [(.25 if v < min(a, b) and not {a, b} <= selected[v] else 1.)
                           for v in (c, e)]
                expected += factors[0] * factors[1]
        assert value == expected
        assert value <= count_diamonds(clique5) == 30
        if cap == 4:
            assert value == 30
