"""図の宣言の置き場所を決めるADR（関門1）。図は決めた記法そのもので描く。"""
import pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, str(pathlib.Path("../figs").resolve()))
from draw import render
from svg_graph import CSS as GCSS
from tokens import LOOK

CSS = pathlib.Path("../adr_css.txt").read_text(encoding="utf-8")

PLACE = {
  "asserts": "対応",
  "items": [
    {"name": "図の宣言を独立した集約として立てる", "figure": {
        "asserts": "階層",
        "items": [{"name": "区切られた文脈", "children": [
            {"name": "Document の集約"},
            {"name": "schema の集約"},
            {"name": "図の宣言の集約", "role": "muted"}]}]}},
    {"name": "Document の内側の値として置く", "figure": {
        "asserts": "階層",
        "items": [{"name": "Document の集約", "children": [
            {"name": "図の宣言", "role": "focus", "children": [
                {"name": "主張"}, {"name": "置くもの"},
                {"name": "つなぐもの"}, {"name": "読む枠"}]}]}]}}],
  "frame": {"axes": [{"unit": "私が想定していた形"}, {"unit": "決定"}]}}

def sec(num, title, inner):
    return f'<section><h2><span class="num">{num}</span>{title}</h2>{inner}</section>'

def table(head, rows, cap=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(
        f'<td class="name">{c}</td>' if i == 0 else f"<td>{c}</td>"
        for i, c in enumerate(r)) + "</tr>" for r in rows)
    c = f'<p class="cap">{cap}</p>' if cap else ""
    return f'{c}<div class="gapwrap"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

D = "ddd-advisor"; T = "tech-lead-advisor"; O = "Orchestrator（実測）"

