import json, subprocess
CWD="/home/daidaiiro/workspace/waffle"
BC=".waffle/documents/specs/bc-waffle/bc-waffle."+"json"
DS=(".waffle/documents/specs/bc-waffle/domain-service/ds-resolve-path-template."+"json")

def run(*a):
    r=subprocess.run(["uv","run","waffle",*a],capture_output=True,text=True,cwd=CWD)
    return (r.stdout or r.stderr).strip()
def q(p,b,e): return json.loads(run("query","--operation","query_path","--path",p,"--blockKey",b,"--expression",e))["value"]
def fill(p,v): return run("scaffold","--operation","fill","--path",p,"--values",json.dumps(v,ensure_ascii=False))[:130]

items=q(BC,"ubiquitousLanguage","items")
for x in items:
    if x["term"]=="パステンプレート":
        x["definition"]="Schema が宣言する、パス変数を含んだ置き場所の型。"
    if x["term"]=="実パス":
        x["definition"]="パス変数がすべて値で埋まった、ひとつに定まるパス。"
    if x["term"]=="解決":
        x["definition"]="パステンプレートとパス変数の値から実パスを導くこと。"
    if x["term"]=="逆解析":
        x["definition"]="実パスとパステンプレートから、パス変数の値を取り出すこと。解決の逆。"
have={x["term"] for x in items}
for t,d in (("パス変数","パステンプレートの中で、値で埋める箇所。"),
            ("配り先","成果物を、原本の置き場所とは別に届ける先。")):
    if t not in have: items.append({"term":t,"definition":d})
print(f"語彙 {len(items)} 語 :", fill(BC,{"content.ubiquitousLanguage.items":items}))
print("  検証 :", run("validate","--path",BC)[:110]); run("render","--path",BC)

# 業務サービスの文書の「変数」を「パス変数」へ
def w(n):
    if isinstance(n,str):
        return n.replace("その変数すべて","そのパス変数すべて").replace("変数を含む","パス変数を含む") \
                .replace("変数の値","パス変数の値").replace("変数がすべて","パス変数がすべて") \
                .replace("変数を値に","パス変数を値に").replace("変数それぞれ","パス変数それぞれ") \
                .replace("現れる変数","現れるパス変数").replace("要求する変数","要求するパス変数") \
                .replace("入る値","入る値").replace("パスパス変数","パス変数")
    if isinstance(n,list): return [w(x) for x in n]
    if isinstance(n,dict): return {k:w(v) for k,v in n.items()}
    return n
vals={}
for b,e,fp in (("title","title","content.title.title"),
               ("description","items","content.description.items"),
               ("existenceRationale","items","content.existenceRationale.items"),
               ("referencedAggregates","items","content.referencedAggregates.items"),
               ("inputsOutputs","inputs","content.inputsOutputs.inputs"),
               ("inputsOutputs","outputs","content.inputsOutputs.outputs"),
               ("inputsOutputs","undefinedInputs","content.inputsOutputs.undefinedInputs"),
               ("acceptanceCriteria","items","content.acceptanceCriteria.items"),
               ("acceptanceScenarios","scenarios","content.acceptanceScenarios.scenarios")):
    cur=q(DS,b,e); new=w(cur)
    if new!=cur: vals[fp]=new
print("業務サービス :", fill(DS,vals) if vals else "変更なし")
print("  検証 :", run("validate","--path",DS)[:110])