"""NON-PRIVATE ideal-law 4-clique error analysis. Never called by private releases.

Independent adjacency/coefficient calculations; no random sampling and no import
of the candidate scorer, RR parameter implementation or private noise functions.
Exact means/counts/polynomial coefficients use integers/Fractions; evaluated real
moments use float64. Intended for small offline validation graphs (n<=20).
"""

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from fractions import Fraction
from itertools import combinations, product
import math
from numbers import Integral, Rational

from private_graphlets.four_clique_exact import validate_cap, validate_order
from private_graphlets.graph import SimpleGraph
from private_graphlets.noise import validate_epsilon


MAX_ANALYSIS_VERTICES = 20


def _inputs(graph, order, cap):
    if graph.num_vertices > MAX_ANALYSIS_VERTICES:
        raise ValueError('offline exact error analysis supports at most 20 vertices')
    order = validate_order(graph.num_vertices, order)
    cap = validate_cap(cap, graph.num_vertices)
    return order, cap


def _finite(value):
    if not math.isfinite(value):
        raise ValueError('analytical value exceeds finite numeric range')
    return value


def ideal_rr_variance(epsilon_rr: float) -> float:
    eta = validate_epsilon(epsilon_rr)
    if eta > 30:
        raise ValueError('match simulator RR epsilon <=30')
    # Independent algebra: q=exp(-eta), tau=q/(1-q)^2.
    return _finite(math.exp(-eta)/(-math.expm1(-eta))/(-math.expm1(-eta)))


def ideal_count_sensitivity(cap: int, epsilon_rr: float) -> float:
    if isinstance(cap, bool) or not isinstance(cap, Integral) or cap < 0:
        raise ValueError('cap must be a nonnegative integer')
    ideal_rr_variance(epsilon_rr)
    if cap < 3:
        return 0.
    q, denominator = math.exp(-epsilon_rr), -math.expm1(-epsilon_rr)
    try:
        return _finite(math.comb(int(cap)-1, 2)*(1+q)/denominator**3)
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError('analytical sensitivity exceeds finite numeric range') from exc


def triangle_multiplicities(graph: SimpleGraph, order: Sequence[int], cap: int) -> dict:
    """Multiplicity of each closing triple; selection independently scans the order."""
    order, cap = _inputs(graph, order, cap)
    result = Counter()
    for i, v in enumerate(order):
        selected = [w for w in order[i+1:] if w in graph.adjacency[v]][:cap]
        result.update(tuple(sorted(triple)) for triple in combinations(selected, 3))
    return dict(sorted(result.items()))


def retained_cliques_bruteforce(graph: SimpleGraph, order: Sequence[int], cap: int) -> tuple[int, int]:
    """(original, retained), using four-sets and a rank-position test, not triples."""
    order, cap = _inputs(graph, order, cap)
    position = {v: i for i, v in enumerate(order)}
    original = retained = 0
    for vertices in combinations(range(graph.num_vertices), 4):
        if not all(v in graph.adjacency[u] for u, v in combinations(vertices, 2)):
            continue
        original += 1
        root = min(vertices, key=position.__getitem__)
        last = max(position[v] for v in vertices)
        # All three leaves retained iff the last one's outgoing rank is <=cap.
        rank_of_last = sum(position[root] < position[w] <= last for w in graph.adjacency[root])
        retained += rank_of_last <= cap
    return original, retained


def _edges(vertices):
    return frozenset(combinations(sorted(vertices), 2))


def _present(graph, edge):
    return int(edge[1] in graph.adjacency[edge[0]])


def _moment_coefficients(edge_count, present_count):
    """Coefficients of prod(A_e+t)-prod(A_e), ascending powers t^1..t^r."""
    return tuple(math.comb(present_count, edge_count-s)
                 if 0 <= edge_count-s <= present_count else 0
                 for s in range(1, edge_count+1))


def evaluate_polynomial(coefficients, tau):
    if not math.isfinite(tau) or tau < 0:
        raise ValueError('tau must be finite and nonnegative')
    try:
        return _finite(math.fsum(c*tau**s for s, c in enumerate(coefficients, 1) if c))
    except OverflowError as exc:
        raise ValueError('analytical variance exceeds finite numeric range') from exc


