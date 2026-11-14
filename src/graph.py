"""Non-recursive BFS dependency graph builder with cycle handling."""

from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Dict, FrozenSet, List, Set, Tuple

from src.cargo import (
    CargoDependency,
    fetch_remote_index_data,
    load_test_index_data,
    parse_direct_dependencies,
    parse_test_repository_graph,
    resolve_latest_matching_version,
)

DependencyResolver = Callable[[str, str], List[CargoDependency]]


@dataclass(frozen=True)
class DependencyGraph:
    """Stores transitive adjacency lists and detected cycle edges."""

    root: str
    adjacency: Dict[str, List[str]]
    cycles: List[Tuple[str, str]]


def should_skip_package(package_name: str, filter_substring: str) -> bool:
    """Return True if package name contains the filter substring."""
    if not filter_substring:
        return False
    return filter_substring in package_name


def create_test_resolver(repo_path: str) -> DependencyResolver:
    """Build dependency resolver backed by uppercase test graph file."""
    raw_text = load_test_index_data(repo_path)
    test_graph = parse_test_repository_graph(raw_text)

    def resolve(crate_name: str, _version: str) -> List[CargoDependency]:
        """Return direct dependencies for node from parsed test graph."""
        deps = test_graph.get(crate_name, [])
        return [CargoDependency(d, "*", False, "normal") for d in deps]

    if not test_graph:
        raise ValueError("Test repository graph file is empty.")
    return resolve


def create_live_resolver(repo_url: str) -> DependencyResolver:
    """Build dependency resolver querying remote Cargo sparse index."""
    cache: Dict[str, str] = {}

    def resolve(crate_name: str, version_or_req: str) -> List[CargoDependency]:
        """Fetch index and resolve dependencies for concrete version."""
        if crate_name not in cache:
            cache[crate_name] = fetch_remote_index_data(repo_url, crate_name)
        raw_index = cache[crate_name]
        try:
            return parse_direct_dependencies(raw_index, version_or_req)
        except ValueError:
            matched_ver = resolve_latest_matching_version(
                raw_index, version_or_req
            )
            return parse_direct_dependencies(raw_index, matched_ver)

    return resolve


def build_dependency_graph_bfs(
    root_package: str,
    root_version: str,
    resolver: DependencyResolver,
    filter_substring: str = "",
) -> DependencyGraph:
    """Construct transitive dependency graph via non-recursive BFS."""
    adjacency: Dict[str, List[str]] = {}
    cycles: List[Tuple[str, str]] = []

    if should_skip_package(root_package, filter_substring):
        return DependencyGraph(root_package, adjacency, cycles)

    visited: Set[str] = {root_package}
    queue: Deque[Tuple[str, str, FrozenSet[str]]] = deque()
    queue.append((root_package, root_version, frozenset({root_package})))

    while queue:
        current_pkg, current_ver, ancestors = queue.popleft()
        direct_deps = resolver(current_pkg, current_ver)
        filtered = [
            dep for dep in direct_deps
            if not should_skip_package(dep.name, filter_substring)
        ]
        adjacency[current_pkg] = [dep.name for dep in filtered]
        enqueue_unvisited_deps(
            filtered, current_pkg, ancestors, visited, queue, cycles
        )

    return DependencyGraph(root_package, adjacency, cycles)


def enqueue_unvisited_deps(
    deps: List[CargoDependency],
    parent: str,
    ancestors: FrozenSet[str],
    visited: Set[str],
    queue: Deque[Tuple[str, str, FrozenSet[str]]],
    cycles: List[Tuple[str, str]],
) -> None:
    """Enqueue unseen dependencies and record cyclic back-edges."""
    for dep in deps:
        if dep.name in ancestors:
            cycles.append((parent, dep.name))
            continue
        if dep.name not in visited:
            visited.add(dep.name)
            queue.append((dep.name, dep.requirement, ancestors | {dep.name}))
