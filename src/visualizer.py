"""PlantUML generator and pure-Python graph image exporter (Stage 5)."""

from pathlib import Path
import shutil
import struct
import subprocess
from typing import Dict, List, Tuple
import urllib.error
import urllib.request
import zlib

PLANTUML_ALPHABET = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
)
PLANTUML_SERVER_URL = "https://www.plantuml.com/plantuml"
HTTP_TIMEOUT_SECONDS = 8
RAW_DEFLATE_WBITS = -15
BIT_SHIFT_FOUR = 4
BIT_SHIFT_TWO = 2
BIT_SHIFT_SIX = 6
MASK_SIX_BITS = 0x3F
MASK_FOUR_BITS = 0x0F
MASK_TWO_BITS = 0x03
CHUNK_STEP_THREE = 3
ZERO_COORD = 0
BORDER_THICKNESS = 2
MAX_LABEL_CHARS = 14
CHAR_ADVANCE_X = 8
PIXEL_SCALE = 2
LABEL_PAD_X = 10
LABEL_PAD_Y = 12
RGB_WHITE = 255
CRC_MASK = 0xFFFFFFFF

NODE_BOX_WIDTH = 130
NODE_BOX_HEIGHT = 34
NODE_GAP_X = 40
NODE_GAP_Y = 55
CANVAS_PADDING = 40
NODES_PER_ROW = 4
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_BIT_DEPTH = 8
PNG_COLOR_TYPE_RGB = 2

