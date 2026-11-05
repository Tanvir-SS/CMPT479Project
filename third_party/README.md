# Pinned research references

Run `bash scripts/bootstrap_references.sh` from the project checkout (the script
also works by absolute path from another directory). All three sources are Git
submodules. GitHub source ZIPs omit submodule contents; the same script fetches
and verifies detached checkouts from the public HTTPS upstreams in that case.

`references.json` records the exact commits, tracked-tree digests and reviewed
file hashes. `.gitmodules` records URLs; Git index entries record the pins.
Do not use `git submodule update --remote` for reproduction. Do not edit or build
inside these sources. ESCAPE binaries belong in the main project's `build/`.

| Directory | Role | License / inclusion basis |
|---|---|---|
| `escape/` | Exact C++ reference | Upstream Apache-2.0 |
| `DistributedLEDPGraphAlgos/` | k-CoreD / EdgeOrientΔ source reference | Upstream MIT |
| `Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy/` | Authors' 4-cycle notebooks | No license found at the pin; project owner reports author permission for inclusion in this academic research repository, 2026-11-05 |

No software license is assigned to the baseline. Original files and attribution
are preserved. Permission for broader redistribution is not documented here and
must be confirmed with the project owner before such a use. No private messages
or personal details are stored. The notebooks are not an all-six-pattern package.
See [team setup](../docs/TEAM_SETUP.md) and
[source review](../docs/SOURCE_REVIEW.md#phase-07-baseline-inspection-and-portable-references).

All references are optional for our Python estimators. Our Python k-CoreD port
and independently implemented six-factor 4-clique RR baseline do not import or
execute upstream code. ESCAPE integration tests require its C++ sources and g++.
Reference source is not included in our Python wheel or source distribution;
use the repository/bootstrap workflow for references.
