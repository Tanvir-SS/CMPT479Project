# Checkpoint 32 — SC-ESCAPE Stage 4 verification

2026-11-22 (America/Vancouver). **Stage 4 COMPLETE; verification PARTIAL.**
The explicit follow-up authorizes lightweight correctness, privacy-implementation
and mathematical MSE review, and supersedes the previous Stage 3 stopping point
only for that scope. **Stop before Stage 5.**

## Starting state and preservation

Starting main revision: `24239de210d69c47a1fdc945536d6095eecdb646`.
Stage 3 was still uncommitted: STATUS modified, with the SC-ESCAPE module,
Stage 3 tests, implementation document and checkpoint 31 untracked. These are
pre-existing work, not newly created by Stage 4. Checkpoint 31 was preserved.
No commit, staging or push occurred.

Before editing, eleven protected files were hashed into ignored
`build/phase32/protected_before.json`: the SC-ESCAPE and old five-stage modules,
shared RR/noise modules, Stage 3 tests/checkpoint, cached fixture truth, processed
graph manifest, reference manifest, pyproject and requirements lock. Notable hashes:

| File | SHA-256 |
|---|---|
| `src/private_graphlets/four_path_sc_escape.py` | `e587ae93c4b7f2ba585f268c483f815a69a1868c281008c658ad9d71d73741d7` |
| `src/private_graphlets/four_path.py` | `9137676c3ff45a3497a1e2f80ed66535e3cf8b03ae0e4c1306d54758c694e136` |
| `tests/test_four_path_sc_escape.py` | `8ae515addfe0d78428b60f4456041d2172325739c2010a284f9a8f58d756daed` |
| `docs/status/checkpoints/31_sc_escape_stage3_implementation.md` | `b8b7cb95aa111a4764169e7eb24cea2eac77309795a2a5f28f1d37a452565c60` |

No graph files, cached ground truths, reference sources, algorithms, existing
tests, dependency pins or previous experiment results were edited. Source hashes
and reference fingerprints were checked, without rebuilding or executing native
references. `/home/tsshergi` originals were not accessed or modified.

## Findings and classification

The report [SC_ESCAPE_VERIFICATION.md](../../SC_ESCAPE_VERIFICATION.md) contains
the source-to-equation mapping, an explicit complete-transcript privacy argument,
sensitivity calculations, unbiasedness derivation and exact ideal MSE expression.

- **Ideal accounting verified:** two degree reports cost 2ε_D, one-owner lower
  RR costs ε_R, two conditional product reports cost ε_S, and only the larger
  endpoint's conditional triangle report changes, costing at most ε_T. Both
  graphs must satisfy the same public degree bound. Fixed histories, zero scales
  and adaptive composition are covered, not just final-output postprocessing.
- **Ideal unbiasedness verified:** degrees at distinct endpoints are independently
  noised; adaptive product noise is conditionally centered; triangle centering
  assigns each triangle once. Product and triangle components use disjoint
  independent ideal randomness. Shared degrees and reused RR bits are explicitly
  accounted for in the variance calculation.
- **Uniform MSE correction:** D_max=0 still produces product noise. Replace D_max
  by max(1,D_max) only inside the adaptive product-noise bound. For one isolated
  vertex, exact ideal MSE is `2/epsilon_S^2 * (1+12/epsilon_D^2+24/epsilon_D^4)`;
  the supplied uniform expression would tend to zero as epsilon_D grows. The
  original expression is confirmed for D_max≥1.
- **Asymptotic qualification:** fixed positive budgets give the requested
  `O(n*(D_max+log(n+1))^4)` bound. `O(n^5)` follows for supplied D_max=O(n),
  including an explicitly supplied bound at most n−1. The API also permits loose
  bounds: an empty graph with supplied D_max=n³ has a triangle-noise contribution
  of order n⁷. Actual degree≤n−1 cannot silently cap the supplied noise scale.
- **Concrete numerical limitation:** accepted epsilon_R=1e-20 yields floating
  p=0.5 and positive `tanh(epsilon_R/2)`. The RR triangle signal vanishes and ideal
  unbiasedness does not carry over. The characterization test records this
  limitation as expected behavior; its passing is not a correctness endorsement.

Overall **PARTIAL** reflects these qualifications and the unresolved numerical
case, not a failed privacy-composition argument in the ideal model. No algorithm
change was made. The executable remains `experimental_unverified`. A supported
precision contract, secure randomness, failure/timing behavior and deployed
client isolation remain unresolved; no formal software certification is claimed.
Full Stage 1–2 proof documents were not supplied; this report independently derives
the statements requested in the Stage 4 attachment.

## Files created or modified in Stage 4

Created:

