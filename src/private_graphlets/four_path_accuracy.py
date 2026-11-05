"""NON-PRIVATE EVALUATION: ideal MSE using true graphs, degrees and triangles.

Never imported by private release modules. All outputs are sensitive evaluation
records, not LEDP releases. Formulas assume ideal independent stage randomness.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from itertools import combinations
import math

import numpy as np

from private_graphlets.four_clique import cap_from_reports, local_cap_report
from private_graphlets.four_clique_exact import ranks, select_outgoing, validate_cap, validate_order
from private_graphlets.four_path import FourPathBudget
from private_graphlets.graph import SimpleGraph
from private_graphlets.kcore import KCoreConfig, kcore_order
from private_graphlets.noise import validate_epsilon
from private_graphlets.randomized_response import rr_parameters
from private_graphlets.triangle import triangle_sensitivity
from private_graphlets.triangle_exact import count_triangles


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise FloatingPointError('analytical evaluation exceeds finite float64 range')
    return value


def _degree_terms(graph: SimpleGraph, budget: FourPathBudget):
    if not isinstance(graph, SimpleGraph) or not isinstance(budget, FourPathBudget):
        raise ValueError('expected SimpleGraph and FourPathBudget')
    t = tuple(len(row)-1 for row in graph.adjacency)
    scale = _finite(2 / validate_epsilon(budget.degree))
    s = _finite(2*scale*scale)
    h = rr_parameters(budget.rr).variance
    g = tuple(sum(t[u] for u in row) for row in graph.adjacency)
    degree = _finite(s*sum(x*x for x in g) + s*s*graph.num_edges)
    rr = _finite(h*math.fsum((t[u]*t[u]+s)*(t[v]*t[v]+s)
                           for u, v in combinations(range(graph.num_vertices), 2)))
    return t, s, h, degree, rr


def degree_product_variance(graph: SimpleGraph, budget: FourPathBudget) -> float:
    """Ideal unconditional Var(Ahat); exact graph access, evaluation only."""
    _, _, _, degree, rr = _degree_terms(graph, budget)
    return _finite(degree+rr)


def closing_edge_multiplicities(graph: SimpleGraph, order: Sequence[int],
                                cap: int) -> dict[tuple[int, int], int]:
    """Sparse exact c_uv map; missing pairs have coefficient zero (including nonedges)."""
    rank = ranks(validate_order(graph.num_vertices, order))
    cap = validate_cap(cap, graph.num_vertices)
    counts = {}
    for v, row in enumerate(graph.adjacency):
        selected = select_outgoing(v, row, rank, cap)
        for a, b in combinations(selected, 2):
            pair = (min(a, b), max(a, b))
            counts[pair] = counts.get(pair, 0)+1
    return counts


def retained_triangle_count(graph: SimpleGraph, order: Sequence[int], cap: int) -> int:
    """Exact NON-PRIVATE retained target; not the original triangle count."""
    return sum(c for (u, v), c in closing_edge_multiplicities(graph, order, cap).items()
               if v in graph.adjacency[u])


@dataclass(frozen=True)
class ConditionalMSE:
    degree_noise: float
    rr_unadjusted: float
    shared_rr_adjustment: float  # Signed -6*Cov, NOT a nonnegative variance.
    triangle_laplace: float
    truncation_squared_error: float
    rr_compact: float
    variance: float
    bias: float
    mse: float
    degree_product_variance: float
    shared_rr_covariance: float
    original_triangles: int
    retained_triangles: int
    missed_triangles: int
    cap: int

    def to_dict(self) -> dict:
        return {'result_type': 'nonprivate_accuracy_evaluation', **asdict(self)}


def conditional_four_path_mse(graph: SimpleGraph, budget: FourPathBudget,
                              order: Sequence[int], cap: int) -> ConditionalMSE:
    """Exact ideal conditional MSE relative to ORIGINAL P4, for fixed G,O,B."""
    if not isinstance(budget, FourPathBudget):
        raise ValueError('expected FourPathBudget')
    c = closing_edge_multiplicities(graph, order, cap)
    t, s, h, degree, rr_a = _degree_terms(graph, budget)
    covariance = _finite(h*sum(value*t[u]*t[v] for (u, v), value in c.items()))
    rr_t = _finite(9*h*sum(value*value for value in c.values()))
    rr_compact = _finite(h*math.fsum(
        (t[u]*t[v]-3*c.get((u, v), 0))**2+s*(t[u]**2+t[v]**2)+s*s
        for u, v in combinations(range(graph.num_vertices), 2)))
    scale = _finite(triangle_sensitivity(cap, budget.rr)/budget.count)
    laplace = _finite(18*graph.num_vertices*scale*scale)
    total = count_triangles(graph)
    retained = sum(value for (u, v), value in c.items() if v in graph.adjacency[u])
    missed = total-retained
    if missed < 0:
        raise AssertionError('retained triangle count exceeds original')
    bias = float(3*missed)
    squared = _finite(bias*bias)
    variance = _finite(math.fsum((degree, rr_compact, laplace)))
    return ConditionalMSE(degree, _finite(rr_a+rr_t), _finite(-6*covariance), laplace,
                          squared, rr_compact, variance, bias, _finite(variance+squared),
                          _finite(degree+rr_a), covariance, total, retained, missed, cap)


def sample_order_cap(graph: SimpleGraph, budget: FourPathBudget, *, seed: int,
                     beta: float = .05, kcore_config: KCoreConfig | None = None
                     ) -> tuple[tuple[int, ...], int]:
    """Prediction-only draw of H. No degree, RR or triangle-count noise is drawn."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError('prediction seed must be a nonnegative integer')
    if isinstance(beta, bool) or not isinstance(beta, (int, float)) or not 0 < beta < 1:
        raise ValueError('beta must be in (0,1)')
    order_rng, cap_rng = (np.random.default_rng(child)
                          for child in np.random.SeedSequence(seed).spawn(2))
    order = kcore_order(graph, budget.ordering, order_rng, kcore_config).order
    rank = ranks(order)
    reports = tuple(local_cap_report(v, row, rank, budget.cap, cap_rng)
                    for v, row in enumerate(graph.adjacency))
    return order, cap_from_reports(reports, graph.num_vertices, budget.cap, beta)


