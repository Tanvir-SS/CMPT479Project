"""Adapter unit tests. Executable stubs test failures, never count as ESCAPE evidence."""

from pathlib import Path
import sys

import pytest

from private_graphlets.escape import (
    EscapeAdapter, EscapeBuildError, EscapeConfigurationError, EscapeExecutionError,
    EscapeOutputError, MAX_VERTICES, TRANSLATION_UNITS, build_count_four,
    parse_count_four_output, resolve_escape_root, serialize_escape_graph,
)
from private_graphlets.graph import SimpleGraph, parse_edge_list


def output_text(n=4, m=6):
    # Hand-derived NON-INDUCED K4 output, only used to test the parser/stubs.
    return "\n".join(map(str, [n, 2*m, 4, 12, 12, 4, 1, 6, 3, 12, 4,
                              4, 12, 12, 3, 6, 1])) + "\n"


def stub(tmp_path, body):
    executable = tmp_path / "stub executable"
    executable.write_text(f"#!{sys.executable}\n" + body)
    executable.chmod(0o755)
    return executable


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "fake source layout"
    for name in (*TRANSLATION_UNITS, "Escape/GetAllCounts.h"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("// Unit test placeholder, not real ESCAPE code.\n")
    return root


def test_root_configuration(monkeypatch, source, tmp_path):
    monkeypatch.delenv("ESCAPE_ROOT", raising=False)
    with pytest.raises(EscapeConfigurationError, match="ESCAPE_ROOT"):
        resolve_escape_root()
    monkeypatch.setenv("ESCAPE_ROOT", str(source))
    assert resolve_escape_root() == source
    monkeypatch.setenv("ESCAPE_ROOT", str(tmp_path / "missing"))
    assert resolve_escape_root(source) == source
    with pytest.raises(EscapeConfigurationError, match="missing ESCAPE"):
        resolve_escape_root()


def test_build_rejects_source_directory_and_symlink(source, tmp_path):
    with pytest.raises(EscapeConfigurationError, match="outside"):
        build_count_four(source, build_dir=source / "build")
    link = tmp_path / "linked-source"
    link.symlink_to(source, target_is_directory=True)
    with pytest.raises(EscapeConfigurationError, match="outside"):
        build_count_four(source, build_dir=link)


def test_missing_compiler(source, tmp_path):
    with pytest.raises(EscapeBuildError, match="compilation failed"):
        build_count_four(source, build_dir=tmp_path / "build", compiler=str(tmp_path / "missing"))


def test_failed_build_never_uses_stale_binary(source, tmp_path):
    compiler = stub(tmp_path, "import sys\nprint('intentional failure', file=sys.stderr)\nsys.exit(7)\n")
    build = tmp_path / "build"
    build.mkdir()
    (build / "count_four").write_text("old artifact")
    with pytest.raises(EscapeBuildError, match="exit 7"):
        build_count_four(source, build_dir=build, compiler=str(compiler))
    assert "intentional failure" in (build / "compile.log").read_text()


def test_compile_timeout(source, tmp_path):
    compiler = stub(tmp_path, "import time\ntime.sleep(5)\n")
    with pytest.raises(EscapeBuildError, match="timed out"):
        build_count_four(source, build_dir=tmp_path / "build", compiler=str(compiler), timeout=0.1)


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 8])
def test_isolate_normalization(n):
    assert serialize_escape_graph(SimpleGraph.from_edges(n, [])) == f"{max(n,4)} 0\n"


def test_serialization_deduplication_order_and_roundtrip():
    graph = parse_edge_list(["7 3", "3 1", "1 3 # duplicate", "0 2", "2 0", "4 1"])
    serialized = serialize_escape_graph(graph)
    assert serialized == "7 3\n0 2\n1 3\n1 4\n"
    assert parse_edge_list(serialized.splitlines()) == graph


def test_size_bound():
    with pytest.raises(ValueError, match="at most"):
        serialize_escape_graph(SimpleGraph.from_edges(MAX_VERTICES + 1, []))


