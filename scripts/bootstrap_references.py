"""Install pinned authorized references in this checkout, for Git clones or ZIPs."""

import argparse
import os
from pathlib import Path
import subprocess
import tempfile

from _reference_tools import git, load_manifest, verify_tree


PROJECT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, timeout: float) -> None:
    subprocess.run(command, check=True, timeout=timeout,
                   env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})


def is_project_git(project: Path) -> bool:
    try:
        return Path(git(project, "rev-parse", "--show-toplevel")).resolve() == project.resolve()
    except subprocess.CalledProcessError:
        return False


def check_submodule_pin(project: Path, name: str, row: dict) -> None:
    entry = git(project, "ls-files", "--stage", "--", row["path"])
    expected = f"160000 {row['commit']} 0\t{row['path']}"
    if entry != expected:
        raise ValueError(f"{name}: Git index must contain the pinned submodule {row['commit']}; "
                         "do not substitute a branch tip")
    for key, expected_value in (("path", row["path"]), ("url", row["url"])):
        actual = git(project, "config", "-f", ".gitmodules", "--get", f"submodule.{name}.{key}")
        if actual != expected_value:
            raise ValueError(f"{name}: .gitmodules {key} differs from reference manifest")
    # A local URL override must not silently fetch a different upstream.
    result = subprocess.run(["git", "-C", str(project), "config", "--get",
                             f"submodule.{name}.url"], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip() != row["url"]:
        raise ValueError(f"{name}: local submodule URL differs; review .git/config manually")


def install_reference(project: Path, name: str, row: dict, *, check_only: bool, timeout: float) -> str:
    target = project / row["path"]
    if target.parent.is_symlink() or target.is_symlink():
        raise ValueError(f"refusing symlink reference location: {target}")
    if row["integration"] == "manual":
        if not target.exists() or (target.is_dir() and not any(target.iterdir())):
            return "MANUAL (optional, no license grant found; see docs/TEAM_SETUP.md)"
        verify_tree(target, row)
        return f"VERIFIED manual checkout {row['commit']} (not bundled or downloaded)"
    project_git = is_project_git(project)
    if project_git:
        check_submodule_pin(project, name, row)
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        verify_tree(target, row)  # Fail before any write to an existing tree.
        return f"VERIFIED {row['commit']}"
    if check_only:
        raise ValueError(f"missing {name}: run bash scripts/bootstrap_references.sh")
    target.parent.mkdir(parents=True, exist_ok=True)
    if project_git:
        run(["git", "-C", str(project), "-c", "credential.helper=", "submodule", "update",
             "--init", "--checkout", "--", row["path"]], timeout=timeout)
    else:
        # ZIP: clone into a disposable directory, verify before atomic promotion.
        # A failed network request never leaves a half-populated source tree.
        with tempfile.TemporaryDirectory(prefix=".bootstrap-", dir=target.parent) as temporary:
            source = Path(temporary) / "source"
            run(["git", "-c", "credential.helper=", "clone", "--no-checkout", "--",
                 row["url"], str(source)], timeout=timeout)
            git(source, "checkout", "--detach", row["commit"], timeout=timeout)
            verify_tree(source, row)
            if target.exists():
                target.rmdir()  # Only an empty directory can be replaced.
            source.rename(target)
    verify_tree(target, row)
    return f"INSTALLED {row['commit']} ({'submodule' if project_git else 'ZIP checkout'})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", action="append", choices=("escape", "kcored", "baseline"))
    parser.add_argument("--check-only", action="store_true", help="Verify without fetching or writing.")
    parser.add_argument("--timeout", type=int, default=180, help="Per Git command seconds (default 180).")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    failed = False
    for name, row in load_manifest(PROJECT).items():
        if args.only and name not in args.only:
            continue
        try:
            message = install_reference(PROJECT, name, row, check_only=args.check_only, timeout=args.timeout)
            print(f"{name}: {message}", flush=True)
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            print(f"{name}: FAILED: {exc}", flush=True)
            if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
                print(exc.stderr.strip(), flush=True)
            print("Check network/DNS and public upstream access; preserve existing files. "
                  "Python estimators remain usable without references.", flush=True)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
