import pathlib
import resvg_py

FONT = str(pathlib.Path.home() / ".local/share/fonts/NotoSansJP.ttf")
mini = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 40"><text x="10" y="25" font-family="Noto Sans JP" font-size="16" fill="#000">業務領域 abc</text></svg>'
for label, kw in [
    ("何も渡さない", {}),
    ("font_files", {"font_files": [FONT]}),
    ("font_dirs", {"font_dirs": [str(pathlib.Path.home() / ".local/share/fonts")]}),
    ("両方+sans指定", {"font_files": [FONT], "sans_serif_family": "Noto Sans JP"}),
]:
    try:
        b = resvg_py.svg_to_bytes(svg_string=mini, **kw)
        print(f"{label:16} {len(b):6} bytes")
        pathlib.Path(f"{pathlib.Path(__file__).parent}/probe-{label}.png").write_bytes(bytes(b))
    except Exception as e:
        print(f"{label:16} 失敗 {e}")