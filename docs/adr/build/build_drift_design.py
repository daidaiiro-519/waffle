import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra

# ── 01 乖離の3つの形
forms = tbl(["乖離の形","何が起きているか"],[
 ("keyrow",["<b>在るはずのものが無い</b>",
   "宣言した単位を、実装の誰も実現していない。<b>仕様には在るが、動くものが無い</b>"]),
 ("keyrow",["<b>無いはずのものが在る</b>",
   "どの宣言も指していない実装が生えている。"
   "<b>誰も仕様として合意していない振る舞いが動いている</b>"]),
 ("",["<b>在るが、言ったとおりに振る舞わない</b>",
   "宣言した基準を満たさない。<b>形はあるが、中身が違う</b>"]),
])

# ── 02 結び目
knots = tbl(["乖離の形","何で捕まえるか","誰が誰を指すか"],[
 ("keyrow",["在るはずのものが無い","<b>名乗り</b>","実装 → 仕様の識別子"]),
 ("keyrow",["無いはずのものが在る","<b>同じ名乗りを、逆向きに数える</b>","実装 → 仕様の識別子"]),
 ("",["言ったとおりに振る舞わない","<b>転記</b>","テスト → シナリオ（一字一句）"]),
])

knots_note = ('<p class="fignote"><b>2本で足りる。</b>'
 '名乗りが存在を、転記が振る舞いを担う。'
 '名乗りは1本で<b>両方向</b>に数えられるので、'
 '「無い」と「余っている」に別々の仕組みを持たなくてよい。</p>')

# ── 03 三角形
tri_note = ('<div class="grid4">'
 '<div class="gbox"><div class="gk2">仕様</div><div class="gv">単位</div>'
 '<div class="gn">集約・エンティティ・値オブジェクト・業務サービス・業務ユースケース</div></div>'
 '<div class="garw">── 宣言 ──▶</div>'
 '<div class="gbox"><div class="gk2">仕様</div><div class="gv">シナリオ</div>'
 '<div class="gn">Given / When / Then。<b>どの単位の振る舞いかを指す</b></div></div>'
 '<div class="gvert">▲<br><span>名乗り</span></div><div></div>'
 '<div class="gvert">│<br><span>転記</span><br>▼</div>'
 '<div class="gbox"><div class="gk2">実装</div><div class="gv">クラス／関数／手続き</div>'
 '<div class="gn"><b>どの宣言の実現かを名乗る</b></div></div>'
 '<div class="garw">◀── 呼ぶ ──</div>'
 '<div class="gbox"><div class="gk2">テスト</div><div class="gv">docstring</div>'
 '<div class="gn">シナリオを一字一句で載せる</div></div>'
 '</div>'
 '<p class="fignote"><b>3点が閉じると、自己申告の裏が取れる。</b>'
 '名乗りは実装が自分で書くものなので、それだけでは嘘をつける。'
 'だが「<b>シナリオ S を載せたテストが呼ぶ実装は、S が指す単位を名乗っているはず</b>」が'
 '成り立たなければ、名乗りかシナリオのどちらかが嘘である。'
 '4辺目（テストが呼ぶ先を辿る）は<b>呼び出しの走査</b>が要るので、費用を別に測る。'
 '<b>3辺だけでも、存在と振る舞いは当たる。</b></p>')

# ── 04 実物で見る
def lane(label, bodyhtml, note):
    return (f'<div class="lane"><div class="lane-h">{label}</div>'
            f'{bodyhtml}<p class="lane-n">{note}</p></div>')

spec_body = '<pre class="gk">agg-document\n'\
 '  公開する操作\n'\
 '    逸脱していないか判定する\n'\
 '      受け入れ基準\n'\
 '        schemaRef を持たない文書を渡したとき、判定せず拒否する\n'\
 '      シナリオ\n'\
 '        Scenario: schemaRef を持たない文書は判定できない\n'\
 '        Given  schemaRef を持たない文書\n'\
 '        When   逸脱していないか判定する\n'\
 '        Then   拒否され、判定は行われない\n'\
 '        振る舞う単位: agg-document#逸脱していないか判定する</pre>'

test_body = '<pre class="gk">def test_rejects_document_without_schema_ref():\n'\
 '    """\n'\
 '    Scenario: schemaRef を持たない文書は判定できない\n'\
 '    Given  schemaRef を持たない文書\n'\
 '    When   逸脱していないか判定する\n'\
 '    Then   拒否され、判定は行われない\n'\
 '    """</pre>'

