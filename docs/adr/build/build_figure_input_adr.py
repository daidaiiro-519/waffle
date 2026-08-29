import sys, pathlib, re
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S); sys.path.insert(0,"/home/daidaiiro/workspace/waffle/.claude/skills/design-svg")
from _common import CSS, sec, fold, tbl, extra
from svg_engine.compose import render_figure
from svg_engine.tokens import DEFAULT_THEME

FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
def figure(inner, vb, cap, minw="38rem"):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:{minw};width:100%;height:auto;display:block" {FF}>{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

th = dict(DEFAULT_THEME, **{
    "color.box-fill":"var(--surface)","color.box-stroke":"var(--rule)","color.ink":"var(--ink)",
    "color.line":"var(--ink-faint)","color.ink-faint":"var(--ink-faint)",
    "color.accent":"var(--infer)","color.accent-bg":"var(--surface)","size.stroke-width-focus":1.6,
    "font.family":"Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"})

s1 = render_figure(
    [{"id":"図","label":"図","role":"focus"},
     {"id":"a","label":"主張"},{"id":"b","label":"読み方"},{"id":"c","label":"置くもの"},
     {"id":"d","label":"つなぐもの"},{"id":"e","label":"読む枠"}],
    [{"from":"図","to":x} for x in ("a","b","c","d","e")],
    direction="TB", theme=th)
FIG1 = figure(re.sub(r'^<svg[^>]*>','',s1)[:-6],
              re.search(r'viewBox="([^"]+)"',s1).group(1),
  "<b>承認済みの仕様が定める、図が持つ5つ。</b>容れ物の名前は「図」で、"
  "「主張」はその中の1つの欄である ── 容れ物を主張と呼ぶのは誤り。"
  "この図はこのエンジン自身が描いている。", "26rem")

# ── 図2 ── 同じ主張でも、データの形で読める描き方が変わる
from svg_engine.tree import layout_tree
def wide(lay):
    n = [{"id":"根","label":"根"}] + [{"id":f"枝{i}","label":f"枝{i}"} for i in range(10)]
    e = [{"from":"根","to":f"枝{i}"} for i in range(10)]
    x = render_figure(n, e, layout=lay, theme=th)
    m = re.search(r'width="(\d+)" height="(\d+)"', x)
    return re.sub(r'^<svg[^>]*>','',x)[:-6], int(m.group(1)), int(m.group(2))
ia, wa, ha = wide(None)
ib, wb, hb = wide(layout_tree)
pad, gap = 16, 40
W = pad*2 + wa + gap + wb; H = pad*2 + 22 + max(ha, hb)
inner = (f'<text x="{pad}" y="{pad+11}" font-size="11" fill="var(--against)">'
         f'層状（既定） {wa}x{ha} ── 縦横比 {max(wa,ha)/min(wa,ha):.1f}</text>'
         f'<g transform="translate({pad},{pad+22})">{ia}</g>'
         f'<text x="{pad+wa+gap}" y="{pad+11}" font-size="11" fill="var(--infer)">'
         f'放射の木 {wb}x{hb} ── 縦横比 {max(wb,hb)/min(wb,hb):.1f}</text>'
         f'<g transform="translate({pad+wa+gap},{pad+22})">{ib}</g>')
FIG2 = figure(inner, f"0 0 {W} {H}",
  "<b>同じ「階層」でも、枝が10本になると層状では帯へ伸びて階層として読めない。</b>"
  "書き手が向きを選ぶのではなく、主張とデータの形から決まる、という根拠。"
  "どちらもこのエンジンが描いている。", "44rem")

