"""層の形を決めるADRの図。変更前＝一直線の5層／変更後＝2本の柱と共有の天辺。"""
import pathlib, sys, json
sys.path.insert(0, "."); sys.path.insert(0, str(pathlib.Path("../figs").resolve()))
from draw import render

BEFORE = {
  "asserts": "階層",
  "reading": "上から下へ一直線。規約が仕様の上に居る",
  "items": [{"name": "knowledge", "children": [
      {"name": "schema の記入指示", "children": [
          {"name": "規約", "role": "focus", "children": [
              {"name": "仕様", "children": [
                  {"name": "実装 ／ テスト"}]}]}]}]}]}

AFTER = {
  "asserts": "階層",
  "reading": "天辺だけを共有し、2本に分かれ、実装で合流する",
  "items": [{"name": "knowledge", "children": [
      {"name": "DomainSpecSchema の記入指示", "children": [
          {"name": "仕様（何ができるか）", "children": [{"name": "実装 ／ テスト", "role": "focus"}]}]},
      {"name": "CodingSchema の記入指示", "children": [
          {"name": "規約（どう綴り、どこに置くか）", "children": [{"name": "実装 ／ テスト", "role": "focus"}]}]}]}]}

out = {}
for k, fig in (("before", BEFORE), ("after", AFTER)):
    s = render(fig)
    out[k] = s
    import re
    m = re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"', s)
    print(k, m.group(1), "x", m.group(2))
pathlib.Path("../figs/adr_layers.json").write_text(json.dumps(out, ensure_ascii=False))
print("書いた")