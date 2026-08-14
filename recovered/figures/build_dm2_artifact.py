"""18本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "data-mesh の変換 ── 18本目")
frag = pathlib.Path(f"{S}/dm2_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 18本目</span>
  <h1><code>data-mesh</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版110行 → <strong>315行</strong>。分析のためのデータに対する、ドメイン駆動設計です。<strong>この本だけ、対処すべき相手が「組織」でもありました。</strong></p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">25</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">5</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">3</span><span class="l">原文（表）</span></div>
    <div class="stat"><span class="n">315</span><span class="l">行（旧110 / 書起し223）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 4つの原則のうち、後ろ2つは組織の話です</h2>
  <p class="narrow">「データを業務の視点で分割する」「データを製品として扱う」はデータの置き方ですが、「自律性を高める」「生態系を作る」は<strong>チームの作り方と統治の仕組み</strong>の話です。旧版はこの後半2つを落としていました。</p>

  <div class="box ok">
    <h3>チーム構成が変わる、という指摘も戻りました</h3>
    <p>データを製品として扱うには、開発チームの中に<strong>データに詳しい担当者</strong>が要る ── 業務のためのシステムの専門家だけの構成では欠けていた役割である、と書かれています。技術の選択ではなく、人の配置の話です。</p>
  </div>

  <div class="box bad">
    <h3>3つの方式の「共通の弱点」も落ちていました</h3>
    <p>1つにまとめる形と生のまま貯める形は、どちらも<strong>業務のためのデータベースを直接参照する</strong>という同じ弱点を持ちます。表の設計を少し変えただけで動かなくなる。<strong>モデルが頻繁に変わる領域ではとくに深刻</strong>で、これが3つ目の方式が要る理由になります。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>この概念が扱う範囲</td><td>概要</td><td>境界を区切って内部を守る、という同じ構図</td></tr>
        <tr><td>業務のためのモデルと分析のためのモデル</td><td>原則1行</td><td><strong>表。目的が違うので流用できない</strong></td></tr>
        <tr><td class="new">　2種類の表</td><td><strong>×</strong></td><td><strong>表。起きたことの表（消さず足すだけ）と性質の表（高度に正規化）</strong></td></tr>
        <tr><td class="new">　分析のためのモデルの形</td><td><strong>×</strong></td><td><strong>図。星の形と雪の結晶の形</strong></td></tr>
        <tr><td>3つの方式</td><td>分類3行</td><td><strong>図</strong>＋子3つ</td></tr>
        <tr><td class="new">　1つにまとめる形：抱える課題</td><td>アンチパターンに1つ</td><td><strong>4つの課題。部門間の意思疎通も含む</strong></td></tr>
        <tr><td class="new">　生のまま貯める形</td><td>1行</td><td>あとから変換できる利点と、品質が保証されない欠点</td></tr>
        <tr><td class="new">　2つに共通する課題</td><td><strong>×</strong></td><td><strong>根本は業務側の実装との密な結びつき。DDDでは特に深刻</strong></td></tr>
        <tr><td>4つの原則</td><td>原則に一部</td><td><strong>表</strong>＋子4つ</td></tr>
        <tr><td class="new">　データを業務の視点で分割する</td><td>一部</td><td><strong>図。境界が区切られた文脈と一致する</strong></td></tr>
        <tr><td class="new">　データを製品として扱う</td><td>×</td><td><strong>4つの要件＋チーム構成が変わるという指摘</strong></td></tr>
        <tr><td class="new">　自律性を高める</td><td><strong>×</strong></td><td><strong>共通基盤を専任チームが整える</strong></td></tr>
        <tr><td class="new">　生態系を作る</td><td><strong>×</strong></td><td><strong>統治の集まりを作り、規則を定める</strong></td></tr>
        <tr><td class="new">ドメイン駆動設計と組み合わせる</td><td>×</td><td><strong>子4つ。同じ言葉／共用サービス／CQRS／連係方法</strong></td></tr>
        <tr><td class="new">　連係方法もそのまま当てはまる</td><td>判断基準に1つ</td><td><strong>図</strong></td></tr>
        <tr><td>どの方式を採るか</td><td>判断基準</td><td><strong>図</strong></td></tr>
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
        <tr><td>3つの方式</td><td>1つにまとめる形／生のまま貯める形</td><td><strong>この2つは共通の弱点を持つ。</strong>内部の実装を直接参照するので、表の設計を少し変えただけで動かなくなる</td></tr>
        <tr><td>3つの方式</td><td>発生源ごとに分ける形</td><td>他の2つと違い、<strong>変換する側ではなく発生源の側が用意する。この向きの違いが密な結びつきを根本から断つ</strong></td></tr>
        <tr><td>境界の一致</td><td>3本の変換の矢印</td><td>囲みの内側で完結している。<strong>囲みをまたぐ変換の線が無いのは、変換を外部の誰かに任せないという主張</strong></td></tr>
        <tr><td>境界の一致</td><td>3つの分析モデル</td><td><strong>あとで1つに統合するものではない。統合しないことが要点で、</strong>必要なら使う側が複数を組み合わせる</td></tr>
        <tr><td>方式の選び方</td><td>2つの括弧書き</td><td>終点に但し書きが付いている。<strong>選んではいけないという意味ではなく、承知したうえで選ぶという意味</strong></td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された315行を、<strong>省略なしで</strong>並べています。25ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / data-mesh</span><span>ノード25 ・ 図5 ・ 原文3</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅴ. 置き換えたもの</h2>
  <p class="narrow">この本は<strong>方式そのものが固有名で呼ばれている</strong>ため、これまでと違う扱いが要りました。</p>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書き起こし版</th><th>置き換え先</th><th>保った内容</th></tr></thead>
      <tbody>
        <tr><td>3つの方式の固有名</td><td>「1つのモデルへまとめる形」「生のまま貯める形」「発生源ごとに分ける形」</td><td>3つの違いと、前2つが共通の弱点を持つこと</td></tr>
        <tr><td>処理の種類・取り込み処理・水準の取り決めを指す略語</td><td>その内容の説明</td><td>2つの処理の目的の違い、取り出して変換して書き出す流れ、信頼できる水準を定めて監視すること</td></tr>
        <tr><td>広告関連の3つの文脈</td><td>受注・配送・請求</td><td>各文脈が業務のためのモデルと分析のためのモデルの両方を持つこと</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>固有名は、その方式が何をするかで呼び直しました</h3>
    <p>呼び名を知らない読み手にも、<strong>何をする方式かがそのまま伝わります。</strong>実際、3つを並べたときに「前2つが同じ弱点を持つ」という関係が、呼び名より読みやすくなりました。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 18本目までの推移</h2>
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
        <tr><td>event-driven-architecture</td><td>115</td><td>372</td><td>309</td></tr>
        <tr><td><strong>data-mesh</strong></td><td><strong>110</strong></td><td><strong>315</strong></td><td><strong>223</strong></td></tr>
        <tr><td><strong>18本の合計</strong></td><td><strong>1,887</strong></td><td><strong>5,234</strong></td><td><strong>4,452</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>18 / 19本。</strong>残り1本 ── <code>closing-heuristics</code>（298行）だけになりました。</p>
</section>

<footer>
  旧要約版110行・書き起こし版223行・変換後315行（描画結果の実測）。<br>
  3つの方式の固有名は、その方式が何をするかの呼び名へ置き換えた。実例は架空の業務へ差し替えた。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-data-mesh.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))