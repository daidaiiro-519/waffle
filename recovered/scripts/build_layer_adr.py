import json, pathlib
S = pathlib.Path("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
CSS = S.joinpath("newfmt.css").read_text(encoding="utf-8")
FIGCSS = S.joinpath("layer_figcss.txt").read_text(encoding="utf-8")
FIG = json.loads(S.joinpath("layer_figs.json").read_text(encoding="utf-8"))

def step(kind, lbl, txt, src=None, weak=None):
    s = f'<div class="step {kind}"><span class="lbl">{lbl}</span><span class="txt">{txt}</span>'
    if src:  s += f'<span class="src">出所: {src}</span>'
    if weak: s += f'<span class="weak"><b>崩れるとき</b> ── {weak}</span>'
    return s + "</div>"
def joint(t): return f'<div class="joint">{t}</div>'
def backing(t): return f'<div class="backing">拠り所 ── {t}</div>'
def table(head, rows):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f'<td class="name">{c}</td>' if i == 0 else f"<td>{c}</td>"
        for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="scroll"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'
def sec(n, t, inner): return f'<section><h2><span class="num">{n}</span>{t}</h2>{inner}</section>'

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>規約は層ではなく、実装を導くもう一つの入力とする</h1>'
 '<p class="lede">仕様・規約・実装の関係を、一直線の積み重ねから、knowledge だけを共通の出発点とする2つの経路へ改める。</p></header>',

 sec("01", "決定",
   '<div class="decision"><p class="main">規約は仕様の層ではない。仕様と規約は同じ格で、'
   'knowledge だけを共通の出発点とし、実装とテストで合流する2つの経路である。</p>'
   '<div class="key"><span class="lbl">決め手</span>'
   '<span class="txt">仕様の執筆は規約を読んでいない。上に積むと'
   '<b>「仕様は規約から導かれる」と読め、実際の依存と食い違う</b>。</span></div></div>'),

 sec("02", "変更前と変更後",
   '<p class="fignote">何が何から導かれるか。</p>'
   '<div class="cmp stack">'
   f'<div class="pane"><span class="pane-label b">変更前 ── 一直線に積む</span><div class="box">{FIG["before"]}</div>'
   '<p class="fignote">規約が仕様の上にあり、仕様は規約から導かれる、と読める</p></div>'
   f'<div class="pane"><span class="pane-label a">変更後 ── 2つの経路が合流する</span><div class="box">{FIG["after"]}</div>'
   '<p class="fignote">knowledge だけが共通で、そこから2つに分かれ、実装とテストで合流する</p></div>'
   '</div>'),

 sec("03", "理由",
   '<div class="chain">'
   + step("evidence", "測った",
       "仕様の文書のうち、規約を名指ししているのは3件だけ。いずれも規約そのものを入力に取るユースケースだった",
       "仕様の走査と、各文書の入力欄の確認",
       "規約を入力に取らない仕様が、規約を参照し始めたとき")
   + joint("だから")
   + step("conclude", "言えること", "仕様の執筆は規約に依存していない")
   + backing("knowledge「仕様の語彙にパターン名を入れない ── 使えるのは規約から下だけ」")
   + joint("一方で")
   + step("evidence", "測った",
       "実装とテストの置き場所・命名・単位・依存は、すべて規約の宣言から導出されている",
       "ドリフト検知が規約の識別子を起点に動く",
       "導出せず、対応を保存する検知が増えたとき")
   + joint("さらに")
   + step("evidence", "測った",
       "規約は仕様と同じ schema 群に属する文書であり、仕様の下位でも上位でもない",
       "アーキテクチャ・コーディング・テストの3規約の宣言",
       "規約が仕様の schema へ統合されたとき")
   + joint("ここで置いた前提")
   + step("premise", "確かめていない",
       "今後も、仕様の執筆に規約が要る場面は現れない",
       None,
       "製品ごとに仕様の書き方を変える必要が出たとき")
   + joint("合わせると")
   + step("conclude", "結論",
       "規約が効くのは実装とテストを導くところだけ。上下に積むと依存の向きを偽ることになる")
   + joint("ただし")
   + step("counter", "反証",
       "3件は現に規約を名指ししている。「規約を扱うユースケースだから例外」は私が付けた解釈であって、観測ではない")
   + '</div>'),

 sec("04", "判断を分けた軸",
   table(["軸", "2つの経路にする（採る）", "仕様の上に積む", "仕様と実装の間に挟む"], [
     ("依存の向きを正しく表すか", "表す", "偽る（仕様が規約から導かれると読める）", "偽る（同上）"),
     ("図の読みやすさ", '<span class="win">分岐と合流の理解が要る</span>',
      '<span class="win">1本の線で最も単純</span>', "1本の線で単純"),
     ("読み順の自然さ", "2本を並行に読む", "上から下へ読める",
      '<span class="win">仕様→規約→実装と読め、規約が実装を縛ることが直感的</span>'),
     ("層を増やさずに済むか", "増やさない", "増やす", "増やす"),
     ("規約の改訂の影響範囲", "実装とテストの導出結果だけ", "仕様まで波及すると読める", "同左"),
   ])
   + '<div class="col"><p>印は、<b>採らなかった案が優る軸</b>。一直線に積む案は図が最も単純で、間に挟む案は読み順が直感的。</p>'
   '<p><b>それでも2つの経路を採る理由。</b>読みやすさで負ける代わりに、依存の向きを偽らない。'
   'この製品で繰り返した失敗は「図が複雑で読めなかった」ことではなく「宣言と実際の依存が食い違ったまま誰も気づかなかった」ことであり、'
   'そこに効く軸を優先した。</p></div>'),

 sec("05", "付随して決めたこと",
   table(["論点", "決定", "根拠"], [
     ("schema と仕様の間に規約を置くか", "置かない。その位置に相当するのは、もう一方の経路の CodingSchema",
      "対称性のために層を作ると、「仕様の綴り方」という名で実装の綴りが仕様へ入る口ができる"),
     ("仕様を書くとき規約を読むか", "読まない。読むのは schema の記入指示と knowledge だけ",
      "読ませると、この製品ではこう綴るという話が仕様へ流れ込む"),
     ("実装を導く入力", "仕様と規約の両方。どちらか一方では具体が決まらない",
      "仕様だけで実装が決まる形にすると、仕様が実装の転記になる"),
     ("どこまでを文書にするか", "上は knowledge（共通の出発点）、下は実装とテスト（合流する先）",
      "抽象の段は上にも下にも無限に作れるので、どこで切るかを決めないと際限がなくなる"),
   ])),

 sec("06", "答えないこと",
   table(["項目", "種別", "行き先"], [
     ("どの特徴を仕様へ置き、どれを規約へ置くか", '<span class="kindtag out">範囲外</span>',
      "この決定は関係の形だけを扱う。分け目を裁く基準は別の決定で定める"),
     ("実装の綴りをどこから導くか", '<span class="kindtag out">範囲外</span>',
      "同上。綴りの導出元を扱う別の決定で定める"),
     ("knowledge から記入指示へのつながりを、どう突き合わせるか", '<span class="kindtag unv">未確認</span>',
      "この関係の中で唯一、検知の仕組みが無いつながり。機構を作る別の決定で扱う"),
     ("仕様の執筆に規約が要る場面が今後現れないか", '<span class="kindtag lim">限界</span>',
      "<b>行き先を持たない。</b>将来のことなので確かめる手段が無い。現れた時点でこの決定を改める"),
   ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span>'
 '<span class="m">新しい形式へ書き換えたうえで、改めて承認を受ける。決定の内容は前の版から変えていない。</span>'
 '</div></section>',

 sec("08", "関連",
   table(["種類", "対象"], [
     ("縛る対象", "仕様・規約・実装の関係。以後の決定は、この関係の上で置き場所を論じる"),
     ("先立つ決定", "理由は論証の連鎖として書く（この記録がその形で書かれている）"),
     ("この決定を使う予定", "仕様と規約の分け目を裁く基準／仕様は実装の綴りを持たない／knowledge から記入指示への突き合わせ"),
   ])),
])

extra = """
.cmp.stack{grid-template-columns:1fr}
.pane .box{display:flex;justify-content:center}
.pane svg{display:block;max-width:100%;height:auto}
.win{font-family:var(--mono);font-size:.68rem;padding:.08em .45em;border-radius:2px;white-space:nowrap;color:var(--against);background:var(--against-bg)}
"""
html = (f"<title>規約は層ではなく、実装を導くもう一つの入力とする</title>"
        f"<style>{CSS}\n{FIGCSS}\n{extra}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-convention-is-not-a-layer.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")