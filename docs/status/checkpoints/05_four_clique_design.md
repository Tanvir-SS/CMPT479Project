# Checkpoint 05 — Candidate LEDP 4-clique design

Date: **2026-10-29** (America/Vancouver).
Outcome: **design and non-private validation complete; stopped for review**.

## Authorization and starting state

The user explicitly authorized the next research direction: study the references,
write candidate pseudocode, investigate correctness, sensitivity, independence,
privacy accounting and likely utility, and prepare a mathematical-review report.
This superseded the phase-04 stop only for that scope. A full private 4-clique
implementation and large utility experiments were not authorized and were not
started. No private ordering, RR sampler or private 4-clique API was added.

Read AGENTS.md, STATUS.md, REVIEW_PACKAGE.md, checkpoints 01–04, source review,
algorithm/privacy/experiment and ESCAPE documentation before completing this
phase. The project started clean at
`8b0735e6b48559d86d1dcd943c6b44920ff736b3` (`phase 4`). The user reports
independent 3-star review, but supplied no memorandum or detailed conclusions;
none are invented here. Historical reports and 3-star code remain unchanged.
Changes are local and uncommitted; no commit or push was performed.

## Files created or updated

| File | Purpose |
|---|---|
| `docs/FOUR_CLIQUE_DESIGN.md` | Exact identities/proofs, source findings, candidate pseudocode, full release/budget ledger, sensitivity derivation, cap bias, covariance, baseline comparison, review questions and next-phase requirements. |
| `scripts/check_four_clique_design.py` | Non-private exact counters and finite rational/algebraic design checks; calls the existing ESCAPE adapter. No private estimator. |
| `docs/status/validation_05.json` | Small intentional evidence summary, actual graph/order/check counts, named cases and raw-report/script/executable hashes. |
| `docs/status/STATUS.md` | Current phase checklist, evidence, conditional findings and explicit new stop. |
| `docs/status/checkpoints/05_four_clique_design.md` | This work and verification record. |
| `README.md` | Link current design/review scope and the non-private reproduction command; preserve existing implementation commands. |

Ignored generated evidence: `build/phase05/design_checks.json` (794,891 bytes),
`design-checks.log`, `escape/{count_four,build.json,compile.log}`,
`pytest.{log,xml}`, and `references-after.json`. The raw report contains original
inputs and actual ESCAPE stdout/stderr/`out.txt` for all cases, separately named
Python counts, full build provenance and algebra results. The compact summary
is not a substitute for that raw report; transfer or regenerate it separately.

No dependency was installed, added or upgraded. Python **3.11.16** and the
existing `.venv`/locked dependencies were used. The lock remains
`ffbb7a1cbe39daaaecba70d68bdd163d5e8e27bbf3a39f17a47f6e13fff6ed4f`.
No production package module or existing test changed.

## Source and paper investigation

Read the pinned external files in place using `rg`, `sed`, `nl` and `cat`;
inspect build information without running upstream setup/experiment scripts.
ESCAPE commit is `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3`; Go commit is
`b03da893ba1c38d3931708bac919562c5ab57963`. Read-only fingerprinting confirms
all 82 and 127 tracked files respectively match `docs/references.json`, with
empty Git porcelain output for both trees. Compilation occurs in this project.

Primary literature consulted:

