import json, pathlib, sys, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from figure_part import render_structure

figure = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
html = render_structure(figure)
# 読めるように改行を入れて出す
html = re.sub(r'><(div|figcaption|p)', r'>\n<\1', html)
print(html)
print("\n--- 出たHTMLに現れた色・大きさ・座標 ---")
hits = re.findall(r'#[0-9A-Fa-f]{3,6}|\d+(?:px|rem|%)|left:|top:', html)
print(hits or "0件")