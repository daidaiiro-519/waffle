"""graph_viewer_html_template — uc-render-document-graphが使う固定HTMLテンプレート。
specKind（DomainSpec）/documentType（それ以外）別のフラットなカテゴリをtreemapで
一瞰し、カテゴリをクリックするとそのカテゴリの個別documentが一覧され、各document
には既にどれと紐づいているか（related）が表示されている、というドリルダウン型UX。

設計の変遷（ユーザーフィードバックを都度反映）: 力指向グラフ→種別グルーピングの
平坦リスト→bc/subdomain包含階層のtree→treemap（subdomain→specKindの2階層ネスト）
→本設計。「文脈境界・集約・サブドメインのタグがない、名称が展開されている」という
指摘を受け、個別documentの固有名を最上位分類に使うのをやめ、specKind自体を
カテゴリタグとして最上位に置いた。「カテゴリを選んで、選んだものが何と紐づくか
わかるのが一番UXが良い」という要望を受け、常時ハイライトのクリック方式から
カテゴリ選択→document一覧（related付き）というドリルダウンへ変更した。
バックエンド不要、ページ内スクロールのみで完結させる。
"""
from __future__ import annotations

import html as _html

from waffle.domain.services.graph_index import compute_categories
from waffle.domain.services.treemap_layout import normalize_sizes, squarify

_TREEMAP_W = 760.0
_TREEMAP_H = 300.0

_TYPE_PALETTE = [
    "#2f5c46", "#7a4f9e", "#a15c2c", "#2c6b8f", "#8f2c4f", "#5c7a2c", "#4f4f4f",
    "#3a6f6f", "#9c5b2e", "#5b5c9c",
]

