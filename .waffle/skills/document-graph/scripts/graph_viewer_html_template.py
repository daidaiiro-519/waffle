"""graph_viewer_html_template — document-graph Skillが使う固定HTMLテンプレート。
契約の`type`別のフラットなカテゴリをtreemapで一瞰し、カテゴリをクリックするとその
カテゴリの個別document一覧（紐づき先付き）が表示される、というドリルダウン型UX。

Waffle本体の src/waffle/domain/services/graph_viewer_html_template.py をベースに
移植した。差分（brainstorm-document-graph-skill.md 論点3・4の合意決定）:
  - node属性を契約の{id, type, title, description, tags}＋relatedだけに絞り込み、
    Waffle固有のspecKind/schemaRefへの参照を除去した。
  - Waffle固有だった「全体」タブ（document.jsonからMD/HTMLをその場でレンダリング
    するタブ）を削除した。Skill側は既に契約準拠のHTML/MDファイルそのものを持って
    いるので、代わりに各documentへ直接の「元ファイルを開く」リンクを1本添える。
"""
from __future__ import annotations

import html as _html

from graph_index import compute_categories
from treemap_layout import normalize_sizes, squarify

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
.refresh-btn {
  font-family: var(--mono); font-size: 0.78rem; padding: 0.42rem 0.8rem; border-radius: 8px;
  border: 1px solid var(--line); background: var(--surface); color: var(--ink-dim); cursor: pointer;
  display: flex; align-items: center; gap: 0.35rem; white-space: nowrap;
}
.refresh-btn:hover { border-color: var(--accent); color: var(--accent); }
main { max-width: 860px; margin: 0 auto; padding: 1.4rem 1.2rem 4rem; }
main > h2 {
  font-family: var(--mono); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--ink-faint); border-bottom: 1px solid var(--line); padding-bottom: 0.4rem; margin: 1.8rem 0 0.6rem;
}
.warn-banner {
  font-size: 0.8rem; color: var(--ink); background: var(--accent-soft); border: 1px solid var(--accent);
  border-radius: 8px; padding: 0.6rem 0.9rem; margin: 1rem 0; white-space: pre-wrap;
}
.treemap { margin-bottom: 0.4rem; }
.treemap svg { width: 100%; height: auto; display: block; border-radius: 10px; overflow: hidden; }
.tm-rect { stroke: var(--paper); stroke-width: 2; cursor: pointer; transition: opacity 0.15s; }
.tm-rect.tm-dim { opacity: 0.3; }
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
.doc-open { font-size: 0.76rem; margin-left: 0.5rem; color: var(--accent); text-decoration: none; }
.doc-open:hover { text-decoration: underline; }
.doc-desc { font-size: 0.82rem; color: var(--ink-dim); margin: 0.25rem 0 0; line-height: 1.5; }
.doc-related { display: flex; flex-direction: column; gap: 0.35rem; margin-top: 0.4rem; }
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
"""


def _type_color(types_seen: dict, t: str) -> str:
    if t not in types_seen:
        types_seen[t] = _TYPE_PALETTE[len(types_seen) % len(_TYPE_PALETTE)]
    return types_seen[t]


def _render_treemap(categories: list[dict], types_seen: dict) -> str:
    """契約の`type`別のフラットなカテゴリを、面積比例のsquarified treemapとして描画する。"""
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
    """紐づき先をカテゴリ別に折りたたんだ小さなツリーとして描画する。各項目はクリックで
    「treemapでそのカテゴリを選び、その中の該当documentを選んだ」のと同じ状態へ遷移する
    リンクにする。"""
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


def _render_panel(category: dict, files_base_url: str) -> str:
    rows = []
    for d in category["docs"]:
        hay = f'{d["id"]} {d["title"]}'.lower()
        desc = d.get("description") or ""
        desc_html = f'<p class="doc-desc">{_html.escape(desc)}</p>' if desc else ""
        open_href = f'{files_base_url}{d["href"]}'
        rows.append(
            f'<div class="doc-row" id="doc-{_html.escape(d["id"])}" data-hay="{_html.escape(hay)}">'
            f'<span class="doc-title">{_html.escape(d["title"])}</span>'
            f'<span class="doc-id">{_html.escape(d["id"])}</span>'
            f'<a class="doc-open" href="{_html.escape(open_href)}" target="_blank" rel="noopener">元ファイルを開く ↗</a>'
            f'{desc_html}'
            f'{_render_related(d["related"])}'
            f'</div>'
        )
    return f'<div class="cat-panel" id="panel-{_html.escape(category["key"])}">{"".join(rows)}</div>'


def _render_warnings(warnings: list[str]) -> str:
    if not warnings:
        return ""
    items = "\n".join(_html.escape(w) for w in warnings)
    return f'<div class="warn-banner">⚠ {items}</div>'


def render_graph_html(graph: dict, warnings: list[str] | None = None, files_base_url: str = "/files/") -> str:
    """全documentを契約の`type`別のフラットなカテゴリへ分類し、treemapで一瞰、
    クリックしたカテゴリのdocument一覧（紐づき先付き）を表示する自己完結HTMLを返す。
    各documentには元ファイル（契約準拠のMD/HTML）への直接リンクを添える。"""
    types_seen: dict = {}
    categories = compute_categories(graph)
    treemap_html = _render_treemap(categories, types_seen)
    panels_html = "".join(_render_panel(c, files_base_url) for c in categories)
    warnings_html = _render_warnings(warnings or [])

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Document Graph</title>
<style>{_CSS}</style>
</head>
<body>
<div class="toolbar">
  <input id="search" type="text" placeholder="開いているカテゴリ内を id / title で検索">
  <button id="refreshBtn" class="refresh-btn" type="button" title="ページを再読み込みして最新の状態を取得します">⟳ 更新</button>
</div>
<main>
{warnings_html}
{treemap_html}
{panels_html}
</main>
<script>
(() => {{
  const boxes = document.querySelectorAll('#treemapSvg rect[data-cat-key]');

  function selectCategory(key) {{
    const panel = document.getElementById('panel-' + key);
    boxes.forEach((b) => {{
      const isSelected = b.dataset.catKey === key;
      b.classList.toggle('tm-active', isSelected);
      b.classList.toggle('tm-dim', !isSelected);
    }});
    document.querySelectorAll('.cat-panel.open').forEach((p) => p.classList.remove('open'));
    if (panel) panel.classList.add('open');
  }}

  function clearCategorySelection() {{
    boxes.forEach((b) => {{ b.classList.remove('tm-active'); b.classList.remove('tm-dim'); }});
    document.querySelectorAll('.cat-panel.open').forEach((p) => p.classList.remove('open'));
  }}

  boxes.forEach((box) => {{
    box.addEventListener('click', () => {{
      const wasOpen = box.classList.contains('tm-active');
      if (wasOpen) {{
        clearCategorySelection();
        return;
      }}
      selectCategory(box.dataset.catKey);
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

document.getElementById('refreshBtn').addEventListener('click', () => location.reload());
</script>
</body>
</html>
"""