def rr_variance_coefficients(graph: SimpleGraph, order: Sequence[int], cap: int) -> tuple[int, int, int]:
    """Exact integer coefficients c1,c2,c3 for Var(F)=c1*tau+c2*tau^2+c3*tau^3."""
    multiplicity = triangle_multiplicities(graph, order, cap)
    coefficients = [0, 0, 0]
    incident = defaultdict(list)
    for triple, m in multiplicity.items():
        edges = _edges(triple)
        k = sum(_present(graph, e) for e in edges)
        for i, value in enumerate(_moment_coefficients(3, k)):
            coefficients[i] += m*m*value
        for edge in edges:
            incident[edge].append((triple, m, edges))
    # Distinct triples share at most one edge, so each covariance occurs once.
    for edge, terms in incident.items():
        for (_, m, e), (_, other_m, f) in combinations(terms, 2):
            if all(_present(graph, pair) for pair in (e | f) - {edge}):
                coefficients[0] += 2*m*other_m
    return tuple(coefficients)


def rr_upper_bound(n: int, cap: int, epsilon_rr: float) -> float:
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 0:
        raise ValueError('n must be a nonnegative integer')
    validate_cap(cap, int(n))
    tau = ideal_rr_variance(epsilon_rr)
    if cap < 3:
        return 0.
    vmax = evaluate_polynomial((3, 3, 1), tau)
    return _finite(n*n*math.comb(cap, 3)*(vmax+3*tau*(cap-2)))


@dataclass(frozen=True)
class ConditionalError:
    n: int
    cap: int
    epsilon_rr: float
    epsilon_count: float
    exact_count: int
    retained_count: int
    rr_expectation: int
    rr_coefficients: tuple[int, int, int]
    rr_variance: float
    sensitivity: float
    laplace_variance: float
    conditional_bias: int
    clipping_bias_squared: int
    mse: float
    rmse: float
    rr_variance_upper_bound: float
    mse_upper_bound: float
    rmse_upper_bound: float
    unique_triples: int
    triple_occurrences: int

    def to_dict(self):
        return {'result_type': 'nonprivate_ideal_error_evaluation', **asdict(self)}


def conditional_error(graph: SimpleGraph, order: Sequence[int], cap: int,
                      epsilon_rr: float, epsilon_count: float) -> ConditionalError:
    """Exact ideal conditional decomposition, numerically evaluated; no sampled values."""
    order, cap = _inputs(graph, order, cap)
    count_eps = validate_epsilon(epsilon_count)
    tau = ideal_rr_variance(epsilon_rr)
    multiplicity = triangle_multiplicities(graph, order, cap)
    original, retained = retained_cliques_bruteforce(graph, order, cap)
    expectation = sum(m*math.prod(_present(graph, e) for e in _edges(t))
                      for t, m in multiplicity.items())
    if expectation != retained:
        raise AssertionError('triple expectation and independent retained-four-set count disagree')
    coefficients = rr_variance_coefficients(graph, order, cap)
    variance = evaluate_polynomial(coefficients, tau)
    delta = ideal_count_sensitivity(cap, epsilon_rr)
    try:
        laplace = _finite(2*graph.num_vertices*(delta/count_eps)**2)
    except OverflowError as exc:
        raise ValueError('analytical Laplace variance exceeds finite numeric range') from exc
    bias = retained-original
    mse = _finite(math.fsum((variance, laplace, bias*bias)))
    bound = rr_upper_bound(graph.num_vertices, cap, epsilon_rr)
    mse_bound = _finite(math.fsum((bound, laplace, bias*bias)))
    return ConditionalError(graph.num_vertices, cap, epsilon_rr, count_eps, original, retained,
        expectation, coefficients, variance, delta, laplace, bias, bias*bias, mse, math.sqrt(mse),
        bound, mse_bound, math.sqrt(mse_bound), len(multiplicity), sum(multiplicity.values()))


def baseline_variance_coefficients(graph: SimpleGraph) -> tuple[int, ...]:
    """Six-factor baseline; shared 2/3 vertices mean 1/3 shared RR edges."""
    _inputs(graph, tuple(range(graph.num_vertices)), max(0, graph.num_vertices-1))
    terms = [_edges(vertices) for vertices in combinations(range(graph.num_vertices), 4)]
    coefficients = [0]*6
    for edges in terms:
        k = sum(_present(graph, e) for e in edges)
        for i, c in enumerate(_moment_coefficients(6, k)):
            coefficients[i] += c
    for first, second in combinations(terms, 2):
        common = first & second
        if not common or not all(_present(graph, e) for e in first ^ second):
            continue
        for i, c in enumerate(_moment_coefficients(len(common), sum(_present(graph, e) for e in common))):
            coefficients[i] += 2*c
    return tuple(coefficients)


