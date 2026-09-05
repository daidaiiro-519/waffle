#!/usr/bin/env python3
"""Rasterize every inline <svg> in an artifact and check its layout geometry.

Hand-authored SVG coordinates cannot be trusted until something draws them.
This script produces the PNGs so the diagrams can actually be looked at, and
flags the geometry faults that are cheap to state numerically.

Dependencies are fetched per-run and nothing is installed system-wide:

    uv run --no-project --with resvg-py --with fonttools \
        python3 scripts/render_svg_check.py artifact.html --out-dir /tmp/render

Looking at the PNGs is the point. The geometry checks below only cover faults
that can be written down as a rule; anything else is found by reading the image.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

# Minimum breathing room between a shape and the frame that encloses it.
FRAME_PADDING = 6.0

# Ink extent of a glyph relative to its font size, measured from the baseline.
# Line height would overstate it and turn captions parked just outside a frame
# into false reports.
CAP_HEIGHT = 0.72
DESCENDER = 0.22

# CJK glyphs are full width; Latin averages a little over half.
CJK_START = 0x2E80


def find_fonts(extra: list[str]) -> dict[str, str]:
    """Map each available font's own family name to its file."""
    from fontTools.ttLib import TTFont

    paths = [Path(p) for p in extra]
    for root in (Path.home() / ".local/share/fonts", Path("/usr/share/fonts")):
        if root.is_dir():
            paths += [p for p in root.rglob("*") if p.suffix.lower() in (".ttf", ".otf", ".ttc")]

    families: dict[str, str] = {}
    for path in paths:
        try:
            font = TTFont(str(path), fontNumber=0, lazy=True)
            for record in font["name"].names:
                if record.nameID in (1, 16):
                    families.setdefault(record.toUnicode(), str(path))
        except Exception:
            continue
    return families


def pick_family(families: dict[str, str]) -> tuple[str, list[str]]:
    """Prefer a family with Japanese coverage, since the artifacts are Japanese."""
    for name in families:
        if any(k in name for k in ("Noto Sans JP", "Noto Sans CJK", "IPA", "BIZ UD", "Yu Gothic")):
            return name, [families[name]]
    if not families:
        raise SystemExit("no usable font found; pass --font <path to .ttf>")
    name = sorted(families)[0]
    return name, [families[name]]


def resolve(html: str, svg: str, family: str, class_styles: dict[str, tuple[float, str]]) -> str:
    """Turn page-level CSS into attributes the standalone SVG carries itself.

    An inline <svg> inherits custom properties and class rules from the page.
    Once lifted out of the page it inherits nothing, so both have to be baked in.
    """
    root = re.search(r":root\s*\{([^}]*)\}", html)
    variables = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root.group(1))) if root else {}

    def expand(match: re.Match[str]) -> str:
        name, fallback = match.group(1), match.group(2)
        return variables.get(name, (fallback or "#888888").strip()).strip()

    svg = re.sub(r"var\((--[\w-]+)(?:,\s*([^)]+))?\)", expand, svg)

    def inline_font(match: re.Match[str]) -> str:
        tag = match.group(0)
        for name in match.group(1).split():
            if name in class_styles:
                size, weight = class_styles[name]
                # The renderer drops text whose family it cannot resolve, without
                # warning, so the family written here must be the font's own name.
                return (f'{tag[:-1]} font-family="{family}" font-size="{size}"'
                        f' font-weight="{weight}">')
        return tag

    svg = re.sub(r'<text[^>]*class="([^"]+)"[^>]*>', inline_font, svg)
    if "xmlns=" not in svg[:200]:
        svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return svg


def read_class_sizes(html: str) -> dict[str, tuple[float, str]]:
    """Recover the size and weight the SVG text classes are set in.

    Both the longhand and the `font:` shorthand appear in practice; missing the
    shorthand leaves the text with no family, and then it never gets drawn.
    """
    styles: dict[str, tuple[float, str]] = {}
    for rule in re.finditer(r"\.([\w-]+)\s*\{([^}]*)\}", html):
        body = rule.group(2)
        shorthand = re.search(r"font\s*:\s*(?:(\d{3}|bold)\s+)?([\d.]+)px", body)
        longhand = re.search(r"font-size\s*:\s*([\d.]+)px", body)
        if shorthand:
            styles[rule.group(1)] = (float(shorthand.group(2)), shorthand.group(1) or "400")
        elif longhand:
            weight = re.search(r"font-weight\s*:\s*(\d{3}|bold)", body)
            styles[rule.group(1)] = (float(longhand.group(1)), weight.group(1) if weight else "400")
    return styles


def rects(svg: str) -> list[tuple[float, float, float, float, bool]]:
    out = []
    for match in re.finditer(r"<rect[^>]*>", svg):
        attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', match.group(0)))
        try:
            x, y = float(attrs["x"]), float(attrs["y"])
            w, h = float(attrs["width"]), float(attrs["height"])
        except (KeyError, ValueError):
            continue
        out.append((x, y, x + w, y + h, "stroke-dasharray" in attrs))
    return out