_CSS = """
:root {
  --paper: #f3f1ec; --ink: #23241f; --ink-dim: #63645a; --ink-faint: #8c8d80;
  --line: #ddd9cd; --surface: #ffffff; --surface-sunken: #faf9f5;
  --accent: #2f5c46; --accent-soft: #e6f0ea; --accent-ink: #ffffff;
  --shadow: 0 1px 2px rgba(35,36,31,0.04), 0 4px 14px rgba(35,36,31,0.05);
  --mono: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;
  --sans: -apple-system, "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif;
}
:root[data-theme="dark"] {
  --paper: #1b1c18; --ink: #eceae2; --ink-dim: #b0af9f; --ink-faint: #7c7b6d;
  --line: #37382f; --surface: #232420; --surface-sunken: #1f201c;
  --accent: #82c4a4; --accent-soft: #1c332a; --accent-ink: #14211b;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #1b1c18; --ink: #eceae2; --ink-dim: #b0af9f; --ink-faint: #7c7b6d;
    --line: #37382f; --surface: #232420; --surface-sunken: #1f201c;
    --accent: #82c4a4; --accent-soft: #1c332a; --accent-ink: #14211b;
  }
}
* { box-sizing: border-box; }
html { scrollbar-gutter: stable; overflow-y: scroll; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--sans); -webkit-font-smoothing: antialiased; overflow-x: hidden; }
.toolbar {
  position: sticky; top: 0; z-index: 10; display: flex; gap: 0.6rem; align-items: center;
  padding: 0.8rem 1rem; background: var(--surface); border-bottom: 1px solid var(--line); box-shadow: var(--shadow);
}
.toolbar input {
  font-family: var(--mono); font-size: 0.82rem; padding: 0.4rem 0.7rem; border-radius: 8px;
  border: 1px solid var(--line); background: var(--surface-sunken); color: var(--ink);
  flex: 1; max-width: 420px;
}
main { max-width: 860px; margin: 0 auto; padding: 1.4rem 1.2rem 4rem; }
main > h2 {
  font-family: var(--mono); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--ink-faint); border-bottom: 1px solid var(--line); padding-bottom: 0.4rem; margin: 1.8rem 0 0.6rem;
}
.treemap { margin-bottom: 0.4rem; }
.treemap svg { width: 100%; height: auto; display: block; border-radius: 10px; overflow: hidden; }
.tm-rect { stroke: var(--paper); stroke-width: 2; cursor: pointer; transition: opacity 0.15s; }
.tm-rect.tm-active { stroke: var(--ink); stroke-width: 3; }
.tm-label { font-family: var(--sans); fill: var(--accent-ink); pointer-events: none; }
.tm-count { font-family: var(--mono); fill: var(--accent-ink); opacity: 0.85; pointer-events: none; }
.hint { font-size: 0.78rem; color: var(--ink-faint); margin: 0.4rem 0 1.4rem; }
.cat-panel {
  display: none; border: 1px solid var(--line); border-radius: 10px; background: var(--surface);
  padding: 0.4rem 1rem; margin-bottom: 1.2rem;
}
.cat-panel.open { display: block; }
.doc-row { padding: 0.6rem 0; border-bottom: 1px solid var(--line); scroll-margin-top: 4.5rem; transition: background 0.3s; }
.doc-row:last-child { border-bottom: none; }
.doc-row.hidden { display: none; }
.doc-row.doc-focus { background: var(--accent-soft); outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 6px; }
.doc-title { font-size: 0.9rem; font-weight: 600; }
.doc-id { font-family: var(--mono); font-size: 0.7rem; color: var(--ink-faint); margin-left: 0.5rem; }
.doc-desc { font-size: 0.82rem; color: var(--ink-dim); margin: 0.25rem 0 0; line-height: 1.5; }
.doc-related { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.4rem; }
.rel-group {
  font-size: 0.72rem; border: 1px solid var(--line); border-radius: 8px;
  background: var(--surface-sunken); padding: 0.1rem 0.5rem;
}
.rel-group summary { cursor: pointer; color: var(--accent); font-family: var(--mono); padding: 0.2rem 0; list-style: none; }
.rel-group summary::-webkit-details-marker { display: none; }
.rel-group summary::before { content: "🔗 "; }
.rel-list { list-style: none; margin: 0.3rem 0 0.4rem 0.15rem; padding: 0 0 0 0.9rem; border-left: 1px solid var(--line); }
.rel-list li { position: relative; padding: 0.2rem 0 0.2rem 0.8rem; }
.rel-list li::before {
  content: ""; position: absolute; left: 0; top: 0.95rem; width: 0.6rem; height: 1px; background: var(--line);
}
.rel-list a {
  display: inline-block; color: var(--ink); text-decoration: none; cursor: pointer;
  font-size: 0.78rem; padding: 0.28rem 0.65rem; border: 1px solid var(--line); border-radius: 7px;
  background: var(--surface); box-shadow: var(--shadow); transition: transform 0.1s, border-color 0.15s, color 0.15s, background 0.15s;
}
.rel-list a:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); transform: translateY(-1px); }
.rel-list a:active { transform: translateY(0); }
.no-related { font-size: 0.74rem; color: var(--ink-faint); margin-top: 0.35rem; }
.doc-tabs { display: flex; gap: 0.4rem; margin: 0.5rem 0 0.5rem; }
.tab-btn {
  font-family: var(--mono); font-size: 0.7rem; padding: 0.2rem 0.6rem; border-radius: 999px;
  border: 1px solid var(--line); background: var(--surface-sunken); color: var(--ink-dim); cursor: pointer;
}
.tab-btn.active { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
.tab-pane { display: none; }
.tab-pane.active { display: block; }
.tab-full iframe { width: 100%; height: 420px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
.tab-full .full-link { font-size: 0.76rem; margin-top: 0.4rem; display: inline-block; color: var(--accent); }
.tab-full .missing { font-size: 0.8rem; color: var(--ink-faint); line-height: 1.6; }
.tab-full .missing code {
  display: block; margin-top: 0.4rem; font-family: var(--mono); font-size: 0.72rem;
  background: var(--surface-sunken); border: 1px solid var(--line); border-radius: 6px;
  padding: 0.5rem 0.7rem; overflow-x: auto; white-space: pre;
}
"""


def _type_color(types_seen: dict, t: str) -> str:
    if t not in types_seen:
        types_seen[t] = _TYPE_PALETTE[len(types_seen) % len(_TYPE_PALETTE)]
    return types_seen[t]


