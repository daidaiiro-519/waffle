"""21種を、同じ経路（意味の型 → 口 → HTML）で通して1枚にまとめる。"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from figures import render          # noqa: E402
from styles import CSS              # noqa: E402

N = lambda i, name, **kw: {"id": i, "name": name, **kw}          # noqa: E731
E_ = lambda a, b, **kw: {"from": a, "to": b, **kw}               # noqa: E731

FIGS = [
 ("flowchart", "順序と分岐", "Mermaid", {
  "kind": "graph",
  "nodes": [N("a", "調べる"), N("b", "決める"), N("c", "引き継ぐ"), N("d", "作る", role="focus")],
  "edges": [E_("a", "b"), E_("b", "c"), E_("c", "d"), E_("d", "a", label="反証が出たら")]}),

 ("state", "状態と遷移", "Mermaid", {
  "kind": "graph",
  "nodes": [N("s", "", role="start"), N("D", "DRAFT"), N("V", "VALIDATED"),
            N("A", "ACTIVE", role="focus"), N("e", "", role="end")],
  "edges": [E_("s", "D", label="骨格"), E_("D", "V", label="整合"),
            E_("V", "A", label="確定"), E_("A", "e", label="廃止"), E_("V", "D", label="不備")]}),

 ("class", "型と関連", "Mermaid", {
  "kind": "graph",
  "nodes": [N("S", "Schema", rows=["+ schemaRef", "+ version"]),
            N("D", "Document", role="focus", rows=["+ documentId", "+ status", "+ validate()"]),
            N("B", "Block", rows=["+ blockType"])],
  "edges": [E_("S", "D", label="従う"), E_("D", "B", label="1対多")]}),

 ("er", "実体と関連", "Mermaid", {
  "kind": "graph",
  "nodes": [N("D", "DOCUMENT", role="focus"), N("B", "BLOCK"), N("S", "SCHEMA")],
  "edges": [E_("D", "B", label="1対多"), E_("D", "S", label="多対1")]}),

 ("architecture", "区画と部品", "Mermaid", {
  "kind": "graph",
  "groups": [{"members": ["cli", "mcp"]}, {"members": ["svc", "model"]}],
  "nodes": [N("cli", "CLI", sub="受け口"), N("mcp", "MCP", sub="受け口"),
            N("uc", "ユースケース", sub="応用", role="focus"),
            N("svc", "業務サービス", sub="領域"), N("model", "モデル", sub="領域")],
  "edges": [E_("cli", "uc"), E_("mcp", "uc"), E_("uc", "svc"), E_("svc", "model")]}),

 ("requirement", "要求と充足", "Mermaid", {
  "kind": "graph",
  "nodes": [N("r", "鍵の一意性", sub="risk: high", role="focus"),
            N("u", "検証ユースケース", sub="usecase"), N("t", "受け入れ試験", sub="test")],
  "edges": [E_("u", "r", label="満たす"), E_("t", "r", label="確かめる")]}),

 ("mindmap", "概念の展開", "Mermaid", {
  "kind": "tree",
  "root": {"name": "区切られた文脈", "children": [
    {"name": "業務領域", "role": "focus", "children": [
      {"name": "中核"}, {"name": "一般"}, {"name": "補完"}]},
    {"name": "同じ言葉"}, {"name": "集約"}]}}),

 ("sequence", "やり取りの順序", "Mermaid", {
  "kind": "exchange",
  "participants": ["Orchestrator", "Waffle", "advisor"],
  "steps": [
    {"kind": "call", "from": "Orchestrator", "to": "Waffle", "text": "骨格を作る"},
    {"kind": "return", "from": "Waffle", "to": "Orchestrator", "text": "埋める場所の一覧"},
    {"kind": "call", "from": "Orchestrator", "to": "advisor", "text": "敵対的に確かめる"},
    {"kind": "return", "from": "advisor", "to": "Orchestrator", "text": "反証、または支持"},
    {"kind": "note", "text": "反証が出たら、差し戻して調べ直す"}]}),

 ("gantt", "作業と日程", "Mermaid", {
  "kind": "lanes", "span": 12,
  "rows": [{"name": "調べる", "bars": [{"from": 0, "to": 3, "label": "3日"}]},
           {"name": "決める", "bars": [{"from": 3, "to": 5, "label": "2日"}]},
           {"name": "引き継ぐ", "bars": [{"from": 5, "to": 6, "tone": "warn", "label": "1日"}]},
           {"name": "作る", "bars": [{"from": 6, "to": 11, "label": "5日"}]}]}),

 ("timeline", "時間順の出来事", "Mermaid", {
  "kind": "lanes", "span": 9,
  "rows": [{"name": "v8", "bars": [{"from": 0, "to": 3, "label": "操作保証を持つ"}]},
           {"name": "v9", "bars": [{"from": 3, "to": 6, "tone": "soft", "label": "鍵の一意性"}]},
           {"name": "v10", "bars": [{"from": 6, "to": 9, "label": "2ブロックを落とす"}]}]}),

 ("journey", "体験の段階", "Mermaid", {
  "kind": "lanes", "span": 5,
  "rows": [{"name": "既存を読む", "bars": [{"from": 0, "to": 3, "tone": "soft", "label": "3"}]},
           {"name": "advisorに聞く", "bars": [{"from": 0, "to": 4, "label": "4"}]},
           {"name": "骨格を作る", "bars": [{"from": 0, "to": 5, "label": "5"}]},
           {"name": "値を埋める", "bars": [{"from": 0, "to": 3, "tone": "warn", "label": "3"}]}]}),

 ("pie", "比率", "Mermaid", {
  "kind": "amounts", "ring": True, "centre": "15部品",
  "slices": [{"name": "文章の部品", "value": 10}, {"name": "図の部品", "value": 5}]}),

 ("xychart", "大小", "Mermaid", {
  "kind": "amounts",
  "slices": [{"name": "v8", "value": 56}, {"name": "v9", "value": 10}, {"name": "v10", "value": 4}]}),

 ("sankey", "流れの量", "Mermaid", {
  "kind": "amounts", "ring": True, "centre": "19本",
  "slices": [{"name": "構造化データ → Markdown", "value": 15},
             {"name": "構造化データ → HTML", "value": 4}]}),

 ("quadrant", "2軸での位置づけ", "Mermaid", {
  "kind": "matrix", "x": "差別化が小さい ← → 大きい", "y": "複雑さ 低 ← → 高",
  "quadrants": ["中核", "見直す", "一般", "補完"],
  "points": [{"name": "文書の検証", "x": .78, "y": .74},
             {"name": "描画", "x": .38, "y": .55},
             {"name": "設定の読み込み", "x": .18, "y": .18}]}),

 ("gitGraph", "枝分かれと合流", "Mermaid", {
  "kind": "lanes", "span": 8,
  "rows": [{"name": "main", "bars": [{"from": 0, "to": 2, "label": "骨格"},
                                     {"from": 6, "to": 8, "label": "合流"}]},
           {"name": "spec", "bars": [{"from": 2, "to": 6, "tone": "soft", "label": "基準を足す"}]}]}),

 ("block", "箱組み", "Mermaid", {
  "kind": "blocks", "cols": 3,
  "cells": [{"name": "受け口"}, {"name": "応用", "tone": "focus"}, {"name": "領域"},
            {"name": "CLI / MCP"}, {"name": "ユースケース", "tone": "focus"}, {"name": "モデル"}]}),

 ("comparison", "変更前と変更後の対比", "新規", {
  "kind": "comparison",
  "sides": [
   {"at": "before", "label": "変更前", "note": "親は1つしか持てない", "groups": [
     {"label": "区切られた文脈の内側", "contentKind": "tree", "content":
      {"name": "区切られた文脈", "children": [
        {"name": "業務領域", "role": "focus", "children": [{"name": "業務ユースケース"}]},
        {"name": "集約"}]}}]},
   {"at": "after", "label": "変更後", "note": "親は事業領域。所属は参照が運ぶ",
    "links": [{"label": "対応"}], "groups": [
     {"label": "問題空間", "contentKind": "tree", "content":
      {"name": "事業領域", "children": [{"name": "業務領域", "role": "focus"}]}},
     {"label": "解決空間", "contentKind": "tree", "content":
      {"name": "区切られた文脈", "children": [{"name": "業務ユースケース"}, {"name": "集約"}]}}]}]}),

 ("transcript", "操作と、返ってきたもの", "新規", {
  "kind": "transcript", "title": "terminal", "lines": [
    {"kind": "comment", "text": "# 宣言を書き換えたあと"},
    {"kind": "command", "text": "$ waffle check-spec-integrity --path …/bc-waffle.json"},
    {"kind": "output", "text": "{\"declared_subdomains_missing_on_disk\":\n   [\"sd-validation\", …7件]}"},
    {"kind": "note", "text": "↑ 宣言された場所を見て、そこに無いと言う"}]}),

 ("listing", "並びと、増えた・減った", "新規", {
  "kind": "listing", "items": [
    {"name": "表題"}, {"name": "目的"}, {"name": "操作保証", "role": "removed"},
    {"name": "保証シナリオ", "role": "removed"}, {"name": "受け入れ基準"},
    {"name": "シナリオ", "role": "added"}, {"name": "用語"}]}),

 ("tree", "入れ子（対比の中身としても使う）", "新規", {
  "kind": "tree",
  "root": {"name": "Document", "children": [
    {"name": "content", "role": "focus", "children": [{"name": "block"}, {"name": "block"}]},
    {"name": "meta"}]}}),
]


def main():
    cards, fails = [], []
    for name, what, origin in [(f[0], f[1], f[2]) for f in FIGS]:
        pass
    for name, what, origin, data in FIGS:
        try:
            body = render(data)
            ok = True
        except Exception as exc:                                  # 失敗も成果として残す
            body = f'<p class="fail">描けなかった: {exc}</p>'
            ok = False
            fails.append(name)
        tag = "new" if origin == "新規" else "mmd"
        cards.append(f'<section class="card"><header><h2>{name}</h2>'
                     f'<span class="t t--{tag}">{origin}</span>'
                     f'<span class="what">{what}</span></header>'
                     f'<div class="stage">{body}</div></section>')

    page = ("<title>21種を同じ経路で通す</title><style>" + CSS + PAGE_CSS + "</style>"
            '<main><h1>21種を同じ経路で通す</h1>'
            '<p class="lede">意味の型 → 並びを決める口 → HTML。'
            'SVGは使わず、位置をpxで書いた箇所は一つもない。</p>'
            + "".join(cards) + "</main>")
    out = pathlib.Path(sys.argv[1])
    out.write_text(page, encoding="utf-8")
    print(f"描いた {len(FIGS) - len(fails)}/{len(FIGS)}" + (f"  失敗: {fails}" if fails else ""))


PAGE_CSS = """
  *{box-sizing:border-box;}
  body{margin:0;padding:2rem 1.4rem 5rem;background:var(--paper);color:var(--ink);
       font-family:var(--sans);}
  main{max-width:60rem;margin:0 auto;display:flex;flex-direction:column;gap:1.6rem;}
  h1{font-size:1.5rem;margin:0;}
  .lede{color:var(--ink-soft);font-size:.9rem;margin:0 0 .6rem;}
  .card{background:var(--surface);border:1px solid var(--rule);border-radius:12px;
        padding:1rem 1.2rem 1.4rem;display:flex;flex-direction:column;gap:.8rem;}
  .card header{display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap;}
  .card h2{font-family:var(--mono);font-size:.9rem;margin:0;}
  .t{font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;padding:.08rem .4rem;
     border-radius:4px;border:1px solid currentColor;}
  .t--mmd{color:var(--ink-faint);} .t--new{color:var(--acc);}
  .what{font-size:.78rem;color:var(--ink-soft);}
  .stage{background:var(--paper);border-radius:8px;padding:1.4rem 1rem;
         display:flex;justify-content:center;overflow-x:auto;}
  .fail{color:var(--warn);font-size:.8rem;}
"""

if __name__ == "__main__":
    main()
