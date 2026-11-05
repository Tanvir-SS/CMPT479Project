"""Standard-library helpers usable before the Python environment is installed."""

import hashlib
import json
from pathlib import Path
import re
import subprocess


def git(path: Path, *args: str, timeout: float = 120) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                            text=True, timeout=timeout, check=True)
    return result.stdout.strip()


def load_manifest(project: Path) -> dict:
    data = json.loads((project / "third_party/references.json").read_text())
    if data["schema_version"] != 1:
        raise ValueError("unsupported reference manifest version")
    for name, row in data["references"].items():
        path = Path(row["path"])
        if (not re.fullmatch(r"[a-z]+", name) or len(path.parts) != 2
                or path.parts[0] != "third_party" or path.parts[1] in (".", "..")
                or not re.fullmatch(r"[0-9a-f]{40}", row["commit"])
                or not row["url"].startswith("https://")
                or row["integration"] not in ("submodule", "manual")):
            raise ValueError(f"unsafe or invalid reference manifest entry: {name}")
    return data["references"]


def fingerprint(path: Path, reviewed: list[str]) -> dict:
    path = path.resolve()
    if Path(git(path, "rev-parse", "--show-toplevel")).resolve() != path:
        raise ValueError(f"not a standalone reference Git tree: {path}")
    names = sorted(git(path, "ls-files", "-z").split("\0"))
    names = [name for name in names if name]
    tree = hashlib.sha256()
    for name in names:
        digest = hashlib.sha256((path / name).read_bytes()).hexdigest()
        tree.update(f"{name}\0{digest}\n".encode())
    status = git(path, "status", "--porcelain", "--untracked-files=all")
    return {
        "path_at_review": str(path),
        "commit": git(path, "rev-parse", "HEAD"),
        "origin": git(path, "remote", "get-url", "origin"),
        "status_porcelain": status + "\n" if status else "",
        "tracked_file_count": len(names),
        "tracked_tree_sha256": tree.hexdigest(),
        "reviewed_file_sha256": {
            name: hashlib.sha256((path / name).read_bytes()).hexdigest() for name in reviewed
        },
    }


def verify_tree(path: Path, row: dict) -> dict:
    result = fingerprint(path, list(row["reviewed_file_sha256"]))
    if git(path, "status", "--porcelain", "--untracked-files=all", "--ignored"):
        raise ValueError(f"modified/untracked/ignored files in {path}; leave it unchanged and review manually")
    for field in ("commit", "tracked_tree_sha256", "reviewed_file_sha256"):
        if result[field] != row[field]:
            raise ValueError(f"{path}: {field} differs from the reviewed pin; refusing to overwrite")
    return result
