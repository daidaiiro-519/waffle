"""規模の大きいグラフを1つ作り、同じ内容をMermaidと自前で描かせる。"""
import json

# Waffleの実際の依存に似せた30ノードの有向グラフ
EDGES = [
 ("cli","uc_render"),("cli","uc_validate"),("cli","uc_scaffold"),("cli","uc_query"),
 ("mcp","uc_render"),("mcp","uc_validate"),("mcp","uc_scaffold"),("mcp","uc_query"),
 ("uc_render","svc_part"),("uc_render","svc_deploy"),("uc_render","repo_doc"),
 ("uc_validate","svc_schema"),("uc_validate","repo_doc"),("uc_validate","repo_schema"),
 ("uc_scaffold","svc_fill"),("uc_scaffold","svc_schema"),("uc_scaffold","repo_doc"),
 ("uc_query","svc_path"),("uc_query","repo_doc"),
 ("svc_part","md_out"),("svc_part","svc_layout"),
 ("svc_deploy","fs"),("svc_schema","model_schema"),("svc_fill","model_doc"),
 ("svc_path","model_doc"),("svc_layout","model_fig"),
 ("repo_doc","fs"),("repo_schema","fs"),
 ("md_out","fs"),("model_doc","model_block"),("model_schema","model_block"),
 ("model_fig","model_block"),("model_block","value_id"),("model_doc","value_id"),
 ("uc_render","svc_md2html"),("svc_md2html","html_out"),("html_out","fs"),
]
LABEL = {
 "cli":"CLI","mcp":"MCP","uc_render":"描画","uc_validate":"検証","uc_scaffold":"骨格生成",
 "uc_query":"問い合わせ","svc_part":"部品描画","svc_deploy":"配備","svc_schema":"schema解決",
 "svc_fill":"値の書き込み","svc_path":"経路の解決","svc_layout":"配置の計算",
 "svc_md2html":"HTML変換","repo_doc":"document","repo_schema":"schema",
 "md_out":"Markdown","html_out":"HTML","fs":"ファイル",
 "model_doc":"Document","model_schema":"Schema","model_fig":"Figure",
 "model_block":"Block","value_id":"識別子",
}
NODES = sorted({n for e in EDGES for n in e})

def mine():
    return {"kind":"graph",
            "nodes":[{"id":n,"name":LABEL.get(n,n)} for n in NODES],
            "edges":[{"from":a,"to":b} for a,b in EDGES]}

def mermaid():
    lines = ["flowchart TB"]
    for n in NODES:
        lines.append(f'    {n}["{LABEL.get(n,n)}"]')
    for a,b in EDGES:
        lines.append(f"    {a} --> {b}")
    return "\n".join(lines)

if __name__ == "__main__":
    print(json.dumps({"nodes":len(NODES),"edges":len(EDGES)}))