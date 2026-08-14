"""advisor2名の検証結果を、判断材料としてまとめる。"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from figures import render          # noqa: E402
from styles import CSS              # noqa: E402

PORT_FIG = {
 "kind": "comparison",
 "sides": [
  {"at": "before", "label": "私の案", "note": "描く道具の形が、そのまま口の形になっていた",
   "groups": [
    {"label": "口を通るもの", "contentKind": "listing", "content": {"items": [
      {"name": "段（何段目）", "role": "removed"},
      {"name": "段内の位置（何番目）", "role": "removed"},
      {"name": "class付きのSVG", "role": "removed"},
    ]}}]},
  {"at": "after", "label": "検証後", "note": "口は座標だけ。見た目の語彙はこちらが決める",
   "groups": [
    {"label": "口を通るもの", "contentKind": "listing", "content": {"items": [
      {"name": "各点の矩形（x, y, 幅, 高さ）", "role": "added"},
      {"name": "各線の経路（点の並び）", "role": "added"},
      {"name": "SVG・DOT・ライブラリの型・例外", "role": "removed"},
      {"name": "CSSのクラス名・色・線の太さ", "role": "removed"},
    ]}}]}]}

DEFECTS = [
 ("段が逆転する", "座標", "解く", "口の欠陥。輪がある時に段の計算が壊れていた"),
 ("辺のラベルが重なる", "座標", "半分", "配置の問題だが、置き場所の判断はこちら側にも残る"),
 ("矢印の先端が無い", "描画", "解かない", "そもそも描いていなかった"),
 ("線が先端を突き抜ける", "描画", "解かない", "線と三角を重ねていた"),
 ("囲みが線に潰れる", "描画", "解かない", "CSSの継承（align-items）"),
 ("帯が縮む", "描画", "解かない", "CSSの誤解（flex:1）"),
 ("縦書きの軸が上下逆", "描画", "解かない", "CSSの誤用（rotate）"),
 ("対比が縦に折り返す", "描画", "解かない", "CSSの設定"),
]


def build():
    rows = "".join(
        f'<tr><td>{name}</td><td class="n">{kind}</td>'
        f'<td class="mark {"yes" if solve == "解く" else ("half" if solve == "半分" else "no")}">'
        f'{solve}</td><td>{why}</td></tr>' for name, kind, solve, why in DEFECTS)

    body = f"""<title>図の描画をどう作り直すか</title><style>{CSS}{PAGE}</style>
<main>

<header>
  <p class="eyebrow">検証結果 — ddd-advisor / tech-lead-advisor</p>
  <h1>図の描画をどう作り直すか</h1>
  <p class="lede">2名のadvisorへ独立に投げた検証が揃った。私の案は2箇所で否定され、1箇所で前提そのものを問われている。決めるべきことは2つに絞れる。</p>
  <div class="stats">
    <div class="stat"><b>2</b><span>否定された設計</span></div>
    <div class="stat alarm"><b>1/8</b><span>Graphvizが解く崩れ</span></div>
    <div class="stat"><b>2</b><span>決めていただきたいこと</span></div>
  </div>
</header>

<section id="agree">
  <h2><span class="num">01</span>両者が、別の経路で同じ結論に着いた</h2>
  <div class="scroll"><table>
    <caption>表1 ── 独立に投げた2名が、同じ危険を指摘した</caption>
    <thead><tr><th>advisor</th><th>何と言ったか</th></tr></thead>
    <tbody>
      <tr><td>ddd</td><td>Graphvizは<b>新しい上流</b>。<code>rankdir</code> <code>cluster</code> <code>dot</code> といった語が語彙へ現れないことを、移行時の明示的な確認項目にせよ</td></tr>
      <tr><td>tech-lead</td><td>SVG文字列・DOT・ライブラリのオブジェクト・例外型を<b>ポートに通すな</b></td></tr>
    </tbody>
  </table></div>
  <div class="callout alarm">
    <span class="k">なぜ同じ結論になったか</span>
    <p>いま <code>graph</code> <code>architecture</code> <code>statediagram</code> という語彙になっているのは、<b>Mermaidという上流の構文名をそのまま採ったから</b>です。dddはこれを「<b>中核の業務領域で『従属する』を選んだ状態</b>」と判定しました。従属が正当なのは2条件だけで、どちらも成立していません。</p>
    <p>そして<b>上流を Graphviz に替えても、構造は同じ</b>です。両者はそこを別々の言葉で指しています。</p>
  </div>
