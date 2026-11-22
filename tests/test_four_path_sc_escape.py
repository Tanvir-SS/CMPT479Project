"""Small Stage 3 implementation checks, not a statistical or privacy audit."""

from dataclasses import asdict
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np
import pytest

from private_graphlets import four_path_sc_escape as sc
from private_graphlets.four_path_exact import count_four_paths_bruteforce
from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.randomized_response import rr_parameters
from private_graphlets.triangle_exact import count_triangles


FIXTURES = Path(__file__).resolve().parents[1] / "data/fixtures"
EXPECTED = json.loads((FIXTURES / "expected_counts.json").read_text())["cases"]
BUDGET = sc.SCEscapeBudget(degree=.2, rr=.3, product=.4, triangle=.5)


class RecordingNoise:
    def __init__(self, value=0.0):
        self.value = value
        self.calls = []

    def laplace(self, location, scale):
        self.calls.append((location, scale))
        return self.value


@pytest.mark.parametrize("name", EXPECTED)
def test_exact_escape_identity_on_small_fixtures(name):
    # Integer identity + independent four-distinct-vertex oracle. No native run
    # or ground-truth rewrite; existing cached fixture P4 truth is column 1.
    graph = load_edge_list(FIXTURES / f"{name}.edges")
    x = tuple(len(row) - 1 for row in graph.adjacency)
    directed_sum = sum(x[v] * sum(x[u] for u in row) for v, row in enumerate(graph.adjacency))
    assert directed_sum % 2 == 0
    expected = directed_sum // 2 - 3 * count_triangles(graph)
    assert expected == count_four_paths_bruteforce(graph) == EXPECTED[name][1]
    # Exercise the implemented local algebra with test-only exact degrees,
    # exact adjacency and p=0; these settings are not a private API mode.
    bits = tuple(j in row for i, row in enumerate(graph.adjacency) for j in range(i))
    zero = RecordingNoise()
    products = [sc.local_product_report(i, row, x, max(map(abs, x), default=0), .4, zero)
                for i, row in enumerate(graph.adjacency)]
    triangles = [sc.local_triangle_report(i, row, bits, 0., 0., zero)
                 for i, row in enumerate(graph.adjacency)]
    assert .5 * sum(products) - 3 * sum(triangles) == expected


def test_lower_rr_probability_threshold_and_one_owner_including_nonedges():
    epsilon = .7
    p = 1 / (math.exp(epsilon) + 1)
    assert sc.rr_parameters is rr_parameters
    assert rr_parameters(epsilon).flip_probability == pytest.approx(p)
    threshold = rr_parameters(epsilon).flip_probability

    class FixedUniform:
        calls = []

        def random(self, size):
            self.calls.append(size)
            return np.array([0., threshold, np.nextafter(1., 0.)][:size])

    graph = SimpleGraph.from_edges(4, [(0, 1), (0, 3), (2, 3)])
    rng = FixedUniform()
    rows = [sc.local_rr_lower_row(i, row, epsilon, rng) for i, row in enumerate(graph.adjacency)]
    assert rng.calls == [0, 1, 2, 3]
    assert rows == [(), (False,), (True, False), (False, False, True)]
    pairs = [(i, j) for i, row in enumerate(rows) for j in range(len(row))]
    assert len(pairs) == len(set(pairs)) == 6
    assert {tuple(sorted(pair)) for pair in pairs} == set(combinations(range(4), 2))


def test_exact_laplace_scales_and_local_algebra():
    rng = RecordingNoise(-.375)
    assert sc.local_degree_report(frozenset({0, 1}), .25, rng) == 1.625
    assert rng.calls == [(0., 4.)]  # 1/epsilon_D, never 2/epsilon_D.
    x = (-2., .5, 3., -1.)
    assert sc.local_product_report(0, frozenset({1, 2}), x, 3., .5, rng) == -7.375
    assert rng.calls[-1] == (0., 24.)  # 2*|-2|*3/.5.
    bits = (True, False, True, False, False, False)
    # All three lower neighbors: t=2, s=3. Upper neighbors are ignored.
    assert sc.local_triangle_report(3, frozenset({0, 1, 2, 4}), bits, .2, 8., rng) == 1.025
    assert rng.calls[-1] == (0., 8.)
    zero = RecordingNoise()
    assert sc.local_product_report(1, frozenset({0}), (2., 0.), 2., .5, zero) == 0.
    assert zero.calls == [(0., 0.)]


def test_triangle_centering_expectation_on_one_triangle():
    p = rr_parameters(.7).flip_probability
    # Only the (1,0) RR bit closes vertex 2's lower wedge. Two outcomes suffice.
    for actual_edge in (False, True):
        probability_one = 1 - p if actual_edge else p
        reports = [sc.local_triangle_report(2, frozenset({0, 1}), (bit, False, False),
                                            p, 0., RecordingNoise()) for bit in (False, True)]
        mean = (1 - probability_one) * reports[0] + probability_one * reports[1]
        assert mean / math.tanh(.7 / 2) == pytest.approx(float(actual_edge), abs=1e-15)


def test_budget_total_and_configurable_allocations():
    assert BUDGET.total == pytest.approx(1.6)
    assert sc.SCEscapeBudget(.1, .2, .3, .3).total == 1.
    assert sc.SCEscapeBudget(.25, .1, .2, .2).total == 1.


@pytest.mark.parametrize("field", ["degree", "rr", "product", "triangle"])
@pytest.mark.parametrize("value", [0., -1., True, float("nan"), float("inf")])
def test_invalid_budgets(field, value):
    values = asdict(BUDGET)
    values[field] = value
    with pytest.raises(ValueError):
        sc.SCEscapeBudget(**values)


