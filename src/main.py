"""Entrypoint executing Stages 1, 2, and 3 via CLI parameters."""

import sys
from typing import List
from src.cargo import CargoDependency, get_crate_dependencies
from src.cli import parse_arguments, print_config_key_value
from src.graph import (
    DependencyGraph,
    build_dependency_graph_bfs,
    create_live_resolver,
    create_test_resolver,
)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def print_direct_dependencies(
    package_name: str, direct_deps: List[CargoDependency]
) -> None:
    """Print direct dependencies extracted in Stage 2."""
    print("\n=== Stage 2: Direct Dependencies ===")
    if not direct_deps:
        print(f"Package '{package_name}' has no direct dependencies.")
        return
    for dep in direct_deps:
        print(f"- {dep.name} ({dep.requirement})")


def print_dependency_graph(graph: DependencyGraph) -> None:
    """Print constructed transitive BFS graph and detected cycles."""
    print(
        f"\n=== Stage 3: Transitive Dependency Graph (Root: {graph.root}) ==="
    )
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
    """Parse CLI arguments, extract direct deps, and build BFS graph."""
    try:
        config = parse_arguments(sys.argv[1:])
    except Exception as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return EXIT_FAILURE

    print_config_key_value(config)

    try:
        direct_deps = get_crate_dependencies(
            repo_target=config.repo_url_or_path,
            crate_name=config.package_name,
            crate_version=config.package_version,
            test_mode=config.test_mode,
        )
        print_direct_dependencies(config.package_name, direct_deps)

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
        print(f"Execution error: {error}", file=sys.stderr)
        return EXIT_FAILURE

    print_dependency_graph(graph)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(run_cli_pipeline())
