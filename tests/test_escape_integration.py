"""Real ESCAPE comparisons. All tests execute the external reference binary."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest

from private_graphlets.escape_validation import compare_case, validation_cases
from private_graphlets.graph import load_edge_list


pytestmark = pytest.mark.escape_integration
CASES = validation_cases()
FIXTURES = Path(__file__).resolve().parents[1] / "data/fixtures"
EXPECTED = json.loads((FIXTURES / "expected_counts.json").read_text())["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_three_independent_counters(escape_adapter, case):
    row = compare_case(escape_adapter, case)
    assert row["all_agree"], row
    expected = {"edgeless_6": 0, "star_3": 1, "star_4": 4, "K4": 4, "K5": 20,
                "path_7": 0, "overlapping_stars": 2, "disjoint_stars_and_isolates": 2,
                "zero_vertices": 0, "one_isolate": 0, "single_edge": 0, "triangle": 0}
    if case.name in expected:
        assert row["escape_three_stars"] == expected[case.name]
    # Particularly distinguishes non-induced stars from induced stars (zero) in cliques.
    if case.name == "K4":
        assert list(row["escape_connected_four"].values()) == [4, 12, 12, 3, 6, 1]
    if case.name == "K5":
        assert list(row["escape_connected_four"].values()) == [20, 60, 60, 15, 30, 5]


@pytest.mark.parametrize("name", EXPECTED)
def test_original_six_column_fixtures(escape_adapter, name):
    result = escape_adapter.run(load_edge_list(FIXTURES / f"{name}.edges"))
    assert list(result.counts.connected_four.values()) == EXPECTED[name]


def test_concurrent_calls_do_not_share_out_txt(escape_adapter):
    selected = CASES[1:5]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(escape_adapter.count_three_stars, [c.graph for c in selected]))
    assert results == [1, 4, 4, 20]
