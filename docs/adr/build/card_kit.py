import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, extra

OUT = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr")

def zone(title, badge, inner):
    b = f'<span class="cnt">{badge}</span>' if badge else ""
    return f'<section class="zn"><h4 class="zn-h"><span>{title}</span>{b}</h4>{inner}</section>'

def pair(k, v):
    return f'<div class="pr"><span class="pr-k">{k}</span><span class="pr-v">{v}</span></div>'

def head(kind_ja, did, ja, en, lede, callout=None, foot=None):
    h = ('<div class="rh">'
         f'<div class="rchips"><span class="chip kind">{kind_ja}</span>'
         f'<span class="chip id">{did}</span></div>'
         f'<h3 class="rt">{ja}</h3><p class="ren">{en}</p>'
         f'<p class="rlede">{lede}</p>')
    if callout:
        t, b = callout
        h += (f'<div class="actor"><p class="ac-who">{t}</p>'
              f'<p class="ac-want">{b}</p></div>')
    if foot:
        k, v = foot
        h += (f'<div class="rchips foot-chips"><span class="chip lbl">{k}</span>'
              f'<span class="chip ref">{v}</span></div>')
    return h + "</div>"

def two(lh, lbody, rh, rbody, arrow=True):
    a = '<div class="io-a">→</div>' if arrow else '<div class="io-a"></div>'
    return ('<div class="io">'
            f'<div class="io-c"><p class="io-h">{lh}</p>{lbody}</div>'
            + a +
            f'<div class="io-c"><p class="io-h">{rh}</p>{rbody}</div></div>')

def note(t): return f'<div class="znote">{t}</div>'

def page(slug, n, kind_ja, kind_en, lede, docu, *_ignored):
    """1種別ぶんの完成イメージ。

    描かれる文書だけを載せる。欄の定義（必須か・何を書くか）は
    「Domain の型」が持つので、ここには置かない ── 同じことを2か所に書かないため。
    """
    body = (f'<header class="ph"><p class="eyebrow">完成イメージ ── Domain の型 {n} / 8</p>'
            f'<h1>{kind_ja}<span class="h1en">{kind_en}</span></h1>'
            f'<p class="lede">{lede}</p></header>'
            f'<div class="rdoc">{docu}</div>'
            '<p class="foot"><b>これは、型を起こしたあとに描かれる姿を手で描いたものである。</b>'
            '描画の機能はまだ無い。'
            '欄の定義（必須か・何を書くか）と、いまとの差・そう決めた理由は'
            '<a href="https://claude.ai/code/artifact/e0e51605-4fd9-4212-ace1-28fa5bf1075d">'
            'Domain の型</a>が持つ。</p>')
    html = (f"<title>{kind_ja} ── 完成イメージ</title>"
            f"<style>{CSS}\n{CARD_CSS}</style>"
            f'<div class="wrap narrow">{body}</div>')
    (OUT / f"tier2-domain-{slug}.html").write_text(html, encoding="utf-8")
    return len(html)