- [ESCAPE, WWW 2017](https://www.cs.cornell.edu/courses/cs6241/2020sp/readings/Pinar-2017-ESCAPE.pdf),
  particularly Section 6, Figure 3 and Theorem 7.
- [Mundra et al., PVLDB 2025](https://www.vldb.org/pvldb/vol18/p4199-mundra.pdf),
  k-CoreD and EdgeOrientΔ algorithms and their privacy/utility statements.
- [Suppakitpaisarn et al., AISTATS 2025](https://proceedings.mlr.press/v258/suppakitpaisarn25a.html),
  Algorithm 1/Definition 2/Theorem 3.4 in the authors' accessible
  [arXiv v1, 19 May 2025](https://arxiv.org/pdf/2505.12954).

The proceedings page's raw-GitHub PDF link failed to render in the web reader
(`application/octet-stream`); the arXiv author version was used and identified
explicitly. This is a source-access fallback, not a failed computation. An
initial status-file editing patch was rejected for targeting the same path
twice; a single-update patch resolved it without losing content. No test,
build or comparison failed; no permission blocker arose.
We did not reproduce either paper's private algorithm or import its guarantees
onto our proposed protocol.

Findings are detailed in the design document:

- The Go pair loop uses adjusted RR closing-edge indicators on actual outgoing
  neighbors. Its equal-level coins are independent across endpoints/stages;
  they do not supply the consistent DAG needed for a clique identity. Its
  count-noise arguments and the cap need a fresh sensitivity/bias audit.
- The candidate uses final private levels plus public IDs, not coarsened core
  estimates. Publishing the true oriented graph or selected neighbors is excluded.
- ESCAPE closes pairs of forward triangles around the first edge of a clique.
  This is an independent exact oracle. Its true-edge pruning cannot be imported
  into LEDP without analyzing access to those additional private leaf edges.
- The candidate's RR uses one report per unordered pair from a fixed owner,
  independent across pairs and from ordering/cap noise. Reuse across triples
  preserves each expectation but induces covariance across roots.
- For fixed transcript and prefix cap, a sufficient local bound is
  `choose(B-1,2)*M^2*(M+a)` with `a=1/(exp(epsilon_R)-1)` and `M=a+1`.
  Replacement matters: a small example changes a score by 12 when `M^3=8`.
- The design allocates `epsilon_O+epsilon_D+epsilon_R+epsilon_C=epsilon`, with
  illustrative quarters. Conditional cap degree-vector sensitivity is 1;
  local count sensitivity uses the bound above. All local noise precedes the
  untrusted coordinator. The ordering contract and every transcript still need
  formal review; merely adding Laplace noise is not a proof.
- An enforced cap can lose real cliques (K5 retains 2 of 5 with cap 3). A noisy
  upper cap reduces loss probability but does not make it exactly zero.
- A triangle with many earlier centers has out-degree at most 3 but quadratic
  RR variance in the number of centers. Low out-degree alone is not enough for
  an independent-root variance analysis.
- The appropriate general baseline is debiased RR, spending the same total
  undirected-edge budget. Three factors instead of six may help, but extra
  budget splits, local Laplace noise, cap loss and correlations may dominate.
  No empirical or theoretical superiority is claimed.

## Commands and actual results

Executed from `/home/tsshergi/CMPT479Project`:

```bash
mkdir -p build/phase05
set -o pipefail
ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python scripts/check_four_clique_design.py \
  --summary docs/status/validation_05.json | tee build/phase05/design-checks.log

ESCAPE_ROOT=/home/tsshergi/escape .venv/bin/python -m pytest -q \
  --junitxml=build/phase05/pytest.xml > build/phase05/pytest.log 2>&1

.venv/bin/python scripts/reference_fingerprints.py > build/phase05/references-after.json
git diff --check
git status --short
.venv/bin/python scripts/check_four_clique_design.py --help
```

The build command saved in `escape/build.json` is equivalent to:

```bash
g++ -std=c++11 -O2 -Wall -I /home/tsshergi/escape \
  /home/tsshergi/escape/exe/count_four.cpp \
  /home/tsshergi/escape/Graph.cpp /home/tsshergi/escape/GraphIO.cpp \
  /home/tsshergi/escape/TriangleProgram.cpp \
  -o /home/tsshergi/CMPT479Project/build/phase05/escape/count_four
```

The adapter actually compiles to an isolated temporary output and then moves the
successful binary into place; `build.json` preserves that exact temporary path.
It exited 0 with **160 existing upstream warnings**. The adapter then executes
the binary in separate temporary working directories. Graphs below four vertices
are padded with isolates; existing size/precision guards are retained.

| Check | Observed result / scope |
|---|---|
| Graph comparisons | **1,112 passed**, actual ESCAPE equals brute-force K4, oriented-triple and directed-diamond counts. |
| Exhaustive graph portion | **1,100** labeled simple graphs for n=0–5, every vertex permutation. |
| Other graphs | **12** examples through n=10, six orders per example. |
| Order checks | **124,542 passed**. Non-private peeling/mock levels are test inputs, not private ordering outputs. |
| RR product means | All **8** three-edge truth configurations pass exact rational expectation checks at RR epsilon `log(2)`. |
| Conditional sensitivity | **10,240 passed** across all RR tables on four prospective neighbors, raw root sets, single additions and caps 0–4; deletions have identical absolute differences. |
| Counterexamples | Shared RR coin on three absent pairs has mean product **2**; K5 cap 2/3/4 counts **0/2/5**. |
| Full configured pytest | **256 passed in 14.49s**, zero failures, errors or skips. |
| ESCAPE regression coverage | **34 marked integration cases passed within that full run**: 33 in `test_escape_integration.py` plus the saved-pipeline case in `test_experiments.py`. No separate integration-only rerun was needed. |
| External tree integrity | **82 ESCAPE + 127 Go tracked files unchanged**, clean worktrees. |
| Existing project integrity | Source package, tests, pins, checkpoints 01–04 and phase-04 handoff match starting HEAD. |

Graph generation is completely specified in the script. Beyond exhaustive
graphs: K6, K7, star n8, path n8, K3,3, cycle n6, K4 plus four isolates,
four centers on a common triangle, ER(n8,p=.4,seed5001),
ER(n10,p=.7,seed5002), BA(n10,m3,seed5003), and SBM([5,5],
[[.6,.2],[.2,.6]],seed5004). The six orders are ID, reverse ID, degree/ID,
exact peeling, shuffle seed `2026102905`, and mock `(7*v)%3` levels with ID ties.
There are **no private mechanism seeds or sampled private estimates** in this
phase; the RR algebra enumerates every possible bit report using fractions.

Inline Python audit commands compared fingerprint JSONs, checked the lock hash,
parsed JUnit XML and used `git diff HEAD -- ...` to verify preserved files.
Final checks **passed** for 36 local Markdown link targets, balanced code fences,
raw-report/script hashes, result consistency, ignored generated evidence and
whitespace. The script's help command succeeded. Checkpoint/status links are
relative so they work in a clone. No timing/utility benchmark was run.

## Limitations and next steps

Finite exact checks support the combinatorial identities and catch specific
mathematical mistakes; they do not prove LEDP, arbitrary-parameter sensitivity,
independence of a future RNG implementation or accuracy dominance. The general
arguments are written for independent review. In particular, the k-CoreD full
transcript contract remains a prerequisite, not a verified component of our
package. Cap bias, overlap-dependent variance, communication costs, finite
precision and side channels are unresolved implementation/theory obligations.

The private 4-clique estimator, private-ordering integration and utility grid are
not implemented. No real confidential graph was used. No package rebuild or
fresh environment recreation was necessary for this docs/design-only phase;
the existing configured environment ran the checks. No new statistical privacy
claim or 3-star review conclusion is inferred from these results.

Send the files listed at the end of `FOUR_CLIQUE_DESIGN.md` and the separate raw
evidence to an independent researcher. Obtain review of the target/cap choice,
conditional sensitivity, transcript composition and covariance formula before
authorizing implementation. Milestone scope and any future empirical comparison
must be agreed explicitly. **STOP here; no next phase without follow-up.**
