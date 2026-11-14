"""Tests for non-recursive BFS transitive dependency graph builder."""

import unittest
from src.cargo import CargoDependency, parse_test_repository_graph
from src.graph import build_dependency_graph_bfs


def make_memory_resolver(graph_text: str):
    """Create in-memory dependency resolver from test graph text."""
    parsed = parse_test_repository_graph(graph_text)

    def resolve(pkg: str, _ver: str) -> list:
        """Return direct CargoDependency list for package."""
        return [
            CargoDependency(dep, "*", False, "normal")
            for dep in parsed.get(pkg, [])
        ]

    return resolve


class TestBfsDependencyGraph(unittest.TestCase):
    """Test suite verifying BFS traversal, filtering, and cycle safety."""

    def test_bfs_order_and_diamond_graph(self) -> None:
        """Verify breadth-first traversal order on diamond graph."""
        raw = "A: B, C\nB: D\nC: D, E\nD:\nE:\n"
        resolver = make_memory_resolver(raw)
        graph = build_dependency_graph_bfs("A", "1.0.0", resolver)
        nodes = list(graph.adjacency.keys())
        self.assertEqual(nodes, ["A", "B", "C", "D", "E"])
        self.assertEqual(graph.cycles, [])

    def test_cyclic_dependencies_handled_safely(self) -> None:
        """Ensure cycles do not cause infinite loop and are recorded."""
        raw = "A: B\nB: C\nC: A\n"
        resolver = make_memory_resolver(raw)
        graph = build_dependency_graph_bfs("A", "1.0.0", resolver)
        self.assertEqual(list(graph.adjacency.keys()), ["A", "B", "C"])
        self.assertEqual(graph.cycles, [("C", "A")])

    def test_self_loop_cycle_handled(self) -> None:
        """Ensure direct self-dependency A -> A is detected."""
        raw = "A: A, B\nB:\n"
        resolver = make_memory_resolver(raw)
        graph = build_dependency_graph_bfs("A", "1.0.0", resolver)
        self.assertIn(("A", "A"), graph.cycles)
        self.assertIn("B", graph.adjacency)

    def test_substring_filtering_excludes_subgraph(self) -> None:
        """Exclude packages matching filter substring and their children."""
        raw = "A: B, SKIPME\nB: C\nSKIPME: D\nC:\nD:\n"
        resolver = make_memory_resolver(raw)
        graph = build_dependency_graph_bfs(
            "A", "1.0.0", resolver, filter_substring="SKIP"
        )
        self.assertEqual(graph.adjacency["A"], ["B"])
        self.assertNotIn("SKIPME", graph.adjacency)
        self.assertNotIn("D", graph.adjacency)

    def test_root_filtered_returns_empty_graph(self) -> None:
        """Return empty graph if root package matches filter substring."""
        raw = "TESTAPP: B\nB:\n"
        resolver = make_memory_resolver(raw)
        graph = build_dependency_graph_bfs(
            "TESTAPP", "1.0.0", resolver, filter_substring="TEST"
        )
        self.assertEqual(graph.adjacency, {})


if __name__ == "__main__":
    unittest.main()
