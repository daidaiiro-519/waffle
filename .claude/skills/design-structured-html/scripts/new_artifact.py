#!/usr/bin/env python3
"""Create a standalone HTML artifact from the bundled template."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a structured standalone HTML artifact."
    )
    parser.add_argument("output", type=Path, help="Destination .html path")
    parser.add_argument("--title", required=True, help="Document title")
    parser.add_argument("--lang", default="ja", help="HTML language code (default: ja)")
    parser.add_argument(
        "--eyebrow", default="Structured information artifact", help="Short document type"
    )
    parser.add_argument(
        "--summary",
        default="重要な結論から詳細へ進める、構造化された情報アーティファクトです。",
        help="One- or two-sentence lead",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    destination = args.output.expanduser().resolve()
    if destination.suffix.lower() not in {".html", ".htm"}:
        print("error: output must use .html or .htm", file=sys.stderr)
        return 2
    if destination.exists() and not args.force:
        print(f"error: {destination} already exists; pass --force to overwrite", file=sys.stderr)
        return 2

    template = Path(__file__).resolve().parents[1] / "assets" / "structured-artifact-template.html"
    if not template.is_file():
        print(f"error: template not found: {template}", file=sys.stderr)
        return 2

    replacements = {
        "{{LANG}}": args.lang,
        "{{TITLE}}": args.title,
        "{{EYEBROW}}": args.eyebrow,
        "{{SUMMARY}}": args.summary,
        "{{UPDATED}}": date.today().isoformat(),
    }
    content = template.read_text(encoding="utf-8")
    for source, target in replacements.items():
        content = content.replace(source, target)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8", newline="\n")
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
