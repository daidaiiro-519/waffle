"""業務サービスの文書を1件作るための共通手順。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def create(doc_id: str, values: dict) -> None:
    path = f".waffle/documents/specs/bc-waffle/domain-service/{doc_id}." + "json"
    out = run("scaffold", "--operation", "create", "--schemaRef", "DomainSpecSchema",
              "--discriminator", "specKind=domain-service",
              "--documentId", doc_id, "--contextRef", "bc-waffle")
    if '"skeleton"' not in out:
        print(f"  [{doc_id}] 作成できず: {out[:120]}")
        return
    values = {"status": "CREATED", "tags": ["framework:waffle"], **values}
    f = run("scaffold", "--operation", "fill", "--path", path,
            "--values", json.dumps(values, ensure_ascii=False))
    if '"written"' not in f:
        print(f"  [{doc_id}] 書き込めず: {f[:160]}")
        return
    v = run("validate", "--path", path)
    ok = '"VALIDATED"' in v
    print(f"  [{doc_id}] {'検証を通過' if ok else v[:180]}")
    if ok:
        run("render", "--path", path)
