"""エラー契約の操作保証を、errors ブロックへ移す（未登録のものだけ足し、保証からは外す）。"""
from __future__ import annotations

import json
import re
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SRC = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
       "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad/guarantees_dump." + "json")
CODE = re.compile(r"[A-Z]{3,}(?:_[A-Z]+)+")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(p, b, e):
    try:
        return json.loads(run("query", "--operation", "query_path", "--path", p,
                              "--blockKey", b, "--expression", e))["value"]
    except Exception:
        return None


def condition_of(text: str) -> str:
    """『〜のとき、システムは…』の前半を、エラーの条件として取り出す。"""
    head = re.split(r"、\s*システムは|、\s*Check[A-Za-z]+は", text)[0]
    return re.sub(r"^(When|While|If)\s*", "", head).strip("。 ")


with open(SRC, encoding="utf-8") as f:
    dump = json.load(f)

added = dropped = 0
for name, v in dump["usecases"].items():
    path = v["path"]
    keep, moving = [], []
    for g in v["guarantees"]:
        t = g if isinstance(g, str) else g.get("text", "")
        m = CODE.findall(t)
        (moving if m else keep).append((g, t, m[0] if m else None))
    move = [x for x in moving if x[2]]
    if not move:
        continue

    errors = q(path, "errors", "items") or []
    have = {e["code"] for e in errors}
    for _, t, code in move:
        if code not in have:
            errors.append({"code": code, "condition": [condition_of(t)]})
            have.add(code)
            added += 1
        dropped += 1

    # 保証からエラー契約を外し、対応する保証シナリオも外す
    kept_g = [g for g, _, code in [(a, b, c) for a, b, c in moving if not c]] + [g for g, _, _ in
                                                                                 [(a, b, c) for a, b, c in
                                                                                  [(x[0], x[1], x[2]) for x in keep]]]
    kept_g = [g for g, _, _ in keep]
    codes_moved = {c for _, _, c in move}
    gs = [s for s in (q(path, "guaranteeScenarios", "scenarios") or [])
          if not (CODE.findall(s.get("gherkin", "") + s.get("name", "")) and
                  set(CODE.findall(s.get("gherkin", "") + s.get("name", ""))) & codes_moved)]

    vals = {"content.errors.items": errors,
            "content.operationGuarantees.items": kept_g,
            "content.guaranteeScenarios.scenarios": gs}
    out = run("scaffold", "--operation", "fill", "--path", path,
              "--values", json.dumps(vals, ensure_ascii=False))
    ok = '"written"' in out
    ver = run("validate", "--path", path)
    status = "OK" if '"VALIDATED"' in ver else (out[:80] + " / " + ver[:140])
    print(f"  {name:38} 移した {len(move)} 件  {status}")
    if '"VALIDATED"' in ver:
        run("render", "--path", path)

print(f"\nerrors へ新規登録 {added} 件 / 保証から外した {dropped} 件")
