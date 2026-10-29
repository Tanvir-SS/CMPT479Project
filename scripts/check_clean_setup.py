"""Verify setup in a fresh temporary project copy using a predownloaded wheelhouse."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    wheelhouse = project / "build/wheelhouse"
    if not wheelhouse.is_dir():
        raise SystemExit("First download requirements.lock wheels into build/wheelhouse (see README).")
    # Includes new project files before the first commit, excludes ignored artifacts.
    files = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=project,
    ).decode().split("\0")[:-1]
    log_path = project / "build/reproduction-check.log"
    with tempfile.TemporaryDirectory(prefix="cmpt479-reproduction-") as temporary:
        checkout = Path(temporary) / "project"
        for name in files:
            target = checkout / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project / name, target)
        env = os.environ.copy()
        for key in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME"):
            env.pop(key, None)
        env.update(PIP_NO_INDEX="1", PIP_FIND_LINKS=str(wheelhouse))
        with log_path.open("w") as log:
            # Deliberately launch from outside the copied project.
            subprocess.run(["bash", str(checkout / "scripts/setup.sh")],
                           cwd=temporary, env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
    print(f"Fresh offline setup, dependency check and smoke tests passed. Log: {log_path}")


if __name__ == "__main__":
    main()