impl_thick = '<pre class="gk">class Document:\n'\
 '    """構造化された成果物。\n'\
 '\n'\
 '    実現する宣言: ent-document\n'\
 '    """\n'\
 '\n'\
 '    def validate(self, schema):\n'\
 '        """schema に適合するかを判定する。\n'\
 '\n'\
 '        実現する宣言:\n'\
 '          agg-document#逸脱していないか判定する\n'\
 '        """</pre>'

impl_thin = '<pre class="gk">def validate_document(doc, schema):\n'\
 '    """schema に適合するかを判定する。\n'\
 '\n'\
 '    実現する宣言:\n'\
 '      agg-document#逸脱していないか判定する\n'\
 '    """</pre>'

tri = ('<div class="tri">'
 + lane("仕様 ── document.json", spec_body,
        "宣言の正本。<b>シナリオが、どの単位の振る舞いかを指す</b>（足すのはここだけ）")
 + lane("テスト ── docstring", test_body,
        "シナリオを一字一句で載せる。<b>ずれれば照合が落ちる</b>")
 + lane("実装 ── docstring", impl_thick,
        "<b>どの宣言の実現かを名乗る。</b>書き方（<code>実現する宣言:</code>）は規約が決める")
 + '</div>')

shapes = ('<div class="tri" style="grid-template-columns:1fr 1fr">'
 + lane("厚い実装 ── クラスで実現する", impl_thick, "集約もエンティティもクラスとして現れる")
 + lane("薄い実装 ── 手続きで実現する", impl_thin, "<b>クラスは無い。</b>それでも名乗れる")
 + '</div>')

shapes_why = '<div class="chain">' + "".join([
  step("evidence","出典",
    "knowledge がアンチパターンとして名指ししている ── "
    "「<b>集約の宣言をクラスの存在と同一視する</b>」。"
    "欠陥は「宣言した不変条件を、<b>クラスもトランザクション境界も守っていない</b>」ときに生じる"),
  joint("だから"),
  step("conclude","言えること",
    "<b>クラスが在るかは、仕様の関心事ではない。</b>"
    "実装がどんな形で実現するかは、規約と実装の判断である"),
  joint("では何を担保したいのか"),
  step("evidence","出典",
    "書き起こしはこう言う ── 「<b>ソースコードが同じ言葉を語り</b>、"
    "業務エキスパートの捉え方をそのまま表現する」。"
    "欲しいのは<b>言葉が実装まで届いていること</b>であって、クラスがあることではない"),
  joint("問いを置き換えると"),
  step("conclude","結論",
    "検査するのは「<b>宣言した単位が、実装のどこかで名乗られているか</b>」。"
    "クラスでも関数でも手続きでもよい。"
    "<b>形を問わないので、実装がどう作られるかを先に知る必要が無い</b>"),
  joint("その帰結"),
  step("conclude","結論",
    "<b>仕様は、実装の厚みも様式も持たなくてよい。</b>"
    "それを持ちたくなるのは、実装の形を当てにいっているときだけである"),
]) + "</div>"

# ── 06 足すもの
add = tbl(["何を","どこへ","仕様の高さを越えないか"],[
 ("keyrow",["<b>シナリオが「どの単位の振る舞いか」を指す</b>","<b>Domain の型</b>",
   f"{ok} 指すのは<b>仕様自身の識別子</b>。実装の語彙は1つも出てこない"]),
 ("",["実装が、どの宣言の実現かを名乗る","規約（実装の書き方）",
   f"{ok} <b>仕様への追加は無い。</b>名乗るのは実装の側"]),
 ("",["名乗りの書き方（どの語で、どこに書くか）","規約",
   f"{ok} 仕様がここを決めると、実装の語彙が入る"]),
])

add_note = ('<p class="fignote"><b>仕様に足すのは1つだけである。</b>'
 'しかも足すのは<b>シナリオが単位を指す</b>という参照であって、'
 '実装について何かを述べる欄ではない。'
 'これが無いと、シナリオが「どの単位の振る舞いを確かめているのか」が分からず、'
 '三角形の1辺が引けない。</p>')

# ── 07 閉じないもの
remains = tbl(["閉じないもの","なぜ閉じないか","どう扱うか"],[
 ("keyrow",["<b>「試していない」と「合っている」が見分けられない</b>",
   "テストが緑でも、中身が空かもしれない。"
   "<b>宣言の形では届かない</b> ── 網羅率や変異テストの領域である",
   "<b>型に足さない。</b>別の道具の仕事だと明示する"]),
 ("",["宣言した「常に満たすこと」を、実装が本当に守っているか",
   "変える操作のシナリオが覆うが、言えるのは<b>「覆うシナリオが在るか」まで</b>。"
   "「トランザクション境界に収まっているか」を静的解析だけで判定できる範囲は限られる ── "
   "knowledge が留保として明記している",
   "<b>判定できない部分は対象外だと明示し、赤にしない</b>"]),
 ("",["名乗りが嘘 ── 違う宣言を指している","名乗りは自己申告である",
   "<b>三角形の4辺目（テストが呼ぶ先）で裏が取れる。</b>費用を別に測る"]),
])

