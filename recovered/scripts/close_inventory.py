"""棚卸しの引き継ぎ文書を閉じる。残るのは、次のサイクルへ渡す1件だけ。"""
import json
import subprocess

PATH = ".waffle/documents/handoff/handoff-artifact-share-test-inventory.json"
CWD = "/home/daidaiiro/workspace/waffle"


def q(block, expr):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", PATH, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


findings = q("reviewStatus", "findings")

# 形の測り方の件は決着した
for f in findings:
    if "形の測り方は qa-advisor の管轄" in f["note"]:
        f["resolutionStatus"] = "resolved"
        f["note"] = (
            "差し戻し2件は両方とも決着した。配置に受け皿が無い件は解消し、重心の件は"
            "qa-advisor が実測して『分けて数えてもピラミッドは救えない——底そのものが"
            "シナリオへ束ねられているため』と判定。原因は、同じ重心の宣言が3つの規約文書に"
            "一字一句同じ形で入っていたこと（雛形の既定値の残存）で、この文脈について"
            "一度も判断されていなかった。diamond へ書き直し、理由も可否の判断が2か所に"
            "分かれている事実から導く形へ改めた（a52bd2a）")

findings.append({
    "advisor": "qa-advisor", "refBlock": "designViewpoints", "refIndex": 1,
    "resolutionStatus": "open",
    "note": "配置の宣言に、実体の無い行がもう1つ残っている——業務の側の契約（application/contract）。"
            "契約の検証37件は全て入口とブラウザにあり、そこは空のまま。口の契約の検証を書いて埋めるか、"
            "行を落とすかは配置の判断なので tech-lead-advisor の担当。今回は事実の報告に留める",
})

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill", "--path", PATH,
     "--values", json.dumps({"content.reviewStatus.findings": findings},
                            ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:300])
print("STDERR:", r.stderr[:200])
