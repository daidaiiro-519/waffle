import sys, pathlib
S = "/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0, S)
from _common import CSS, sec, fold, tbl, step, joint, extra
C = lambda s: f"<code>{s}</code>"
FF = 'font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
DEFS = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs>')

def gb(x, y, w, h, t, s=None, a="var(--rule)", strong=False):
    o = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" '
         f'stroke="{a}" stroke-width="{2 if strong else 1}"/>')
    o += (f'<text x="{x+w/2}" y="{y+(h/2+5 if not s else h/2-3)}" text-anchor="middle" '
          f'font-size="12.5" font-weight="600" fill="var(--ink)">{t}</text>')
    if s:
        o += (f'<text x="{x+w/2}" y="{y+h/2+15}" text-anchor="middle" font-size="10.5" '
              f'fill="var(--ink-faint)">{s}</text>')
    return o

def ga(x1, y1, x2, y2):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink-faint)" '
            f'stroke-width="1.4" marker-end="url(#ah)"/>')

def gt(x, y, t, c="var(--ink-faint)", sz=10.5, anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{sz}" fill="{c}">{t}</text>'

def gsvg(vb, inner, cap, minw="44rem"):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:{minw};width:100%;height:auto;display:block" {FF}>{DEFS}{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

def ex(s):
    return f'<pre class="ex">{s}</pre>'

# --- 図: 旧い型は起こさない ---
g = ''
g += gt(14, 20, "新しい型 ── 宣言から起こす", "var(--infer)", 11)
g += gb(14, 32, 160, 44, "新しい宣言", None, "var(--infer)", True)
g += ga(174, 54, 244, 54)
g += gb(244, 32, 150, 44, "起こす", None, "var(--infer)")
g += ga(394, 54, 464, 54)
g += gb(464, 32, 150, 44, "型", None, "var(--infer)")
g += gt(14, 104, "旧い型 ── 宣言が無い。既に型として在るので、起こす相手がいない", "var(--assume)", 11)
g += gb(14, 116, 160, 44, "旧い型", "そのまま在る", "var(--assume)", True)
g += ga(174, 138, 244, 138)
g += gb(244, 116, 150, 44, "読む", None, "var(--assume)")
g += ga(394, 138, 464, 138)
g += gb(464, 116, 150, 44, "判定・描画", None, "var(--assume)")
g += gt(14, 190, "だから段1 が背負うのは「旧い型を読める」ことだけで、"
                "「旧い宣言を起こせる」ことではない", "var(--ink-soft)", 11)
FIG = gsvg("0 0 660 206", g,
 "<b>旧い型は、既に型として存在する。</b>起こす相手が無いので、"
 "段1 に要るのは<b>旧い型を読んで判定・描画できること</b>だけである。")

BONE = tbl(["鍵", "説明", "形", "修飾"], [
 ("keyrow", [C("documentId"), "この文書を一意に指す", "値（文字列）", "必須"]),
 ("keyrow", [C("schemaRef"), "<b>どの型のどの版に照らして判定するか</b>", "値（文字列）", "必須"]),
 ("", [C("kind"), "この文書がどの枝か", "値（文字列）", "必須・選択肢"]),
 ("", [C("role"), "実体か雛形か", "値（文字列）", "選択肢（<code>entity</code>／<code>template</code>）・既定値 <code>entity</code>"]),
 ("keyrow", [C("usable"), "<b>これに頼ってよいか。人が決める</b>", "値（文字列）",
   "必須・選択肢（<code>draft</code>／<code>active</code>）"]),
 ("", [C("createdAt") + "・" + C("updatedAt"), "作られた時・直された時", "値（文字列）", "必須"]),
 ("", [C("tags"), "文書に付ける印", "並び（値）", "—"]),
 ("keyrow", [C("content"), "<b>文書の中身。型を知らない木</b>", "まとまり", "必須・閉じる"]),
])

GRAMMAR = tbl(["文法", "鍵", "何を表すか", "起こしたときの姿"], [
 ("keyrow", ["<b>値</b>", C("value"), "ひとつの値", C("type") + " が文字列・整数・真偽のいずれか"]),
 ("keyrow", ["<b>まとまり</b>", C("group"), "名前の付いた欄の集まり",
   C("type: object") + " と " + C("properties")]),
 ("", ["<b>並び</b>", C("list"), "同じ形のものが並ぶ", C("type: array") + " と " + C("items")]),
 ("keyrow", ["<b>入れ子</b>", C("nest"), "<b>自分と同じ形の子を持てる。深さに上限を置く</b>",
   "自分自身への " + C("$ref") + "（上限まで展開する）"]),
 ("", ["<b>選び</b>", C("choice"), "いくつかの形のどれかひとつ", C("oneOf")]),
 ("", ["<b>名前で共有</b>", C("shared"), "同じ形を名前で括り、何度でも指す",
   C("$defs") + " へ置き、" + C("$ref") + " で指す"]),
])

MODIFY = tbl(["修飾", "鍵", "何を表すか", "どの文法に付くか", "起こしたときの姿"], [
 ("keyrow", ["<b>必須</b>", C("required"), "無いと成り立たない", "まとまりの欄", C("required") + " へ名前を足す"]),
 ("", ["<b>決め打ち</b>", C("fixed"), "その値しか取れない", "値", C("const")]),
 ("keyrow", ["<b>選択肢</b>", C("options"), "この中のどれか", "値", C("enum")]),
 ("", ["<b>最小の個数</b>", C("minCount"), "少なくともいくつ要るか", "並び", C("minItems")]),
 ("", ["<b>閉じる</b>", C("closed"), "<b>知らない欄を置けない</b>", "まとまり", C("additionalProperties: false")]),
 ("", ["<b>既定値</b>", C("default"), "書かなければこの値", "値", C("default")]),
])

STD = tbl(["組み立て", "何を持つか", "なぜ文法だけに任せないか"], [
 ("keyrow", ["<b>図</b>",
   "<b>主張</b>（16のどれか）／<b>読み方</b>／置くもの／つなぐもの／読む枠。"
   "<b>どの欄が必須・禁止かは、主張が決める</b>",
   "<b>意味がどの型でも同じでなければ、図を描く側が型ごとに分岐する</b>"]),
 ("keyrow", ["<b>木</b>",
   "節ごとに<b>名前と要約</b>を持ち、自分と同じ形の子を持てる。<b>深さに上限を置く</b>",
   "<b>実測で、2つの型が同じ木を別々の名前で組んでいた</b>。"
   "揃えないと、読む側が型ごとに書き分けることになる"]),
])

KEYGLOSS = tbl(["どこに", "鍵にあたるもの", "説明にあたるもの"], [
 ("keyrow", ["まとまりの欄", "欄の名前", "その欄を何のために読むか"]),
 ("keyrow", ["<b>並びの要素</b>", "<b>要素の鍵</b>", "<b>要素の説明</b>"]),
 ("", ["木の節", "節の名前", "節の要約"]),
 ("", ["図", C("asserts") + "（主張）", C("reading") + "（読み方）"]),
])

STEPS = tbl(["順", "すること", "なぜこの順か"], [
 ("keyrow", ["<b>1</b>", "<b>表紙を置く</b> ── 節01 の欄をそのまま置く",
   "どの型にも同じ外側が要る。中身より先に器が要る"]),
 ("keyrow", ["<b>2</b>", "<b>種別の枝を作る</b> ── 種別の鍵は<b>1つ</b>",
   "<b>content の形が枝ごとに変わる</b>ので、content を作る前に枝が決まっている必要がある"]),
 ("", ["<b>3</b>", "<b>共有する組み立てを先に置く</b> ── " + C("$defs") + " を作る",
   "<b>指す先が無いと " + C("$ref") + " が書けない</b>"]),
 ("keyrow", ["<b>4</b>", "<b>ブロックの定義を、宣言の順に content の下へ置く</b>",
   "<b>宣言の順がそのまま読む順になる</b>。並べ替える根拠が無い"]),
 ("", ["<b>5</b>", "各ブロックの中身を、文法に従って組む",
   "ブロックの器ができてからでないと、中身を入れられない"]),
 ("", ["<b>6</b>", "修飾を当てる",
   "<b>修飾は形に付くもの</b>なので、形が決まってからしか当たらない"]),
 ("keyrow", ["<b>7</b>", "<b>説明を、鍵の隣に置く</b>",
   "鍵が全部出そろってからでないと、置き漏らしが分からない"]),
 ("", ["<b>8</b>", "枝ごとの必須ブロックの一覧を当てる",
   "ブロックが全部在ってからでないと、一覧が指す先を確かめられない"]),
 ("", ["<b>9</b>", "描き方と、成果物の宛先を型へ置く。<b>実体へ写さない</b>",
   "型が組み上がってからでないと、どこへ置くかが決まらない"]),
])

OLD = tbl(["問い", "答え"], [
 ("keyrow", ["旧い宣言を起こせる必要があるか", "<b>無い。</b>旧い型は既に型として在り、起こす相手がいない"]),
 ("keyrow", ["では段1 は何を背負うか", "<b>旧い型を読んで、判定と描画ができること</b>"]),
 ("", ["旧い型に新しい部品を足すか", "<b>足さない。</b>足すと、旧い型が新旧の混ざった形になる"]),
 ("", ["いつ外せるか", "その型を指す文書が全部移り、旧い版を落としたとき"]),
])

DECIDED = tbl(["決めたこと", "中身", "覆したくなったら"], [
 ("keyrow", ["<b>鍵は英語、説明は日本語</b>",
   "鍵は機械が使う名前なので英語の識別子にする。説明・仕様の本文はユビキタス言語（日本語）で書く",
   "<b>鍵を日本語にすると、既存の全文書の鍵と混ざる</b>。移すときに二重の書き換えになる"]),
 ("keyrow", ["<b>「使ってよいか」は2つ</b>",
   "<code>draft</code>／<code>active</code> の2つ。<b>非推奨を持たない</b>。退役は文書を消すことで表す",
   "<b>非推奨は誰も守っていなかった</b> ── 判定も描画も見ておらず、参照されても何も起きない。実物は3本あり、<b>参照は0件</b>だった。"
   "「消せる＝誰も頼っていない」は導けるので、札は要らない"]),
 ("", ["<b>入れ子の上限は仕様で決めない</b>", "型ごとに宣言する。段1 は「上限を持つこと」だけを定める",
   "上限を段1 で固定すると、型ごとの事情を吸収できない"]),
])

OPEN = tbl(["項目", "何が決まっていないか", "どこで決めるか"], [
 ("keyrow", ["<b>図の16の主張ごとの必須・禁止</b>", "主張ごとの対応表そのもの",
   "<b>図の仕様</b> ── <b>第1段の中</b>。図は段1 が持つ部品なので、段1 の実装より前に要る"]),
 ("keyrow", ["<b>値の型の種類</b>",
   "文字列・整数・真偽で足りるか。<b>実測では他に無かった</b>が、確かめていない",
   "<b>段2 の仕様</b> ── 8つの型を組み直すときに、足りなければ出る"]),
 ("", ["起こす機能の置き場所", "段1 の実装のどこが、この仕様を読むか", "実装のとき"]),
 ("", ["説明の書き方の下限", "「何のために読むか」をどこまで書けば足りるか",
   "<b>使ってみて決める</b> ── 索引を引いて足りるかを見る"]),
])

body = "".join([
 '<header><p class="eyebrow">仕様 ── 段1</p>'
 '<h1>すべての型に共通する契約</h1>'
 '<p class="lede">段1 は<b>部品を提供するだけ</b>で、操作を持たない。'
 '段2 がこの部品を組み合わせて型を宣言する。'
 '<b>段2 が自前で部品を組んでいたら、それは段1 の欠落である。</b></p></header>',

 sec("01", "表紙",
   "<b>どの文書にも共通する外側。</b>導けるものは持たない。",
   BONE,
   fold("工程の状態を持たない理由",
     '<p class="blob">適合したか・描いたか・中身に何があるかは、'
     '<b>文書と型と成果物から導ける</b>。導けるものを保存すると古くなる。</p>'
     '<p class="foldnote">導けないのは <code>usable</code> だけである ── '
     '<b>人が下す判断で、文書のどこにも書かれていない</b>。</p>')),

 sec("02", "構造の文法",
   "<b>6つ。これで組めないものは、段1 の欠落である。</b>",
   GRAMMAR,
   ),

 sec("03", "修飾",
   "<b>6つ。形に付いて、取れる値を狭める。</b>",
   MODIFY,
   fold("正規表現を持たない理由",
     '<p class="blob">実測では、正規表現による制限が<b>一度も使われていなかった</b>。'
     '「<code>pattern</code>」として現れていたものは、<b>欄の名前</b>だった。</p>'
     '<p class="foldnote"><b>実物にある無駄は賄わない。</b>'
     '必要になったら、そのとき部品として足す。</p>')),

 sec("04", "標準の組み立て",
   "<b>2つ。文法だけでも組めるが、意味がどの型でも同じでなければ困るもの。</b>",
   STD),

 sec("05", "鍵と説明の規律",
   "<b>どの部品も鍵と説明を持つ。例外を作らない。</b>",
   KEYGLOSS,
   fold("例外を作ると何が起きるか",
     '<p class="blob">実測では、組の要素<b>281件のうち152件（54%）で説明が取れなかった</b>。'
     '取れなかったものも <code>term</code>/<code>definition</code>、'
     '<code>conceptId</code>/<code>note</code> のように<b>鍵と説明の対</b>で、'
     '<b>形は揃っていて名前だけが違っていた</b>。</p>'
     '<p class="foldnote">つまり不足していたのは規律であって、構造ではない。</p>')),

 sec("06", "型を起こす組み立ての手順",
   "<b>9段。順序は入れ替えられない</b> ── 後の段が前の段の結果を使う。",
   STEPS,
   fold("この節だけが、承認済みの決定から出ていない",
     '<p class="blob">ほかの7節は承認済みの決定を書き下ろしたものだが、'
     '<b>この順序はここで新しく決めている</b>。'
     '承認済みの決定は「型を起こす操作が要る」と定めただけである。</p>'
     '<p class="foldnote">順序の根拠は<b>依存だけ</b>である ── '
     '「読みやすいから」ではなく、<b>前の結果が無いと次が書けない</b>。'
     '依存で説明できない並べ替えがあれば、それは根拠が無い。</p>')),

 sec("07", "古い形の宣言を読む",
   "<b>起こす必要は無い。読めればよい。</b>",
   FIG + OLD,
   fold("これが移す計画を軽くする",
     '<p class="blob">移す計画は「<b>段1 は新旧どちらの宣言も読めなければならない</b>」を'
     '第1段の条件に置いた。<b>そこまでは要らない</b> ── '
     '旧い型は既に型として在るので、<b>起こす相手がいない</b>。</p>'
     '<p class="foldnote">段1 が背負うのは<b>旧い型を読んで判定と描画ができること</b>だけになる。'
     '移す計画の危ないところを、1件ぶん軽くできる。</p>')),

 sec("08", "この仕様で決めたこと",
   "<b>3つ。いずれも承認済みの決定からは出ない</b>ので、ここで決めた。",
   DECIDED),

 sec("09", "まだ決めていないこと",
   "4つ残る。<b>行き先はすべて決まっている</b> ── ただし図の仕様だけ、いつ書くかが空いている。",
   OPEN),

 sec("10", "承認", None,
   '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-17 承認</span>'
   '<span class="m">2026-08-16 初稿</span></div>'),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
pre.ex{margin:0;padding:.9rem 1rem;font-family:var(--mono);font-size:.8rem;line-height:1.75;
       background:var(--surface-2);border-top:1px solid var(--rule-soft);overflow-x:auto;color:var(--ink-soft)}
"""
out = ("<title>段1 ── すべての型に共通する契約</title>"
       f'<style>{CSS}\n{extra2}</style><div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/tier1-spec.html").write_text(out, encoding="utf-8")
print("書いた", len(out))