def baseline_error(graph: SimpleGraph, epsilon: float) -> dict:
    tau = ideal_rr_variance(epsilon)
    coefficients = baseline_variance_coefficients(graph)
    truth, _ = retained_cliques_bruteforce(graph, tuple(range(graph.num_vertices)), max(0,graph.num_vertices-1))
    variance = evaluate_polynomial(coefficients, tau)
    return {'result_type': 'nonprivate_ideal_error_evaluation', 'mechanism': 'six_factor_baseline',
            'epsilon_rr': epsilon, 'exact_count': truth, 'expectation': truth,
            'rr_coefficients': coefficients, 'rr_variance': variance, 'laplace_variance': 0.,
            'clipping_bias_squared': 0, 'mse': variance, 'rmse': math.sqrt(variance)}


def cap_underestimate_probability(graph: SimpleGraph, order: Sequence[int],
                                  epsilon_cap: float, beta: float) -> dict:
    """Exact ideal cap-stage CDF product and upper bounds; no random cap sampling.

    Full clique protocol n<4 shortcut is respected. Probability may underflow;
    log_probability distinguishes that from a mathematically impossible event.
    """
    order, _ = _inputs(graph, order, max(0, graph.num_vertices-1))
    eps = validate_epsilon(epsilon_cap)
    if isinstance(beta, bool) or not isinstance(beta, (int, float)) or not 0 < beta < 1:
        raise ValueError('beta must be strictly between zero and one')
    n = graph.num_vertices
    q = [sum(w in graph.adjacency[v] for w in order[i+1:]) for i, v in enumerate(order)]
    d = max(q, default=0)
    if d == 0 or n < 4:
        return {'probability': 0., 'log_probability': None, 'single_max_bound': 0.,
                'multiple_max_bound': 0., 'maximizers': q.count(d), 'original_count_squared_loss_bound': 0.}
    margin_in_scale_units = math.log(n)-math.log(beta)
    values = [eps*(d-1-degree)-margin_in_scale_units for degree in q]
    logs = [math.log(.5)+x if x <= 0 else math.log1p(-.5*math.exp(-x)) for x in values]
    log_probability = _finite(math.fsum(logs))
    probability = math.exp(log_probability)
    single = beta*math.exp(-eps)/(2*n)
    r = q.count(d)
    truth, _ = retained_cliques_bruteforce(graph, order, n-1)
    return {'probability': probability, 'log_probability': log_probability,
            'single_max_bound': single, 'multiple_max_bound': single**r, 'maximizers': r,
            'original_count_squared_loss_bound': probability*truth**2}


@dataclass(frozen=True)
class EnumeratedMoments:
    mean: Fraction
    variance: Fraction
    third_central: Fraction
    fourth_central: Fraction
    table_count: int
    enumerated_pair_count: int
    full_pair_count: int


def enumerate_rr_moments(graph: SimpleGraph, order: Sequence[int], cap: int, *,
                         odds: int | Fraction = 2, baseline: bool = False,
                         include_unused_pairs: bool = True) -> EnumeratedMoments:
    """Independent finite-table rational integration, eta=log(rational odds).

    Up to 10 pairs (1024 tables). Optional marginalization integrates independent
    unused pairs analytically; returned pair counts explicitly distinguish it.
    This deliberately does not call multiplicity, variance or estimator scorers.
    """
    order, cap = _inputs(graph, order, cap)
    if isinstance(odds, bool) or not isinstance(odds, Rational) or odds <= 1:
        raise ValueError('exact rational RR odds must be >1')
    rank = {v:i for i,v in enumerate(order)}
    terms = []
    if baseline:
        terms = [tuple(combinations(vertices,2)) for vertices in combinations(range(graph.num_vertices),4)]
    else:
        for v in range(graph.num_vertices):
            later = sorted((w for w in graph.adjacency[v] if rank[w]>rank[v]), key=rank.__getitem__)[:cap]
            terms.extend(tuple(combinations(sorted(vertices),2)) for vertices in combinations(later,3))
    all_pairs = list(combinations(range(graph.num_vertices),2))
    pairs = all_pairs if include_unused_pairs else sorted({e for term in terms for e in term})
    if len(pairs)>10:
        raise ValueError('finite RR enumeration supports at most 10 sampled pairs')
    values = []
    denominator = (odds+1)**len(pairs)
    for report in product((0,1),repeat=len(pairs)):
        matches = sum(bit==_present(graph,edge) for edge,bit in zip(pairs,report))
        probability = Fraction(odds**matches,denominator)
        weights = {edge:Fraction((odds+1)*bit-1,odds-1) for edge,bit in zip(pairs,report)}
        score = sum((math.prod(weights[e] for e in term) for term in terms), Fraction(0))
        values.append((probability,score))
    mean = sum((p*x for p,x in values),Fraction(0))
    moments = [sum((p*(x-mean)**k for p,x in values),Fraction(0)) for k in (2,3,4)]
    return EnumeratedMoments(mean,*moments,len(values),len(pairs),len(all_pairs))
