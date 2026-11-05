"""Reference locations only; no reference code is imported into our estimators."""

import os
from pathlib import Path


REFERENCE_PATHS = {
    "escape": ("ESCAPE_ROOT", "escape"),
    "kcored": ("KCORED_ROOT", "DistributedLEDPGraphAlgos"),
    "baseline": ("BASELINE_ROOT", "Counting-Graphlets-of-Size-k-under-Local-Differential-Privacy"),
}


def project_root() -> Path:
    """Locate the source checkout, independently of the caller's cwd.

    Editable installs and source archives retain this layout. A standalone wheel
    needs absolute explicit/environment overrides for external references.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src/private_graphlets").is_dir():
            return parent
    raise ValueError("reference defaults need a project checkout; use an absolute reference path")


def reference_path(name: str, root: str | Path | None = None) -> Path:
    """CLI/API override > environment > checkout-relative third_party directory.

    Relative overrides also resolve against the project root. Invalid explicit
    choices never silently fall through to a different source checkout.
    """
    env, directory = REFERENCE_PATHS[name]
    configured = root if root is not None else os.environ.get(env)
    if configured is None:
        return project_root() / "third_party" / directory
    if not str(configured).strip():
        raise ValueError(f"empty reference path for {env}")
    path = Path(configured).expanduser()
    return (path if path.is_absolute() else project_root() / path).resolve()
