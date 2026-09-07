# -*- coding: utf-8 -*-
"""Kata 原型。A-1 アドレス / A-2 正規化 / A-3 射影 / A-4 部分木 / A-5 差分 / A-6 突き合わせ"""
import json, re, sys, unicodedata, hashlib, bisect
from pathlib import Path

BASE = Path(__file__).parent
SCHEMA = json.loads((BASE/"schema/ddd@1.json").read_text(encoding="utf-8"))
KINDS = SCHEMA["kinds"]
CONTRACT = "md@1"

# ---------- A-1 アドレス ----------
def addr_of(node, parent=""):
    seg = f'{KINDS[node["kind"]]["code"]}#{node["id"]}'
    return f"{parent}#{seg}" if parent else seg

def walk(node, parent=""):
    a = addr_of(node, parent)
    yield a, node
    for c in node.get("children", []):
        yield from walk(c, a)

# ---------- A-2 正規化 ----------
def canonical(node):
    k = KINDS[node["kind"]]
    out = {"kind": node["kind"], "id": node["id"], "uid": node["uid"]}
    for f in k["fields"]:                      # 鍵順はスキーマの宣言順
        if f in node and node[f] is not None:  # 不在はキーを置かない
            out[f] = nfc(node[f])
    if node.get("children"):
        out["children"] = [canonical(c) for c in node["children"]]
    return out

def nfc(v):
    if isinstance(v, str):  return unicodedata.normalize("NFC", v)
    if isinstance(v, list): return [nfc(x) for x in v]
    if isinstance(v, dict): return {k: nfc(x) for k, x in v.items()}
    return v

def dumps(node):
    return json.dumps(node, ensure_ascii=False, indent=2) + "\n"

# ---------- A-3 射影 ----------
def tmpl(kind, n, depth):
    h = "#" * (depth + 2)
    if kind == "context":
        return f'{h} 境界づけられた文脈: {n["name"]} `{{#CTX:{n["id"]}}}`\n\n{n["purpose"]}\n'
    if kind == "aggregate":
        return f'{h} 集約: {n["name"]} `{{#AGG:{n["id"]}}}`\n\nルート: `{n["root"]}`\n\n{n["purpose"]}\n'
    if kind == "entity":
        rows = "\n".join(f'| {a["name"]} | {a["type"]} | {a["note"]} |' for a in n["attributes"])
        return (f'{h} エンティティ: {n["name"]}\n\n識別子: {n["identity"]}\n\n'
                f'| 属性 | 型 | 備考 |\n|---|---|---|\n{rows}\n')
    if kind == "invariant":
        return f'- **INV-{n["id"]}** {n["statement"]}\n'
    if kind == "usecase":
        pre = " / ".join(n["pre"]); post = " / ".join(n["post"])
        return (f'{h} 業務ユースケース: UC-{n["id"]} {n["name"]}\n\n'
                f'- アクター: {n["actor"]}\n- 事前条件: {pre}\n- 事後条件: {post}\n')
    if kind == "scenario":
        return (f'- **SC-{n["id"]}**  \n'
                f'  前提 {n["given"]}  \n  もし {n["when"]}  \n  ならば {n["then"]}\n')
    raise KeyError(kind)

GROUP = {"invariant": "不変条件", "scenario": "シナリオ"}

def render(node, depth=0):
    out = [tmpl(node["kind"], node, depth)]
    kids = node.get("children", [])
    prev = None
    for c in kids:
        if c["kind"] in GROUP and c["kind"] != prev:
            out.append(f'\n{"#" * (depth + 3)} {GROUP[c["kind"]]}\n\n')
        elif c["kind"] not in GROUP:
            out.append("\n")
        prev = c["kind"]
        out.append(render(c, depth + 1) if c["kind"] not in GROUP else tmpl(c["kind"], c, depth + 1))
    return "".join(out)

def render_doc(root):
    return f'<!-- kata: profile=ddd@1 contract={CONTRACT} -->\n\n' + render(canonical(root))

# ---------- A-4 部分木 ----------
class Index:
    def __init__(self, roots):
        self.n = {}
        for r in roots:
            for a, node in walk(r): self.n[a] = node
        self.keys = sorted(self.n)
    def children(self, prefix=""):
        d = prefix.count("#") + 2 if prefix else 2
        return [k for k in self.keys if k.startswith(prefix) and k.count("#") == d - (0 if prefix else 1)]
    def subtree(self, prefix):
        i = bisect.bisect_left(self.keys, prefix); out = []
        while i < len(self.keys) and self.keys[i].startswith(prefix):
            out.append(self.keys[i]); i += 1
        return out
    def by_kind(self, kind, under=""):
        return [k for k in self.keys if k.startswith(under) and self.n[k]["kind"] == kind]

# ---------- A-5 差分 ----------
def sig(node):
    c = dict(canonical(node)); c.pop("children", None)
    return hashlib.sha256(dumps(c).encode()).hexdigest()[:12]

