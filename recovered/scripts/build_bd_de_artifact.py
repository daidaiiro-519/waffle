"""12・13本目のアーティファクトを組み立てる。2本を1つにまとめる（どちらも第I部の土台で短い）。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "business-domain / domain-expert の変換 ── 12・13本目")
bd = pathlib.Path(f"{S}/bd_preview.html").read_text(encoding="utf-8")
de = pathlib.Path(f"{S}/de_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 12・13本目</span>
  <h1><code>business-domain</code> と <code>domain-expert</code> を書き起こし版から移す</h1>
  <p class="standfirst">第Ⅰ部の土台にあたる2本です。<strong>どちらも書き起こし版が50行台</strong>と短く、<code>subdomain</code> と <code>ubiquitous-language</code> が前提にしている同じ層の話なので、1回でまとめて扱いました。旧要約版159行 → <strong>255行</strong>。</p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">18</span><span class="l">ノード（7＋11）</span></div>
    <div class="stat ok"><span class="n">4</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">1</span><span class="l">原文（表）</span></div>
    <div class="stat"><span class="n">255</span><span class="l">行（旧159 / 書起し108）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. この2本は、書き起こし版より旧要約版のほうが長い</h2>
  <p class="narrow">これまでの11本とは逆です。書き起こし版が58行と50行しかないのに、旧要約版は79行と80行ありました。<strong>短い原典を、決まった型（原則・分類・判断基準・実例・アンチパターン）に流し込んだぶん長くなっていた</strong>ということです。</p>

  <div class="box bad">
    <h3>長さは増えても、図は0でした</h3>
    <p><code>business-domain</code> の書き起こし版には<strong>事業領域の構造を示す図</strong>があります。旧版はこれを落として、原則の文章に置き換えていました。型に合う要素だけが残り、型に無いものは落ちる——これまでの11本と同じ壊れ方です。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. business-domain — 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>事業領域とは何か</td><td>あり</td><td>顧客に提供するサービスの大枠</td></tr>
        <tr><td class="new">事業領域の構造</td><td><strong>×</strong></td><td><strong>図。中核・一般・補完への分解</strong></td></tr>
        <tr><td class="new">会社と事業領域は1対1ではない</td><td>一部</td><td><strong>表＋事業領域ごとに独立して分析する</strong></td></tr>
        <tr><td class="new">事業領域は変わる</td><td>×</td><td><strong>分析の対象は現在の事業領域であって、社名や沿革ではない</strong></td></tr>
        <tr><td>事業領域か業務領域か</td><td>判断基準</td><td><strong>図</strong>＋規模では決まらないこと</td></tr>
        <tr><td>アンチパターン</td><td>あり</td><td>そのまま維持</td></tr>
      </tbody>
    </table>
  </div>

  <div class="box ok">
    <h3>注釈で足したもの</h3>
    <p><strong>3本の矢印</strong> ── 業務領域が3つあるという意味ではない。分類が3種類あるという意味で、1つの分類の下に業務領域がいくつあってもよいし、ある分類に当てはまる業務領域が1つも無いこともある。</p>
    <p><strong>「顧客に提供しているサービスの大枠か」</strong> ── 規模の大小では決まらない。小さな会社の事業領域が、大きな会社の1つの業務領域より小さいことは普通にある。</p>
  </div>

  <div class="doc">
    <div class="doc-head"><span>knowledge / business-domain</span><span>ノード7 ・ 図2 ・ 原文1 ・ 121行</span></div>
    <div class="doc-body">

__BD__

    </div>
  </div>
</section>

<section>
  <h2>Ⅲ. domain-expert — 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>業務エキスパートとは誰か</td><td>あり</td><td>要求を出す人、あるいは使う人</td></tr>
        <tr><td class="new">役割 ×3</td><td>原則にまとめて</td><td><strong>代弁者／同じ言葉の源泉／なぜ必要かの対話相手</strong>に分解</td></tr>
        <tr><td class="new">　同じ言葉の源泉である</td><td>一部</td><td><strong>同じ言葉は技術者が作るものではなく、この人たちから採るもの</strong></td></tr>
        <tr><td>設計の専門家ではない</td><td>原則1行</td><td><strong>図。知っていることと知らないことの線引き</strong></td></tr>
        <tr><td class="new">知識の範囲はばらばらでよい</td><td>×</td><td><strong>1人に全部揃っている必要は無い。違うからこそ全体が見える</strong></td></tr>
        <tr><td>間に人を挟まない</td><td>アンチパターン</td><td><strong>図。挟む形と直接話す形の対比</strong>＋判断基準としても立てた</td></tr>
        <tr><td class="new">アンチパターン：設計の判断を求める</td><td>×</td><td>答えられないか、業務の視点から離れた答えが返る</td></tr>
      </tbody>
    </table>
  </div>

  <div class="box ok">
    <h3>注釈で足したもの</h3>
    <p><strong>挟む形（囲み）</strong> ── 間に立つ人が仕事をしていないという意味ではない。<strong>変換そのものが情報を落とすので、誰がやっても同じことが起きる。</strong></p>
    <p><strong>業務エキスパートから「どう実装するか」</strong> ── この線があるのは、そこに期待してはいけないことを示すためである。<strong>知らないのは能力の不足ではなく、役割の範囲である。</strong></p>
    <p><strong>直接話す矢印</strong> ── 片方向に描いてあるが、この関係は双方向である。技術者からの問いが、業務エキスパート自身も気づいていなかった曖昧さを明らかにすることがある。</p>
  </div>

  <div class="doc">
    <div class="doc-head"><span>knowledge / domain-expert</span><span>ノード11 ・ 図2 ・ 134行</span></div>
    <div class="doc-body">

__DE__

    </div>
  </div>
</section>

<section>
  <h2>Ⅳ. 置き換えたもの</h2>
  <p class="narrow">この2本は<strong>実在の企業名がそのまま書かれていた</strong>ので、これまでとは種類の違う置き換えが要りました。</p>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書き起こし版</th><th>置き換え先</th><th>保った構造</th></tr></thead>
      <tbody>
        <tr><td>実在企業4社と、その事業領域</td><td>架空の会社4種（荷物を届ける／喫茶を営む／通販と計算資源の貸出／移動の仲介と料理の配達）</td><td>1社が事業領域を1つ持つ場合と、2つ持つ場合の対比</td></tr>
        <tr><td>実在企業の実際の沿革（製紙 → ゴム → 有線通信 → 無線通信設備）</td><td>架空の沿革（印刷 → 包装材 → 物流の梱包設計）</td><td>創業時とまったく違う事業へ移りうるという主張</td></tr>
        <tr><td>広告代理店の3職種</td><td>配送を担う会社の3職種（集荷の計画・車両の手配・実績の分析）</td><td>知識の範囲が違う複数の人が、合わせて全体をなすこと</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>機械で確認しました</h3>
    <p>実在の企業名4社と実例（広告代理店）を grep して<strong>0件</strong>。</p>
  </div>
</section>

<section>
  <h2>Ⅴ. 13本目までの推移</h2>
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
        <tr><td><strong>business-domain</strong></td><td><strong>79</strong></td><td><strong>121</strong></td><td><strong>58</strong></td></tr>
        <tr><td><strong>domain-expert</strong></td><td><strong>80</strong></td><td><strong>134</strong></td><td><strong>50</strong></td></tr>
        <tr><td><strong>13本の合計</strong></td><td><strong>1,343</strong></td><td><strong>3,611</strong></td><td><strong>3,085</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>13 / 19本。</strong>残り6本・約1,650行です。<strong>第Ⅰ部（土台）と設計編（第4〜10章）が揃いました。</strong>残るのは実践編（イベントストーミング・現場への導入）と、応用編（マイクロサービス・イベント駆動・データメッシュ）、そして締めの経験則です。</p>
</section>

<footer>
  旧要約版159行・書き起こし版108行・変換後255行（描画結果の実測）。<br>
  実在の企業名と、実在企業の実際の沿革は、すべて架空の会社へ置き換えた。示している構造は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__BD__", bd).replace("__DE__", de)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-business-domain-and-expert.html").write_text(
    out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))