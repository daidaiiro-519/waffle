"""書き起こし版19本が、実際にどんな種類の中身でできているかを数える。

器を先に決めず、実物の見出しを集めて分類する。分類に落ちないものは
「まだ名前が無い種類」として残し、そこから器の語彙を導く。
"""
from __future__ import annotations

import glob
import os
import re
from collections import Counter, defaultdict

ARCHIVE = ("/home/daidaiiro/workspace/waffle/.waffle/skills/ddd-advisor/"
           "references/archive/knowledge-v1-book-transcription")

BUCKET = [
    ("定義", r"^定義$|とは$|の定義"),
    ("分類", r"分類|3つの|種類"),
    ("判断基準", r"判断基準|基準$|選び方|使い分け"),
    ("図表", r"^図\d|（図\d"),
    ("具体例", r"具体例|^例|の例$|ケース"),
    ("比較", r"比較|対比|違い"),
    ("手順", r"手順|ステップ|方法|やり方|進め方|する（\d|を特定|を調べる|を評価"),
    ("実装", r"実装|コード|クラス|インターフェース|関数|スキーマ"),
    ("利点欠点", r"利点|欠点|メリット|デメリット|長所|短所|トレードオフ"),
    ("アンチパターン", r"アンチパターン|よくある誤り|失敗"),
    ("関連概念", r"関連概念|関連$"),
    ("用語", r"用語|補足|訳語"),
    ("なぜ", r"^なぜ|理由|背景|動機"),
]

counts = Counter()
by_bucket = defaultdict(list)
unmatched = []
per_file = {}

for path in sorted(glob.glob(f"{ARCHIVE}/*.md")):
    name = os.path.basename(path)
    heads = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("#"):
            continue
        h = line.lstrip("#").strip()
        if h:
            heads.append(h)
    per_file[name] = len(heads)
    for h in heads:
        # 章節番号を落として本体だけ見る
        core = re.sub(r"[（(]?\d+(\.\d+)*[）)]?\s*$", "", h).strip()
        core = re.sub(r"^\d+(\.\d+)*\s*", "", core).strip()
        hit = None
        for label, pat in BUCKET:
            if re.search(pat, core):
                hit = label
                break
        if hit:
            counts[hit] += 1
            by_bucket[hit].append(core)
        else:
            unmatched.append((name, core))

print(f"見出し総数 {sum(per_file.values())} 件 / 19本\n")
print("── 種類ごとの件数 ──")
for label, _ in BUCKET:
    if counts[label]:
        print(f"  {label:12} {counts[label]:4}")
print(f"  {'どれにも落ちない':12} {len(unmatched):4}")

print("\n── どれにも落ちない見出し（先頭40件）──")
for name, h in unmatched[:40]:
    print(f"  [{name[:22]:22}] {h[:58]}")
