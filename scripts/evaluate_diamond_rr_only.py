"""Separate six-dataset evaluation entry point for the supplied RR-only estimator.

`check` validates inputs without sampling. `run` is an explicit new experiment;
it preserves each observation in SQLite and refuses overwriting an earlier run.
No imports from, or changes to, the existing hybrid diamond evaluation script.
"""

import argparse
from datetime import datetime, timezone
import fcntl
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import sqlite3
import sys
import time

import numpy as np
import pandas as pd

from private_graphlets.diamond_rr_only import estimate_rr_only_diamonds
from private_graphlets.escape import parse_count_four_output
from private_graphlets.graph_datasets import PROJECT, digest, json_bytes, load_prepared_graph

GRAPH_IDS = ("karate", "dolphins", "les_miserables", "brightkite_50", "ba_n100", "sbm_n100")
EPSILONS = (.5, 1., 2.)
METHOD = "one_owner_rr_only_diamond"
DEFAULT_OUTPUT = PROJECT / "experiments/results/diamond_rr_only_six_datasets"


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)


def load_inputs():
    manifest_path = PROJECT / "data/processed/graph_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    lookup = {row["id"]: row for row in manifest["graphs"]}
    if len(manifest["graphs"]) != 6 or set(lookup) != set(GRAPH_IDS):
        raise ValueError("expected the six pinned benchmark graphs")
    graphs, truth = [], []
    for name in GRAPH_IDS:
        row = lookup[name]
        spec = dict(path="data/processed/"+row["path"], sha256=row["sha256"],
                    n=row["processed_vertices"], m=row["processed_edges"])
        graph = load_prepared_graph(spec)
        if digest(PROJECT / "data/processed" / row["mapping_path"]) != row["mapping_sha256"]:
            raise ValueError("mapping hash changed")
        native = parse_count_four_output(row["validation"]["escape_output"],
                    num_vertices=graph.num_vertices, num_edges=graph.num_edges).connected_four["diamond"]
        graphs.append(graph)
        truth.append(dict(graph=name, **spec, exact_count=native,
                          mapping_sha256=row["mapping_sha256"], escape_output=row["validation"]["escape_output"],
                          reference=manifest["escape_reference"]))
    return graphs, truth


def configuration(trials, seed):
    if type(trials) is not int or not 1 <= trials < 2**32:
        raise ValueError("trials must be an integer in [1,2**32)")
    if type(seed) is not int or seed < 0:
        raise ValueError("an explicit nonnegative simulation master seed is required")
    return dict(method=METHOD, graph_ids=list(GRAPH_IDS), epsilons=list(EPSILONS), trials=trials,
                master_seed=seed, seed_rule="(master<<64)|(graph_index<<48)|(epsilon_index<<32)|trial",
                epsilon_rr="total_epsilon", epsilon_laplace=0., epsilon_ordering=0., variance_ddof=0)


def provenance():
    paths = [Path(__file__), *(PROJECT / "src/private_graphlets" / name for name in
             ("diamond_rr_only.py", "randomized_response.py", "noise.py", "graph.py", "graph_datasets.py", "escape.py")),
             PROJECT / "data/processed/graph_manifest.json", PROJECT / "third_party/references.json"]
    return dict(source_sha256={str(p.relative_to(PROJECT)): digest(p) for p in paths},
                python=sys.version, platform=platform.platform(),
                dependencies={name: importlib.metadata.version(name) for name in ("numpy", "pandas", "networkx")})


def coordinates(config):
    for gi in range(len(GRAPH_IDS)):
        for ei in range(len(EPSILONS)):
            for trial in range(config["trials"]):
                yield gi, ei, trial


def seed_for(config, gi, ei, trial):
    return (config["master_seed"] << 64) | (gi << 48) | (ei << 32) | trial


