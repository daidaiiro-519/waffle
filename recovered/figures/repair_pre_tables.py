"""既存アーティファクトの中で、表がコード塊に閉じ込められている箇所を表へ戻す。

描画の修正はドキュメント側にしか効かないので、修正前に組み立てた
アーティファクトは古い見え方のまま残る。同型の箇所を横断で直す。
"""
from __future__ import annotations

import html
import pathlib
import re


def to_table(md: str) -> str:
    rows = [r.strip() for r in md.strip().splitlines() if r.strip()]
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
    head, body = cells[0], cells[2:]          # 2行目は区切り
    th = "".join(f"<th>{html.escape(c)}</th>" for c in head)
    tb = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>"
                 for r in body)
    return f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>'


for name in ("domain-model", "evolving-design"):
    p = pathlib.Path(f"docs/adr/knowledge-conversion-{name}.html")
    src = p.read_text(encoding="utf-8")
    n = 0

    def sub(m):
        global n
        inner = html.unescape(m.group(1)).strip()
        if not inner.startswith("|"):
            return m.group(0)
        n += 1
        return to_table(inner)

    out = re.sub(r"<pre[^>]*>(.*?)</pre>", sub, src, flags=re.S)
    p.write_text(out, encoding="utf-8")
    print(f"{name}: {n}件を表へ戻した")