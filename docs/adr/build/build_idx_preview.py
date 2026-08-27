import sys, json, pathlib, html
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S)
from _common import CSS, sec, fold, tbl, extra
e=html.escape
R=lambda n: pathlib.Path(f"{S}/{n}").read_text(encoding="utf-8")
wide=R("idx_wide.json"); nac=R("idx_narrow_ac.json"); nerr=R("idx_narrow_err.json")
old=R("idx_before.json")

FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
DEFS=('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs>')
def gb(x,y,w,h,t,s=None,a="var(--rule)",strong=False):
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" stroke="{a}" stroke-width="{2 if strong else 1}"/>'
    o+=f'<text x="{x+w/2}" y="{y+(h/2+5 if not s else h/2-3)}" text-anchor="middle" font-size="13" font-weight="600" fill="var(--ink)">{t}</text>'
    if s: o+=f'<text x="{x+w/2}" y="{y+h/2+15}" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">{s}</text>'
    return o
def ga(x1,y1,x2,y2,lb=None,lx=None,ly=None):
    o=f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/>'
    if lb: o+=f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">{lb}</text>'
    return o

a=''
a+=gb(14,40,150,46,"読み手","何かを知りたい")
a+=ga(164,63,236,63,"広く取る",200,54)
a+=gb(236,40,196,46,"1段目の索引","鍵と読み方だけ・全文の4%","var(--infer)",True)
a+=ga(432,63,504,63,"当たりを付ける",468,54)
a+=gb(504,40,180,46,"引くブロックを決める")
a+=ga(594,86,594,124)
a+=gb(452,124,284,46,"2段目の索引","そのブロックの鍵と説明を丸ごと","var(--infer)",True)
a+='<text x="736" y="152" font-size="10.5" fill="var(--ink-faint)">誤りなら2%</text>'
a+=ga(452,147,300,147,"要素を決める",376,138)
a+=gb(110,124,190,46,"その要素だけを引く")
FIG=gsvg=(f'<figure class="fig"><div class="scroll"><svg viewBox="0 0 830 190" role="img" '
  f'style="min-width:44rem;width:100%;height:auto;display:block" {FF}>{DEFS}{a}</svg></div>'
  f'<figcaption><b>広く取るときは1段目だけ。細かく取るときに、そのブロックの2段目を引く。</b>'
  f'全文を読むのは、最後に必要な要素だけになる。</figcaption></figure>')

sizes = tbl(["取り出し","中身","大きさ","全文に対して"],[
 ("keyrow",["<b>1段目</b>","12ブロックの鍵と読み方","1,213字","<b>4%</b>"]),
 ("",["2段目 ── 誤り","6件の鍵と説明","645字","2%"]),
 ("",["2段目 ── 受け入れ基準","37件の鍵と説明","5,543字","22%"]),
 ("keyrow",["<b>1段目＋誤りを引く</b>","当たりを付けて、1ブロック取る","1,858字","<b>7%</b>"]),
 ("",["（参考）全文","","24,414字","100%"]),
])

body="".join([
 '<header><p class="eyebrow">完成イメージ</p>'
 '<h1>索引を2段にすると、どう引けるか</h1>'
 '<p class="lede">広く取るときは<b>鍵と読み方だけ</b>。細かく取るときに、'
 'そのブロックの<b>鍵と説明</b>を引く。'
 'すべて <code>uc-render-document</code> の実物である。</p></header>',

 sec("01","引き方",
   "<b>2段に分けると、切り詰める長さを決めなくてよくなる。</b>"
   "広い索引は小さく保て、細かい索引は必要なブロックだけに限られる。",
   FIG),

 sec("02","大きさ",
   "当たりを付けて1ブロック取っても、<b>全文の7%</b>で済む。",
   sizes),

 f'<section><h2><span class="num">03</span>1段目 ── 広く取る</h2>'
 f'<p class="lead">鍵と読み方だけ。<b>この文書に何があるかではなく、どのブロックが何に答えるか</b>が分かる。</p>'
 f'<div class="scroll"><pre class="out">{e(wide)}</pre></div></section>',

 f'<section><h2><span class="num">04</span>2段目 ── 細かく取る</h2>'
 f'<p class="lead">ブロックを指定して引く。<b>鍵と説明が対</b>になっているので、'
 f'どの要素を取ればよいかを決められる。</p>'
 f'<h3 class="sub-h">誤り（6件・全部）</h3>'
 f'<div class="scroll"><pre class="out">{e(nerr)}</pre></div>'
 f'<h3 class="sub-h">受け入れ基準（37件のうち先頭5件）</h3>'
 f'<div class="scroll"><pre class="out">{e(nac)}</pre></div></section>',

 f'<section><h2><span class="num">05</span>いまの索引と比べる</h2>'
 f'<p class="lead"><b>いまの索引は、どの文書でも同じ内容になる。</b>'
 f'型の読み方の写しなので、その文書について何も語らない。</p>'
 f'<div class="scroll"><pre class="out">{e(old)}</pre></div>'
 f'<p class="blob">1段目と見比べると、<b>持っている情報はほぼ同じ</b>である。'
 f'違うのは<b>保存しているかどうか</b>と、'
 f'<b>2段目で文書の中身へ降りられるかどうか</b>。</p></section>',

 sec("06","この形で決まること",
   "欄が7つから減り、切り詰める長さを決める必要も無くなった。",
   tbl(["論点","この形では"],[
     ("keyrow",["索引が返す欄","<b>1段目は鍵と読み方の2つ。</b>2段目は鍵と説明の2つ"]),
     ("keyrow",["切り詰める長さ","<b>決めなくてよい。</b>2段目は必要なブロックだけなので、丸ごと載せられる"]),
     ("",["落とした欄","形・量・見出し・欄の名前。"
       "<b>鍵と説明があれば導けるか、読み方と重なる</b>"]),
     ("",["保存するか","<b>しない。</b>どちらの段も、取り出すときに組み立てる"]),
   ])),

 sec("07","まだ決めていないこと",
   "2つ残る。<b>どちらも実際に使ってみないと決められない</b>。",
   tbl(["項目","何が分からないか"],[
     ("",["1段目に量を戻すか",
       "「37件ある」が分かると、2段目を引くかどうかの判断が変わるかもしれない。"
       "<b>いまは落としているが、使ってみて要るなら戻す</b>"]),
     ("",["2段目をブロック単位より細かくできるか",
       "37件のうち一部だけを引く道があるか。<b>いまは1ブロック丸ごと</b>"]),
   ])),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
pre.out{margin:0;padding:.9rem 1rem;font-family:var(--mono);font-size:.74rem;
        line-height:1.75;white-space:pre;color:var(--ink-soft)}
.lead{font-family:var(--serif);font-size:1.02rem;font-weight:600;line-height:1.65;
      border-left:3px solid var(--ink);padding-left:.85rem}
"""
out=("<title>索引を2段にすると、どう引けるか</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/index-two-tier-preview.html").write_text(out,encoding="utf-8")
print("書いた",len(out))
