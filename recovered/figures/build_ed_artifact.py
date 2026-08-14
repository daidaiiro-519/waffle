"""17本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "event-driven-architecture の変換 ── 17本目")
frag = pathlib.Path(f"{S}/ed_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 17本目</span>
  <h1><code>event-driven-architecture</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版115行 → <strong>372行</strong>。<code>communication</code> の送信箱・サーガと、<code>microservices</code> の境界の話が合流します。<strong>3種類のイベントの使い分けが、旧版では分類3行に潰れていました。</strong></p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">28</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">5</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">7</span><span class="l">原文（表4・JSON2・JS1）</span></div>
    <div class="stat"><span class="n">372</span><span class="l">行（旧115 / 書起し309）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 同じ出来事を3通りに書き分ける例が落ちていました</h2>
  <p class="narrow">この本の中心は<strong>「何をどれだけ載せるか」で3種類に分かれる</strong>ことです。書き起こし版はそれを、1つの出来事を3通りに書いたコードで見せています。旧版はコードを全部落としていたので、3つの違いが「最小限／すべて／業務の出来事」という語の並びだけになっていました。</p>

  <div class="box ok">
    <h3>3つの違いは、目的の違いです</h3>
    <p>注釈で固定しました ── <strong>3つは技術の違いではなく、何のために出すかの違いである。</strong>知らせるだけのものは連係の複雑さを減らすため、状態を運ぶものはデータを非同期に複製するため、業務イベントは業務領域の活動をモデル化して説明するため。</p>
  </div>

  <div class="box bad">
    <h3>密な結びつき3種の「起点が1つ」であることも落ちていました</h3>
    <p>時間・機能・実装の3つの結びつきは、すべて<strong>業務イベントをそのまま外へ公開したこと</strong>から生じます。図にして注釈で名指ししました ── 個別に対処するより、<strong>この起点を絶つほうが根本的である。</strong></p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>イベント駆動型とは何か</td><td>概要</td><td>区切られた文脈の入口を設計する手段</td></tr>
        <tr><td class="new">　イベントの履歴を保存する形とは別物である</td><td>アンチパターン</td><td><strong>表。範囲と役割が違う。独立して決められる</strong></td></tr>
        <tr><td class="new">メッセージの種類</td><td>×</td><td><strong>図。イベントと指示、そのうち片方が3つに分かれる</strong></td></tr>
        <tr><td class="new">　イベントと指示の違い</td><td>×</td><td><strong>指示は拒否できるが、イベントは取り消せない</strong></td></tr>
        <tr><td class="new">　イベントのデータの形</td><td>×</td><td>原文。説明のための情報と内容そのもの</td></tr>
        <tr><td>3種類のイベント</td><td>分類3行</td><td>子3つ（うち1つはさらに子3つ）</td></tr>
        <tr><td class="new">　知らせるだけのイベント</td><td>1行</td><td><strong>原文＋好ましい2つの状況（守るべき情報・最新の状態）</strong></td></tr>
        <tr><td class="new">　状態を運ぶイベント</td><td>1行</td><td><strong>発信側が止まっても動ける。形は2通り</strong></td></tr>
        <tr><td class="new">　　知らせるだけとの違い／状態を運ぶとの違い</td><td>×</td><td><strong>目的が違う。集約の状態ではなく一生の途中の出来事</strong></td></tr>
        <tr><td class="new">　　同じ出来事を3つの種類で書き分ける</td><td><strong>×</strong></td><td><strong>原文。この本の中心</strong></td></tr>
        <tr><td class="new">3種類の密な結びつき</td><td>アンチパターンに2つ</td><td><strong>図＋子3つ。起点が1つであることが見える</strong></td></tr>
        <tr><td class="new">結びつきをほどく</td><td><strong>×</strong></td><td><strong>図。改善前と改善後の対比</strong></td></tr>
        <tr><td class="new">最悪の場合を前提に置く</td><td>×</td><td><strong>表。5つの事態と備え</strong></td></tr>
        <tr><td class="new">外へ出すイベントと内側のイベントを使い分ける</td><td>×</td><td>外へ出す業務イベントを限定する</td></tr>
        <tr><td class="new">求める一貫性の水準から選ぶ</td><td>判断基準に1つ</td><td><strong>表＋図</strong></td></tr>
        <tr><td>どのイベントを使うか</td><td>判断基準</td><td><strong>図</strong></td></tr>
        <tr><td>アンチパターン ×4</td><td>あり</td><td>そのまま維持</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅲ. 注釈の例</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>図</th><th>どこの話か</th><th>図に載せきれないこと</th></tr></thead>
      <tbody>
        <tr><td>メッセージの種類</td><td>イベント／指示</td><td>決定的な違いは<strong>拒否できるかどうか。</strong>逆向きの処理をするには埋め合わせの指示しかない</td></tr>
        <tr><td>メッセージの種類</td><td>業務イベント</td><td>他の2つと違い、<strong>外部の誰も興味を持たなくても役に立つ。</strong>そのまま外へ出すと実装の詳細が漏れる</td></tr>
        <tr><td>密な結びつき</td><td>業務イベントをそのまま外へ公開する</td><td><strong>3つすべての起点がここにある。</strong>個別に対処するより起点を絶つほうが根本的</td></tr>
        <tr><td>改善の前後</td><td>実績の集計から配送の計画</td><td><strong>改善前には無かった線。</strong>受け取ったときに取りに行く形にすると、遅延の仕組みが要らなくなる</td></tr>
        <tr><td>イベントの選び方</td><td>発信側の実装の詳細を隠したいか</td><td>「はい」のとき<strong>共用サービスを経由させることが前提</strong>になっている。種類を選ぶだけでは詳細は隠れない</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された372行を、<strong>省略なしで</strong>並べています。28ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / event-driven-architecture</span><span>ノード28 ・ 図5 ・ 原文7</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅴ. 置き換えたもの</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書き起こし版</th><th>置き換え先</th><th>保った構造</th></tr></thead>
      <tbody>
        <tr><td>人の身分に関わる出来事を3通りに書き分けた例</td><td>配送先の変更を3通りに書き分けた例</td><td>事実だけ／変わった値／業務としての出来事の要点、という3つの違い</td></tr>
        <tr><td>給与明細の発行を使った、知らせるだけのイベントの例</td><td>送り状の作成</td><td>内容そのものは載せず、たどる先だけを渡す形</td></tr>
        <tr><td>広告関連の4つの文脈（改善の前後）</td><td>顧客の管理・受注・配送の計画・実績の集計</td><td>1つが直接ばらまく形と、共用サービスを挟んで2種類に分ける形の対比</td></tr>
        <tr><td>「パラノイアだけが生き残る」という見出し</td><td>「最悪の場合を前提に置く」</td><td>5つの事態を「起きる」として設計する、という指針</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>機械で確認しました</h3>
    <p>書籍固有の題材（人の身分に関わる出来事・給与明細・広告の文脈群・比喩的な見出し）を grep して<strong>0件</strong>。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 17本目までの推移</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>本</th><th>旧要約版</th><th>変換後</th><th>書き起こし版</th></tr></thead>
      <tbody>
        <tr><td>subdomain</td><td>112</td><td>268</td><td>222</td></tr>
        <tr><td>bounded-context</td><td>93</td><td>189</td><td>291</td></tr>
        <tr><td>domain-model</td><td>112</td><td>376</td><td>431</td></tr>
        <tr><td>business-logic-simple</td><td>107</td><td>206</td><td>210</td></tr>
        <tr><td>evolving-design</td><td>111</td><td>271</td><td>283</td></tr>
        <tr><td>ubiquitous-language</td><td>99</td><td>231</td><td>177</td></tr>
        <tr><td>design-heuristics</td><td>120</td><td>310</td><td>203</td></tr>
        <tr><td>architecture-patterns</td><td>104</td><td>349</td><td>268</td></tr>
        <tr><td>event-sourced-domain-model</td><td>107</td><td>501</td><td>408</td></tr>
        <tr><td>context-integration</td><td>105</td><td>352</td><td>250</td></tr>
        <tr><td>communication</td><td>114</td><td>303</td><td>234</td></tr>
        <tr><td>business-domain</td><td>79</td><td>121</td><td>58</td></tr>
        <tr><td>domain-expert</td><td>80</td><td>134</td><td>50</td></tr>
        <tr><td>event-storming</td><td>108</td><td>301</td><td>262</td></tr>
        <tr><td>real-world-ddd</td><td>102</td><td>314</td><td>308</td></tr>
        <tr><td>microservices</td><td>109</td><td>321</td><td>265</td></tr>
        <tr><td><strong>event-driven-architecture</strong></td><td><strong>115</strong></td><td><strong>372</strong></td><td><strong>309</strong></td></tr>
        <tr><td><strong>17本の合計</strong></td><td><strong>1,777</strong></td><td><strong>4,919</strong></td><td><strong>4,229</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>17 / 19本。</strong>残り2本・約520行 ── データメッシュと、締めの経験則です。</p>
</section>

<footer>
  旧要約版115行・書き起こし版309行・変換後372行（描画結果の実測）。<br>
  実例は架空の業務へ、比喩的な見出しはその内容へ置き換えた。3種類の違いと、密な結びつきの起点は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-event-driven-architecture.html").write_text(
    out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))