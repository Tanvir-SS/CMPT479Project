"""Independent NON-PRIVATE diamond evaluation: exactly six graphs, 4x200 trials.

Calls the unchanged estimate_diamonds API. SQLite commits each observation;
trials.csv is flushed per observation and rebuilt from SQLite on resume.
No smoke mode, baseline, exact recount, cap selection or parameter optimization.
"""

import argparse
import csv
from datetime import datetime, timezone
import fcntl
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from private_graphlets.diamond import DiamondBudget, estimate_diamonds
from private_graphlets.escape import parse_count_four_output
from private_graphlets.graph_datasets import PROJECT, digest, json_bytes, load_prepared_graph
from private_graphlets.kcore import KCoreConfig

GRAPH_IDS = ["karate", "dolphins", "les_miserables", "brightkite_50", "ba_n100", "sbm_n100"]
EXPECTED = [151, 300, 4544, 245, 217982, 3093]
EPSILONS = [.5, 1., 2., 4.]
DEFAULT_CONFIG = PROJECT / "experiments/configs/diamond_six_datasets.json"
DEFAULT_OUTPUT = PROJECT / "experiments/results/diamond_six_datasets"
DEFAULT_PLOTS = PROJECT / "plots/diamond_six_datasets"
METHOD = "kcore_rr_full_wedge_hybrid_diamond"
SOURCE_FILES = ["diamond.py", "graph.py", "kcore.py", "noise.py", "randomized_response.py",
                "four_clique_exact.py", "escape.py", "graph_datasets.py"]
PROVENANCE_KEYS = ["runner_sha256", "source_sha256", "dataset_manifest_sha256", "dependencies",
                   "reference_manifest_sha256", "submodules", "python"]


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)


def seed_for(master, gi, ei, trial):
    return (master << 64) | (gi << 48) | (ei << 32) | trial


def load_inputs(config_path):
    c = json.loads(config_path.read_text())
    budgets = [dict(total=e, ordering=e/4, rr=3*e/8, wedge=3*e/8) for e in EPSILONS]
    if (c["trials"] != 200 or c["graph_ids"] != GRAPH_IDS or c["budgets"] != budgets
            or c["cap_rule"] != "public_n_minus_1" or c["variance_ddof"] != 0
            or c["method"] != METHOD or c["dataset_manifest"] != "data/processed/graph_manifest.json"
            or c["wedge_scale_rule"] != "2*(B-1)/epsilon_wedge"
            or c["kcore_config"] != dict(psi=.5, threshold_fraction=.5, bias_factor=1)):
        raise ValueError("preserve the authorized fixed six-dataset configuration")
    if type(c["master_seed"]) is not int or c["master_seed"] < 0:
        raise ValueError("invalid master seed")
    for budget in budgets:
        DiamondBudget(**budget)
    manifest = json.loads((PROJECT / c["dataset_manifest"]).read_text())
    lookup = {row["id"]: row for row in manifest["graphs"]}
    if len(manifest["graphs"]) != 6 or set(lookup) != set(GRAPH_IDS):
        raise ValueError("the pinned manifest must contain exactly six graphs")
    graphs, truth = [], []
    for name, expected in zip(GRAPH_IDS, EXPECTED, strict=True):
        record = lookup[name]
        spec = dict(path="data/processed/" + record["path"], sha256=record["sha256"],
                    n=record["processed_vertices"], m=record["processed_edges"])
        graph = load_prepared_graph(spec)
        if (graph.num_vertices < 3 or digest(PROJECT / "data/processed" / record["mapping_path"])
                != record["mapping_sha256"]):
            raise ValueError("invalid graph scope or mapping hash")
        native = parse_count_four_output(record["validation"]["escape_output"],
                    num_vertices=graph.num_vertices, num_edges=graph.num_edges).connected_four["diamond"]
        if native != expected:
            raise ValueError("saved native diamond truth differs from the inspected manifest")
        graphs.append(graph)
        truth.append(dict(graph=name, **spec, exact_count=native,
                          mapping_path=record["mapping_path"], mapping_sha256=record["mapping_sha256"],
                          escape_output=record["validation"]["escape_output"],
                          reference=manifest["escape_reference"]))
    return c, graphs, truth