def summarize_predictions(rows: Sequence[ConditionalMSE]) -> dict:
    """Average conditional MSE, NOT MSE at an averaged order/cap."""
    if len(rows) < 2:
        raise ValueError('at least two prediction histories required')
    values = np.asarray([row.mse for row in rows])
    bias = np.asarray([row.bias for row in rows])
    mean_bias = float(bias.mean())
    result = {
        'result_type': 'nonprivate_monte_carlo_prediction', 'samples': len(rows),
        'predicted_mse': float(values.mean()),
        'prediction_se': float(values.std(ddof=1)/math.sqrt(len(rows))),
        'mean_conditional_variance': float(np.mean([r.variance for r in rows])),
        'predicted_bias': mean_bias, 'squared_mean_bias': mean_bias**2,
        'between_history_variance': float(np.mean((bias-mean_bias)**2)),
        'mean_missed_triangles': float(np.mean([r.missed_triangles for r in rows])),
        'truncation_frequency': float(np.mean([r.missed_triangles > 0 for r in rows])),
    }
    for field in ('degree_noise', 'rr_unadjusted', 'shared_rr_adjustment', 'triangle_laplace',
                  'truncation_squared_error', 'rr_compact'):
        result['mean_'+field] = float(np.mean([getattr(r, field) for r in rows]))
    for value in result.values():
        if isinstance(value, float):
            _finite(value)
    return result


def predicted_four_path_mse(graph: SimpleGraph, budget: FourPathBudget, *,
                            seeds: Sequence[int], beta: float = .05,
                            kcore_config: KCoreConfig | None = None) -> dict:
    """Monte Carlo over private H only; caller supplies independent trial seeds."""
    if len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError('need at least two distinct prediction seeds')
    return summarize_predictions([
        conditional_four_path_mse(graph, budget, *sample_order_cap(
            graph, budget, seed=seed, beta=beta, kcore_config=kcore_config))
        for seed in seeds])
