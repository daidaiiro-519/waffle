import sys, pathlib, re
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S); sys.path.insert(0,"/home/daidaiiro/workspace/waffle/.claude/skills/design-svg")
from _common import CSS, sec, fold, tbl, extra
from svg_engine.compose import render_figure
from svg_engine.tokens import DEFAULT_THEME

FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
def figure(inner, vb, cap, minw="40rem"):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:{minw};width:100%;height:auto;display:block" {FF}>{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

# ── 図1 概念図 ── 中心も外周も空で、真ん中だけがある
def ring(cx, cy, r, stroke, dash="", fill="none"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.3"{d}/>'
def txt(x, y, t, size=12, fill="var(--ink)", w=600, anchor="middle"):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{w}" fill="{fill}">{t}</text>')
a  = txt(150, 20, "クリーンアーキ／オニオンが想定する形", 11.5, "var(--ink-faint)", 500)
a += ring(150, 130, 96, "var(--rule)") + ring(150, 130, 62, "var(--rule)") + ring(150, 130, 30, "var(--ink)", fill="var(--surface)")
a += txt(150, 128, "業務規則", 11) + txt(150, 142, "を守る", 9.5, "var(--ink-faint)", 400)
a += txt(150, 92, "応用", 10.5, "var(--ink-soft)", 500) + txt(150, 46, "基盤", 10.5, "var(--ink-soft)", 500)
a += txt(430, 20, "このエンジンを当てはめた形", 11.5, "var(--ink-faint)", 500)
a += ring(430, 130, 96, "var(--against)", "5 4") + ring(430, 130, 62, "var(--infer)") + ring(430, 130, 30, "var(--against)", "5 4")
a += txt(430, 133, "空", 12, "var(--against)")
a += txt(430, 92, "純粋な計算", 10.5, "var(--infer)", 600) + txt(430, 46, "空", 11, "var(--against)")
FIG1 = figure(a, "0 0 620 240",
  "<b>中心（業務規則）も外周（基盤）も空で、真ん中だけがある。</b>"
  "3つのパターンはどれも「内側を外側の揺れから守る」ために立っている。守る対象と揺れる相手が"
  "両方とも存在しないので、輪を描くと名前のついた空箱が2つできる。")

# ── 図2 層 ── すでに成立していた
LAYERS = [("3", "合成", "compose, canvas"),
          ("2", "部品", "shapes ×8（箱・辺・囲み・量・表・装飾…）"),
          ("1", "方針・配置", "style / sugiyama, radial, tree, grid, nesting, labels"),
          ("0", "語彙・台帳", "tokens, text, geometry, boolean, registry, lint_values")]
b = ""
for i, (n, name, mods) in enumerate(LAYERS):
    y = 26 + i * 54
    b += f'<rect x="14" y="{y}" width="470" height="42" rx="3" fill="var(--surface)" stroke="var(--rule)"/>'
    b += f'<rect x="14" y="{y}" width="4" height="42" fill="var(--ink-faint)"/>'
    b += txt(32, y + 19, f"層{n}　{name}", 12, "var(--ink)", 600, "start")
    b += txt(32, y + 34, mods, 10, "var(--ink-faint)", 400, "start")
    if i < 3:
        b += (f'<line x1="504" y1="{y+44}" x2="504" y2="{y+50}" stroke="var(--ink-faint)" stroke-width="1.3"/>'
              f'<polygon points="504,{y+56} 500.2,{y+48} 507.8,{y+48}" fill="var(--ink-faint)"/>')
b += txt(516, 130, "呼んでよい向き", 10, "var(--ink-faint)", 400, "start")
b += txt(516, 144, "（上から下だけ）", 10, "var(--ink-faint)", 400, "start")
b += f'<rect x="516" y="176" width="150" height="46" rx="3" fill="var(--surface)" stroke="var(--infer)" stroke-width="1.6"/>'
b += txt(591, 196, "下から上への呼び出し", 10, "var(--infer)", 500)
b += txt(591, 212, "0 件", 15, "var(--infer)", 700)
FIG2 = figure(b, "0 0 690 248",
  "<b>責務で層を引き直して実測した結果。規則性が無いのではなく、規則性があるのに書かれていなかった。</b>"
  "`verify` はこの数直線に載らない ── 生成物を外から検査する直交した軸である。")

# ── 図3 パイプとフィルタ ── エンジン自身に描かせる
th = dict(DEFAULT_THEME, **{
    "color.box-fill": "var(--surface)", "color.box-stroke": "var(--rule)",
    "color.ink": "var(--ink)", "color.line": "var(--ink-faint)",
    "color.ink-faint": "var(--ink-faint)", "color.accent": "var(--infer)",
    "color.accent-bg": "var(--surface)",
    "font.family": "Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"})
stages = ["宣言", "解決", "描画", "配置", "合成"]
types = ["Declaration", "Style", "Fragment", "Placed"]
_pipe = render_figure(
    [{"id": s, "label": s} for s in stages],
    [{"from": a_, "to": b_, "label": t} for a_, b_, t in zip(stages, stages[1:], types)],
    direction="LR", theme=th)
PIPE_INNER = re.sub(r'^<svg[^>]*>', '', _pipe)[:-6]
_vb = re.search(r'viewBox="([^"]+)"', _pipe).group(1)
FIG3 = figure(PIPE_INNER, _vb,
  "<b>この図はこのエンジン自身が描いている</b>（配色はページのトークンを注入した）。"
  "段はすでに一本の流れとして存在する。足りないのは矢印に書いた型で、"
  "いまはこの5段が全部 <code>dict</code> と文字列で繋がっている ── だから段を飛ばしても書けてしまう。",
  "34rem")

body="".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>層は宣言して凍結し、段は型で繋ぎ、残りは落ちる試験で縛る</h1>'
 '<p class="lede">この描画エンジンに規則性が無いわけではなかった。'
 '<b>責務で層を引くと下から上への呼び出しは0件で、すでに厳格な層状だった。</b>'
 'ただし誰も宣言しておらず、誰も検査していない。'
 '同じ理由で「Waffle語彙を一切知らない」は<b>11ファイルで破れ</b>、'
 '直書きを禁じる検査は<b>実装済みのまま呼ばれず45件が放置</b>されていた。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">この描画エンジンは、'
  '<b>クリーンアーキテクチャ／オニオン／ヘキサゴナルのいずれの構成も採らない</b>。'
  '採るのは<b>厳格な層状・パイプとフィルタ・関数核</b>の3つで、規約は次の3条とする。</p>'
  '<div class="key"><span class="lbl">規約1</span>'
  '<span class="txt"><b>下から上を呼ばない。層を飛ばさない。</b>（いま0違反。宣言して凍結する）</span></div>'
  '<div class="key"><span class="lbl">規約2</span>'
  '<span class="txt"><b>段ごとに型が変わり、前の段を飛ばせない。</b>（未着手。<code>dict</code> が27箇所）</span></div>'
  '<div class="key"><span class="lbl">規約3</span>'
  '<span class="txt"><b>契約は中立なモジュールが所有し、実装が所有しない。</b>（5違反）</span></div>'
  '<p class="main">構造で縛れないもの（語彙の漏れ・値の直書き）は落ちる試験で捕まえ、'
  '<b>いま破れている分はファイルごとの件数を天井として記録し、増えたら落とす</b>。</p></div>'),

 sec("02","クリーンアーキとオニオンを採らない理由",
  "3つとも同じ1点で立つ ── 依存は内側へ向かい、内側は外側を知らない。その前提が両側とも欠けている。",
  FIG1 + tbl(["輪","何が入るはずか","実測"],[
    ("keyrow",["最内周","業務規則（Entities / Domain Model）",
      "<b>空。</b><code>geometry</code> も <code>sugiyama</code> も数学で、"
      "業務エキスパートが「そうではない」と言う対象が存在しない"]),
    ("",["中間","応用・変換","<b>ここだけがある。</b>純粋な計算"]),
    ("keyrow",["最外周","基盤（DB・Web・フレームワーク）",
      "<b>空。</b>サードパーティのimportが1件もなく、I/O・時刻・乱数のいずれも持たない"]),
  ]),
  fold("では当てはまる場所はどこかを開く",
   '<p>Clean 自身の言い方では「データベースもWebも<b>詳細</b>である」。描画ライブラリはその詳細側にあたる。'
   'つまり<b>このエンジンはWaffleのクリーンアーキにおける最外周の輪そのもの</b>であり、'
   '輪の構造はWaffle側で既に成立している。'
   'エンジンの内側へもう一枚オニオンを入れ子にする話ではない。</p>')),

 sec("03","層はすでに成立していた",
  "責務で層を引き直し、下から上への呼び出しを機械で数えた。",
  FIG2 + tbl(["パターン","規約","いまの状態"],[
    ("keyrow",["厳格な層状","下から上を呼ばない／層を飛ばさない","<b>0違反。</b>宣言して凍結できる"]),
    ("keyrow",["パイプとフィルタ","段ごとに入出力の型が決まり、段を飛ばせない",
      "段はあるが<b>全部 <code>dict</code> で繋がっている</b>"]),
    ("",["関数核","純粋・決定的・副作用なし","成立（例外は台帳の登録副作用1つ）"]),
  ]),
  fold("層内に1つある違反を開く",
   '<p><code>grid</code>・<code>tree</code>・<code>radial</code>・<code>nesting</code> が、'
   '同じ層の <code>sugiyama</code> から <code>LayoutResult</code> を借りている（実測5箇所）。'
   '<b>4つの戦略が共有する契約を、戦略のうちの1つが所有している。</b>'
   'これが規約3の対象で、中立なモジュールへ5行を移すだけで解ける ── 層は増やさない。</p>')),

 sec("04","段を型で繋ぐ",
  "型で防げるのは「形と状態」の誤りで、検査で捕まえるのは「語と数」の誤り。片方がもう片方を含まない。",
  FIG3 + tbl(["このセッションで実際に踏んだ誤り","型で防げるか"],[
    ("keyrow",["<code>groups</code> と <code>layout=</code> の同時指定が黙って無視された",
      "<b>防げる</b> ── ありえない組み合わせを構築できない形にする"]),
    ("keyrow",["<code>placement</code> が <code>\"own-origin\"</code>/<code>\"absolute\"</code> という文字列",
      "<b>防げる</b> ── 座標空間が別の型なら混ざらない。フラグは消えて型になる"]),
    ("keyrow",["物差しが中心↔縁を取り違え、辺の長さを1.3〜1.9倍と誤読した",
      "<b>防げる</b> ── 同じ理由"]),
    ("",["<code>style</code> の未知トークン名が素通りする","半分"]),
    ("",["Waffle語彙が11ファイルへ漏れた","<b>防げない</b>（文章）"]),
    ("",["見た目の値の直書きが45件","<b>防げない</b>（数値リテラル）"]),
  ])),

 sec("05","縛りが効くための前提",
  "型注釈を足すだけでは何も縛られない。同じ失敗を3度繰り返すことになる。",
  '<p>実測すると、関数150件のうち<b>114件に戻り値の型注釈がある</b>。'
  'そして<b>静的検査器は1つも設定されていない</b>（mypy も pyright も無い）。'
  'つまり型注釈は、いま docstring と同じ「宣言だけの契約」である。</p>'
  '<p>したがって<b>規約2に着手する前に、静的検査器を1つ入れる</b>。'
  '順序を逆にすると、docstring・型注釈に続いて3度目の宣言だけの契約を作ることになる。</p>'),

 sec("06","構造で縛れないものの扱い",
  "ゼロを要求すると、検査を弱めるか無視するかのどちらかになる。どちらに転んでも、いまと同じ場所へ戻る。",
  '<p>語彙の11ファイルはWaffle側の作業と場所が重なり、直書きの45件には誤検出が混じる'
  '（<code>len(poly) &gt;= 3</code> のような構造上の数値まで拾っている）。'
  'そこで<b>ファイルごとの現在値を天井として記録する。下げるのは自由、上げるのは不可。</b>'
  '新しい違反はその場で落ち、既存の負債は消えないまま見え続ける。</p>',
  fold("例外表にする案を採らなかった理由を開く",
   '<p>破れている箇所を1件ずつ「これは例外」と登録する形も採れる。採らなかったのは、'
   '<b>例外表は増える方向にしか動かないから</b>である。1件足すたびに理由が書かれ、'
   'その理由が妥当かは誰も再検査しない。件数の天井なら、<b>減ったかどうかが数字1つで分かる</b>。</p>')),

 sec("07","答えないこと",None,
  '<p>この決定は<b>「宣言した規約を実物が守っているか」しか裁かない</b>。'
  '規約そのものが正しいかは裁けない ── それは人間の判断であり、advisor の敵対的検証が担う。</p>'
  '<p>また、Waffle本体への配置（ポートをどこに置き、変換アダプタをどこへ書くか）は'
  'この決定の外にある。ここで決めるのは<b>エンジンの内側の規律だけ</b>である。</p>'),

 '<section><h2><span class="num">08</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-29</span></div></section>',

 sec("09","関連","この決定は、層構成を採らないという判断と対になる。","",
  fold("前後の決定を開く（4件）",
    tbl(["種類","対象"],[
      ("keyrow",["先立つ判断","ヘキサゴナル層構成を敷かない（advisor 2体の敵対的検証で合意）── "
        "<b>層を敷かないと決めたので、規律を別の形で持つ必要が生じた</b>"]),
      ("",["同時に決まったこと","静的検査器を1つ導入する（規約2の前提）"]),
      ("",["後続の判断","Waffle語彙をエンジンから追い出す（<code>convert()</code> の移動）── 天井が下がる形で効く"]),
      ("",["縛る対象","<code>.claude/skills/design-svg/svg_engine/</code> 配下の全モジュールと試験"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.2rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
"""
out=("<title>層は宣言して凍結し、段は型で繋ぎ、残りは落ちる試験で縛る</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-contract-tests.html").write_text(out,encoding="utf-8")
print("書いた",len(out))
