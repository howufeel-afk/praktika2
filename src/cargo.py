"""Cargo package dependency fetcher and parser using standard library."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import List
import urllib.error
import urllib.request

HTTP_USER_AGENT = "CargoVisualizer/1.0 (StudentProject)"
HTTP_TIMEOUT_SECONDS = 15
NORMAL_DEPENDENCY_KIND = "normal"
CRATE_MIN_LEN_ONE = 1
CRATE_MIN_LEN_TWO = 2
CRATE_MIN_LEN_THREE = 3


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
    """Load mock repository JSON lines from local file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Mock file not found: {file_path}")
    return path.read_text(encoding="utf-8")


def parse_direct_dependencies(
    raw_index_lines: str, target_version: str
) -> List[CargoDependency]:
    """Parse JSON lines and return dependencies for matching version."""
    dependencies: List[CargoDependency] = []
    version_matched = False

    for line in raw_index_lines.strip().splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        record = json.loads(line_clean)
        if record.get("vers") == target_version:
            version_matched = True
            for item in record.get("deps", []):
                dependencies.append(
                    CargoDependency(
                        name=item.get("name", ""),
                        requirement=item.get("req", "*"),
                        optional=item.get("optional", False),
                        kind=item.get("kind", NORMAL_DEPENDENCY_KIND),
                    )
                )
            break

    if not version_matched:
        raise ValueError(f"Version '{target_version}' not found in index.")

    return [
        dep for dep in dependencies
        if dep.kind == NORMAL_DEPENDENCY_KIND and not dep.optional
    ]


def get_crate_dependencies(
    repo_target: str,
    crate_name: str,
    crate_version: str,
    test_mode: bool,
) -> List[CargoDependency]:
    """Fetch and filter direct dependencies for given crate and version."""
    if test_mode:
        raw_data = load_test_index_data(repo_target)
    else:
        raw_data = fetch_remote_index_data(repo_target, crate_name)

    return parse_direct_dependencies(raw_data, crate_version)