GLYPH_MAP: Dict[str, List[str]] = {
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"],
    "O": ["010", "101", "101", "101", "010"],
    "P": ["110", "101", "110", "100", "100"],
    "Q": ["010", "101", "101", "111", "011"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    "-": ["000", "000", "111", "000", "000"],
    "_": ["000", "000", "000", "000", "111"],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["110", "001", "010", "100", "111"],
    "3": ["110", "001", "010", "001", "110"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "110", "001", "110"],
    "6": ["011", "100", "110", "101", "010"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["010", "101", "010", "101", "010"],
    "9": ["010", "101", "011", "001", "110"],
}


def generate_plantuml_text(
    adjacency: Dict[str, List[str]],
    cycles: List[Tuple[str, str]],
    root_name: str,
    is_reverse: bool = False,
) -> str:
    """Build PlantUML diagram source text for dependency graph."""
    mode_label = "Reverse Dependencies" if is_reverse else "Dependency Graph"
    arrow = "<.." if is_reverse else "-->"
    lines = [
        "@startuml",
        "skinparam shadowing false",
        "skinparam componentStyle rectangle",
        f"title {mode_label}: {root_name}",
    ]
    if not adjacency:
        lines.append(f'note "No nodes in graph for {root_name}" as N1')
        lines.append("@enduml")
        return "\n".join(lines) + "\n"

    for node, targets in adjacency.items():
        if not targets:
            lines.append(f"[{node}]")
            continue
        for target in targets:
            lines.append(f"[{node}] {arrow} [{target}]")

    for source, target in cycles:
        lines.append(f"[{source}] ..> [{target}] #red : cycle")

    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def encode_three_bytes(b1: int, b2: int, b3: int) -> str:
    """Encode 3 bytes into 4 PlantUML base64 characters."""
    c1 = b1 >> BIT_SHIFT_TWO
    c2 = ((b1 & MASK_TWO_BITS) << BIT_SHIFT_FOUR) | (b2 >> BIT_SHIFT_FOUR)
    c3 = ((b2 & MASK_FOUR_BITS) << BIT_SHIFT_TWO) | (b3 >> BIT_SHIFT_SIX)
    c4 = b3 & MASK_SIX_BITS
    return (
        PLANTUML_ALPHABET[c1]
        + PLANTUML_ALPHABET[c2]
        + PLANTUML_ALPHABET[c3]
        + PLANTUML_ALPHABET[c4]
    )


def encode_plantuml_deflate(plantuml_text: str) -> str:
    """Compress and encode PlantUML text for PlantUML server URLs."""
    compressor = zlib.compressobj(
        zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, RAW_DEFLATE_WBITS
    )
    raw = compressor.compress(plantuml_text.encode("utf-8"))
    raw += compressor.flush()
    encoded: List[str] = []
    for idx in range(ZERO_COORD, len(raw), CHUNK_STEP_THREE):
        b1 = raw[idx]
        b2 = raw[idx + 1] if idx + 1 < len(raw) else ZERO_COORD
        b3 = raw[idx + 2] if idx + 2 < len(raw) else ZERO_COORD
        encoded.append(encode_three_bytes(b1, b2, b3))
    return "".join(encoded)


def try_fetch_plantuml_remote(plantuml_text: str, fmt: str) -> bytes:
    """Attempt to render PlantUML diagram via official PlantUML server."""
    token = encode_plantuml_deflate(plantuml_text)
    url = f"{PLANTUML_SERVER_URL}/{fmt}/{token}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "CargoVisualizer/1.0"}
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
        return resp.read()


def try_render_local_plantuml(puml_path: Path, fmt: str) -> bool:
    """Attempt rendering using locally installed plantuml CLI if present."""
    binary = shutil.which("plantuml")
    if not binary:
        return False
    flag = "-tsvg" if fmt == "svg" else "-tpng"
    res = subprocess.run(
        [binary, flag, str(puml_path)],
        capture_output=True,
        check=False,
    )
    return res.returncode == ZERO_COORD


def compute_node_positions(
    nodes: List[str],
) -> Tuple[Dict[str, Tuple[int, int]], int, int]:
    """Compute (x, y) top-left coordinates for graph nodes in grid."""
    positions: Dict[str, Tuple[int, int]] = {}
    count = max(len(nodes), 1)
    cols = min(count, NODES_PER_ROW)
    rows = (count + NODES_PER_ROW - 1) // NODES_PER_ROW
    width = (
        CANVAS_PADDING * 2
        + cols * NODE_BOX_WIDTH
        + max(cols - 1, ZERO_COORD) * NODE_GAP_X
    )
    height = (
        CANVAS_PADDING * 2
        + rows * NODE_BOX_HEIGHT
        + max(rows - 1, ZERO_COORD) * NODE_GAP_Y
    )
    for idx, name in enumerate(nodes):
        row = idx // NODES_PER_ROW
        col = idx % NODES_PER_ROW
        x_pos = CANVAS_PADDING + col * (NODE_BOX_WIDTH + NODE_GAP_X)
        y_pos = CANVAS_PADDING + row * (NODE_BOX_HEIGHT + NODE_GAP_Y)
        positions[name] = (x_pos, y_pos)
    return positions, width, height


def build_svg_edges(
    adjacency: Dict[str, List[str]],
    cycles: List[Tuple[str, str]],
    positions: Dict[str, Tuple[int, int]],
) -> List[str]:
    """Create SVG line elements for normal and cyclic edges."""
    lines: List[str] = []
    half_w = NODE_BOX_WIDTH // 2
    for src, targets in adjacency.items():
        x1, y1 = positions[src]
        for dst in targets:
            if dst in positions:
                x2, y2 = positions[dst]
                lines.append(
                    f'<line x1="{x1 + half_w}" y1="{y1 + NODE_BOX_HEIGHT}" '
                    f'x2="{x2 + half_w}" y2="{y2}" '
                    f'stroke="#334155" stroke-width="2"/>'
                )
    for src, dst in cycles:
        if src in positions and dst in positions:
            x1, y1 = positions[src]
            x2, y2 = positions[dst]
            lines.append(
                f'<line x1="{x1 + half_w}" y1="{y1}" '
                f'x2="{x2 + half_w}" y2="{y2}" '
                f'stroke="#dc2626" stroke-dasharray="4" stroke-width="2"/>'
            )
    return lines


def render_fallback_svg(
    adjacency: Dict[str, List[str]], cycles: List[Tuple[str, str]]
) -> str:
    """Render clean standalone SVG diagram when PlantUML server is offline."""
    positions, width, height = compute_node_positions(list(adjacency.keys()))
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]
    lines.extend(build_svg_edges(adjacency, cycles, positions))
    for name, (x_pos, y_pos) in positions.items():
        lines.append(
            f'<rect x="{x_pos}" y="{y_pos}" width="{NODE_BOX_WIDTH}" '
            f'height="{NODE_BOX_HEIGHT}" rx="6" fill="#eff6ff" '
            f'stroke="#2563eb" stroke-width="2"/>'
        )
        lines.append(
            f'<text x="{x_pos + LABEL_PAD_X}" y="{y_pos + 22}" '
            f'font-family="monospace" font-size="14" fill="#1e293b">'
            f"{name}</text>"
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def draw_line_on_buffer(
    buf: bytearray,
    size: Tuple[int, int],
    p1: Tuple[int, int],
    p2: Tuple[int, int],
    color: Tuple[int, int, int],
) -> None:
    """Rasterize straight line segment onto RGB pixel buffer."""
    width, height = size
    x1, y1 = p1
    x2, y2 = p2
    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    for step in range(steps + 1):
        px = int(x1 + (x2 - x1) * step / steps)
        py = int(y1 + (y2 - y1) * step / steps)
        if ZERO_COORD <= px < width and ZERO_COORD <= py < height:
            offset = (py * width + px) * CHUNK_STEP_THREE
            buf[offset : offset + CHUNK_STEP_THREE] = bytes(color)


def draw_label_on_buffer(
    buf: bytearray,
    size: Tuple[int, int],
    origin: Tuple[int, int],
    text: str,
) -> None:
    """Draw uppercase bitmap label onto RGB pixel buffer."""
    width, height = size
    ox, oy = origin
    for char_idx, ch in enumerate(text.upper()[:MAX_LABEL_CHARS]):
        glyph = GLYPH_MAP.get(ch, GLYPH_MAP["-"])
        for row_idx, row_bits in enumerate(glyph):
            for col_idx, bit in enumerate(row_bits):
                if bit != "1":
                    continue
                px = ox + char_idx * CHAR_ADVANCE_X + col_idx * PIXEL_SCALE
                py = oy + row_idx * PIXEL_SCALE
                if (
                    ZERO_COORD <= px < width - 1
                    and ZERO_COORD <= py < height - 1
                ):
                    off = (py * width + px) * CHUNK_STEP_THREE
                    buf[off : off + CHUNK_STEP_THREE] = b"\x1e\x29\x3b"


def draw_box_on_buffer(
    buf: bytearray,
    size: Tuple[int, int],
    top_left: Tuple[int, int],
    label: str,
) -> None:
    """Draw bordered node rectangle with label onto RGB pixel buffer."""
    width, height = size
    bx, by = top_left
    for dy in range(NODE_BOX_HEIGHT):
        for dx in range(NODE_BOX_WIDTH):
            px, py = bx + dx, by + dy
            if not (ZERO_COORD <= px < width and ZERO_COORD <= py < height):
                continue
            is_border = (
                dx < BORDER_THICKNESS
                or dx >= NODE_BOX_WIDTH - BORDER_THICKNESS
                or dy < BORDER_THICKNESS
                or dy >= NODE_BOX_HEIGHT - BORDER_THICKNESS
            )
            rgb = b"\x25\x63\xeb" if is_border else b"\xef\xf6\xff"
            off = (py * width + px) * CHUNK_STEP_THREE
            buf[off : off + CHUNK_STEP_THREE] = rgb
    text_pos = (bx + LABEL_PAD_X, by + LABEL_PAD_Y)
    draw_label_on_buffer(buf, size, text_pos, label)


def pack_png_chunk(tag: bytes, data: bytes) -> bytes:
    """Create binary PNG chunk with length prefix and CRC32 checksum."""
    crc = zlib.crc32(tag + data) & CRC_MASK
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def encode_rgb_buffer_to_png(buf: bytearray, width: int, height: int) -> bytes:
    """Encode raw RGB pixel buffer into valid PNG binary bytes."""
    raw_rows = bytearray()
    stride = width * CHUNK_STEP_THREE
    for row in range(height):
        raw_rows.append(ZERO_COORD)
        raw_rows.extend(buf[row * stride : (row + 1) * stride])

    ihdr = struct.pack(
        ">IIBBBBB",
        width,
        height,
        PNG_BIT_DEPTH,
        PNG_COLOR_TYPE_RGB,
        ZERO_COORD,
        ZERO_COORD,
        ZERO_COORD,
    )
    return (
        PNG_SIGNATURE
        + pack_png_chunk(b"IHDR", ihdr)
        + pack_png_chunk(b"IDAT", zlib.compress(bytes(raw_rows)))
        + pack_png_chunk(b"IEND", b"")
    )


def render_fallback_png(
    adjacency: Dict[str, List[str]], cycles: List[Tuple[str, str]]
) -> bytes:
    """Render standalone binary PNG diagram using only standard library."""
    positions, width, height = compute_node_positions(list(adjacency.keys()))
    size = (width, height)
    buf = bytearray([RGB_WHITE] * (width * height * CHUNK_STEP_THREE))
    half_w = NODE_BOX_WIDTH // 2
    for src, targets in adjacency.items():
        x1, y1 = positions[src]
        for dst in targets:
            if dst in positions:
                x2, y2 = positions[dst]
                p1 = (x1 + half_w, y1 + NODE_BOX_HEIGHT)
                p2 = (x2 + half_w, y2)
                draw_line_on_buffer(buf, size, p1, p2, (51, 65, 85))
    for src, dst in cycles:
        if src in positions and dst in positions:
            x1, y1 = positions[src]
            x2, y2 = positions[dst]
            draw_line_on_buffer(
                buf, size, (x1 + half_w, y1), (x2 + half_w, y2), (220, 38, 38)
            )
    for name, pos in positions.items():
        draw_box_on_buffer(buf, size, pos, name)
    return encode_rgb_buffer_to_png(buf, width, height)


def save_graph_visualization(
    adjacency: Dict[str, List[str]],
    cycles: List[Tuple[str, str]],
    root_name: str,
    output_file: str,
    is_reverse: bool = False,
) -> Tuple[str, str]:
    """Generate PlantUML source and export requested output image file."""
    puml_text = generate_plantuml_text(
        adjacency, cycles, root_name, is_reverse
    )
    out_path = Path(output_file)
    puml_path = out_path.with_suffix(".puml")
    puml_path.write_text(puml_text, encoding="utf-8")

    suffix = out_path.suffix.lower()
    if suffix in (".puml", ".txt"):
        out_path.write_text(puml_text, encoding="utf-8")
        return puml_text, str(out_path)

    fmt = "svg" if suffix == ".svg" else "png"
    if try_render_local_plantuml(puml_path, fmt):
        return puml_text, str(out_path)

    try:
        rendered_bytes = try_fetch_plantuml_remote(puml_text, fmt)
        out_path.write_bytes(rendered_bytes)
        return puml_text, str(out_path)
    except (urllib.error.URLError, TimeoutError, OSError):
        if fmt == "svg":
            out_path.write_text(
                render_fallback_svg(adjacency, cycles), encoding="utf-8"
            )
        else:
            out_path.write_bytes(render_fallback_png(adjacency, cycles))
        return puml_text, str(out_path)
