"""描画済みの knowledge の .md から、アーティファクト用のプレビュー断片を組み立てる。

手で書き写すと抜けるので、実際の描画物から機械で生成する。
"""
from __future__ import annotations

import html
import re
import sys

SRC = sys.argv[1]
lines = open(SRC, encoding="utf-8").read().splitlines()

# ノードの木は "## <ブロック名>" 以降。それより前は概要・出典・関連。
start = next(i for i, s in enumerate(lines) if s.startswith("## ") and i > 40)
body = lines[start + 1:]

out: list[str] = []
depth_class = {3: "", 4: " d2", 5: " d3"}
open_depth: list[int] = []
buf: list[str] = []
mode = None          # None / "mermaid" / "table"
fence_lang = ""


def flush_paras():
    """溜めた本文を段落・図・表として吐き出す。"""
    global buf
    text = "\n".join(buf).strip()
    buf = []
    if not text:
        return
    for chunk in re.split(r"\n\s*\n", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk.startswith("|"):
            rows = [r for r in chunk.splitlines() if r.startswith("|")]
            if len(rows) < 2:
                continue
            head = [c.strip() for c in rows[0].strip("|").split("|")]
            out.append('<div class="tablewrap"><table><thead><tr>'
                       + "".join(f"<th>{html.escape(c)}</th>" for c in head)
                       + "</tr></thead><tbody>")
            for r in rows[2:]:
                cells = [c.strip() for c in r.strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>")
            out.append("</tbody></table></div>")
        else:
            out.append(f"<p>{html.escape(chunk)}</p>")


for raw in body:
    m = re.match(r"^(#{3,5}) (.+)$", raw)
    if m and mode is None:
        flush_paras()
        d = len(m.group(1))
        while open_depth and open_depth[-1] >= d:
            out.append("</div>")
            open_depth.pop()
        out.append(f'<div class="node{depth_class.get(d, "")}">'
                   f'<div class="node-h"><span class="nm">{html.escape(m.group(2))}</span></div>')
        open_depth.append(d)
        continue
    if raw.startswith("```"):
        if mode is None:
            flush_paras()
            fence_lang = raw[3:].strip()
            mode = "fence"
            buf = []
        else:
            code = html.escape("\n".join(buf))
            cls = ' class="mermaid"' if fence_lang == "mermaid" else ""
            out.append(f'<div class="blk"><pre{cls}>\n{code}\n</pre></div>')
            buf = []
            mode = None
        continue
    buf.append(raw)

flush_paras()
while open_depth:
    out.append("</div>")
    open_depth.pop()

print("\n".join(out))