def read_rows(db, config, truth):
    rows = []
    jobs = iter(coordinates(config))
    for i, (ordinal, payload) in enumerate(db.execute("SELECT ordinal,payload FROM trials ORDER BY ordinal")):
        coordinate = next(jobs, None)
        if coordinate is None:
            raise ValueError("too many saved trials")
        gi, ei, trial = coordinate
        row = json.loads(payload)
        expected = dict(graph=GRAPH_IDS[gi], method=METHOD, graph_index=gi, epsilon_index=ei,
                        trial=trial, epsilon=EPSILONS[ei], epsilon_rr=EPSILONS[ei],
                        n=truth[gi]["n"], m=truth[gi]["m"], exact_count=truth[gi]["exact_count"],
                        seed=str(seed_for(config, gi, ei, trial)))
        if ordinal != i or any(row[k] != value for k, value in expected.items()):
            raise ValueError("invalid saved coordinate, seed, budget or truth")
        if not math.isfinite(row["estimate"]) or not math.isfinite(row["runtime_seconds"]) or row["runtime_seconds"] < 0:
            raise ValueError("invalid saved estimate/runtime")
        rows.append(row)
    return rows


def summarize(rows):
    records = []
    if not rows:
        return pd.DataFrame()
    for _, cell in pd.DataFrame(rows).groupby(["graph_index", "epsilon_index"], sort=True):
        first = cell.iloc[0]
        x = cell.estimate.to_numpy(dtype=float)
        errors = x-first.exact_count
        mse, mae = float(np.mean(errors**2)), float(np.mean(abs(errors)))
        records.append(dict(graph=first.graph, method=METHOD, n=int(first.n), m=int(first.m),
                            epsilon=first.epsilon, epsilon_rr=first.epsilon, trials=len(x),
                            exact_count=int(first.exact_count), mean_estimate=float(np.mean(x)),
                            bias=float(np.mean(x)-first.exact_count), variance=float(np.var(x, ddof=0)),
                            variance_ddof=0, mse=mse, rmse=math.sqrt(mse), mae=mae,
                            mean_relative_error=mae/first.exact_count if first.exact_count else math.nan,
                            relative_rmse=math.sqrt(mse)/first.exact_count if first.exact_count else math.nan,
                            mean_runtime_seconds=float(cell.runtime_seconds.mean()),
                            negative_estimates=int((x < 0).sum())))
    return pd.DataFrame(records)


def export(db, config, truth, output):
    rows = read_rows(db, config, truth)
    for name, frame in (("trials.csv", pd.DataFrame(rows)), ("summary.csv", summarize(rows))):
        temporary = output / (name+".tmp")
        frame.to_csv(temporary, index=False, float_format="%.17g")
        temporary.replace(output / name)
    total = len(GRAPH_IDS)*len(EPSILONS)*config["trials"]
    state = dict(status="complete" if len(rows) == total else "partial", completed_trials=len(rows),
                 target_trials=total, remaining_trials=total-len(rows),
                 result_type="nonprivate_public_graph_evaluation", updated_utc=datetime.now(timezone.utc).isoformat(),
                 files_sha256={name: digest(output / name) for name in
                     ("config.json", "provenance.json", "escape_ground_truth.json", "trials.csv", "summary.csv")})
    atomic_json(output / "manifest.json", state)
    return state


