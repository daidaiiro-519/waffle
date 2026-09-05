# -*- coding: utf-8 -*-
"""変換契約。版ごとに1つ。純関数だけを置く。
md@2 は md@1 の所見3件を直したもの：
  1 アドレスを見出しから外し、HTMLコメントへ
  2 INV-01 が集約ごとに重複するので、親の id を表示に添える
  3 h5 に達するので、深さ4以上は見出しをやめて定義リストにする
"""
import html as H

MAX_H = 4          # 所見3

def _h(depth):     return "#" * min(depth + 2, MAX_H)
def _anchor(addr, n): return f'<!-- @ {addr} uid={n["uid"]} -->\n'

# ---------------- md@2 ----------------
def md2(n, addr, depth, parent):   # 返り値は (前, 後)
    k, a = n["kind"], _anchor(addr, n)
    if k == "context":   return f'{a}{_h(depth)} 境界づけられた文脈: {n["name"]}\n\n{n["purpose"]}\n', ''
    if k == "aggregate": return f'{a}{_h(depth)} 集約: {n["name"]}\n\nルート: `{n["root"]}`\n\n{n["purpose"]}\n', ''
    if k == "entity":
        rows = "\n".join(f'| {x["name"]} | {x["type"]} | {x["note"]} |' for x in n["attributes"])
        return (f'{a}{_h(depth)} エンティティ: {n["name"]}\n\n識別子: {n["identity"]}\n\n'
                f'| 属性 | 型 | 備考 |\n|---|---|---|\n{rows}\n'), ''
    if k == "invariant":                                    # 所見2: 親を添える
        return f'{a}- **{parent}/INV-{n["id"]}** {n.get("statement") or n.get("rule")}\n', ''
    if k == "usecase":
        return (f'{a}{_h(depth)} 業務ユースケース: {parent}/UC-{n["id"]} {n["name"]}\n\n'
                f'- アクター: {n["actor"]}\n- 事前条件: {" / ".join(n["pre"])}\n'
                f'- 事後条件: {" / ".join(n["post"])}\n'), ''
    if k == "scenario":
        return (f'{a}- **SC-{n["id"]}**  \n  前提 {n["given"]}  \n'
                f'  もし {n["when"]}  \n  ならば {n["then"]}\n'), ''
    raise KeyError(k)

def md2_group(label, depth):                                # 所見3
    return f'\n{_h(depth)} {label}\n\n' if depth + 2 <= MAX_H else f'\n**{label}**\n\n'

# ---------------- html@1 ----------------
def h1(n, addr, depth, parent):
    e = H.escape
    d = f'<{ {"context":"section","aggregate":"section"}.get(n["kind"],"div") } class="kata-{n["kind"]}" data-addr="{e(addr)}" data-uid="{e(n["uid"])}">'
    k = n["kind"]
    if k == "context":   body = f'<h{min(depth+2,6)}>境界づけられた文脈: {e(n["name"])}</h{min(depth+2,6)}><p>{e(n["purpose"])}</p>'
    elif k == "aggregate": body = f'<h{min(depth+2,6)}>集約: {e(n["name"])}</h{min(depth+2,6)}><p>ルート: <code>{e(n["root"])}</code></p><p>{e(n["purpose"])}</p>'
    elif k == "entity":
        rows="".join(f'<tr><td>{e(x["name"])}</td><td>{e(x["type"])}</td><td>{e(x["note"])}</td></tr>' for x in n["attributes"])
        body = f'<h{min(depth+2,6)}>エンティティ: {e(n["name"])}</h{min(depth+2,6)}><p>識別子: {e(n["identity"])}</p><table><thead><tr><th>属性</th><th>型</th><th>備考</th></tr></thead><tbody>{rows}</tbody></table>'
    elif k == "invariant": body = f'<p><b>{e(parent)}/INV-{e(n["id"])}</b> {e(n.get("statement") or n.get("rule"))}</p>'
    elif k == "usecase":   body = f'<h{min(depth+2,6)}>業務ユースケース: {e(parent)}/UC-{e(n["id"])} {e(n["name"])}</h{min(depth+2,6)}><ul><li>アクター: {e(n["actor"])}</li><li>事前条件: {e(" / ".join(n["pre"]))}</li><li>事後条件: {e(" / ".join(n["post"]))}</li></ul>'
    elif k == "scenario":  body = f'<p><b>SC-{e(n["id"])}</b><br>前提 {e(n["given"])}<br>もし {e(n["when"])}<br>ならば {e(n["then"])}</p>'
    else: raise KeyError(k)
    tag = "section" if n["kind"] in ("context","aggregate") else "div"
    return d + body + "\n", f"</{tag}>\n"          # 入れ子にする

def h1_group(label, depth): return f'<h{min(depth+2,6)}>{H.escape(label)}</h{min(depth+2,6)}>\n'

CONTRACTS = {"md@2": (md2, md2_group, '<!-- kata: profile=ddd@1 contract=md@2 -->\n\n'),
             "html@1": (h1, h1_group, '<!-- kata: profile=ddd@1 contract=html@1 -->\n')}
