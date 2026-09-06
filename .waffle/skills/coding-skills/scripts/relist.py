# -*- coding: utf-8 -*-
"""規則の一覧を、詳細の塊から書き出す。

  python3 scripts/relist.py            書き出す
  python3 scripts/relist.py --check    書き出したものと正本が一致するかを見る

**一覧は導出物である。**手で書くと、詳細と食い違う ──
実際に、一覧と詳細の両方に在る欄105件のうち36件で値が食い違っていた。
写しを作ってから写しのずれを守る検査を足すより、写しを作らないほうが短い。

芯（ID・言明・検証方法）と出典は、規則の塊と `## 出典` に1つずつ在る。
一覧が持つのは、その塊から取れる短い欄だけである。
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import ROOT, load_all, load_templates, sections, tables  # noqa: E402

def shape(kind: str):
    """一覧の（節の名前, 言明の呼び名, 残りの列）を、その種別の雛形から読む。

    **列をここに書き写さない。**宣言しているのは雛形の一覧の表である。
    """
    tpl = load_templates().get(kind)
    if not tpl:
        return None
    for name, body in sections(tpl).items():
        for tb in tables(body):
            if tb.has("ID") and len(tb.columns) >= 2:
                return name, tb.columns[1], tb.columns[2:]
    return None


def details(body: str) -> list[tuple[str, str, dict]]:
    """### ID　言明 の塊を、(ID, 言明, 欄) で返す。"""
    out = []
    for m in re.finditer(r"^### ([A-Z][A-Z0-9-]+)　(.*)$", body, re.M):
        nxt = re.search(r"^(### |## )", body[m.end():], re.M)
        blk = body[m.end():m.end() + (nxt.start() if nxt else len(body))]
        head = blk.index("| 項目 | 内容 |")
        end = blk.index("\n\n", head)
        fields = dict(re.findall(r"^\| ([^|]+?) \| (.+?) \|$", blk[head:end], re.M))
        fields.pop("項目", None)
        out.append((m.group(1), m.group(2), fields))
    return out


def table_for(spec) -> str | None:
    """その規約の一覧を、詳細から組み立てる。"""
    sh = shape(spec.kind)
    if not sh:
        return None
    _, stmt, cols = sh
    rows = details(spec.body)
    if not rows:
        return None
    head = "| ID | " + stmt + " | " + " | ".join(cols) + " |\n"
    head += "|---|---|" + "---|" * len(cols) + "\n"
    for rid, title, f in rows:
        head += (f"| {rid} | {title} | "
                 + " | ".join(f.get(c, "─") for c in cols) + " |\n")
    return head


def apply(spec, table: str) -> str | None:
    """一覧の節の表を差し替える。変わらなければ None。"""
    sh = shape(spec.kind)
    if not sh:
        return None
    name = sh[0]
    m = re.search(rf"^## {re.escape(name)}\n\n", spec.body, re.M)
    if not m:
        return None
    end = spec.body.index("\n\n", m.end())
    if spec.body[m.end():end + 1] == table:
        return None
    return spec.body[:m.end()] + table + spec.body[end + 1:]


def main() -> int:
    check = "--check" in sys.argv
    bad, wrote = [], 0
    for s in load_all():
        table = table_for(s)
        if not table:
            continue
        new = apply(s, table)
        if new is None:
            continue
        if check:
            bad.append(f"{s.where}: 一覧が詳細と食い違う")
            continue
        path = ROOT / s.where
        head = path.read_text(encoding="utf-8")
        front = head[:head.index("\n---\n") + 5] if head.startswith("---\n") else ""
        path.write_text(front + new, encoding="utf-8")
        wrote += 1
    if check:
        print(f"一覧を持つ規約を、詳細から組み直して比べた ── "
              f"食い違い {len(bad)} 件")
        for b in bad:
            print("  " + b)
        return 1 if bad else 0
    print(f"{wrote} 本の一覧を、詳細から書き出した")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
