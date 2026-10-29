"""NON-PRIVATE combinatorial/algebraic evidence for the phase-05 design.

No private ordering, randomized-response sampler, or private 4-clique estimator
is implemented here. Finite weighted-table checks are exact rational algebra.
"""

import argparse
from fractions import Fraction
import hashlib
from itertools import combinations, permutations, product
import json
import math
from pathlib import Path
import random

import networkx as nx

from private_graphlets.escape import EscapeAdapter, build_count_four
from private_graphlets.graph import SimpleGraph


def outgoing(graph, order):
    rank = {v: i for i, v in enumerate(order)}
    return [set(w for w in row if rank[v] < rank[w]) for v, row in enumerate(graph.adjacency)]


def brute_cliques(graph):
    return sum(all(v in graph.adjacency[u] for u, v in combinations(vertices, 2))
               for vertices in combinations(range(graph.num_vertices), 4))


def triple_count(graph, out):
    return sum(all(b in graph.adjacency[a] for a, b in combinations(leaves, 2))
               for row in out for leaves in combinations(sorted(row), 3))


def diamond_count(graph, out):
    return sum(b in graph.adjacency[a]
               for u, row in enumerate(out) for v in row
               for a, b in combinations(sorted(row & out[v]), 2))


def peeling_order(graph):
    # Exact NON-PRIVATE order used only as an oracle/input to the identity test.
    remaining = set(range(graph.num_vertices))
    order = []
    while remaining:
        v = min(remaining, key=lambda u: (len(graph.adjacency[u] & remaining), u))
        order.append(v)
        remaining.remove(v)
    return tuple(order)


def cases():
    for n in range(6):
        possible = list(combinations(range(n), 2))
        for mask in range(1 << len(possible)):
            graph = SimpleGraph.from_edges(n, [edge for i, edge in enumerate(possible) if mask & (1 << i)])
            yield f"exhaustive_n{n}_mask{mask}", graph, {"family": "exhaustive", "n": n, "mask": mask}
    book = nx.complete_graph(3)
    book.add_edges_from((v, w) for v in range(3, 7) for w in range(3))
    isolates = nx.complete_graph(4)
    isolates.add_nodes_from(range(4, 8))
    examples = [
        ("K6", nx.complete_graph(6)), ("K7", nx.complete_graph(7)),
        ("star_n8", nx.star_graph(7)), ("path_n8", nx.path_graph(8)),
        ("book_four_centers", book), ("K4_four_isolates", isolates),
        ("K33", nx.complete_bipartite_graph(3, 3)), ("cycle_n6", nx.cycle_graph(6)),
        ("ER_n8_p04_seed5001", nx.gnp_random_graph(8, 0.4, seed=5001)),
        ("ER_n10_p07_seed5002", nx.gnp_random_graph(10, 0.7, seed=5002)),
        ("BA_n10_m3_seed5003", nx.barabasi_albert_graph(10, 3, seed=5003)),
        ("SBM_n10_seed5004", nx.stochastic_block_model([5,5], [[0.6,0.2],[0.2,0.6]], seed=5004)),
    ]
    for name, graph in examples:
        yield name, SimpleGraph.from_edges(len(graph), graph.edges()), {"family": "named", "name": name}