</section>

<section id="denied">
  <h2><span class="num">02</span>私の案が否定された</h2>
  <p class="col">「Graphvizから class 付きのSVGを受け取り、CSSを当てる」という案でした。今日それが動くことを実測して喜んだのですが、<b>喜んだ点そのものが侵入経路</b>でした。</p>
  <div class="callout alarm">
    <span class="k">tech-lead の指摘</span>
    <p>アダプター側でポートを定義することになり、コアがGraphvizの出力形式に縛られる。そして<b>Graphvizが付けるクラス名（<code>node</code> <code>edge</code>）が、そのままWaffleのCSS設計の語彙になる</b>。</p>
  </div>
  {render(PORT_FIG)}
  <div class="scroll"><table>
    <caption>表2 ── もう1つの否定：整数だけの口も不適切だった</caption>
    <thead><tr><th>　</th><th>理由</th></tr></thead>
    <tbody>
      <tr><td>実装できない</td><td>「段と段内の位置」は段組み配置を前提にした形。<b>自由座標を返すGraphvizが実装できない</b></td></tr>
      <tr><td>欠陥を表現できない</td><td>実測で出た「輪がある時に段が逆転」は、<b>段indexという表現では正しい状態を表現すること自体ができない</b>。ポートの形が原因側にあった</td></tr>
    </tbody>
  </table></div>
</section>

<section id="spike">
  <h2><span class="num">03</span>Graphvizは何を解くのか</h2>
  <p class="col">tech-lead から最も重い指摘が来ました。<b>「Graphvizが解くのは座標。矢印の先端も線の終端も、SVGを生成する側の責務であり、座標を解かせても消えない」</b>。安いスパイクで測ってから決めよ、と。</p>
  <div class="callout">
    <span class="k">そのスパイクは、実は既に済んでいました</span>
    <p>今日この会話の中で、8件すべてを<b>Graphvizを使わずに直しています</b>。以下はその内訳です。</p>
  </div>
  <div class="scroll"><table>
    <caption>表3 ── 実測した崩れ8件と、Graphvizが解くかどうか</caption>
    <thead><tr><th>崩れ</th><th>種類</th><th>Graphvizが</th><th>実際の原因</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <div class="callout alarm">
    <span class="k">結論</span>
    <p><b>8件のうち、Graphvizが確実に解くのは1件だけ</b>でした。そして<b>その1件も、口の形を直すこと（表2の2行目）で捉えられます</b>。残り6〜7件は私の描画の細部で、座標を誰が解くかとは無関係でした。</p>
    <p>つまり<b>「Graphvizに寄せれば線の問題が片付く」という私の見立ては、根拠が薄かった</b>ということです。</p>
  </div>
</section>

<section id="unknown">
  <h2><span class="num">04</span>ただし、本当の争点は未測定です</h2>
  <div class="callout alarm">
    <span class="k">8件を直したあとの評価</span>
    <p>「ツリーが微妙に崩れてる箇所がおおい」「Mermaidで描画した時よりも見にくいものがかなり多い」「完全な再現には程遠い」</p>
  </div>
  <p class="col">これは8件を直した<b>あと</b>の評価です。つまり<b>まだ数えていない差が残っています</b>。件数も、原因も、それがGraphvizで解けるものかどうかも、測っていません。</p>
  <p class="col">Graphvizの採否を決めるなら、<b>ここを数えるのが本当のスパイク</b>です。表3は「既に直した8件」の内訳であって、「残っている差」の内訳ではありません。</p>
</section>

<section id="decide">
  <h2><span class="num">05</span>決めていただきたいこと</h2>
  <div class="scroll"><table>
    <caption>表4 ── 私一人では決められないもの</caption>
    <thead><tr><th>　</th><th>何を</th><th>なぜあなたが要るか</th></tr></thead>
    <tbody>
      <tr><td class="n">1</td><td><b>語彙の帰納に付き合っていただけるか</b></td><td>ddd曰く「Waffleの業務エキスパートは文書を書く人だが、実際はほぼ設計者本人＝技術者。技術者が自問して決めた語彙は、技術用語が混ざったことに気づけない」。<code>graph</code> がそのまま語彙になったのは不注意ではなく<b>この構造の産物</b>。対策は<b>語を伏せて既存の図を見せ、何を言いたかったかを答えてもらう</b>こと</td></tr>
      <tr><td class="n">2</td><td><b>残っている品質差を先に数えるか</b></td><td>表3で「Graphvizは1件しか解かない」と出た以上、採否の根拠は<b>未測定の残りの中</b>にしかない。数えずに採ると、C拡張への依存を根拠なく背負う</td></tr>
    </tbody>
  </table></div>
