#!/usr/bin/env python3
"""Search, render, and validate the bundled Material Symbols Outlined snapshot."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable


SKILL_ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = SKILL_ROOT / "assets" / "common" / "icons" / "material-symbols"
CODEPOINTS_PATH = ASSET_DIR / "codepoints.txt"
TTF_PATH = ASSET_DIR / "MaterialSymbolsOutlined.ttf"
SOURCE_PATH = ASSET_DIR / "SOURCE.json"

TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".htm",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".ts",
    ".tsx",
}

FORBIDDEN_PATTERNS = {
    "Google Fonts Material Symbols CDN": re.compile(
        r"fonts\.(?:googleapis|gstatic)\.com[^\n\"']*material[+\s_-]*symbols",
        re.IGNORECASE,
    ),
    "legacy Material Icons": re.compile(
        r"\bmaterial-icons\b|\bMaterial\s+Icons\b", re.IGNORECASE
    ),
    "Lucide": re.compile(r"\blucide(?:-react|-vue|-icons)?\b", re.IGNORECASE),
    "Font Awesome": re.compile(
        r"\bfont[ -]?awesome\b|\bfa-(?:solid|regular|brands)\b", re.IGNORECASE
    ),
    "Heroicons": re.compile(r"\bheroicons?\b", re.IGNORECASE),
    "Iconify": re.compile(r"\biconify\b", re.IGNORECASE),
    "Bootstrap Icons": re.compile(r"\bbootstrap-icons?\b", re.IGNORECASE),
    "Feather Icons": re.compile(r"\bfeather-icons?\b", re.IGNORECASE),
    "Phosphor Icons": re.compile(r"\bphosphor-icons?\b", re.IGNORECASE),
    "inline hand-drawn SVG icon": re.compile(
        r"""class\s*=\s*["'][^"']*\bicon\b[^"']*["'][^>]*>
            [\s\S]{0,300}?<svg\b""",
        re.IGNORECASE | re.VERBOSE,
    ),
}

ICON_REFERENCE_PATTERNS = (
    re.compile(
        r"""data-material-symbol\s*=\s*["']([a-z0-9_]+)["']""",
        re.IGNORECASE,
    ),
    re.compile(
        r"""class\s*=\s*["'][^"']*\bmaterial-symbols-outlined\b[^"']*["'][^>]*>
            \s*([a-z0-9_]+)\s*</""",
        re.IGNORECASE | re.VERBOSE,
    ),
    re.compile(
        r"""\b(?:materialSymbol|renderMaterialSymbol|material_symbol|render_material_symbol)
            \s*\(\s*["']([a-z0-9_]+)["']""",
        re.IGNORECASE | re.VERBOSE,
    ),
    re.compile(r"""ms-outlined__([a-z0-9_]+)__""", re.IGNORECASE),
)

RENDERED_NAME_RE = re.compile(
    r"^ms-outlined__(?P<name>[a-z0-9_]+)__"
    r"f(?P<fill>[01])-w(?P<weight>\d+)-"
    r"g(?P<grade>n?\d+)-o(?P<optical>\d+)-s(?P<size>\d+)\.png$"
)


def load_codepoints() -> dict[str, int]:
    if not CODEPOINTS_PATH.is_file():
        raise RuntimeError(f"Missing codepoints file: {CODEPOINTS_PATH}")

    icons: dict[str, int] = {}
    for line_number, raw_line in enumerate(
        CODEPOINTS_PATH.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            raise RuntimeError(
                f"Malformed codepoints line {line_number}: {raw_line!r}"
            )
        name, value = parts
        if name in icons:
            raise RuntimeError(f"Duplicate icon name in codepoints: {name}")
        try:
            icons[name] = int(value, 16)
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid codepoint on line {line_number}: {value!r}"
            ) from exc
    return icons


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_assets() -> list[str]:
    errors: list[str] = []
    try:
        source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Cannot read {SOURCE_PATH}: {exc}"]

    for filename, expected_digest in source.get("files", {}).items():
        path = ASSET_DIR / filename
        if not path.is_file():
            errors.append(f"Missing asset: {path}")
            continue
        actual_digest = sha256(path)
        if actual_digest != expected_digest:
            errors.append(
                f"Checksum mismatch: {path} "
                f"(expected {expected_digest}, got {actual_digest})"
            )

    try:
        icons = load_codepoints()
    except RuntimeError as exc:
        errors.append(str(exc))
    else:
        if not icons:
            errors.append("The codepoints allowlist is empty")

    return errors


