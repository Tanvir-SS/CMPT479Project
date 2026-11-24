"""Prepare the opt-in SNAP suite and collect native ESCAPE ground truth on Linux."""
import gzip
import json
import math
from pathlib import Path
import resource
import subprocess
import tarfile
import tempfile

from private_graphlets.escape import build_count_four, parse_count_four_output
from private_graphlets.graph import SimpleGraph
from private_graphlets.graph_datasets import (
    PROJECT, canonical_bytes, digest, json_bytes, load_prepared_graph, write_identical_or_new,
)

RAW = PROJECT / "data/raw/snap_large"
OUT = PROJECT / "data/processed/snap_large"
BUILD = PROJECT / "build/phase34"
# (id, archive, original nodes, original records, archive sha256)
SOURCES = (
    ("email_eu_core", "email-Eu-core.txt.gz", 1005, 25571,
     "4b47acdb80197b085fe63c819c357ae488131ee904ed93d1b219a68b0f9e245f"),
    ("facebook", "facebook_combined.txt.gz", 4039, 88234,
     "125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7"),
    ("wikispeedia", "wikispeedia_paths-and-graph.tar.gz", 4604, 119882,
     "97697096f5d2dcb77aa69e3992305c6c561de89edb9fb10b5ad9feaf8ba534d5"),
)


def records(stream):
    for line in stream:
        value = line.decode("utf-8").strip()
        if value and not value.startswith("#"):
            yield value


def read_graph(name, archive, n):
    if name == "wikispeedia":
        with tarfile.open(archive, "r:gz") as tar:
            prefix = "wikispeedia_paths-and-graph/"
            titles = list(records(tar.extractfile(prefix + "articles.tsv")))
            if len(titles) != n or len(set(titles)) != n:
                raise ValueError("article roster differs from expected universe")
            nodes = sorted(titles)
            index = {title: i for i, title in enumerate(nodes)}
            pairs = [tuple(index[t] for t in line.split("\t"))
                     for line in records(tar.extractfile(prefix + "links.tsv"))]
    else:
        nodes = list(range(n))
        with gzip.open(archive, "rb") as stream:
            pairs = [tuple(map(int, line.split())) for line in records(stream)]
        if {v for pair in pairs for v in pair} != set(nodes):
            raise ValueError("numeric IDs differ from the expected contiguous roster")
    loops = sum(a == b for a, b in pairs)
    graph = SimpleGraph.from_edges(n, ((a, b) for a, b in pairs if a != b))
    return nodes, graph, len(pairs), loops


def limit_memory():
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))


def count(binary, path, n, m):
    # count_four uses int64 indices/counts and binary64 output. n^4 bounds
    # four-distinct ordered tuples and n(n-1)(n-2)(n-3) before division.
    if not (1000 < n < 10000 and n**4 < 2**53):
        raise ValueError("outside the reviewed large-SNAP numeric domain")
    with tempfile.TemporaryDirectory(dir=BUILD) as work:
        subprocess.run([binary, path], cwd=work, timeout=120, check=True,
                       preexec_fn=limit_memory, stdout=subprocess.DEVNULL)
        raw = (Path(work) / "out.txt").read_text()
    counts = parse_count_four_output(raw, num_vertices=n, num_edges=m)
    return raw, counts.connected_four


def main():
    binary = build_count_four(build_dir=BUILD / "escape")
    suite = []
    for name, filename, n, expected, sha in SOURCES:
        archive = RAW / filename
        if digest(archive) != sha:
            raise ValueError(f"source archive hash mismatch: {filename}")
        nodes, graph, rows, loops = read_graph(name, archive, n)
        if rows != expected:
            raise ValueError(f"unexpected original edge count: {rows}")
        path = OUT / f"{name}.edges"
        mapping = OUT / f"{name}.mapping.json"
        write_identical_or_new(path, canonical_bytes(graph))
        write_identical_or_new(mapping, json_bytes([
            dict(processed_id=i, original_id=v) for i, v in enumerate(nodes)]))
        m = graph.num_edges
        spec = dict(id=name, family="prepared_edge_list", path=str(path.relative_to(PROJECT)),
                    sha256=digest(path), n=n, m=m)
        if load_prepared_graph(spec) != graph:
            raise ValueError("graph did not round-trip through the prepared loader")
        raw, counts = count(binary, path, n, m)
        degrees = [len(row) for row in graph.adjacency]
        suite.append(dict(**spec, archive=filename, archive_sha256=sha,
                          mapping_path=str(mapping.relative_to(PROJECT)), mapping_sha256=digest(mapping),
                          original_vertices=n, original_edges=rows, self_loops_removed=loops,
                          duplicate_or_reverse_edges_removed=rows-loops-m, isolates=degrees.count(0),
                          density=m/math.comb(n, 2), maximum_degree=max(degrees),
                          escape_output=raw, connected_four=counts))
        print(name, n, m, counts, flush=True)
    build = json.loads((BUILD / "escape/build.json").read_text())
    manifest = dict(dataset_suite="snap_large", escape_source_sha256=build["source_sha256"], graphs=suite)
    write_identical_or_new(OUT / "graph_manifest.json", json_bytes(manifest))


if __name__ == "__main__":
    main()
