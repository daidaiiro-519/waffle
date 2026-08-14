import pathlib, re, resvg_py
OUT = pathlib.Path(__file__).parent / "probe"
FONT = str(pathlib.Path.home() / ".local/share/fonts/NotoSansJP.ttf")
for svg_path in sorted(OUT.glob("*.svg")):
    svg = re.sub(r'(width|height)="([\d.]+)pt"', r'\1="\2"', svg_path.read_text())
    png = resvg_py.svg_to_bytes(svg_string=svg, zoom=2.0, background="#FFFFFF",
                                font_files=[FONT], sans_serif_family="Noto Sans JP")
    (OUT / f"{svg_path.stem}.png").write_bytes(bytes(png))
    print(svg_path.stem, len(png))