body="".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>図の欄を、仕様が定める5つへ揃える</h1>'
 '<p class="lede">スキーマは <code>Figure</code> という欄を既に持っているが、'
 '中身が承認済みの仕様と合っていない。<b>主張の欄が無く、代わりに書き手が向きを選ぶ欄がある</b>'
 ' ── 描き方は主張から決まる、という承認済みの決定に反している。'
 'しかもこの欄を<b>描く実装は無く、使っている文書も0件</b>である。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">スキーマの <code>Figure</code> 欄の中身を、'
  '<b>仕様が定める5つ ── 主張・読み方・置くもの・つなぐもの・読む枠</b> へ揃える。'
  '<b>容れ物の名前は変えない</b>（仕様が「図」と呼んでいる）。</p>'
  '<div class="key"><span class="lbl">描き方の決まり方</span>'
  '<span class="txt"><b>描き方は、主張とデータの形から決まる。書き手は選ばない。</b>'
  'だからスキーマの <code>direction</code>（並びの向き）は落とす。'
  '主張だけで1つに固定するのでもない ── 同じ主張でも、データの形が変われば'
  '読める描き方が変わる（節03の実測）。<b>その判定を担う変換器は、呼ぶ側が持つ</b>'
  '（承認済みの決定）。</span></div>'
  '<div class="key"><span class="lbl">代償</span>'
  '<span class="txt">スキーマの欄を置き換える。<b>ただし移行の対象は0件</b>'
  '── いまの欄を使っている文書は1つも無く、描く実装も無い。'
  '置き換えるなら、いまがいちばん安い。</span></div></div>'),

 sec("02","仕様が定める5つと、いまの欄",
  "容れ物は合っている。合っていないのは中身である。",
  FIG1 + tbl(["仕様が定めるもの","いまのスキーマ","判定"],[
    ("keyrow",["<b>主張</b> ── 16通りのどれか","<b>無い</b>",
      "<b>足す。</b>これが無いと、その図が何を主張しているかが文書に残らない"]),
    ("",["読み方 ── 図全体として何が言えるか","<code>reading</code>","そのまま"]),
    ("",["置くもの","<code>nodes</code>","名前を揃える"]),
    ("",["つなぐもの","<code>edges</code>","名前を揃える"]),
    ("",["読む枠 ── 軸・基準・区切り・囲み","<code>groups</code>","<b>広げる。</b>いまは囲みしか持てない"]),
    ("keyrow",["──","<code>direction</code>","<b>落とす。</b>描き方を書き手に選ばせている"]),
  ])),

 sec("03","描き方は、主張だけでは決まらない",
  "同じ主張でも、データの形で読める描き方が変わる。だから書き手にも、主張の表にも固定できない。",
  FIG2 + tbl(["枝の数","層状（既定）","放射の木","読めるか"],[
    ("",["3本","240x140（縦横比 1.7）","287x230（1.2）","どちらでも読める"]),
    ("keyrow",["<b>10本</b>","<b>828x140（縦横比 5.9 ── 帯になる）</b>","339x298（1.1）",
      "<b>層状では階層として読めない</b>"]),
  ]),
  fold("いまの実装がどうなっているかを開く",
   '<p>いまの変換器は<b>階層を常に層状（上から下）で描く</b>。データの形で替える判定は'
   '実装されていない。上の実測が、実装すべき理由そのものになる ── '
   '判定の基準（どの縦横比で替えるか等）は、変換器の仕様で決める。</p>')),

 sec("04","5つに無い2つの欄をどうするか",
  "仕様は5つと定めるが、スキーマは7つ持っている。残る2つは性質が違う。",
  tbl(["欄","何を書くか","判定"],[
    ("keyrow",["<code>intent</code>","この図が<b>何を示すためのものか</b>を1文",
      "<b>落とす。</b>「どの主張か」は主張の欄が、「何が言えるか」は読み方の欄が持つ。"
      "目的だけを別に書くと、3つが少しずつ重なって、どれを読めばよいか決まらない"]),
    ("",["<code>notes</code>","読み手が<b>書き手と違う読み方をしかねない箇所</b>",
      "<b>残す。</b>読み方の欄自身が「注意書きはこちらへ」と指しており、"
      "役割が分かれている。ただし仕様は5つと数えているので、"
      "<b>仕様の側を6つに直すか、注釈を読み方の一部とみなすかを決める必要がある</b>"]),
  ]),
  fold("仕様と実装のどちらを直すかを開く",
   '<p>ここは<b>仕様の数え方の側に穴がある</b>可能性が高い。読み方の欄の書き方指示が'
   '「個々の節点・辺・囲みについて読み違えを防ぐ注意書きは、ここではなく注釈へ書きます」と'
   '明記しており、<b>注釈が存在する前提で書かれている</b>。5つという数え方だけが'
   'それを拾えていない。段2 で型を組み直すときに、仕様の側を確かめる。</p>')),

 sec("05","この欄が誰にも使われていないこと",
  "置き換えの安さを支える事実なので、測り方を残す。",
  tbl(["確かめたこと","結果"],[
    ("keyrow",["この欄を描く実装","<b>無い。</b>Python のどこも <code>figure</code> を触っていない"]),
    ("keyrow",["この欄を使っている文書","<b>0件</b>"]),
    ("",["主張の記法を描く実装","<b>ある。</b>変換器とエンジンで16件すべて通っている"]),
  ])),

 sec("06","答えないこと",None,
  '<p><b>いつ置き換えるか</b>は、この決定の外にある。型の作り直し（段2）の一部として運ぶ。</p>'
  '<p>主張の記法そのもの（16通りの必須・禁止）は既に承認済みで、ここでは変えない。</p>'
  '<p><b>どの形になったら描き方を替えるか</b>（縦横比の基準など）も、この決定の外にある。'
  '変換器の仕様で決める ── 変換器は呼ぶ側が持つと既に決まっている。</p>'),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span>'
 '<span class="m">2026-08-30</span></div></section>',

 sec("08","関連",None,"",
  fold("前後の決定を開く（4件）",
    tbl(["種類","対象"],[
      ("keyrow",["先立つ決定","図の語彙を、描き方の名前から主張の名前へ移す（承認済み）── "
        "<b>「描き方は主張から決まる」がここで決まっている。<code>direction</code> を落とす根拠</b>"]),
      ("keyrow",["先立つ決定","16の主張ごとの必須・禁止（承認済み）── <b>図が持つ5つはここで定まっている</b>"]),
      ("",["先立つ決定","変換器は仕様の側が持ち、描く側は目録だけを公開する（承認済み）"]),
      ("",["縛る対象","図を持ちうるすべての型の <code>Figure</code> 欄"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.2rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
"""
out=("<title>図の欄を、仕様が定める5つへ揃える</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-figure-input.html").write_text(out,encoding="utf-8")
print("書いた",len(out))
