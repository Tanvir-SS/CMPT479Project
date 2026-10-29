"""Reproducible NON-PRIVATE accuracy evaluation on public synthetic graphs.

This module can access exact graphs, seeds, truth and timings. None of its
records are private releases. It never changes the private estimator formula.
"""

import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

import networkx as nx
import numpy as np
import pandas as pd

from private_graphlets.escape import EscapeAdapter, parse_count_four_output, serialize_escape_graph
from private_graphlets.exact import count_three_stars, count_three_stars_bruteforce
from private_graphlets.graph import SimpleGraph, load_edge_list
from private_graphlets.noise import validate_epsilon
from private_graphlets.three_star import estimate_three_stars


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def generate_graph(spec: dict) -> SimpleGraph:
    """Deterministic graph specification; random graph seeds are mandatory."""
    family = spec["family"]
    allowed = {
        "star": {"n"}, "complete": {"n"},
        "erdos_renyi": {"n", "p", "seed"},
        "barabasi_albert": {"n", "m", "seed"},
        "stochastic_block": {"sizes", "p", "seed"},
    }
    if family not in allowed or set(spec) != allowed[family] | {"family", "id"}:
        raise ValueError(f"unknown family or incorrect graph keys: {spec}")
    if "seed" in spec:
        _integer(spec["seed"], "graph seed")
    if family == "stochastic_block":
        if not isinstance(spec["sizes"], list) or not spec["sizes"]:
            raise ValueError("SBM sizes must be a nonempty list")
        sizes = [_integer(n, "block size", 1) for n in spec["sizes"]]
        n = sum(sizes)
    else:
        n = _integer(spec["n"], "n", 1)
    if n > 1_000:
        raise ValueError("experiment graphs must have at most 1,000 vertices")
    if family in ("erdos_renyi", "stochastic_block"):
        p = np.asarray(spec["p"], dtype=float)
        if not np.all(np.isfinite(p)) or np.any((p < 0) | (p > 1)):
            raise ValueError("graph probabilities must be finite and in [0,1]")
        if family == "stochastic_block":
            if p.shape != (len(sizes), len(sizes)) or not np.array_equal(p, p.T):
                raise ValueError("SBM probability matrix must be square and symmetric")
        elif p.ndim:
            raise ValueError("ER probability must be scalar")
    if family == "star":
        graph = nx.star_graph(n - 1)
    elif family == "complete":
        graph = nx.complete_graph(n)
    elif family == "erdos_renyi":
        graph = nx.gnp_random_graph(n, float(p), seed=spec["seed"])
    elif family == "barabasi_albert":
        m = _integer(spec["m"], "BA m", 1)
        if m >= n:
            raise ValueError("BA requires m < n")
        graph = nx.barabasi_albert_graph(n, m, seed=spec["seed"])
    else:
        graph = nx.stochastic_block_model(sizes, p.tolist(), seed=spec["seed"],
                                          directed=False, selfloops=False, sparse=True)
    return SimpleGraph.from_edges(n, graph.edges())


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text())
    keys = {"schema_version", "experiment_id", "epsilons", "trials", "privacy_seed",
            "representative_graph", "graphs"}
    if not isinstance(config, dict) or set(config) != keys or config["schema_version"] != 1:
        raise ValueError("unsupported experiment configuration schema")
    _integer(config["trials"], "trials", 2)
    _integer(config["privacy_seed"], "privacy_seed")
    if not config["epsilons"] or len(set(config["epsilons"])) != len(config["epsilons"]):
        raise ValueError("epsilons must be nonempty and distinct")
    for epsilon in config["epsilons"]:
        validate_epsilon(epsilon)
    if not config["graphs"]:
        raise ValueError("at least one graph is required")
    ids = [spec["id"] for spec in config["graphs"]]
    if len(set(ids)) != len(ids) or any(re.fullmatch(r"[A-Za-z0-9_-]+", name) is None for name in ids):
        raise ValueError("graph IDs must be unique safe filenames")
    if config["representative_graph"] not in ids:
        raise ValueError("representative_graph must name a configured graph")
    for spec in config["graphs"]:
        generate_graph(spec)  # Validate every graph before writing experiment output.
    return config


