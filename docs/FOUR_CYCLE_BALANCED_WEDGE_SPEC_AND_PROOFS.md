# CMPT 479 — Balanced Wedge-Laplace 4-Cycle Estimator

**Status:** Mathematical design and proofs finalized for an ideal one-round, pure relationship-edge-LDP protocol. This document specifies the mechanism for subsequent Codex implementation. It does **not** establish research novelty or empirical practicality.

## 1. Scope and assumptions

- Input: any simple, undirected graph `G=(V,E)` with `n>=4`, with public vertex universe and IDs; each real vertex knows its own incident edges. Count **non-induced**, undirected 4-cycles: each four-vertex set contributes 0–3 cycles.
- Neighboring inputs differ in the presence/absence of one **undirected** edge. The privacy claim applies to all local reports, their timing, and the public schedule (the complete transcript), not only to the final estimate.
- Privacy budget `epsilon>0` is a fixed constant for asymptotic statements. Every vertex holds its private row of the symmetric adjacency relation, but privacy must cover the two endpoints of a changed edge.
- If `n` is not a prime `>=5`, choose the smallest prime `p>=max(n,5)` and pad the public vertex universe with `p-n` isolated dummy vertices. These vertices have public zero adjacency and can be simulated with independently generated noise. Bertrand's postulate gives `p=Theta(n)` for `n>=4`.
- This is a **simulation protocol** for research. If deployed, generating simulation seeds or deterministic noise known to the adversary would undermine privacy. Seeds can be saved as reproducibility metadata outside the protected public transcript.

## 2. Full protocol

1. Generate all **ordered occurrences** of blocks `B_(a,b)=(a,a+b,a+2b,a+3b) mod p` for every `a in F_p`, `b in F_p\\{0}`. There are `q=p(p-1)` occurrences. **Keep duplicates** even if their four-vertex sets coincide. All entries in each block are distinct because `p>3`.
2. Sample **one** uniformly random permutation `pi` of the `p` vertex labels, independent of the private graph. Apply the same `pi` to every block.
3. For **each block occurrence independently**, choose uniformly one of the three distinct undirected cycles on its four vertices. For example, with sorted vertices `u<v<w<x`, use the three representative cyclic orders `(u,v,w,x)`, `(u,v,x,w)`, `(u,w,v,x)`; these represent the three cycles exactly once. This selection is public and graph-independent.
4. For the selected cycle `(a,b,c,d)`, set endpoints `a,c`, and centers `b,d`. Publicly request wedge indicator `X_b(a,c)=A_{ba} A_{bc}` from `b` and `X_d(a,c)=A_{da} A_{dc}` from `d`. **Neither party sends its unperturbed indicator.** All requests are fixed before accessing private graph data.
5. Each vertex constructs its vector of *all* requested wedge indicators (one coordinate per request, even if requests duplicate a wedge). Each coordinate receives fresh, independently generated `Laplace(scale=24/epsilon)` noise. Each vertex sends its entire noisy vector in a single reporting round; absent request vectors have public length zero. The two wedge noises in each candidate must be independent, and **fresh noise is required for every occurrence**.
6. For each candidate `t`, the server calculates `Z_t=Y_(t,1)*Y_(t,2)`, and outputs

   `C_hat = [3*binom(p,4)/(p*(p-1))] * sum_(t=1)^q Z_t`.

No graph-dependent selection of candidate blocks, no degree projection, clipping, post-hoc correction, truncation to nonnegative values, or change in noise scale is part of the algorithm.

## 3. Combinatorial balance lemmas

**Lemma 1 (pair balance).** Each unordered pair of distinct vertices occurs in exactly `lambda_2=12` block occurrences.

*Proof.* For positions `r!=s` from `{0,1,2,3}` and distinct vertex labels `u!=v`, the equations `u=a+r*b`, `v=a+s*b` in `F_p` uniquely determine `b=(v-u)/(s-r)` (nonzero) and `a=u-r*b`. For each of the `6` unordered position pairs, there are two orders assigning `u,v` to positions. Hence `lambda_2=6*2=12`. QED.

**Lemma 2 (one- and three-vertex multiplicities).** Each vertex occurs in exactly `r=4(p-1)` block occurrences. Each unordered triple occurs in at most `lambda_3=24` block occurrences.

*Proof.* For any fixed position, vertex `u` appears once for every `b!=0` by taking `a=u-r*b`, so total is `4(p-1)`. For any fixed triple and any of the at most `4*3*2=24` injective assignments of its three vertices to ordered block positions, the first two equations determine `a,b` uniquely; the third either holds or does not. Thus at most 24 block occurrences contain that triple. QED.

**Corollary (high-overlap block pairs).** Let `H_t` be the number of **ordered** block-occurrence pairs `(B,B')` with `|B intersect B'|=t`. For each `B`, any `B'` sharing at least three vertices contains at least one of the four triples of `B`. Each triple occurs in at most 24 blocks, so `H_3+H_4 <= 96*q = O(p^2)`.

## 4. Complete-transcript privacy proof

