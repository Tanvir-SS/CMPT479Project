# AISTATS 2025 P4 baseline — source gate and reconstruction

## Identification and source-verification gate (before implementation)

**Gate passed, 2026-11-06 (America/Vancouver).** Classification: faithful
independent P4 reconstruction of Algorithm1, with the undirected one-report-per-
pair convention demonstrated by the authors' C4 notebook. Not a reproduction of
published P4 code (none is present), not a new private estimator, and not a
literal independent report from both endpoints. The ownership convention and
algebraic implementation refinement below are explicit.

Suppakitpaisarn, Ponnoprat, Hirankarn and Hillebrand, *Counting Graphlets of Size k
under Local Differential Privacy*, AISTATS2025, PMLR258:5005–5013.
[Official page](https://proceedings.mlr.press/v258/suppakitpaisarn25a.html),
[official PDF](https://raw.githubusercontent.com/mlresearch/v258/main/assets/suppakitpaisarn25a/suppakitpaisarn25a.pdf),
[arXiv v1](https://arxiv.org/html/2505.12954v1).
Official PDF SHA256:
`5572fe21fbb76d92c7a92a5daa86b580b8d25284210b292e982819ffed29356f`.
Downloaded read-only reference copy and PDFKit extraction are in build/phase16/.
The PDF contains17 pages including the checklist and supplementary Section8,
which supplies lower-bound proofs, not a different counting mechanism.
OpenReview was browser-challenged; the official PDF and arXiv full text were
accessible. Browser PDF download initially rejected octet-stream; curl required
an approved network retry. No project dependency was installed.

### Essential claim locations

| Claim | Exact source location |
|---|---|
| Count distinct subgraphs, not induced vertex sets | Section2.1; Lemma3.1 proof explicitly chooses only pattern-required edges |
| Error means root expected squared error | Section2.1 displayed integral; Theorem3.4 proof |
| One-bit local adjacency and per-user composition | Section2.2 Definitions1–3 |
| RR distribution and correction | Section2.3 Definition4; Algorithm1 line2 |
| Single RR query | Algorithm1 line1; privacy paragraph immediately after algorithm |
| Distinct vertex tuples, required-edge product, automorphism division | Algorithm1 lines3–4 |
| Normalization and unbiasedness | Lemmas3.1 and3.2 |
| Overlap covariance argument and fixed-epsilon RMSE bound | Lemma3.3, equation(1), Theorem3.4 |
| C4 experiment and classical noisy-graph comparator | Sections2.3 and6.1 |
| Literal computation cost | Sections6.1 and7: O(n^k) |
| Epsilon dependence not explicitly resolved | Section7 final paragraph before acknowledgments |
| Supplement | Section8, missing proofs for Section4 |

Algorithm1 and Lemmas3.1–3.2 are on official PDF page4; Theorem3.4 on page5;
Section7 on page9. ArXiv pagination differs; section/algorithm labels are stable.
The paper's Section6.1 sample error displays sqrt(sum of ten squared errors)
without division by ten; that differs by sqrt(10) from standard sample RMSE.
Future project evaluation uses mean squared error and its square root explicitly.

### Author software and ownership ambiguity

The official page's Software link and Section6.1 identify
https://github.com/gcwsilver/Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy.
Pinned revision:85eff6efa2b1d649ee238620a998ec7f1d305aac. Current pinned contents:
README.md and two C4 notebooks, no P4 implementation, package or license file.
Owner-reported academic permission remains the repository's inclusion basis;
no new license or broader permission is inferred. Sources are unchanged.

`babarasi_square.ipynb`: cell4 defines the two debiased weights, cell5 flips only
pairs i<j in an undirected NetworkX graph, cell8 builds symmetric weights,
cells10–11 sum products over four distinct vertices and divide C4 by8.
`babarasi_rr_mse.ipynb`: cells5,7–8 perturb the graph then count C4 without
weight debiasing. Thus the former demonstrates the proposed method, the latter
the paper's classical comparator. The three-weight debiased P4 expression is
supported by Algorithm1; labeling it only a classical comparator would be wrong.

Algorithm1 writes all i,j without specifying duplicate endpoint ownership. We
resolve this with the notebook's single unordered-pair randomization, assign each
pair to its lower public-ID endpoint, and mirror its report at the server.
This implements the author-code undirected convention. Sampling two independent
endpoint reports would produce a different transcript/distribution and require
2*epsilon accounting for a changed undirected edge. We do not silently do that.

## Technical specification

Inputs: validated simple undirected graph, fixed public vertices0..n−1, positive
finite epsilon, fixed pattern P4 with automorphisms identity and reversal.
No private order, cap, partition, graph sampling, noisy degree or count noise.

Client v reads only its incident membership bits for every w>v, including
nonedges. It reports Y_vw with flip probability q=1/(exp(epsilon)+1), using
independent pair coins. The last client has an empty message. There is exactly
one query round; report lengths depend only on public n.

Server maps each bit to W_uv=(Y_uv−q)/(1−2q), mirrors W_vu=W_uv, and sets the
unused diagonal to zero. Equivalently W is exp(epsilon)/(exp(epsilon)−1) for
true reports and −1/(exp(epsilon)−1) for false reports. The output is

    P_hat = (1/2) sum_(a,b,c,d all distinct) W_ab W_bc W_cd.

Only three required edges enter; additional host edges are allowed. Reversal
is the only P4 automorphism, giving division by2. No division by24 or by the
number of four-sets. K4 has12 P4 copies, C4 has4, diamond6 and bare path1.
Each monomial involves three distinct independent unordered reports, so its
mean is x_ab*x_bc*x_cd. Summing gives the non-induced P4 count; no truncation bias.

### Exact server-only algebraic refinement (independently derived here)

For any symmetric zero-diagonal real weight matrix, let r_b=sum_a W_ab. Then

    P_hat = sum_(b<c) W_bc * [(r_b−W_bc)(r_c−W_bc)
                             − sum_a W_ba W_ca].

Proof: fixing middle edge b,c, the product of row sums enumerates all outer
endpoints except b,c; subtracting the dot product removes the case a=d. Its
terms a=b,c vanish by the zero diagonal. Choosing b<c counts each path once,
replacing the reversal factor. This is an identity for arbitrary signed weights,
not an exact-graph shortcut. Server code never receives raw edges/degrees.
The finite-precision evaluation order changes, but the real-arithmetic estimator
and randomization distribution do not. Tests compare to literal permutations
on random signed matrices, all small graphs and RR outputs. No new sampling
or graph-dependent pruning is used.

## Ideal privacy accounting and comparison boundary

For a changed edge {u,v}, only the lower-ID owner's reported coordinate changes.
All other report probabilities cancel. For the affected bit, either likelihood
ratio is exp(epsilon) or exp(−epsilon). Therefore the entire ideal report vector
has likelihood ratio at most exp(epsilon); any deterministic server function is
postprocessing. Locally, changing one adjacency bit affects at most one owned
coordinate (or none if the other endpoint owns it). There is no sum over n
clients for this adjacency relation, and no additional server query.

This is an explicit ideal-model accounting derivation for the chosen ownership
convention, not an executable privacy certification. The paper's per-user
Definitions1–2 alone must not be conflated with a two-endpoint graph transcript.
If both endpoints independently release at epsilon, global undirected-edge
accounting is2epsilon; use epsilon/2 per endpoint to target global epsilon, and
recognize the resulting estimator distribution differs from this implementation.

For Phase5B the baseline spends its entire edge budget on its one RR release;
our candidate spends the declared total D+O+R+M+C. Numerical totals are comparable
only under the same fixed-public-vertex, add/remove-one-undirected-edge model
and reviewed candidate composition. No candidate mechanism/budget is changed.
Both implementations remain experimental_unverified and centralized simulations;
seeds, NumPy randomness, floating-point behavior, failures/timing, client
isolation and transport remain unresolved for deployment. Repeated releases
consume additional budget; this API does not implement a privacy ledger.

## Error: published theorem versus project derivation

Theorem3.4 establishes RMSE O(n^(k−1)) for fixed pattern and fixed positive
epsilon; for P4 this is O(n^3), equivalently MSE O(n^6) because unbiasedness
holds. Section7 explicitly leaves joint n/epsilon bounds for future work.
No exact epsilon-dependent MSE formula is supplied in that theorem. The paper's
lower-bound classes concern cliques/cycles; do not claim its P4-specific optimality.

Independent conservative epsilon-dependent derivation for our specialization:
write W_e=x_e+U_e, E[U_e]=0, Var(U_e)=h=exp(epsilon)/expm1(epsilon)^2. A single
three-edge monomial has variance at most C=(1+h)^3−1=3h+3h²+h³.
Cauchy–Schwarz bounds each covariance by C. Covariance vanishes for disjoint
report sets. For each ordered tuple, tuples sharing at least two vertices are
at most choose(4,2)^2*2!*(n−2)(n−3)=72(n−2)(n−3), an overcount including self.
Dividing by the squared automorphism count gives, for n>=4,

    MSE <= 18*n*(n−1)*(n−2)^2*(n−3)^2 * (3h+3h²+h³).

For n<4 the estimator is identically zero. This loose upper bound, not a paper
formula or exact MSE identity, gives RMSE O(n^3*sqrt(3h+3h²+h³)), and the loose
small-epsilon bound O(n^3/epsilon^3). Constants and epsilon dependence differ
from the five-stage estimator; equal n-exponents do not imply equal accuracy.

Tests use an independent small-graph variance oracle: expand the unordered-path
polynomial in centered independent U_e. For each nonempty report subset S,
c_S=sum_(paths containing S) product_(e in path minus S) x_e. Distinct U-subset
monomials are orthogonal, yielding exact ideal variance sum_S c_S² h^|S|.
This oracle is test-only non-private evaluation, not server-side truth access.

## Computational and communication costs

Literal Algorithm1: O(n^k*|E_pattern|) coordinator arithmetic, O(n²) RR storage;
fixed k gives O(n^k). For P4 n100 there are94,109,400 ordered tuples.
Our exact middle-edge specialization uses O(n³) coordinator time (row sums and
pairwise row dot products), O(n²) memory. Local randomization is O(n−v−1) work
per owner, O(n²) total, and uploads n(n−1)/2 logical bits in public pair order.
No RR table is sent to clients; only public setup parameters are required.
There is one noninteractive upload round. Python bool tuples are not bit-packed
transport; actual wire communication is unimplemented. Sampling/representation
and finite guards add O(n²) work. Size guard n<=100 bounds this reconstruction.

No graph truth can reduce the server's pair work; numerical rejection uses public
n and RR bounds before randomization. Negative/fractional estimates are retained.
No classical control is implemented in this phase: raw noisy-graph counting is
secondary and the debiased candidate already is Algorithm1's specialization.