</section>

<section id="proceed">
  <h2><span class="num">06</span>採否に依存せず進められること</h2>
  <p class="col">両者とも「ポートの整備はGraphvizの採否に依存しない」と述べています。以下は先に済ませられます。</p>
  <div class="scroll"><table>
    <caption>表5 ── 先に進める4つ</caption>
    <thead><tr><th>　</th><th>やること</th><th>根拠</th></tr></thead>
    <tbody>
      <tr><td class="n">1</td><td><b>中間表現をドメイン層に立てる。</b>ただし図の部品だけ。テキストは現行のまま</td><td>いまの部品は「Markdownを出す」と自ら宣言しており、出す先を知っている。全部品を一度に移すのは費用が先行する（tech-lead 反対4）</td></tr>
      <tr><td class="n">2</td><td><b><code>LayoutSolver</code> ポートを定義。</b>矩形と経路だけを通す</td><td>外部技術を知る唯一の箇所。ここ以外にポートは要らない</td></tr>
      <tr><td class="n">3</td><td>既存の座標計算を <code>adapters/outbound/</code> へ移す。ただし<b>「宣言されていない関係をどう補うか」の規則はドメイン知識なので引き上げる</b></td><td>あの規則は座標計算ではなく業務ルール。委譲すると静かに失われる</td></tr>
      <tr><td class="n">4</td><td><b>契約テストを先に書き、既存実装に流す。</b>「輪で段が逆転」がここで赤くなることを確認する</td><td>座標の一致ではなく性質を検証する。偽実装と本物へ同じスイートを流せる形にする</td></tr>
    </tbody>
  </table></div>
  <p class="col"><b>4まで済ませると、Graphvizの採否を後ろへ倒せます。</b></p>
</section>

<section id="watch">
  <h2><span class="num">07</span>見過ごしてはいけない点</h2>
  <div class="scroll"><table>
    <caption>表6 ── 両者が「これを落とすな」と挙げたもの</caption>
    <thead><tr><th>出どころ</th><th>内容</th></tr></thead>
    <tbody>
      <tr><td>ddd</td><td><b>語彙側を先に確定させ、schemaの宣言を直してから実装を追随させる。</b>実装だけ先に直すと、宣言と実装が別々に漂流する。<code>graph</code> と <code>flowchart TB</code> の食い違いが、その漂流が既に起きた実例</td></tr>
      <tr><td>ddd</td><td><b>x-prompt に「HTMLの場合は」という分岐が現れたら、語彙が出力に汚染されている。</b>最も早く現れ、最も安く見つかる兆候。常設の検査にできる</td></tr>
      <tr><td>ddd</td><td><b><code>figure</code> も今回の再定義に含める。</b>除外すると、無内容な語が1つ残り、そこへすべての例外が流れ込む</td></tr>
      <tr><td>ddd</td><td>旧語と新語の並存には<b>期限を付ける</b>。期限の無い並存は、版の提供ではなく同義語の放置</td></tr>
      <tr><td>tech-lead</td><td>網羅性の検査（MDでできることはHTMLでも）は、<b>部品の一覧をschemaから読み出して</b>組む。テスト側にハードコードすると新種の追加を検知できない</td></tr>
      <tr><td>tech-lead</td><td><b>「systemインストール不要」を私は確認していない。</b>候補が1つしか挙がっていない現状は、技術選定の基準を満たしていない</td></tr>
      <tr><td>tech-lead</td><td>571行の独立経路のうち<b>図はごく一部で、大半はページの骨格</b>。図を畳むこととページを畳むことは別作業</td></tr>
    </tbody>
  </table></div>
  <div class="callout">
    <span class="k">最後の1点について</span>
    <p>私はPyPIのファイル一覧で3OS分のウィールが配布されていることを確認しましたが、<b>実際にクリーンな環境で入るかは試していません</b>。tech-leadの指摘どおり、確認していないことを確認済みとして扱っていました。</p>
  </div>
