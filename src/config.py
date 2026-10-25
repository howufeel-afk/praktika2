"""Configuration data model and input validation logic."""

from dataclasses import dataclass
from pathlib import Path
import re
import urllib.parse

CRATE_NAME_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_-]*$"
SEMVER_PATTERN = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$"
SUPPORTED_GRAPH_EXTS = (".png", ".svg", ".puml", ".txt")


@dataclass(frozen=True)
class AppConfig:
    """Application runtime configuration parameters."""

    package_name: str
    repo_url_or_path: str
    test_mode: bool
    package_version: str
    output_file: str
    filter_substring: str


def validate_package_name(name: str) -> None:
    """Validate package name conforms to Cargo crate naming rules."""
    if not name:
        raise ValueError("Package name cannot be empty.")
    if not re.match(CRATE_NAME_PATTERN, name):
        raise ValueError(f"Invalid package name format: '{name}'.")


def validate_version(version: str) -> None:
    """Validate package semantic version string."""
    if not version:
        raise ValueError("Version string cannot be empty.")
    if not re.match(SEMVER_PATTERN, version):
        raise ValueError(f"Invalid semver version format: '{version}'.")


def validate_repo_target(target: str, is_test_mode: bool) -> None:
    """Validate repository target URL or local filesystem path."""
    if not target:
        raise ValueError("Repository target cannot be empty.")
    if is_test_mode:
        path = Path(target)
        if not path.exists():
            raise ValueError(f"Test repo file not found: '{target}'.")
        return

    parsed = urllib.parse.urlparse(target)
    valid_schemes = ("http", "https", "file")
    if parsed.scheme not in valid_schemes:
        raise ValueError(f"Unsupported URL scheme in repo: '{target}'.")


def validate_output_file(output_path: str) -> None:
    """Validate destination graph file extension."""
    if not output_path:
        raise ValueError("Output file name cannot be empty.")
    if not any(
        output_path.lower().endswith(ext) for ext in SUPPORTED_GRAPH_EXTS
    ):
        allowed = ", ".join(SUPPORTED_GRAPH_EXTS)
        raise ValueError(f"Output file must have extension: {allowed}.")


def validate_config(config: AppConfig) -> None:
    """Perform validation across all configured fields."""
    validate_package_name(config.package_name)
    validate_version(config.package_version)
    validate_repo_target(config.repo_url_or_path, config.test_mode)
    validate_output_file(config.output_file)