**Lemma 3 (per-vertex L1 sensitivity).** Condition on a fixed public schedule (including `pi`, the candidate cycle choices, request IDs and lengths). For any vertex `v`, changing an incident edge `{v,u}` can change its wedge indicator `X_v(a,c)` only if `{u,v}` belongs to that candidate's four-vertex block and `v` is a center. A fixed block contains `u,v` in at most 12 occurrences by Lemma 1, and each occurrence generates at most one report from each given center. Hence the complete vector for endpoint `v` has L1 sensitivity at most 12. No other vertex's indicator depends on `{u,v}`.

**Theorem 1 (pure epsilon relationship-edge privacy).** Apply the Laplace mechanism separately to each vertex's fixed coordinate vector, with iid noise scale `b=24/epsilon`. The vector released by any affected endpoint has privacy parameter at most `12/b=epsilon/2`. An undirected-edge change affects at most two endpoint vectors; sequential composition gives total log-likelihood ratio at most `epsilon`. The schedule distribution is independent of the graph, so conditioning and then marginalizing over it preserves the guarantee. Server-side multiplication and aggregation are post-processing. Thus the **entire public transcript** is pure `epsilon` relationship-edge-DP (and consequently meets the intended undirected-edge LEDP definition).

Note: do not silently claim a per-user privacy budget of epsilon simultaneously at both endpoints; the protocol intentionally splits the undirected-edge budget into epsilon/2 per endpoint. Dummy vertex messages are public-data computations with noise and do not weaken the guarantee.

## 5. Unbiasedness proof

Let `N=3*binom(p,4)` be the total number of **candidate undirected 4-cycles**. For each sampled candidate `t`, its exact indicator is `I_t=X_(t,1)*X_(t,2)`. With independent centered Laplace noises `eta_(t,1), eta_(t,2)`,

`E[Y_(t,1)*Y_(t,2) | schedule] = I_t`.

For any fixed block occurrence, uniform `pi` makes its four-vertex image uniformly distributed over all `binom(p,4)` four-vertex sets. Uniform independent selection of one of three cycles gives each of `N` candidate cycles marginal probability `1/N`. Thus `E[I_t]=C4(G)/N`. Linearity gives

`E[C_hat] = (N/q)*sum_t E[Z_t] = (N/q)*q*(C4(G)/N) = C4(G)`.

No independence between the **sampled blocks** is assumed or needed for this expectation.

## 6. Rigorous sampling-variance proof

For a four-vertex set `U`, define `h(U)= (1/3) * (number of existing undirected 4-cycles on U)`, so `0<=h(U)<=1` and `mu=E_[U uniform 4set] h(U)=C4(G)/N`. Let `T_h=sum_(B in blocks) h(pi(B))`, where block occurrences (including duplicates) are retained.

Let `U,V` be **independent**, uniformly random four-vertex sets; write `P_t=Pr(|U intersect V|=t)` for `t=0,...,4`. Let

`c_t=E[h(U)h(V) | |U intersect V|=t]`, where `0<=c_t<=1`, and let `H_t` count **ordered** pairs of blocks with intersection size `t` in the unpermuted design. By uniform random relabelling, `E[T_h^2]=sum_t H_t*c_t`. Independence gives `q^2*mu^2=q^2*sum_t P_t*c_t`.

Therefore,

`Var(T_h)=sum_(t=0)^4 delta_t*c_t`, with `delta_t=H_t-q^2*P_t`.

**The two-design cancellation.** The pair balance and vertex balance imply exact factorial-moment identities for `r=0,1,2`:

`sum_t H_t*binom(t,r) = q^2*E[binom(|U intersect V|,r)] = q^2*sum_t P_t*binom(t,r)`.

- `r=0`: both sides are `q^2`.
- `r=1`: every vertex appears `4q/p` times, so `sum H_t*t = p*(4q/p)^2=q^2*(16/p)`; for independent `U,V`, `E|U intersect V|=16/p`.
- `r=2`: every unordered pair appears `6q/binom(p,2)=12` times, so `sum H_t*binom(t,2)=binom(p,2)*12^2=q^2*(36/binom(p,2))`, which also equals the independent-set expectation.

Hence `sum_t delta_t*Q(t)=0` for **every quadratic polynomial** `Q`.

Take the unique quadratic polynomial interpolating `c_0,c_1,c_2` at `t=0,1,2`. Its values at `t=3,4` have constant absolute bounds because `0<=c_i<=1` (explicitly, `Q(3)=c_0-3c_1+3c_2`, `Q(4)=3c_0-8c_1+6c_2`). Subtract its zero contribution:

`Var(T_h)=sum_(t=3)^4 delta_t*(c_t-Q(t))`.

Each `|c_t-Q(t)|` is bounded by an absolute constant. Lemma 2 gives `H_3+H_4 <=96q`. For independently sampled four-sets, `P_3+P_4=O(p^-3)` (with the usual large-p asymptotic); therefore `q^2*(P_3+P_4)=O(p)=O(q)` since `q=Theta(p^2)`. It follows that

