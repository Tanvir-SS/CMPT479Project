"""Canonical one-owner, undirected specialization of AISTATS 2025 debiased RR.

Independent six-factor counting path; not a reproduction of the authors' notebook.
All epsilon is allocated to the pair table. No ordering/count noise is added.
"""

from itertools import combinations
import math

import numpy as np

from private_graphlets.four_clique import CliqueBudget, CliqueResult, simulation_streams
from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import validate_epsilon
from private_graphlets.randomized_response import rr_matrix, rr_parameters, sample_rr_upper


def baseline_score(weights: np.ndarray) -> float:
    """Pure postprocessing of a released RR matrix, all unordered four-sets."""
    with np.errstate(over='raise',invalid='raise'):
        result=math.fsum(float(weights[a,b]*weights[a,c]*weights[a,d]*
                               weights[b,c]*weights[b,d]*weights[c,d])
                         for a,b,c,d in combinations(range(len(weights)),4))
    if not math.isfinite(result):
        raise FloatingPointError("baseline exceeds finite float64 range")
    return result


def simulate_baseline(graph: SimpleGraph, epsilon: float, *, seed: int | None = None
                       ) -> tuple[CliqueResult, tuple[bool,...]]:
    epsilon=validate_epsilon(epsilon)
    rr_parameters(epsilon)
    if graph.num_vertices>100:
        raise ValueError("four-set baseline simulator supports at most 100 vertices")
    rng=simulation_streams(seed)[2]
    reports=() if graph.num_vertices<4 else sample_rr_upper(graph,epsilon,rng)
    estimate=0.0 if graph.num_vertices<4 else baseline_score(rr_matrix(graph.num_vertices,reports,epsilon))
    result=CliqueResult(estimate,graph.num_vertices,"none","none",None,
                       CliqueBudget(epsilon,0,0,epsilon,0),0,"six_factor_debiased_rr_four_clique")
    return result,reports


def estimate_four_cliques_baseline(graph: SimpleGraph, epsilon: float, *, seed: int | None = None) -> CliqueResult:
    return simulate_baseline(graph,epsilon,seed=seed)[0]
