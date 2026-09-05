# -*- coding: utf-8 -*-
"""Kata 中核層。プロファイルの意味を1つも持たない。
kinds / contract は外から渡す。DDD も research も、このファイルは知らない。"""
import json, re, bisect, hashlib, unicodedata, copy
from pathlib import Path

# ---------------- プロファイル ----------------
class Profile:
    def __init__(self, path):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        self.name, self.kinds = d["profile"], d["kinds"]
        self.traced = set(d.get("traced", []))
        self.groups = d.get("groups", {})
    def code(self, kind):     return self.kinds[kind]["code"]
    def fields(self, kind):   return self.kinds[kind]["fields"]
    def children(self, kind): return self.kinds[kind].get("children", [])

# ---------------- A-1 アドレス ----------------
def addr_of(p, node, parent=""):
    seg = f'{p.code(node["kind"])}#{node["id"]}'
    return f"{parent}#{seg}" if parent else seg

def walk(p, node, parent=""):
    a = addr_of(p, node, parent)
    yield a, node
    for c in node.get("children", []): yield from walk(p, c, a)

# ---------------- A-2 正規化 ----------------
def _nfc(v):
    if isinstance(v, str):  return unicodedata.normalize("NFC", v)
    if isinstance(v, list): return [_nfc(x) for x in v]
    if isinstance(v, dict): return {k: _nfc(x) for k, x in v.items()}
    return v

def canonical(p, n):
    out = {"kind": n["kind"], "id": n["id"], "uid": n["uid"]}
    for f in p.fields(n["kind"]):
        if f in n and n[f] is not None: out[f] = _nfc(n[f])
    if n.get("children"): out["children"] = [canonical(p, c) for c in n["children"]]
    return out

def dumps(x): return json.dumps(x, ensure_ascii=False, indent=2) + "\n"

# ---------------- A-3 射影（契約はデータ） ----------------
def _fmt(tpl, n):
    def sub(m):
        f, sep = (m.group(1).split("|", 1) + [None])[:2]
        v = n.get(f, "")
        return sep.join(v) if isinstance(v, list) and sep else ("" if v is None else str(v))
    return re.sub(r"\{([^}]+)\}", sub, tpl)

class Contract:
    def __init__(self, path):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        self.name, self.head, self.hmax = d["name"], d.get("head", ""), d.get("heading_max", 6)
        self.kinds, self.group = d["kinds"], d.get("group", "{label}")
        self.anchor = d.get("anchor", "")

def render(p, c, node, addr=None, depth=0, parent=""):
    addr = addr if addr is not None else addr_of(p, node)
    spec, k = c.kinds[node["kind"]], node["kind"]
    h = "#" * min(depth + 2, c.hmax)
    ctx = dict(node); ctx["_h"] = h; ctx["_parent"] = parent
    out = [_fmt(c.anchor, {"addr": addr, "uid": node["uid"]})] if c.anchor else []
    tpl = spec["tpl"].replace("{{h}}", h).replace("{{parent}}", parent)   # 二重括弧を先に解く
    out.append(_fmt(tpl, ctx))
    if "table" in spec:
        t = spec["table"]; rows = node.get(t["field"]) or []
        out.append("| " + " | ".join(x[0] for x in t["cols"]) + " |\n")
        out.append("|" + "---|" * len(t["cols"]) + "\n")
        for r in rows: out.append("| " + " | ".join(str(r.get(x[1], "")) for x in t["cols"]) + " |\n")
        out.append("\n")
    prev = None
    for ch in node.get("children", []):
        if ch["kind"] in p.groups and ch["kind"] != prev:
            lbl = p.groups[ch["kind"]]
            gh = "#" * min(depth + 3, c.hmax)
            out.append(_fmt(c.group.replace("{{h}}", gh), {"label": lbl}) + "\n")
        prev = ch["kind"]
        out.append(render(p, c, ch, addr_of(p, ch, addr), depth + 1, node["id"]))
    return "".join(out)

def render_doc(p, c, root): return c.head + render(p, c, canonical(p, root))

