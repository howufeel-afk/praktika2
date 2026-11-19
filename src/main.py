"""Entrypoint executing Stages 1 through 5 via CLI parameters."""

import sys
from typing import List
from src.cargo import CargoDependency, get_crate_dependencies
from src.cli import parse_arguments, print_config_key_value
from src.config import AppConfig
from src.graph import (
    DependencyGraph,
    build_dependency_graph_bfs,
    create_live_resolver,
    create_live_reverse_resolver,
    create_test_resolver,
    create_test_reverse_resolver,
)
from src.visualizer import save_graph_visualization

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


def print_dependency_graph(
    graph: DependencyGraph, is_reverse: bool = False
) -> None:
    """Print constructed transitive BFS graph (Stages 3 and 4)."""
    if is_reverse:
        print(
            f"\n=== Stage 4: Reverse Dependency Graph "
            f"(Target: {graph.root}) ==="
        )
    else:
        print(
            f"\n=== Stage 3: Transitive Dependency Graph "
            f"(Root: {graph.root}) ==="
        )

    if not graph.adjacency:
        print("Graph is empty (node filtered out or no nodes).")
        return

    arrow = "<-" if is_reverse else "->"
    for node, deps in graph.adjacency.items():
        targets = ", ".join(deps) if deps else "(none)"
        print(f"{node} {arrow} {targets}")

    if graph.cycles:
        print("\n=== Detected Cyclic Dependencies ===")
        for source, target in graph.cycles:
            print(f"Cycle edge: {source} -> {target}")


def print_visualization_result(puml_text: str, output_file: str) -> None:
    """Print generated PlantUML representation and saved image path."""
    print("\n=== Stage 5: PlantUML Representation ===")
    print(puml_text.strip())
    print(f"\nSaved diagram image: {output_file}")


def execute_forward_pipeline(config: AppConfig) -> DependencyGraph:
    """Run Stages 2 and 3 (direct deps and forward transitive BFS)."""
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

    return build_dependency_graph_bfs(
        root_package=config.package_name,
        root_version=config.package_version,
        resolver=resolver,
        filter_substring=config.filter_substring,
    )


def execute_reverse_pipeline(config: AppConfig) -> DependencyGraph:
    """Run Stage 4 reverse dependency traversal using BFS."""
    if config.test_mode:
        resolver = create_test_reverse_resolver(config.repo_url_or_path)
    else:
        resolver = create_live_reverse_resolver()

    return build_dependency_graph_bfs(
        root_package=config.package_name,
        root_version=config.package_version,
        resolver=resolver,
        filter_substring=config.filter_substring,
    )


def run_cli_pipeline() -> int:
    """Execute full CLI pipeline across Stages 1 to 5."""
    try:
        config = parse_arguments(sys.argv[1:])
    except Exception as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return EXIT_FAILURE

    print_config_key_value(config)

    try:
        if config.reverse_mode:
            graph = execute_reverse_pipeline(config)
        else:
            graph = execute_forward_pipeline(config)

        print_dependency_graph(graph, is_reverse=config.reverse_mode)
        puml_text, saved_path = save_graph_visualization(
            adjacency=graph.adjacency,
            cycles=graph.cycles,
            root_name=graph.root,
            output_file=config.output_file,
            is_reverse=config.reverse_mode,
        )
    except Exception as error:
        print(f"Execution error: {error}", file=sys.stderr)
        return EXIT_FAILURE

    print_visualization_result(puml_text, saved_path)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(run_cli_pipeline())
