"""1文書の中で、同じ見出しが繰り返されているかを見る。

繰り返されているなら、その文書は「1つの概念＋固定ブロック」ではなく
「複数の下位概念が、それぞれ同じ形の中身を持つ木」である。
"""
from __future__ import annotations

import glob
import os
import re
from collections import Counter

ARCHIVE = ("/home/daidaiiro/workspace/waffle/.waffle/skills/ddd-advisor/"
           "references/archive/knowledge-v1-book-transcription")

total_rep = 0
for path in sorted(glob.glob(f"{ARCHIVE}/*.md")):
    name = os.path.basename(path)
    heads = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("#"):
            h = re.sub(r"[（(]?\d+(\.\d+)*[）)]?\s*$", "", line.lstrip("#").strip()).strip()
            if h:
                heads.append(h)
    c = Counter(heads)
    rep = {h: n for h, n in c.items() if n >= 2}
    if not rep:
        continue
    total_rep += 1
    top = sorted(rep.items(), key=lambda x: -x[1])[:4]
    print(f"■ {name:32} 見出し{len(heads):3}件中、繰り返し{len(rep)}種")
    for h, n in top:
        print(f"      {n}回  {h[:52]}")

print(f"\n繰り返しのある文書: {total_rep} / 19本")

# 第2階層（##）の直下に何個の第3階層（###）がぶら下がるか
print("\n── 親見出しの下にぶら下がる子の数（上位10）──")
rows = []
for path in sorted(glob.glob(f"{ARCHIVE}/*.md")):
    name = os.path.basename(path)
    cur, cnt = None, 0
    for line in open(path, encoding="utf-8"):
        if line.startswith("### "):
            cnt += 1
        elif line.startswith("## "):
            if cur and cnt:
                rows.append((cnt, name, cur))
            cur, cnt = line.lstrip("#").strip(), 0
    if cur and cnt:
        rows.append((cnt, name, cur))
for n, name, h in sorted(rows, reverse=True)[:10]:
    print(f"  {n:2}個  [{name[:24]:24}] {h[:40]}")