def test_numeric_parameter_guards():
    for values in ((.1, 31., .1, .1), (1e308, 1., 1e308, 1e308),
                   (5e-324, 1., 1., 1.)):
        with pytest.raises(ValueError):
            sc.SCEscapeBudget(*values)
    with pytest.raises(FloatingPointError):
        sc.local_product_report(0, frozenset({1}), (1e308, 1e308), 1e308, 1., RecordingNoise())
    with pytest.raises(FloatingPointError):
        sc.local_degree_report(frozenset(), 1., RecordingNoise(float("inf")))
    with pytest.raises(FloatingPointError, match="sensitivity underflowed"):
        sc.local_product_report(0, frozenset(), (1e-300,), 1e-300, 1., RecordingNoise())


@pytest.mark.parametrize("n", [0, 1, 3, 5])
def test_seeded_small_graphs_isolates_and_safe_records(n):
    graph = SimpleGraph.from_edges(n, [(0, 1), (1, 0)] if n >= 2 else [])
    # Explicit public bound; never infer max(degree) for the caller.
    run = sc.simulate_sc_escape(graph, budget=BUDGET, public_max_degree=2, seed=3100 + n)
    assert run == sc.simulate_sc_escape(graph, budget=BUDGET, public_max_degree=2, seed=3100 + n)
    assert run.result == sc.estimate_sc_escape(graph, budget=BUDGET, public_max_degree=2,
                                              seed=np.int64(3100 + n))
    assert math.isfinite(run.result.estimate)
    transcript = asdict(run.transcript)
    assert set(transcript) == {"noisy_degrees", "rr_lower", "local_product_reports", "local_triangle_reports"}
    assert [len(transcript[k]) for k in transcript] == [n, n*(n-1)//2, n, n]
    assert all(type(bit) is bool for bit in run.transcript.rr_lower)
    record = run.result.to_dict()
    assert set(record) == {"schema_version", "result_type", "mechanism", "pattern", "count_semantics",
                           "target", "simulation_only", "privacy_status", "epsilon_total", "estimate",
                           "degree_product_estimate", "triangle_estimate", "num_vertices",
                           "public_max_degree", "budget"}
    assert record["privacy_status"] == "experimental_unverified"
    assert record["epsilon_total"] == BUDGET.total
    json.dumps(record, allow_nan=False)
    assert run.result.estimate == pytest.approx(run.result.degree_product_estimate - 3*run.result.triangle_estimate)


def test_two_round_public_schedule_streams_and_supplied_bound(monkeypatch):
    originals = {name: getattr(sc, name) for name in
                 ("local_degree_report", "local_rr_lower_row", "local_product_report", "local_triangle_report")}
    calls = []
    for name, function in originals.items():
        def spy(*args, _name=name, _function=function):
            calls.append((_name, args))
            return _function(*args)
        monkeypatch.setattr(sc, name, spy)
    for edges in ([], [(0, 1), (1, 2), (2, 0)]):
        calls.clear()
        streams = sc.sc_escape_streams(3109)
        graph = SimpleGraph.from_edges(4, edges)
        run = sc.simulate_sc_escape(graph, budget=BUDGET, public_max_degree=7, streams=streams)
        assert [name for name, args in calls] == [name for name in originals for _ in range(4)]
        for _, args in calls[8:12]:
            assert args[2] == tuple(d - 1 for d in run.transcript.noisy_degrees)
            assert args[-1] is streams.product
        for _, args in calls[12:]:
            assert args[2] is run.transcript.rr_lower  # Full broadcast, no neighbor queries.
            assert args[4] == 7 / BUDGET.triangle  # Explicit loose public bound retained.
            assert args[-1] is streams.triangle
        assert run.result.public_max_degree == 7


def test_negative_fractional_output_and_zero_public_bound(monkeypatch):
    streams = sc.sc_escape_streams(3110)
    monkeypatch.setattr(sc, "_laplace", lambda scale, rng: -.125 if rng is streams.product else 0.)
    result = sc.estimate_sc_escape(SimpleGraph.from_edges(4, []), budget=BUDGET,
                                   public_max_degree=0, streams=streams)
    assert result.estimate == -.25
    assert result.triangle_estimate == 0.


def test_zero_scale_sampler():
    assert sc._laplace(0., np.random.default_rng(3111)) == 0.


@pytest.mark.parametrize("bound", [-1, True, 1.5, None, 0])
def test_bound_validation_before_sampling(bound, monkeypatch):
    monkeypatch.setattr(sc, "sc_escape_streams", lambda *args: pytest.fail("invalid bound sampled"))
    with pytest.raises(ValueError):
        sc.estimate_sc_escape(SimpleGraph.from_edges(2, [(0, 1)]), budget=BUDGET,
                              public_max_degree=bound, seed=1)


def test_explicit_bound_required_and_rng_contracts():
    graph = SimpleGraph.from_edges(2, [])
    with pytest.raises(TypeError):
        sc.estimate_sc_escape(graph, budget=BUDGET, seed=1)
    for seed in (-1, True, 1.5):
        with pytest.raises(ValueError):
            sc.sc_escape_streams(seed)
    streams = sc.sc_escape_streams(3112)
    with pytest.raises(ValueError):
        sc.estimate_sc_escape(graph, budget=BUDGET, public_max_degree=1, seed=1, streams=streams)
    with pytest.raises(ValueError):
        sc.SCEscapeStreams(streams.degree, streams.degree, streams.product, streams.triangle)
    # Drawing from S must not advance T (or either Round 1 stream).
    fresh = sc.sc_escape_streams(3112)
    streams.product.laplace(size=10)
    assert streams.triangle.random() == fresh.triangle.random()
    assert streams.degree.random() == fresh.degree.random()
    assert streams.rr.random() == fresh.rr.random()