def diff(a: Index, b: Index):
    A, B = set(a.keys), set(b.keys)
    add, rem = B - A, A - B
    ua = {a.n[k]["uid"]: k for k in rem}
    moved = [(ua[b.n[k]["uid"]], k) for k in add if b.n[k]["uid"] in ua]   # AD-7 uid で同定
    mv_from = {f for f, _ in moved}; mv_to = {t for _, t in moved}
    return {"added": sorted(add - mv_to), "removed": sorted(rem - mv_from),
            "moved": sorted(moved),
            "changed": sorted(k for k in A & B if sig(a.n[k]) != sig(b.n[k]))}

# ---------- A-6 突き合わせ ----------
TRACED = set(SCHEMA["traced"])   # AD-9 プロファイルが宣言する

def verify(idx, src_dir):
    """AD-7: @spec は uid を指す。move しても迷子にならない"""
    S = {idx.n[k]["uid"] for k in idx.keys if idx.n[k]["kind"] in TRACED}
    I = set()
    for f in Path(src_dir).rglob("*.py"):
        I |= set(re.findall(r"@spec\s+([A-Z]+-[0-9A-F]+)", f.read_text(encoding="utf-8")))
    at = {idx.n[k]["uid"]: k for k in idx.keys}
    return {"未実装": sorted(at[u] for u in S - I), "仕様外": sorted(I - S)}

# ---------- AD-8 Reference ----------
def refs_to(idx, uid):
    """この uid を指しているノード（逆引き）"""
    return sorted(k for k, n in idx.n.items() if uid in (n.get("refs") or []))

def can_delete(idx, addr):
    inbound = refs_to(idx, idx.n[addr]["uid"])
    return (not inbound), inbound

def search(idx, text, under=""):
    """AD-8 の残り1件。全文の当たりをアドレスで返す"""
    out = []
    for k, n in idx.n.items():
        if not k.startswith(under): continue
        blob = json.dumps({f: n.get(f) for f in KINDS[n["kind"]]["fields"]}, ensure_ascii=False)
        if text in blob: out.append(k)
    return sorted(out)

if __name__ == "__main__":
    root = json.loads((BASE/"instance/CTX-予約.json").read_text(encoding="utf-8"))
    (BASE/"render/CTX-予約.md").write_text(render_doc(root), encoding="utf-8")
    print("rendered")


# ================= AD-10  Reference は型と解決状態を持つ =================
REF_KINDS = ("spec", "impl", "external")

def refs_of(node):
    """旧: ["INV-0004"] も受ける。新: {"kind":..., "target":...}"""
    for r in (node.get("refs") or []):
        yield r if isinstance(r, dict) else {"kind": "spec", "target": r}

def resolve_refs(idx, src_root="."):
    """F-19 解決しない参照を落とす"""
    uids = {n["uid"] for n in idx.n.values()}
    out = []
    for addr, n in idx.n.items():
        for r in refs_of(n):
            k, t = r["kind"], r["target"]
            if k == "spec":       ok = t in uids
            elif k == "impl":     ok = (Path(src_root) / t).exists()
            elif k == "external": ok = None          # 外部は確認ない
            else:                 ok = False
            out.append({"from": addr, "kind": k, "target": t, "resolved": ok})
    return out

def unresolved(idx, src_root="."):
    return [r for r in resolve_refs(idx, src_root) if r["resolved"] is False]

# ================= 欠落と集計の述語 =================
def missing_child(idx, kind, child_kind):
    """『シナリオを1つも持たない集約は』"""
    out = []
    for addr, n in idx.n.items():
        if n["kind"] != kind: continue
        if not any(c["kind"] == child_kind for c in (n.get("children") or [])):
            out.append(addr)
    return sorted(out)

def count_by(idx, group_field, kind=None, under=""):
    """『未実装は担当ごとに何件か』"""
    c = {}
    for addr, n in idx.n.items():
        if not addr.startswith(under): continue
        if kind and n["kind"] != kind: continue
        key = n.get(group_field, "(未記入)")
        if isinstance(key, list): key = tuple(key)
        c[key] = c.get(key, 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


# ================= 契約を選べる射影（所見3件を直した md@2 と html@1）=================
import contracts as _C
GROUP2 = {"invariant": "不変条件", "scenario": "シナリオ"}

def render2(node, contract="md@2", addr="", depth=0, parent=""):
    fn, grp, _ = _C.CONTRACTS[contract]
    a = addr
    head, tail = fn(node, a, depth, parent)
    out = [head]
    prev = None
    me = node["id"]
    for c in node.get("children", []):
        ca = addr_of(c, a)
        if c["kind"] in GROUP2 and c["kind"] != prev: out.append(grp(GROUP2[c["kind"]], depth + 1))
        prev = c["kind"]
        out.append(render2(c, contract, ca, depth + 1, me if c["kind"] in ("invariant", "usecase") else parent))
    out.append(tail)
    return "".join(out)

def render_doc2(root, contract="md@2"):
    _, _, head = _C.CONTRACTS[contract]
    return head + render2(canonical(root), contract, addr_of(root))

def resolve(idx, uid):
    """@spec の uid から、人が読める位置へ戻す"""
    for a, n in idx.n.items():
        if n["uid"] == uid:
            return {"uid": uid, "addr": a, "name": n.get("name") or n.get("statement") or n.get("rule") or n.get("given","")}
    return None