def labels(svg: str, class_styles: dict[str, tuple[float, str]]) -> list[tuple[float, float, float, float, str]]:
    out = []
    pattern = r'<text([^>]*)>([^<]*)</text>'
    for match in re.finditer(pattern, svg):
        attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', match.group(1)))
        body = match.group(2).strip()
        if not body:
            continue
        try:
            x, y = float(attrs["x"]), float(attrs["y"])
        except (KeyError, ValueError):
            continue
        fallback = class_styles.get(attrs.get("class", "").split(" ")[0], (12.0, "400"))[0]
        size = float(attrs.get("font-size") or fallback)
        width = sum(size * (1.0 if ord(ch) > CJK_START else 0.55) for ch in body)
        left = x - width / 2 if attrs.get("text-anchor") == "middle" else x
        out.append((left, y - size * CAP_HEIGHT, left + width, y + size * DESCENDER, body))
    return out


def geometry_faults(svg: str, class_styles: dict[str, tuple[float, str]]) -> list[str]:
    view = re.search(r'viewBox="([\d.\s-]+)"', svg)
    if not view:
        return ["missing viewBox"]
    vx, vy, vw, vh = (float(n) for n in view.group(1).split())

    # Generated SVG usually wraps everything in one transform, which puts the raw
    # coordinates outside the viewBox on purpose. Comparing them as written would
    # report the whole drawing as broken. Nothing here is hand-placed either, so
    # the geometry rules have nothing to catch.
    if re.search(r"<g[^>]*\stransform=", svg):
        return []
    frames = [r for r in rects(svg) if r[4]]
    faults: list[str] = []

    def inspect(left: float, top: float, right: float, bottom: float, what: str) -> None:
        if left < vx or right > vx + vw or top < vy or bottom > vy + vh:
            faults.append(f"{what}: outside the viewBox [{left:.0f}-{right:.0f}, {top:.0f}-{bottom:.0f}]")
        for fl, ft, fr, fb, _ in frames:
            if not (left < fr and right > fl and top < fb and bottom > ft):
                continue
            if left < fl or right > fr or top < ft or bottom > fb:
                faults.append(f"{what}: crosses the frame at {fl:.0f}-{fr:.0f}")
            elif min(left - fl, fr - right) < FRAME_PADDING:
                faults.append(
                    f"{what}: only {min(left - fl, fr - right):.0f}px from the frame edge"
                )

    for left, top, right, bottom, dashed in rects(svg):
        if not dashed:
            inspect(left, top, right, bottom, f"box at [{left:.0f},{top:.0f}]")
    for left, top, right, bottom, body in labels(svg, class_styles):
        inspect(left, top, right, bottom, f'text "{body[:16]}"')
    return faults


def render(svg: str, fonts: list[str], family: str, zoom: float) -> bytes:
    import resvg_py

    return bytes(
        resvg_py.svg_to_bytes(
            svg_string=svg,
            zoom=zoom,
            background="#FFFFFF",
            font_files=fonts,
            sans_serif_family=family,
            text_rendering="geometric_precision",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--font", action="append", default=[])
    parser.add_argument("--zoom", type=float, default=2.0)
    args = parser.parse_args()

    source = Path(args.html)
    html = source.read_text(encoding="utf-8")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    families = find_fonts(args.font)
    family, fonts = pick_family(families)
    class_styles = read_class_sizes(html)

    diagrams = list(re.finditer(r"<svg[\s\S]*?</svg>", html))
    if not diagrams:
        print("no inline <svg> in this artifact")
        return 0

    failed = False
    print(f"font: {family}")
    for index, match in enumerate(diagrams):
        svg = resolve(html, match.group(0), family, class_styles)
        (out_dir / f"{source.stem}-{index}.svg").write_text(svg, encoding="utf-8")
        png = out_dir / f"{source.stem}-{index}.png"
        png.write_bytes(render(svg, fonts, family, args.zoom))

        faults = geometry_faults(svg, class_styles)
        # The renderer omits unresolvable text silently. Stripping the text has to
        # change the image; if it does not, nothing was drawn in the first place.
        if "<text" in svg:
            stripped = re.sub(r"<text[\s\S]*?</text>", "", svg)
            if render(stripped, fonts, family, args.zoom) == png.read_bytes():
                faults.append("no text was drawn; the font family did not resolve")

        print(f"\n{png}")
        for fault in faults:
            print(f"  x {fault}")
        print("  " + ("no geometry faults" if not faults else f"{len(faults)} to fix"))
        failed |= bool(faults)

    print("\nOpen each PNG and look at it. The checks above do not see collisions "
          "between lines and text, crowding, or a diagram that is merely unclear.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
