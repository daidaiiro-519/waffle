import json, subprocess
CWD="/home/daidaiiro/workspace/waffle"
H=".waffle/documents/handoff/handoff-criteria-scenario-link.json"
v={"content.reviewStatus.completionImageConfirmedBy.confirmed": True,
   "content.reviewStatus.completionImageConfirmedBy.confirmedBy": "daidaiiro",
   "content.reviewStatus.completionImageConfirmedBy.confirmedAt": "2026-08-10",
   "content.reviewStatus.completionImageConfirmedBy.note":
     "スキーマ定義の変更を主とし、既存の仕様と実装を再定義した契約で成立させる。"
     "検査は後段。語彙は描画される見出しに合わせてそろえたうえで確認を得た。"}
r=subprocess.run(["uv","run","waffle","scaffold","--operation","fill","--path",H,
                  "--values",json.dumps(v,ensure_ascii=False)],capture_output=True,text=True,cwd=CWD)
print((r.stdout or r.stderr).strip()[:170])