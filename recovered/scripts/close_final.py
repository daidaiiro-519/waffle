"""棚卸しの引き継ぎ文書を、すべて決着した状態にする。"""
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
for f in findings:
    if "業務の側の契約" in f["note"]:
        f["resolutionStatus"] = "resolved"
        f["note"] = (
            "業務の側の契約の行は、埋める側で決着した。判断の順序は「行に実体があるか」"
            "ではなく「その行が支えている必須ルールに、守るべき実体があるか」——偽物が"
            "本物より甘くなる事故は既に一度起きており、記録も残っている。調べる過程で3件の"
            "取り残しが出た。鍵と値の保管の偽物が3つあり記録を見せる名前が2種類に分かれて"
            "いたこと（失敗を作れるのは1つだけだった）、その保管の読み取りを本番では誰も"
            "呼んでいないのに口・本物・偽物が別々の振る舞いを持っていたこと、そして集約の"
            "読み書きの口がまだ素の辞書を受け渡すと宣言していたこと。すべて直し、同じ問いを"
            "本物と偽物の両方へ投げる束を2つ置いた（2e3394a）")

constraints = q("constraints", "items")
constraints.append(
    "招かれている人の名簿の口は、本物が利用者プールへ直接つながるため、"
    "本物と偽物を突き合わせる束の対象にできない。規約が実物のサービスに依存する"
    "単体の検証を禁じているためで、偽物の側だけを保つ。この除外は宣言の側にも書いた"
    "——書かないと、3つのうち2つしか対象になっていないことが誰にも見えない。")
constraints.append(
    "鍵と値の保管の読み取りを口から落としたので、書いたものを読み返す検証は、"
    "偽物が自分の記録を見せる面を直接見る形になっている。口の読み取りとして"
    "確かめると、本番に無い経路を固定することになる。")

values = {
    "content.reviewStatus.findings": findings,
    "content.constraints.items": constraints,
    "content.reviewStatus.completionImageConfirmedBy.confirmed": True,
    "content.reviewStatus.completionImageConfirmedBy.confirmedBy": "オーケストレータ",
    "content.reviewStatus.completionImageConfirmedBy.note":
        "宣言された階層へ全ての検証が収まり、宣言されていて空だった行は3つとも実体を"
        "持った（業務の操作の単体・外への出口・業務の側の契約）。手元で動くプログラムの"
        "行は新設した。直下に残るのは検証ではない補助のモジュールだけ。",
}

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill", "--path", PATH,
     "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:400])
print("STDERR:", r.stderr[:200])
