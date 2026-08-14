"""書き起こし版の見出しが、変換後にどれだけ現れているかを数える。

見出しの語がそのまま残るとは限らない（語彙を揃え、実例を差し替えたため）。
ここで見たいのは、旧要約版にしか無い話を拾っていないか、
書き起こし版の見出しを取りこぼしていないか、の2点。
"""
from __future__ import annotations

import pathlib
import re
import subprocess

A = ".waffle/skills/ddd-advisor/references/archive/knowledge-v1-book-transcription"
DOCS = ["subdomain", "bounded-context", "domain-model", "business-logic-simple",
        "evolving-design", "ubiquitous-language", "design-heuristics",
        "architecture-patterns", "event-sourced-domain-model", "context-integration",
        "communication", "business-domain", "domain-expert", "event-storming",
        "real-world-ddd"]

STOP = re.compile(r"[（(].*?[)）]|[0-9.]+|[・、。「」〜—\s]")

for d in DOCS:
    src = pathlib.Path(f"{A}/{d}.md").read_text(encoding="utf-8")
    new = pathlib.Path(f".waffle/knowledge/ACTIVE/{d}.md").read_text(encoding="utf-8")
    old = subprocess.run(["git", "show", f"HEAD:.waffle/knowledge/ACTIVE/{d}.md"],
                         capture_output=True, text=True).stdout

    heads = [STOP.sub("", h) for h in re.findall(r"^#{2,3} (.+)$", src, re.M)]
    heads = [h for h in heads if h and h not in ("概要", "定義", "関連概念",
                                                 "判断基準", "アンチパターン", "構造",
                                                 "具体例", "役割", "重要な注意")]
    # 見出しの語幹（先頭4文字）が変換後に現れるか
    hit = [h for h in heads if h[:4] in STOP.sub("", new)]
    miss = [h for h in heads if h[:4] not in STOP.sub("", new)]
    # 旧要約版にしか無い節（＝書き起こし版に無いのに変換後にある見出し）
    new_heads = [STOP.sub("", h) for h in re.findall(r"^#{3,5} (.+)$", new, re.M)]
    src_flat = STOP.sub("", src)
    invented = [h for h in new_heads
                if h[:4] not in src_flat and h not in ("この概念が答える判断", "留保事項")]
    print(f"{d:30} 書起し見出し {len(heads):2}件中 {len(hit):2}件を反映"
          f" / 書起しに無い見出し {len(invented)}件"
          + (f"  → {invented}" if invented else ""))
    if miss:
        print(f"{'':30}   反映が確認できず: {miss}")