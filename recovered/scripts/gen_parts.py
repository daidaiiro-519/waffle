import json, pathlib, sys
sys.path.insert(0, "src")
from waffle.domain.services import part_renderer as P

samples = {}

samples["sequence"] = (
    {"participants": [
        {"id": "orchestrator", "kind": "actor", "label": "Orchestrator"},
        {"id": "waffle", "kind": "participant", "label": "Waffle"},
        {"id": "advisor", "kind": "participant", "label": "advisor"}],
     "steps": [
        {"kind": "command", "from": "orchestrator", "to": "waffle", "message": "骨格を作る", "activate": True},
        {"kind": "return", "from": "waffle", "to": "orchestrator", "message": "埋める場所の一覧", "deactivate": True},
        {"kind": "loop", "message": "観点ごとに",
         "steps": [{"kind": "command", "from": "orchestrator", "to": "advisor", "message": "敵対的に確かめる"},
                   {"kind": "return", "from": "advisor", "to": "orchestrator", "message": "反証、または支持"}]},
        {"kind": "alt", "branches": [
            {"label": "全員が支持した", "steps": [{"kind": "command", "from": "orchestrator", "to": "waffle", "message": "値を書き込む"}]},
            {"label": "反証が出た", "steps": [{"kind": "event", "from": "orchestrator", "message": "差し戻して調べ直す"}]}]}]},
    lambda d: P._sequence(d["steps"], d["participants"]))

samples["architecture"] = (
    {"zones": [
        {"id": "inbound", "label": "受け口", "contains": [{"id": "cli", "label": "CLI"}, {"id": "mcp", "label": "MCP"}]},
        {"id": "app", "label": "応用", "contains": [{"id": "uc", "label": "ユースケース"}]},
        {"id": "domain", "label": "領域", "contains": [{"id": "svc", "label": "業務サービス"}, {"id": "model", "label": "モデル"}]}],
     "connections": [{"from": "cli", "to": "uc"}, {"from": "mcp", "to": "uc"},
                     {"from": "uc", "to": "svc"}, {"from": "svc", "to": "model"}]},
    lambda d: P._architecture(d["zones"], d["connections"]))

samples["flowchart"] = (
    {"stages": [{"id": "investigate", "label": "調べる"}, {"id": "decide", "label": "決める"},
                {"id": "handoff", "label": "引き継ぐ"}, {"id": "build", "label": "作る"}],
     "transitions": [{"from": "investigate", "to": "decide"}, {"from": "decide", "to": "handoff"},
                     {"from": "handoff", "to": "build"},
                     {"from": "build", "to": "investigate", "label": "反証が出たら"}]},
    lambda d: P._flowchart(d["stages"], d["transitions"]))

samples["graph"] = (
    {"groups": [{"label": "問題空間", "nodes": ["事業領域", "業務領域"]},
                {"label": "解決空間", "nodes": ["区切られた文脈", "業務ユースケース", "集約"]}],
     "nodes": [], "direction": "TB",
     "edges": [{"from": "事業領域", "to": "業務領域", "label": "含む"},
               {"from": "区切られた文脈", "to": "業務ユースケース", "label": "持つ"},
               {"from": "区切られた文脈", "to": "集約", "label": "持つ"},
               {"from": "業務ユースケース", "to": "業務領域", "label": "対応する"}]},
    lambda d: P._graph(d["edges"], d["nodes"], d["groups"], d["direction"]))

samples["statediagram"] = (
    {"transitions": [{"from": "[*]", "to": "DRAFT", "command": "骨格を作る"},
                     {"from": "DRAFT", "to": "VALIDATED", "command": "構造の整合を確かめる"},
                     {"from": "VALIDATED", "to": "ACTIVE", "command": "成果物として確定する"},
                     {"from": "ACTIVE", "to": "DEPRECATED", "command": "使うのをやめる"},
                     {"from": "VALIDATED", "to": "DRAFT", "command": "不備が見つかった"}],
     "pseudo_states": []},
    lambda d: P._statediagram(d["transitions"], d["pseudo_states"]))

out = {}
for name, (data, fn) in samples.items():
    md = fn(data)
    out[name] = {"input": data, "mermaid": md.replace("```mermaid\n", "").replace("\n```", "")}
    print(f"--- {name} ---")
    print(out[name]["mermaid"])
    print()

pathlib.Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")