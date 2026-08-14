"""層の形を決めるADRを組む。承認済みADRと同じ器・同じCSSを使う。"""
import json, pathlib
S = pathlib.Path(".")
CSS   = (S/"adr_css.txt").read_text(encoding="utf-8")
FIGCSS= (S/"figs/adr_assets.txt").read_text(encoding="utf-8")
FIG   = json.loads((S/"figs/adr_layers.json").read_text(encoding="utf-8"))

def sec(n, t, inner): return f'<section><h2><span class="num">{n}</span>{t}</h2>{inner}</section>'
def table(head, rows, cap=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f'<td class="name">{c}</td>' if i==0 else f"<td>{c}</td>"
        for i, c in enumerate(r)) + "</tr>" for r in rows)
    c = f'<p class="cap">{cap}</p>' if cap else ""
    return f'<div class="gapwrap"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>{c}'

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>規約を層から外し、実装を導くもう一方の入力として置く</h1>'
 '<p class="lede">仕様・規約・実装の上下関係を、一直線の積み重ねから、天辺だけを共有する2本の柱へ改める。</p></header>',

 sec("01", "決定", 
   '<div class="fig"><p class="one">規約は仕様の上でも下でもない。仕様と規約は同じ格で、'
   '<b>天辺の knowledge だけを共有し、実装とテストで合流する2本の柱</b>である。</p></div>'
   '<p class="cap">主文だけでは読み方が定まらない箇所を、同時に確定させる。</p>'
   + table(["確定させること", "決定", "定めないと"], [
     ("仕様を書くとき規約を読むか", "読まない。読むのは schema の記入指示と knowledge だけ",
      "仕様に「この製品ではこう綴る」が流れ込み、実装の綴りが仕様へ回り込む"),
     ("実装を導く入力", "仕様と規約の<b>両方</b>。どちらか一方では具体が決まらない",
      "仕様だけで実装が決まる形になり、仕様が実装の転記になる"),
     ("schema と仕様の間に規約を置くか", "置かない。その位置に相当するのは、もう一方の柱の CodingSchema",
      "対称性のために層が増え、「仕様の綴り方」という名で実装の綴りが入る口ができる"),
     ("際限", "上は knowledge（2本が共有する天辺）、下は実装とテスト（2本が合流する底）",
      "抽象の階段は上にも下にも無限に伸びるので、どこまで文書にするかが決まらない"),
   ])),

 sec("02", "理由",
   '<div class="two">'
   '<div class="space problem"><span class="space-label">実測</span><b>規約は仕様を書くときに読まれていない</b>'
   '<p>仕様の文書で規約を名指ししているのは3件だけで、いずれも規約そのものを扱うユースケース'
   '（<code>check-usecase-class-drift</code> 等が <code>architectureRef</code> を入力に取る）。'
   '仕様の執筆が規約に依存している箇所は1つも無い。</p></div>'
   '<div class="space solution"><span class="space-label">帰結</span><b>層に置くと嘘になる</b>'
   '<p>規約を仕様の上の層とすると「仕様は規約から導かれる」と読めるが、実際の依存はそうなっていない。'
   '規約が効くのは実装を導く辺だけであり、そこでのみ仕様と合流する。</p></div>'
   '</div>'
   + table(["読み取れる事実", "出所"], [
     ("規約は <code>CodingSchema/v7</code> に従う文書で、仕様と同じ格", "architecture / coding-standard / test-standard の3件を実測"),
     ("実装の置き場所・命名・単位・依存は、すべて規約の宣言から導出されている", "6つのドリフト検知が <code>architectureRef</code> を起点に動く"),
     ("仕様は「何ができるか」しか持たない", "受け入れ基準・シナリオ・エラー契約。綴りは持たない設計"),
   ])),

 sec("03", "変更前と変更後",
   '<p class="cap">宣言が何にぶら下がるか。</p>'
   '<div class="cmp">'
   f'<div class="pane"><span class="pane-label before">変更前</span>{FIG["before"]}'
   '<p class="fignote">規約が仕様の上に居る。仕様は規約から導かれる、と読める</p></div>'
   f'<div class="pane"><span class="pane-label after">変更後</span>{FIG["after"]}'
   '<p class="fignote">天辺だけを共有して2本に分かれ、実装とテストで合流する</p></div>'
   '</div>'),

 sec("04", "この決定が動かすもの",
   table(["対象", "どう変わるか"], [
     ("要件の一覧", "「5層・4辺」という整理を、「2本の柱・6辺」へ書き換える"),
     ("網の穴の位置", "穴は天辺の2辺（knowledge → それぞれの記入指示）に特定される。ここだけ検知が無い"),
     ("規約の改訂の影響範囲", "規約を変えても仕様は変わらない。変わるのは実装とテストの導出結果だけ"),
   ])),

 sec("05", "答えないこと",
   table(["論点", "いまは決めない理由"], [
     ("天辺の2辺にどう網を張るか", "別の決定として起こす。この決定は形だけを定める"),
     ("仕様と規約の分け目を裁く基準", "別の決定として起こす。形が決まらないと、どちらへ落とすかを論じられない"),
     ("実装の綴りをどこから導くか", "別の決定として起こす（<code>operationName</code> の扱いを含む）"),
   ])),

 '<section><h2><span class="num">06</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span>'
 '<span style="font-size:.9rem;color:var(--ink-soft)">この形に合意が取れてから、残る3つの決定を起こす。</span></div></section>',
])

html = (f"<title>規約を層から外し、実装を導くもう一方の入力として置く</title>"
        f"<style>{CSS}\n{FIGCSS}\n"
        ".cmp{display:flex;flex-direction:column;gap:1.6rem}"
        ".pane{display:flex;flex-direction:column;gap:.55rem}"
        ".pane-label{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase}"
        ".pane-label.before{color:var(--warn)}.pane-label.after{color:var(--solution)}"
        ".pane .wf-fig{display:block;max-width:100%;height:auto}"
        ".two{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--rule)}"
        "@media(max-width:40rem){.two{grid-template-columns:1fr}}"
        "</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-convention-is-not-a-layer.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")