import sys, pathlib
S = "/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0, S)
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra
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

# --- FIG1: 二度書きになるか、起こせるか ---
a = ''
a += gt(14, 20, "変更前 ── 仕様は人が読むもの。型は別に手で書く", "var(--against)", 11)
a += gb(14, 32, 170, 44, "仕様", "人が読む文", "var(--against)")
a += ga(184, 54, 250, 54)
a += gb(250, 32, 170, 44, "人が読む", None, "var(--against)")
a += ga(420, 54, 486, 54)
a += gb(486, 32, 170, 44, "型を手で書く", "同じことを二度", "var(--against)", True)
a += gt(14, 100, "変更後 ── 仕様の一節が、そのまま宣言の一項目へ起きる", "var(--infer)", 11)
a += gb(14, 112, 170, 48, "仕様の一節", "鍵・説明・形・修飾", "var(--infer)", True)
a += ga(184, 136, 250, 136)
a += gb(250, 112, 170, 48, "起こす", "機械が読む", "var(--infer)")
a += ga(420, 136, 486, 136)
a += gb(486, 112, 170, 48, "段2 の宣言の一項目", None, "var(--infer)", True)
a += gt(14, 182, "書くのは一度だけ。仕様と型が食い違いようがない", "var(--infer)")
FIG1 = gsvg("0 0 680 196", a,
 "<b>仕様を「後から起こせる形」で書くと、書くのは一度で済む。</b>"
 "いまは仕様と型が別々に書かれるので、<b>食い違っても誰も気づかない</b>。")

# --- FIG2: いつ起こすか ---
b = ''
b += gb(14, 40, 160, 46, "仕様", "いま書く", "var(--infer)", True)
b += ga(174, 63, 244, 63)
b += gb(244, 40, 160, 46, "段1 の実装", "人が書く", "var(--assume)")
b += ga(404, 63, 474, 63)
b += gb(474, 40, 170, 46, "起こす機能", "段1 が持つ", "var(--assume)")
b += ga(559, 86, 559, 118)
b += gb(474, 118, 170, 46, "仕様を起こす", "同じ仕様を入力に", "var(--infer)", True)
b += ('<line x1="474" y1="141" x2="94" y2="141" stroke="var(--ink-faint)" stroke-width="1.4"/>')
b += ga(94, 141, 94, 90)
b += gt(232, 134, "書いたものが、あとで自分の入力になる", "var(--infer)")
FIG2 = gsvg("0 0 680 180", b,
 "<b>仕様を書くための機能は、まだ無い。</b>だから最初の仕様は人が書く ── "
 "ただし<b>後で機能ができたとき、その入力になる形</b>で書いておく。")

axis = ('<div class="scroll"><table>'
 '<thead><tr><th>案</th>'
 '<th class="keycol">後から機械が起こせる<br><span class="sub">決め手</span></th>'
 '<th>いま書き始められる</th>'
 '<th>今ある仕組みに縛られない</th>'
 '<th>読んで分かる</th></tr></thead><tbody>'
 f'<tr class="pickrow"><td class="cond">起こせる形で書く<br><span class="sub">採る</span></td>'
 f'<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ok}<br><span class="sub">表と例で書く</span></td></tr>'
 f'<tr><td class="cond">いまの spec の形式で書く</td>'
 f'<td>{ok}</td><td>{ng}<br><span class="sub">その形式ごと作り直す</span></td>'
 f'<td>{ng}</td><td>{ok}</td></tr>'
 f'<tr><td class="cond">ふつうの文章で書く</td>'
 f'<td>{ng}</td><td>{ok}</td><td>{ok}</td><td>{ok}</td></tr>'
 '</tbody></table></div>')

raise_map = tbl(["仕様の側に書く欄", "起きたときの姿", "誰が使うか"], [
 ("keyrow", ["<b>鍵</b>", "宣言の項目の名前", "型を起こす"]),
 ("keyrow", ["<b>説明</b>", "その項目を<b>何のために読むか</b>", "読み方の指針を返す"]),
 ("", ["<b>書ける形</b>", "文法6つのどれか（値／まとまり／並び／入れ子／選び／名前で共有）", "型を起こす"]),
 ("", ["<b>修飾</b>", "必須・決め打ち・選択肢・最小の個数・閉じる・既定値", "型を起こす"]),
 ("", ["<b>例</b>", "起こさない。<b>人が読むためだけに置く</b>", "—"]),
])