def test_parse_noninduced_columns():
    result = parse_count_four_output(output_text(), num_vertices=4, num_edges=6)
    assert result.three_stars == 4  # Induced K1,3 count in K4 would be zero.
    assert result.connected_four == {
        "3-star": 4, "3-path": 12, "tailed triangle": 12,
        "4-cycle": 3, "diamond": 6, "4-clique": 1,
    }
    assert result.three_vertex == (4, 12, 12, 4)


def test_signed_zero_from_edgeless_escape_output():
    lines = output_text(n=4, m=0).splitlines()
    lines[8] = "-0.000000"
    result = parse_count_four_output("\n".join(lines), num_vertices=4, num_edges=0)
    assert result.four_vertex[2] == 0


@pytest.mark.parametrize("bad", ["nan", "Infinity", "-1", "0.25", "junk", "", "1_0", "1e2", str(2**53)])
@pytest.mark.parametrize("index", [2, 11, 16])
def test_reject_invalid_counts(bad, index):
    lines = output_text().splitlines()
    lines[index] = bad
    with pytest.raises(EscapeOutputError):
        parse_count_four_output("\n".join(lines), num_vertices=4, num_edges=6)


@pytest.mark.parametrize("change", ["missing", "extra", "bad_n", "wrong_n", "undirected_m"])
def test_output_shape_and_header(change):
    lines = output_text().splitlines()
    if change == "missing":
        lines.pop()
    elif change == "extra":
        lines.append("0")
    elif change == "bad_n":
        lines[0] = "4.0"
    elif change == "wrong_n":
        lines[0] = "5"
    else:
        lines[1] = "6"
    with pytest.raises(EscapeOutputError):
        parse_count_four_output("\n".join(lines), num_vertices=4, num_edges=6)


def test_missing_executable(tmp_path):
    with pytest.raises(EscapeConfigurationError, match="not an executable"):
        EscapeAdapter(tmp_path / "missing")


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_timeout_validation(tmp_path, timeout):
    with pytest.raises(ValueError, match="timeout"):
        EscapeAdapter(tmp_path / "missing", timeout=timeout)


def test_command_failure_includes_stderr(tmp_path):
    binary = stub(tmp_path, "import sys\nprint('broken', file=sys.stderr)\nsys.exit(9)\n")
    with pytest.raises(EscapeExecutionError, match="exited 9.*broken"):
        EscapeAdapter(binary).run(SimpleGraph.from_edges(4, []))


def test_missing_output_never_reads_stale_parent_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out.txt").write_text(output_text())
    binary = stub(tmp_path, "pass\n")
    with pytest.raises(EscapeOutputError, match="out.txt"):
        EscapeAdapter(binary).run(SimpleGraph.from_edges(4, []))


def test_timeout_is_explicit(tmp_path):
    binary = stub(tmp_path, "import time\ntime.sleep(5)\n")
    with pytest.raises(EscapeExecutionError, match="timed out"):
        EscapeAdapter(binary, timeout=0.1).run(SimpleGraph.from_edges(4, []))


@pytest.mark.parametrize("content", ["b'junk'", "b'\\xff'"])
def test_unreadable_or_malformed_output(tmp_path, content):
    binary = stub(tmp_path, f"from pathlib import Path\nPath('out.txt').write_bytes({content})\n")
    with pytest.raises(EscapeOutputError):
        EscapeAdapter(binary).run(SimpleGraph.from_edges(4, []))


def test_isolated_workdir_and_count_api(tmp_path):
    text = output_text()
    binary = stub(tmp_path, "from pathlib import Path\nimport sys\n"
                  "assert Path(sys.argv[1]).read_text().startswith('4 6\\n')\n"
                  f"Path('out.txt').write_text({text!r})\nprint(Path.cwd())\n")
    graph = SimpleGraph.from_edges(4, [(i, j) for i in range(4) for j in range(i+1, 4)])
    adapter = EscapeAdapter(binary)
    run = adapter.run(graph)
    assert run.output_text == text
    assert run.counts.three_stars == adapter.count_three_stars(graph) == 4
    assert not Path(run.stdout.strip()).exists()  # Temporary run directory cleaned.
    assert not (tmp_path / "out.txt").exists()
