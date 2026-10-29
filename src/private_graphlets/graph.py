"""Validated, immutable simple undirected graphs on public IDs 0 through n-1."""

from collections.abc import Iterable
from dataclasses import dataclass
from numbers import Integral
from pathlib import Path


def _nonnegative_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return int(value)


@dataclass(frozen=True, slots=True)
class SimpleGraph:
    """Symmetric adjacency with no loops, duplicate neighbors, or missing IDs.

    The entire adjacency is sensitive local input, not a mechanism release.
    Prefer ``from_edges`` for construction; direct adjacency is also validated.
    """

    adjacency: tuple[frozenset[int], ...]

    def __post_init__(self) -> None:
        rows = tuple(frozenset(row) for row in self.adjacency)
        n = len(rows)
        for vertex, neighbors in enumerate(rows):
            for neighbor in neighbors:
                _nonnegative_integer(neighbor, "vertex ID")
                if neighbor >= n:
                    raise ValueError("vertex ID outside the declared vertex set")
                if neighbor == vertex:
                    raise ValueError("self-loops are not allowed")
                if vertex not in rows[neighbor]:
                    raise ValueError("undirected adjacency must be symmetric")
        object.__setattr__(self, "adjacency", rows)

    @classmethod
    def from_edges(cls, num_vertices: int, edges: Iterable[tuple[int, int]]) -> "SimpleGraph":
        """Deduplicate edges, including reversed copies; retain all isolates."""
        n = _nonnegative_integer(num_vertices, "num_vertices")
        rows: list[set[int]] = [set() for _ in range(n)]
        for u, v in edges:
            u = _nonnegative_integer(u, "vertex ID")
            v = _nonnegative_integer(v, "vertex ID")
            if u >= n or v >= n:
                raise ValueError("vertex ID outside the declared vertex set")
            if u == v:
                raise ValueError("self-loops are not allowed")
            rows[u].add(v)
            rows[v].add(u)
        return cls(tuple(frozenset(row) for row in rows))

    @property
    def num_vertices(self) -> int:
        return len(self.adjacency)

    @property
    def num_edges(self) -> int:
        """Exact sensitive edge count; for validation/evaluation, not release."""
        return sum(map(len, self.adjacency)) // 2


def parse_edge_list(lines: Iterable[str]) -> SimpleGraph:
    """Read ``n m`` followed by pairs, where m is the UNIQUE undirected count.

    Blank lines and # comments (including inline comments) are ignored.
    Duplicate/reversed rows are allowed but do not increase m. Loops are errors.
    """
    records = (
        (number, line.partition("#")[0].split())
        for number, line in enumerate(lines, start=1)
    )
    records = ((number, fields) for number, fields in records if fields)

    def pair(number: int, fields: list[str]) -> tuple[int, int]:
        if len(fields) != 2:
            raise ValueError(f"line {number}: expected exactly two integers")
        try:
            return int(fields[0]), int(fields[1])
        except ValueError as exc:
            raise ValueError(f"line {number}: expected exactly two integers") from exc

    try:
        number, fields = next(records)
    except StopIteration as exc:
        raise ValueError("missing n m header") from exc
    n, expected_edges = pair(number, fields)
    _nonnegative_integer(n, "num_vertices")
    _nonnegative_integer(expected_edges, "header edge count")
    if expected_edges > n * (n - 1) // 2:
        raise ValueError("header edge count exceeds the simple-graph maximum")

    def edges() -> Iterable[tuple[int, int]]:
        for number, fields in records:
            u, v = pair(number, fields)
            if not (0 <= u < n and 0 <= v < n):
                raise ValueError(f"line {number}: vertex ID outside [0, n)")
            if u == v:
                raise ValueError(f"line {number}: self-loops are not allowed")
            yield u, v

    graph = SimpleGraph.from_edges(n, edges())
    if graph.num_edges != expected_edges:
        raise ValueError("header edge count does not match unique undirected edges")
    return graph


def load_edge_list(path: str | Path) -> SimpleGraph:
    """Load a UTF-8 edge-list file; propagate filesystem or validation errors."""
    with Path(path).open(encoding="utf-8") as stream:
        return parse_edge_list(stream)
