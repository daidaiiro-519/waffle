import json, subprocess
CWD="/home/daidaiiro/workspace/waffle"
P=".waffle/documents/agent/waffle."+"json"
r=subprocess.run(["uv","run","waffle","query","--operation","index_scan","--path",P],
                 capture_output=True,text=True,cwd=CWD)
blocks=list(json.loads(r.stdout)["value"].keys())
target=None
for b in blocks:
    rr=subprocess.run(["uv","run","waffle","query","--operation","query_path","--path",P,
                       "--blockKey",b,"--expression","@"],capture_output=True,text=True,cwd=CWD)
    if "フルサイクル" in rr.stdout or "直行レーン" in rr.stdout:
        target=b; print("見つかった:",b); print(rr.stdout[:400]); break