def normalize_query(parts: Iterable[str]) -> str:
    return "_".join(" ".join(parts).strip().lower().replace("-", "_").split())


def search_icons(query: str, icons: dict[str, int], limit: int) -> list[tuple[float, str]]:
    query_tokens = [token for token in query.split("_") if token]
    results: list[tuple[float, str]] = []
    for name in icons:
        if name == query:
            score = 10.0
        elif query in name:
            score = 6.0 - (len(name) - len(query)) / 1000
        else:
            matched_tokens = sum(token in name.split("_") for token in query_tokens)
            token_score = matched_tokens / max(1, len(query_tokens))
            fuzzy_score = difflib.SequenceMatcher(None, query, name).ratio()
            score = token_score * 3 + fuzzy_score
        results.append((score, name))
    return sorted(results, key=lambda item: (-item[0], item[1]))[:limit]


def parse_color(value: str) -> tuple[int, int, int, int]:
    normalized = value.strip().lstrip("#")
    if len(normalized) not in {6, 8} or not re.fullmatch(
        r"[0-9a-fA-F]+", normalized
    ):
        raise ValueError("Color must be #RRGGBB or #RRGGBBAA")
    if len(normalized) == 6:
        normalized += "ff"
    return tuple(int(normalized[index : index + 2], 16) for index in range(0, 8, 2))