def provenance():
    return dict(git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT, text=True).strip(),
                python=sys.version, platform=platform.platform(), hardware=platform.machine(),
                processor=platform.processor(), logical_cpu_count=os.cpu_count(),
                dependencies={k: importlib.metadata.version(k) for k in ("numpy", "pandas", "networkx", "matplotlib")},
                runner_sha256=digest(Path(__file__)),
                source_sha256={name: digest(PROJECT / "src/private_graphlets" / name) for name in SOURCE_FILES},
                dataset_manifest_sha256=digest(PROJECT / "data/processed/graph_manifest.json"),
                reference_manifest_sha256=digest(PROJECT / "third_party/references.json"),
                submodules=subprocess.check_output(["git", "submodule", "status"], cwd=PROJECT, text=True).strip())


def coordinates(c):
    return [(gi, ei, t) for gi in range(6) for ei in range(4) for t in range(c["trials"])]


def read_rows(db, c, truth):
    stored = db.execute("SELECT ordinal,payload FROM trials ORDER BY ordinal").fetchall()
    expected = coordinates(c)
    if len(stored) > len(expected):
        raise ValueError("too many saved trials")
    rows = []
    for i, (ordinal, payload) in enumerate(stored):
        row = json.loads(payload)
        gi, ei, t = expected[i]
        b, g = c["budgets"][ei], truth[gi]
        if ordinal != i or (row["graph_index"], row["epsilon_index"], row["trial"]) != (gi, ei, t):
            raise ValueError("saved trials are not a unique contiguous coordinate prefix")
        fixed = dict(graph=g["graph"], n=g["n"], m=g["m"], method=METHOD, epsilon=b["total"],
                     epsilon_ordering=b["ordering"], epsilon_rr=b["rr"], epsilon_wedge=b["wedge"],
                     cap=g["n"]-1, wedge_noise_scale=2*(g["n"]-2)/b["wedge"],
                     seed=str(seed_for(c["master_seed"], gi, ei, t)), exact_count=g["exact_count"],
                     privacy_status="experimental_unverified")
        if any(row[k] != value for k, value in fixed.items()):
            raise ValueError("saved graph, budget, cap, scale, truth or seed mismatch")
        if not all(math.isfinite(row[k]) for k in ("estimate", "runtime_seconds", "rr_weight")) or row["runtime_seconds"] < 0:
            raise ValueError("invalid estimate or runtime")
        rows.append(row)
    return rows


def summarize(rows):
    records = []
    if not rows:
        return pd.DataFrame()
    for _, cell in pd.DataFrame(rows).groupby(["graph_index", "epsilon_index"], sort=True):
        first = cell.iloc[0]
        x = cell.estimate.to_numpy(dtype=float)
        mean = float(np.mean(x))
        error = x - first.exact_count
        mse, mae = float(np.mean(error**2)), float(np.mean(abs(error)))
        bias, variance = mean - first.exact_count, float(np.var(x, ddof=0))
        if not math.isclose(mse, variance+bias*bias, rel_tol=1e-12, abs_tol=1e-12):
            raise AssertionError("population MSE identity failed")
        record = {key: first[key] for key in ("graph", "n", "m", "method", "epsilon", "epsilon_ordering",
                   "epsilon_rr", "epsilon_wedge", "cap", "wedge_noise_scale", "rr_weight", "exact_count")}
        record.update(trials=len(cell), mean_estimate=mean, bias=bias, variance=variance, variance_ddof=0,
                      mse=mse, rmse=math.sqrt(mse), mae=mae,
                      mean_relative_error=mae/first.exact_count if first.exact_count else math.nan,
                      relative_rmse=math.sqrt(mse)/first.exact_count if first.exact_count else math.nan,
                      mean_runtime_seconds=float(cell.runtime_seconds.mean()),
                      runtime_total_seconds=float(cell.runtime_seconds.sum()),
                      negative_estimates=int((x < 0).sum()), noninteger_estimates=int((x != np.rint(x)).sum()))
        records.append(record)
    return pd.DataFrame(records)


