# Checkpoint 12 — Four-path accuracy validation

Date: **2026-11-05 (America/Vancouver)**.
Status: **COMPLETE — Phase 4A stopping point; Phase 4B not started.**

## Scope, prerequisites and preservation

Owner authorized ideal MSE analysis, non-private evaluation infrastructure and
one small validation study. Read AGENTS.md, project setup/dependency information,
privacy/triangle/P4 documents, checkpoints 09–11 and existing code/test/experiment
conventions. Phase 3 files were already pending at the start; preserve them.
No private correctness defect was found, so no private estimator/mechanism,
Phase 1–3 tests, source pin, dependency lock or third-party source was changed.
No new dependency, setup script, plot, baseline, large sweep, commit or push.

## Files

Created:

- `src/private_graphlets/four_path_accuracy.py`
- `src/private_graphlets/four_path_experiments.py`
- `scripts/run_four_path_experiments.py`
- `experiments/configs/four_path_phase12_validation.json`
- `tests/test_four_path_accuracy.py`
- `tests/test_four_path_experiments.py`
- `docs/FOUR_PATH_ACCURACY.md`
- `docs/status/checkpoints/12_four_path_accuracy_validation.md`

Focused documentation updates: `README.md`, `docs/ALGORITHMS.md`,
`docs/PRIVACY_NOTES.md`, `docs/status/STATUS.md`. Prior checkpoints/results remain.

## Mathematical finding and implemented boundaries

The supplied complete MSE identity is correct for the ideal independent-stage
mechanism. For fixed G and H=(O,B), expand error as
Q(Z)+sum U_uv*(X_u X_v-3c_uv)-3 sum L_v+3M, where
Q=sum g_v Z_v+sum_{uv in E} Z_u Z_v. Zero-mean independent RR/count randomness
makes omitted cross terms zero; Var(Q)=s sum g_v^2+s^2m. The resulting identity is

```text
MSE = s sum g_v^2+s^2m
    + h E_H sum_{u<v}[(t_u t_v-3c_uv)^2+s(t_u^2+t_v^2)+s^2]
    + (18n/epsilon_C^2) E_H[Delta_T(B)^2]
    + 9 E_H[M(H)^2].
```

The calculator reports degree noise, unadjusted RR variance, the signed -6Cov
adjustment, local-count Laplace variance and squared truncation error separately.
A compact square-form RR term avoids cancellation in the total. It distinguishes
conditional variance/bias, E[M^2], (E[M])^2 and between-history variance.
Exact retained/missed counts use integers. No exact data enter private outputs.

Prediction samples only private ordering and cap with independent trial seeds.
Full simulation calls the unchanged five-stage estimator in a disjoint seed domain.
Mechanism result/transcript JSONL is separated from non-private seeded CSVs,
exact graphs/counts, analytical contributions and timings. All artifacts belong
to a non-private synthetic study, not an LEDP release. Source/software/config
provenance, artifact hashes, refused overwrites and full replay are implemented.

API signatures, derivation, independence conditions and complexity are detailed
in `docs/FOUR_PATH_ACCURACY.md`. Existing generation/hash/provenance/coordinate
seed utilities are reused; no plotting or baseline command is added.

## Actual test commands and outcomes

Fresh baseline:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

**587 passed in 20.21s**, 0 failures/errors/skips.

New accuracy/infrastructure tests:

```bash
.venv/bin/python -m pytest -q tests/test_four_path_accuracy.py tests/test_four_path_experiments.py
```

**72 passed in 1.95s**, 0 failures/errors/skips. Forty parameterized moment
checks cover five four-vertex graphs (including isolates), two orders, and caps
0/1/2/n-1. Independent RR/degree moment enumeration checks covariance-sensitive
MSE; a mixed K4 cap-1/cap-3 history checks 72 versus 36 for E[bias_H^2] versus
E[bias_H]^2. Other tests cover finite outputs, predictor-only randomness, schema
boundaries, disjoint seeds, replay, corruption, configuration and overwrite guards.

Targeted Phase 4A/3/2/1 regression:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q tests/test_four_path_accuracy.py tests/test_four_path_experiments.py tests/test_four_path_protocol.py tests/test_triangle_protocol.py tests/test_four_path_exact.py
```

**267 passed in 4.71s**, 0 failures/errors/skips, including actual ESCAPE fixture
comparisons from Phase 1.

Final full suite:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q
```