toc = tbl(["節", "何を書くか", "出どころ"], [
 ("keyrow", ["<b>表紙</b>", "どの文書にも共通する外側 ── 識別子・型と版・種別・content",
   "<b>Document は導けないものだけを持つ</b>（承認済み）"]),
 ("keyrow", ["<b>構造の文法6つ</b>", "値／まとまり／並び／入れ子（深さ有界）／選び／名前で共有",
   "<b>段1 が部品を提供する</b>（承認済み）"]),
 ("", ["<b>修飾6つ</b>", "必須／決め打ち／選択肢／最小の個数／閉じる／既定値", "同上"]),
 ("", ["<b>標準の組み立て</b>", "図・木 ── 文法だけでも組めるが、<b>意味がどの型でも同じでなければ困る</b>もの", "同上"]),
 ("keyrow", ["<b>鍵と説明の規律</b>", "どの部品も鍵と説明を持つ",
   "<b>部品に鍵と説明を持たせる</b>（承認済み）"]),
 ("keyrow", ["<b>型を起こす組み立ての手順</b>", "宣言から型を組み立てる順序と規則。<b>いちばん厚い節</b>",
   "<b>Schema は3つの操作を持つ</b>（承認済み。中身は未着手）"]),
 ("", ["<b>古い形の宣言を読む</b>", "範囲外の37本を壊さないための条件", "<b>移す計画</b>（未承認）"]),
])

why = (step("premise", "前提",
   "<b>仕様を書くための機能は、これから作る。</b>いまは無い")
 + joint("だから")
 + step("conclude", "言えること",
   "<b>最初の仕様は、人が書くしかない。</b>その機能の入力になる形で書いておかないと、"
   "機能ができたときに<b>もう一度書き直すことになる</b>")
 + joint("今ある形式はどうか")
 + step("premise", "前提",
   "いまの spec の形式（<code>DomainSpecSchema</code>）は、<b>この移行で作り直す対象そのもの</b>である")
 + joint("だから")
 + step("conclude", "言えること",
   "<b>それで書くと、書いた先が動く。</b>作り直す対象を、作り直すための仕様の器に使うことになる")
 + joint("ふつうの文章はどうか")
 + step("counter", "反する例",
   "ふつうの文章なら、いますぐ書けて何にも縛られない。<b>ただし機械が起こせない</b> ── "
   "鍵と説明と形が、文のどこにあるか決まらないため")
 + joint("合わせると")
 + step("conclude", "結論",
   "<b>仕様は、後から起こせる形で書く。</b>今の形式は使わない。"
   "各節を〈鍵・説明・書ける形・修飾・例〉の組として書き、"
   "<b>例だけは起こさない</b>"))

