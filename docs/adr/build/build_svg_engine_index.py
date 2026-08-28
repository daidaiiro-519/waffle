"""svg_engine の索引 ── 描く手そのものについての決定と実測を、別立てで並べる。

本体の索引（build_artifact_index.py）は「別の作業の記録は載せない ── それぞれ
独立した索引を持つ」と宣言している。svg_engine は design-svg Skill の事業領域で、
Waffle は利用側なので、この索引を独立させる。

題と状態は各頁から読む。手で写さない。
"""
import re, sys, pathlib
S = "/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0, S)
from _common import CSS, sec, fold, tbl, extra

ADR = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr")
A = "https://claude.ai/code/artifact/"

# 群 → [(ファイル名, 成果物ID, 種別, 状態の上書き)]
GROUPS = [
 ("01", "描いたものを、どう確かめるか",
  "<b>崩れを見つける手立て。</b>ここが弱いと、ほかの決定が正しく効いているかを測れない。",
  [("adr-svg-engine-testing.html", "346d2397-11a3-4b94-83b3-6339391a6418", "決定", None)]),

 ("02", "何が場所を占め、辺はどこへ着くか",
  "<b>置いたものどうしの関係。</b>占有領域と接続点は、同じ「実際に描いたもの」から決まる。",
  [("adr-occupancy.html",          "3eaab855-5edf-4c24-bac5-795a01d47e8a", "決定", None),
   ("concave-attachment.html",     "acbc62ab-1046-4360-b162-f43db02fe444", "決定", None)]),

 ("03", "台帳の中身をどう分けるか",
  "<b>部品と図の契約。</b>図が部品のふりをすると、節点として置いたときに壊れる。",
  [("adr-part-and-figure.html",    "7c490796-4276-4bc3-aa66-e8185e466481", "決定", None)]),

 ("04", "実測",
  "<b>決定の裏づけ。</b>決定の側から辿れるが、数字そのものを見たいときはここから。",
  [("part-placement-matrix.html",  "8069bf12-c76a-45d9-8b8d-f79e7b8f46a9", "実測", "—")]),
]

# 実装の現在地。頁から読めないので、ここに置く（数字は測って書き換える）
STATE = [
 ("辺の着き先", "描いたインクのうち、狙った側にいちばん近い点。輪郭という中間物を持たない"),
 ("部品が申告すること", "大きさと、置く前に描くか置いた後に描くか（<code>placement</code>）と、名前を自分で描いたか。"
  "<b>輪郭は申告しない。</b>申告した大きさはインクを含む（詰まっていることは課さない）"),
 ("段の間隔", "その間を通る辺の札が収まる幅から導く。札には逃げ場がある"),
 ("名前を描くのは誰か", "部品が申告する。描いたなら包む側は描かない"),
 ("文字の欄の幅", "中身から決める1つの関数（<code>text.column_width</code>）。固定トークンは持たない"),
 ("半角文字の幅の比", "0.65 ── Chromium で実測した最大。場所の取り置きなので平均でなく最大"),
 ("幾何検査", "<code>check</code>／<code>check_shapes</code>／<code>check_attachment</code> の3つ"),
 ("試験", "175本。うち検査自身を壊して鳴らす試験と、台帳の全部品を通す契約の試験を含む"),
 ("総当たり", "11種×2通り＝22通り、崩れ0件"),
 ("16の主張", "Waffle の宣言から16通りすべてを描ける。<b>宣言に書いた文字が1つ残らず絵に出る</b>ことまで機械で見る"
  " ── <a href=\"https://claude.ai/code/artifact/e104fa31-4eb7-47aa-b417-147c1b6f3e61\">対応表</a>"),
]

