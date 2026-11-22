# SC-ESCAPE Stage 4 verification

2026-11-22 (America/Vancouver). **Overall classification: PARTIAL.**

The ideal real-arithmetic estimator is unbiased and its complete two-round
transcript satisfies the supplied undirected-edge accounting on the stated
public-bound domain. Source inspection and focused checks match those equations.
The supplied parameter-dependent MSE bound needs a D_max=0 correction; the O(n⁵)
corollary needs an explicit restriction on the supplied bound. There is also a
concrete, unresolved tiny-epsilon floating-point limitation. Thus this report
does **not** certify the executable over its entire accepted parameter range.

| Review item | Finding |
|---|---|
| Ideal counting identity and unbiasedness | PASS under independent ideal randomizers |
| Ideal full-transcript privacy | PASS on the fixed public D_max domain |
| Covariance and conditional variance | Derived explicitly below; no independence assumption between reused reports |
| Supplied MSE expression | Valid for D_max≥1; corrected below for D_max=0 |
| Fixed-allocation asymptotic bound | Confirmed, including D_max=0 |
| O(n⁵) corollary | Confirmed when supplied D_max=O(n); false for arbitrary loose bounds |
| Executable numerical/privacy guarantee | PARTIAL; tiny RR epsilon counterexample and deployment qualifications remain |

No estimator, existing test, graph, cache, dependency or reference source was
changed. The simulator retains `experimental_unverified`. This is a mathematical
and source review supported by small deterministic tests, not a formal software
privacy certification. **Stage 5 has not begun.**

## Scope, implementation and counting semantics

Reviewed the Stage 3 module/tests/document/checkpoint, current STATUS, evaluation
standards, `SimpleGraph`, noise/RR helpers, exact P₄/triangle counters and the
original five-stage estimator. SC-ESCAPE does not import or call that estimator.
The new implementation remains in `four_path_sc_escape.py`; the earlier estimator
remains in `four_path.py` unchanged.

Let V={0,…,n−1} be fixed and public. G is simple, undirected and loop-free.
Write d_v=|N(v)|, a_v=d_v−1, and

\[
A=\sum_{\{u,v\}\in E}a_u a_v
 =\tfrac12\sum_v a_v\sum_{u\in N(v)}a_u.
\]

For each middle edge {u,v}, (d_u−1)(d_v−1) chooses an outer neighbor at each
end, excluding the middle vertices. A coincident outer vertex contributes once
per edge of a triangle, hence three times per triangle. All remaining choices
give one undirected four-distinct-vertex path, with reversal identified. Therefore
P₄=A−3T. Extra host edges are permitted: these are non-induced unlabeled copies,
not induced graphs or vertex sets (K₄ contains 12 P₄ copies).

Eight existing cached small-fixture truths and the independent ordered-quadruple
oracle are checked by the existing Stage 3 tests. This review reran those tests;
it did not regenerate fixtures or recompute native ESCAPE truth.

| Source boundary | Verified behavior |
|---|---|
| `local_degree_report` | One d_v+Lap(0,1/ε_D) report per vertex, including isolates |
| `local_rr_lower_row` | Exactly i fresh uniform draws for row i, all j<i, including nonedges; p from shared `rr_parameters` |
| `local_product_report` | Actual neighbors used only locally; receives the entire centered degree transcript; noise scale 2|x_v|H/ε_S |
| `local_triangle_report` | Actual lower neighbors only; pairs j<k<i look up bit k(k−1)/2+j in the complete packed table |
| `simulate_sc_escape` | All Round 1 reports precede both Round 2 components; fixed n reports of each type; 1/2 aggregation and −3 subtraction |
| `sc_escape_streams` | SeedSequence children in fixed degree/RR/product/triangle order; generators advance without per-vertex resets |
| Result/transcript | Only intended private reports, postprocessed estimates and public metadata; no raw rows, degrees, exact truth or seed |

