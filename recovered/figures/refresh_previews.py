"""既存アーティファクトの完全プレビューを、いまの描画物から作り直す。

注釈を足したので、プレビューが古いままだと成果物と食い違う。
手で書き写すと取りこぼすため、描画物から機械で作り直す。
"""
from __future__ import annotations

import pathlib
import re
import subprocess

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
COUNTS = {"bounded-context": 189, "business-logic-simple": 206,
          "domain-model": 376, "evolving-design": 271}
OLD = {"bounded-context": 178, "business-logic-simple": 200,
       "domain-model": 360, "evolving-design": 255}
ALL_NEW = {"subdomain": 268, "bounded-context": 189, "domain-model": 376,
           "business-logic-simple": 206, "evolving-design": 271,
           "ubiquitous-language": 231, "design-heuristics": 310}
ALL_OLD = {"subdomain": 244, "bounded-context": 178, "domain-model": 360,
           "business-logic-simple": 200, "evolving-design": 255,
           "ubiquitous-language": 214, "design-heuristics": 278}

BODY = re.compile(r'(<div class="doc-body">\n\n).*?(\n\n    </div>)', re.S)

for name in COUNTS:
    frag = subprocess.run(["python3", f"{S}/md_to_preview.py",
                           f".waffle/knowledge/ACTIVE/{name}.md"],
                          capture_output=True, text=True,
                          cwd="/home/daidaiiro/workspace/waffle").stdout
    p = pathlib.Path(f"docs/adr/knowledge-conversion-{name}.html")
    t = p.read_text(encoding="utf-8")
    t, n = BODY.subn(lambda m: m.group(1) + frag + m.group(2), t)
    for k, old in ALL_OLD.items():
        t = t.replace(f"<td>{old}</td>", f"<td>{ALL_NEW[k]}</td>")
        t = t.replace(f"<strong>{old}行</strong>", f"<strong>{ALL_NEW[k]}行</strong>")
        t = t.replace(f'<span class="n">{old}</span>', f'<span class="n">{ALL_NEW[k]}</span>')
        t = t.replace(f"変換後{old}行", f"変換後{ALL_NEW[k]}行")
    p.write_text(t, encoding="utf-8")
    print(f"{name}: プレビューを差し替えた（{n}箇所）/ 注釈の表 "
          f"{frag.count('図に載せきれないこと')} 件")