import json, re, subprocess
CWD="/home/daidaiiro/workspace/waffle"
DS=(".waffle/documents/specs/bc-waffle/domain-service/ds-resolve-path-template."+"json")
def run(*a):
    r=subprocess.run(["uv","run","waffle",*a],capture_output=True,text=True,cwd=CWD)
    return (r.stdout or r.stderr).strip()
def q(b,e): return json.loads(run("query","--operation","query_path","--path",DS,"--blockKey",b,"--expression",e))["value"]
def w(n):
    if isinstance(n,str): return re.sub(r'(?<!パス)変数','パス変数',n)
    if isinstance(n,list): return [w(x) for x in n]
    if isinstance(n,dict): return {k:w(v) for k,v in n.items()}
    return n
vals={}
for b,e,fp in (("description","items","content.description.items"),
               ("existenceRationale","items","content.existenceRationale.items"),
               ("referencedAggregates","items","content.referencedAggregates.items"),
               ("inputsOutputs","inputs","content.inputsOutputs.inputs"),
               ("inputsOutputs","outputs","content.inputsOutputs.outputs"),
               ("inputsOutputs","undefinedInputs","content.inputsOutputs.undefinedInputs"),
               ("acceptanceCriteria","items","content.acceptanceCriteria.items"),
               ("acceptanceScenarios","scenarios","content.acceptanceScenarios.scenarios")):
    cur=q(b,e); new=w(cur)
    if new!=cur: vals[fp]=new
print(run("scaffold","--operation","fill","--path",DS,"--values",json.dumps(vals,ensure_ascii=False))[:120])
print("検証 :", run("validate","--path",DS)[:110])