CARD_CSS = extra + """
.h1en{display:block;font-family:var(--mono);font-size:.9rem;font-weight:400;
      color:var(--ink-faint);margin-top:.35rem}
.foot{font-size:.82rem;line-height:1.75;color:var(--ink-faint);
      border-top:1px solid var(--rule);padding-top:1rem}

.rdoc{border:1px solid var(--rule);border-radius:3px;background:var(--surface);overflow:hidden}
.rh{background:var(--surface-2);border-bottom:1px solid var(--rule);
    padding:1.6rem 1.5rem 1.3rem;display:flex;flex-direction:column;gap:.5rem}
.rchips{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center}
.foot-chips{margin-top:.5rem}
.chip{font-family:var(--mono);font-size:.7rem;line-height:1;padding:.4em .65em;border-radius:2px;
      border:1px solid var(--rule);color:var(--ink-faint);background:var(--surface)}
.chip.kind{border-color:var(--infer);color:var(--infer);background:var(--infer-bg);
           font-family:var(--sans);font-weight:600}
.chip.id{color:var(--ink-soft)}
.chip.ref{font-weight:600;color:var(--ink-soft)}
.chip.lbl{border:none;background:none;padding-left:0;font-family:var(--sans);font-size:.76rem}
.rt{font-family:var(--serif);font-size:clamp(1.35rem,3.2vw,1.7rem);font-weight:600;
    margin:.15rem 0 0;line-height:1.4}
.ren{font-family:var(--mono);font-size:.86rem;color:var(--ink-faint);margin:0}
.rlede{font-size:.98rem;line-height:1.85;color:var(--ink-soft);margin:.5rem 0 0;max-width:34rem}
.actor{margin:.6rem 0 0;padding-left:.95rem;border-left:3px solid var(--infer)}
.ac-who{font-family:var(--serif);font-size:1.02rem;font-weight:600;margin:0}
.ac-want{font-size:.91rem;line-height:1.8;color:var(--ink-soft);margin:.15rem 0 0}

.zn{padding:0 1.5rem;margin-top:1.7rem;display:flex;flex-direction:column;gap:.9rem}
.zn:last-child{padding-bottom:1.6rem}
.zn-h{display:flex;align-items:center;gap:.8rem;margin:0;font-family:var(--serif);
      font-size:1.02rem;font-weight:600;color:var(--ink);flex-wrap:wrap}
.zn-h>span:first-child{flex:none}
.zn-h::after{content:"";flex:1;height:1px;background:var(--rule);order:9}
.cnt{font-family:var(--mono);font-size:.68rem;font-weight:400;color:var(--ink-faint);
     border:1px solid var(--rule);border-radius:2px;padding:.3em .55em;flex:none}

/* 入口と出口を、横に並べて対にする */
.io{display:grid;grid-template-columns:1fr auto 1fr;gap:1rem;align-items:start}
.io-c{border:1px solid var(--rule-soft);border-radius:2px;background:var(--surface-2);
      padding:.85rem .95rem;min-width:0}
.io-h{font-size:.78rem;color:var(--ink-faint);margin:0 0 .45rem}
.io-r{display:flex;flex-wrap:wrap;gap:.15rem .7rem;align-items:baseline;font-size:.92rem}
.io-a{align-self:center;color:var(--ink-faint);font-size:1.1rem}
@media(max-width:46rem){.io{grid-template-columns:1fr}.io-a{display:none}}

.pr{display:flex;flex-wrap:wrap;gap:.15rem .8rem;align-items:baseline;font-size:.9rem;line-height:1.8}
.pr-k{flex:none}
.pr-v{color:var(--ink-soft);min-width:0}

.figwrap{border:1px solid var(--rule-soft);border-radius:2px;background:#FFF;padding:.9rem .6rem}
.wf-fig{display:block;max-width:100%;height:auto;overflow:visible}

.crit .scroll{border-color:var(--infer)}
.crit thead th{background:var(--infer-bg);color:var(--infer)}
.gk{margin:0;font-family:var(--mono);font-size:.76rem;line-height:1.8;background:var(--surface-2);
    border:1px solid var(--rule-soft);border-radius:2px;padding:.75rem .85rem;overflow-x:auto;
    white-space:pre;color:var(--ink)}
.errs{border-top:1px solid var(--rule-soft);padding-top:.85rem}
.errs-h{font-size:.78rem;color:var(--ink-faint);margin:0 0 .35rem}
.post{margin:0;padding-left:1.1rem;font-size:.92rem;line-height:1.85;color:var(--ink-soft)}
.zn .sub{font-size:.82rem;line-height:1.7}

@media(max-width:46rem){
  .rh{padding:1.3rem 1.1rem 1.1rem}
  .zn{padding:0 1.1rem;margin-top:1.5rem}
}
.znote{font-size:.85rem;line-height:1.8;color:var(--ink-soft);padding-left:.85rem;
       border-left:2px solid var(--rule)}
.znote b{color:var(--ink)}
.big{font-family:var(--serif);font-size:1.25rem;font-weight:600}
.wrap.narrow{max-width:48rem;gap:1.6rem}
.ph{gap:.5rem}
.ph .lede{font-size:.95rem}
"""
