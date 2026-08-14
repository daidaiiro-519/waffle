"""schema をどう変えるかのADR（関門1）。前の2つのADRの訂正を含む。"""
import pathlib, sys
sys.path.insert(0, "."); sys.path.insert(0, str(pathlib.Path("../figs").resolve()))
from draw import render
from svg_graph import CSS as GCSS
from tokens import LOOK
CSS = pathlib.Path("../adr_css.txt").read_text(encoding="utf-8")

SHAPE = {
  "asserts": "対応",
  "items": [
    {"name": "描き方の指定が、宣言と x-render の両方に散っている", "figure": {
        "asserts": "階層",
        "items": [{"name": "図の宣言", "children": [
            {"name": "intent", "role": "muted"}, {"name": "reading"},
            {"name": "direction", "role": "muted"}, {"name": "groups"},
            {"name": "nodes"}, {"name": "edges"}, {"name": "notes", "role": "muted"}]}]}},
    {"name": "主張が軸になり、欄は3つに畳まれる", "figure": {
        "asserts": "階層",
        "items": [{"name": "図の宣言", "children": [
            {"name": "asserts（主張）", "role": "focus"},
            {"name": "items（置くもの）"}, {"name": "links（つなぐもの）"},
            {"name": "frame（読む枠）"}]}]}}],
  "frame": {"axes": [{"unit": "変更前"}, {"unit": "変更後"}]}}

def sec(n, t, inner): return f'<section><h2><span class="num">{n}</span>{t}</h2>{inner}</section>'
def table(head, rows, cap=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f'<td class="name">{c}</td>' if i==0 else f"<td>{c}</td>"
        for i, c in enumerate(r)) + "</tr>" for r in rows)
    c = f'<p class="cap">{cap}</p>' if cap else ""
    return f'{c}<div class="gapwrap"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

