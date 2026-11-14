"""Entrypoint executing Stage 3 transitive dependency graph analysis."""

import sys
from src.cli import parse_arguments
from src.graph import (
    DependencyGraph,
    build_dependency_graph_bfs,
    create_live_resolver,
    create_test_resolver,
)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def print_dependency_graph(graph: DependencyGraph) -> None:
    """Print constructed transitive graph and any detected cycles."""
    print(f"=== Transitive Dependency Graph (Root: {graph.root}) ===")
    if not graph.adjacency:
        print("Graph is empty (root filtered out or no nodes).")
        return

    for node, deps in graph.adjacency.items():
        targets = ", ".join(deps) if deps else "(none)"
        print(f"{node} -> {targets}")

    if graph.cycles:
        print("\n=== Detected Cyclic Dependencies ===")
        for source, target in graph.cycles:
            print(f"Cycle edge: {source} -> {target}")


def run_cli_pipeline() -> int:
    """Parse arguments, build BFS dependency graph, and display output."""
    try:
        config = parse_arguments(sys.argv[1:])
    except Exception as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return EXIT_FAILURE

    try:
        if config.test_mode:
            resolver = create_test_resolver(config.repo_url_or_path)
        else:
            resolver = create_live_resolver(config.repo_url_or_path)

        graph = build_dependency_graph_bfs(
            root_package=config.package_name,
            root_version=config.package_version,
            resolver=resolver,
            filter_substring=config.filter_substring,
        )
    except Exception as error:
        print(f"Graph construction error: {error}", file=sys.stderr)
        return EXIT_FAILURE

    print_dependency_graph(graph)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(run_cli_pipeline())
