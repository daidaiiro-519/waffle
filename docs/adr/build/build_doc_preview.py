import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, extra
C=lambda s: f"<code>{s}</code>"
FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
DEFS=('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs>')
def gb(x,y,w,h,t,s=None,a="var(--rule)",strong=False):
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" stroke="{a}" stroke-width="{2 if strong else 1}"/>'
    o+=f'<text x="{x+w/2}" y="{y+(h/2+5 if not s else h/2-3)}" text-anchor="middle" font-size="12.5" font-weight="600" fill="var(--ink)">{t}</text>'
    if s: o+=f'<text x="{x+w/2}" y="{y+h/2+15}" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">{s}</text>'
    return o
def ga(x1,y1,x2,y2,lb=None,lx=None,ly=None):
    o=f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/>'
    if lb: o+=f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">{lb}</text>'
    return o
def gsvg(vb,inner,cap):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:44rem;width:100%;height:auto;display:block" {FF}>{DEFS}{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

# 型の解決 ── 段組み: col1 x14w150(→164) / gap136 / col2 x300w170(→470) / gap136 / col3 x606w180
a=''
a+=gb(14,58,150,50,"ユースケース","調整だけを担う","var(--assume)",True)
a+=ga(164,72,300,44)
a+='<text x="232" y="30" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">\u2460 schemaRef を解決する</text>'
a+=gb(300,20,170,48,"\u578b\uff08\u6bb52\uff09",None,"var(--rule)")
a+=ga(164,96,300,128)
a+='<text x="232" y="160" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">\u2461 解決した型を引数で渡す</text>'
a+=gb(300,104,170,50,"Document","参照は持つが解決しない","var(--infer)",True)
a+=ga(470,129,606,129)
a+='<text x="538" y="160" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">\u2462 判定する／描く</text>'
a+=gb(606,104,180,50,"成果物","適合の可否／描いたもの")
FIG1=gsvg("0 0 800 180",a,
 "<b>解決するのはユースケース。</b>Document は <code>schemaRef</code> を持つが、"
 "自分では取りに行かない \u2500\u2500 解決した相手を引数で受け取る。")

# 骨格を作る／値を埋める
b=''
b+=gb(14,20,150,46,"ユースケース",None,"var(--assume)")
b+=ga(164,43,300,43)
b+='<text x="232" y="34" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">\u2460 型を解決する</text>'
b+=gb(300,20,170,46,"\u578b\uff08\u6bb52\uff09",None,"var(--infer)")
b+=ga(470,43,606,43)
b+='<text x="538" y="34" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">\u2461 骨格を作る</text>'
b+=gb(606,20,190,46,"器と書き方の指針","新しい Document","var(--infer)",True)
b+=gb(14,116,150,46,"書き手",None,"var(--assume)")
b+=ga(164,139,300,139)
b+='<text x="232" y="130" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">\u2462 値を決める</text>'
b+=gb(300,116,170,46,"Document",None,"var(--infer)")
b+=ga(470,139,606,139)
b+='<text x="538" y="130" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">\u2463 値を埋める</text>'
b+=gb(606,116,190,46,"道の先へ置く","型は要らない")
FIG2=gsvg("0 0 810 182",b,
 "<b>骨格を作るのは型のコマンド、値を埋めるのは Document のコマンド。</b>"
 "作られる側がまだ無いので、器は型が作る。")

holds = tbl(["欄","中身","誰が入れるか"],[
 ("keyrow",["<b>識別子</b>","この文書を一意に指す","骨格を作るときに与える"]),
 ("",["<b>型と版</b>",f"{C('DomainSpecSchema/v11')} のような参照","同上"]),
 ("",["<b>種別</b>","どの枝か","同上"]),
 ("",["<b>役どころ</b>","実体か雛形か","書き手（既定は実体）"]),
 ("keyrow",["<b>使ってよいか</b>","下書き／有効／非推奨","<b>人が決める。導けない唯一のもの</b>"]),
 ("",["<b>時刻</b>","作られた時／直された時","機械"]),
 ("",["<b>ラベル</b>","文書に付ける印","書き手"]),
 ("keyrow",["<b>content</b>","<b>型を知らない木。</b>値は外から渡される","<b>書き手。ここだけが値埋めの対象</b>"]),
])

cmds = tbl(["操作","誰の","入力","返す／変える","型が要るか","完結するか"],[
 ("keyrow",["<b>骨格を作る</b>","<b>型（段2）</b>","識別子・種別",
   "器と書き方の指針","<b>型そのもの</b>","<b>完結する</b>"]),
 ("keyrow",["<b>値を埋める</b>","Document","道・値","content を書き換える",
   "<b>要らない</b>","<b>完結する</b>"]),
 ("",["<b>値を取り出す</b>","Document","道","その道の値",
   "<b>要らない</b>","<b>完結する</b>"]),
 ("keyrow",["<b>逸脱していないか判定する</b>","Document","<b>解決済みの型</b>",
   "適合しているかどうか","<b>要る</b>","<b>完結する</b>"]),
 ("keyrow",["<b>描く</b>","Document","<b>解決済みの型</b>","成果物",
   "<b>要る</b>","<b>完結する</b>"]),
 ("",["<b>終端化する</b>","Document","後続の版","使ってよいかを非推奨へ",
   "<b>要らない</b>","<b>完結する</b>"]),
 ("",["<b>読み方の指針を返す</b>","<b>型（段2）</b>","ブロックの鍵","そのブロックの読み方",
   "<b>型そのもの</b>","<b>完結する</b>"]),
])