HTML = f'''<title>図の宣言を、Document の内側の値として置く</title>
<style>{CSS}{LOOK}{GCSS}
  .f-fig{{display:block;max-width:100%;height:auto}}
  figure{{margin:0}}
  figure .f-cmp{{flex-direction:column;gap:1.8rem}}
  .fignote{{font-size:.8rem;color:var(--ink-faint);margin:.9rem 0 0}}
</style>
<div class="wrap">

  <header>
    <p class="eyebrow">Any Decision Record — 関門1（仕様への橋渡し）</p>
    <h1>図の宣言を、Document の内側の値として置く</h1>
    <p class="lede">承認済みのADR「図の語彙を、描き方から主張へ移す」を仕様に落とすにあたり、この記法をどのDDD要素として、どこに置くかを決めます。前のADRは覆っていません。</p>
  </header>

  {sec("01", "決定",
    '<div class="fig"><p class="one">図の宣言は、Document の集約の内側にある再帰する値オブジェクトとして置く。'
    '16の主張はその属性であり、種別ではない。欄の必須・禁止を守るのは schema ひとつとする。</p></div>'
    + table(["確定させること", "決定", "定めないと"], [
        ["守り手", "schema ひとつ。不変条件には「常に主張が定める組と一致する」の1行だけを書き、守り手を名指しする",
         "16主張×3欄の対応表が不変条件にも写り、正本が2箇所になる"],
        ["主張の表し方", "属性。1つの形＋主張をキーにした制約プロファイル",
         "16個の形に分かれ、置くものの定義が16回複製されて同期の義務が残る"],
        ["新設する文書", "2件だけ。16語と出典を置く knowledge と、宣言の形を検査するユースケース",
         "実装だけあって仕様が無い検査（現に1件ある）が増える"],
        ["実装を動かす順", "語彙が先。描画の実装を層の外へ移すのは最後",
         "2つ目の描画先が無いまま口の形を決め、1つの実装の都合を写す"],
        ["ADRの射程", "中核のモデルに置くのは「主張が欄を決める」まで。「主張が描き方を決める」は外",
         "描き方という技術の都合が、業務の言葉のモデルに混ざる"],
      ], "主文だけでは読み方が定まらない箇所を、同時に確定させる。"))}

  {sec("02", "理由", table(["理由", "根拠", "主張"], [
      ["図の宣言は一貫性の境界にならない",
       "図の宣言だけを Document と別のトランザクションで確定させる場面が無い。集約は「1つのインスタンスが1つのトランザクションの単位」", D],
      ["識別子で指せないものは集約ではない",
       "集約どうしは識別子で参照し合う。図の宣言は documentId のように外から名指しできない", D],
      ["16は種別の条件を満たさない",
       "種別が問うのは<b>ブロック集合が入れ替わるか</b>で、必須・任意の割り当ての差ではない。ここで変わるのは後者だけ", D],
      ["schema が守る規則も不変条件として宣言する形が既にある",
       "<code>agg-schema</code> の不変条件9件のうち<b>8件が守り手 schema</b>。ここだけ例外にすると「不変条件」が2つの意味を持つ（実測で確認）", f"{D} / {O}"],
      ["移行の対象は document ではない",
       "部品名は schema の <code>x-render</code> にしか無く、document は data しか持たない。値として持つ document は<b>6枚</b>。180枚は再描画して差分ゼロを確かめる対象", T],
      ["2つ目の描画先が repo に無い",
       "自前SVGの描画器は作業場（<code>/tmp</code>）にあり git 管理外。口を1実装から決めることになる", T],
    ]))}

  {sec("03", "変更前と変更後",
    '<p class="cap">図の宣言が、どこに住むか。</p>'
    f'<figure>{render(PLACE)}'
    '<figcaption class="fignote">この図は、前のADRで決めた記法で描いています'
    '（外側の主張は「対応」、面の中身は「階層」の宣言）。</figcaption></figure>')}

  {sec("04", "「置き場所」を分けた軸", table(
    ["満たしたい条件", "独立した集約", "Document の内側の値"], [
      ["1つのトランザクションの単位になる", "✗ ならない", "○ Document の保存に収まる"],
      ["外から識別子で指せる", "✗ 指せない", "○ 指す必要が無い"],
      ["規則が値の内側に集まる", "✗ 外へ散る", "○ 集まる"],
      ["将来ひとりで版管理される要求に応えられる", "○ 応えられる", "✗ そのとき集約へ移す"],
    ], "左の列は満たしたい条件で、満たすものに ○、満たさないものに ✗ を付けた。"))}

  {sec("05", "答えないこと", table(["論点", "状態"], [
      ["入れ子の深さの上限", "実測では現行の最大は1段。上限2が提案されている。数の確定は schema の版を切る側"],
      ["<code>direction</code> を消したとき、向きを指定していた箇所をどう扱うか", "79箇所のうち縦を指定していた件数を数えてから決める"],
      ["文章の部品13種を同じ仕様に混ぜるか", "変更理由が違うので分ける。ただし宣言の形の検査は18名全体にかかる"],
      ["層の宣言に1行足すか", "「外へ出す形式を組み立てる処理は adapter に置く」。実装を動かす前に決める"],
    ]))}

  {sec("06", "承認",
    '<div class="approve"><span class="k">状態</span><span class="v">未承認</span>'
    '<span style="font-size:.9rem;color:var(--ink-soft)">'
    '前のADRは覆っていない。置き場所と順番だけを決めるため、承認を待つ。</span></div>')}

  {sec("07", "関連", table(["種類", "対象"], [
      ["新設する文書", "16語と出典を置く knowledge ／ 宣言の形を検査するユースケース"],
      ["変更する文書", "<code>agg-document</code>（値と不変条件）／<code>bc-waffle</code>（同じ言葉・シナリオ名10件）／<code>uc-render-document</code>（部品名の列挙）／層の宣言"],
      ["変更不要と判定したもの", "<code>agg-schema</code>（既存の2つの不変条件が文言のまま新しい語彙を射程に収める）／<code>uc-validate-document</code>"],
      ["先行する決定", "図の語彙を、描き方から主張へ移す（承認済み）"],
      ["この決定が正した私の誤り", "180枚が移行対象という理解／描画部品に死語4つがあるという報告（実測は18種すべて実装あり）／数え漏らす測定"],
    ]))}

</div>
'''
out = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-figure-placement.html")
out.write_text(HTML, encoding="utf-8")
print("書いた", out.stat().st_size, "bytes")