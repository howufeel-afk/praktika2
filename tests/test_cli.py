"""Tests for CLI parsing and parameter validation logic."""

import unittest
from src.cli import parse_arguments


class TestCliConfiguration(unittest.TestCase):
    """Test suite for validating CLI inputs and error handling."""

    def test_valid_minimal_cli_arguments(self) -> None:
        """Ensure standard valid CLI parameters parse successfully."""
        args = [
            "--package", "serde",
            "--version", "1.0.104",
            "--repo", "https://index.crates.io",
            "--output", "deps.png",
        ]
        cfg = parse_arguments(args)
        self.assertEqual(cfg.package_name, "serde")
        self.assertEqual(cfg.package_version, "1.0.104")
        self.assertFalse(cfg.test_mode)

    def test_invalid_package_name_format(self) -> None:
        """Reject illegal characters in package name."""
        args = ["--package", "123!bad", "--version", "1.0.0"]
        with self.assertRaises(ValueError):
            parse_arguments(args)

    def test_invalid_version_semver_format(self) -> None:
        """Reject non-semver version strings."""
        args = ["--package", "tokio", "--version", "latest"]
        with self.assertRaises(ValueError):
            parse_arguments(args)

    def test_invalid_repo_url_scheme(self) -> None:
        """Reject repository targets with invalid schemes."""
        args = [
            "--package", "tokio",
            "--version", "1.0.0",
            "--repo", "ftp://invalid-cargo-index.org",
        ]
        with self.assertRaises(ValueError):
            parse_arguments(args)

    def test_test_mode_missing_file(self) -> None:
        """Reject test-mode path pointing to non-existent file."""
        args = [
            "--package", "tokio",
            "--version", "1.0.0",
            "--test-mode",
            "--repo", "non_existent_mock_index.jsonl",
        ]
        with self.assertRaises(ValueError):
            parse_arguments(args)

    def test_invalid_output_extension(self) -> None:
        """Reject unsupported output graphic file extension."""
        args = [
            "--package", "tokio",
            "--version", "1.0.0",
            "--output", "graph.exe",
        ]
        with self.assertRaises(ValueError):
            parse_arguments(args)


if __name__ == "__main__":
    unittest.main()