Round 2A and 2B need no messages from one another, so their sequential execution
in the simulator is still one protocol round. Packed RR storage avoids a second
graph copy. The schedule is a function of public IDs/n, not of private adjacency.
The server must broadcast the entire table and degree vector; it must not request
or serve only the pairs selected by a client's actual neighbors. Local iteration
costs are not constant-time and are outside the intended message transcript.
There is no clipping, truncation, projection or rounding of estimates.

The triangle component matches the lower-triangle RR, centered lower-neighbor
wedge reports and Laplace scale in
[Imola, Murakami and Chaudhuri, Algorithm 3, USENIX Security 2021](https://www.usenix.org/system/files/sec21-imola.pdf#page=10).
Its projection is the identity on our bounded input domain. We do not adopt a
private bound estimator or neighbor-dependent query optimization from that work.

## Complete ideal transcript privacy

Fix public D=D_max and all four positive budgets independently of private data.
The adjacency domain is
\(\mathcal G_{n,D}=\{G:\max_v d_v\le D\}\).
Neighbors G,G⁺ differ by adding one undirected edge {a,b}, a<b, and **both** must
lie in this domain. Removal follows by reversing the same argument. This is not
node privacy, arbitrary neighbor-list replacement or edge-swap adjacency.
In the paper's terminology a symmetric undirected-edge change is relationship
adjacency; the account below explicitly charges both endpoint rows.

Let R₁=(\(\hat d\),B) and R₂=(\(\hat S\),\(\hat w\)). Consider the entire
transcript (R₁,R₂), including RR bits and per-client reports, not merely the final
estimate. Fresh ideal randomizers are independent across stages and clients.

**Round 1 degrees.** Two degrees change by one. Each Laplace scale 1/ε_D
bounds its log-density ratio by ε_D; the joint release costs 2ε_D. No scale
2/ε_D is substituted. A change in one local adjacency bit has sensitivity one.

**Round 1 RR.** There is one reporting owner, b, for {a,b}. Only this input bit
changes; every other RR input agrees. For either output bit the likelihood ratio
is at most (1−p)/p=exp(ε_R). Including nonedges and using fixed row lengths avoids
revealing the adjacency through omitted reports. This gives ε_R, not 2ε_R.

**Conditional product reports.** Fix the *same* R₁=r₁ in both worlds. Put
x_v=\(\hat d_v\)−1 and H=max|x_v|; these and all product scales now agree between
worlds. Changing one local neighbor u changes S_v by x_v x_u, so

\[
|S_v(G^+;r_1)-S_v(G;r_1)|\le |x_v|H=\Delta_v.
\]

Only endpoint rows a,b change, even though their noisy degree values are used
elsewhere: those values are held fixed in this conditional comparison. Scale
2Δ_v/ε_S gives at most ε_S/2 per changed row, hence ε_S total. If Δ_v=0 then
x_v=0 or H=0, so S_v=0 for every local input with this transcript; the zero-scale
point mass is identical in both worlds. No division by zero is needed in the
privacy argument. H is postprocessing of released degrees, not a new private
maximum-degree estimate.

**Conditional triangle reports.** Fix B as well. The smaller endpoint a ignores
its changed upper neighbor b. Only b's lower-neighbor list changes. Let L be
its lower neighbors before adding a. Then |L|≤D−1 because both graphs satisfy
the same public bound, and

\[
w_b(G^+;B)-w_b(G;B)=\sum_{u\in L}(B_{\{a,u\}}-p).
\]

Its magnitude is at most (D−1)max(p,1−p)≤D for D≥1. The scale D/ε_T therefore
costs at most ε_T for the whole conditional triangle transcript. Other clients
may consume B_ab, but its *reported value is fixed* here; this is not a second
unconditional sensitivity contribution. For D=0 there are no distinct neighboring
graphs in the domain, and the privacy condition is vacuous.

**Composition.** The conditional Round 2 joint kernel costs ε_S+ε_T. Noise scales
may depend on R₁: the bound holds for each fixed transcript, so adaptive sequential
composition applies. With common dominating measures (and identical degenerate
coordinates), the full likelihood ratio factors into Round 1 and conditional
Round 2 factors, giving

\[
\frac{f_G(r_1)f_G(r_2\mid r_1)}
     {f_{G^+}(r_1)f_{G^+}(r_2\mid r_1)}
\le \exp(2\epsilon_D+\epsilon_R+\epsilon_S+\epsilon_T).
\]

The reverse ratio has the same bound. Integration gives the event-level DP
inequality. Aggregate A, T, P₄, H and public configuration are postprocessing.
No other sensitive reports or adjacency-dependent communication are implemented.
The intended local randomizers are functions only of a client's row and public
history; the Python driver nevertheless holds the graph in one process.

Input rejection is an offline precondition check, not a private mechanism on
graphs outside this domain. Choosing D from true degrees without a privacy
analysis, publishing validity results on unrestricted graphs, exposing local
timings, or publishing seeds would not be covered by this argument. A public
budget/configuration must likewise not encode a private graph statistic.

## Unbiasedness and dependence

Use ideal independent Z_v~Lap(0,1/ε_D), x_v=a_v+Z_v, and independent fresh
unit-Laplace variables to generate the adaptive product noises η_v. Conditional
on x, E[η_v|x]=0 and all conditional moments exist. Therefore

\[
E[\hat A\mid x]=A_0(x):=\sum_{\{u,v\}\in E}x_u x_v,
\quad E[\hat A]=\sum_{\{u,v\}\in E}a_u a_v=A.
\]

Each edge has distinct endpoints, so independent zero-mean degree noises suffice;
there is no squared-noisy-degree diagonal requiring a bias correction.
Adaptive noise scale dependence on x does not invalidate its conditional zero
mean. Product reports are generally correlated through x; they are not treated
as unconditionally independent.

For every unordered pair j<k, define

\[
c_{jk}=|\{i>k:j,k\in N(i)\}|,\qquad q=1-2p>0.
\]

These coefficients include open as well as closed wedges. If e_jk is the true
adjacency bit, E[B_jk−p]=q e_jk. Consequently

\[
\sum_i w_i=\sum_{j<k}c_{jk}(B_{jk}-p),\qquad
E[\hat T]=\sum_{j<k}c_{jk}e_{jk}=T.
\]

Each triangle is assigned once, to its largest vertex. Zero-mean independent
triangle Laplace noise does not change the expectation. Thus E[\(\hat P_4\)]=P₄.
For a **fixed graph**, \(\hat A\) uses only degree/product randomness and
\(\hat T\) uses only RR/triangle randomness. Their ideal independence gives
Cov(\(\hat A,\hat T\))=0. Merely using distinct generator objects does not prove
this for arbitrarily correlated custom streams. SeedSequence provides the
intended research stream separation, not a theorem about ideal random bits.

## Exact ideal MSE decomposition

Let m=|E|, σ²=2/ε_D² and
\(g_v=\sum_{u\in N(v)}a_u\). Expanding the degree polynomial gives

\[
A_0-A=\sum_v g_v Z_v+\sum_{\{u,v\}\in E}Z_uZ_v.
\]

Distinct quadratic edge terms are uncorrelated even when they share one vertex:
a different endpoint contributes a zero-mean factor. Linear/quadratic cross
terms also have expectation zero. This yields

\[
\operatorname{Var}(A_0)=\frac2{\epsilon_D^2}\sum_v g_v^2
                         +\frac{4m}{\epsilon_D^4}.
\]

Given x, each η_v has variance 8x_v²H²/ε_S². The factor 1/2 in aggregation is
squared, giving

\[
\operatorname{Var}(\hat A\mid x)
 =\frac2{\epsilon_S^2}H^2\sum_v x_v^2.
\]

The conditional mean-zero noise is uncorrelated with A₀, so the total variance
adds the expectation of this term, **not** a product of expectations of H² and
\(\sum x_v^2\). They are dependent.

All B_jk are independent, with variance p(1−p), regardless of their true bit.
Several clients can reuse a bit. Summing its coefficients before squaring retains
that covariance:

\[
\operatorname{Var}(\hat T)
 =\frac{p(1-p)}{q^2}\sum_{j<k}c_{jk}^2
  +\frac{2nD^2}{\epsilon_T^2q^2}.
\]

In particular, replacing \(\sum c_{jk}^2\) with \(\sum c_{jk}\) would incorrectly
treat shared RR reports as independent. Combining all terms gives the exact
ideal expression

\[
\boxed{\begin{aligned}
\operatorname{MSE}(\hat P_4^{SC})={}&
\frac2{\epsilon_D^2}\sum_v g_v^2+\frac{4m}{\epsilon_D^4}
+\frac2{\epsilon_S^2}E\!\left[H^2\sum_v x_v^2\right]\\
&+9\frac{p(1-p)}{q^2}\sum_{j<k}c_{jk}^2
+\frac{18nD^2}{\epsilon_T^2q^2}.
\end{aligned}}
\]

The factor nine is from subtracting three times T. This formula is an analytical
identity for ideal randomizers, not an exact numerical guarantee for NumPy.

## Bound, corrections and asymptotics

For D≥1, |g_v|≤D² and m≤nD/2. Also
\(c_{jk}\le D\) and \(\sum_{j<k}c_{jk}=\sum_i\binom{d_i^-}{2}\le nD^2/2\),
so \(\sum c_{jk}^2\le nD^3/2\). These terms are zero when D=0.

For the adaptive noise term let \(D_* =\max(1,D)\), n≥1 and
M=max_v|Z_v|. Then H≤D_*+M, and
P(M>t)≤min(1,n exp(−ε_D t)). Integrating this tail (or shifting an exponential
by log(n)/ε_D) gives

\[
E[M^4]\le\epsilon_D^{-4}
\{L^4+4L^3+12L^2+24L+24\},\qquad L=\log n.
\]

Hence E[H⁴]=O((D_*+log(n+1)/ε_D)⁴), while
\(H^2\sum_v x_v^2\le nH^4\). Finally

\[
\frac{p(1-p)}{q^2}=\frac{e^{\epsilon_R}}{(e^{\epsilon_R}-1)^2},\qquad
\frac1{q^2}=\left(\frac{e^{\epsilon_R}+1}{e^{\epsilon_R}-1}\right)^2.
\]

A uniform bound, with constants independent of the positive budgets, is

\[
\boxed{\begin{aligned}
\operatorname{MSE}=O\Bigg(&
\frac{nD^4}{\epsilon_D^2}+\frac{nD}{\epsilon_D^4}
+\frac n{\epsilon_S^2}\left(D_*+\frac{\log(n+1)}{\epsilon_D}\right)^4\\
&+\frac{e^{\epsilon_R}}{(e^{\epsilon_R}-1)^2}nD^3
+\frac{nD^2}{\epsilon_T^2}
 \left(\frac{e^{\epsilon_R}+1}{e^{\epsilon_R}-1}\right)^2\Bigg).
\end{aligned}}
\]

For n=0 all releases are empty and MSE=0. For D≥1, D_*=D and this is precisely
the supplied big-O expression. The correction changes **analysis only**, not
D_max, noise scales, the input domain or the estimator.

**D=0 counterexample to an unqualified uniform bound.** With n=1, the graph has
no edges or triangles, x=Z−1 and H=|x|, but the product report still adds noise.
The exact MSE is

\[
\frac2{\epsilon_S^2}E[(Z-1)^4]
 =\frac2{\epsilon_S^2}
  \left(1+\frac{12}{\epsilon_D^2}+\frac{24}{\epsilon_D^4}\right).
\]

The originally supplied RHS has only
\(\epsilon_S^{-2}(\log2/\epsilon_D)^4\) left in this case. It tends to zero as
ε_D→∞ while the exact MSE tends to 2/ε_S². Thus the original expression needs
D≥1, an additional budget restriction, or the D_* correction for uniformity.
If budgets are fixed and big-O constants may depend on them, this counterexample
does not invalidate the fixed-budget asymptotic statement.

**Fixed positive allocations.** With all four epsilons fixed independently of n
(not just fixed fractions of a total budget shrinking with n), the corrected
bound gives
\(O(n(D_*+\log(n+1))^4)=O(n(D+\log(n+1))^4)\), since log(n+1)≥log2 for n≥1.
Thus the requested fixed-allocation corollary holds, including D=0.

**Worst case O(n⁵).** This follows when the *supplied* D is O(n), in particular
when 0≤D≤n−1 is explicitly given. The API permits looser bounds unchanged;
actual graph degree≤n−1 does not automatically bound the supplied noise scale.
For an empty graph and supplied D=n³, the final triangle-noise contribution is
18n⁷/(ε_T²q²), so an unrestricted O(n⁵) statement is false. No silent replacement
by n−1 is justified. This is an asymptotic statement about the ideal graph family;
the current simulator itself is guarded at n≤1000.

## Numerical finding and unresolved issues

At the accepted ε_R=10⁻²⁰, `rr_parameters` returns floating p=0.5, whereas
`tanh(epsilon_R/2)` remains positive. RR has therefore lost its true-edge signal:
even for a true closing edge, the two centered report outcomes average to zero,
and dividing by the nonzero denominator cannot recover T=1. The new deterministic
characterization test demonstrates this limitation without any trials. Its pass
records the defect; it is **not** evidence of numeric unbiasedness.

No shared RR helper or estimator was altered to repair it. Deciding a supported
precision range or using a different numerical/randomness representation would
require an explicit numerical contract; rejecting only this example would not
establish unbiasedness or DP throughout the remaining finite-precision range.
The ideal proof assumes exact p and does not apply verbatim to this boundary.

Further unresolved executable concerns remain: finite random grids and arithmetic,
overflow/underflow and observable errors, seed disclosure/reuse, correlated custom
generators, and lack of deployed client isolation or side-channel protection.
No ideal statement here includes public raw validation errors or runtime traces.
Independent formal review is still required. No claimed low-out-degree benefit,
empirical MSE agreement, utility finding or production DP certification follows.

## Checks performed and stopping point

```bash
.venv/bin/python -m pytest -q tests/test_four_path_sc_escape.py tests/test_sc_escape_verification.py
```

Final result: **57 passed in 0.05s**, no failures/errors/skips: 46 existing cases
plus 11 added cases. New coverage consists of three fixed RR histories for one
neighboring-graph pair and full selected transcript density ratios; a tight
lower-wedge sensitivity example; two 16-node degree moment calculations; two
shared-RR covariance examples; an eight-node conditional-noise moment calculation;
a three-node fourth-moment calculation for D=0; and the tiny-epsilon characterization.
Finite moment nodes are deterministic analytical cubature, not Monte Carlo,
simulated trials, or empirical Laplace fits. These limited examples supplement
the symbolic arguments; they cannot establish universal privacy by themselves.

Existing tests already cover explicit public-bound validation, replay, scales,
ownership, schedules, cached noiseless truth and output fields; no duplicate
test framework or historical regression suite was added. All three pinned
references verified unchanged. Eleven protected Stage 3/source/config/cache files
were hashed before and after. See
[checkpoint 32](status/checkpoints/32_sc_escape_stage4_verification.md) for commands,
preservation details and the complete file list. **Stop after Stage 4.** No Stage 5
runner, benchmark trial, 200-trial experiment, baseline, tuning, dataset/cache
change, dependency change, commit or push was performed.