`Var(T_h) <= C * [H_3+H_4+q^2*(P_3+P_4)] = O(q)=O(p^2)`.

This proof is valid for **any** bounded `h` on four-vertex sets; it does not assume graph sparsity, degree restrictions, or independence of block samples.

**Random cycle choices.** For each block occurrence `t`, let `I_t` denote the indicator of the uniformly selected cycle. Conditioned on the random permutation, the selections are **independent across occurrences** (including repeated blocks) and `E[I_t|pi]=h(pi(B_t))`. Also `Var(I_t|pi)<=1/4`. Thus with `T=sum_t I_t`,

`Var(T) = Var(T_h) + E[sum_t Var(I_t|pi)] <= O(q)+q/4 = O(q)=O(p^2)`.

The sampling-only scaled estimator `(N/q)*T` hence has variance

`(N/q)^2 * O(q) = O(N^2/q) = O(p^6)` because `N=Theta(p^4)` and `q=Theta(p^2)`.

## 7. Privacy-noise variance and final MSE

Conditioned on the public schedule, the two noise terms per candidate are independent, with `eta~Lap(b)`, `E eta=0`, `Var eta=2b^2`. For binary `X_1,X_2`,

`Z=(X_1+eta_1)(X_2+eta_2)` has conditional variance

`Var(Z|schedule)=2b^2*(X_1+X_2)+4b^4 <=4b^2+4b^4`.

Different candidate occurrences use **fresh independent noise coordinates**, so cross-candidate conditional covariances are zero. The total privacy-noise variance is at most

`(N/q)^2 * q*(4b^2+4b^4) = (N^2/q)*(4b^2+4b^4)`.

With `b=24/epsilon`, this is `O((epsilon^-2+epsilon^-4)*p^6)`. By the law of total variance, and using unbiasedness,

`MSE(C_hat) = Var(C_hat) = O([1+epsilon^-2+epsilon^-4] * p^6)`.

Since `p=Theta(n)`, for a **fixed** `epsilon>0`,

`RMSE(C_hat) = O_epsilon(n^3)` and `MSE(C_hat)=O_epsilon(n^6)` for **all** simple undirected graphs. The big-O constant can be very large (particularly for epsilon<=1); this does **not** imply good empirical relative accuracy on sparse graphs.

## 8. Codex implementation requirements and narrow tests

**Implement exactly this design; do not optimize away the essential randomness or change its privacy mechanism.** Keep a clean separation between graph-dependent local wedge evaluation, independent private randomization, and server aggregation.

Focused tests:
1. For prime sizes `p=5,7,11,13`, verify `q=p*(p-1)`, every block has distinct labels, each unordered vertex pair has multiplicity exactly `12`, and triple multiplicity <=24.
2. For fixed public schedules on neighboring graphs, verify that changing any one undirected edge changes at most 12 wedge coordinates **per affected endpoint**, and that all other report vectors remain unchanged.
3. Verify Laplace scale `24/epsilon` for all four required budgets, every noisy output coordinate is fresh, that repeated block occurrences and the independent cycle choices are not deduplicated, and that the complete message schedule is graph-independent.
4. Set noise to zero **only in separate deterministic counting tests**; verify expected values of the sampling estimator via exhaustive small-prime permutations (where feasible) or independent repeated trials, and verify exact non-induced counts on the eight repository fixtures via the existing exact counter. Sampling outputs are **not** required to equal exact counts in any single trial.
5. Check `K4` has **3** non-induced 4-cycles, the 4-cycle fixture has **1**, and adding isolated vertices leaves the ground truth unchanged.
6. Check numerical handling of large signed/noisy products: **do not clamp, round, delete negative estimates, or deduplicate blocks**.

Main evaluations **only after tests**: follow the separately supplied Milestone 3 guide verbatim: six pinned datasets/hashes; ESCAPE exact non-induced 4-cycle counts; total `epsilon in {0.5,1,2,4}`; `200` independently randomized trials per graph/epsilon (`4800` outputs); save trial estimates, MSE, RMSE, bias, `ddof=0` variance, MAE, relative RMSE, runtime, parameters and simulation seeds. Use an independently runnable 4-cycle script, cache exact counts, and produce a concise verification summary.

## 9. Boundaries of the result

- These mathematical results establish correctness and worst-case asymptotic privacy/accuracy for the **ideal specified protocol**, not novelty, empirical competitiveness, or software correctness.
- The sampling variance proof depends critically on **a uniformly random global vertex permutation**, **independent cycle selection per occurrence**, and retaining block multiplicities. Removing any of these requires a new proof.
- The privacy proof depends critically on **a graph-independent request schedule**, **at most one center report per vertex per block**, **fresh independent Laplace noise**, and the **epsilon/2 + epsilon/2 endpoint split**.
- If an adversary learns the actual Laplace randomness through published simulation seeds, the privacy guarantee for such a transcript does not apply. Reproducibility seeds should not form part of the public private-mechanism transcript.
- No claim of originality beyond the specific proposal is established by these proofs; conduct a separate novelty review before calling it a new research contribution.
