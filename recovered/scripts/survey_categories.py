"""7つのサブドメインの分類と根拠を並べる。細分化が分類を変えているかを見る。"""
from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(".waffle/documents/specs/bc-waffle/subdomain")

for sd in sorted(ROOT.iterdir()):
    doc = sd / (sd.name + ".json")
    if not doc.exists():
        continue
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", str(doc), "--expression", "@"],
                       capture_output=True, text=True, cwd="/home/daidaiiro/workspace/waffle")
    blocks = {b["blockKey"]: b["value"] for b in json.loads(r.stdout)["results"]}
    cat = blocks.get("category", {})
    mem = blocks.get("members", {}).get("items", [])
    print(f"\n■ {sd.name}  [{cat.get('classification', '?')}]  ユースケース {len(mem)}件")
    for rr in cat.get("rationale", []):
        print(f"   根拠: {rr}")