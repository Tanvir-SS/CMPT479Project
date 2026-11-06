# Requested Phase 8 — Four-clique privacy audit

2026-11-06 (UTC). **Completed before Phase 9. Overall result: PARTIAL.**
The ideal complete-transcript composition proof is established for exact stage
allocations/ideal independent randomizers; the executable research simulator
remains `experimental_unverified`. No estimator or allocation was redesigned.
This is distinct from the preserved historical `08_macos_setup.md`.

## Revision, scope and source-to-proof record

Initial inspection found clean `f369d291f78c3908fac8cb60d163afce065eb2d8`, behind
origin/main by two commits. The checkout advanced externally during inspection
to clean **`6fba863e984fda8f55c016655df7ded917cc0576`**, including completed P4
work. We did not pull, branch, commit or push. The clique mechanism, k-CoreD,
RR, baseline, adapter and Phase-6 config/runner are unchanged across this advance.
The current revision is the audit target. Read the newly current checkpoint 12
and preserve all P4 source/reports. Capture both starting snapshots and rerun
baseline tests rather than attributing old results to the new suite.

Read AGENTS, README, TEAM_SETUP, current status, Phase 5–7 reports, current
clique design/implementation/k-CoreD audit/review files, actual source and tests.
Inspected pinned Go threshold/promotion/coordinator/RR/triangle/noise sources,
ESCAPE orientation and clique closure, and both baseline notebook code cells.
Consulted the primary PVLDB paper Algorithms 3.1–3.3/Theorem 3.3, ESCAPE Section 6,
and the AISTATS author version Algorithm 1. Sources and attribution are linked
in [FOUR_CLIQUE_PRIVACY_PROOF.md](../../FOUR_CLIQUE_PRIVACY_PROOF.md).
All three submodules verify at their unchanged pins.

The proof's Section 2 contains the **complete code-to-proof mapping**, function
locations, all private inputs, randomness, messages, public operations and
pseudocode. `build/phase08/source_map.json` contains source hashes and definition
line numbers for kcore, four_clique, exact helpers, RR, baseline, CLI and ESCAPE.
The full logical transcript includes thresholds/all round bits, order, Q/B,
the full one-owner RR table, all already-noised local reports and the sum.

## Final privacy statement and stages

For fixed public V and one-undirected-edge adjacency, exact independent ideal
kernels and the prescribed local release boundary give pure
**epsilon-star = O+D+R+C LEDP** for every measurable full-transcript event.
Requested-epsilon LEDP follows when the exact sum is <=requested epsilon.
Public order/cap and configuration must be genuinely public or previously charged;
seeds and local RNG states are secret, with no memory/timing/error side channels.
This theorem does not certify the executable distribution or a distributed deployment.

| Stage | Proven ideal full-stage cost | Reason |
|---|---|---|
| Ordering | O | Two endpoint degree queries at fO/2 each; <=t_v promotion queries per endpoint at (1-f)O/(2t_v), conditioned on released histories. |
| Noisy outgoing cap | D | Fixed-order outgoing-degree vector has L1 sensitivity **one**; local scale 1/D. |
| RR | R | Exactly one affected lower-public-ID-owned pair; every edge/nonedge reported once. |
| Local scores | C | Full-vector fixed-transcript sensitivity Delta_B; independent local Laplace scale Delta_B/C. |
| Levels/order/cap/aggregate | 0 additional | Postprocessing already charged reports. |

For B<3, Delta_B=0. Otherwise the verified bound is
`C(B-1,2)*M^2*(M+a)`, a=1/expm1(R), M=a+1. Prefix selection allows insertion,
deletion or replacement. Replacement uses the two-weight product range
[-aM,M^2], giving M^2(M+a) per common pair. Only the earlier endpoint's score
changes at fixed prior transcript, so this is a vector L1 bound, not merely a
local bound. All **294,912** exhaustive n=4 neighboring-vector comparisons pass;
1,024 full n=5 RR tables cover replacement/deletion and attain 12 at R=log(2),B=3.
No formula replacement is required.

The cap tail is sharper than the previously proposed beta/2 statement. If d>0,
`P(B<d|G,pi)=product_v F_L(d-1-log(n/beta)/D-q_v)` and is at most
`beta*exp(-D)/(2n)`; r maximizers give that quantity to power r. For d=0 it is
zero. The ceil operation accounts for the extra exp(-D). No good-cap event is
needed for the privacy proof; beta is not a DP delta.

## Discrepancies and limitations found

1. Floating `math.isclose` validation permits a small nominal-budget overspend:
   `CliqueBudget(2,0,0,1,1+1e-14)` has sum `2.0000000000000098`. The theorem uses
   exact actual allocations; source tolerance is not exact requested-epsilon
   accounting. Default/API behavior was preserved and the limitation documented.
