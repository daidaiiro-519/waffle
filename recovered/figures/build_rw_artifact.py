"""15本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "real-world-ddd の変換 ── 15本目")
frag = pathlib.Path(f"{S}/rw_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 15本目</span>
  <h1><code>real-world-ddd</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版102行 → <strong>314行</strong>。すでに動いているシステムへどう持ち込むか、という実践編です。<strong>この本には「やらないこと」が多く書かれていて、そこが落ちていました。</strong></p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">26</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">5</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">4</span><span class="l">原文（表）</span></div>
    <div class="stat"><span class="n">314</span><span class="l">行（旧102 / 書起し308）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 「描いていない経路」が3つあります</h2>
  <p class="narrow">この本は<strong>やってはいけないこと</strong>を、選択肢として並べずに排除する形で書いています。図にすると、その排除が「線が無い」という形で現れるので、注釈で名指ししました。</p>

  <div class="tablewrap">
    <table>
      <thead><tr><th>図</th><th>描いていないもの</th><th>なぜ</th></tr></thead>
      <tbody>
        <tr><td>改善の進め方</td><td>「全体を一から書き直す」という第3の選択肢</td><td>描き忘れではなく、<strong>ほとんど成功せず、経営の側の支持も得られない</strong>ため</td></tr>
        <tr><td>実装方法の移行</td><td>手続きから直接イベント履歴式へ飛ぶ経路</td><td><strong>誤ったトランザクション境界をそのまま持ち込む</strong>ことになる</td></tr>
        <tr><td>外から包んで置き換える</td><td>データベースをどちらが持つか</td><td>移行のあいだは<strong>「1文脈1データベース」の原則を一時的に曲げて共有してよい</strong></td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>全部やるか、やらないかではない</td><td>原則2行</td><td><strong>すでに稼働しているシステムでこそ効く</strong>、という位置づけ</td></tr>
        <tr><td>最初にやる2つのこと</td><td>判断基準に手順</td><td><strong>図</strong>＋子2つ。コードから始めない理由つき</td></tr>
        <tr><td class="new">　事業活動を理解する</td><td>×</td><td><strong>4つの問い＋組織図が手がかりになる</strong></td></tr>
        <tr><td class="new">　　中核の業務領域を見つける</td><td>×</td><td><strong>ありがたくない経験則 ── 大きな泥団子がある場所</strong></td></tr>
        <tr><td class="new">　　一般／補完の業務領域を見つける</td><td>×</td><td>既製品で置き換わるか／粗削りでも問題にならないか</td></tr>
        <tr><td class="new">　既存システムの構造を調べる</td><td>×</td><td><strong>注目するのは、それぞれの部分の一生の違い</strong></td></tr>
        <tr><td class="new">　　設計の基本方針を評価する</td><td>×</td><td><strong>表。文脈の地図から探す5つの不適切な関係</strong></td></tr>
        <tr><td>大きな絵を描いて、小さく始める</td><td>原則1行</td><td><strong>図＋子2つ。まず論理的な境界を業務領域に対応させる</strong></td></tr>
        <tr><td class="new">　論理の境界を物理の境界へ変えるとき</td><td>×</td><td><strong>表。連係の問題ごとの変更先</strong></td></tr>
        <tr><td class="new">　実装方法の不一致を見つける</td><td>×</td><td>中核に手続き・1行のオブジェクトを使っているのが最悪</td></tr>
        <tr><td>同じ言葉を育てる</td><td>×</td><td><strong>図</strong>＋必要条件は業務知識と適切なモデルの2つ</td></tr>
        <tr><td class="new">　外から包んで置き換える</td><td>×</td><td><strong>図。4つの手順＋入口は移行後に取り除く</strong></td></tr>
        <tr><td class="new">　段階的に直す</td><td>×</td><td><strong>図。始めどころは値オブジェクトの候補</strong></td></tr>
        <tr><td class="new">　　守りの仕組みを置く</td><td>×</td><td>モデル変換装置と共用サービスで上下から守る</td></tr>
        <tr><td class="new">道具として位置づける</td><td><strong>×</strong></td><td><strong>子4つ。「売り込む」より道具の1つとして</strong></td></tr>
        <tr><td class="new">　同じ言葉から始める</td><td>×</td><td><strong>もっとも重要なのはソースコードを同じ言葉で書くこと</strong></td></tr>
        <tr><td class="new">　権威ではなく理由で説得する</td><td><strong>×</strong></td><td><strong>表。6つの問いと、それぞれの理由</strong></td></tr>
        <tr><td class="new">　イベント履歴式の利点は業務エキスパートに響く</td><td>×</td><td>気に入って同僚へ勧めてくれるようになる</td></tr>
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
        <tr><td>最初の5段</td><td>1. 事業活動と事業方針を調べる</td><td><strong>コードから始めないのが要点。</strong>先にコードを読むと、いま入り組んでいる場所が重要な場所に見えてしまう</td></tr>
        <tr><td>モジュールの組み替え</td><td>技術の視点で割った形</td><td>この形が誤りだと言っているのではない。<strong>業務領域の境界と対応していないと、1つの業務の変更がすべての箱にまたがる</strong></td></tr>
        <tr><td>実装方法の移行</td><td>状態を持つ集約</td><td><strong>ここを飛ばしてはいけない。</strong>いったんここで止まり、集約の境界を確かめる</td></tr>
        <tr><td>外から包んで置き換える</td><td>既存のシステム（大）／（小）</td><td>大きさが変わるのは機能が移るため。<strong>既存の側では急を要する修正を除いて修正も拡張も止める。止めないと新しい側が追いつけない</strong></td></tr>
        <tr><td>改善の進め方</td><td>2つの終点</td><td>どちらを選んでも、<strong>その前に業務知識と適切なモデルが要る。</strong>無いまま着手すると同じ形が再生産される</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された314行を、<strong>省略なしで</strong>並べています。26ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / real-world-ddd</span><span>ノード26 ・ 図5 ・ 原文4</span></div>
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
        <tr><td>広告の業務領域を使ったモジュール構成（前後10個の名前）</td><td>配送の業務領域（前5個・後4個）</td><td>技術の視点で割った形から業務の視点で割った形への組み替え。<strong>箱の数が変わることも含めて</strong></td></tr>
        <tr><td>植物の生態にちなんだ移行方式の呼び名</td><td>「外から包んで置き換える」</td><td>包んで育て、最後に宿主が役目を終えるという移行の形</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>呼び名を説明に言い換えました</h3>
    <p>比喩に由来する呼び名は、<strong>その方式が何をするかの説明</strong>に置き換えています。呼び名を知らない読み手にも、何をする方式かがそのまま伝わります。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 15本目までの推移</h2>
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
        <tr><td><strong>real-world-ddd</strong></td><td><strong>102</strong></td><td><strong>314</strong></td><td><strong>308</strong></td></tr>
        <tr><td><strong>15本の合計</strong></td><td><strong>1,553</strong></td><td><strong>4,226</strong></td><td><strong>3,655</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>15 / 19本。</strong>残り4本・約1,100行 ── マイクロサービス、イベント駆動、データメッシュ、締めの経験則です。<strong>本編（第Ⅰ〜Ⅲ部）が揃い、残るのは応用編と締めだけになりました。</strong></p>
</section>

<footer>
  旧要約版102行・書き起こし版308行・変換後314行（描画結果の実測）。<br>
  モジュール構成の例は架空の業務へ、比喩に由来する呼び名はその方式が何をするかの説明へ置き換えた。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-real-world-ddd.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))