def _render_treemap(categories: list[dict], types_seen: dict) -> str:
    """specKind/documentType別のフラットなカテゴリを、面積比例のsquarified treemapとして描画する。"""
    if not categories:
        return ""
    sizes = normalize_sizes([c["count"] for c in categories], _TREEMAP_W, _TREEMAP_H)
    boxes = squarify(sizes, 0, 0, _TREEMAP_W, _TREEMAP_H)
    parts = []
    for c, (x, y, w, h) in zip(categories, boxes):
        color = _type_color(types_seen, c["label"])
        parts.append(
            f'<rect class="tm-rect" data-cat-key="{_html.escape(c["key"])}" '
            f'x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{color}">'
            f'<title>{_html.escape(c["label"])} ({c["count"]}件) — クリックで一覧</title></rect>'
        )
        if w > 54 and h > 20:
            font_size = min(15, max(9, w / 10))
            parts.append(
                f'<text class="tm-label" x="{x + 7:.1f}" y="{y + font_size + 6:.1f}" font-size="{font_size:.0f}">'
                f'{_html.escape(c["label"])}</text>'
            )
            if h > 36:
                parts.append(
                    f'<text class="tm-count" x="{x + 7:.1f}" y="{y + font_size + 22:.1f}" font-size="{font_size - 1:.0f}">'
                    f'{c["count"]}件</text>'
                )
    svg = "".join(parts)
    return (
        f'<section class="treemap"><h2>カテゴリ（クリックで一覧を開く）</h2>'
        f'<svg id="treemapSvg" viewBox="0 0 {_TREEMAP_W:.0f} {_TREEMAP_H:.0f}" role="img">{svg}</svg></section>'
        f'<p class="hint">箱をクリックすると、そのカテゴリのdocument一覧と紐づき先が表示されます。</p>'
    )


def _render_related(related: list[dict]) -> str:
    """紐づき先をカテゴリ別に折りたたんだ小さなツリーとして描画する。
    平坦なバッジの羅列だと件数が多いdocumentで読めなくなるため
    （ユーザーフィードバック「リンクの表現をツリーにしないと」）。各項目はクリックで
    「treemapでそのカテゴリを選び、その中の該当documentを選んだ」のと同じ状態へ
    遷移するリンクにする（ユーザーフィードバック「紐づき先に飛べるようにしたい」）。"""
    if not related:
        return '<div class="no-related">紐づき先なし</div>'
    by_category: dict[str, list[dict]] = {}
    for r in related:
        by_category.setdefault(r["category"], []).append(r)
    groups = []
    for category, items in sorted(by_category.items(), key=lambda kv: -len(kv[1])):
        cat_key = f"cat::{category}"
        lis = "".join(
            f'<li><a class="rel-link" data-cat-key="{_html.escape(cat_key)}" data-doc-id="{_html.escape(r["id"])}">'
            f'{_html.escape(r["title"])}</a></li>'
            for r in items
        )
        groups.append(
            f'<details class="rel-group"><summary>{_html.escape(category)} ({len(items)}件)</summary>'
            f'<ul class="rel-list">{lis}</ul></details>'
        )
    return f'<div class="doc-related">{"".join(groups)}</div>'


def _render_full_tab(doc_id: str, viewer_available: dict[str, str], path_by_id: dict[str, str]) -> str:
    """「全体」タブの中身。uc-render-document-graphはメタデータの集計・投影に留め、
    MD本文のHTMLレンダリングはしない（uc-render-document-viewerの責務、ddd-advisor/
    tech-lead-advisor確認済み）。既に生成済みの個別viewer HTML（.waffle/view/
    {documentId}.html）があればiframeで参照し、無ければ生成コマンドを案内する
    （ユーザーフィードバック「開いた時にdescriptionのみの場合と全体のHTMLを見たい時
    はタブで切り替えできると嬉しい」）。"""
    href = viewer_available.get(doc_id)
    if href:
        return (
            f'<iframe src="{_html.escape(href)}" loading="lazy"></iframe>'
            f'<a class="full-link" href="{_html.escape(href)}" target="_blank" rel="noopener">別タブで開く ↗</a>'
        )
    path = path_by_id.get(doc_id, "")
    cmd = f"uv run --project . waffle render-document-viewer --path {path} --outputPath .waffle/view/{doc_id}.html"
    return f'<div class="missing">このdocumentの全体HTMLはまだ生成されていません。<code>{_html.escape(cmd)}</code></div>'


