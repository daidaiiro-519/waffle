"""書き起こし版に実際どんな中身が入っているかを、種類ごとに標本抽出する。"""
from __future__ import annotations

import glob
import os
import re

ARCHIVE = ("/home/daidaiiro/workspace/waffle/.waffle/skills/ddd-advisor/"
           "references/archive/knowledge-v1-book-transcription")


def blocks(text):
    """```で囲まれた塊を、言語つきで取り出す。"""
    return re.findall(r"```(\w*)\n(.*?)```", text, re.S)


langs = {}
samples = {}
for path in sorted(glob.glob(f"{ARCHIVE}/*.md")):
    name = os.path.basename(path)
    t = open(path, encoding="utf-8").read()
    for lang, body in blocks(t):
        key = lang or "(無指定)"
        langs[key] = langs.get(key, 0) + 1
        if key not in samples:
            samples[key] = (name, body.strip()[:600])

print("── コードブロックの言語別件数 ──")
for k, v in sorted(langs.items(), key=lambda x: -x[1]):
    print(f"  {k:12} {v:4}")

print("\n── 言語ごとの標本 ──")
for k, (name, body) in samples.items():
    print(f"\n■ {k}  [{name}]")
    print(body[:420])
    print("...")
