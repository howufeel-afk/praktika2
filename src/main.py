"""Entrypoint integrating Stage 1 and Stage 2 workflows."""

import sys
from src.cargo import get_crate_dependencies
from src.cli import parse_arguments, print_config_key_value

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def run_cli_pipeline() -> int:
    """Execute argument parsing and direct dependency extraction."""
    try:
        config = parse_arguments(sys.argv[1:])
    except Exception as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return EXIT_FAILURE

    print_config_key_value(config)

    print("\n=== Direct Dependencies (Stage 2) ===")
    try:
        direct_deps = get_crate_dependencies(
            repo_target=config.repo_url_or_path,
            crate_name=config.package_name,
            crate_version=config.package_version,
            test_mode=config.test_mode,
        )
    except Exception as error:
        print(f"Dependency retrieval error: {error}", file=sys.stderr)
        return EXIT_FAILURE

    if not direct_deps:
        print(f"Package '{config.package_name}' has no direct dependencies.")
        return EXIT_SUCCESS

    for dep in direct_deps:
        print(f"- {dep.name} ({dep.requirement})")

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(run_cli_pipeline())
