#!/usr/bin/env python3
"""Run lightweight structural checks on a standalone HTML artifact."""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse


class ArtifactParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: Counter[str] = Counter()
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.headings: list[tuple[int, str]] = []
        self._heading_level: int | None = None
        self._heading_parts: list[str] = []
        self._in_title = False
        self._title_parts: list[str] = []
        self._in_style = False
        self._style_parts: list[str] = []
        self.html_lang: str | None = None
        self.has_charset = False
        self.has_viewport = False
        self.images_without_alt: list[str] = []
        self.buttons_without_label = 0
        self.buttons_without_type = 0
        self._button_stack: list[dict[str, object]] = []
        self.table_stack: list[dict[str, bool]] = []
        self.tables: list[dict[str, bool]] = []
        self.external_assets: list[str] = []

    @staticmethod
    def attrs_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.tags[tag] += 1
        data = self.attrs_dict(attrs)
        if tag == "html":
            self.html_lang = data.get("lang") or None
        if "id" in data:
            self.ids.append(data["id"])
        if tag == "a":
            href = data.get("href", "")
            if href.startswith("#") and len(href) > 1:
                self.fragments.append(href[1:])
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_level = int(tag[1])
            self._heading_parts = []
        if tag == "title":
            self._in_title = True
        if tag == "style":
            self._in_style = True
        if tag == "meta":
            if "charset" in data:
                self.has_charset = True
            if data.get("name", "").lower() == "viewport":
                self.has_viewport = True
        if tag == "img" and "alt" not in data:
            self.images_without_alt.append(data.get("src", "<unknown>"))
        if tag == "button":
            state: dict[str, object] = {
                "has_label": bool(data.get("aria-label") or data.get("title")),
                "has_type": bool(data.get("type")),
                "text": [],
            }
            self._button_stack.append(state)
        if tag == "table":
            self.table_stack.append({"caption": False, "th": False})
        elif self.table_stack and tag == "caption":
            self.table_stack[-1]["caption"] = True
        elif self.table_stack and tag == "th":
            self.table_stack[-1]["th"] = True
        for attribute in ("src", "href"):
            value = data.get(attribute, "")
            parsed = urlparse(value)
            if parsed.scheme in {"http", "https"} and tag in {"script", "link", "img", "source"}:
                self.external_assets.append(value)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._heading_level is not None and tag == f"h{self._heading_level}":
            text = " ".join("".join(self._heading_parts).split())
            self.headings.append((self._heading_level, text))
            self._heading_level = None
            self._heading_parts = []
        if tag == "title":
            self._in_title = False
        if tag == "style":
            self._in_style = False
        if tag == "button" and self._button_stack:
            state = self._button_stack.pop()
            label = " ".join("".join(state["text"]).split())  # type: ignore[index]
            if not state["has_label"] and not label:
                self.buttons_without_label += 1
            if not state["has_type"]:
                self.buttons_without_type += 1
        if tag == "table" and self.table_stack:
            self.tables.append(self.table_stack.pop())

    def handle_data(self, data: str) -> None:
        if self._heading_level is not None:
            self._heading_parts.append(data)
        if self._in_title:
            self._title_parts.append(data)
        if self._in_style:
            self._style_parts.append(data)
        if self._button_stack:
            self._button_stack[-1]["text"].append(data)  # type: ignore[index, union-attr]

    @property
    def title(self) -> str:
        return " ".join("".join(self._title_parts).split())

    @property
    def css(self) -> str:
        return "\n".join(self._style_parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a structured HTML artifact")
    parser.add_argument("html", type=Path, help="HTML file to validate")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args()


def validate(path: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {"file": str(path), "errors": ["file does not exist"], "warnings": []}

    text = path.read_text(encoding="utf-8")
    parser = ArtifactParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # HTMLParser errors are rare, preserve diagnostic.
        errors.append(f"HTML parsing failed: {exc}")

    if not re.match(r"\s*<!doctype\s+html", text, flags=re.IGNORECASE):
        errors.append("missing <!doctype html>")
    if not parser.html_lang:
        errors.append("missing html[lang]")
    if not parser.has_charset:
        errors.append("missing meta charset")
    if not parser.has_viewport:
        errors.append("missing viewport meta")
    if not parser.title:
        errors.append("missing non-empty title")
    if parser.tags["main"] != 1:
        errors.append(f"expected exactly one <main>, found {parser.tags['main']}")
    if parser.tags["h1"] != 1:
        errors.append(f"expected exactly one <h1>, found {parser.tags['h1']}")

    duplicate_ids = sorted(key for key, count in Counter(parser.ids).items() if count > 1)
    if duplicate_ids:
        errors.append("duplicate ids: " + ", ".join(duplicate_ids))
    missing_fragments = sorted(set(parser.fragments) - set(parser.ids))
    if missing_fragments:
        errors.append("broken fragment links: " + ", ".join(f"#{x}" for x in missing_fragments))

    previous_level: int | None = None
    for level, heading in parser.headings:
        if previous_level is not None and level > previous_level + 1:
            warnings.append(
                f"heading level jumps from h{previous_level} to h{level}: {heading or '<empty>'}"
            )
        previous_level = level
        if not heading:
            warnings.append(f"empty h{level}")

    if parser.images_without_alt:
        errors.append("images missing alt: " + ", ".join(parser.images_without_alt))
    if parser.buttons_without_label:
        errors.append(f"buttons without accessible label: {parser.buttons_without_label}")
    if parser.buttons_without_type:
        warnings.append(f"buttons without explicit type: {parser.buttons_without_type}")
    for index, table in enumerate(parser.tables, start=1):
        if not table["caption"]:
            warnings.append(f"table {index} has no caption")
        if not table["th"]:
            errors.append(f"table {index} has no header cells")

    if parser.external_assets:
        warnings.append("external assets reduce portability: " + ", ".join(parser.external_assets))
    if "@media print" not in parser.css:
        warnings.append("no print stylesheet detected")
    if not re.search(r"@media\s*\([^)]*max-width", parser.css):
        warnings.append("no responsive max-width media query detected")
    if "prefers-color-scheme" not in parser.css and "data-theme" not in parser.css:
        warnings.append("no dark/theme styling detected")
    if re.search(r"\{\{[A-Z0-9_-]+\}\}", text):
        warnings.append("unresolved template placeholders remain")

    return {
        "file": str(path.resolve()),
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "sections": parser.tags["section"],
            "headings": len(parser.headings),
            "tables": len(parser.tables),
            "unique_ids": len(set(parser.ids)),
        },
    }


def main() -> int:
    args = parse_args()
    result = validate(args.html.expanduser())
    errors = result["errors"]
    warnings = result["warnings"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Validated: {result['file']}")
        for message in errors:
            print(f"ERROR: {message}")
        for message in warnings:
            print(f"WARN:  {message}")
        summary = result.get("summary")
        if summary:
            print("Summary: " + ", ".join(f"{k}={v}" for k, v in summary.items()))
        if not errors and not warnings:
            print("OK: no structural issues found")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
