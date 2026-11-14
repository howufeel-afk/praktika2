"""Cargo package dependency fetcher and test repository parser."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Dict, List
import urllib.error
import urllib.request

HTTP_USER_AGENT = "CargoVisualizer/1.0 (StudentProject)"
HTTP_TIMEOUT_SECONDS = 15
NORMAL_DEPENDENCY_KIND = "normal"
CRATE_MIN_LEN_ONE = 1
CRATE_MIN_LEN_TWO = 2
CRATE_MIN_LEN_THREE = 3
UPPER_PACKAGE_PATTERN = r"^[A-Z]+$"
KEY_VALUE_PARTS = 2


@dataclass(frozen=True)
class CargoDependency:
    """Represents a direct cargo crate dependency."""

    name: str
    requirement: str
    optional: bool
    kind: str


def compute_crate_index_subpath(crate_name: str) -> str:
    """Compute relative path of crate in Cargo sparse index."""
    name = crate_name.lower()
    length = len(name)
    if length == CRATE_MIN_LEN_ONE:
        return f"1/{name}"
    if length == CRATE_MIN_LEN_TWO:
        return f"2/{name}"
    if length == CRATE_MIN_LEN_THREE:
        return f"3/{name[0]}/{name}"
    return f"{name[0:2]}/{name[2:4]}/{name}"


def fetch_remote_index_data(repo_url: str, crate_name: str) -> str:
    """Fetch crate metadata lines from remote Cargo sparse index."""
    subpath = compute_crate_index_subpath(crate_name)
    target_url = f"{repo_url.rstrip('/')}/{subpath}"
    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": HTTP_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(
            req, timeout=HTTP_TIMEOUT_SECONDS
        ) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"Failed to fetch crate '{crate_name}' (HTTP {error.code})"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Network error while connecting to index: {error.reason}"
        ) from error


def load_test_index_data(file_path: str) -> str:
    """Load mock repository data from local file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Mock file not found: {file_path}")
    return path.read_text(encoding="utf-8")


def parse_direct_dependencies(
    raw_index_lines: str, target_version: str
) -> List[CargoDependency]:
    """Parse JSON lines and return dependencies for matching version."""
    for line in raw_index_lines.strip().splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        record = json.loads(line_clean)
        if record.get("vers") == target_version:
            return extract_normal_deps(record.get("deps", []))

    raise ValueError(f"Version '{target_version}' not found in index.")


def extract_normal_deps(raw_deps: List[dict]) -> List[CargoDependency]:
    """Filter out dev and optional dependencies from raw JSON list."""
    result: List[CargoDependency] = []
    for item in raw_deps:
        kind = item.get("kind", NORMAL_DEPENDENCY_KIND)
        optional = item.get("optional", False)
        if kind == NORMAL_DEPENDENCY_KIND and not optional:
            result.append(
                CargoDependency(
                    name=item.get("name", ""),
                    requirement=item.get("req", "*"),
                    optional=optional,
                    kind=kind,
                )
            )
    return result


def resolve_latest_matching_version(
    raw_index_lines: str, requirement: str
) -> str:
    """Select newest non-yanked version matching requirement prefix."""
    prefix = re.sub(r"[^0-9.]", "", requirement.split(",")[0])
    versions: List[str] = []
    for line in raw_index_lines.strip().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if not record.get("yanked", False):
            versions.append(record.get("vers", ""))

    if not versions:
        raise ValueError("No available non-yanked versions found.")

    matching = [ver for ver in versions if ver.startswith(prefix)]
    return matching[-1] if matching else versions[-1]


def parse_test_graph_line(line: str) -> tuple:
    """Parse single 'NODE: DEP1, DEP2' line from test repository."""
    if ":" not in line:
        raise ValueError(f"Invalid test repo line format: '{line}'.")
    parts = line.split(":", maxsplit=1)
    if len(parts) != KEY_VALUE_PARTS:
        raise ValueError(f"Invalid test repo entry: '{line}'.")

    node = parts[0].strip()
    if not re.match(UPPER_PACKAGE_PATTERN, node):
        raise ValueError(f"Test package must be uppercase Latin: '{node}'.")

    raw_targets = parts[1].strip()
    if not raw_targets:
        return node, []

    deps = [item.strip() for item in raw_targets.split(",") if item.strip()]
    for dep in deps:
        if not re.match(UPPER_PACKAGE_PATTERN, dep):
            raise ValueError(
                f"Test dependency must be uppercase Latin: '{dep}'."
            )
    return node, deps


def parse_test_repository_graph(raw_text: str) -> Dict[str, List[str]]:
    """Parse uppercase Latin package graph from test repository text."""
    graph: Dict[str, List[str]] = {}
    for line in raw_text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        node, deps = parse_test_graph_line(clean)
        graph[node] = deps
    return graph


def get_crate_dependencies(
    repo_target: str,
    crate_name: str,
    crate_version: str,
    test_mode: bool,
) -> List[CargoDependency]:
    """Fetch and filter direct dependencies for given crate and version."""
    if test_mode:
        raw_data = load_test_index_data(repo_target)
        if repo_target.lower().endswith(".jsonl"):
            return parse_direct_dependencies(raw_data, crate_version)
        graph = parse_test_repository_graph(raw_data)
        if crate_name not in graph:
            raise ValueError(f"Package '{crate_name}' not in test repo.")
        return [
            CargoDependency(dep, "*", False, NORMAL_DEPENDENCY_KIND)
            for dep in graph[crate_name]
        ]

    raw_data = fetch_remote_index_data(repo_target, crate_name)
    return parse_direct_dependencies(raw_data, crate_version)
