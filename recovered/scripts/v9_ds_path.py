"""業務サービス文書の置き場所を宣言する。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
REF = "DomainSpecSchema/v9"
J = "." + "json"

params = {
    "kindValue": "domain-service",
    "pathVars": {"contextRef": "contextRef", "documentId": "documentId"},
    "path": ".waffle/documents/specs/{contextRef}/domain-service/{documentId}" + J,
    "deploy": [],
}
r = subprocess.run(["uv", "run", "waffle", "patch-schema", "--schemaRef", REF,
                    "--operation", "set_kind_render_target",
                    "--params", json.dumps(params, ensure_ascii=False)],
                   capture_output=True, text=True, cwd=CWD)
print("置き場所を宣言 :", (r.stdout or r.stderr).strip()[:200])

c = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "create",
                    "--schemaRef", "DomainSpecSchema", "--discriminator", "specKind=domain-service",
                    "--documentId", "ds-probe", "--contextRef", "bc-waffle"],
                   capture_output=True, text=True, cwd=CWD)
out = (c.stdout or c.stderr).strip()
print("試しに作る :", out[:180] if '"path"' not in out else "ok")
try:
    d = json.loads(out)
    print("  置き場所 :", d.get("path"))
    print("  ブロック :", list(d["skeleton"]["content"].keys()))
except Exception:
    pass