def export(db, c, truth, output):
    rows = read_rows(db, c, truth)
    for name, frame in (("trials.csv", pd.DataFrame(rows)), ("summary.csv", summarize(rows))):
        temporary = output / (name + ".tmp")
        frame.to_csv(temporary, index=False, float_format="%.17g")
        temporary.replace(output / name)
    state = dict(status="complete" if len(rows) == 4800 else "partial", completed_trials=len(rows),
                 target_trials=4800, remaining_trials=4800-len(rows),
                 updated_utc=datetime.now(timezone.utc).isoformat(),
                 result_type="nonprivate_public_graph_evaluation",
                 files_sha256={name: digest(output / name) for name in
                               ("config.json", "provenance.json", "escape_ground_truth.json", "trials.csv", "summary.csv")})
    atomic_json(output / "manifest.json", state)
    return state


def run(config_path, output, *, resume=False, max_new_trials=None):
    if max_new_trials is not None and max_new_trials < 1:
        raise ValueError("max-new-trials must be positive")
    c, graphs, truth = load_inputs(config_path)
    current = provenance()
    if output.exists() and not resume:
        raise FileExistsError("output exists; use --resume to continue without duplicate trials")
    existing = output.exists()
    output.mkdir(parents=True, exist_ok=resume)
    with (output / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if existing:
            if json.loads((output / "config.json").read_text()) != c or json.loads((output / "escape_ground_truth.json").read_text()) != truth:
                raise ValueError("resume configuration/truth differs")
            old = json.loads((output / "provenance.json").read_text())
            if any(current[k] != old[k] for k in PROVENANCE_KEYS):
                raise ValueError("resume source/environment provenance differs")
        else:
            for name, value in (("config", c), ("provenance", current), ("escape_ground_truth", truth)):
                atomic_json(output / f"{name}.json", value)
        with sqlite3.connect(output / "trials.sqlite3", timeout=0) as db:
            db.execute("CREATE TABLE IF NOT EXISTS trials (ordinal INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
            db.commit()
            saved = read_rows(db, c, truth)
            # Repair any interrupted CSV append from the durable source of truth.
            if saved:
                export(db, c, truth, output)
            jobs, start = coordinates(c), len(saved)
            stop = len(jobs) if max_new_trials is None else min(len(jobs), start+max_new_trials)
            kcore_config = KCoreConfig(**c["kcore_config"])
            try:
                with (output / "trials.csv").open("a", newline="") as stream:
                    writer = None
                    for i in range(start, stop):
                        gi, ei, t = jobs[i]
                        graph = graphs[gi]
                        budget = DiamondBudget(**c["budgets"][ei])
                        cap = graph.num_vertices - 1
                        seed = seed_for(c["master_seed"], gi, ei, t)
                        begin = time.perf_counter()
                        result = estimate_diamonds(graph, budget.total, cap=cap, budget=budget,
                                                   seed=seed, kcore_config=kcore_config)
                        seconds = time.perf_counter() - begin
                        if result.budget != budget or result.cap != cap or result.wedge_noise_scale != 2*(cap-1)/budget.wedge:
                            raise AssertionError("estimator returned different public parameters")
                        row = dict(graph=GRAPH_IDS[gi], n=graph.num_vertices, m=graph.num_edges,
                                   graph_index=gi, epsilon_index=ei, trial=t, method=METHOD,
                                   epsilon=budget.total, epsilon_ordering=budget.ordering,
                                   epsilon_rr=budget.rr, epsilon_wedge=budget.wedge, cap=cap,
                                   wedge_noise_scale=result.wedge_noise_scale, rr_weight=result.rr_weight,
                                   seed=str(seed), estimate=result.estimate, exact_count=truth[gi]["exact_count"],
                                   runtime_seconds=seconds, privacy_status=result.privacy_status)
                        db.execute("INSERT INTO trials VALUES (?,?)", (i, json.dumps(row, allow_nan=False)))
                        db.commit()
                        if writer is None:
                            writer = csv.DictWriter(stream, fieldnames=list(row))
                            if start == 0:
                                writer.writeheader()
                        writer.writerow(row)
                        stream.flush()
                        if (i+1) % 25 == 0 or i+1 == stop:
                            print(json.dumps(dict(completed_trials=i+1, graph=GRAPH_IDS[gi],
                                                  epsilon=budget.total, cell_trials=t+1)), flush=True)
                        if t == c["trials"]-1:
                            # Only summaries/manifest here: avoid replacing an open append file.
                            rows = read_rows(db, c, truth)
                            summarize(rows).to_csv(output / "summary.csv", index=False, float_format="%.17g")
                            atomic_json(output / "progress.json", dict(completed_trials=i+1, target_trials=4800))
            finally:
                state = export(db, c, truth, output)
            state["new_trials_this_invocation"] = stop-start
            return state


def verify(output):
    c, _, truth = load_inputs(output / "config.json")
    state = json.loads((output / "manifest.json").read_text())
    for name, value in state["files_sha256"].items():
        if digest(output / name) != value:
            raise ValueError("saved artifact hash mismatch")
    current, old = provenance(), json.loads((output / "provenance.json").read_text())
    if any(current[k] != old[k] for k in PROVENANCE_KEYS):
        raise ValueError("source/environment provenance changed")
    if json.loads((output / "escape_ground_truth.json").read_text()) != truth:
        raise ValueError("ground truth cache changed")
    with sqlite3.connect(f"file:{output}/trials.sqlite3?mode=ro", uri=True) as db:
        rows = read_rows(db, c, truth)
    raw = pd.read_csv(output / "trials.csv", dtype={"seed": str}, float_precision="round_trip")
    pd.testing.assert_frame_equal(raw, pd.DataFrame(rows), check_dtype=False, check_exact=True)
    summary = pd.read_csv(output / "summary.csv", float_precision="round_trip")
    pd.testing.assert_frame_equal(summary, summarize(rows), check_dtype=False, rtol=1e-12, atol=1e-12)
    if not (len(rows) == 4800 == len({row["seed"] for row in rows}) and len(summary) == 24
            and (summary.trials == 200).all() and state["completed_trials"] == 4800 and state["status"] == "complete"):
        raise ValueError("study is incomplete or duplicates observations")
    result = dict(status="verified", trials=4800, cells=24, trials_per_cell=200,
                  remaining_trials=0, cap_equals_n_minus_one=True, fixed_budget_allocations=True,
                  csv_sqlite_agree=True, summary_metrics_agree=True, population_variance_identity=True,
                  negative_estimates=int((raw.estimate < 0).sum()),
                  noninteger_estimates=int((raw.estimate != np.rint(raw.estimate)).sum()))
    atomic_json(output / "verification.json", result)
    return result


def plot(output, plot_dir):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    state = json.loads((output / "manifest.json").read_text())
    if state["status"] != "complete" or digest(output / "summary.csv") != state["files_sha256"]["summary.csv"]:
        raise ValueError("plot requires the completed, unchanged saved summary")
    frame = pd.read_csv(output / "summary.csv", float_precision="round_trip")
    labels = ["Karate Club", "Dolphins", "Les Misérables", "Brightkite-50"]
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    for graph, label, marker in zip(GRAPH_IDS[:4], labels, ("o", "s", "^", "D"), strict=True):
        cell = frame[frame.graph == graph].sort_values("epsilon")
        if len(cell) != 4 or not (cell.mean_relative_error > 0).all():
            raise ValueError("invalid real-world accuracy series")
        ax.plot(cell.epsilon, cell.mean_relative_error, marker=marker, linewidth=1.8, label=label)
    ax.set(title="Hybrid diamond accuracy on four real-world datasets\nPublic cap B = n − 1; 200 trials per setting",
           xlabel="Total privacy budget ε", ylabel="Mean Relative Error (MAE / exact diamond count)", yscale="log")
    ax.set_xticks(EPSILONS, ["0.5", "1", "2", "4"])
    ax.grid(which="both", alpha=.25)
    ax.legend()
    fig.tight_layout()
    plot_dir.mkdir(parents=True, exist_ok=True)
    path = plot_dir / "mean_relative_error.png"
    fig.savefig(path, dpi=160, metadata={"Software": "private-graphlets"})
    plt.close(fig)
    result = dict(plot=str(path), sha256=digest(path), source_summary_sha256=digest(output / "summary.csv"),
                  metric="mean_relative_error = MAE / exact_count", graphs=GRAPH_IDS[:4])
    atomic_json(plot_dir / "provenance.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify", "plot"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--plot-dir", type=Path, default=DEFAULT_PLOTS)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-new-trials", type=int)
    args = parser.parse_args()
    if args.command == "run":
        result = run(args.config, args.output, resume=args.resume, max_new_trials=args.max_new_trials)
    elif args.command == "verify":
        result = verify(args.output)
    else:
        result = plot(args.output, args.plot_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
