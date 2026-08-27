"""図に、CSS の見た目を属性として焼き込む。

図だけを取り出しても正しく描け、機械で確かめられるようにするため。
ページ側に CSS があればそちらが勝つ（属性は CSS より弱い）。
"""
from __future__ import annotations
import re, xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
PAINT = {"fill","stroke","stroke-width","stroke-dasharray","opacity","font-size",
         "font-weight","font-family","text-anchor","rx","ry"}

def _rules(css: str):
    """トークンを解いた上で、選択子ごとの宣言を取り出す。"""
    tok = {}
    for m in re.finditer(r'(--[a-z0-9-]+)\s*:\s*([^;}]+)', css):
        tok[m.group(1)] = m.group(2).strip()
    def solve(v, depth=0):
        if depth > 6: return v
        return re.sub(r'var\((--[a-z0-9-]+)(?:,[^)]*)?\)',
                      lambda m: solve(tok.get(m.group(1), "#888"), depth+1), v)
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel, body = m.group(1).strip(), m.group(2)
        if sel.startswith(("@", ":root")): continue
        decls = {}
        for part in body.split(";"):
            if ":" not in part: continue
            k, v = part.split(":", 1); k = k.strip()
            if k in PAINT: decls[k] = solve(v.strip())
        if not decls: continue
        for one in sel.split(","):
            one = one.strip()
            if one: out.append((one, decls))
    return out

def _parse_sel(sel: str):
    """『.a .b tag』の形だけを扱う。最後の単位が対象、手前は先祖の条件。"""
    parts = []
    for unit in sel.split():
        tag = re.match(r'^([a-zA-Z]+)', unit)
        parts.append((tag.group(1) if tag else None, set(re.findall(r'\.([A-Za-z0-9_-]+)', unit))))
    return parts

def inline(svg: str) -> str:
    css_rules = inline.rules
    ET.register_namespace("", NS)
    root = ET.fromstring(svg)
    def cls(el): return set((el.get("class") or "").split())
    def walk(el, anc):
        tag = el.tag.split("}")[-1]; c = cls(el)
        for sel, decls in css_rules:
            parts = _parse_sel(sel)
            t, need = parts[-1]
            if t and t != tag: continue
            if not need <= c: continue
            ok = True
            for at, ac in parts[:-1]:
                if not any(ac <= h and (at is None or True) for h in anc): ok = False; break
            if not ok: continue
            for k, v in decls.items():
                if el.get(k) is None: el.set(k, v)
        for ch in el: walk(ch, anc + [c])
    walk(root, [])
    return ET.tostring(root, encoding="unicode")
