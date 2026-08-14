"""Handoff の完成イメージを、ノードの形に合わせて書く。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = ".waffle/documents/handoff/handoff-array-element-editing." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def n(i, t, s, st):
    return {"id": i, "title": t, "sub": s, "status": st}


LAYERS = [
    {"label": "宣言",
     "nodes": [
         n("key", "鍵の宣言", "どの欄が要素を一意に指すか", "new"),
         n("refs", "参照関係の宣言", "その鍵がどこから指されるか", "new"),
         n("ord", "順序の宣言", "並び全体でひとつの値であること", "new"),
     ],
     "description": "配列ノードごとに Schema へ置く。要素側の共有定義には置かない"
                    "（同じ定義を参照する別の配列まで巻き添えにするため）。"
                    "3つとも記入指示へ抜けるので、書き手にも見える。"},
    {"label": "業務サービス",
     "nodes": [
         n("dspatch", "ds-patch-array-element", "鍵で要素を書き換える写像", "new"),
         n("dscollect", "ds-collect-key-references", "宣言をたどって参照を集める", "new"),
         n("dsdecl", "宣言の読み出し", "3つの宣言を Schema から取り出す", "new"),
     ],
     "description": "どれも agg-document と agg-schema の2つにまたがり、"
                    "どちらの状態も変えない純粋な計算。"
                    "ds-patch-array-element は鍵の指し方の規則が変われば変わり、"
                    "ds-collect-key-references は参照のたどり方が変われば変わるので、分けている。"},
    {"label": "業務ユースケース",
     "nodes": [
         n("ucscaffold", "uc-scaffold-document", "要素操作の受け付けと保存", "existing"),
         n("ucvalidate", "uc-validate-document", "鍵の一意性と宣言の完全性", "existing"),
         n("ucpatch", "uc-patch-schema", "種別の取り消しと互換の関門", "existing"),
         n("uccoverage", "uc-check-criteria-coverage", "参照の欠けの検知", "existing"),
     ],
     "description": "新しい業務ユースケースは立てない。"
                    "uc-scaffold-document の既存の編成（読む→書き込み先を解決する→書く→保存する）を"
                    "要素操作もそのまま使うため、別に立てると同じ編成が3箇所へ複製される。"},
    {"label": "受け口",
     "nodes": [
         n("cli", "CLI", "waffle scaffold --operation add_element 等", "existing"),
         n("mcp", "MCP", "同じ operation を公開する", "existing"),
         n("hook", "先行読み取りの判定", "要素操作は対象外として通す", "existing"),
     ],
     "description": "operation 名と引数を素通しするだけで、判定を持たせない。"
                    "hook だけは engine より手前で止めるため、"
                    "engine が禁じた手順だけを勧めないよう理由の文言を直す。"},
]

REL = [
    {"from": "key", "to": "dspatch", "kind": "uses", "label": "要素を一意に指す"},
    {"from": "key", "to": "ucvalidate", "kind": "uses", "label": "一意性を検査する"},
    {"from": "refs", "to": "dscollect", "kind": "uses", "label": "たどる道"},
    {"from": "refs", "to": "ucvalidate", "kind": "uses", "label": "宣言の欠けを検査する"},
    {"from": "ord", "to": "ucscaffold", "kind": "uses", "label": "要素操作を塞ぐ"},
    {"from": "dsdecl", "to": "dspatch", "kind": "uses", "label": "鍵と固定値"},
    {"from": "dsdecl", "to": "dscollect", "kind": "uses", "label": "参照関係"},
    {"from": "dspatch", "to": "ucscaffold", "kind": "uses", "label": "書き換えた配列"},
    {"from": "dscollect", "to": "ucscaffold", "kind": "uses", "label": "取り下げてよいか"},
    {"from": "dscollect", "to": "uccoverage", "kind": "uses", "label": "指す先が無い参照"},
    {"from": "cli", "to": "ucscaffold", "kind": "uses", "label": "operation を渡す"},
    {"from": "mcp", "to": "ucscaffold", "kind": "uses", "label": "operation を渡す"},
    {"from": "hook", "to": "ucscaffold", "kind": "uses", "label": "手前で通す／止める"},
]

vals = {
    "content.completionImage.layers": LAYERS,
    "content.completionImage.relationships": REL,
}
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:200])
print(run("validate", "--path", P)[:400])