def render_icon(args: argparse.Namespace, icons: dict[str, int]) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
    except ImportError as exc:
        raise RuntimeError(
            "Rendering requires Pillow. Install it with: python -m pip install Pillow"
        ) from exc

    if args.name not in icons:
        raise RuntimeError(
            f"Unknown Material Symbol: {args.name!r}. "
            f"Run `python scripts/common/material_symbols.py search {args.name}` first."
        )
    if args.size < 16:
        raise RuntimeError("--size must be at least 16")
    if args.padding < 0 or args.padding * 2 >= args.size:
        raise RuntimeError("--padding must leave a positive glyph area")
    if not 100 <= args.weight <= 700:
        raise RuntimeError("--weight must be between 100 and 700")
    if not -50 <= args.grade <= 200:
        raise RuntimeError("--grade must be between -50 and 200")
    if not 20 <= args.optical_size <= 48:
        raise RuntimeError("--optical-size must be between 20 and 48")

    color = parse_color(args.color)
    glyph_size = args.size - args.padding * 2
    font = ImageFont.truetype(str(TTF_PATH), glyph_size)
    font.set_variation_by_axes(
        [args.fill, args.grade, args.optical_size, args.weight]
    )
    glyph = chr(icons[args.name])
    bbox = font.getbbox(glyph)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    if width <= 0 or height <= 0:
        raise RuntimeError(f"Font returned an empty glyph for {args.name!r}")

    # 先画到超大临时画布，再按「实际墨迹」重新居中。
    # font.getbbox() 返回的是含 ascent/bearing 的布局包围盒，不等于墨迹范围：
    # 扁平字形（如 key）用它定位会整体偏上 10% 以上，且每个字形偏移量不同，
    # 一组图标摆进同尺寸容器时就会高低不齐。这里改为按渲染后的 alpha 通道定位。
    scratch = args.size * 2
    tmp = Image.new("RGBA", (scratch, scratch), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text(
        (scratch // 4, scratch // 4), glyph, font=font, fill=color
    )
    ink = tmp.getchannel("A").getbbox()
    if ink is None:
        raise RuntimeError(f"Font rendered no ink for {args.name!r}")
    ink_w, ink_h = ink[2] - ink[0], ink[3] - ink[1]
    if ink_w > glyph_size or ink_h > glyph_size:
        raise RuntimeError(
            f"Glyph ink {ink_w}×{ink_h}px exceeds the padded glyph area "
            f"({glyph_size}px) for {args.name!r}; raise --size or lower --padding."
        )

    image = Image.new("RGBA", (args.size, args.size), (0, 0, 0, 0))
    ink_x = round((args.size - ink_w) / 2)
    ink_y = round((args.size - ink_h) / 2)
    image.paste(tmp.crop(ink), (ink_x, ink_y))

    grade_label = f"n{abs(args.grade)}" if args.grade < 0 else str(args.grade)
    # 颜色进文件名，否则同一图标渲染多种颜色会静默互相覆盖。
    # 默认色不加后缀，保持既有文件名与工程引用向后兼容。
    color_suffix = ""
    if args.color.strip().lower() not in ("#1677ff", "1677ff"):
        color_suffix = "-c" + "".join(f"{c:02X}" for c in color[:3])
    output_name = (
        f"ms-outlined__{args.name}__f{args.fill}-w{args.weight}-"
        f"g{grade_label}-o{args.optical_size}-s{args.size}{color_suffix}.png"
    )
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Material-Symbol-Name", args.name)
    metadata.add_text("Material-Symbol-Style", "Outlined")
    metadata.add_text("Material-Symbol-Fill", str(args.fill))
    metadata.add_text("Material-Symbol-Weight", str(args.weight))
    metadata.add_text("Material-Symbol-Grade", str(args.grade))
    metadata.add_text("Material-Symbol-Optical-Size", str(args.optical_size))
    # 墨迹盒（居中后的实际占位），供排版侧核对与精确定位
    metadata.add_text(
        "Material-Symbol-Ink-Box",
        f"{ink_x},{ink_y},{ink_x + ink_w},{ink_y + ink_h}",
    )
    metadata.add_text(
        "Material-Symbol-Revision",
        json.loads(SOURCE_PATH.read_text(encoding="utf-8"))["revision"],
    )
    image.save(output_path, pnginfo=metadata, optimize=True)
    return output_path


def iter_targets(paths: Iterable[str]) -> Iterable[Path]:
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and (
                    child.suffix.lower() in TEXT_EXTENSIONS
                    or child.suffix.lower() in {".png", ".pptx"}
                ):
                    yield child
        else:
            yield path


def validate_png(
    path: Path, icons: dict[str, int], require_metadata: bool
) -> tuple[list[str], int]:
    try:
        from PIL import Image
    except ImportError as exc:
        return ([f"{path}: PNG validation requires Pillow ({exc})"], 0)

    try:
        with Image.open(path) as image:
            name = image.info.get("Material-Symbol-Name")
            style = image.info.get("Material-Symbol-Style")
    except OSError as exc:
        return ([f"{path}: cannot read PNG ({exc})"], 0)

    if not name:
        if require_metadata:
            return ([f"{path}: missing Material Symbols provenance metadata"], 0)
        return ([], 0)
    errors: list[str] = []
    if name not in icons:
        errors.append(f"{path}: unknown Material Symbol metadata name {name!r}")
    if style != "Outlined":
        errors.append(f"{path}: expected Outlined style metadata, got {style!r}")
    return (errors, 1)


def validate_pptx(path: Path, icons: dict[str, int]) -> tuple[list[str], int]:
    errors: list[str] = []
    icon_count = 0
    try:
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if not member.startswith("ppt/media/") or not member.lower().endswith(
                    ".png"
                ):
                    continue
                try:
                    from PIL import Image

                    with Image.open(io.BytesIO(archive.read(member))) as image:
                        name = image.info.get("Material-Symbol-Name")
                        style = image.info.get("Material-Symbol-Style")
                except (ImportError, OSError) as exc:
                    errors.append(f"{path}:{member}: cannot inspect PNG ({exc})")
                    continue
                if not name:
                    continue
                icon_count += 1
                if name not in icons:
                    errors.append(
                        f"{path}:{member}: unknown Material Symbol {name!r}"
                    )
                if style != "Outlined":
                    errors.append(
                        f"{path}:{member}: expected Outlined style, got {style!r}"
                    )
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"{path}: cannot read PPTX ({exc})")
    return errors, icon_count


def validate_text(path: Path, icons: dict[str, int]) -> tuple[list[str], int]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ([f"{path}: cannot read text ({exc})"], 0)

    errors: list[str] = []
    for label, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(text):
            errors.append(f"{path}: forbidden icon source detected: {label}")

    names: list[str] = []
    for pattern in ICON_REFERENCE_PATTERNS:
        names.extend(match.group(1).lower() for match in pattern.finditer(text))
    unique_names = set(names)
    for name in sorted(unique_names):
        if name not in icons:
            errors.append(f"{path}: unknown Material Symbol name {name!r}")
    return errors, len(unique_names)


def validate_targets(
    raw_paths: Iterable[str], icons: dict[str, int], require_icons: bool
) -> tuple[list[str], int]:
    errors = verify_assets()
    icon_count = 0
    seen: set[Path] = set()
    for path in iter_targets(raw_paths):
        if path in seen:
            continue
        seen.add(path)
        if not path.exists():
            errors.append(f"Missing validation target: {path}")
            continue
        suffix = path.suffix.lower()
        if suffix in TEXT_EXTENSIONS:
            target_errors, count = validate_text(path, icons)
        elif suffix == ".pptx":
            target_errors, count = validate_pptx(path, icons)
        elif suffix == ".png":
            target_errors, count = validate_png(
                path, icons, require_metadata=path.name.startswith("ms-outlined__")
            )
        else:
            errors.append(f"Unsupported validation target: {path}")
            continue
        errors.extend(target_errors)
        icon_count += count

    if require_icons and icon_count == 0:
        errors.append(
            "No verifiable Material Symbols references or rendered PNG metadata found"
        )
    return errors, icon_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Use the bundled Material Symbols Outlined library deterministically."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "verify-assets", help="Verify bundled official files against SOURCE.json."
    )

    search_parser = subparsers.add_parser(
        "search", help="Search the complete bundled icon-name allowlist."
    )
    search_parser.add_argument("query", nargs="+", help="English icon keywords.")
    search_parser.add_argument("--limit", type=int, default=20)

    render_parser = subparsers.add_parser(
        "render", help="Render one approved symbol to a provenance-tagged PNG."
    )
    render_parser.add_argument("name", help="Exact Material Symbol ligature name.")
    render_parser.add_argument("--output-dir", required=True)
    render_parser.add_argument("--size", type=int, default=256)
    render_parser.add_argument("--padding", type=int, default=24)
    render_parser.add_argument("--color", default="#1677FF")
    render_parser.add_argument("--fill", type=int, choices=(0, 1), default=0)
    render_parser.add_argument("--weight", type=int, default=400)
    render_parser.add_argument("--grade", type=int, default=0)
    render_parser.add_argument("--optical-size", type=int, default=24)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Reject unapproved icon libraries and invalid Material Symbols names.",
    )
    validate_parser.add_argument("paths", nargs="+", help="Files or directories.")
    validate_parser.add_argument(
        "--require-icons",
        action="store_true",
        help="Fail unless at least one verifiable Material Symbol is present.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "verify-assets":
            errors = verify_assets()
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("OK: official Material Symbols assets match SOURCE.json")
            return 0

        icons = load_codepoints()
        if args.command == "search":
            query = normalize_query(args.query)
            if not query:
                parser.error("search query cannot be empty")
            if args.limit < 1:
                parser.error("--limit must be positive")
            for score, name in search_icons(query, icons, args.limit):
                print(f"{name}\tU+{icons[name]:04X}\t{score:.3f}")
            return 0

        if args.command == "render":
            errors = verify_assets()
            if errors:
                raise RuntimeError("; ".join(errors))
            output_path = render_icon(args, icons)
            print(output_path)
            return 0

        if args.command == "validate":
            errors, icon_count = validate_targets(
                args.paths, icons, require_icons=args.require_icons
            )
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"OK: validated {icon_count} Material Symbols reference(s)")
            return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
