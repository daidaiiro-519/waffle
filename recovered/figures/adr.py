"""図の語彙のADR（関門1）。図は、決めようとしている記法そのもので描く。"""
import pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, str(pathlib.Path("../figs").resolve()))
from draw import render
from svg_graph import CSS as GCSS
from tokens import LOOK

CSS = pathlib.Path("../adr_css.txt").read_text(encoding="utf-8")

BEFORE_AFTER = {
  "asserts": "対応",
  "items": [
    {"name": "1つの名前が、6つの主張を担っている", "figure": {
        "asserts": "階層",
        "items": [{"name": "flowchart", "role": "muted", "children": [
            {"name": "条件による選択"}, {"name": "向きのある関係"},
            {"name": "区画への所属"}, {"name": "分類"}]}]}},
    {"name": "主張が名前になり、描き方は従属する", "figure": {
        "asserts": "階層",
        "items": [{"name": "何を主張するか", "role": "focus", "children": [
            {"name": "条件による選択"}, {"name": "向きのある関係"},
            {"name": "区画への所属"}, {"name": "分類"}]}]}}],
  "frame": {"axes": [{"unit": "変更前"}, {"unit": "変更後"}]}}

BODY = f'''<title>図の語彙を、描き方から主張へ移す</title>
<style>{CSS}{LOOK}{GCSS}
  .fignote{{font-size:.82rem;color:var(--ink-faint);margin:.4rem 0 0}}
  .f-fig{{display:block;max-width:100%;height:auto}}
</style>
<div class="wrap">

  <header>
    <p class="eyebrow">Any Decision Record — 関門1（仕様への橋渡し）</p>
    <h1>図の語彙を、描き方から主張へ移す</h1>
    <p class="lede">いま document に残るのは「どう描くか」だけです。その図が何を主張しているかを残すかどうかを決めます。</p>
  </header>

  <section>
    <h2><span class="num">01</span>決定<span class="blk">block 01</span></h2>
    <div class="fig"><p class="one">図の部品名を、描き方の名前から「何を主張するか」へ置き換える。書ける形は固定し、どの欄を書けるかは主張が決める。描き方は主張から従属して決まり、書き手は選ばない。</p></div>
    <p class="cap">主文だけでは読み方が定まらない箇所を、同時に確定させる。</p>
    <div class="gapwrap"><table>
      <thead><tr><th>確定させること</th><th>決定</th><th>定めないと</th></tr></thead>
      <tbody>
        <tr><td class="name">主張の一覧</td><td>関係7・量9の16。既に確立した枠組みから採る（量はFTの9分類、関係は図の分類の一般形）</td><td>自分で分類を作ることになり、置き換えたい語彙の痕跡から語彙を再生産する</td></tr>
        <tr><td class="name">書ける形</td><td>欄は3つ（置くもの・つなぐもの・読む枠）、書ける名前は18。主張ごとに形を変えない</td><td>主張の数だけ形が増え、記法ではなく品揃えになる</td></tr>
        <tr><td class="name">入れ子</td><td>置くものは、宣言そのものを中に持てる</td><td>面の中身が名前の文字列で止まり、変更前と変更後が書けない</td></tr>
        <tr><td class="name">描き分け</td><td>線と角度が意味を運ぶものはSVG、文字が主役のものはHTML。塗りと線は属性で持つ</td><td>図を取り出したとき色が消え、機械で確かめられない</td></tr>
        <tr><td class="name">Markdown</td><td>従来どおりMermaidへ変換して出す。変換は出力の境界でのみ行う</td><td>Mermaidをやめる決定と読まれる</td></tr>
      </tbody>
    </table></div>
  </section>

  <section>
    <h2><span class="num">02</span>理由<span class="blk">block 02</span></h2>
    <div class="fig"><p class="one">決め手は、その図が何を主張しているかが、どこにも記録されないこと。</p></div>
    <p class="cap">実際に描かれた180枚を数えると、<b>125枚が <code>flowchart</code> ひとつの下にあり、その中身は少なくとも6種類の違うこと</b>を言っていました。条件による選択が62、向きのある関係が30、区画への所属が21、順序と分類が13。<br>
    読み手は絵の形から主張を推測するしかありません。私が機械で分類したとき、無作為12枚のうち3枚を取り違えました。<b>私が外すということは、読み手も外すということです。</b><br>
    ほかの不利益は手当てで下げられます——名前を増やせば粒度は上がり、注釈を足せば読みは助かり、執筆ガイダンスを厚くすれば書き手は迷わない。しかしどれも<b>記録されるのは描き方のまま</b>で、主張は残りません。これだけが後から取り返せない。</p>
    <div class="gapwrap"><table>
      <thead><tr><th>不利益</th><th>手当てで下げられるか</th><th>決め手か</th></tr></thead>
      <tbody>
        <tr><td class="name">主張が記録されない</td><td>下げられない。名前を増やしても注釈を足しても、残るのは描き方</td><td class="yes">これ</td></tr>
        <tr><td class="name">1語が6つの意味を持つ</td><td>名前を増やせば下がる</td><td class="no">—</td></tr>
        <tr><td class="name">上流の構文名に従属している</td><td>名前を付け替えれば下がる</td><td class="no">—</td></tr>
        <tr><td class="name">書き手が描き方を選んでいる</td><td>ガイダンスで下がる</td><td class="no">—</td></tr>
      </tbody>
    </table></div>
  </section>

  <section>
    <h2><span class="num">03</span>変更前と変更後<span class="blk">block 03</span></h2>
    <p class="cap">document に何が残るかが変わる。</p>
    <figure>{render(BEFORE_AFTER)}
      <figcaption class="fignote">この図は、決めようとしている記法そのもので描いています（主張は「対応」、面の中身は「階層」の宣言）。</figcaption>
    </figure>
  </section>

  <section>
    <h2><span class="num">04</span>「決め手」を選んだ軸<span class="blk">block 04</span></h2>
    <p class="cap">不利益を、手当てで下げられるものと、下げられないものに分けました。読みにくい・粒度が粗い・書き手が迷うは、どれも程度です。名前を増やす、注釈を足す、ガイダンスを厚くする——いずれも効きます。<br>
    主張が記録されないことだけは程度ではありません。<b>後から遡って復元できない</b>ので、手当ての量に依存せず決着します。</p>
  </section>

  <section>
    <h2><span class="num">05</span>答えないこと<span class="blk">block 05</span></h2>
    <div class="gapwrap"><table>
      <thead><tr><th>問い</th><th>ここで答えない理由</th></tr></thead>
      <tbody>
        <tr><td class="name">16の主張それぞれの日本語表記</td><td>語そのものは仕様を書く段で確定する。ここで決めるのは「主張を名前にする」ことまで</td></tr>
        <tr><td class="name">既存125枚をいつ移すか</td><td>移行の段取りは引き継ぎの段で決める</td></tr>
        <tr><td class="name">文章の部品（表・箇条書き・節）を同じ枠で扱うか</td><td>図の語彙とは変更理由が違う。別の決定にする</td></tr>
        <tr><td class="name">ADRSchemaのブロック構成</td><td>この決定の後続。block 03 の器が書けることは確かめたので、順番はこちらが先</td></tr>
      </tbody>
    </table></div>
  </section>

  <section>
    <h2><span class="num">06</span>承認<span class="blk">block 06</span></h2>
    <div class="approve">
      <span class="k">状態</span>
      <span class="v">未承認</span>
      <span style="font-size:.9rem;color:var(--ink-soft)">18ある描画部品のうち、図に相当する5つを入れ替えるため、承認を待つ。</span>
    </div>
  </section>

  <section>
    <h2><span class="num">07</span>関連<span class="blk">block 07</span></h2>
    <div class="gapwrap"><table>
      <thead><tr><th>種類</th><th>対象</th></tr></thead>
      <tbody>
        <tr><td class="name">縛る仕様</td><td>schema の <code>x-render</code> 宣言／uc-render-document の受け入れ基準（部品名を列挙している）</td></tr>
        <tr><td class="name">影響する実装</td><td>part_renderer.py（417行・18部品）</td></tr>
        <tr><td class="name">影響する document</td><td>実際に図を持つもの。180枚（knowledge 130・specs 50）</td></tr>
        <tr><td class="name">実測の出所</td><td>成果物に実際に描かれた図の全数え上げ／16の主張と難しい実物4件を組んだ試作／図の検査21枚</td></tr>
        <tr><td class="name">先行する決定</td><td>関係は記号でなく言葉で表す／Mermaidは下限であって上限ではない／配る成果物は外部ホストを踏まない</td></tr>
        <tr><td class="name">後続の決定</td><td>ADRSchemaのブロック構成（関門1）</td></tr>
      </tbody>
    </table></div>
  </section>

</div>
'''

out = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-figure-vocabulary.html")
out.write_text(BODY, encoding="utf-8")
print("書いた", out.stat().st_size, "bytes")