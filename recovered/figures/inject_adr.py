"""生成済みのHTMLへ、ADRの2部品とカバレッジの節を差し込む。

図の断片には波括弧が入るので、組み立て時のf-stringには載せない。
"""
import json, pathlib, sys
S = pathlib.Path(__file__).parent
sys.path.insert(0, str(S))
from adr_css import ADR_CSS

target = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/figure-parts-preview.html")
html = target.read_text(encoding="utf-8")
adr = json.loads((S / "adr_fragments.json").read_text(encoding="utf-8"))

html = html.replace("</style>", ADR_CSS + "</style>", 1)

NEW = """
<section id="proposed">
  <h2><span class="num">02</span>ADRで使った図（部品にするとどうなるか）</h2>
  <p class="col">下の2枚は<b>まだ実装されていない部品</b>の提案です。上の5つと違い、Mermaidを経由せずHTMLを直接組み立てます。図そのものは、この節のために描いたのではなく、<b>提案した構造化データを部品に通して出したHTML</b>をそのまま置いています。</p>

  <div class="part" id="p-comparison">
    <div class="head"><h3>comparison</h3><span class="verdict rename">提案・未実装</span></div>
    <p class="col"><b>変更前と変更後の対比</b> ── 面を2つ並べ、囲みで塊を示し、面をまたぐ対応を線で結ぶ。</p>
""" + adr["comparison"] + """
    <p class="col">データにあるのは <code>at</code>（変更前か後か）と <code>role</code>（注目・移動）だけで、<b>色は一つも書かれていません</b>。橙と青緑は <code>at</code> から、強調は <code>role</code> から導かれます。線もデータには無く、親子関係から部品が置いています。</p>
  </div>

  <div class="part" id="p-session">
    <div class="head"><h3>session</h3><span class="verdict rename">提案・未実装</span></div>
    <p class="col"><b>操作と、返ってきたものの対比</b> ── 同じ操作を変更前後で並べ、行を種類ごとに描き分ける。</p>
""" + adr["session"] + """
    <p class="col">行は <code>comment</code> / <code>command</code> / <code>output</code> / <code>note</code> の4種だけです。<b>座標もレイアウトの計算もありません</b>——縦に並べるだけなので、図の配置を解く必要がありません。</p>
  </div>
</section>

<section id="coverage">
  <h2><span class="num">03</span>Markdownで描ける図のうち、部品になっているもの</h2>
  <p class="col">同梱の mermaid-guide が扱う構文は <b>17種</b>。うち部品があるのは <b>4種</b>です。残りは部品を通らず、書きたければ原文としてそのまま埋め込むしかありません。</p>
  <div class="scroll">
    <table>
      <caption>表2 ── 構文の被覆と、Waffleの文書で要りそうかの見立て</caption>
      <thead><tr><th>構文</th><th>何を示す</th><th>部品</th><th>見立て</th></tr></thead>
      <tbody>
        <tr><td><code>sequence</code></td><td>やり取りの順序</td><td>有</td><td>—</td></tr>
        <tr><td><code>flowchart</code></td><td>工程の並びと分岐</td><td>有（2つ）</td><td>向きが選べない</td></tr>
        <tr><td><code>state</code></td><td>状態と遷移</td><td>有</td><td>—</td></tr>
        <tr><td><code>architecture</code></td><td>区画と部品</td><td>有</td><td>中身を要検討</td></tr>
        <tr><td><code>quadrant</code></td><td>2軸での位置づけ</td><td><b>無</b></td><td><b>既に使用中。</b>subdomainの分類が原文で埋まっている</td></tr>
        <tr><td><code>mindmap</code></td><td>概念の木</td><td><b>無</b></td><td>knowledgeのnodesがまさに木</td></tr>
        <tr><td><code>class</code></td><td>型と関連</td><td><b>無</b></td><td>ドメイン仕様で要りそう</td></tr>
        <tr><td><code>er</code></td><td>実体と関連</td><td><b>無</b></td><td>同上</td></tr>
        <tr><td><code>timeline</code></td><td>時間順の出来事</td><td><b>無</b></td><td>決定の経緯・版の推移</td></tr>
        <tr><td><code>block</code></td><td>汎用の箱組み</td><td><b>無</b></td><td>他で代替できる場面が多い</td></tr>
        <tr><td><code>requirement</code></td><td>要求と充足</td><td><b>無</b></td><td>用途が薄い</td></tr>
        <tr><td><code>pie</code> <code>xychart</code> <code>sankey</code></td><td>量と比率</td><td><b>無</b></td><td>Waffleの文書に量はあまり出ない</td></tr>
        <tr><td><code>gantt</code> <code>git</code> <code>journey</code></td><td>日程・履歴・体験</td><td><b>無</b></td><td>用途が薄い</td></tr>
      </tbody>
    </table>
  </div>
  <div class="callout alarm">
    <span class="k">被覆より先に効く問題</span>
    <p>部品が無い図は、<b>原文の塊として書けてしまいます</b>。実際 subdomain の分類図は <code>quadrant</code> の原文として埋まっています。書けてしまう限り、構造化されず、検証もされず、HTML側へも展開できません。</p>
    <p>つまり<b>「何種類そろえるか」より「原文の逃げ道を閉じるか」の方が先に効きます</b>。閉じると決めれば、実際に使う構文は全部そろえる必要が出てきます。</p>
  </div>
</section>

"""
html = html.replace('<section id="caveat">', NEW + '<section id="caveat">', 1)
html = html.replace('<span class="num">02</span>気づいたこと', '<span class="num">04</span>気づいたこと', 1)
target.write_text(html, encoding="utf-8")
print("差し込み完了", len(html), "bytes")