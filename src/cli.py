"""Command-line interface parser and configuration printer."""

import argparse
from typing import List, Optional

from src.config import AppConfig, validate_config

DEFAULT_CARGO_INDEX_URL = "https://index.crates.io"
DEFAULT_OUTPUT_GRAPH = "graph.png"
DEFAULT_FILTER_STRING = ""


def build_cli_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser with variant 25 options."""
    parser = argparse.ArgumentParser(
        description="Cargo dependency visualizer (Variant 25)."
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Name of the analyzed Rust crate.",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_CARGO_INDEX_URL,
        help="Crates index base URL or local test repo path.",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Enable local mock test repository mode.",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Analyzed package version (e.g., 0.1.0).",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_GRAPH,
        help="Output graph file name.",
    )
    parser.add_argument(
        "--filter",
        default=DEFAULT_FILTER_STRING,
        help="Substring for filtering ignored packages.",
    )
    return parser


def parse_arguments(cli_args: Optional[List[str]] = None) -> AppConfig:
    """Parse CLI tokens into validated AppConfig object."""
    parser = build_cli_parser()
    args = parser.parse_args(cli_args)
    config = AppConfig(
        package_name=args.package,
        repo_url_or_path=args.repo,
        test_mode=args.test_mode,
        package_version=args.version,
        output_file=args.output,
        filter_substring=args.filter,
    )
    validate_config(config)
    return config


def print_config_key_value(config: AppConfig) -> None:
    """Print parsed parameters in key-value format for Stage 1."""
    print("=== Configuration Parameters ===")
    print(f"package: {config.package_name}")
    print(f"repo: {config.repo_url_or_path}")
    print(f"test_mode: {config.test_mode}")
    print(f"version: {config.package_version}")
    print(f"output: {config.output_file}")
    print(f"filter: {config.filter_substring}")
    print("================================")