combo = tbl(["やりたいこと","どう組み合わせるか","併用が要るか"],[
 ("keyrow",["<b>索引を取り出す</b>",
   "型へ<b>読み方の指針</b>を、Document へ<b>中身</b>を求め、<b>ユースケースが束ねる</b>",
   "<b>要る。</b>両方の持ち物が混ざる"]),
 ("keyrow",["<b>描く</b>",
   "ユースケースが型を解決 → <b>Document が判定</b> → <b>Document が描く</b>",
   "<b>要らない。</b>型は引数として渡るだけ"]),
 ("",["新しい文書を起こす",
   "ユースケースが型を解決 → <b>型が骨格を作る</b> → 書き手が値を決める → "
   "<b>Document が値を埋める</b>","<b>要らない。</b>順に呼ぶだけ"]),
 ("",["逸脱を確かめる","ユースケースが型を解決 → <b>Document が判定</b>","<b>要らない</b>"]),
])

pre = tbl(["操作","事前に成り立っていること","終わったとき成り立っていること"],[
 ("",["骨格を作る","型が在り、識別子と種別が与えられている",
   "器が型の形どおりに起き、書き方の指針が添う"]),
 ("",["値を埋める","道が与えられている","その道の先に値が置かれている"]),
 ("",["値を取り出す","道が与えられている","その道の先の値が返る"]),
 ("keyrow",["<b>描く</b>",
   "<b>型が引数で渡され、逸脱していない</b>",
   "決まった場所に成果物が在る"]),
 ("",["終端化する","後続の版が在る","使ってよいかが非推奨になっている"]),
])

body="".join([
 '<header><p class="eyebrow">完成イメージ</p>'
 '<h1>Document は何を持ち、どう呼ばれるか</h1>'
 '<p class="lede">持ち物・操作の中身・型の解決のされ方・'
 '<b>型の操作との併用が要るかどうか</b>を、ひととおり並べる。</p></header>',

 sec("01","Document が持つもの",
   "<b>導けないものだけ。</b>値埋めの対象は content ただひとつである。",
   holds),

 sec("02","型はどう解決されるか",
   "<b>解決するのはユースケース。</b>Document は参照を持つが、自分では取りに行かない。",
   FIG1),

 sec("03","操作の一覧",
   "<b>どれも、それ自身では完結する。</b>型が要る操作は、解決済みの型を引数で受け取る。",
   cmds,
   fold("「完結する」とはどういう意味か",
     '<p class="blob">その操作の中で、<b>ほかの集約のコマンドを呼ばない</b>という意味である。'
     '型が要る操作も、<b>型は引数として渡ってくる</b>だけで、Document が型を取りに行くことはない。</p>'
     '<p class="foldnote">承認済みの規律 ── '
     '<b>集約は参照は持つが、自分では解決しない。解決した相手を引数で受け取る。</b></p>')),

 sec("04","操作を組み合わせるとき",
   "<b>併用が要るのは、両方の持ち物が混ざるときだけ</b>である。",
   combo,
   fold("索引だけが併用を要る理由を開く",
     '<p class="blob">索引は<b>ブロックの読み方（型の持ち物）</b>と'
     '<b>そこに何がどれだけあるか（文書の持ち物）</b>を組にして返す。'
     '<b>片方だけでは役に立たない</b> ── 読み方だけではどの文書でも同じになり、'
     '中身だけでは何のために読むブロックか分からない。</p>'
     '<p class="foldnote">束ねるのはユースケースの仕事である。'
     '<b>調整だけを担う</b>という位置づけに、そのまま収まる。</p>')),

 sec("05","呼ぶ順と、その前後",
   "<b>「検証前に描かせない」は、描くの事前条件として現れる。</b>状態の遷移ではない。",
   FIG2 + pre),

 sec("06","この一覧で決まらないこと",
   "3つ残る。<b>いずれも仕様か、移す計画で決める。</b>",
   tbl(["項目","何が決まっていないか"],[
     ("",["各欄と操作の名前","仮に置いたもの。仕様で確定する"]),
     ("",["「使ってよいか」の語","下書き／有効／非推奨 で足りるか"]),
     ("keyrow",["終端化するときの扱い",
       "<b>後続の版が要るか</b>、非推奨にするだけでよいか。"
       "工程の状態を落としたので、終端という言い方自体が要るかも含めて決める"]),
   ])),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
"""
out=("<title>Document は何を持ち、どう呼ばれるか</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/document-preview.html").write_text(out,encoding="utf-8")
print("書いた",len(out))
