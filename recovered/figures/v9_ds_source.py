"""業務サービス文書の置き場所と、描画先を宣言する。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
REF = "DomainSpecSchema/v9"
J = "." + "json"


def patch(op, params):
    r = subprocess.run(["uv", "run", "waffle", "patch-schema", "--schemaRef", REF,
                        "--operation", op, "--params", json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    out = (r.stdout or r.stderr).strip()
    return "ok" if '"changed"' in out else out[:180]


print("文書の置き場所 :", patch("set_field", {
    "defName": None,
    "fieldPath": "x-source-target.domain-service",
    "value": ".waffle/documents/specs/{contextRef}/domain-service/{documentId}" + J}))

print("描画先 :", patch("set_kind_render_target", {
    "kindValue": "domain-service",
    "pathVars": {"contextRef": "contextRef", "documentId": "documentId"},
    "path": ".waffle/specs/{contextRef}/domain-service/{documentId}.md",
    "deploy": [".waffle/specs/{contextRef}/domain-service/{documentId}.md"]}))

c = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "create",
                    "--schemaRef", "DomainSpecSchema", "--discriminator", "specKind=domain-service",
                    "--documentId", "ds-probe", "--contextRef", "bc-waffle"],
                   capture_output=True, text=True, cwd=CWD)
out = (c.stdout or c.stderr).strip()
try:
    d = json.loads(out)
    print("試しに作る : 置き場所 =", d.get("path"))
except Exception:
    print("試しに作る :", out[:200])
