# Checkpoint 16 — P4 Phase 5A: AISTATS 2025 baseline

Date: 2026-11-06 (America/Vancouver). **Complete; stop before Phase 5B.**

## Scope and saved state

The resumed session inspected a clean working tree at `8849987` (4-Path:
Phase 5A step). Already saved were:

- `src/private_graphlets/four_path_baseline_2025.py`: independent Algorithm 1
  reconstruction, single owned-pair RR transcript, server-only cubic polynomial,
  budget/result/transcript/run APIs, guards and explicit research provenance.
- `tests/test_four_path_baseline_2025.py`: 57 tests, exhaustive normalization,
  bounded transcript expectations/variance, eight ESCAPE fixtures, seeded checks.
- `docs/FOUR_PATH_BASELINE_2025.md`: pre-implementation source gate,
  paper/notebook reconstruction, ideal privacy and independent error derivation.

The saved implementation required no algorithm correction. Resumption completed
fidelity review, API/test/limitation documentation, current README/ALGORITHMS/
PRIVACY_NOTES/STATUS updates and this new checkpoint, then verified the saved
implementation again. No code or test file was edited during resumption.

## Source-verification conclusion

**Faithful independent reconstruction**, not an exact reproduction of author P4
code (none exists at the pin), and not an approximate replacement estimator.
The proposed Algorithm 1 itself multiplies debiased RR weights; the classical
comparator counts uncorrected perturbed-graph edges. P4 divides ordered distinct
paths by its two automorphisms. This estimates non-induced unlabeled copies.

Algorithm 1 lines 1–4, Section 2.3 Definition 4, and Lemmas 3.1–3.2 identify
randomization, correction, normalization and unbiasedness. The estimator displays
are unnumbered. Lemma 3.3 equation (1) is the overlap argument, not the estimator
formula. Section 2.1 defines L2 error as RMSE; Theorem 3.4 gives fixed-epsilon
O(n^3) for P4. Section 7 leaves explicit joint epsilon dependence unresolved.
Supplementary Section 8 adds lower-bound proofs, not a different mechanism.

The paper leaves endpoint duplication unclear. The linked C4 notebook samples
only i<j and mirrors it. We explicitly adopt that convention, with public
lower-ID ownership. A changed undirected edge then changes one RR coordinate;
the ideal transcript likelihood ratio is bounded by exp(epsilon). Independent
duplicate endpoint releases at epsilon would cost 2epsilon instead. Neither
finite-law tests nor this ideal argument certify executable floating-point DP.

The O(n^3) middle-edge identity is our mathematically exact server refinement of
the literal O(n^4) tuple sum. The explicit epsilon-dependent MSE upper bound and
centered-noise variance oracle are independently derived here, not attributed
to a numbered paper equation. Full derivations, exact source map, paper hash,
notebook cell references, all APIs, costs and limitations are in the
[technical report](../../FOUR_PATH_BASELINE_2025.md).

## Actual verification

Exact commands are recorded in the technical report's executed-verification
section. Before interruption: baseline 57 passed in 2.94s; combined baseline,
exact P4, ESCAPE and RR tests 236 passed in 4.79s; full regression 878 passed in
30.92s (pre-addition baseline 821 passed in 31.76s).

After resumption:

- Baseline tests: **57 passed in 3.50s**.
- Full regression with `--junitxml=build/phase16/resumed-full.xml`:
  **878 passed in 32.15s**.
- Reference verification: exit 0, all three verified with clean source trees.
- Preservation snapshot: **55 files checked, zero changed hashes**.
- Final `git diff --check`: exit 0; final status contains only the six
  documentation paths listed below, with no source/test/reference changes.

No test failures, errors or skips in these runs. All 1,100 labeled simple graphs
on zero through five vertices satisfy the deterministic identity. All 64
four-vertex graphs use all 64 possible pair-report transcripts at epsilon log(2)
for exact finite-law mean/variance checks. Actual native ESCAPE validates eight
fixture targets. Eight fixtures each use 3,000 fixed-seed epsilon-2 draws;
maximum absolute standardized mean discrepancy is 1.833, below the declared
six-analytic-SE threshold. These 24,000 draws are bounded correctness checks,
not Phase 5B comparisons. Negative/fractional values remain unchanged.

Reference pins unchanged: ESCAPE `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3`,
LEDP `b03da893ba1c38d3931708bac919562c5ab57963`, baseline
`85eff6efa2b1d649ee238620a998ec7f1d305aac`. No dependency changes. The baseline
reference has no license file; existing owner-reported academic permission is
preserved without assigning a license or disclosing correspondence.

Local ignored evidence: `build/phase16/paper.pdf`, `paper.txt`, `moments/`,
`escape/`, `resumed-full.xml`, `resumed-references.json`, `preservation.json`.
Source browser/download issues were resolved through the official PDF and
approved download; no unresolved source-access blocker remains.

## Final documentation changes

`README.md`, `docs/ALGORITHMS.md`, `docs/PRIVACY_NOTES.md`,
`docs/FOUR_PATH_BASELINE_2025.md`, `docs/status/STATUS.md`, and this checkpoint.
Earlier checkpoints are retained as historical records. No commit or push.

## Limitations and next authorized phase

The n<=100 implementation is a centralized NumPy simulator, not a deployed
local protocol or cryptographic sampler. Floating-point privacy and operational
side channels remain unverified. The independent epsilon bound is loose and
not a ranking of methods. No P4 author code or published P4 experiments exist
at the pinned reference. The classical control is optional and deferred.

Phase 5A is ready for a separately authorized Phase 5B comparison with common
non-induced targets, compatible undirected-edge accounting, equal total budgets,
independent trial coordinates, uncertainty and runtime reporting, and retained
negative estimates. Candidate composition still needs independent review.
No comparative sweep, scaling study or comparative plot was performed. Existing
private estimator, budgets, Phase 1–4B results and references remain unchanged.
