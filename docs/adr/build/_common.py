import pathlib
S = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/build")
CSS = S.joinpath("newfmt.css").read_text(encoding="utf-8")

def sec(n,t,lead,main,fold=None):
    h=f'<section><h2><span class="num">{n}</span>{t}</h2>'
    if lead: h+=f'<p class="lead">{lead}</p>'
    h+=main
    if fold: h+=fold
    return h+"</section>"
def fold(sm,inner): return f'<details class="fold"><summary>{sm}</summary>{inner}</details>'
def tbl(head,rows):
    hh="".join(f"<th>{c}</th>" for c in head)
    bb="".join(f'<tr class="{r[0]}">'+"".join(f'<td class="cond">{c}</td>' if i==0 else f"<td>{c}</td>"
       for i,c in enumerate(r[1]))+"</tr>" for r in rows)
    return f'<div class="scroll"><table><thead><tr>{hh}</tr></thead><tbody>{bb}</tbody></table></div>'
def step(k,l,t): return f'<div class="step {k}"><span class="lbl">{l}</span><span class="txt">{t}</span></div>'
def joint(t): return f'<div class="joint">{t}</div>'
ok='<span class="mk ok"><span class="sym">○</span></span>'
ng='<span class="mk ng"><span class="sym">×</span></span>'


extra = """
.lead{font-family:var(--serif);font-size:1.02rem;font-weight:600;line-height:1.65;border-left:3px solid var(--ink);padding-left:.85rem}
.mk{display:inline-flex;align-items:center;gap:.4rem;white-space:nowrap}
.mk .sym{font-size:1.05rem;line-height:1;font-weight:700}
.mk.ok .sym{color:#1B6B4A} .mk.ng .sym{color:#9A3B44}
.keycol{background:#F5EDDF;color:#7A4E12}
.keyrow td{background:#F5EDDF}
.keytag{font-family:var(--mono);font-size:.63rem;color:#7A4E12;background:var(--surface);
        border:1px solid #7A4E12;border-radius:2px;padding:.06em .4em;margin-left:.5rem;white-space:nowrap}
.pickrow td{background:#E9F0F6}
.sub{font-weight:400;font-size:.82rem;color:var(--ink-faint)}
.fold{border:1px solid var(--rule);border-radius:2px;background:var(--surface)}
.fold>summary{cursor:pointer;padding:.7rem .95rem;font-size:.86rem;color:var(--ink-soft);
              list-style:none;display:flex;align-items:center;gap:.5rem}
.fold>summary::before{content:"▸";color:var(--ink-faint);font-size:.8rem}
.fold[open]>summary::before{content:"▾"}
.fold>summary::-webkit-details-marker{display:none}
.fold .scroll{border:none;border-top:1px solid var(--rule);border-radius:0}
.foldnote{font-size:.84rem;line-height:1.75;color:var(--ink-soft);padding:.8rem .95rem;border-top:1px solid var(--rule-soft)}
.foldnote b{color:var(--ink)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  .mk.ok .sym{color:#79C5A0} .mk.ng .sym{color:#DE9AA1}
  .keycol,.keyrow td{background:#2A2216;color:#D9B674}
  .keytag{color:#D9B674;border-color:#D9B674} .pickrow td{background:#172430}}}
"""