</section>

<footer>
  <p>ddd-advisor / tech-lead-advisor へ、それぞれ独立した検証として並列に投げた結果を統合したもの。両者とも、参照したknowledgeファイルを判断ごとに明示している。</p>
  <p>図はこの検証のために作った描画部品で組んでいる（対比の器＋一覧の中身）。SVGは使っていない。</p>
</footer>

</main>"""
    out = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/render-redesign-verification.html")
    out.write_text(body, encoding="utf-8")
    print("書いた", out.stat().st_size, "bytes")


PAGE = """
  *{box-sizing:border-box;}
  body{margin:0;padding:clamp(2rem,5vw,4rem) clamp(1rem,4vw,2rem) 6rem;
       background:var(--paper);color:var(--ink);font-family:var(--sans);
       font-size:16px;line-height:1.85;}
  main{max-width:62rem;margin:0 auto;display:flex;flex-direction:column;gap:3.2rem;}
  header{display:flex;flex-direction:column;gap:.9rem;}
  .eyebrow{font-family:var(--mono);font-size:.7rem;letter-spacing:.16em;
           text-transform:uppercase;color:var(--ink-faint);}
  h1{font-size:clamp(1.7rem,4vw,2.4rem);line-height:1.35;font-weight:600;margin:0;text-wrap:balance;}
  .lede{color:var(--ink-soft);font-size:1.02rem;margin:0;max-width:38rem;}
  p{margin:0;} .col{max-width:44rem;}
  .stats{display:flex;flex-wrap:wrap;gap:2.2rem;margin-top:.5rem;padding-top:1.1rem;
         border-top:1px solid var(--rule);}
  .stat{display:flex;flex-direction:column;}
  .stat b{font-family:var(--mono);font-size:1.5rem;font-weight:600;line-height:1.2;}
  .stat span{font-size:.78rem;color:var(--ink-faint);}
  .stat.alarm b{color:var(--warn);}
  section{display:flex;flex-direction:column;gap:1.3rem;}
  h2{font-size:1.35rem;font-weight:600;margin:0;padding-bottom:.6rem;
     border-bottom:1px solid var(--rule);display:flex;align-items:baseline;gap:.8rem;}
  h2 .num{font-family:var(--mono);font-size:.72rem;color:var(--ink-faint);letter-spacing:.1em;flex:none;}
  .callout{border-left:3px solid var(--acc);background:var(--surface);padding:1.1rem 1.3rem;
           border-radius:0 10px 10px 0;display:flex;flex-direction:column;gap:.55rem;}
  .callout.alarm{border-left-color:var(--warn);background:var(--warn-bg);}
  .callout .k{font-family:var(--mono);font-size:.66rem;letter-spacing:.12em;
              text-transform:uppercase;color:var(--ink-faint);}
  .callout p{max-width:46rem;}
  .scroll{overflow-x:auto;}
  table{border-collapse:collapse;width:100%;font-size:.87rem;min-width:34rem;}
  caption{text-align:left;font-size:.8rem;color:var(--ink-faint);padding-bottom:.5rem;}
  th,td{text-align:left;vertical-align:top;padding:.62rem .8rem;
        border-bottom:1px solid var(--rule-soft);line-height:1.65;}
  thead th{font-size:.72rem;letter-spacing:.06em;color:var(--ink-faint);
           font-weight:600;border-bottom:1px solid var(--rule);white-space:nowrap;}
  tbody tr:last-child td{border-bottom:none;}
  td.n{font-family:var(--mono);white-space:nowrap;}
  td.mark{font-weight:600;white-space:nowrap;}
  td.mark.yes{color:var(--acc);} td.mark.no{color:var(--ink-faint);} td.mark.half{color:var(--warn);}
  code{font-family:var(--mono);font-size:.86em;background:var(--surface-2);
       padding:.1em .38em;border-radius:4px;}
  footer{border-top:1px solid var(--rule);padding-top:1.3rem;font-size:.82rem;
         color:var(--ink-faint);display:flex;flex-direction:column;gap:.5rem;}
"""

if __name__ == "__main__":
    build()
