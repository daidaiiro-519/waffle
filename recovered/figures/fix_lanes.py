"""2つの経路を使い分ける宣言を、UDDループの中で判断する形へ直す。

名前が付かないこと自体が、分ける必要が無いことの合図だった。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = ".waffle/documents/agent/waffle." + "json"


def q(block, expr):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", P, "--blockKey", block, "--expression", expr],
                       capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(values):
    r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill", "--path", P,
                        "--values", json.dumps(values, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=CWD)
    print((r.stdout or r.stderr).strip()[:160])


rules = q("operatingRules", "items")
for x in rules:
    if "フルサイクル" in x.get("rule", ""):
        x["rule"] = (
            "作業は UDDループ（調べる→決める→引き継ぐ→作る）を通す。"
            "どこまで踏むかはその都度判断する——"
            "新規capability・挙動変更・schema変更を伴うなら4段とも踏み、"
            "単一フィールド修正・機械的な文言変換・調査単体なら決めることが無いので段は薄くなる。")
        x["why"] = (
            "経路を2つ用意して先に選ばせると、『どちらの道か』という判断が本来の判断の前に増える。"
            "しかも一方の名前が付けられなかった——"
            "自然な名前が付かないのは、分ける必要が無いことの合図である。"
            "1本のループに寄せても判断は無くならず、"
            "spec合意前の実装（既知の再発パターン）と、軽微な修正への過剰な儀式化の"
            "どちらへ振れるかを、その都度測ることになる。")
        x["howToApply"] = (
            "境界事例（例：複数フィールドにまたがるが挙動は変わらない修正）は judgmentTasks の基準に従う。"
            "迷ったら『決めることがあるか』を先に問う——"
            "決めることがあるなら、決める段と引き継ぐ段を省かない。")
fill({"content.operatingRules.items": rules})

jt = q("judgmentTasks", "items")
for x in jt:
    s = json.dumps(x, ensure_ascii=False)
    if "フルサイクル" in s or "直行レーン" in s:
        x["situation"] = "作業が UDDループ のどの段まで踏むべきか自明でないとき"
        x["criteria"] = (
            "「振る舞いが変わるか」「将来同種の判断が繰り返されるか」のいずれかが Yes なら4段とも踏む。"
            "両方 No なら、決めることが無いので決める段と引き継ぐ段は薄くてよい。")
        x["reason"] = (
            "段の踏み方を宣言だけで割り切れないため、最終判断は Orchestrator 自身に残す。")
fill({"content.judgmentTasks.items": jt})

for cmd in (["validate", "--path", P], ["render", "--path", P]):
    r = subprocess.run(["uv", "run", "waffle", *cmd], capture_output=True, text=True, cwd=CWD)
    print(cmd[0], ":", (r.stdout or r.stderr).strip()[:130])
