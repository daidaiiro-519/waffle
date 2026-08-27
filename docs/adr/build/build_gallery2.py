import sys, json, pathlib, html
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S)
from _common import CSS, sec, fold, tbl, extra
from md2html import conv
e=html.escape
parts=json.loads(pathlib.Path(S+"/parts_out.json").read_text(encoding="utf-8"))
figs=json.loads(pathlib.Path(S+"/notation_figs.json").read_text(encoding="utf-8"))
figcss=pathlib.Path(S+"/fig_css.txt").read_text(encoding="utf-8")

MEANING={"paragraph":("文","ひとかたまりの文"),"list":("並び","順不同に並べる"),
 "table":("表","同じ欄を持つものを並べて比べる"),"kvtable":("名前と値の組","1つのものの、名前と値"),
 "keyvalue":("名前と値の組","1つのものの、名前と値"),"code":("字面","そのまま見せる"),
 "section":("繰り返して入れ子で描く","器 ── 自分では描かない"),"object":("降りる","経路 ── 自分では描かない"),
 "divider":("（落とす）","区切り線は意味を持たない")}
GROUP={"paragraph":"意味","list":"意味","table":"意味","code":"意味",
 "kvtable":"重複","keyvalue":"重複","section":"器","object":"器","divider":"落とす"}
TAGCLS={"意味":"infer","重複":"against","器":"assume","落とす":"faint"}

def pane(label, inner, cls=""):
    return (f'<div class="pn {cls}"><span class="pl">{label}</span>{inner}</div>')
def pre(txt, cls="code"):
    return f'<div class="scroll"><pre class="{cls}">{e(txt)}</pre></div>'
def jsonp(o):
    return pre(json.dumps(o,ensure_ascii=False,indent=1))

def part_card(p):
    n=p["name"]; mean,says=MEANING.get(n,(n,""))
    g=GROUP.get(n,"意味")
    return ('<article class="pc">'
      f'<header class="pch"><code class="pn0">{n}</code>'
      f'<span class="arrow">→</span><b class="mean">{mean}</b>'
      f'<span class="psays">{says}</span>'
      f'<span class="gtag g-{TAGCLS[g]}">{g}</span></header>'
      '<div class="grid3">'
      + pane("宣言", jsonp(p["decl"]))
      + pane("描いた Markdown", pre(p["md"] or "（何も出ない）","code"))
      + pane("プレビュー", f'<div class="prev">{conv(p["md"]) if p["md"].strip() else "<p class=mdp>（何も出ない）</p>"}</div>')
      + '</div></article>')

def fig_card(f):
    d=f["decl"]
    decl = jsonp(d) if isinstance(d,dict) else pre(str(d))
    return ('<article class="pc">'
      f'<header class="pch"><b class="mean">{f["name"]}</b>'
      f'<span class="psays">{e(f["note"].split("<")[0][:46])}</span></header>'
      '<div class="grid2">'
      + pane("宣言", decl)
      + pane("描いた図（SVG）", f'<div class="figout">{f["svg"] or "（図が残っていない）"}</div>')
      + '</div></article>')

text=[p for p in parts if p["group"]=="文字"]
core=[f for f in figs[:16]]
hard=[f for f in figs[16:]]

body="".join([
 '<header><p class="eyebrow">語彙ごとの描画イメージ</p>'
 '<h1>意味の名前で書いたとき、何がどう出るか</h1>'
 '<p class="lede">文字の部品は<b>宣言・Markdown・プレビュー</b>の3列、'
 '図は<b>宣言と描いた SVG</b>の2列で並べる。'
 'Markdown はその場で描いたもの、プレビューはその Markdown をそのまま見た目にしたもの、'
 '図は以前に実際に描かれたものである。</p></header>',

 sec("01","文字の部品 ── いまの名前と、意味の名前",
   "9つのうち<b>意味として残るのは4つ</b>。2つは同じ意味の重複、2つは器・経路、1つは落とす。",
   tbl(["いまの名前","意味の名前","群"],[
     ("",["<code>paragraph</code>","文","意味"]),
     ("",["<code>list</code>","並び<span class='sub'>（要素の形から導ける）</span>","意味"]),
     ("",["<code>table</code>","表","意味"]),
     ("",["<code>code</code>","字面","意味"]),
     ("keyrow",["<code>kvtable</code> と <code>keyvalue</code>","<b>名前と値の組</b>（1つに畳む）","重複"]),
     ("",["<code>section</code>","繰り返して入れ子で描く","器"]),
     ("",["<code>object</code>","降りる","経路"]),
     ("",["<code>divider</code>","—","落とす"]),
   ])),

 f'<section><h2><span class="num">02</span>文字の部品 ── 宣言・Markdown・プレビュー</h2>'
 f'<p class="lead">同じ宣言から、Markdown とその見た目を並べる。</p>'
 f'<div class="cards">{"".join(part_card(p) for p in text)}</div></section>',

 f'<section><h2><span class="num">03</span>図 ── 16の主張</h2>'
 f'<p class="lead">欄は <code>items</code>・<code>links</code>・<code>frame</code> の3つだけ。'
 f'<b>どれを書けるかは主張が決め、描き方はそこから決まる。書き手は描き方を選ばない。</b></p>'
 f'<div class="cards">{"".join(fig_card(f) for f in core)}</div></section>',

 f'<section><h2><span class="num">04</span>難しい実物で試したもの</h2>'
 f'<p class="lead">組み合わせが要る4件。<b>入れ子・囲み・突き合わせ</b>がここに出る。</p>'
 f'<div class="cards">{"".join(fig_card(f) for f in hard)}</div></section>',

 sec("05","この一覧から見えること",
   "承認済みの決定で足りないと判定した4つが、実物でも確かめられる。",
   tbl(["足りないもの","この一覧のどこに出るか"],[
     ("keyrow",["突き合わせる器","<b>変更前と変更後</b>が <code>対応</code> で書かれている。"
       "格子の主張と器を兼ねている"]),
     ("keyrow",["読む必要の度合い","<b>文字の部品に一つも無い。</b>"
       "この一覧の折り畳みも、宣言からではなく HTML を手で書いている"]),
     ("",["<code>frame.groups</code>","<b>やり取りの順序</b>に「frame に 'groups' は書けない」"
       "という注記が残り、図が描かれていない"]),
     ("",["差分の語彙","<b>変更前と変更後</b>で <code>muted</code>・<code>focus</code> を流用している。"
       "落とした・足した・変えた が無い"]),
   ])),
])

