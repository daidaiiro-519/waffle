import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, extra

UNIT = "agg-document#逸脱していないか判定する"

def slots(a, b, c):
    """3つの結び目の状態。値は 'on' / 'off' / 'bad'。"""
    labels = [("宣言 ── シナリオが単位を指す", a),
              ("転記 ── テストがシナリオを載せる", b),
              ("名乗り ── 実装が宣言を指す", c)]
    out = []
    for name, st in labels:
        mark = {"on":"●","off":"○","bad":"✕"}[st]
        out.append(f'<span class="slot {st}"><span class="m">{mark}</span>{name}</span>')
    return '<div class="slots">' + "".join(out) + '</div>'

def term(lines):
    return '<pre class="term">' + "\n".join(lines) + '</pre>'

def scene(n, title, what, slot_html, term_html, note=None):
    h = (f'<div class="scene"><div class="sc-h"><span class="sc-n">{n}</span>'
         f'<span class="sc-t">{title}</span></div>'
         f'<p class="sc-w">{what}</p>{slot_html}{term_html}')
    if note:
        h += f'<p class="sc-note">{note}</p>'
    return h + "</div>"

# ── 場面
s0 = scene("00","そろっている",
  "宣言・転記・名乗りの3つが揃っている。",
  slots("on","on","on"),
  term(['<span class="p">$</span> waffle 乖離を見る',
        '',
        '  <span class="g">乖離はありません</span>',
        '  宣言 57 / 名乗られている 57 / 名乗りの余り 0',
        '  シナリオ 214 / テストに写っている 214']))

s1 = scene("01","実装を書き忘れた",
  "宣言もシナリオもテストも書いたが、<b>実装が無い</b>。テストは落ちる ── "
  "ただしテストが落ちるのは<b>その1件を試したとき</b>だけである。"
  "宣言だけ足してテストを後回しにすると、テストすら落ちない。",
  slots("on","on","bad"),
  term(['<span class="p">$</span> waffle 乖離を見る',
        '',
        '  <span class="r">✕ 宣言にあって、実装に無い</span>  1件',
        f'      {UNIT}',
        '      この宣言を名乗る実装がありません']),
  "<b>テストを1本も書いていなくても捕まる。</b>宣言と実装だけを突き合わせている")

s2 = scene("02","名乗っていない実装が生えた",
  "誰かが便利だからと関数を足した。<b>どの宣言も指していない。</b>",
  slots("on","on","bad"),
  term(['<span class="p">$</span> waffle 乖離を見る',
        '',
        '  <span class="r">✕ どの宣言も指していない実装があります</span>  1件',
        '      document.py :: normalize_schema_ref',
        '      仕様として合意されていない振る舞いです']),
  "<b>同じ名乗りを逆向きに数えるだけ。</b>新しい仕組みは要らない")

s3 = scene("03","仕様を直して、テストを直し忘れた",
  "シナリオの Then を「拒否され、判定は行われない」へ書き換えた。"
  "<b>テストの docstring は古いまま。</b>",
  slots("on","bad","on"),
  term(['<span class="p">$</span> waffle 乖離を見る',
        '',
        '  <span class="r">✕ シナリオがテストに写っていません</span>  1件',
        '      Scenario: schemaRef を持たない文書は判定できない',
        '      仕様   Then  拒否され、判定は行われない',
        '      テスト Then  <span class="r">エラーになる</span>']),
  "<b>テストは緑のまま通る。</b>それでも捕まる ── 一字一句で照合しているため")

s4 = scene("04","名乗りが嘘だった",
  "実装は名乗っているが、<b>指している宣言が違う</b>。"
  "コピーして作ったときに起きやすい。",
  slots("on","on","on"),
  term(['<span class="p">$</span> waffle 乖離を見る',
        '',
        '  <span class="y">△ 名乗りとシナリオが食い違います</span>  1件',
        '      test_rejects_document_without_schema_ref が呼ぶ実装は',
        '        <span class="y">agg-schema#新しい版を切る</span> を名乗っています',
        '      しかし載せたシナリオが指す単位は',
        '        <span class="y">agg-document#逸脱していないか判定する</span> です']),
  "<b>3辺だけでは当たらない。</b>テストが呼ぶ先まで辿る4辺目が要る ── "
  "だから △ にしてある")

s5 = scene("05","テストの中身が空だった",
  "docstring にはシナリオが一字一句写っている。実装も名乗っている。"
  "<b>ただしテストの本体が何も確かめていない。</b>",
  slots("on","on","on"),
  term(['<span class="p">$</span> waffle 乖離を見る',
        '',
        '  <span class="g">乖離はありません</span>']),
  "<b>これは閉じない。</b>宣言の形では届かない ── "
  "「試していない」と「合っている」は、宣言からは同じに見える。"
  "<b>網羅率や変異テストの仕事だと明示して、ここでは赤にしない</b>")

# ── まとめ
summary = tbl(["ずれ方","何が赤くなるか","要る辺"],[
 ("keyrow",["実装を書き忘れた","<b>宣言にあって、実装に無い</b>","名乗り"]),
 ("keyrow",["名乗っていない実装が生えた","<b>どの宣言も指していない実装があります</b>","名乗り（逆向き）"]),
 ("",["仕様を直して、テストを直し忘れた","<b>シナリオがテストに写っていません</b>","転記"]),
 ("",["テストを直して、仕様を直し忘れた","同上（照合は向きを持たない）","転記"]),
 ("",["名乗りが嘘だった","<b>名乗りとシナリオが食い違います</b>","<b>4辺目</b>（テストが呼ぶ先）"]),
 ("",["テストの中身が空だった","<b>何も出ない</b>","<b>閉じない</b>"]),
])

