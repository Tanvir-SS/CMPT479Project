"""NON-PRIVATE adapter for the reviewed ESCAPE count_four executable.

Never calls a Python exact counter as a substitute for an ESCAPE result.
The supported domain is simple graphs with at most 1,000 vertices. This
conservative bound keeps the reviewed int64/double counting arithmetic small;
this adapter is not a large-graph precision certification.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from private_graphlets.graph import SimpleGraph


MAX_VERTICES = 1_000
CONNECTED_PATTERNS = ("3-star", "3-path", "tailed triangle", "4-cycle", "diamond", "4-clique")
TRANSLATION_UNITS = ("exe/count_four.cpp", "Graph.cpp", "GraphIO.cpp", "TriangleProgram.cpp")


class EscapeError(RuntimeError):
    """An ESCAPE reference check could not produce a trustworthy result."""


class EscapeConfigurationError(EscapeError):
    pass


class EscapeBuildError(EscapeError):
    pass


class EscapeExecutionError(EscapeError):
    pass


class EscapeOutputError(EscapeError):
    pass


def resolve_escape_root(root: str | Path | None = None) -> Path:
    """Explicit root takes precedence over ESCAPE_ROOT; no machine-specific default."""
    configured = root if root is not None else os.environ.get("ESCAPE_ROOT")
    if not configured:
        raise EscapeConfigurationError("provide --escape-root or set ESCAPE_ROOT")
    source = Path(configured).expanduser().resolve()
    for name in (*TRANSLATION_UNITS, "Escape/GetAllCounts.h"):
        if not (source / name).is_file():
            raise EscapeConfigurationError(f"missing ESCAPE source: {source / name}")
    return source


def _timeout(seconds: float) -> None:
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("timeout must be finite and positive")


def build_count_four(
    escape_root: str | Path | None = None,
    *,
    build_dir: str | Path = "build/escape",
    compiler: str = "g++",
    timeout: float = 120,
) -> Path:
    """Compile original translation units outside the source tree; save provenance.

    Builds once per call, without executing upstream setup/make/wrapper scripts.
    Callers can reuse the returned executable for many graphs. A failed build
    raises even if an older executable exists.
    """
    _timeout(timeout)
    source = resolve_escape_root(escape_root)
    destination = Path(build_dir).resolve()
    if destination.is_relative_to(source):
        raise EscapeConfigurationError("build directory must be outside the ESCAPE source tree")
    destination.mkdir(parents=True, exist_ok=True)
    executable = destination / "count_four"
    # Hash original headers and translation units, without copying or changing them.
    files = sorted(set(source.glob("Escape/*.h")) | {source / p for p in TRANSLATION_UNITS})
    hashes = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with tempfile.TemporaryDirectory(prefix="compile-", dir=destination) as temporary:
        target = Path(temporary) / "count_four"
        command = [compiler, "-std=c++11", "-O2", "-Wall", "-I", str(source),
                   *(str(source / p) for p in TRANSLATION_UNITS), "-o", str(target)]
        (destination / "compile-command.json").write_text(json.dumps(command, indent=2) + "\n")
        try:
            with (destination / "compile.log").open("w") as log:
                completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                           timeout=timeout, check=False)
            if completed.returncode != 0 or not target.is_file():
                raise EscapeBuildError(
                    f"ESCAPE compilation failed (exit {completed.returncode}); "
                    f"see {destination / 'compile.log'}"
                )
            target.replace(executable)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise EscapeBuildError(f"ESCAPE compilation failed: {exc}") from exc
    try:
        version = subprocess.run([compiler, "--version"], capture_output=True, text=True,
                                 timeout=10, check=True).stdout.splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError) as exc:
        raise EscapeBuildError(f"cannot record compiler version: {exc}") from exc
    manifest = {
        "source_root": str(source), "source_sha256": hashes,
        "compiler": version, "command": command, "returncode": completed.returncode,
        "executable": str(executable),
        "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "warning_count": (destination / "compile.log").read_text().count("warning:"),
    }
    (destination / "build.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return executable


def serialize_escape_graph(graph: SimpleGraph) -> str:
    """Canonical unique u<v edge list, padding to four vertices with isolates.

    Extra isolates leave all connected four-vertex counts unchanged. Other
    output columns describe the padded graph, not necessarily the original.
    """
    if graph.num_vertices > MAX_VERTICES:
        raise ValueError(f"ESCAPE adapter supports at most {MAX_VERTICES} vertices")
    rows = [f"{max(4, graph.num_vertices)} {graph.num_edges}"]
    rows.extend(f"{u} {v}" for u, neighbors in enumerate(graph.adjacency)
                for v in sorted(neighbors) if u < v)
    return "\n".join(rows) + "\n"


@dataclass(frozen=True, slots=True)
class EscapeCounts:
    """Parsed NON-INDUCED counts of the normalized graph, directly from ESCAPE."""

    num_vertices: int
    adjacency_entries: int
    three_vertex: tuple[int, ...]
    four_vertex: tuple[int, ...]

    @property
    def connected_four(self) -> dict[str, int]:
        return dict(zip(CONNECTED_PATTERNS, self.four_vertex[5:], strict=True))

    @property
    def three_stars(self) -> int:
        return self.four_vertex[5]


def parse_count_four_output(text: str, *, num_vertices: int, num_edges: int) -> EscapeCounts:
    """Parse all 17 lines, checking headers and integral, finite count values."""
    lines = text.splitlines()
    if len(lines) != 17:
        raise EscapeOutputError(f"expected 17 ESCAPE output lines, got {len(lines)}")
    try:
        if any(re.fullmatch(r"[0-9]+", line.strip()) is None for line in lines[:2]):
            raise ValueError("header must contain unsigned decimal integers")
        headers = tuple(int(line) for line in lines[:2])
    except ValueError as exc:
        raise EscapeOutputError("invalid ESCAPE n,2m header") from exc
    if headers != (num_vertices, 2 * num_edges):
        raise EscapeOutputError(f"unexpected ESCAPE n,2m header: {headers}")
    counts = []
    for index, line in enumerate(lines[2:], start=3):
        try:
            # printf emits -0.000000 for some zero disconnected counts. Decimal
            # treats signed zero as zero; the numeric check still rejects <0.
            if re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", line.strip()) is None:
                raise EscapeOutputError(f"malformed count on ESCAPE line {index}: {line!r}")
            value = Decimal(line.strip())
            if (not value.is_finite() or value < 0 or value >= 2**53
                    or value != value.to_integral_value()):
                raise EscapeOutputError(f"invalid or inexact count on ESCAPE line {index}: {line!r}")
            counts.append(int(value))
        except InvalidOperation as exc:
            raise EscapeOutputError(f"malformed count on ESCAPE line {index}: {line!r}") from exc
    return EscapeCounts(*headers, tuple(counts[:4]), tuple(counts[4:]))


@dataclass(frozen=True, slots=True)
class EscapeRun:
    """Non-private reference evidence; never include in a private release record."""

    counts: EscapeCounts
    original_num_vertices: int
    input_text: str
    output_text: str
    stdout: str
    stderr: str


class EscapeAdapter:
    """Run a supplied count_four binary with isolated, temporary per-call output."""

    def __init__(self, executable: str | Path, *, timeout: float = 30):
        _timeout(timeout)
        self.executable = Path(executable).resolve()
        if not self.executable.is_file() or not os.access(self.executable, os.X_OK):
            raise EscapeConfigurationError(f"not an executable: {self.executable}")
        self.timeout = timeout

    def run(self, graph: SimpleGraph) -> EscapeRun:
        serialized = serialize_escape_graph(graph)
        # ESCAPE hardcodes out.txt in cwd. Fresh temporary directories prevent
        # stale output, collisions between concurrent calls, and reference writes.
        with tempfile.TemporaryDirectory(prefix="private-graphlets-escape-") as temporary:
            directory = Path(temporary)
            graph_path = directory / "graph.edges"
            graph_path.write_text(serialized, encoding="ascii")
            try:
                completed = subprocess.run(
                    [str(self.executable), str(graph_path)], cwd=directory,
                    capture_output=True, text=True, timeout=self.timeout, check=False,
                )
            except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
                raise EscapeExecutionError(f"ESCAPE execution failed: {exc}") from exc
            if completed.returncode:
                raise EscapeExecutionError(
                    f"ESCAPE exited {completed.returncode}; "
                    f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
                )
            try:
                output = (directory / "out.txt").read_text(encoding="ascii")
            except (OSError, UnicodeError) as exc:
                raise EscapeOutputError(f"ESCAPE did not write readable out.txt: {exc}") from exc
            counts = parse_count_four_output(
                output, num_vertices=max(4, graph.num_vertices), num_edges=graph.num_edges,
            )
        return EscapeRun(counts, graph.num_vertices, serialized, output,
                         completed.stdout, completed.stderr)

    def count_three_stars(self, graph: SimpleGraph) -> int:
        return self.run(graph).counts.three_stars
