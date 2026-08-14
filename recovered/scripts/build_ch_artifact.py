"""19本目（最後）のアーティファクトを組み立てる。全19本の締めも兼ねる。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "closing-heuristics の変換 ── 19本目（完了）")
frag = pathlib.Path(f"{S}/ch_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 19本目 ── 完了</span>
  <h1><code>closing-heuristics</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版110行 → <strong>299行</strong>。最後の1本です。この本は<strong>実際の失敗の記録</strong>で、5つの区切られた文脈それぞれに別の教訓があります。<strong>これで19本すべての変換が終わりました。</strong></p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">25</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">3</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">6</span><span class="l">原文（表5・C#1）</span></div>
    <div class="stat"><span class="n">299</span><span class="l">行（旧110 / 書起し298）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 事例が5つとも落ちていました</h2>
  <p class="narrow">旧版に残っていたのは判定の流れと3つの判断基準だけ。<strong>付録の事例研究が丸ごとありません。</strong>この本の価値は「何が正しいか」ではなく「何をやってどう失敗したか」なので、これが落ちると本の半分が消えます。</p>

  <div class="tablewrap">
    <table>
      <thead><tr><th>文脈</th><th>教訓</th></tr></thead>
      <tbody>
        <tr><td>1つ目：集荷の受付</td><td><strong>設計は粗くても、同じ言葉があれば成立した。</strong>「動くソフトウェアを早く出せるか」が事業として重要な場合がある</td></tr>
        <tr><td>2つ目：荷主の管理</td><td><strong>名前に前置きが要り始めたら、境界が足りない。</strong>データベース側へ逃がした結果、別々の言葉が並び立った</td></tr>
        <tr><td>3つ目：外部の通知の取り込み</td><td><strong>カテゴリーが変わったのに、実装を変えなかった</strong></td></tr>
        <tr><td>4つ目：運賃の精算</td><td><strong>同じ言葉があったので、変えどきに気づけた</strong></td></tr>
        <tr><td>5つ目：提携先の連携基盤</td><td><strong>カテゴリーの判断そのものが誤っていた。</strong>分割の失敗に見えたが、本当は補完だった</td></tr>
      </tbody>
    </table>
  </div>

  <div class="box ok">
    <h3>「逆転の検証」も落ちていました</h3>
    <p>通常はカテゴリーを決めてから実装方法を選びますが、<strong>その順序を逆にたどってカテゴリーの判断そのものを確かめる</strong>手です。注釈で条件を固定しました ── <strong>憶測や粉飾を入れずに選ぶことが条件である。</strong>「中核だからドメインモデルにすべき」と考えた時点で、この検証は成り立たなくなる。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>3つのカテゴリーの対比</td><td>分類</td><td>表。6つの観点</td></tr>
        <tr><td>全判断を1枚にまとめた流れ</td><td>判断基準</td><td><strong>図。入口はカテゴリー1つ、出口はテスト方針</strong></td></tr>
        <tr><td class="new">事例から学ぶ</td><td><strong>×</strong></td><td><strong>子5つ（うち2つはさらに子を持つ）</strong></td></tr>
        <tr><td class="new">　2つ目：正しくやることは高くついた</td><td>×</td><td><strong>適切な境界を最初から見つけることはほとんど不可能</strong></td></tr>
        <tr><td class="new">　2つ目：別々の言葉が並び立った</td><td>×</td><td><strong>2チームが会話せず別々に実装。数年にわたって欠陥を抱えた</strong></td></tr>
        <tr><td class="new">　5つ目：本当の課題は分割ではなかった</td><td>×</td><td><strong>競争優位はソフトウェアではなく協業関係にあった</strong></td></tr>
        <tr><td class="new">同じ言葉は選ぶものではない</td><td>×</td><td><strong>表。5つの文脈で有無と結果が対応している</strong></td></tr>
        <tr><td class="new">実装方法からカテゴリーを逆に検証する</td><td><strong>×</strong></td><td><strong>図＋表。食い違いの2つの読み方</strong></td></tr>
        <tr><td class="new">たいへんさを無視しない</td><td>×</td><td><strong>たいへんさは、設計判断の進化につながる重要な兆候</strong></td></tr>
        <tr><td class="new">境界の引き方4つと、その評価</td><td>×</td><td><strong>表。1つは絶対にやってはいけない</strong></td></tr>
        <tr><td class="new">　最初の文脈の大きさ</td><td>×</td><td>業務知識が乏しいほど広く始める</td></tr>
        <tr><td class="new">実践するときの6つの段</td><td>×</td><td><strong>図。逆の検証で戻る線がある</strong></td></tr>
        <tr><td>アンチパターン ×6</td><td>あり</td><td>そのまま維持</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅲ. 完全プレビュー</h2>
  <p class="narrow">描画された299行を、<strong>省略なしで</strong>並べています。25ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / closing-heuristics</span><span>ノード25 ・ 図3 ・ 原文6</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅳ. 19本すべての結果</h2>
  <div class="tally">
    <div class="stat"><span class="n">19</span><span class="l">本</span></div>
    <div class="stat"><span class="n">450</span><span class="l">ノード</span></div>
    <div class="stat"><span class="n">80</span><span class="l">図</span></div>
    <div class="stat"><span class="n">30</span><span class="l">原文（コード・表）</span></div>
    <div class="stat ok"><span class="n">2.8×</span><span class="l">旧要約版比</span></div>
  </div>

  <div class="tablewrap">
    <table>
      <thead><tr><th>本</th><th>旧要約版</th><th>変換後</th><th>書き起こし版</th><th>図</th></tr></thead>
      <tbody>
        <tr><td>business-domain</td><td>79</td><td>121</td><td>58</td><td>2</td></tr>
        <tr><td>domain-expert</td><td>80</td><td>134</td><td>50</td><td>2</td></tr>
        <tr><td>subdomain</td><td>112</td><td>268</td><td>222</td><td>5</td></tr>
        <tr><td>ubiquitous-language</td><td>99</td><td>231</td><td>177</td><td>3</td></tr>
        <tr><td>bounded-context</td><td>93</td><td>189</td><td>291</td><td>2</td></tr>
        <tr><td>context-integration</td><td>105</td><td>352</td><td>250</td><td>8</td></tr>
        <tr><td>business-logic-simple</td><td>107</td><td>206</td><td>210</td><td>1</td></tr>
        <tr><td>domain-model</td><td>112</td><td>376</td><td>431</td><td>3</td></tr>
        <tr><td>event-sourced-domain-model</td><td>107</td><td>501</td><td>408</td><td>5</td></tr>
        <tr><td>architecture-patterns</td><td>104</td><td>349</td><td>268</td><td>6</td></tr>
        <tr><td>communication</td><td>114</td><td>303</td><td>234</td><td>5</td></tr>
        <tr><td>design-heuristics</td><td>120</td><td>310</td><td>203</td><td>5</td></tr>
        <tr><td>evolving-design</td><td>111</td><td>271</td><td>283</td><td>3</td></tr>
        <tr><td>event-storming</td><td>108</td><td>301</td><td>262</td><td>5</td></tr>
        <tr><td>real-world-ddd</td><td>102</td><td>314</td><td>308</td><td>5</td></tr>
        <tr><td>microservices</td><td>109</td><td>321</td><td>265</td><td>7</td></tr>
        <tr><td>event-driven-architecture</td><td>115</td><td>372</td><td>309</td><td>5</td></tr>
        <tr><td>data-mesh</td><td>110</td><td>315</td><td>223</td><td>5</td></tr>
        <tr><td><strong>closing-heuristics</strong></td><td><strong>110</strong></td><td><strong>299</strong></td><td><strong>298</strong></td><td><strong>3</strong></td></tr>
        <tr><td><strong>合計</strong></td><td><strong>1,997</strong></td><td><strong>5,533</strong></td><td><strong>4,750</strong></td><td><strong>80</strong></td></tr>
      </tbody>
    </table>
  </div>

  <div class="box bad">
    <h3>旧要約版が落としていたもの</h3>
    <p><strong>図は19本すべてで0でした。</strong>書き起こし版に図があった本でも、例外なく落ちています。理由ははっきりしていて、旧版の器（原則・分類・判断基準・実例・アンチパターン）に<strong>図を入れる場所が無かった</strong>からです。型に合うものだけが残り、型に無いものは落ちる。</p>
    <p>同じことがコードにも起きていました。<code>domain-model</code> のコード7本、<code>event-sourced-domain-model</code> のコード7本 ── どちらも全滅していました。</p>
  </div>

  <div class="box ok">
    <h3>途中で形が2回変わりました</h3>
    <p><strong>1回目</strong>：Markdown の表がコード塊に囲われて表として読めなかった件。仕様に「宣言された種類が描画の出力形式そのものであるとき、囲わずにそのまま置く」を足しました。</p>
    <p><strong>2回目</strong>：図の後ろに置いていた辺の一覧表（から／へ／関係）が、図の書き写しでしかなかった件。<code>figure.notes</code>（どこの話か／図に載せきれないこと）に入れ替えました。<strong>この形が19本を通じて一番効きました</strong> ── 「どこの話か」に図の要素名しか書けないので、どこにも紐づかない一般論を書いた時点でそれが見えます。</p>
  </div>

  <div class="box bad">
    <h3>1つだけ、注釈の無い図が残っています</h3>
    <p><code>subdomain</code> の分類マトリクス（差別化と複雑さの2軸）です。この図は4象限の図で、いまの描画の語彙には対応する種類がないため、原文として持たせています。注釈の表が付くのは図の宣言だけなので、ここには付きません。<strong>意図と読み取りの文章は付いており、4象限すべての説明はそこに入っています。</strong>専用の種類を1つの図のために足すのは釣り合わないと判断しました。</p>
  </div>
</section>

<section>
  <h2>Ⅴ. 置き換えたもの（全19本）</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>種類</th><th>対応</th><th>例</th></tr></thead>
      <tbody>
        <tr><td>書籍の実例（業務の題材）</td><td>架空の業務へ置き換え。<strong>構造は保つ</strong></td><td>見込み客の履歴 → 配送の依頼の履歴（連絡先が途中で変わる位置は動かさない）</td></tr>
        <tr><td>実在の企業名・実際の沿革</td><td>架空の会社へ</td><td>印刷 → 包装材 → 物流の梱包設計</td></tr>
        <tr><td>実在の製品名（計12個以上）</td><td>役割の説明へ</td><td>「外部との入口を担う一般的な仕組み」</td></tr>
        <tr><td>人名・考案者名</td><td>役割へ、または主張そのものへ</td><td>引用は「誰が言ったか」を落として「何を言ったか」だけ残す</td></tr>
        <tr><td>比喩に由来する呼び名</td><td>その方式が何をするかの説明へ</td><td>「外から包んで置き換える」</td></tr>
        <tr><td>特定の法令名・出来事の名称</td><td>その内容の説明へ</td><td>「追記しかできない置き場から情報を消せるか」</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>毎回、機械で確認しました</h3>
    <p>変換のたびに書籍固有の語を grep して0件を確認しています。<strong>19本すべてで0件です。</strong>また旧版の器（原則・分類・判断基準・実例・アンチパターン）が残っていないことも、19本すべてで確認済みです ── 入力は書き起こし版だけで、旧要約版の文言が残る経路はありません。</p>
  </div>
</section>

<footer>
  旧要約版1,997行・書き起こし版4,750行・変換後5,533行（描画結果の実測）。450ノード・図80・原文30。<br>
  すべて書き起こし版から組み立て、旧要約版の器は19本とも消えている。書籍固有の題材は架空の業務へ置き換え、構造は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-closing-heuristics.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))