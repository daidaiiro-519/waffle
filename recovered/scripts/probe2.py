import pathlib
import resvg_py

src = pathlib.Path("sample-gate1-subdomain-0.svg").read_text()
for label, svg in [
    ("そのまま", src),
    ("xmlnsを足す", src.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)),
    ("xmlns+実フォント名", src.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
                          .replace('font-family="NotoSansJP"', 'font-family="Noto Sans JP"')),
]:
    b = resvg_py.svg_to_bytes(svg_string=svg, zoom=2.0, background="#EDF0F3")
    print(f"{label:20} {len(b):7} bytes")
    pathlib.Path(f"probe2-{label}.png").write_bytes(bytes(b))