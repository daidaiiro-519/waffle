"""書き起こし版の見出しが、要約版のどこにも見当たらないものを洗い出す。

見出しの語が要約版の本文に一度も現れないものを「落ちた候補」として挙げる。
語の一致で見るだけなので、これは判定ではなく当たりを付けるための一覧。
"""
from __future__ import annotations

import glob
import os
import re

BASE = "/home/daidaiiro/workspace/waffle"
ARCHIVE = f"{BASE}/.waffle/skills/ddd-advisor/references/archive/knowledge-v1-book-transcription"
SUMMARY = f"{BASE}/.claude/skills/ddd-advisor/references/knowledge"

# 器（KnowledgeSchema）のブロックに素直に対応する見出しは、対応先があるので除く
CONTAINER = re.compile(r"定義|分類|判断基準|アンチパターン|関連概念|概要|原則|実例|出典")


def words(text: str) -> set:
    return set(re.findall(r"[ぁ-んァ-ヶ一-龠A-Za-z]{2,}", text))


rows = []
for path in sorted(glob.glob(f"{ARCHIVE}/*.md")):
    name = os.path.basename(path)
    dst = f"{SUMMARY}/{name}"
    if not os.path.exists(dst):
        rows.append((name, ["（要約版が存在しない）"]))
        continue
    summary = open(dst, encoding="utf-8").read()
    sw = words(summary)

    missing = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("#"):
            continue
        head = line.lstrip("#").strip()
        if not head or CONTAINER.search(head):
            continue
        # 見出しの語のうち、要約版に一度も現れないものが半分を超えたら落ちた候補
        hw = [w for w in words(head) if len(w) >= 2]
        if not hw:
            continue
        unseen = [w for w in hw if w not in sw]
        if len(unseen) >= max(1, len(hw) // 2):
            missing.append(head)
    if missing:
        rows.append((name, missing))

total = sum(len(m) for _, m in rows)
print(f"落ちた候補のある knowledge: {len(rows)} / 19本   候補の見出し 計 {total} 件\n")
for name, missing in sorted(rows, key=lambda r: -len(r[1])):
    print(f"■ {name}  ({len(missing)}件)")
    for m in missing:
        print(f"    {m}")
    print()