def run(output, config, *, resume=False, max_new_trials=None):
    if max_new_trials is not None and max_new_trials < 1:
        raise ValueError("max-new-trials must be positive")
    graphs, truth = load_inputs()
    current = provenance()
    existing = output.exists()
    if existing and not resume:
        raise FileExistsError("output already exists; use --resume, never overwrite previous results")
    output.mkdir(parents=True, exist_ok=resume)
    with (output / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        metadata = {"config": config, "provenance": current, "escape_ground_truth": truth}
        for name, value in metadata.items():
            path = output / f"{name}.json"
            if existing:
                if json.loads(path.read_text()) != value:
                    raise ValueError(f"resume {name} differs")
            else:
                atomic_json(path, value)
        with sqlite3.connect(output / "trials.sqlite3", timeout=0) as db:
            db.execute("CREATE TABLE IF NOT EXISTS trials (ordinal INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
            db.commit()
            start = len(read_rows(db, config, truth))
            added = 0
            try:
                for ordinal, (gi, ei, trial) in enumerate(coordinates(config)):
                    if ordinal < start:
                        continue
                    if max_new_trials is not None and added >= max_new_trials:
                        break
                    epsilon, graph = EPSILONS[ei], graphs[gi]
                    seed = seed_for(config, gi, ei, trial)
                    begin = time.perf_counter()
                    result = estimate_rr_only_diamonds(graph, epsilon, seed=seed)
                    elapsed = time.perf_counter()-begin
                    if result.epsilon != epsilon or result.num_vertices != graph.num_vertices:
                        raise ValueError("estimator result does not match requested public inputs")
                    row = dict(graph=GRAPH_IDS[gi], method=METHOD, graph_index=gi, epsilon_index=ei,
                               trial=trial, n=graph.num_vertices, m=graph.num_edges,
                               epsilon=epsilon, epsilon_rr=epsilon, seed=str(seed), estimate=result.estimate,
                               exact_count=truth[gi]["exact_count"], runtime_seconds=elapsed,
                               privacy_model=result.privacy_model, privacy_status=result.privacy_status)
                    db.execute("INSERT INTO trials VALUES (?,?)", (ordinal, json.dumps(row, allow_nan=False)))
                    db.commit()
                    added += 1
                    if trial == config["trials"]-1:
                        print(json.dumps(export(db, config, truth, output)), flush=True)
            finally:
                state = export(db, config, truth, output)
    return {**state, "new_trials_this_invocation": added}


def verify(output):
    config = json.loads((output / "config.json").read_text())
    if config != configuration(config["trials"], config["master_seed"]):
        raise ValueError("saved configuration differs from this runner")
    _, truth = load_inputs()
    if (json.loads((output / "provenance.json").read_text()) != provenance()
            or json.loads((output / "escape_ground_truth.json").read_text()) != truth):
        raise ValueError("saved source/data provenance differs")
    state = json.loads((output / "manifest.json").read_text())
    for name, value in state["files_sha256"].items():
        if digest(output / name) != value:
            raise ValueError("saved artifact hash changed")
    with sqlite3.connect(f"file:{output}/trials.sqlite3?mode=ro", uri=True) as db:
        rows = read_rows(db, config, truth)
    if rows:
        raw = pd.read_csv(output / "trials.csv", dtype={"seed": str}, float_precision="round_trip")
        summary = pd.read_csv(output / "summary.csv", float_precision="round_trip")
        pd.testing.assert_frame_equal(raw, pd.DataFrame(rows), check_dtype=False, check_exact=True)
        pd.testing.assert_frame_equal(summary, summarize(rows), check_dtype=False, rtol=1e-12, atol=1e-12)
    total = len(GRAPH_IDS)*len(EPSILONS)*config["trials"]
    if (len(rows) != state["completed_trials"] or state["target_trials"] != total
            or state["remaining_trials"] != total-len(rows)
            or state["status"] != ("complete" if len(rows) == total else "partial")):
        raise ValueError("saved completion state differs")
    return dict(status="verified", study_status=state["status"], trials=len(rows), remaining_trials=total-len(rows))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "run", "verify"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, help="Explicit research master seed; required for run/check")
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-new-trials", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = verify(args.output)
        else:
            config = configuration(args.trials, args.seed)
            if args.command == "check":
                _, truth = load_inputs()
                result = dict(status="inputs_checked_no_sampling", config=config, graphs=len(truth),
                              planned_trials=len(GRAPH_IDS)*len(EPSILONS)*args.trials,
                              diamond_truth={r["graph"]: r["exact_count"] for r in truth})
            else:
                result = run(args.output, config, resume=args.resume, max_new_trials=args.max_new_trials)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
    except (ValueError, OSError, FloatingPointError, OverflowError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