O = "Orchestrator（実測）"
HTML = f'''<title>図の宣言の schema を、主張を軸にした形へ置き換える</title>
<style>{CSS}{LOOK}{GCSS}
  .f-fig{{display:block;max-width:100%;height:auto}}
  figure{{margin:0}} figure .f-cmp{{flex-direction:column;gap:1.8rem}}
  .fignote{{font-size:.8rem;color:var(--ink-faint);margin:.9rem 0 0}}
</style>
<div class="wrap">

  <header>
    <p class="eyebrow">Any Decision Record — 関門1（仕様への橋渡し）</p>
    <h1>図の宣言の schema を、主張を軸にした形へ置き換える</h1>
    <p class="lede">実物を測ったところ、前の2つのADRに事実の誤りが見つかりました。決定は覆りませんが、決め手の書き方と記法に訂正が要ります。あわせて schema がどう変わるかを示します。</p>
  </header>

  {sec("01", "決定",
    '<div class="fig"><p class="one">図の宣言の欄を、7つから「主張＋3欄」へ置き換える。'
    'x-render は描き方の指定をやめ、どのデータがどの欄に当たるかの対応づけだけを持つ。</p></div>'
    + table(["確定させること", "決定", "定めないと"], [
        ["<code>intent</code>（自由記述の主張）", "落とす。<code>asserts</code> が引き取る",
         "自由記述の主張が残り、語彙化した意味が消える"],
        ["<code>reading</code>（どう読むか）", "残す。<code>frame</code> の中へ置く（欄は3つのまま、名前が19へ）",
         "器の面にはある「読みの一言」が、単独の図でだけ消える"],
        ["<code>notes</code>（図に載せきれないこと）", "落とす。要素を名指しした注釈の表として、図の外に既に決まっている",
         "同じ役目が図の中と外に二重に生まれる"],
        ["<code>direction</code>", "落とす。向きは描き方の都合で、主張ではない",
         "描き方の指定が宣言に残り続ける"],
        ["x-render の21の指定キー", "対応づけ（<code>〜From</code>）だけを残し、描き方の指定（<code>direction</code>／<code>badge</code>／<code>ordered</code>／<code>heading</code> 等）は落とす",
         "部品名を主張へ変えても、描き方の指定が別の鍵として残る"],
      ], "主文だけでは読み方が定まらない箇所を、同時に確定させる。"))}

  {sec("02", "理由", table(["理由", "根拠", "どの決定の理由か", "主張"], [
      ["主張は既に記録されている。ただし語彙になっていない",
       "図の宣言79件<b>すべて</b>が <code>intent</code> を持つ。「事業領域が、複数の業務領域から成ることを示す」のような自由記述",
       "<code>intent</code> を落とす", O],
      ["主張と描き方が、別々に宣言され互いを縛っていない",
       "<code>intent</code> は document 側、描き方は schema の <code>x-render</code> 側。描画は <code>intent</code> を一切読まない",
       "主文（主張を軸にする）", O],
      ["描き方の指定が、宣言と x-render の両方に散っている",
       "宣言側に <code>direction</code>、x-render 側に <code>direction</code>／<code>badge</code>／<code>ordered</code>／<code>heading</code> ほか計21の指定キー",
       "<code>direction</code> と指定キーを落とす", O],
      ["読み手への一言は、器では既に持っている",
       "対比の器は面ごとに「読みの一言」を持つ。単独の図にだけ置き場所が無い",
       "<code>reading</code> を残す", O],
      ["図に載せきれないことは、図の外の器で決めてある",
       "要素を名指しした注釈の表として決定済み",
       "<code>notes</code> を落とす", O],
    ], "前の2つのADRの決め手を、この実測で言い直しています。"))}

  {sec("03", "変更前と変更後",
    '<p class="cap">図の宣言が持つ欄。薄いものは落とす。</p>'
    f'<figure>{render(SHAPE)}'
    '<figcaption class="fignote">この図は、前のADRで決めた記法で描いています。</figcaption></figure>')}

  {sec("04", "schema がどう変わるか", table(
    ["変える対象", "いま", "変更後"], [
      ["図の宣言（document の中身）",
       "7つの欄 — <code>intent</code> / <code>reading</code> / <code>direction</code> / <code>groups</code> / <code>nodes</code> / <code>edges</code> / <code>notes</code>",
       "主張＋3欄 — <code>asserts</code> / <code>items</code> / <code>links</code> / <code>frame</code>。<code>groups</code> は <code>items</code> の入れ子へ、<code>reading</code> は <code>frame</code> の中へ"],
      ["x-render の <code>as</code>",
       "描き方の名前（<code>flowchart</code> / <code>sequence</code> / <code>statediagram</code> / <code>architecture</code> / <code>graph</code>）",
       "主張の名前（16のうち1つ）"],
      ["x-render の指定キー",
       "21個。対応づけ（<code>nodesFrom</code> 等）と描き方の指定（<code>direction</code> / <code>badge</code> / <code>ordered</code> / <code>heading</code> 等）が混在",
       "対応づけのみ。描き方の指定は落とす"],
      ["欄の必須・禁止",
       "宣言なし",
       "主張ごとに <code>if</code>／<code>then</code> で表す。「階層に <code>links</code> は書けない」等"],
      ["版",
       "—",
       "RenderMetaSchema を上げる（<code>as</code> の値そのものが変わるため）。図の宣言を持つ schema も上げる（document の中身が変わるため）"],
    ], "どこが変わるかを、対象ごとに分けて示します。"))}

  {sec("05", "答えないこと", table(["論点", "状態"], [
      ["79件の <code>intent</code> を、どの主張へ写すか", "1件ずつ人が判断する。機械分類は誤り率が高い（12枚中3枚）"],
      ["<code>notes</code> の移し先の器の形", "別に決定済み。ここでは触らない"],
      ["文章の部品13種", "変更理由が違う。別論点"],
      ["実装をどの順で動かすか", "別のADR（置き場所）で扱う"],
    ]))}

  {sec("06", "承認",
    '<div class="approve"><span class="k">状態</span><span class="v">未承認</span>'
    '<span style="font-size:.9rem;color:var(--ink-soft)">'
    '前の2つのADRの決め手を言い直すため、承認を待つ。決定そのものは覆っていない。</span></div>')}

  {sec("07", "関連", table(["種類", "対象"], [
      ["言い直す決め手", "「主張がどこにも記録されない」→「<b>主張と描き方が別々に宣言され、対応していない</b>」"],
      ["記法への追加", "<code>frame.reading</code>。書ける名前が18から19へ。欄は3つのまま"],
      ["先行する決定", "図の語彙を、描き方から主張へ移す（承認済み）／図の宣言を Document の内側の値として置く（未承認）"],
      ["この決定が正した私の誤り",
       "既存の宣言を一度も見ずに「記録されない」と書いた／描画部品に死語4つという報告（実測は18種すべて実装あり）／document 側の移行は不要という報告（実測は79件）"],
    ]))}

</div>
'''
out = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-figure-schema.html")
out.write_text(HTML, encoding="utf-8")
print("書いた", out.stat().st_size, "bytes")