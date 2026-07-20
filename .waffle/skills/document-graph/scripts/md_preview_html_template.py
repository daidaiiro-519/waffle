"""md_preview_html_template — 「全体」タブがMD形式ソースを表示するときに使うテンプレート。

Waffle本体の src/waffle/domain/services/document_viewer_html_template.py を移植した
（CSS・レイアウトは無変更）。差分は masthead の識別情報のみ: 元はWaffle固有の
schemaRef/updatedAtを表示していたが、契約にその2項目は無いため、契約が実際に持つ
`type`で置き換えた（documentId相当のid欄は維持）。見た目・構造はそれ以外すべて同一。
"""
from __future__ import annotations

from html import escape as _e

_CSS = """
@font-face { font-family: "Ledger Slab"; src: local("Roboto Slab"), local("Georgia"); }
:root {
  --paper: #f3f1ec; --ink: #23241f; --ink-dim: #63645a; --ink-faint: #8c8d80;
  --line: #ddd9cd; --surface: #ffffff; --surface-sunken: #faf9f5;
  --accent: #2f5c46; --accent-soft: #e6f0ea; --accent-ink: #ffffff;
  --shadow: 0 1px 2px rgba(35,36,31,0.04), 0 4px 14px rgba(35,36,31,0.05);
  --mono: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;
  --sans: -apple-system, "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif;
  --serif: "Ledger Slab", "Hiragino Mincho ProN", Georgia, serif;
}
:root[data-theme="dark"] {
  --paper: #1b1c18; --ink: #eceae2; --ink-dim: #b0af9f; --ink-faint: #7c7b6d;
  --line: #37382f; --surface: #232420; --surface-sunken: #1f201c;
  --accent: #82c4a4; --accent-soft: #1c332a; --accent-ink: #14211b;
  --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 6px 18px rgba(0,0,0,0.25);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #1b1c18; --ink: #eceae2; --ink-dim: #b0af9f; --ink-faint: #7c7b6d;
    --line: #37382f; --surface: #232420; --surface-sunken: #1f201c;
    --accent: #82c4a4; --accent-soft: #1c332a; --accent-ink: #14211b;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 6px 18px rgba(0,0,0,0.25);
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--sans); line-height: 1.75; -webkit-font-smoothing: antialiased; overflow-x: hidden; }
.wrap { max-width: 760px; margin: 0 auto; padding: 3rem 1.5rem 6rem; }
header.masthead { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: var(--shadow); padding: 1.6rem 1.8rem; margin-bottom: 2rem; }
.masthead .kicker { font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-faint); }
.masthead h1 { font-family: var(--serif); font-size: clamp(1.4rem, 3.2vw, 1.9rem); font-weight: 600; margin: 0.35rem 0 0.9rem; text-wrap: balance; }
.meta-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.9rem; }
.tag-pill { font-family: var(--mono); font-size: 0.72rem; padding: 0.2rem 0.65rem; border-radius: 999px; background: var(--accent-soft); color: var(--accent); border: 1px solid var(--line); }
.masthead dl { display: grid; grid-template-columns: auto 1fr; gap: 0.25rem 1rem; font-family: var(--mono); font-size: 0.76rem; color: var(--ink-faint); border-top: 1px solid var(--line); padding-top: 0.8rem; }
.masthead dt { white-space: nowrap; }
.masthead dd { margin: 0; color: var(--ink-dim); overflow-wrap: anywhere; }
.masthead .description { color: var(--ink-dim); margin: 0 0 0.9rem; max-width: 68ch; overflow-wrap: anywhere; }
article { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: var(--shadow); padding: 2rem 2.2rem 2.4rem; }
article h1 { font-family: var(--serif); font-size: clamp(1.3rem, 3vw, 1.7rem); margin: 0 0 1rem; }
article h2 { font-family: var(--mono); font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); margin: 2.2rem 0 0.9rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--line); }
article > h2:first-of-type, article > h1:first-child + h2 { margin-top: 0; }
article h3 { font-family: var(--serif); font-size: 1.05rem; font-weight: 600; color: var(--ink); margin: 1.4rem 0 0.6rem; }
article p { margin: 0 0 0.9rem; max-width: 68ch; overflow-wrap: anywhere; }
article ul, article ol { margin: 0 0 0.9rem; padding-left: 1.3rem; max-width: 68ch; }
article li { margin-bottom: 0.35rem; overflow-wrap: anywhere; }
article strong { color: var(--ink); }
.table-scroll { overflow-x: auto; margin-bottom: 1.2rem; }
article table { border-collapse: collapse; width: 100%; min-width: max-content; font-size: 0.9rem; }
article th, article td { text-align: left; padding: 0.55rem 0.9rem; border-bottom: 1px solid var(--line); vertical-align: top; overflow-wrap: anywhere; }
article th { font-family: var(--mono); font-size: 0.82rem; letter-spacing: 0.03em; text-transform: uppercase; color: var(--ink-faint); font-weight: 600; border-bottom: 1.5px solid var(--ink-faint); }
article tr:last-child td { border-bottom: none; }
article code { font-family: var(--mono); font-size: 0.87em; background: var(--surface-sunken); border: 1px solid var(--line); border-radius: 4px; padding: 0.08em 0.4em; }
article pre { font-family: var(--mono); font-size: 0.83rem; line-height: 1.65; background: var(--surface-sunken); border: 1px solid var(--line); border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0 0 1.2rem; overflow-x: auto; white-space: pre-wrap; }
article pre code { background: none; border: none; padding: 0; }
article pre.mermaid { text-align: center; background: var(--surface-sunken); }
article pre.mermaid svg { max-width: 100%; }
article hr { border: none; border-top: 1px solid var(--line); margin: 1.8rem 0; }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""


def _render_tags(tags: list[str]) -> str:
    return "".join(f'<span class="tag-pill">{_e(t)}</span>' for t in tags)


def _render_dl_rows(document_id: str, schema_ref: str, updated_at: str) -> str:
    """Waffle本体のdocumentId/schemaRef/updatedAtと同じ3行構成。schemaRef/updatedAtは
    frontmatterに値がある場合のみ行を出す（Waffle製documentは常に一致、それ以外の
    起源のMDでは存在しない属性なので省略する——x-frontmatterの空値省略規約と同じ扱い）。"""
    rows = [f"<dt>documentId</dt><dd>{_e(document_id)}</dd>"]
    if schema_ref:
        rows.append(f"<dt>schemaRef</dt><dd>{_e(schema_ref)}</dd>")
    if updated_at:
        rows.append(f"<dt>updatedAt</dt><dd>{_e(updated_at)}</dd>")
    return "".join(rows)


def render_preview_html(
    title: str,
    document_id: str,
    tags: list[str],
    description: str,
    body_html: str,
    schema_ref: str = "",
    updated_at: str = "",
) -> str:
    """MDから変換した本文HTMLを、Waffle本体のuc-render-document-viewerと同一構成の
    masthead（documentId/schemaRef/updatedAt）付き自己完結HTMLへ組み立てる。"""
    description_html = f'<p class="description">{_e(description)}</p>' if description else ""
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{_e(title)}</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div class="kicker">Document Preview</div>
    <h1>{_e(title)}</h1>
    {description_html}
    <div class="meta-row">
      {_render_tags(tags)}
    </div>
    <dl>
      {_render_dl_rows(document_id, schema_ref, updated_at)}
    </dl>
  </header>
  <article>
{body_html}
  </article>
</div>
<script>mermaid.initialize({{startOnLoad: true}});</script>
</body>
</html>
"""