# ── 3つの結び目
knots = tbl(["結び目","誰が誰を指すか","仕様に足すものはあるか"],[
 ("keyrow",["<b>宣言</b>","シナリオ → 単位",
   "<b>ある。これ1つだけ。</b>指し先は仕様自身の識別子"]),
 ("",["<b>転記</b>","テスト → シナリオ（一字一句）","無い"]),
 ("keyrow",["<b>名乗り</b>","実装 → 宣言の識別子",
   "<b>無い。</b>名乗るのは実装の側で、書き方は規約が決める"]),
])

body = "".join([
 '<header><p class="eyebrow">完成イメージ</p>'
 '<h1>ずれたとき、何が赤くなるか</h1>'
 '<p class="lede">同じ1件を、<b>6通りにずらしてみる</b>。'
 'それぞれで検査が何を言うかを、そのまま並べた。'
 '最後の1つは<b>何も言わない</b> ── 閉じないものが何かを、実際に見るためである。</p></header>',

 sec("01","3つの結び目",
  "この頁を通して、<b>この3つが在るか無いか</b>だけを見る。",
  knots,
  '<p class="fignote">以降の場面では、3つの状態を '
  '<span class="slot on"><span class="m">●</span>ある</span>'
  '<span class="slot bad"><span class="m">✕</span>壊れている</span> で示す。</p>'),

 sec("02","6つの場面",
  "実例は「文書が schema に適合するかを判定する」1件。"
  "<b>これを6通りにずらす。</b>",
  s0 + s1 + s2 + s3 + s4 + s5),

 sec("03","まとめ",
  "<b>3辺で4つ捕まる。</b>4辺目で5つ目、6つ目は閉じない。",
  summary),

 sec("04","読み方",
  "この頁で見せたかったのは<b>2つ</b>である。",
  tbl(["","何を見てほしいか"],[
   ("keyrow",["<b>テストが緑でも赤が出る</b>",
     "場面 03 がそれである。テストは通るのに、仕様と写しがずれていれば捕まる。"
     "<b>テストの合否とは別の線で見ている</b>"]),
   ("keyrow",["<b>テストが1本も無くても赤が出る</b>",
     "場面 01 がそれである。宣言と名乗りだけを突き合わせるので、"
     "<b>実装に着手していないことがそのまま出る</b>"]),
   ("",["逆に、閉じないもの",
     "場面 05。<b>3つの結び目がすべて在っても、中身が空なら何も言えない。</b>"
     "ここを閉じたことにしないのが、いちばん大事だと考えている"]),
  ])),
])

extra2 = extra + """
.slots{display:flex;flex-wrap:wrap;gap:.4rem}
.slot{display:inline-flex;align-items:center;gap:.35rem;font-size:.74rem;line-height:1;
      padding:.32em .6em;border-radius:2px;border:1px solid var(--rule);background:var(--surface-2);
      color:var(--ink-soft)}
.slot .m{font-size:.85rem;line-height:1}
.slot.on{border-color:#1B6B4A;color:#1B6B4A;background:var(--infer-bg)}
.slot.off{border-color:var(--rule);color:var(--ink-faint)}
.slot.bad{border-color:#9A3B44;color:#9A3B44;background:var(--against-bg)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  .slot.on{border-color:#79C5A0;color:#79C5A0}
  .slot.bad{border-color:#DE9AA1;color:#DE9AA1}}}
:root[data-theme="dark"] .slot.on{border-color:#79C5A0;color:#79C5A0}
:root[data-theme="dark"] .slot.bad{border-color:#DE9AA1;color:#DE9AA1}
.scene{border:1px solid var(--rule);border-radius:2px;background:var(--surface);
       padding:1rem 1.1rem;display:flex;flex-direction:column;gap:.7rem}
.scene + .scene{margin-top:1rem}
.sc-h{display:flex;align-items:baseline;gap:.7rem}
.sc-n{font-family:var(--mono);font-size:.7rem;color:var(--ink-faint);letter-spacing:.1em}
.sc-t{font-family:var(--serif);font-size:1.08rem;font-weight:600}
.sc-w{font-size:.9rem;line-height:1.8;color:var(--ink-soft);margin:0}
.sc-w b{color:var(--ink)}
.sc-note{font-size:.83rem;line-height:1.75;color:var(--ink-soft);margin:0;
         padding-left:.8rem;border-left:2px solid var(--rule)}
.sc-note b{color:var(--ink)}
.term{margin:0;font-family:var(--mono);font-size:.76rem;line-height:1.85;
      background:var(--surface-2);border:1px solid var(--rule-soft);border-radius:2px;
      padding:.8rem .9rem;overflow-x:auto;white-space:pre;color:var(--ink-soft)}
.term .p{color:var(--ink-faint)}
.term .g{color:#1B6B4A;font-weight:600}
.term .r{color:#9A3B44;font-weight:600}
.term .y{color:#7A4E12;font-weight:600}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  .term .g{color:#79C5A0} .term .r{color:#DE9AA1} .term .y{color:#D9B674}}}
:root[data-theme="dark"] .term .g{color:#79C5A0}
:root[data-theme="dark"] .term .r{color:#DE9AA1}
:root[data-theme="dark"] .term .y{color:#D9B674}
"""
html = ("<title>ずれたとき、何が赤くなるか</title>"
        f"<style>{CSS}\n{extra2}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/drift-walkthrough.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")