def algebra_checks():
    # At eta=log(2), p=1/3 and the adjusted weights are exactly -1 and 2.
    expected_products = []
    for true_bits in product((0, 1), repeat=3):
        expectation = Fraction(0)
        for reports in product((0, 1), repeat=3):
            probability = math.prod(Fraction(2 if x == a else 1, 3)
                                    for a, x in zip(true_bits, reports))
            expectation += probability * math.prod(3*x-1 for x in reports)
        assert expectation == math.prod(true_bits)
        expected_products.append({"true_bits": true_bits, "expected_product": int(expectation)})
    leaves = range(1, 5)
    pairs = list(combinations(leaves, 2))
    maxima = {B: 0 for B in range(5)}
    comparisons = 0
    for reports in product((0, 1), repeat=len(pairs)):
        weights = dict(zip(pairs, (3*x-1 for x in reports)))
        for mask in range(16):
            neighbors = {v for v in leaves if mask & (1 << (v-1))}
            for new_vertex in set(leaves) - neighbors:
                for B in range(5):
                    old = sorted(neighbors)[:B]
                    new = sorted(neighbors | {new_vertex})[:B]
                    def score(vertices):
                        return sum(math.prod(weights[edge] for edge in combinations(triple, 2))
                                   for triple in combinations(vertices, 3))
                    difference = abs(score(new) - score(old))
                    bound = 0 if B < 3 else math.comb(B-1, 2)*12  # M²(M+a)=2²(2+1)
                    assert difference <= bound
                    maxima[B] = max(maxima[B], difference)
                    comparisons += 1
    graph = SimpleGraph.from_edges(5, combinations(range(5), 2))
    full = outgoing(graph, range(5))
    capped = {B: triple_count(graph, [set(sorted(row)[:B]) for row in full]) for B in (2,3,4)}
    assert capped == {2:0, 3:2, 4:5}
    # One erroneous shared coin for three absent edges gives E[W^3]=2, not 0.
    shared_coin = Fraction(2,3)*(-1)**3 + Fraction(1,3)*2**3
    assert shared_coin == 2
    return {"rr_product_cases": expected_products,
            "shared_coin_absent_triangle_expected_product": int(shared_coin),
            "sensitivity_neighbor_comparisons": comparisons,
            "max_observed_sensitivity_at_eta_log2": maxima,
            "K5_cap_counts": capped,
            "independent_endpoint_coin_K4_expected_count": "4*(1/2)^3 = 1/2"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--escape-root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("build/phase05/design_checks.json"))
    parser.add_argument("--summary", type=Path, default=Path("build/phase05/design_summary.json"))
    args = parser.parse_args()
    binary = build_count_four(args.escape_root, build_dir="build/phase05/escape")
    adapter = EscapeAdapter(binary)
    rows, order_checks = [], 0
    for name, graph, parameters in cases():
        truth = brute_cliques(graph)
        run = adapter.run(graph)
        escape_count = run.counts.connected_four["4-clique"]
        assert escape_count == truth, (name, truth, escape_count)
        if graph.num_vertices <= 5:
            orders = permutations(range(graph.num_vertices))
        else:
            ids = tuple(range(graph.num_vertices))
            shuffled = list(ids)
            random.Random(2026102905).shuffle(shuffled)
            orders = [ids, ids[::-1], tuple(sorted(ids, key=lambda v: (len(graph.adjacency[v]), v))),
                      peeling_order(graph), tuple(shuffled), tuple(sorted(ids, key=lambda v: ((7*v)%3,v)))]
        checked = 0
        for order in orders:
            out = outgoing(graph, order)
            assert triple_count(graph, out) == diamond_count(graph, out) == truth, (name, order)
            checked += 1
        order_checks += checked
        rows.append({"case": name, "parameters": parameters, "n": graph.num_vertices,
                     "m": graph.num_edges, "bruteforce_K4": truth, "escape_K4": escape_count,
                     "orders_checked": checked, "input": run.input_text,
                     "escape_output": run.output_text, "stdout": run.stdout, "stderr": run.stderr})
    report = {"result_type": "nonprivate_design_validation", "status": "passed",
              "graph_cases": len(rows), "order_checks": order_checks,
              "private_ordering_executed": False, "private_estimator_implemented": False,
              "build": json.loads((binary.parent / "build.json").read_text()),
              "cases": rows, "algebra": algebra_checks()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    summary = {key:value for key,value in report.items() if key not in ("cases", "build")}
    summary.update(raw_report=str(args.output), raw_report_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   named_graphs=[{key:row[key] for key in ("case","n","m","escape_K4","orders_checked")}
                                 for row in rows if row["parameters"]["family"] != "exhaustive"],
                   executable_sha256=report["build"]["executable_sha256"])
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"PASS: {len(rows)} actual ESCAPE comparisons; {order_checks} order checks; "
          f"{report['algebra']['sensitivity_neighbor_comparisons']} finite sensitivity checks")


if __name__ == "__main__":
    main()
