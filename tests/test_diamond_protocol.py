"""Protocol fidelity, reconstruction and small seeded moment diagnostics."""

from dataclasses import asdict, replace
import importlib.util
from itertools import combinations, product
import json
import math
from pathlib import Path

import numpy as np
import pytest

from private_graphlets import diamond as d
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import kcore_order
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper


def clique(n=4):
    return SimpleGraph.from_edges(n, combinations(range(n), 2))


def test_default_and_explicit_budgets_replay_and_only_transcript_reconstruction():
    for budget in (d.allocate_budget(3), d.DiamondBudget(4, .5, 1.5, 2)):
        run = d.simulate_diamonds(clique(), budget.total, cap=3, budget=budget, seed=2420)
        assert run == d.simulate_diamonds(clique(), budget.total, cap=3, budget=budget, seed=2420)
        assert run.result == d.estimate_diamonds(clique(), budget.total, cap=3, budget=budget, seed=2420)
        assert run.result.estimate == d.aggregate_diamonds(run.transcript)
        assert run.transcript.budget == budget
        assert math.fsum((budget.ordering, budget.rr, budget.wedge)) == budget.total
        assert run.transcript.ordering == kcore_order(clique(), budget.ordering, d._simulation_streams(2420)[0])
    assert run != d.simulate_diamonds(clique(), 4, cap=3, budget=budget, seed=2421)


@pytest.mark.parametrize("bad", [0, -1, True, "1", float("nan"), float("inf"), 1e-310])
def test_invalid_epsilon(bad):
    with pytest.raises((ValueError, OverflowError)):
        d.simulate_diamonds(clique(), bad, cap=3, seed=1)


def test_invalid_public_configuration_and_malformed_reports():
    for cap in (0, 1, -1, True, 2.5):
        with pytest.raises(ValueError):
            d.simulate_diamonds(clique(), 3, cap=cap)
    for seed in (-1, True, 1.5):
        with pytest.raises(ValueError):
            d.simulate_diamonds(clique(), 3, cap=3, seed=seed)
    for values in [(3, 0, 1, 2), (3, 1, 0, 2), (3, 1, 2, 0),
                   (3, 1, 1, 1 + 1e-14), (3, 1.1, .9, 1)]:
        with pytest.raises(ValueError):
            d.DiamondBudget(*values)
    with pytest.raises(ValueError, match="explicit budget"):
        d.allocate_budget(4)  # no silent min(epsilon/3,1) redistribution
    with pytest.raises(ValueError, match="budget total"):
        d.simulate_diamonds(clique(), 2, cap=3, budget=d.allocate_budget(3))
    t = d.simulate_diamonds(clique(), 3, cap=3, seed=2422).transcript
    for broken in (replace(t, rr_upper=t.rr_upper[:-1]), replace(t, wedge_reports=t.wedge_reports[:-1]),
                   replace(t, wedge_reports=((0.,),) + t.wedge_reports[1:]),
                   replace(t, ordering=replace(t.ordering, ordering_type="nonprivate_kcore_oracle"))):
        with pytest.raises(ValueError):
            d.aggregate_diamonds(broken)


def test_public_parameters_exact_scale_variances_and_weight():
    for cap in (2, 3, 7):
        for epsilon in (.25, 1, 2):
            p = d.hybrid_parameters(cap, epsilon, epsilon)
            v = math.exp(epsilon) / math.expm1(epsilon)**2
            assert p.sensitivity == 2 * (cap - 1)
            assert p.scale == 2 * (cap - 1) / epsilon
            assert p.rr_product_variance_bound == pytest.approx(2*v + v*v)
            assert p.wedge_variance == 2*p.scale*p.scale
            assert p.rr_weight == pytest.approx(p.wedge_variance / (2*v + v*v + p.wedge_variance))


def test_reconstruction_matches_explicit_outer_pairs_not_choose_of_noisy_sum():
    run = d.simulate_diamonds(clique(5), 3, cap=2, seed=2423)
    t = run.transcript
    w = rr_matrix(5, t.rr_upper, t.budget.rr)
    lookup = [dict(zip(row, values)) for row, values in zip(d.wedge_requests(t.ordering.order), t.wedge_reports)]
    lam = run.result.rr_weight
    explicit = 0.
    for a, b in combinations(range(5), 2):
        values = [(lam*w[a,c]*w[b,c] + (1-lam)*lookup[c][a,b]
                   if (a,b) in lookup[c] else w[a,c]*w[b,c])
                  for c in range(5) if c not in (a, b)]
        explicit += w[a,b] * sum(x*y for x,y in combinations(values, 2))
    assert run.result.estimate == pytest.approx(explicit, rel=1e-12)
    # Nonbinary signed example: pair product=-1/8, choose(sum,2)=-3/32.
    assert ((.5-.25)**2 - (.5**2 + (-.25)**2))/2 == -.125