OPEN = [
 ("湾の凹んだ側の着き先", "承認済み（現状維持）",
  "インクに着く。見え方が問題になるか、湾を持つ形が2件目に出たら再検討"),
 ("群を指す辺", "宣言できない",
  "群に id が無い。「塊を指したい」図が出たら、群に id を足して名指しできるようにする"),
 ("生の数値", "44箇所",
  "多くは SVG の書式（コマンドの引数の数）と多項式の係数。可変にすべきものは潰した"),
]


def read(name):
    """頁から、題と一文と状態を取る。"""
    s = (ADR / name).read_text(encoding="utf-8")
    h1 = re.search(r"<h1>(.*?)</h1>", s, re.S)
    main = re.search(r'<p class="main">(.*?)</p>', s, re.S)
    if main is None:
        main = re.search(r'<p class="lede">(.*?)</p>', s, re.S)
    st = re.search(r'<span class="k">状態</span><span class="v">([^<]*)</span>', s)
    strip = lambda m: re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    return strip(h1), strip(main), (st.group(1) if st else "状態の節が無い")


def cut(t, n=110):
    return t if len(t) <= n else t[: n - 1] + "…"


body = ["".join([
 '<header><p class="eyebrow">索引 ── svg_engine</p>'
 '<h1>描く手についての決定と実測</h1>'
 '<p class="lede">svg_engine は <b>design-svg Skill の事業領域</b>で、Waffle は利用側。'
 'だから Waffle 本体の索引には載せず、ここへ分ける。'
 '<b>題と状態は各頁から読んでいる</b>ので、頁を直せばここも変わる。</p></header>'
])]

counts = {}
for num, title, lead, items in GROUPS:
    rows = []
    for name, aid, kind, override in items:
        h1, main, state = read(name)
        if override:
            state = override
        badge = f'<span class="kindtag {"unv" if state.startswith("承認済み") else "lim"}">{state}</span>'
        rows.append(("keyrow" if kind == "決定" else "",
                     [f'<b><a href="{A}{aid}">{h1}</a></b>' if kind == "決定"
                      else f'<a href="{A}{aid}">{h1}</a>',
                      kind, badge, cut(main)]))
        counts[kind] = counts.get(kind, 0) + 1
    body.append(sec(num, title, lead, tbl(["成果物", "種別", "状態", "何を決めたか"], rows)))

body.append(sec("05", "いまの実装",
  "<b>決定が実物へどう落ちているか。</b>決定を読まなくても、いまの姿だけ知りたいとき。",
  tbl(["何を", "どうなっているか"], [("", [k, v]) for k, v in STATE])))

body.append(sec("06", "開いたままのもの",
  "<b>閉じていない論点。</b>実装は変えていない。",
  tbl(["論点", "状態", "次に何があれば決まるか"], [("", list(r)) for r in OPEN]),
  fold("この索引の作り方",
    '<p class="foldnote">組み立ては <code>docs/adr/build/build_svg_engine_index.py</code>。'
    '<b>この頁を直接編集しない</b> ── 次に生成したときに消える。'
    '05 と 06 だけは頁から読めないので、組み立て側に書いてある。</p>')))

extra2 = extra + """
a{color:var(--fact)}
a:hover{text-decoration:none}
/* 種別と状態の欄は折り返さない。行が少ないと最後の欄に幅を取られ、
   「決定」が縦に割れる（実測で確認した）。ただし4列の表だけに効かせる ──
   2列・3列の表では2列目が本文なので、折り返さないと右へはみ出す（実測） */
td:nth-child(2):nth-last-child(3),th:nth-child(2):nth-last-child(3),
td:nth-child(3):nth-last-child(2),th:nth-child(3):nth-last-child(2){white-space:nowrap}
td:first-child:nth-last-child(4){min-width:11rem}
"""
out = ("<title>描く手についての決定と実測</title>"
       f'<style>{CSS}\n{extra2}</style><div class="wrap">{"".join(body)}</div>')
(ADR / "svg-engine-index.html").write_text(out, encoding="utf-8")
print("書いた", len(out), "／", counts)