no_answer = tbl(["項目", "何が決まっていないか", "いつ決まるか"], [
 ("keyrow", ["<b>起こす機能をどこに置くか</b>", "段1 の実装のどこが読むか", "<b>実装のとき</b>"]),
 ("", ["仕様の置き場所", "<code>docs/</code> か、別の場所か", "書き始めるとき"]),
 ("", ["各語の名前", "部品と修飾の呼び名は、まだ仮", "<b>この仕様を書く中で決まる</b>"]),
 ("keyrow", ["<b>読む必要の度合い</b>", "<b>初稿では欄のひとつに置いたが、落とした</b> ── 承認済みの決定に無く、その決め手（宣言させるものを増やさない）に反していた", "<b>決着済み</b>"]),
])

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>仕様を、後から型として起こせる形で書く</h1>'
 '<p class="lede">仕様を書くための機能は、これから作る。'
 'いまは無いので<b>最初の仕様は人が書くしかない</b> ── '
 'ただし<b>後でその機能の入力になる形</b>で書いておかないと、二度書きになる。</p></header>',

 sec("01", "決定", None,
   '<div class="decision"><p class="main">Waffle の段1 の仕様は、'
   '<b>後から機械が型として起こせる形で書く</b>。'
   'いまの spec の形式（<code>DomainSpecSchema</code>）は使わない。'
   '各節を<b>〈鍵・説明・書ける形・修飾・例〉</b>の組として書き、'
   '<b>例だけは起こさない</b>。</p>'
   '<div class="key"><span class="lbl">決め手</span><span class="txt">'
   '<b>いまの形式は、この移行で作り直す対象そのものである。</b>'
   'それを仕様の器に使うと、書いた先が動く。'
   'かといってふつうの文章では、<b>鍵と説明と形が文のどこにあるか決まらない</b>ので起こせない。'
   '</span></div></div>'),

 sec("02", "変更前と変更後",
   "変わるのは<b>仕様が誰に読まれるか</b>である。",
   FIG1),

 sec("03", "仕様の一節は、何に起きるか",
   "<b>欄ごとに、行き先が決まっている。</b>行き先の無い欄は<b>例だけ</b>である。",
   raise_map,
   fold("なぜ例だけ起こさないのか",
     '<p class="blob">例は<b>人が仕様を読むためのもの</b>で、型の形を決めない。'
     '起こすと、<b>ひとつの書き方が正であるかのように型へ焼き込まれる</b>。</p>'
     '<p class="foldnote">同じ理由で、例は<b>複数置いてよい</b>。'
     'ひとつしか置けないなら、それは例ではなく決め打ちである。</p>')),

 sec("04", "段1 の仕様が持つ節",
   "<b>7つ。うち6つは承認済みの決定から出る。</b>新しく決めるのは中身だけである。",
   toc,
   fold("いちばん厚い節はどれか",
     '<p class="blob"><b>型を起こす組み立ての手順</b>である。'
     '承認済みの決定は「その操作が要る」と定めただけで、'
     '<b>どういう順序でどう組むかは、まだ何も決まっていない</b>。</p>'
     '<p class="foldnote">ほかの6節は、承認済みの決定を<b>書き下ろす</b>作業に近い。'
     'ここだけが<b>これから決める</b>作業である。</p>')),

 sec("05", "理由",
   "書くための機能が無いので人が書く。<b>ただし、あとで自分の入力になる形にしておく。</b>",
   FIG2 + why),

 sec("06", "判断を分けた軸",
   "採る案は4つの条件をすべて満たす。<b>落とすものが無い</b>。",
   axis,
   fold("落とすものが無いのは、なぜ怪しくないか",
     '<p class="blob">ふつうは<b>どれかを落とす</b>。ここで落ちないのは、'
     '<b>3案が同じ土俵にいないため</b>である ── '
     'いまの形式は「作り直す対象を器に使う」ので条件以前に成り立たず、'
     'ふつうの文章は「起こせない」という決め手をそのまま外している。</p>'
     '<p class="foldnote"><b>比較が効いていないという合図でもある。</b>'
     'もし別の書き方が出てきたら、そのときに軸を引き直す。</p>')),

 sec("07", "答えないこと",
   "4つ残る。<b>3つはこの仕様を書く中で決まる。</b>",
   no_answer),

 sec("08", "承認", None,
   '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span>'
   '<span class="m">2026-08-16</span></div>'),

 sec("09", "関連", None,
   fold("縛る対象と、前後の決定を開く（5件）",
     tbl(["種類", "対象"], [
       ("keyrow", ["縛る対象", "段1 の仕様を、どの形で書くか"]),
       ("keyrow", ["先立つ決定", "<b>段1 が部品を提供し、段2 が8つを宣言する</b>（承認済み）── 節の中身がここから出る"]),
       ("", ["先立つ決定", "Schema は3つの操作を持つ（承認済み）── <b>型を起こす</b>の中身が、この仕様の最も厚い節になる"]),
       ("", ["先立つ決定", "部品に鍵と説明を持たせ、索引を取り出すときに組み立てる（承認済み）"]),
       ("keyrow", ["この決定を使う予定", "<b>段1 の仕様そのもの</b>（次に書く）／移す計画の第1段"]),
     ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
"""
out = ("<title>仕様を、後から型として起こせる形で書く</title>"
       f'<style>{CSS}\n{extra2}</style><div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-spec-form.html").write_text(out, encoding="utf-8")
print("書いた", len(out))
