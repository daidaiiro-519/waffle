import json, subprocess
CWD="/home/daidaiiro/workspace/waffle"
P=(".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/"
   "usecase/uc-check-criteria-coverage.json")
R=[("満たす条件を1件も挙げていない","満たす基準を1件も挙げていない"),
   ("どのシナリオからも指されていない条件を挙げる","どのシナリオからも指されていない基準を挙げる"),
   ("条件側から見た欠け","基準の側から見た欠け"),
   ("どの条件も挙げていないシナリオ","どの基準も挙げていないシナリオ"),
   ("満たす条件を空で宣言した","満たす基準を空で宣言した"),
   ("満たす条件の欄","満たす基準の欄"),
   ("シナリオ側から見た欠け","シナリオの側から見た欠け")]
def w(n):
    if isinstance(n,str):
        for a,b in R: n=n.replace(a,b)
        return n
    if isinstance(n,list): return [w(x) for x in n]
    if isinstance(n,dict): return {k:w(v) for k,v in n.items()}
    return n
def q(b,e):
    r=subprocess.run(["uv","run","waffle","query","--operation","query_path","--path",P,
                      "--blockKey",b,"--expression",e],capture_output=True,text=True,cwd=CWD)
    return json.loads(r.stdout)["value"]
vals={}
for b,e,fp in (("acceptanceCriteria","items","content.acceptanceCriteria.items"),
               ("acceptanceScenarios","scenarios","content.acceptanceScenarios.scenarios"),
               ("postconditions","items","content.postconditions.items")):
    cur=q(b,e); new=w(cur)
    if new!=cur: vals[fp]=new
r=subprocess.run(["uv","run","waffle","scaffold","--operation","fill","--path",P,
                  "--values",json.dumps(vals,ensure_ascii=False)],capture_output=True,text=True,cwd=CWD)
print((r.stdout or r.stderr).strip()[:150])