#!/usr/bin/env python3
"""Verify and embed brand font assets in standalone HTML artifacts."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = SKILL_ROOT / "assets" / "common" / "fonts" / "nocoly"
SOURCE_FILE = FONT_DIR / "SOURCE.json"
START_MARKER = "<!-- nocoly-fonts:start -->"
END_MARKER = "<!-- nocoly-fonts:end -->"
REMOTE_FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com", "rsms.me/inter")

HTML_LANG_RE = re.compile(
    r"<html\b[^>]*\blang\s*=\s*(['\"])([^'\"]+)\1", re.IGNORECASE
)
LANG_RE = re.compile(r"\blang\s*=\s*(['\"])([^'\"]+)\1", re.IGNORECASE)
EMBEDDED_ASSET_RE = re.compile(
    r"/\*\s*nocoly-font-asset:\s*([^;]+);\s*sha256=([0-9a-f]{64})\s*\*/\s*"
    r"@font-face\s*\{.*?src:\s*url\(\"data:([^;]+);base64,([^\"]+)\"\).*?\}",
    re.DOTALL,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_source() -> dict:
    if not SOURCE_FILE.is_file():
        raise RuntimeError(f"missing font source manifest: {SOURCE_FILE}")
    return json.loads(SOURCE_FILE.read_text(encoding="utf-8"))


def expected_assets(source: dict) -> dict[str, str]:
    assets = {
        item["file"]: item["sha256"] for item in source["fonts"].values()
    }
    assets.update(source.get("files", {}))
    return assets


def verify_assets(source: dict) -> None:
    errors: list[str] = []
    for filename, expected in expected_assets(source).items():
        path = FONT_DIR / filename
        if not path.is_file():
            errors.append(f"missing: {path}")
            continue
        actual = sha256(path)
        if actual != expected:
            errors.append(f"checksum mismatch: {filename} ({actual})")
    if errors:
        raise RuntimeError("font asset verification failed:\n- " + "\n- ".join(errors))


def canonical_language(raw: str) -> str | None:
    normalized = raw.strip().replace("_", "-").lower()
    if normalized.startswith(("zh-hk", "zh-mo")):
        return "zh-HK"
    if normalized.startswith(("zh-tw", "zh-hant")):
        return "zh-TW"
    if normalized.startswith(("zh-cn", "zh-sg", "zh-hans")):
        return "zh-CN"
    if normalized.startswith("ja"):
        return "ja"
    if normalized.startswith("ko"):
        return "ko"
    if normalized.startswith("en"):
        return "en"
    return None


def languages_in_html(html: str, override: str | None = None) -> tuple[str, list[str]]:
    root_match = HTML_LANG_RE.search(html)
    root_raw = override or (root_match.group(2) if root_match else "")
    root = canonical_language(root_raw)
    if root is None:
        raise RuntimeError(
            "Nocoly HTML must declare a supported <html lang>: en, zh-CN, zh-TW, "
            "zh-HK, ja, or ko (or pass --lang)."
        )

    discovered = [root]
    for match in LANG_RE.finditer(html):
        language = canonical_language(match.group(2))
        if language and language not in discovered:
            discovered.append(language)
    return root, discovered


def font_keys(languages: list[str]) -> list[str]:
    return ["inter", *(language for language in languages if language != "en")]


def face_css(item: dict) -> str:
    encoded = base64.b64encode((FONT_DIR / item["file"]).read_bytes()).decode("ascii")
    return (
        f'/* nocoly-font-asset: {item["file"]}; sha256={item["sha256"]} */\n'
        "@font-face{"
        f'font-family:"{item["family"]}";'
        f'src:url("data:{item["mime"]};base64,{encoded}") format("{item["format"]}");'
        "font-style:normal;font-weight:100 900;font-display:block;}"
    )


def style_block(source: dict, root: str, languages: list[str]) -> str:
    fonts = source["fonts"]
    faces = "\n".join(face_css(fonts[key]) for key in font_keys(languages))
    root_family = fonts["inter"]["family"] if root == "en" else fonts[root]["family"]
    selectors: list[str] = []
    for language in languages:
        if language == "en":
            family = fonts["inter"]["family"]
            selector = '[lang|="en"]'
        else:
            family = fonts[language]["family"]
            selector = f'[lang|="{language}"]'
        selectors.append(f'{selector}{{font-family:"{family}",sans-serif;}}')

    data_languages = ",".join(languages)
    return (
        f"{START_MARKER}\n"
        f'<style id="nocoly-fonts" data-brand-fonts="nocoly" data-font-langs="{data_languages}">\n'
        f"{faces}\n"
        ':root{--font-sans-latin:"Inter",sans-serif;'
        f'--font-sans-cjk:"{root_family}",sans-serif;}}\n'
        f'html{{font-synthesis:none;}}html body{{font-family:"{root_family}",sans-serif;}}\n'
        + "\n".join(selectors)
        + f"\n</style>\n{END_MARKER}"
    )


def remove_existing_block(html: str) -> str:
    pattern = re.compile(
        r"\s*"
        + re.escape(START_MARKER)
        + r".*?"
        + re.escape(END_MARKER)
        + r"\s*(?=</head\s*>)",
        re.DOTALL | re.IGNORECASE,
    )
    return pattern.sub("", html)


def write_atomic(path: Path, content: str) -> None:
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.chmod(mode)
    temp_path.replace(path)


def embed_html(input_path: Path, output_path: Path, lang: str | None) -> None:
    source = load_source()
    verify_assets(source)
    html = input_path.read_text(encoding="utf-8")
    root, languages = languages_in_html(html, lang)
    if any(host in html for host in REMOTE_FONT_HOSTS):
        raise RuntimeError(
            "remote font URL found; remove Google Fonts/Inter CDN references before embedding"
        )
    html = remove_existing_block(html)
    head_close = re.search(r"</head\s*>", html, re.IGNORECASE)
    if not head_close:
        raise RuntimeError("HTML has no </head> tag")
    block = style_block(source, root, languages)
    html = html[: head_close.start()] + block + "\n" + html[head_close.start() :]
    write_atomic(output_path, html)
    print(f"OK: embedded Nocoly fonts ({', '.join(font_keys(languages))}) -> {output_path}")


def validate_html(path: Path, lang: str | None) -> None:
    source = load_source()
    verify_assets(source)
    html = path.read_text(encoding="utf-8")
    _, languages = languages_in_html(html, lang)
    errors: list[str] = []

    if START_MARKER not in html or END_MARKER not in html:
        errors.append("missing Nocoly font embed block")
    for host in REMOTE_FONT_HOSTS:
        if host in html:
            errors.append(f"remote font host found: {host}")
    if "font-synthesis:none" not in html.replace(" ", ""):
        errors.append("font-synthesis:none is missing")

    embedded: dict[str, tuple[str, str, str]] = {}
    for match in EMBEDDED_ASSET_RE.finditer(html):
        filename, declared_hash, mime, encoded = match.groups()
        try:
            payload = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            errors.append(f"invalid base64 font payload: {filename}")
            continue
        embedded[filename.strip()] = (
            declared_hash,
            hashlib.sha256(payload).hexdigest(),
            mime,
        )

    for key in font_keys(languages):
        item = source["fonts"][key]
        record = embedded.get(item["file"])
        if not record:
            errors.append(f'missing embedded font: {item["file"]}')
            continue
        declared_hash, actual_hash, mime = record
        if declared_hash != item["sha256"] or actual_hash != item["sha256"]:
            errors.append(f'embedded checksum mismatch: {item["file"]}')
        if mime != item["mime"]:
            errors.append(f'embedded MIME mismatch: {item["file"]}')

    if errors:
        raise RuntimeError("Nocoly HTML font validation failed:\n- " + "\n- ".join(errors))
    print(f"OK: validated embedded Nocoly fonts -> {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify-assets", help="verify bundled font checksums")

    embed = subparsers.add_parser("embed-html", help="embed fonts into standalone HTML")
    embed.add_argument("input", type=Path)
    embed.add_argument("--output", type=Path, help="output path; defaults to in-place")
    embed.add_argument("--lang", help="override the root document language")

    validate = subparsers.add_parser("validate-html", help="validate embedded HTML fonts")
    validate.add_argument("input", type=Path)
    validate.add_argument("--lang", help="override the root document language")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "verify-assets":
            source = load_source()
            verify_assets(source)
            print(f"OK: verified {len(expected_assets(source))} Nocoly font assets")
        elif args.command == "embed-html":
            embed_html(args.input, args.output or args.input, args.lang)
        elif args.command == "validate-html":
            validate_html(args.input, args.lang)
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
