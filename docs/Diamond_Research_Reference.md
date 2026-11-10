# 6. Diamond (K₄ minus one edge)

*Research status: Proposed hybrid estimator; mathematical privacy and utility bounds are conditional on the stated protocol assumptions. Implementation pending.*

A diamond consists of two triangles sharing an edge. We count **non-induced diamonds**: the sixth edge may also be present, so every 4-clique contributes six diamonds.

## B. Exact ESCAPE counting formula

ESCAPE counts diamonds by choosing two triangles that share an edge:

$$
D(G)=\sum_{\{a,b\}\in E}\binom{t_{ab}}{2},\qquad
 t_{ab}=\sum_{c\ne a,b} A_{ac}A_{bc}.
$$

Here, $A_{ab}$ indicates whether an edge exists, and $t_{ab}$ is the number of common neighbors of $a$ and $b$. Each pair of common neighbors forms one diamond with central edge $\{a,b\}$. The formula includes diamonds inside 4-cliques and is our exact ground-truth reference.

## C. Proposed private estimator

We combine **k-CoreD ordering**, **randomized-response (RR) edge reports**, and **Laplace-noised outgoing-wedge reports**. We use a fixed public cap $B\ge 2$; actual outgoing-neighbor lists remain private. The privacy budget is $\varepsilon=\varepsilon_O+\varepsilon_R+\varepsilon_W$.

**Stage 1 — Private orientation.** Run k-CoreD with budget $\varepsilon_O$ to obtain a private total ordering $\pi$. Each vertex $c$ locally retains its first $B$ actual outgoing neighbors, denoted $S_c$.

**Stage 2 — Private edge reports.** Exactly one endpoint reports each possible unordered pair by RR with budget $\varepsilon_R$. The coordinator debiases the report $R_{ab}$:

$$
W_{ab}=\frac{(e^{\varepsilon_R}+1)R_{ab}-1}{e^{\varepsilon_R}-1},
\qquad \mathbb E[W_{ab}]=A_{ab}.
$$

**Stage 3 — Private wedge reports.** For every pair $\{a,b\}$ later than $c$, vertex $c$ forms $X_{c,ab}=\mathbf 1[\{a,b\}\subseteq S_c]$ and reports a noisy value:

$$
Y_{c,ab}=X_{c,ab}+L_{c,ab},\qquad
L_{c,ab}\sim\operatorname{Lap}\!\left(0,\frac{2(B-1)}{\varepsilon_W}\right).
$$

Every eligible pair, including zero entries, is reported; the report schedule reveals no actual wedges.

**Hybrid common-neighbor estimate.** Let $v=e^{\varepsilon_R}/(e^{\varepsilon_R}-1)^2$, $V_R=2v+v^2$, $V_W=8(B-1)^2/\varepsilon_W^2$, and choose the public weight $\lambda=V_W/(V_R+V_W)$. Then

$$
\widehat X_{c,ab}=\begin{cases}
\lambda W_{ac}W_{bc}+(1-\lambda)Y_{c,ab}, & \pi(c)<\min\{\pi(a),\pi(b)\},\\
W_{ac}W_{bc}, & \text{otherwise}.
\end{cases}
$$

Let $\mathcal P_{ab}$ denote all unordered pairs of distinct vertices other than $a,b$. The coordinator estimates diamonds using only the private reports:

$$
\boxed{\widehat D(G)=\sum_{a<b}W_{ab}
\sum_{\{c,d\}\in\mathcal P_{ab}}
\widehat X_{c,ab}\widehat X_{d,ab}.}
$$

No noise is added to the final count. Without clipping, this estimator is unbiased; clipping may cause undercounting in expectation.

## D. Privacy proof: ε-Local Edge Differential Privacy (proposed)

Two neighboring graphs have the same public vertex set and differ by one undirected edge. We consider the **complete transcript**, including intermediate messages.

**Stage 1 — k-CoreD ($\varepsilon_O$).** We rely on Mundra et al. (2025), Theorem 3.3, for the $\varepsilon_O$-LEDP guarantee of the complete k-CoreD protocol, under its stated assumptions.

**Stage 2 — RR ($\varepsilon_R$).** Each unordered pair has one public reporting owner. Changing one graph edge changes only one RR input, so the entire RR stage satisfies $\varepsilon_R$-LEDP.

**Stage 3 — Wedges ($\varepsilon_W$).** Conditioned on the earlier transcript and fixed ordering, changing one edge affects the retained outgoing-neighbor set of only its earlier endpoint. An addition/removal changes at most $B-1$ wedge coordinates; a capped replacement changes at most $2(B-1)$. Thus

$$
\Delta_1(\text{wedge vector})\le 2(B-1),\qquad
b_W=\frac{2(B-1)}{\varepsilon_W}.
$$

Independent Laplace noise of scale $b_W$ on **every eligible coordinate** makes the joint wedge-vector release $\varepsilon_W$-LEDP. The hybrid weighting and final diamond count are post-processing.

Therefore, adaptive sequential composition gives

$$
\boxed{\varepsilon_{\mathrm{total}}=\varepsilon_O+\varepsilon_R+\varepsilon_W.}
$$

**Scope.** This is a conditional ideal-protocol proof, assuming independent randomization, a fixed public $B$, public pair ownership and tie-breaking, a valid full-transcript k-CoreD guarantee, and no other unprotected graph-dependent messages. Implementation-level verification remains necessary.

## E. Accuracy guarantee: MSE and RMSE bounds

The estimator's error comes from RR, Laplace noise in wedge reports, and possible clipping. Let $H$ denote the private ordering (with fixed cap $B$), and let $\delta(H)=D(G)-\mathbb E[\widehat D\mid H]$ denote the conditional clipping bias. The exact MSE decomposition is

$$
\operatorname{MSE}(\widehat D)
=\mathbb E_H\!\left[\operatorname{Var}(\widehat D\mid H)+\delta(H)^2\right].
$$

For one common-neighbor estimate, the RR-only variance is at most $V_R=2v+v^2$, while a noisy wedge has variance $V_W=8(B-1)^2/\varepsilon_W^2$. With the public weight above, the hybrid variance is bounded by

$$
\operatorname{Var}(\widehat X_{\mathrm{hybrid}})
\le\frac{V_RV_W}{V_R+V_W}\le V_R.
$$

Different candidate diamonds reuse RR edges and wedge reports, so their errors can be correlated. A conservative full-estimator bound that accounts for this reuse is

$$
\operatorname{MSE}(\widehat D)\le
NL\big[(1+v)^5-1\big]+\mathbb E_H[\delta(H)^2],
$$

where $N=\binom n2\binom{n-2}2$ is the number of possible diamond contributions, and $L=25\binom{n-2}2+2(n-3)$ bounds the number of contributions sharing a random report with any one contribution.

**No-clipping case.** The bias term vanishes. For fixed positive stage budgets, the conservative bounds simplify to

$$
\boxed{\operatorname{MSE}(\widehat D)=O\!\left(n^6\big[(1+v)^5-1\big]\right),\quad
\operatorname{RMSE}(\widehat D)=O\!\left(n^3\sqrt{(1+v)^5-1}\right).}
$$

For small $\varepsilon$, if $\varepsilon_R$ is a fixed positive fraction of the total budget, this gives $\operatorname{MSE}=O(n^6/\varepsilon^{10})$ and $\operatorname{RMSE}=O(n^3/\varepsilon^5)$. These are **upper bounds**, not predictions of experimental error or proof of improvement over RR-only counting. With clipping, the additional squared-bias term must be retained.
