import json, pathlib, sys
sys.path.insert(0, ".")
from cases import CASES
from draw import render
from grammar import RULES

CSS = """
  :root{--paper:#EDF0F3;--surface:#FFF;--ink:#171B23;--ink-soft:#4B5563;
        --ink-faint:#79828F;--rule:#D3DAE2;--acc:#16636B;
        --sans:"Hiragino Kaku Gothic ProN","Noto Sans JP",system-ui,sans-serif;
        --mono:ui-monospace,Menlo,Consolas,monospace}
  @media(prefers-color-scheme:dark){:root:not([data-theme="light"]){
        --paper:#10131A;--surface:#191E27;--ink:#E3E8EF;--ink-soft:#A9B3C0;
        --ink-faint:#7B8694;--rule:#2E3742;--acc:#6BC0C7}}
  *{box-sizing:border-box}
  body{margin:0;padding:clamp(1.5rem,4vw,3rem) clamp(1rem,3vw,2rem) 5rem;
       background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.8}
  main{max-width:64rem;margin:0 auto;display:flex;flex-direction:column;gap:1.4rem}
  h1{font-size:clamp(1.5rem,4vw,2rem);margin:.4rem 0 0;font-weight:600}
  .eyebrow{font-family:var(--mono);font-size:.68rem;letter-spacing:.16em;
           text-transform:uppercase;color:var(--ink-faint);margin:0}
  .lede{color:var(--ink-soft);margin:.6rem 0 0;max-width:44rem}
  h2{font-size:1rem;margin:1.4rem 0 -.2rem}
  .card{background:var(--surface);border:1px solid var(--rule);border-radius:12px;
        padding:1rem 1.1rem 1.2rem;display:flex;flex-direction:column;gap:.6rem}
  .card header{display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap}
  .card h3{margin:0;font-size:.95rem}
  .fam{font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;padding:.05rem .4rem;
       border-radius:4px;border:1px solid currentColor;color:var(--acc)}
  .note{font-size:.8rem;color:var(--ink-faint)}
  .pair{display:grid;gap:1rem}
  @media(min-width:56rem){.pair{grid-template-columns:minmax(0,1fr) minmax(0,22rem)}}
  .stage{background:var(--paper);border-radius:8px;padding:.9rem;overflow-x:auto;
         display:flex;justify-content:center;align-items:center;min-height:6rem}
  pre{margin:0;font-family:var(--mono);font-size:.66rem;line-height:1.6;
      background:var(--paper);border-radius:8px;padding:.9rem;overflow-x:auto;
      color:var(--ink-soft);max-height:22rem}
  .f-fig{display:block;max-width:100%;height:auto}
"""

def brief(fig):
    d = {"asserts": fig["asserts"]}
    for k in ("items", "links", "frame"):
        if fig.get(k):
            d[k] = fig[k]
    s = json.dumps(d, ensure_ascii=False, indent=1)
    return s if len(s) < 1500 else s[:1500] + "\n …"

rows = []
for name, fig in CASES:
    fam = "関係" if name in ("つながり","階層","包含","順序","循環","対応") else "量"
    rows.append(f'<section class="card"><header><h3>{name}</h3>'
                f'<span class="fam">{fam}</span>'
                f'<span class="note">{RULES[name]["note"]}</span></header>'
                f'<div class="pair"><div class="stage">{render(fig)}</div>'
                f'<pre>{brief(fig)}</pre></div></section>')

top = ('<header><p class="eyebrow">図解の記法 — 決められたルールの範囲内で組む</p>'
       '<h1>欄は3つ、書ける名前は16、主張は15</h1>'
       '<p class="lede">左が描いたもの、右が書いたもの。'
       '主張ごとに入力の形を変えていません。<b>どの欄を書けるかは主張が決め、'
       '描き方はそこから従属して決まります</b>。書き手は描き方を選びません。</p></header>')

html = ("<title>図解の記法</title><style>" + CSS + "</style><main>" + top
        + "<h2>関係を主張するもの</h2>" + "".join(rows[:6])
        + "<h2>量を主張するもの</h2>" + "".join(rows[6:]) + "</main>")
out = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/figure-notation.html")
out.write_text(html, encoding="utf-8")
print("書いた", out.stat().st_size, "bytes /", len(rows), "枚")