extra2 = extra + figcss + """
.cards{display:flex;flex-direction:column;gap:1.1rem}
.pc{border:1px solid var(--rule);border-radius:3px;background:var(--surface);overflow:hidden}
.pch{display:flex;flex-wrap:wrap;align-items:baseline;gap:.6rem;padding:.7rem .95rem;
     background:var(--surface-2);border-bottom:1px solid var(--rule)}
.pn0{font-size:.85rem;background:none;border:none;padding:0;color:var(--ink-faint)}
.arrow{color:var(--ink-faint);font-size:.8rem}
.mean{font-size:.98rem;font-family:var(--serif)}
.psays{font-size:.82rem;color:var(--ink-faint)}
.gtag{margin-left:auto;font-family:var(--mono);font-size:.66rem;padding:.1em .5em;border-radius:2px;white-space:nowrap}
.g-infer{color:var(--infer);background:var(--infer-bg)}
.g-against{color:var(--against);background:var(--against-bg)}
.g-assume{color:var(--assume);background:var(--assume-bg)}
.g-faint{color:var(--ink-faint);background:var(--surface-2)}
.grid3{display:grid;grid-template-columns:minmax(0,.95fr) minmax(0,1fr) minmax(0,1.1fr)}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr)}
@media(max-width:60rem){.grid3,.grid2{grid-template-columns:minmax(0,1fr)}}
.grid3>*+*,.grid2>*+*{border-left:1px solid var(--rule-soft)}
@media(max-width:60rem){.grid3>*+*,.grid2>*+*{border-left:none;border-top:1px solid var(--rule-soft)}}
.pn{display:flex;flex-direction:column;min-width:0}
.pl{font-family:var(--mono);font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;
    color:var(--ink-faint);padding:.6rem .95rem .3rem}
.pn .scroll{border:none;border-radius:0;background:none;flex:1}
.pn pre{margin:0;padding:0 .95rem .85rem;font-family:var(--mono);font-size:.74rem;
        line-height:1.7;white-space:pre;color:var(--ink-soft)}
.prev{padding:.15rem .95rem .9rem;font-size:.86rem;line-height:1.8}
.prev>*+*{margin-top:.55rem}
.mdh{font-family:var(--serif);font-size:.95rem;font-weight:600;margin:0}
.mdp{margin:0}
.mdul,.mdol{margin:0;padding-left:1.15rem}
.mdcode{margin:0;padding:.5rem .7rem;background:var(--surface-2);border:1px solid var(--rule-soft);
        border-radius:3px;font-family:var(--mono);font-size:.75rem;overflow-x:auto;white-space:pre}
.mdtblwrap{overflow-x:auto}
.mdtbl{border-collapse:collapse;font-size:.8rem;min-width:0;width:100%}
.mdtbl th,.mdtbl td{border:1px solid var(--rule-soft);padding:.3rem .5rem;text-align:left}
.mdtbl th{background:var(--surface-2);font-weight:600}
.mdhr{border:none;border-top:1px solid var(--rule);margin:.4rem 0}
.figout{padding:.3rem .95rem .9rem}
.figout svg{max-width:100%;height:auto}
.lead{font-family:var(--serif);font-size:1.02rem;font-weight:600;line-height:1.65;
      border-left:3px solid var(--ink);padding-left:.85rem}
"""
out=("<title>語彙ごとの描画イメージ</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/vocabulary-gallery.html").write_text(out,encoding="utf-8")
print("書いた",len(out))