2. A public fixed seed makes the simulator deterministic. Neighboring four-vertex
   graphs produce opposite bits for the changed pair under the same seed; the
   conditioned transcript has a 1-versus-0 event. This is an explicit limitation,
   not a privacy-testing certificate. Neither hidden seeded nor unseeded NumPy
   draws establish secure/ideal independence.
3. The initial geometric range guard does not prevalidate all threshold-dependent
   round parameters. The n=4 empty graph, O=4e-10, seed=8 example errors during
   promotions after initial validation. The earlier source comment overstates
   the guard. These public-history-dependent aborts and all numeric exceptions
   are separately identified; exact-kernel DP is not claimed for execution.
4. Go/paper group/round constants differ; Python explicitly releases all thresholds,
   fixes ties with IDs, uses a different sampler and explicit n<4 shortcut. Direct
   privacy reasoning covers the ideal control flow, but no ordering utility
   theorem is inherited. Paper “same or higher” queries coincide with “same” for
   eligible level-r clients under the synchronous maximum-level-r invariant.
5. Finite-support/discretized randomness, raw local-score overflow checks, timing,
   access patterns, input validation and whole-process graph ownership remain
   outside the proved local transcript boundary. Never publish exact diagnostics
   alongside a protected release and call them postprocessing.

No concrete structural defect invalidates ideal composition or prevents meaningful
ideal error analysis. **PARTIAL** reflects the unresolved executable/nominal-budget
contracts; it is not a claim that tests prove privacy. Future numerical accounting
or secure deployment changes require independent review, not budget tuning here.

## Files and verified regression fix

Created `docs/FOUR_CLIQUE_PRIVACY_PROOF.md`,
`tests/test_four_clique_privacy_audit.py`, and this checkpoint. Updated AGENTS and
STATUS to reflect this explicit request while retaining previous history.

A pre-existing current-revision test failed in non-private
`src/private_graphlets/four_path_study.py::verify_study`: CSV reads an undefined
relative metric as NaN while the recomputed summary used None. Strict pandas
FutureWarning handling turned its comparison into a failure. A three-line fix
normalizes recomputed missing values with `expected.where(expected.notna(),nan)`
before the existing strict comparison. No numbers, tolerances, estimator, study
config or saved artifacts changed. This compatibility fix is the only edited
production source file; it is not a new P4 study or extension.

## Actual commands and outcomes

```bash
# Initial f369d29 checkout:
.venv/bin/python -m pytest -q --junitxml=build/phase08/before.xml
# After external checkout advance, before audit additions/fix:
.venv/bin/python -m pytest -q --junitxml=build/phase08/before_current.xml
.venv/bin/python scripts/reference_fingerprints.py --verify

.venv/bin/python -m pytest -q tests/test_four_clique_privacy_audit.py \
  --junitxml=build/phase08/audit.xml
.venv/bin/python -m pytest -q tests/test_four_clique_privacy_audit.py tests/test_four_path_study.py \
  --junitxml=build/phase08/targeted.xml
.venv/bin/python -m pytest -q tests/test_four_clique_privacy_audit.py tests/test_kcore.py \
  tests/test_four_clique_core.py tests/test_four_clique_protocol.py tests/test_four_path_study.py \
  --junitxml=build/phase08/final.xml
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase08/references_after.json
git diff --check
```

| Check | Observed outcome |
|---|---|
| Initial older revision baseline | **392 passed in 29.14s**. |
| Current revision baseline | **1 failed, 679 passed in 47.26s**; existing P4 None/NaN FutureWarning, not a clique failure. |
| New Phase-8 checks | **26 passed in 1.89s**. |
| New checks plus P4 verifier regression | **47 passed in 8.68s** after the representation fix. |
| Final targeted mechanism/ordering/baseline/P4-verifier suite | **153 passed in 18.48s**, no skips/errors/failures. |
| Source fingerprints | All three exact pins/content verified; no third-party changes. |

Tests include all cap modes, public B<3, endpoint vector changes, conditional
geometric likelihood algebra, ordering schedule/ties/query limits, budget modes,
RR ownership/report schedule, replay, extreme supported/invalid parameters and
explicit simulator limitations. Existing distribution/independence tests remain.
No statistical tolerance or correctness assertion was weakened.

Host: Linux/WSL2 x86_64, Python 3.11.16, existing lock unchanged. No macOS execution
was available in this audit; its earlier setup results are historical. All new
tests use standard Python/NumPy/pytest and avoid platform-specific APIs.

**Phase 8 complete. Proceed only to the user-authorized Phase 9 ideal error
analysis; do not infer executable privacy from the completed proof/tests.**
