# Checkpoint 08 — Mac setup

Date: **2026-11-05 (America/Vancouver)**.
Status: **COMPLETE — setup boundary reached; no further research work started**.

## Scope and starting state

The user authorized completing the team setup on their Mac mini. Read TEAM_SETUP,
STATUS and checkpoint 07 first. Starting revision:
`5e01b4cb1804ffdf37da5e3034b6e5f312a6b131`; `git status --short` was empty.
Host: Darwin arm64; Python 3.11.9 already available from Python.framework;
Apple Clang 21.0.0 provided `/usr/bin/g++`. No `.venv`, initialized reference
submodules, Homebrew or GNU GCC installation was found in checked locations.

## Commands and observed outcomes

- `bash scripts/bootstrap_references.sh`: sandbox initially blocked `.git/config`
  writes. Authorized elevated retry succeeded and installed all three exact pins.
- `mkdir -p build/macos-setup && bash scripts/setup.sh > build/macos-setup/setup.log 2>&1`:
  created Python 3.11.9 venv, but sandbox DNS blocked dependency downloads.
- Authorized network retry:
  `bash scripts/setup.sh > build/macos-setup/setup-network.log 2>&1`.
  All locked, hash-verified dependencies and the editable package installed;
  `pip check` reported no broken requirements. Full pytest: **349 passed,
  43 errors in 19.55s**. Setup exited 1; this is not a completed setup pass.
- `cat build/escape-pytest/compile.log`: Apple libc++ rejected the pinned
  `Escape::JSIterator` (including missing subscript/operator operations).
  Integration cases errored during compilation, not count comparison.
- Downloaded the official installer with
  `curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o build/macos-setup/install-homebrew.sh`.
- Authorized attempt:
  `NONINTERACTIVE=1 /bin/bash build/macos-setup/install-homebrew.sh > build/macos-setup/homebrew.log 2>&1`.
  Exited 1: insufficient permissions to install to `/opt/homebrew`; local
  administrator authentication is required. User asked to run the downloaded
  installer in Terminal. GNU GCC is not yet installed or tested.
- `bash scripts/bootstrap_references.sh --check-only`: all three VERIFIED.
- `.venv/bin/python scripts/reference_fingerprints.py --verify > build/macos-setup/fingerprints.json`:
  exit 0, all three source fingerprints verified.
- `.venv/bin/private-graphlets info`: exit 0, package 0.1.0 on Python 3.11.9.

## Files and preservation

Added macOS guidance to `docs/TEAM_SETUP.md`, updated `docs/status/STATUS.md`,
and created this checkpoint. Local environment, downloads and logs are ignored.
Reference sources, pins, lock, algorithms, privacy accounting, experiment configs
and saved results are unchanged. No new utility experiments, commits or pushes.
Historical checkpoints and verification claims remain historical.

## Completed follow-up after administrator authentication

The user reported Homebrew installed. `/opt/homebrew/bin/brew --version` showed
7.0.12. A sandboxed `brew list --versions gcc` failed on a Homebrew cache write.
Authorized `/opt/homebrew/bin/brew install gcc` succeeded, installing GCC 16.2.0
and its seven dependencies (gmp, isl, mpfr, libmpc, lz4, xz, zstd).

Commands and actual results:

```bash
/opt/homebrew/bin/g++-16 --version
cp build/escape-pytest/compile.log build/macos-setup/apple-clang-compile.log
ln -s /opt/homebrew/bin/g++-16 .venv/bin/g++
PATH="$PWD/.venv/bin:$PATH" bash scripts/setup.sh > build/macos-setup/setup-gcc.log 2>&1
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python scripts/check_escape.py > build/macos-setup/exact-fixtures.log 2>&1
bash scripts/bootstrap_references.sh --check-only
.venv/bin/python scripts/reference_fingerprints.py --verify > build/macos-setup/fingerprints-final.json
git diff --check
```

- GNU compiler reports `g++-16 (Homebrew GCC 16.2.0) 16.2.0`.
- Setup exited 0: dependency check clean; **392 passed in 22.06s**, no skips or
  errors, including actual ESCAPE integration; package info succeeded.
- Exact-only validation exited 0: **8/8 fixtures** agree in all six non-induced
  connected pattern columns. Raw reference output and build provenance are under
  `build/reference-checks/escape/`, separately from Python counters.
- All three pinned references VERIFIED again; fingerprint verification exited 0.
- Whitespace check passed. Only team/status documentation changed in tracked source;
  the new checkpoint is untracked pending owner review. No commit or push.

Activate `.venv` before setup/tests so the project-local compiler link is on PATH.
The link is ignored and must be recreated if the venv is removed. No global shell
configuration or system compiler was changed. Source and dependency pins remain
unchanged. This validates setup, not formal privacy or accuracy proofs.

Fresh clone/ZIP portability checks and saved research-result verification were not
repeated on this Mac. No utility experiments were launched. Stop here.
