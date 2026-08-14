import json, subprocess
CWD="/home/daidaiiro/workspace/waffle"
P=".waffle/documents/agent/waffle."+"json"
v={"content.role.text":
   "UDDループ（調べる→決める→引き継ぐ→作る）を1本の道として通し、"
   "作業ごとにどこまで踏むかを判断するOrchestrator。"
   "決めることがある作業で、決める段と引き継ぐ段を省かないことに責任を持つ。"
   "構造の検証・生成・描画はWaffleが機械的に担い、判断はアドバイザーSkillが敵対的に確かめる。"}
r=subprocess.run(["uv","run","waffle","scaffold","--operation","fill","--path",P,
                  "--values",json.dumps(v,ensure_ascii=False)],capture_output=True,text=True,cwd=CWD)
print((r.stdout or r.stderr).strip()[:150])
for c in (["validate","--path",P],["render","--path",P]):
    rr=subprocess.run(["uv","run","waffle",*c],capture_output=True,text=True,cwd=CWD)
    print(c[0],":",(rr.stdout or rr.stderr).strip()[:120])