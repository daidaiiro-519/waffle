"""図の直前に説明文が添えられているかを数える。

図だけが情報を運んでいるなら、読み手は図を描画しないと意味が取れない。
書き起こし版がどうしているかを見て、規則を実物から導く。
"""
from __future__ import annotations

import glob
import os
import re

ARCHIVE = ("/home/daidaiiro/workspace/waffle/.waffle/skills/ddd-advisor/"
           "references/archive/knowledge-v1-book-transcription")

with_prose, without = 0, []
for path in sorted(glob.glob(f"{ARCHIVE}/*.md")):
    name = os.path.basename(path)
    lines = open(path, encoding="utf-8").read().splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("```mermaid"):
            continue
        # 直前の非空行をさかのぼる（見出しに当たったら説明無しとみなす）
        j = i - 1
        prose = None
        while j >= 0:
            s = lines[j].strip()
            if not s:
                j -= 1
                continue
            if s.startswith("#"):
                break
            prose = s
            break
        if prose and not prose.startswith("|") and len(prose) >= 10:
            with_prose += 1
        else:
            heading = next((lines[k].lstrip("#").strip() for k in range(i, -1, -1)
                            if lines[k].startswith("#")), "?")
            without.append((name, heading))

total = with_prose + len(without)
print(f"mermaid の図 {total} 個中、直前に説明文があるもの {with_prose} 個 "
      f"({with_prose * 100 // total}%)\n")
print("── 説明文が見当たらない図 ──")
for name, h in without:
    print(f"  [{name[:26]:26}] {h[:46]}")
