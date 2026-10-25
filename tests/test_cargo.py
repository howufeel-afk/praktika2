"""Tests for Cargo package dependency parsing logic."""

import unittest
from src.cargo import (
    compute_crate_index_subpath,
    parse_direct_dependencies,
)

SAMPLE_INDEX_DATA = (
    '{"name":"test_pkg","vers":"0.1.0","deps":['
    '{"name":"a","req":"^0.1","kind":"normal","optional":false}'
    ']}\n'
    '{"name":"test_pkg","vers":"0.2.0","deps":['
    '{"name":"b","req":"^1.0","kind":"normal","optional":false},'
    '{"name":"c","req":"^2.0","kind":"dev","optional":false},'
    '{"name":"d","req":"^0.5","kind":"normal","optional":true}'
    ']}\n'
)


class TestCargoIndexParser(unittest.TestCase):
    """Test suite for Cargo sparse index layout and parsing."""

    def test_subpath_computation_rules(self) -> None:
        """Verify subpaths according to Cargo index rules."""
        self.assertEqual(compute_crate_index_subpath("a"), "1/a")
        self.assertEqual(compute_crate_index_subpath("io"), "2/io")
        self.assertEqual(compute_crate_index_subpath("syn"), "3/s/syn")
        self.assertEqual(
            compute_crate_index_subpath("serde"), "se/rd/serde"
        )

    def test_filter_dev_and_optional_deps(self) -> None:
        """Ensure dev and optional dependencies are filtered out."""
        deps = parse_direct_dependencies(SAMPLE_INDEX_DATA, "0.2.0")
        dep_names = [dep.name for dep in deps]
        self.assertEqual(dep_names, ["b"])

    def test_version_not_found(self) -> None:
        """Raise error when requested package version does not exist."""
        with self.assertRaises(ValueError):
            parse_direct_dependencies(SAMPLE_INDEX_DATA, "9.9.9")


if __name__ == "__main__":
    unittest.main()
