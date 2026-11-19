"""Tests for PlantUML generation and graph image rendering (Stage 5)."""

from pathlib import Path
import tempfile
import unittest
from src.visualizer import (
    encode_plantuml_deflate,
    generate_plantuml_text,
    render_fallback_png,
    render_fallback_svg,
    save_graph_visualization,
)


class TestGraphVisualizer(unittest.TestCase):
    """Test suite verifying PlantUML syntax and PNG/SVG export."""

    def test_plantuml_forward_and_cycle_syntax(self) -> None:
        """Verify PlantUML output contains nodes, arrows, and cycles."""
        adj = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        puml = generate_plantuml_text(adj, [("D", "A")], "A", False)
        self.assertIn("@startuml", puml)
        self.assertIn("[A] --> [B]", puml)
        self.assertIn("[D] ..> [A] #red : cycle", puml)
        self.assertIn("@enduml", puml)

    def test_plantuml_reverse_arrow_direction(self) -> None:
        """Verify reverse mode uses reverse dependency arrows."""
        adj = {"D": ["B", "C"], "B": [], "C": []}
        puml = generate_plantuml_text(adj, [], "D", True)
        self.assertIn("Reverse Dependencies: D", puml)
        self.assertIn("[D] <.. [B]", puml)

    def test_plantuml_deflate_encoding(self) -> None:
        """Ensure PlantUML deflate encoder produces non-empty token."""
        token = encode_plantuml_deflate("@startuml\n[A] --> [B]\n@enduml")
        self.assertTrue(bool(token))

    def test_fallback_png_has_valid_header(self) -> None:
        """Verify generated PNG bytes start with standard PNG signature."""
        adj = {"A": ["B"], "B": []}
        png_bytes = render_fallback_png(adj, [])
        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_save_puml_and_svg_files(self) -> None:
        """Verify save_graph_visualization writes both .puml and .svg."""
        adj = {"A": ["B"], "B": []}
        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_target = Path(tmp_dir) / "out.svg"
            puml_text, saved = save_graph_visualization(
                adj, [], "A", str(svg_target), False
            )
            self.assertEqual(saved, str(svg_target))
            self.assertTrue(svg_target.is_file())
            self.assertTrue(svg_target.with_suffix(".puml").is_file())
            self.assertIn("<svg", render_fallback_svg(adj, []))
            self.assertIn("@startuml", puml_text)


if __name__ == "__main__":
    unittest.main()