def _render_panel(category: dict, viewer_available: dict[str, str], path_by_id: dict[str, str]) -> str:
    rows = []
    for d in category["docs"]:
        hay = f'{d["id"]} {d["title"]}'.lower()
        desc = d.get("description") or ""
        desc_html = f'<p class="doc-desc">{_html.escape(desc)}</p>' if desc else ""
        rows.append(
            f'<div class="doc-row" id="doc-{_html.escape(d["id"])}" data-hay="{_html.escape(hay)}">'
            f'<span class="doc-title">{_html.escape(d["title"])}</span>'
            f'<span class="doc-id">{_html.escape(d["id"])}</span>'
            f'<div class="doc-tabs">'
            f'<button class="tab-btn active" data-tab="desc">概要</button>'
            f'<button class="tab-btn" data-tab="full">全体</button>'
            f'</div>'
            f'<div class="tab-pane tab-desc active">{desc_html}{_render_related(d["related"])}</div>'
            f'<div class="tab-pane tab-full">{_render_full_tab(d["id"], viewer_available, path_by_id)}</div>'
            f'</div>'
        )
    return f'<div class="cat-panel" id="panel-{_html.escape(category["key"])}">{"".join(rows)}</div>'


def render_graph_html(
    graph: dict, viewer_available: dict[str, str] | None = None, path_by_id: dict[str, str] | None = None
) -> str:
    """全documentをspecKind/documentType別のフラットなカテゴリへ分類し、treemapで一瞰、
    クリックしたカテゴリのdocument一覧（紐づき先付き）を表示する自己完結HTMLを返す。
    各documentは「概要」（description要約＋紐づき先）と「全体」（生成済みなら個別
    viewer HTMLをiframe参照、未生成ならコマンド案内）をタブで切り替えられる。"""
    types_seen: dict = {}
    viewer_available = viewer_available or {}
    path_by_id = path_by_id or {}
    categories = compute_categories(graph)
    treemap_html = _render_treemap(categories, types_seen)
    panels_html = "".join(_render_panel(c, viewer_available, path_by_id) for c in categories)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Waffle Document Graph</title>
<style>{_CSS}</style>
</head>
<body>
<div class="toolbar">
  <input id="search" type="text" placeholder="開いているカテゴリ内を documentId / title で検索">
</div>
<main>
{treemap_html}
{panels_html}
</main>
<script>
(() => {{
  const boxes = document.querySelectorAll('#treemapSvg rect[data-cat-key]');

  function selectCategory(key) {{
    const panel = document.getElementById('panel-' + key);
    boxes.forEach((b) => b.classList.toggle('tm-active', b.dataset.catKey === key));
    document.querySelectorAll('.cat-panel.open').forEach((p) => p.classList.remove('open'));
    if (panel) panel.classList.add('open');
  }}

  boxes.forEach((box) => {{
    box.addEventListener('click', () => {{
      const wasOpen = box.classList.contains('tm-active');
      if (wasOpen) {{
        boxes.forEach((b) => b.classList.remove('tm-active'));
        document.querySelectorAll('.cat-panel.open').forEach((p) => p.classList.remove('open'));
        return;
      }}
      selectCategory(box.dataset.catKey);
    }});
  }});

  document.querySelectorAll('.tab-btn').forEach((btn) => {{
    btn.addEventListener('click', () => {{
      const row = btn.closest('.doc-row');
      row.querySelectorAll('.tab-btn').forEach((b) => b.classList.toggle('active', b === btn));
      row.querySelectorAll('.tab-pane').forEach((p) => p.classList.toggle('active', p.classList.contains('tab-' + btn.dataset.tab)));
    }});
  }});

  document.querySelectorAll('.rel-link').forEach((link) => {{
    link.addEventListener('click', (e) => {{
      e.preventDefault();
      selectCategory(link.dataset.catKey);
      const target = document.getElementById('doc-' + link.dataset.docId);
      if (!target) return;
      target.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      target.classList.add('doc-focus');
      setTimeout(() => target.classList.remove('doc-focus'), 1600);
    }});
  }});
}})();

document.getElementById('search').addEventListener('input', (e) => {{
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('.doc-row').forEach((row) => {{
    row.classList.toggle('hidden', !!q && !row.dataset.hay.includes(q));
  }});
}});
</script>
</body>
</html>
"""
