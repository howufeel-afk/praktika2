"""Non-recursive BFS dependency graph builder with cycle handling."""

from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Dict, FrozenSet, List, Set, Tuple

from src.cargo import (
    CargoDependency,
    fetch_remote_index_data,
    fetch_remote_reverse_dependents,
    load_test_index_data,
    parse_direct_dependencies,
    parse_jsonl_full_graph,
    parse_test_repository_graph,
    resolve_latest_matching_version,
)

DependencyResolver = Callable[[str, str], List[CargoDependency]]
LIVE_REVERSE_MAX_DEPTH = 2


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


def invert_adjacency_graph(
    forward_graph: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """Transpose forward dependency edges into reverse dependency map."""
    reversed_map: Dict[str, List[str]] = {
        node: [] for node in forward_graph
    }
    for parent, children in forward_graph.items():
        for child in children:
            dependents = reversed_map.setdefault(child, [])
            if parent not in dependents:
                dependents.append(parent)
    return reversed_map


def create_jsonl_test_resolver(raw_jsonl: str) -> DependencyResolver:
    """Build dependency resolver backed by local Cargo JSONL mock file."""

    def resolve(crate_name: str, version_or_req: str) -> List[CargoDependency]:
        """Resolve direct dependencies for crate from mock JSONL lines."""
        try:
            return parse_direct_dependencies(
                raw_jsonl, version_or_req, crate_name
            )
        except ValueError:
            matched_ver = resolve_latest_matching_version(
                raw_jsonl, version_or_req, crate_name
            )
            return parse_direct_dependencies(
                raw_jsonl, matched_ver, crate_name
            )

    return resolve


def create_test_resolver(repo_path: str) -> DependencyResolver:
    """Build dependency resolver backed by test graph or mock JSONL file."""
    raw_text = load_test_index_data(repo_path)
    if repo_path.lower().endswith(".jsonl"):
        return create_jsonl_test_resolver(raw_text)

    test_graph = parse_test_repository_graph(raw_text)
    if not test_graph:
        raise ValueError("Test repository graph file is empty.")

    def resolve(crate_name: str, _version: str) -> List[CargoDependency]:
        """Return direct dependencies for node from parsed test graph."""
        if crate_name not in test_graph:
            raise ValueError(f"Package '{crate_name}' not in test repo.")
        deps = test_graph[crate_name]
        return [CargoDependency(d, "*", False, "normal") for d in deps]

    return resolve


def create_test_reverse_resolver(repo_path: str) -> DependencyResolver:
    """Build reverse dependency resolver from local test repository."""
    raw_text = load_test_index_data(repo_path)
    if repo_path.lower().endswith(".jsonl"):
        forward_graph = parse_jsonl_full_graph(raw_text)
    else:
        forward_graph = parse_test_repository_graph(raw_text)

    if not forward_graph:
        raise ValueError("Test repository graph file is empty.")
    reversed_graph = invert_adjacency_graph(forward_graph)

    def resolve(crate_name: str, _version: str) -> List[CargoDependency]:
        """Return packages that depend on crate_name."""
        if crate_name not in reversed_graph:
            raise ValueError(f"Package '{crate_name}' not in test repo.")
        parents = reversed_graph[crate_name]
        return [CargoDependency(p, "*", False, "normal") for p in parents]

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
            return parse_direct_dependencies(
                raw_index, version_or_req, crate_name
            )
        except ValueError:
            matched_ver = resolve_latest_matching_version(
                raw_index, version_or_req, crate_name
            )
            return parse_direct_dependencies(
                raw_index, matched_ver, crate_name
            )

    return resolve


def create_live_reverse_resolver() -> DependencyResolver:
    """Build bounded reverse resolver querying crates.io API."""
    depths: Dict[str, int] = {}

    def resolve(crate_name: str, _version: str) -> List[CargoDependency]:
        """Fetch reverse dependents up to bounded depth."""
        current_depth = depths.setdefault(crate_name, 0)
        if current_depth >= LIVE_REVERSE_MAX_DEPTH:
            return []
        dependents = fetch_remote_reverse_dependents(crate_name)
        for dep in dependents:
            depths.setdefault(dep, current_depth + 1)
        return [
            CargoDependency(dep, "*", False, "normal") for dep in dependents
        ]

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