# ---------------- A-4 索引 ----------------
class Index:
    def __init__(self, p, roots):
        self.p = p
        self.n = {a: n for r in roots for a, n in walk(p, r)}
        self.keys = sorted(self.n)
    def children(self, prefix=""):
        d = (prefix.count("#") + 2) if prefix else 1
        return [k for k in self.keys if k.startswith(prefix) and k.count("#") == d]
    def subtree(self, pre):
        i = bisect.bisect_left(self.keys, pre); o = []
        while i < len(self.keys) and self.keys[i].startswith(pre): o.append(self.keys[i]); i += 1
        return o
    def by_kind(self, kind, under=""): return [k for k in self.keys if k.startswith(under) and self.n[k]["kind"] == kind]
    def resolve(self, uid):
        for a, n in self.n.items():
            if n["uid"] == uid: return {"uid": uid, "addr": a, "label": next((str(n[f]) for f in self.p.fields(n["kind"]) if n.get(f)), "")}

# ---------------- A-5 差分 ----------------
def _sig(p, n):
    c = dict(canonical(p, n)); c.pop("children", None)
    return hashlib.sha256(dumps(c).encode()).hexdigest()[:12]

def diff(a, b):
    A, B = set(a.keys), set(b.keys); add, rem = B - A, A - B
    ua = {a.n[k]["uid"]: k for k in rem}
    mv = [(ua[b.n[k]["uid"]], k) for k in add if b.n[k]["uid"] in ua]
    return {"added": sorted(add - {t for _, t in mv}), "removed": sorted(rem - {f for f, _ in mv}),
            "moved": sorted(mv), "changed": sorted(k for k in A & B if _sig(a.p, a.n[k]) != _sig(b.p, b.n[k]))}

# ---------------- A-6 突き合わせ / Reference ----------------
def refs_of(n):
    for r in (n.get("refs") or []): yield r if isinstance(r, dict) else {"kind": "spec", "target": r}

def resolve_refs(idx, root="."):
    uids = {n["uid"] for n in idx.n.values()}; out = []
    for a, n in idx.n.items():
        for r in refs_of(n):
            ok = (r["target"] in uids) if r["kind"] == "spec" else \
                 ((Path(root) / r["target"]).exists() if r["kind"] == "impl" else None)
            out.append({"from": a, **r, "resolved": ok})
    return out

def verify(idx, src_dir, pat=r"@spec\s+([A-Z]+-[0-9A-Fa-f]+)"):
    S = {idx.n[k]["uid"] for k in idx.keys if idx.n[k]["kind"] in idx.p.traced}
    I = set()
    for f in Path(src_dir).rglob("*"):
        if f.is_file() and f.suffix in (".py", ".md", ".ts", ".go"):
            I |= set(re.findall(pat, f.read_text(encoding="utf-8", errors="ignore")))
    at = {n["uid"]: a for a, n in idx.n.items()}
    return {"未実装": sorted(at[u] for u in S - I), "仕様外": sorted(I - S),
            "未解決参照": [r for r in resolve_refs(idx) if r["resolved"] is False]}

# ---------------- 述語 ----------------
def missing_child(idx, kind, child):
    return sorted(a for a, n in idx.n.items() if n["kind"] == kind
                  and not any(c["kind"] == child for c in (n.get("children") or [])))

def count_by(idx, field, kind=None, under=""):
    c = {}
    for a, n in idx.n.items():
        if not a.startswith(under) or (kind and n["kind"] != kind): continue
        k = n.get(field, "(未記入)"); k = tuple(k) if isinstance(k, list) else k
        c[k] = c.get(k, 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))

OPS = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b, "contains": lambda a, b: b in str(a),
       "gt": lambda a, b: str(a) > str(b), "lt": lambda a, b: str(a) < str(b)}

def find(idx, kind=None, where=None, order_by=None, under=""):
    rows = [(a, n) for a, n in idx.n.items() if a.startswith(under) and (kind is None or n["kind"] == kind)]
    for c in (where or []):
        rows = [(a, n) for a, n in rows if c["field"] in n and OPS[c["op"]](n[c["field"]], c["value"])]
    if order_by: rows.sort(key=lambda an: str(an[1].get(order_by["field"], "")), reverse=order_by.get("desc", False))
    return [a for a, _ in rows]

def tool_schema(p):
    """AIに渡すパラメータを、プロファイルから生成する（AD-4）"""
    return {"name": "find", "input_schema": {"type": "object", "properties": {
        "kind": {"enum": sorted(p.kinds)},
        "where": {"type": "array", "items": {"type": "object", "properties": {
            "field": {"enum": sorted({f for k in p.kinds for f in p.fields(k)})},
            "op": {"enum": sorted(OPS)}, "value": {"type": "string"}}}}}}}
