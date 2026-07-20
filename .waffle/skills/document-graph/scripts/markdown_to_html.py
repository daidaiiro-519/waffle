"""markdown_to_html — Waffle自身（part_renderer.py）が生成するMarkdownの限定語彙
（見出し/段落/箇条書き/テーブル/コードフェンス/水平線/太字/インラインコード）だけを
対象にした、行ベースの最小変換。汎用Markdown方言（脚注・定義リスト等）は扱わない。

tech-lead-advisor助言: Waffleが生成しないMDの語彙を扱う必要が出るまでは、
サードパーティのMarkdownパーサーを依存に追加しない（evidence-based-scope）。
"""
from __future__ import annotations

from html import escape as _e
import re

_HEADING_RE = re.compile(r"^(#{1,6}) (.*)$")
_FENCE_RE = re.compile(r"^```(\w*)$")
_UL_RE = re.compile(r"^- (.*)$")
_OL_RE = re.compile(r"^\d+\. (.*)$")
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
_INLINE_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_INLINE_CODE_RE = re.compile(r"`([^`]+?)`")


def _inline(text: str) -> str:
    """段落・リスト・テーブルセル内のインライン記法（**太字**/`code`）を変換する。
    テキスト自体はHTMLエスケープしつつ、既存の<br>（テーブルのbulletセル）だけは
    生成元のpart_rendererが埋め込む既知のHTML断片として透過させる。"""
    parts = text.split("<br>")
    return "<br>".join(_inline_escape(p) for p in parts)


def _inline_escape(text: str) -> str:
    text = _e(text)
    text = _INLINE_CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _INLINE_BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    return text


def _split_table_row(line: str) -> list[str]:
    inner = line.strip()[1:-1]
    return [cell.strip() for cell in inner.split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-+:?", c) for c in cells)


def _render_table(lines: list[str]) -> str:
    rows = [_split_table_row(line) for line in lines]
    header = rows[0]
    body_rows = rows[2:] if len(rows) > 1 and _is_separator_row(rows[1]) else rows[1:]
    out = ["<table>", "<thead><tr>"]
    for cell in header:
        out.append(f"<th>{_inline(cell)}</th>")
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in body_rows:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{_inline(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return '<div class="table-scroll">' + "".join(out) + "</div>"


def convert(markdown_text: str) -> str:
    """WaffleのMarkdown正本をHTML断片へ変換する。"""
    lines = markdown_text.split("\n")
    out: list[str] = []
    i = 0
    paragraph_buf: list[str] = []

    def flush_paragraph():
        if paragraph_buf:
            out.append(f"<p>{_inline(' '.join(paragraph_buf))}</p>")
            paragraph_buf.clear()

    while i < len(lines):
        line = lines[i]

        fence_m = _FENCE_RE.match(line)
        if fence_m:
            flush_paragraph()
            lang = fence_m.group(1)
            i += 1
            code_lines = []
            while i < len(lines) and lines[i] != "```":
                code_lines.append(lines[i])
                i += 1
            i += 1  # 閉じフェンスを読み飛ばす
            code_text = "\n".join(code_lines)
            if lang == "mermaid":
                out.append(f'<pre class="mermaid">{_e(code_text)}</pre>')
            else:
                out.append(f"<pre><code>{_e(code_text)}</code></pre>")
            continue

        heading_m = _HEADING_RE.match(line)
        if heading_m:
            flush_paragraph()
            level = len(heading_m.group(1))
            out.append(f"<h{level}>{_inline(heading_m.group(2))}</h{level}>")
            i += 1
            continue

        if line.strip() == "---":
            flush_paragraph()
            out.append("<hr>")
            i += 1
            continue

        if _TABLE_ROW_RE.match(line):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and _TABLE_ROW_RE.match(lines[i]):
                table_lines.append(lines[i])
                i += 1
            out.append(_render_table(table_lines))
            continue

        if _UL_RE.match(line):
            flush_paragraph()
            items = []
            while i < len(lines) and _UL_RE.match(lines[i]):
                items.append(_UL_RE.match(lines[i]).group(1))
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ul>")
            continue

        if _OL_RE.match(line):
            flush_paragraph()
            items = []
            while i < len(lines) and _OL_RE.match(lines[i]):
                items.append(_OL_RE.match(lines[i]).group(1))
                i += 1
            out.append("<ol>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ol>")
            continue

        if line.strip() == "":
            flush_paragraph()
            i += 1
            continue

        paragraph_buf.append(line.strip())
        i += 1

    flush_paragraph()
    return "\n".join(out)