def trial_rng(master_seed: int, graph_index: int, epsilon_index: int, trial: int):
    """Distinct deterministic PCG64 streams, keyed independently of graph RNGs."""
    sequence = np.random.SeedSequence(master_seed, spawn_key=(graph_index, epsilon_index, trial))
    return np.random.Generator(np.random.PCG64(sequence))


def ideal_graph_variance(graph: SimpleGraph, epsilon: float) -> float:
    """Ideal continuous-noise moment identity for review, not a DP certificate."""
    b = 2 / validate_epsilon(epsilon)
    terms = []
    for neighbors in graph.adjacency:
        t = len(neighbors) - 1
        a = (3*t*t - 1) / 6
        terms.append(2*a*a*b*b + (7*t*t - 2/3)*b**4 + 14*b**6)
    return math.fsum(terms)


def summarize(values, truth: int, runtimes, analytic_variance: float) -> dict:
    """Sample variance uses ddof=1; error moments use divisor T, not T-1."""
    values, runtimes = np.asarray(values, dtype=float), np.asarray(runtimes, dtype=float)
    if (values.ndim != 1 or values.size < 2 or runtimes.shape != values.shape
            or not np.all(np.isfinite(values)) or not np.all(np.isfinite(runtimes))
            or np.any(runtimes < 0)):
        raise ValueError("need at least two finite estimates with nonnegative finite timings")
    errors = values - truth
    mean, variance = float(values.mean()), float(values.var(ddof=1))
    bias, mae = mean - truth, float(np.abs(errors).mean())
    rmse = math.sqrt(float(np.square(errors).mean()))
    se = math.sqrt(analytic_variance / values.size)
    relative = lambda value: value / truth if truth else math.nan
    return {
        "trials": int(values.size), "mean_estimate": mean, "empirical_bias": bias,
        "sample_std": math.sqrt(variance), "sample_variance": variance,
        "mae": mae, "rmse": rmse,
        "relative_bias": relative(bias), "relative_mae": relative(mae),
        "relative_rmse": relative(rmse), "relative_error_defined": bool(truth),
        "analytic_variance": analytic_variance, "analytic_rmse": math.sqrt(analytic_variance),
        "analytic_mean_se": se, "empirical_mean_se": math.sqrt(variance / values.size),
        "bias_z": bias / se if se else math.nan,
        "variance_ratio": variance / analytic_variance if analytic_variance else math.nan,
        "negative_trials": int(np.count_nonzero(values < 0)),
        "min_estimate": float(values.min()), "max_estimate": float(values.max()),
        "mechanism_seconds_total": float(runtimes.sum()),
        "mechanism_seconds_mean": float(runtimes.mean()),
    }


