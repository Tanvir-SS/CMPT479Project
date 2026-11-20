# Supplied RR-only diamond estimator: integration

2026-11-19 (America/Vancouver). Integrated the owner's supplied estimator into
`src/private_graphlets/diamond_rr_only.py`. Existing algorithms, including
`randomized_response.py` and the hybrid diamond estimator/runner, are unchanged.
This phase adds compatibility checks, not a new benchmark study or privacy proof.

## API and correspondence

```python
from private_graphlets.graph import load_edge_list
from private_graphlets.diamond_rr_only import estimate_rr_only_diamonds

graph = load_edge_list("data/fixtures/diamond.edges")
result = estimate_rr_only_diamonds(graph, epsilon=1.0, seed=2905)
print(result.to_dict())
```

`sample_rr_upper(graph, epsilon, rng)` and `rr_matrix(n, bits, epsilon)` are
imported directly from the existing RR module. There is no replacement sampler,
debiasing implementation, orientation, cap, Laplace stage or degree query.
All epsilon is passed to RR. Each unordered pair, including nonedges, has one
lower-public-ID owner as already implemented there. The existing supported RR
parameter range (including epsilon<=30) and its errors propagate unchanged.

The owner's budget clarification specifies epsilon **0.5, 1, 2** for evaluation:
epsilon_RR=epsilon_total, epsilon_Laplace=0 and epsilon_Ordering=0. There is no
budget split or optimization. Every possible unordered pair receives exactly
one report using the same full epsilon. Under the ideal one-edge adjacency
model, only one pair's input bit changes, so the joint RR-table privacy cost is
epsilon, not the number of pairs times epsilon. The final diamond estimate is
post-processing of that table. No extra noise, rounding or clipping is added.

`diamond_polynomial(W)` uses exactly the supplied identities:

```text
P = W @ W
Q = (W*W) @ (W*W)                  # * is entrywise
Dhat = sum_{a<b} W_ab * (P_ab² - Q_ab)/2
```

The symmetric zero diagonal of W excludes the central endpoints from common
neighbors. The subtraction removes identical outer vertices. Counts are
non-induced unlabeled edge-subgraphs: K4 contributes six diamonds. Time is
O(n³), temporary storage O(n²). Negative/fractional estimates remain intact.

Changes relative to the pasted source are limited to normal Python formatting,
boundary validation and repository metadata conventions:

- Normalize input to floating arithmetic to avoid integer-matrix overflow in
  offline calls; reject nonfinite, nonsquare, nonzero-diagonal or asymmetric
  matrices. Exact symmetry replaces `allclose` because shared RR output is
  exactly mirrored. Overflow/invalid arithmetic raises explicitly.
- Preserve all supplied result fields and add `privacy_status=experimental_unverified`
  to distinguish the retained ideal-model label from executable certification.
- Normalize accepted integral simulation seeds to Python integers. The supplied
  sampling and counting formulas and epsilon allocation are unchanged.

The result contains public n/epsilon and the estimate/semantic labels. Seeds,
exact counts and graph structure are absent. Both seeded and unseeded NumPy
sampling are research simulations, not cryptographic deployment randomizers.
The `ideal_pure_edge_LDP_one_owner` label describes the intended ideal protocol;
these integration tests do not establish formal or executable DP.

## Separate evaluation entry point

`scripts/evaluate_diamond_rr_only.py` follows the existing six-dataset conventions
and writes only to its own default directory:
`experiments/results/diamond_rr_only_six_datasets/`. Existing hybrid config,
script, results and plot paths are not reused or modified. No evaluation script
accompanied the pasted module; this new entry point defaults to the established
six graphs, epsilon .5/1/2 and 200 trials, with an explicitly supplied master seed.
The clarified grid therefore prepares 3,600 trials (18 cells); none has been run.

```bash
# Safe input/configuration check: ZERO estimator calls, no experiment output.
.venv/bin/python scripts/evaluate_diamond_rr_only.py check --seed 202611192901

# Future experiment commands, prepared but NOT executed in this integration:
.venv/bin/python scripts/evaluate_diamond_rr_only.py run --seed 202611192901
.venv/bin/python scripts/evaluate_diamond_rr_only.py run --seed 202611192901 --resume
.venv/bin/python scripts/evaluate_diamond_rr_only.py verify
```

The runner resolves pinned inputs from the manifest, verifies graph/mapping
hashes, and reuses cached native ESCAPE diamond counts. It passes the full
epsilon to the new estimator without hybrid O/R/W allocation or cap fields.
It saves per-observation SQLite commits and exports trials/summary CSVs at cell
boundaries and on exit. Resume checks sources, settings, data and versions,
then processes only unsaved coordinates. Existing output cannot be overwritten.
Seeds use `(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial`; CSV seed
columns must be read as strings. Execution metadata includes source/data hashes.
Exact truth and seeds belong to non-private evaluation records only.

Summaries use population variance, direct MSE, RMSE, signed bias, MAE, MAE/truth,
relative RMSE and runtime. Relative metrics are empty for zero truth. No rounding,
negative-value clipping, plots, automatic comparisons or parameter tuning occur.

## Actual verification

Initial integration: `.venv/bin/python -m pytest -q tests/test_diamond_rr_only.py`:
**26 passed in 0.99s**, no failures/skips. Tests cover eight cached exact fixtures,
the weighted polynomial against explicit outer-pair enumeration, small public
universes, signed fractional output, read-only matrices, invalid inputs, direct
shared-RR dispatch at full epsilon, result serialization and reproducibility.
The runner test uses only two tiny edgeless fixture calls in a temporary directory
to check save/resume/no duplicate execution, zero-truth metrics and output safety.
It does not label fixture outputs as benchmark or ESCAPE runs.

After the owner's budget clarification, the dispatch check is parameterized at
all three requested epsilons and the preflight checks explicit zero budgets for
the absent mechanisms. The focused rerun passed **4 tests, 24 deselected in
0.41s**; input-only preflight reports 18 cells / 3,600 planned trials. The RR
module and the new estimator remain byte-for-byte unchanged by this clarification.

The six-input `check` command passed without sampling; all three bundled reference
fingerprints verify. The original four-budget plan was **not run**; the clarified
three-budget plan also remains unexecuted, and the
default RR-only results directory does not exist. No fresh ESCAPE build/count,
statistical RR re-audit, full regression, baseline comparison or accuracy claim.
See [checkpoint 29](status/checkpoints/29_diamond_rr_only_integration.md).
