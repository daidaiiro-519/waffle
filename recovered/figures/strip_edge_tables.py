"""図の後ろに置いていた辺の一覧表を、既存アーティファクトから取り除く。

図に書いてあることを文字で書き直しただけの表なので、読み手には何も足していない。
描画側は宣言から落としたが、修正前に組み立てたアーティファクトには残っている。
"""
from __future__ import annotations

import pathlib
import re

HEAD = re.compile(r'<div class="tablewrap"><table><thead><tr>'
                  r'<th>から</th><th>へ</th><th>関係</th>'
                  r'</tr></thead><tbody>.*?</tbody></table></div>', re.S)

# 辺の表を落としたぶん、行数が変わった。実測へ合わせ直す。
COUNTS = {"subdomain": 244, "bounded-context": 178, "domain-model": 360,
          "business-logic-simple": 200, "evolving-design": 255,
          "ubiquitous-language": 214, "design-heuristics": 278}
OLD = {"subdomain": 279, "bounded-context": 191, "domain-model": 382,
       "business-logic-simple": 209, "evolving-design": 277,
       "ubiquitous-language": 240, "design-heuristics": 341}

for name in ("bounded-context", "business-logic-simple", "domain-model", "evolving-design"):
    p = pathlib.Path(f"docs/adr/knowledge-conversion-{name}.html")
    src = p.read_text(encoding="utf-8")
    out, n = HEAD.subn("", src)
    for k, old in OLD.items():
        out = out.replace(f"<td>{old}</td>", f"<td>{COUNTS[k]}</td>")
        out = out.replace(f"<strong>{old}行</strong>", f"<strong>{COUNTS[k]}行</strong>")
        out = out.replace(f'<span class="n">{old}</span>', f'<span class="n">{COUNTS[k]}</span>')
        out = out.replace(f"変換後{old}行", f"変換後{COUNTS[k]}行")
    p.write_text(out, encoding="utf-8")
    print(f"{name}: 辺の表 {n} 件を除いた")