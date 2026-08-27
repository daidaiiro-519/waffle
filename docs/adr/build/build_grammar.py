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
def ga(x1,y1,x2,y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/>'
a=''
a+=gb(14,40,180,48,"段2 の宣言","構造化データ","var(--infer)",True)
a+=ga(194,64,262,64)
a+=gb(262,40,190,48,"落とし方の規則","部品ごとに1つ","var(--assume)",True)
a+=ga(452,64,520,64)
a+=gb(520,40,180,48,"JSON Schema","機械が使う型")
a+=ga(610,88,610,132)
a+=gb(470,132,280,48,"段3 の骨格／逸脱の判定",None)
a+='<text x="14" y="122" font-size="10.5" fill="var(--ink-faint)">部品が決まれば、落とし方も決まる ──</text>'
a+='<text x="14" y="140" font-size="10.5" fill="var(--ink-faint)">宣言に書ける語ひとつひとつに、行き先が1つ対応する</text>'
FIG=(f'<figure class="fig"><div class="scroll"><svg viewBox="0 0 770 196" role="img" '
     f'style="min-width:44rem;width:100%;height:auto;display:block" {FF}>{DEFS}{a}</svg></div>'
     f'<figcaption><b>型を起こすとは、宣言から構造を組み立てること。</b>'
     f'描くこと（読み手向けの成果物へ落とすこと）とは別の操作である。</figcaption></figure>')

skel = tbl(["部品","何を述べるか","成果物のどこへ落ちるか"],[
 ("keyrow",["<b>識別子</b>","この文書を一意に指す",f"{C('documentId')}（文字・必須）"]),
 ("",["<b>型と版</b>","どの型の、どの版に従うか",f"{C('schemaRef')}（文字・必須）"]),
 ("",["<b>種別</b>","この文書がどの枝か",f"{C('specKind')} など（選択肢・必須）"]),
 ("",["<b>状態</b>","作成済／検証済／描画済／終端",f"{C('status')}（選択肢）"]),
 ("",["<b>役どころ</b>","実体か雛形か",f"{C('documentRole')}（選択肢・既定値あり）"]),
 ("",["<b>時刻</b>","作られた時／直された時",f"{C('createdAt')} / {C('updatedAt')}（時刻）"]),
 ("",["<b>ラベル</b>","文書に付ける印",f"{C('tags')}（文字の並び）"]),
])

gram = tbl(["部品","何を組めるか","成果物のどこへ落ちるか"],[
 ("keyrow",["<b>値</b>","文字・数・真偽・時刻",
   f"{C('type')} が {C('string')}／{C('number')}／{C('boolean')}、時刻は {C('format: date-time')}"]),
 ("keyrow",["<b>まとまり</b>","名前つきの欄の集まり",
   f"{C('type: object')} ＋ {C('properties')} ＋ {C('additionalProperties: false')}"]),
 ("keyrow",["<b>並び</b>","同じ形の繰り返し。<b>各要素は鍵と説明を持つ</b>",
   f"{C('type: array')} ＋ {C('items')}。要素の {C('properties')} に鍵と説明を置き、両方 {C('required')}"]),
 ("",["<b>入れ子</b>","まとまりの中のまとまり。<b>深さは有界</b>",
   f"深さのぶんだけ展開する。<b>{C('$ref')} の再帰は使わない</b>"]),
 ("keyrow",["<b>選び</b>","ある欄の値で、必須ブロックの集合が変わる",
   f"{C('allOf')} ＋ {C('if')}（{C('const')} で枝を指す）＋ {C('then')}（{C('required')}）。"
   f"既定の枝は {C('else')}"]),
 ("",["<b>名前で共有</b>","同じ形を名前で何度でも使う",f"{C('$defs')} ＋ {C('$ref')}"]),
])

lim = tbl(["修飾","何を述べるか","落ちる先"],[
 ("",["必須","書かれていなければならない",C("required")]),
 ("",["決め打ち","この値でなければならない",C("const")]),
 ("",["選択肢","この中のどれか",C("enum")]),
 ("",["最小の個数","少なくとも何件",C("minItems")]),
 ("",["閉じる","宣言していない欄を許さない",C("additionalProperties: false")]),
 ("keyrow",["<b>既定値</b>","書かなければこの値になる",C("default")]),
])

std = tbl(["標準の組み立て","なぜ段1 が持つか","落ちる先"],[
 ("keyrow",["<b>図</b>","<b>16の主張と、主張ごとの必須と禁止が、どの型でも同じでなければ困る</b>",
   f"{C('$defs')} に置き、主張ごとの必須・禁止を {C('allOf')} ＋ {C('if')}/{C('then')} で書く"]),
 ("keyrow",["<b>木</b>","<b>2つの型が同じものを別々の名前で自前に組んでいた</b>",
   "深さのぶんだけ展開したまとまりの入れ子"]),
])

mean = tbl(["語","何を述べるか","落ちる先"],[
 ("",["記入の指針","この欄に何を書くべきか",C("x-prompt-write")]),
 ("",["読み方","このブロックを何のために読むか",C("x-prompt-query")]),
 ("keyrow",["<b>読む必要の度合い</b>","本筋か、裏付けか、内訳か <b>← 足す</b>","新しい語"]),
])

draw = tbl(["語","何を述べるか","落ちる先"],[
 ("keyrow",["<b>描き方</b>","部品の並び・順序・見出しの深さ・隠すか",
   "ブロックの定義に付く。<b>いまの4語をまとめる</b>"]),
 ("keyrow",["<b>成果物の宛先</b>","描き先の形式・置き場所・道の変数・配る先・表紙へ出す欄",
   "schema の根に付く。<b>いまの2語をまとめる</b>"]),
])

drop = tbl(["落とすもの","理由"],[
 ("",[C("pattern"),"<b>一度も使われていない。</b>1件と数えたのは、偶然そういう名前の欄だった"]),
 ("",[C("title")+" / "+C("description"),
   "<b>成果物の側の語。</b>宣言では、鍵と説明・読み方が同じ役目を果たす"]),
 ("",[C("maxItems")+" ほか","使われていない"]),
])

body="".join([
 '<header><p class="eyebrow">段1 の部品と落とし方</p>'
 '<h1>宣言に書ける語と、その行き先</h1>'
 '<p class="lede"><b>部品が決まれば、落とし方も決まる。</b>'
 '宣言に書ける語ひとつひとつに、成果物のどこへ落ちるかが1つ対応する。'
 'これが「型を起こす」規則になる。</p></header>',

 sec("01","型を起こすとは何か",
   "<b>描くこと（読み手向けの成果物へ落とすこと）とは別の操作である。</b>"
   "JSON Schema は人が読むものではなく、機械が使う型だからである。",
   FIG +
   tbl(["操作","何を作るか","入力","誰の"],[
     ("keyrow",["<b>型を起こす</b>","<b>段2 の型そのもの（構造）</b>","段2 の宣言","<b>作り手</b>"]),
     ("keyrow",["<b>骨格を作る</b>","段3 の実体の器（値が空）","段2 の型＋識別子＋種別","<b>段2 のコマンド</b>"]),
     ("",["描く","読み手向けの成果物","Document ＋ 型","Document のコマンド"]),
   ])),

 sec("02","表紙",
   "Document はエンティティである。<b>どの型でも同じものを持つ。</b>",
   skel),

 sec("03","構造の文法 ── 6つ",
   "中身を組み立てる語。<b>どれも鍵と説明を持つ</b>という規律が掛かる。",
   gram,
   fold("入れ子を展開する理由を開く",
     '<p class="blob"><code>$ref</code> の再帰を使うと、深さに限りが無くなる。'
     '<b>「再帰は常に有界である」は既にある不変条件</b>なので、'
     '深さのぶんだけ展開して、構造そのもので満たす。</p>'
     '<p class="foldnote">実測では、いちばん深い型で15段。'
     '概念の木と図の入れ子がそれにあたる。</p>')),

 sec("04","値に掛かる修飾",
   "独立した部品ではなく、文法に掛かるもの。<b>既定値を足した。</b>",
   lim),

 sec("05","標準の組み立て",
   "文法だけでも組めるが、<b>意味がどの型でも同じでなければ困る</b>ので、段1 が名前付きで持つ。",
   std),

 sec("06","意味の語と、描き方の語",
   "構造の各所に添えるもの。<b>読む必要の度合いを足し、描き方は6語から2語へまとめる。</b>",
   '<h3 class="sub-h">意味の語</h3>' + mean +
   '<h3 class="sub-h">描き方の語</h3>' + draw),

 sec("07","落とすもの",
   "説明が付かないまま残っていた語を、確かめたうえで落とす。",
   drop,
   fold("<code>pattern</code> を1件と数えていた件",
     '<p class="blob">構造の語を数えたとき <code>pattern</code> が1回出た。'
     '中身を見たら<b>「この概念の実現方針」という欄の名前</b>だった。'
     '正規表現の <code>pattern</code> は<b>一度も使われていない</b>。</p>'
     '<p class="foldnote">数えた語が、言語なのか欄の名前なのかを見分けていなかった。</p>')),

 sec("08","この一覧で決まらないこと",
   "3つ残る。<b>いずれも段2 の側を決めるときに扱う。</b>",
   tbl(["項目","何が決まっていないか"],[
     ("",["各語の名前","「描き方」「成果物の宛先」は仮。仕様で確定する"]),
     ("",["読む必要の度合いの段階","本筋／裏付け／内訳 で足りるか"]),
     ("keyrow",["段2 が持つべきもの","この部品を使って何を組むか。<b>次に決める</b>"]),
   ])),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
"""
out=("<title>宣言に書ける語と、その行き先</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/tier1-grammar.html").write_text(out,encoding="utf-8")
print("書いた",len(out))
