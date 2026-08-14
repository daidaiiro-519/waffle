import json, pathlib, sys
S = pathlib.Path(__file__).parent
sys.path.insert(0, str(S))
from parts_v2 import render_comparison

# 同じ器に、違う中身を3種入れる
tree_fig = {
 "intent": "業務領域が、区切られた文脈の内側から外へ出る",
 "sides": [
  {"at":"before","label":"変更前","reading":"親は1つしか持てない","groups":[
    {"label":"区切られた文脈の内側","contentKind":"tree","content":
      {"name":"区切られた文脈","children":[
        {"name":"業務領域","role":"focus","children":[{"name":"業務ユースケース"}]},
        {"name":"集約"}]}}]},
  {"at":"after","label":"変更後","reading":"親は事業領域。所属は参照が運ぶ",
   "links":[{"label":"対応"}],"groups":[
    {"label":"問題空間","contentKind":"tree","content":
      {"name":"事業領域","children":[{"name":"業務領域","role":"focus"}]}},
    {"label":"解決空間","contentKind":"tree","content":
      {"name":"区切られた文脈","children":[{"name":"業務ユースケース"},{"name":"集約"}]}}]}]}

transcript_fig = {
 "intent": "同じ操作の結果が、宣言の書き換えで変わる",
 "sides": [
  {"at":"before","label":"変更前","groups":[{"label":"","contentKind":"transcript","content":
    {"title":"terminal","lines":[
      {"kind":"comment","text":"# 宣言を新しい置き場所へ書き換えたあと"},
      {"kind":"command","text":"$ waffle check-spec-integrity --path …/bc-waffle.json"},
      {"kind":"output","text":"{\"declared_subdomains_missing_on_disk\": [],\n \"subdomain_ref_mismatches\": []}"},
      {"kind":"note","text":"↑ 古い場所を見て「違反なし」。効いていないことに気づけない"}]}}]},
  {"at":"after","label":"変更後","groups":[{"label":"","contentKind":"transcript","content":
    {"title":"terminal","lines":[
      {"kind":"comment","text":"# 同じ操作"},
      {"kind":"command","text":"$ waffle check-spec-integrity --path …/bc-waffle.json"},
      {"kind":"output","text":"{\"declared_subdomains_missing_on_disk\":\n   [\"sd-validation\", …7件]}"},
      {"kind":"note","text":"↑ 宣言された場所を見て、そこに無いと言う"}]}}]}]}

listing_fig = {
 "intent": "仕様の器から、2つのブロックが落ちる",
 "sides": [
  {"at":"before","label":"v9","groups":[{"label":"ブロック構成","contentKind":"listing","content":
    {"items":[{"name":"表題"},{"name":"目的"},{"name":"操作保証","role":"removed"},
              {"name":"保証シナリオ","role":"removed"},{"name":"受け入れ基準"},{"name":"用語"}]}}]},
  {"at":"after","label":"v10","groups":[{"label":"ブロック構成","contentKind":"listing","content":
    {"items":[{"name":"表題"},{"name":"目的"},{"name":"受け入れ基準"},
              {"name":"シナリオ","role":"added"},{"name":"用語"}]}}]}]}

MERMAID = {
 "classDiagram": """classDiagram
    class Document {
      +documentId
      +status
      +validate()
    }
    class Block {
      +blockType
    }
    Document "1" *-- "多" Block""",
 "erDiagram": """erDiagram
    DOCUMENT ||--o{ BLOCK : "持つ"
    DOCUMENT }o--|| SCHEMA : "従う\"""",
 "quadrantChart": """quadrantChart
    title 業務領域の分類
    x-axis 差別化が小さい --> 差別化が大きい
    y-axis 複雑さが低い --> 複雑さが高い
    quadrant-1 中核
    quadrant-2 見直す
    quadrant-3 一般
    quadrant-4 補完
    文書の検証: [0.78, 0.72]
    描画: [0.35, 0.55]
    設定の読み込み: [0.2, 0.2]""",
 "mindmap": """mindmap
  root((区切られた文脈))
    業務領域
      中核
      一般
      補完
    同じ言葉
    集約""",
 "timeline": """timeline
    title 仕様の器の推移
    v8 : 操作保証を持つ
    v9 : 鍵の一意性を足す
    v10 : 2ブロックを落とす""",
 "journey": """journey
    title 仕様を書く
    section 調べる
      既存を読む: 3: 書き手
      advisorに聞く: 4: 書き手
    section 決める
      骨格を作る: 5: 書き手
      値を埋める: 3: 書き手""",
 "gantt": """gantt
    title 工程
    dateFormat YYYY-MM-DD
    section 進行
    調べる    :a1, 2026-08-01, 3d
    決める    :a2, after a1, 2d
    引き継ぐ  :a3, after a2, 1d
    作る      :a4, after a3, 5d""",
 "pie": """pie title 部品の内訳
    "文章の部品" : 10
    "図の部品" : 5""",
 "gitGraph": """gitGraph
    commit id: "骨格"
    branch spec
    commit id: "基準を足す"
    commit id: "検証を通す"
    checkout main
    merge spec""",
 "requirementDiagram": """requirementDiagram
    requirement 鍵の一意性 {
        id: 1
        text: 同じ鍵を二度作らない
        risk: high
        verifymethod: test
    }
    element 検証 {
        type: usecase
    }
    検証 - satisfies -> 鍵の一意性""",
 "sankey-beta": """sankey-beta

構造化データ,Markdown,15
構造化データ,HTML,4
Markdown,成果物,15
HTML,成果物,4""",
 "xychart-beta": """xychart-beta
    title "版ごとの仕様の数"
    x-axis [v8, v9, v10]
    y-axis "件数" 0 --> 60
    bar [56, 10, 4]""",
 "block-beta": """block-beta
columns 3
  a["受け口"] b["応用"] c["領域"]
  d["CLI / MCP"] e["ユースケース"] f["モデル"]""",
}

out = {
 "comparisons": {
   "tree": render_comparison(tree_fig),
   "transcript": render_comparison(transcript_fig),
   "listing": render_comparison(listing_fig)},
 "comparison_data": {"tree": tree_fig, "listing": listing_fig},
 "mermaid_extra": MERMAID,
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print("comparison:", {k: len(v) for k, v in out["comparisons"].items()})
print("mermaid 追加:", len(MERMAID), "種")