def aggregate_trials(raw: pd.DataFrame, graphs: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Recalculate all metrics solely from saved trial/graph records and config."""
    rows = []
    expected_count = len(config["graphs"]) * len(config["epsilons"]) * config["trials"]
    if len(raw) != expected_count or raw.duplicated(["graph_id", "epsilon_index", "trial"]).any():
        raise ValueError("wrong trial count or duplicate trial keys")
    if list(graphs["graph_id"]) != [spec["id"] for spec in config["graphs"]]:
        raise ValueError("graph metadata/config order mismatch")
    for gi, spec in enumerate(config["graphs"]):
        metadata = graphs.iloc[gi]
        graph = generate_graph(spec)
        for ei, epsilon in enumerate(config["epsilons"]):
            group = raw[(raw.graph_id == spec["id"]) & (raw.epsilon_index == ei)].sort_values("trial")
            if (list(group.trial) != list(range(config["trials"]))
                    or not (group.epsilon == epsilon).all()
                    or not (group.graph_index == gi).all()):
                raise ValueError("missing trials or inconsistent stream coordinates")
            truth = int(metadata.exact_three_stars)
            metrics = summarize(group.estimate, truth, group.mechanism_seconds,
                                ideal_graph_variance(graph, epsilon))
            rows.append({"graph_id": spec["id"], "family": spec["family"],
                         "epsilon": epsilon, "num_vertices": int(metadata.num_vertices),
                         "num_edges": int(metadata.num_edges), "exact_three_stars": truth,
                         **metrics})
    return pd.DataFrame(rows)


def _provenance() -> dict:
    project = Path(__file__).resolve().parents[2]
    paths = [*sorted((project / "src/private_graphlets").glob("*.py")),
             project / "scripts/run_experiments.py", project / "requirements.lock",
             project / "pyproject.toml"]
    versions = {name: importlib.metadata.version(name) for name in
                ("numpy", "networkx", "pandas", "matplotlib", "pytest", "private-graphlets")}
    try:
        revision = subprocess.check_output(["git", "-C", str(project), "rev-parse", "HEAD"],
                                           stderr=subprocess.DEVNULL, text=True).strip()
        dirty = subprocess.check_output(["git", "-C", str(project), "status", "--porcelain"],
                                        stderr=subprocess.DEVNULL, text=True)
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, "Git metadata unavailable"
    return {"python": platform.python_version(), "platform": platform.platform(),
            "dependencies": versions, "git_revision": revision, "git_status": dirty,
            "source_sha256": {str(p.relative_to(project)): sha256(p) for p in paths if p.is_file()}}


def run_experiment(config_path: Path, output: Path, adapter: EscapeAdapter) -> dict:
    """Run every configured cell; preserve a failed manifest on any error.

    Refuse to overwrite any existing directory. Each timing encloses only the
    estimator API; RNG construction, graph generation, ESCAPE and I/O are excluded.
    """
    config = load_config(config_path)
    output.mkdir(parents=True, exist_ok=False)
    (output / "graphs").mkdir()
    (output / "config.json").write_bytes(config_path.read_bytes())
    manifest = {"schema_version": 1, "result_type": "nonprivate_synthetic_evaluation",
                "simulation_only": True, "status": "running", "provenance": _provenance(),
                "randomness": {"bit_generator": "PCG64", "privacy_seed": config["privacy_seed"],
                               "spawn_key": "(graph_index, epsilon_index, trial), zero-based"},
                "escape_executable_sha256": sha256(adapter.executable),
                "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    manifest["command"] = [sys.executable, *sys.argv]
    build_manifest = adapter.executable.parent / "build.json"
    if build_manifest.is_file():
        manifest["escape_build"] = json.loads(build_manifest.read_text())
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    started = time.perf_counter()
    try:
        graph_rows, trial_rows, reference_rows = [], [], []
        for gi, spec in enumerate(config["graphs"]):
            graph = generate_graph(spec)
            graph_path = output / "graphs" / f"{spec['id']}.edges"
            lines = [f"{graph.num_vertices} {graph.num_edges}"]
            lines.extend(f"{u} {v}" for u, row in enumerate(graph.adjacency)
                         for v in sorted(row) if u < v)
            graph_path.write_text("\n".join(lines) + "\n")
            truth = count_three_stars(graph)
            reference = adapter.run(graph)
            brute = count_three_stars_bruteforce(graph) if graph.num_vertices <= 12 else None
            if truth != reference.counts.three_stars or (brute is not None and brute != truth):
                raise ValueError(f"exact reference disagreement for {spec['id']}")
            reference_rows.append({"graph_id": spec["id"], "formula_count": truth,
                                   "escape_count": reference.counts.three_stars,
                                   "bruteforce_count": brute,
                                   "escape_input_text": reference.input_text,
                                   "escape_output_text": reference.output_text,
                                   "stdout": reference.stdout, "stderr": reference.stderr})
            degrees = np.array([len(row) for row in graph.adjacency])
            graph_rows.append({"graph_id": spec["id"], "family": spec["family"],
                               "num_vertices": graph.num_vertices, "num_edges": graph.num_edges,
                               "exact_three_stars": truth, "escape_three_stars": reference.counts.three_stars,
                               "graph_seed": spec.get("seed"), "graph_sha256": sha256(graph_path),
                               "degree_mean": float(degrees.mean()), "degree_max": int(degrees.max()),
                               "degree_variance": float(degrees.var()),
                               "isolates": int(np.count_nonzero(degrees == 0))})
            for ei, epsilon in enumerate(config["epsilons"]):
                for trial in range(config["trials"]):
                    rng = trial_rng(config["privacy_seed"], gi, ei, trial)
                    begin = time.perf_counter()
                    estimate = estimate_three_stars(graph, epsilon, rng=rng).estimate
                    elapsed = time.perf_counter() - begin
                    trial_rows.append({"graph_id": spec["id"], "graph_index": gi,
                                       "epsilon": epsilon, "epsilon_index": ei, "trial": trial,
                                       "estimate": estimate, "mechanism_seconds": elapsed})
            print(f"Completed {spec['id']}: n={graph.num_vertices}, m={graph.num_edges}, S3={truth}")
        pd.DataFrame(graph_rows).to_csv(output / "graphs.csv", index=False)
        pd.DataFrame(trial_rows).to_csv(output / "trials.csv", index=False)
        (output / "escape_reference.json").write_text(json.dumps(reference_rows, indent=2) + "\n")
        # Aggregate from the serialized records, ensuring plots and metrics share data.
        raw = pd.read_csv(output / "trials.csv", float_precision="round_trip")
        graphs = pd.read_csv(output / "graphs.csv", float_precision="round_trip")
        aggregate_trials(raw, graphs, config).to_csv(output / "summary.csv", index=False)
        manifest.update(status="complete", pipeline_seconds=time.perf_counter() - started,
                        graphs=len(graph_rows), cells=len(config["graphs"])*len(config["epsilons"]),
                        trials=len(trial_rows))
        manifest["files_sha256"] = {str(p.relative_to(output)): sha256(p)
                                     for p in sorted(output.rglob("*")) if p.is_file() and p != manifest_path}
    except Exception as exc:
        manifest.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    return manifest


def verify_results(output: Path, *, replay: bool = False) -> dict:
    """Check hashes, graphs, every aggregate, and optionally replay every estimate."""
    manifest = json.loads((output / "manifest.json").read_text())
    if manifest["status"] != "complete":
        raise ValueError("experiment did not complete")
    for name, digest in manifest["files_sha256"].items():
        if sha256(output / name) != digest:
            raise ValueError(f"artifact hash mismatch: {name}")
    config = load_config(output / "config.json")
    graphs = pd.read_csv(output / "graphs.csv", float_precision="round_trip")
    raw = pd.read_csv(output / "trials.csv", float_precision="round_trip")
    summary = pd.read_csv(output / "summary.csv", float_precision="round_trip")
    expected = aggregate_trials(raw, graphs, config)
    pd.testing.assert_frame_equal(summary, expected, check_exact=False, rtol=2e-13, atol=1e-12)
    references = json.loads((output / "escape_reference.json").read_text())
    for gi, spec in enumerate(config["graphs"]):
        graph = load_edge_list(output / "graphs" / f"{spec['id']}.edges")
        if graph != generate_graph(spec):
            raise ValueError("saved graph differs from configured generator")
        truth = count_three_stars(graph)
        row, reference = graphs.iloc[gi], references[gi]
        parsed = parse_count_four_output(reference["escape_output_text"],
                                         num_vertices=max(4, graph.num_vertices),
                                         num_edges=graph.num_edges)
        if (row.num_vertices != graph.num_vertices or row.num_edges != graph.num_edges
                or row.exact_three_stars != truth or row.escape_three_stars != truth
                or reference["graph_id"] != spec["id"] or reference["escape_count"] != truth
                or parsed.three_stars != truth
                or reference["escape_input_text"] != serialize_escape_graph(graph)):
            raise ValueError("saved graph/reference metadata mismatch")
        if replay:
            for trial in raw[raw.graph_id == spec["id"]].itertuples():
                rng = trial_rng(config["privacy_seed"], gi, trial.epsilon_index, trial.trial)
                actual = estimate_three_stars(graph, trial.epsilon, rng=rng).estimate
                if actual != trial.estimate:
                    raise ValueError(f"replay mismatch: {spec['id']}, epsilon={trial.epsilon}, trial={trial.trial}")
    return {"status": "verified", "graphs": len(graphs), "cells": len(summary),
            "trials": len(raw), "exact_seed_replay": replay,
            "runtime_replayed": False}