**659 passed in 21.24s**, 0 failures/errors/skips. No test was weakened. No test
or statistical check failed in this phase. Numerical/configuration failures and
corrupted files in tests are intentional asserted error cases, not suppressed
verification failures.

## Pilot execution and replay

```bash
.venv/bin/python scripts/run_four_path_experiments.py run
.venv/bin/python scripts/run_four_path_experiments.py verify --replay
```

Run exited 0: **5 graphs, 1500 full trials, 1500 prediction trials**, pipeline
time **0.44778587529435754 seconds**. Verify exited 0 with all trials replayed.
Outputs are ignored under `experiments/results/four_path_phase12_validation/`.
This directory was created once, not overwritten. Test runs use disposable
temporary directories and tiny trial counts.

Fixed settings: D=2,O=.5,R=1,M=1,C=2 (total 6.5), beta=.05; master seed
202611051204; ER graph n=8,p=.35, seed 120401. Each graph uses 300 independent
full trials and 300 independent H samples. Thresholds were declared in config
before the run: discrepancy multiplier 3 and maximum relative combined SE .25.
No data-dependent seed/tolerance/sample-size tuning or automatic expansion.

| Graph | Exact P4 | Exact T | Empirical MSE | Empirical SE | Predicted MSE | Prediction SE | Relative discrepancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| path | 1 | 0 | 472.341270 | 47.925826 | 395.334329 | .239592 | +19.4789% |
| cycle | 4 | 0 | 501.130803 | 66.173978 | 442.981504 | .500192 | +13.1268% |
| diamond | 6 | 2 | 558.293463 | 47.383580 | 594.953528 | .660509 | -6.1618% |
| clique | 12 | 4 | 859.143392 | 83.440740 | 809.351201 | 0 | +6.1521% |
| er8 | 38 | 3 | 7817.094418 | 724.529537 | 7488.715618 | 1.021146 | +4.3850% |

All five are `no_discrepancy_detected` under the predeclared combined-SE rule.
This is limited consistency evidence, not precise empirical confirmation. Every
graph has mean missed triangles 0 and truncation frequency 0 in both sampled
streams. The pilot does not empirically validate nonzero truncation; deterministic
tests explicitly cover it. It does not prove truncation probability zero.
The focused accuracy document includes empirical means/bias/variance/RMSE and
mechanism runtimes; the saved summary retains full precision and decompositions.

## Preservation checks

```bash
.venv/bin/python -B scripts/reference_fingerprints.py --verify
git diff --check
git status --short
```

All three pinned references verified with clean statuses, exit 0. Whitespace
check passed. Existing private source content was preserved. Generated results,
transcripts, caches and native build artifacts remain ignored. Source hashes
are saved in the study manifest alongside dependency versions and Git state.

## Bounds, costs and limitations

At fixed positive allocations, degree-noise terms are O(n^5), compact RR terms
O(n^6), triangle noise O(n^3), and squared missed triangles O(n^6). Thus ideal
MSE=O(n^6), RMSE=O(n^3). For K_n, every compact RR square is at least
[(n-2)(n-5)]^2 for n>5, giving a matching ideal Omega(n^6) RR contribution.
These are mathematical bounds for the ideal asymptotic family, not empirical
scaling or guarantees about the n<=1000 floating-point executable. Sparsity,
bounded degree/cap and smaller T give graph-dependent improvements as derived
in the accuracy document; none establishes superiority to an unrun baseline.

Evaluation computes exact counts using adjacency intersections (worst O(n^3)),
closing multiplicities with outgoing sorting and O(nB^2) pair enumeration,
and conditional formula sums in O(n^2) plus those costs. Prediction adds
O(r(n+m)+n log n) ordering and O(n+m) cap work without sampling other stages.
Full simulation costs remain unchanged; analytical diagnostics are timed
separately. Trial rows and serialized histories use O(F+Pn) memory; verification
also loads one graph's full JSONL transcripts, O(F_graph*(n^2+nr)). Hashing/I/O
are linear in artifact bytes, and replay repeats computation. These costs are
not part of private mechanism accounting. Full dense RR dissemination can still
cost O(n^3); physical communication is not implemented.

Independent mathematical/privacy review, numerical/PRNG/error/timing behavior
and actual client isolation remain unresolved. Pilot sampling uncertainty is
substantial and covers only five small graphs. Infrastructure supports a
separately authorized Phase 4B study with predeclared precision/truncation coverage;
it does not justify a utility-superiority claim. **Stop before Phase 4B.**
