import json, subprocess
CWD="/home/daidaiiro/workspace/waffle"
REF="DomainSpecSchema/v9"
TXT=("「業務エキスパートが理解できる日本語の説明：識別子」の形式で設定してください。"
     "説明部分はこの業務サービスが何を決める計算かを業務語彙で簡潔に表す句"
     "（識別子やクラス名をそのまま繰り返さない）。"
     "識別子部分はこの文書自身の識別子をそのまま使う"
     "（識別子は既に別の箇所が正であり、ここでは表示のためだけに引用する）。")
r=subprocess.run(["uv","run","waffle","patch-schema","--schemaRef",REF,"--operation","set_field",
                  "--params",json.dumps({"defName":"TitleBlock",
                                         "fieldPath":"properties.title.x-prompt-write.domain-service",
                                         "value":TXT},ensure_ascii=False)],
                 capture_output=True,text=True,cwd=CWD)
print("題名の指示 :", (r.stdout or r.stderr).strip()[:150])