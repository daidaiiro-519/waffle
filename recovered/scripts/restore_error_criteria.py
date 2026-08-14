"""落としたエラー契約の主張を、受け入れ基準として起こし直す。

errors ブロックは条件の一覧であって主張ではないため、
「〜のとき CODE を返す shall」は受け入れ基準に属する。
"""
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


def cid(code: str) -> str:
    return code.lower().replace("_", "-")


with open(SRC, encoding="utf-8") as f:
    dump = json.load(f)

for name, v in dump["usecases"].items():
    path = v["path"]
    moved = [(g if isinstance(g, str) else g.get("text", "")) for g in v["guarantees"]
             if CODE.search(g if isinstance(g, str) else g.get("text", ""))]
    if not moved:
        continue

    crit = q(path, "acceptanceCriteria", "items") or []
    is_v9 = bool(crit) and isinstance(crit[0], dict)
    have = {c["id"] for c in crit} if is_v9 else set()
    have_text = {(c if isinstance(c, str) else c["text"]) for c in crit}

    scen = q(path, "acceptanceScenarios", "scenarios") or []
    added = 0
    for t in moved:
        if t in have_text:
            continue
        code = CODE.search(t).group()
        i = cid(code)
        while i in have:
            i += "-2"
        crit.append({"id": i, "text": t} if is_v9 else t)
        have.add(i)
        cond = re.sub(r"^(When|While|If)\s*", "",
                      re.split(r"、\s*システムは|、\s*Check[A-Za-z]+は", t)[0]).strip("。 ")
        s = {"name": f"{cond[:40]}のとき{code}",
             "category": "異常系",
             "viewpoint": f"エラー：{cond[:60]}",
             "gherkin": f"Scenario: {cond[:40]}のとき{code}\n  Given {cond}状況\n"
                        f"  When 本ユースケースを実行する\n  Then {code} エラーが返る"}
        s["satisfies" if is_v9 else "covers"] = [i] if is_v9 else f"エラー: {code}"
        scen.append(s)
        added += 1

    if not added:
        continue
    out = run("scaffold", "--operation", "fill", "--path", path,
              "--values", json.dumps({"content.acceptanceCriteria.items": crit,
                                      "content.acceptanceScenarios.scenarios": scen},
                                     ensure_ascii=False))
    ver = run("validate", "--path", path)
    ok = '"VALIDATED"' in ver
    print(f"  {name:38} 基準へ {added} 件  {'OK' if ok else ver[:120]}")