def test_all_rr_tables_integrate_to_fractional_clipped_and_exact_unclipped_targets():
    # R=log(2): W is {-1,2}, flip=1/3. Integrate all 64 pair-report tables.
    # Wedge noises integrate to their means since products use distinct rows.
    edges = tuple(combinations(range(4), 2))
    for mask in (0, 31, 63):
        graph = SimpleGraph.from_edges(4, [e for i,e in enumerate(edges) if mask >> i & 1])
        exact = np.array([[int(v in row) for v in range(4)] for row in graph.adjacency])
        for cap in (2, 3):
            requests = d.wedge_requests(tuple(range(4)))
            y = tuple(tuple(d._local_wedge_indicators(v, row, tuple(range(4)), cap, requests[v]))
                      for v,row in enumerate(graph.adjacency))
            expected = d._reconstruct_diamonds(tuple(range(4)), exact, y, .5)
            summed = 0.
            for bits in product((False, True), repeat=6):
                probability = math.prod(2/3 if bit == bool(mask >> i & 1) else 1/3
                                        for i,bit in enumerate(bits))
                summed += probability*d._reconstruct_diamonds(tuple(range(4)),
                              rr_matrix(4, bits, math.log(2)), y, .5)
            assert summed == pytest.approx(expected, abs=2e-13)


def test_primitive_rr_and_wedge_moments_with_standard_error_tolerances():
    n_samples = 20_000
    rng = np.random.default_rng(2430)
    epsilon = math.log(3)
    params = rr_parameters(epsilon)
    graph = SimpleGraph.from_edges(4, [(0, 1), (0, 2)])
    bits = np.array([sample_rr_upper(graph, epsilon, rng) for _ in range(n_samples)])
    weights = np.where(bits, params.maximum, -params.a)
    truth = np.array([1, 1, 0, 0, 0, 0])
    assert np.all(abs(weights.mean(axis=0)-truth) < 6*math.sqrt(params.variance/n_samples))
    covariance = np.cov(weights, rowvar=False, ddof=1)
    assert np.max(abs(covariance - np.diag(np.diag(covariance)))) < 6*params.variance/math.sqrt(n_samples)
    requests = d.wedge_requests((0, 1, 2, 3))[0]
    scale = 2.
    samples = np.array([d.local_wedge_reports(0, graph.adjacency[0], (0,1,2,3), 2,
                                              requests, scale, rng) for _ in range(n_samples)])
    assert np.all(abs(samples.mean(axis=0)-[1, 0, 0]) < 6*math.sqrt(2*scale**2/n_samples))
    # Laplace fourth moment=24b^4, asymptotic SE(sample variance)=sqrt(20b^4/N).
    assert np.all(abs(samples.var(axis=0, ddof=1)-2*scale**2) < 6*math.sqrt(20*scale**4/n_samples))
    cov = np.cov(samples, rowvar=False, ddof=1)
    assert np.max(abs(cov-np.diag(np.diag(cov)))) < 6*2*scale**2/math.sqrt(n_samples)


def test_small_full_protocol_mean_no_clipping_and_signed_fractional_results():
    # Two tiny graphs, 600 trials each; no standardized-dataset evaluation.
    # Six estimated standard errors is a conservative, finite diagnostic, not a proof.
    summaries = []
    budget = d.DiamondBudget(9, 1, 4, 4)
    for graph, truth, master in ((clique(), 6, 2440), (SimpleGraph.from_edges(4, []), 0, 2441)):
        seeds = np.random.SeedSequence(master).spawn(600)
        values = np.array([d.estimate_diamonds(graph, 9, cap=3, budget=budget,
                            seed=int(seed.generate_state(1, dtype=np.uint64)[0])).estimate for seed in seeds])
        se = values.std(ddof=1)/math.sqrt(len(values))
        assert abs(values.mean()-truth) < 6*se
        assert np.any(values < 0) and np.any(values != np.rint(values))
        summaries.append(dict(truth=truth, trials=len(values), mean=float(values.mean()),
                              standard_error=float(se), negatives=int((values < 0).sum())))
    folder = Path(__file__).resolve().parents[1] / "build/phase24"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "statistical_sanity.json").write_text(json.dumps(summaries, indent=2) + "\n")


def test_small_universes_and_larger_public_cap():
    for n in range(4):
        run = d.simulate_diamonds(SimpleGraph.from_edges(n, []), 3, cap=2, seed=2450)
        assert len(run.transcript.rr_upper) == math.comb(n, 2)
        assert sum(map(len, run.transcript.wedge_reports)) == math.comb(n, 3)
        assert run.result.estimate == 0
    run = d.simulate_diamonds(clique(), 3, cap=10, seed=2450)
    assert run.result.wedge_noise_scale == 18  # no secret effective-cap substitution


def test_single_estimate_cli(capsys):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("diamond_cli", root / "scripts/estimate_diamonds.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    assert cli.main([str(root / "data/fixtures/diamond.edges"), "--epsilon", "3", "--cap", "3",
                     "--seed", "2460"]) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["pattern"] == "diamond" and record["privacy_status"] == "experimental_unverified"
    assert not {"seed", "count", "num_edges", "degrees", "graph"}.intersection(record)
