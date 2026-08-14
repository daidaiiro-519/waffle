"""bc-waffle の7つのサブドメインについて、分類・ユースケース数・扱う対象を並べる。"""
from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(".waffle/documents/specs/bc-waffle/subdomain")


def q(path, block=None, expr="@"):
    a = ["uv", "run", "waffle", "query", "--operation", "query_path", "--path", str(path)]
    if block:
        a += ["--blockKey", block]
    a += ["--expression", expr]
    r = subprocess.run(a, capture_output=True, text=True, cwd="/home/daidaiiro/workspace/waffle")
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


for sd in sorted(ROOT.iterdir()):
    if not sd.is_dir():
        continue
    doc = sd / (sd.name + ".json")
    if not doc.exists():
        cand = [p for p in sd.glob("*.json")]
        doc = cand[0] if cand else None
    ucs = sorted((sd / "usecase").glob("*.json")) if (sd / "usecase").exists() else []
    kind = ver = title = "?"
    if doc:
        d = q(doc)
        if d:
            for b in d.get("results", []):
                v = b.get("value", {})
                if b["blockKey"] == "title":
                    title = v.get("title", "?")
                if b["blockKey"] in ("classification", "category", "subdomainKind"):
                    kind = json.dumps(v, ensure_ascii=False)[:90]
    print(f"\n■ {sd.name}   ユースケース {len(ucs)}件")
    print(f"  文書: {doc.name if doc else '(無し)'}")
    print(f"  表題: {title}")
    for u in ucs:
        print(f"    - {u.stem}")