body = "".join([
 '<header><p class="eyebrow">段2 の仕様 ── 材料</p>'
 '<h1>仕様と実装を、どこで結ぶか</h1>'
 '<p class="lede">基準とシナリオは<b>振る舞い</b>しか運ばない。'
 'TDD で緑になっても、宣言した単位が実装に在る保証にはならない。'
 '<b>結び目をもう1本足す</b>ための設計である。'
 'いまの検査や実装の形は根拠にしていない ── <b>あるべき形だけから組んでいる</b>。</p></header>',

 sec("01","乖離は3つの形しかない",
  "仕様と実装がずれるとき、起きていることは<b>この3つのどれか</b>である。",
  forms),

 sec("02","結び目は2本で足りる",
  "<b>名乗りが存在を、転記が振る舞いを担う。</b>名乗りは1本で両方向に数えられる。",
  knots, knots_note),

 sec("03","3点が閉じる",
  "名乗りは実装の自己申告である。<b>三角形が閉じて初めて、裏が取れる。</b>",
  tri_note),

 sec("04","実物で見る ── 1件を3か所で",
  "同じ1件が、仕様・テスト・実装の3か所に現れる。<b>指し先はすべて仕様の識別子</b>である。",
  tri),

 sec("05","形を問わない",
  "同じ宣言を、<b>クラスで実現しても手続きで実現しても、検査は同じように当たる</b>。"
  "だから仕様は実装の厚みを知らなくてよい。",
  shapes,
  fold("なぜ形を問わないのかを開く", '<div style="padding:.9rem">'+shapes_why+'</div>')),

 sec("06","仕様に足すのは1つだけ",
  "残りは規約の管轄である。<b>仕様は実装について一言も述べない。</b>",
  add, add_note),

 sec("07","閉じないもの",
  "<b>3つ残る。残ることを明示して、赤にしない。</b>"
  "閉じないものを閉じたことにするのが、いちばん危ない。",
  remains),

 '<section><h2><span class="num">08</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span></div></section>',

 sec("09","この頁で決めないこと",
  "2点。<b>どちらもここで決めると、境界を越える</b>。",
  tbl(["項目","なぜここで決めないか"],[
   ("keyrow",["名乗りの<b>書き方</b>（どの語で、どこに書くか）",
     "<b>規約の管轄</b>である。仕様がここを決めると、また実装の語彙が入る"]),
   ("",["テストが呼ぶ先まで辿るかどうか",
     "三角形の4辺目は<b>呼び出しの走査</b>が要る。"
     "<b>3辺だけでも存在と振る舞いは当たる</b>ので、先に3辺を固める"]),
  ])),
])

extra2 = extra + """
.tri{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;align-items:stretch}
@media(max-width:60rem){.tri{grid-template-columns:1fr}}
.lane{border:1px solid var(--rule);border-radius:2px;background:var(--surface);
      padding:.9rem;display:flex;flex-direction:column;gap:.6rem;min-width:0}
.lane-h{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;
        color:var(--ink-faint)}
.lane-n{font-size:.82rem;line-height:1.7;color:var(--ink-soft);margin:0}
.lane-n b{color:var(--ink)}
.lane .gk{font-size:.72rem;line-height:1.7}
.gk{margin:0;font-family:var(--mono);font-size:.78rem;line-height:1.8;background:var(--surface-2);
    border:1px solid var(--rule-soft);border-radius:2px;padding:.7rem .8rem;overflow-x:auto;
    white-space:pre;color:var(--ink)}
.grid4{display:grid;grid-template-columns:1fr auto 1fr;gap:.5rem;align-items:center}
@media(max-width:52rem){.grid4{grid-template-columns:1fr}.garw,.gvert{display:none}}
.gbox{border:1px solid var(--rule);border-radius:2px;background:var(--surface);padding:.7rem .85rem}
.gk2{font-family:var(--mono);font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-faint)}
.gv{font-family:var(--serif);font-size:1rem;font-weight:600;margin-top:.1rem}
.gn{font-size:.8rem;line-height:1.65;color:var(--ink-soft);margin-top:.15rem}
.gn b{color:var(--ink)}
.garw,.gvert{text-align:center;font-family:var(--mono);font-size:.68rem;color:var(--ink-faint);line-height:1.5}
"""
html = ("<title>仕様と実装を、どこで結ぶか</title>"
        f"<style>{CSS}\n{extra2}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/drift-binding.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")
