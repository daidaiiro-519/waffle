"""16本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "microservices の変換 ── 16本目")
frag = pathlib.Path(f"{S}/ms_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 16本目</span>
  <h1><code>microservices</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版109行 → <strong>321行</strong>。応用編の最初です。<code>bounded-context</code> の「大きさに一般解はない」が、ここで<strong>広さの順序という形</strong>になります。図7つ。</p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">25</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">7</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">3</span><span class="l">原文（表2・C#1）</span></div>
    <div class="stat"><span class="n">321</span><span class="l">行（旧109 / 書起し265）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 「深さ」が中心なのに、旧版に定義がありませんでした</h2>
  <p class="narrow">この本は<strong>マイクロサービスの良し悪しを入口と中身の比で測る</strong>という一点で組み立てられています。旧版はこの「深さ」の定義を落としていたので、判断基準が「業務領域に合わせる」という結論だけになっていました。</p>

  <div class="box ok">
    <h3>比であることを、注釈で固定しました</h3>
    <p><strong>深いモジュール（囲み）</strong> ── 「小さい」と「複雑」が同居していることが要点である。<strong>どちらか片方だけを見て評価すると、小さいだけの浅いモジュールを良いものと取り違える。</strong></p>
    <p><strong>共用サービス</strong> ── 中身の処理は変わっていない。入口を小さくするだけでサービスは深くなる。<strong>深さは中身の量ではなく、入口との比で決まる</strong>ためである。</p>
  </div>

  <div class="box bad">
    <h3>両端がどちらも失敗である、という構造も落ちていました</h3>
    <p>境界を広げすぎれば大きな泥団子、狭めすぎれば分散した大きな泥団子。<strong>合理的な選択肢はその間の範囲にしかない。</strong>旧版は「業務領域に合わせる」とだけ書いていて、なぜそこなのかが言えていませんでした。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>この概念が扱う範囲</td><td>概要</td><td><strong>多くの組織が手にしたのは分散した大きな泥団子だった</strong></td></tr>
        <tr><td>サービスとマイクロサービス</td><td>原則1行</td><td>子3つ</td></tr>
        <tr><td class="new">　入口を小さくすると何が起きるか</td><td>×</td><td>明快さ・つながりの理解・独立性の3つ</td></tr>
        <tr><td class="new">　データベースを外へ見せない</td><td>×</td><td><strong>さらけ出すと入口が巨大になる</strong></td></tr>
        <tr><td class="new">　1つの処理につき1つのサービスは、完璧ではない</td><td>アンチパターン</td><td><strong>判断基準としても立てた。なぜ泥団子になるかの筋道つき</strong></td></tr>
        <tr><td class="new">2種類の複雑さ</td><td>原則1行</td><td><strong>表。片方だけ最小にすると何が起きるか</strong></td></tr>
        <tr><td class="new">モジュールの深さ</td><td><strong>×</strong></td><td><strong>図＋子4つ。この本の中心概念</strong></td></tr>
        <tr><td class="new">　浅いモジュールの極端な例</td><td>×</td><td><strong>コード。2つの数を足すだけのサービス</strong></td></tr>
        <tr><td class="new">　深さは論理と物理の両方を表す</td><td>×</td><td><strong>浅いサービスこそが失敗の原因</strong></td></tr>
        <tr><td class="new">　使ってはいけない定義</td><td>×</td><td>「n行以下」「書き換えるほうが簡単」</td></tr>
        <tr><td class="new">　粒度と変更の費用</td><td>×</td><td><strong>U字。両端がどちらも高くつく</strong></td></tr>
        <tr><td class="new">境界の広さは何で決まるか</td><td>分類のみ</td><td><strong>図＋子3つ。集約 → 業務領域 → 区切られた文脈の順序</strong></td></tr>
        <tr><td>　区切られた文脈との関係は対等ではない</td><td>アンチパターン</td><td><strong>図。逆向きの線が無いことが主張</strong></td></tr>
        <tr><td class="new">　集約はもっとも狭い</td><td>一部</td><td><strong>図。3つの確認観点つき</strong></td></tr>
        <tr><td class="new">　業務領域がもっともつり合う</td><td>判断基準に結論のみ</td><td><strong>なぜ自然に深くなるのかの理由＋2つの例外</strong></td></tr>
        <tr><td class="new">入口を小さくする</td><td><strong>×</strong></td><td><strong>図2つ。共用サービスとモデル変換装置で深くする</strong></td></tr>
        <tr><td class="new">4つの概念の対比</td><td>×</td><td>表。境界の広さの順</td></tr>
        <tr><td>境界をどう決めるか</td><td>判断基準</td><td><strong>図</strong></td></tr>
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
        <tr><td>非対称の関係</td><td>マイクロサービスから区切られた文脈</td><td><strong>逆向きの線が無いのが主張。</strong>区切られた文脈は巨大な一枚岩であることもあり、それが有効な選択である場合もある</td></tr>
        <tr><td>境界の広さ</td><td>2つの泥団子</td><td><strong>両端がどちらも失敗として描かれているのが要点。</strong>合理的な選択肢はその間にしかない</td></tr>
        <tr><td>境界の広さ</td><td>業務領域</td><td>もっともつり合うというだけで、<strong>常に正解という意味ではない</strong></td></tr>
        <tr><td>境界の決め方</td><td>集約まで狭める</td><td>この終点だけ条件つき。<strong>他の集約と関係が強いほど、単独にすると浅くなる</strong></td></tr>
        <tr><td>深さ</td><td>中身は単純</td><td>極端な例は2つの数を足すだけのもの。<strong>複雑さを閉じ込めるどころか、不必要な複雑さを持ち込む</strong></td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された321行を、<strong>省略なしで</strong>並べています。25ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / microservices</span><span>ノード25 ・ 図7 ・ 原文3</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅴ. 置き換えたもの</h2>
  <p class="narrow">この本は<strong>他の文献からの引用が3件</strong>あり、これまでとは違う種類の対応が要りました。</p>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書き起こし版</th><th>置き換え先</th><th>保った内容</th></tr></thead>
      <tbody>
        <tr><td>標準化団体の名称と、その団体によるサービスの定義</td><td>定義の内容そのもの</td><td>「1つ以上の機能へたどりつける仕組みで、取り決められた入口を通して提供されるもの」</td></tr>
        <tr><td>文献名・著者名つきの引用（全体の複雑さについて）</td><td>主張そのもの</td><td>部分の複雑さの最小化より、システム全体の構造の複雑さのほうがはるかに重要である</td></tr>
        <tr><td>文献名・著者名つきの「深さ」の評価軸</td><td>評価軸そのもの</td><td>入口と中身の2つでモジュールを定義し、その比で深さを測る</td></tr>
        <tr><td>作業管理サービスの分解例</td><td>「その形で分解すると」という一般化</td><td>各サービスのデータベースは閉じ込められるが、連係のために入口が広がっていく筋道</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>引用は「誰が言ったか」を落として「何を言ったか」だけ残しました</h3>
    <p>出典を示す価値はありますが、引用文をそのまま運ぶことは避けています。<strong>主張の内容は判断に使えるので落とさず、帰属だけを外しました。</strong>留保事項にその旨を書いています。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 16本目までの推移</h2>
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
        <tr><td><strong>microservices</strong></td><td><strong>109</strong></td><td><strong>321</strong></td><td><strong>265</strong></td></tr>
        <tr><td><strong>16本の合計</strong></td><td><strong>1,662</strong></td><td><strong>4,547</strong></td><td><strong>3,920</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>16 / 19本。</strong>残り3本・約840行 ── イベント駆動、データメッシュ、締めの経験則です。</p>
</section>

<footer>
  旧要約版109行・書き起こし版265行・変換後321行（描画結果の実測）。<br>
  団体名・文献名・著者名は落とし、主張の内容だけを残した。深さの定義と境界の広さの順序は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-microservices.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))