- `docs/SC_ESCAPE_VERIFICATION.md`: complete review and corrected bounds.
- `tests/test_sc_escape_verification.py`: 11 focused additional cases.
- `docs/status/checkpoints/32_sc_escape_stage4_verification.md`: this record.

Modified:

- `docs/SC_ESCAPE_IMPLEMENTATION.md`: link Stage 4 and state its numerical and
  theoretical qualifications, without altering historical checkpoint 31.
- `docs/status/STATUS.md`: prepend the current checklist/results; preserve history.

Ignored evidence: `build/phase32/protected_before.json`, `references.json` and
`preservation.json`. No new package module, CLI, evaluation runner or dependency.

## Commands and actual results

Existing Python 3.11 `.venv`; no setup, install or dependency update was needed.
The first targeted run was:

```bash
.venv/bin/python -m pytest -q tests/test_four_path_sc_escape.py tests/test_sc_escape_verification.py
```

**56 passed in 0.10s**, exit 0, no failures/errors/skips (46 existing + 10 new).
After adding the single tiny-RR-epsilon characterization, the same exact command
was rerun: **57 passed in 0.05s**, exit 0, no failures/errors/skips (46 + 11).
No tests were run against the historical estimator suites.

New cases exercise three fixed RR histories for one valid neighboring graph pair
and selected full-transcript likelihood ratios; a lower-wedge sensitivity case;
two degree-polynomial moments with 16 deterministic nodes each; two shared-RR
covariance examples; conditional noise variance with eight sign nodes; D=0
fourth moments with three nodes; and the numerical characterization. These are
finite analytical moment calculations, not sampled trials or a Monte Carlo study.
The existing eight cached-fixture checks were rerun as part of the Stage 3 test
file. No native ESCAPE truth was recomputed.

Reference check:

```bash
.venv/bin/python scripts/reference_fingerprints.py --verify > build/phase32/references.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path
record = json.loads(Path('build/phase32/references.json').read_text())
for name, row in record.items():
    print(name, row.get('verified'), row.get('commit'), row.get('tracked_file_count'))
assert all(row.get('verified') for row in record.values())
PY
```

Exit 0. ESCAPE `7ec2f93c524a0b47cdc8c639602e90d1c1fceff3` (82 files), k-CoreD
`b03da893ba1c38d3931708bac919562c5ab57963` (127), and notebook reference
`85eff6efa2b1d649ee238620a998ec7f1d305aac` (3) all available, clean and verified.
Actual source content was read/hashed in place, never built or modified.

Preparation read the named Stage 3 files and reusable utilities with `cat`/`sed`
and used `rg` for instruction/import discovery. The USENIX primary PDF was opened
and Algorithm 3/Theorem 5 inspected through web tools; no reference installation
or imported upstream code. One large read output was truncated; relevant files
were reread in a bounded call. No failed command or test is hidden as a skip.

Final preservation/file checks:

```bash
.venv/bin/python - <<'PY'
import hashlib, json, sys
from pathlib import Path
before = json.loads(Path('build/phase32/protected_before.json').read_text())
changed = [p for p, digest in before.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest]
result = {'protected_files': len(before), 'changed': changed, 'python': sys.version.split()[0]}
Path('build/phase32/preservation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
assert not changed
for name in ['docs/SC_ESCAPE_VERIFICATION.md', 'docs/SC_ESCAPE_IMPLEMENTATION.md', 'docs/status/STATUS.md', 'docs/status/checkpoints/32_sc_escape_stage4_verification.md', 'tests/test_sc_escape_verification.py']:
    content = Path(name).read_text()
    assert content.endswith('\n'), name
    assert all(line.rstrip() == line for line in content.splitlines()), name
print('Five Stage 4 files: newline/whitespace checks passed.')
PY
git diff --check
git status --short
git rev-parse HEAD
```

Exit 0: **11 protected files, zero changed**, Python **3.11.9**. All five Stage 4
files passed newline/whitespace checks; `git diff --check` produced no errors.
Final status contained only the five pre-existing Stage 3 paths and three new
Stage 4 paths, with changes to the two documentation files as listed above.
HEAD remained the starting revision. This final check did not execute algorithms.

## Deferred work and stopping point

No six-dataset evaluation, 200-trial experiment, budget optimization, baseline,
new mechanism, graph regeneration, ground-truth recomputation, extensive historical
regression, empirical MSE study or plot was executed. No source/privacy-scale
change or implicit cap was introduced to conceal an analytical qualification.

Stage 4 deliverables are complete with **PARTIAL** verification. Future work must
carry the numerical limitation and corrected assumptions forward; this report
does not authorize automatically changing supported epsilons or launching an
evaluation. **STOP. Stage 5 requires a separate explicit request.**
