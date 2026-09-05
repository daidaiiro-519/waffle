# -*- coding: utf-8 -*-
"""A-8 版の移行。閉じた操作集合だけを、宣言順に当てる。推論は入れない。"""
import json, copy
from pathlib import Path
BASE = Path(__file__).parent

OPS = {"rename_field","add_field","drop_field","rename_kind","allow_child","retype_field"}

def load(name): return json.loads((BASE/name).read_text(encoding="utf-8"))

def walk(n):
    yield n
    for c in n.get("children", []): yield from walk(c)

def migrate(inst, plan, schema_to):
    """返り値: (移行後の実体, 埋めるべき穴, 記録)"""
    assert inst.get("schema", "ddd@1") == plan["from"], f'版が違う: {inst.get("schema")} != {plan["from"]}'
    out = copy.deepcopy(inst); log = []
    for op in plan["ops"]:
        k = op["op"]; assert k in OPS, f"未知の操作: {k}"
        hit = 0
        for n in walk(out):
            if k == "rename_kind":
                if n["kind"] == op["from"]: n["kind"] = op["to"]; hit += 1
                continue
            if n["kind"] != op.get("kind"): continue
            if k == "rename_field" and op["from"] in n:
                n[op["to"]] = n.pop(op["from"]); hit += 1
            elif k == "drop_field" and op["field"] in n:
                n.pop(op["field"]); hit += 1
            elif k == "add_field" and op["field"] not in n:
                if "default" in op: n[op["field"]] = op["default"]; hit += 1
                else: hit += 1                      # 既定値が無い＝穴。AIが埋める
            elif k == "retype_field" and op["field"] in n:
                v = n[op["field"]]
                if op["to"] == "array" and not isinstance(v, list):
                    n[op["field"]] = [x.strip() for x in str(v).split(op.get("sep","／"))]; hit += 1
        log.append({"op": k, "kind": op.get("kind") or op.get("from",""), "field": op.get("field") or op.get("to",""), "hit": hit})
    out["schema"] = plan["to"]
    # 穴 = 既定値の無い add_field
    holes = []
    for op in plan["ops"]:
        if op["op"] == "add_field" and "default" not in op:
            for n in walk(out):
                if n["kind"] == op["kind"] and op["field"] not in n:
                    holes.append((n["uid"], op["field"], op.get("prompt","")))
    warn = [l for l in log if l["hit"] == 0]   # F-20 1件も当たらない移行操作は書き間違いを疑う
    return out, holes, log, warn
