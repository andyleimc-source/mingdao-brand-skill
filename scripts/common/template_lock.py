#!/usr/bin/env python3
"""Validate that a generated HTML only changes its HAP_LIVE_DATA object."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path


DATA_PATTERN = re.compile(
    r"(?P<prefix>const\s+HAP_LIVE_DATA\s*=\s*)\{.*?\}(?P<suffix>\s*;)",
    re.DOTALL,
)
DATA_SENTINEL = r"\g<prefix>{/* TEMPLATE_DATA */}\g<suffix>"
TIME_BLOCK_PATTERN = re.compile(
    r'<div\s+class="live-meta">\s*'
    r'<p\s+class="meta-label">直播时间</p>\s*'
    r'<p\s+class="date-value"\s+data-bind="date">.*?</p>\s*'
    r'<p\s+class="weekday-value"\s+data-bind="weekday">.*?</p>\s*'
    r'<p\s+class="time-row"\s+data-bind="time">.*?</p>\s*'
    r'</div>',
    re.DOTALL,
)
DEFAULT_TIME_PATTERN = re.compile(
    r'<p\s+class="time-row"\s+data-bind="time">\d{2}:\d{2}-\d{2}:\d{2}</p>'
)
REQUIRED_LAYOUT_RULES = (
    '.live-meta { right: 124px; top: 983px; z-index: 3; width: 162px; height: 116px; }',
    '.live-meta .date-value { left: 0; top: 34px; width: 75px; height: 58px;',
    'width: 72px; height: 58px; color: var(--white); font-size: 24px; line-height: 58px; font-weight: 400; text-align: right;',
    '.live-meta .time-row { left: 0; top: 74px; width: 162px; height: 42px;',
    'String(rawValue).replace(/[—–−]/g, "-")',
)


def normalize(html: str, source: Path) -> str:
    if not TIME_BLOCK_PATTERN.search(html):
        raise ValueError(
            f"{source}: live-meta must use four independently positioned Figma text nodes"
        )
    if not DEFAULT_TIME_PATTERN.search(html):
        raise ValueError(
            f"{source}: vertical time must use an ASCII hyphen so its ink stays within 162px"
        )
    for rule in REQUIRED_LAYOUT_RULES:
        if rule not in html:
            raise ValueError(f"{source}: missing locked live-meta rule: {rule}")
    normalized, count = DATA_PATTERN.subn(DATA_SENTINEL, html, count=1)
    if count != 1:
        raise ValueError(f"{source}: expected exactly one HAP_LIVE_DATA object")
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure an HAP live output preserves all template structure and styles."
    )
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        template = normalize(args.template.read_text(encoding="utf-8"), args.template)
        output = normalize(args.output.read_text(encoding="utf-8"), args.output)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if template == output:
        print("OK: template structure unchanged")
        return 0

    print(
        "ERROR: output changed locked template structure or styles; "
        "only HAP_LIVE_DATA may differ",
        file=sys.stderr,
    )
    diff = difflib.unified_diff(
        template.splitlines(),
        output.splitlines(),
        fromfile=str(args.template),
        tofile=str(args.output),
        lineterm="",
        n=2,
    )
    for line in list(diff)[:80]:
        print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
