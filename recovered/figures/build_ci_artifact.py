"""10本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "context-integration の変換 ── 10本目")
frag = pathlib.Path(f"{S}/ci_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 10本目</span>
  <h1><code>context-integration</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版105行 → <strong>352行</strong>。<code>bounded-context</code> が「文脈どうしをどうつなぐかは別の話」と委ねていた先です。<strong>図8つ</strong>で、これまでで最多になりました。</p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">31</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">8</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">1</span><span class="l">原文（表）</span></div>
    <div class="stat"><span class="n">352</span><span class="l">行（旧105 / 書起し250）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. この本は、6つの方法の「置き場所」が意味を持ちます</h2>
  <p class="narrow">6つの連係方法のうち、モデル変換装置と共用サービスは<strong>やることがほぼ同じ</strong>です。違うのは、誰が変換するかと、どちらの側に置くかの2点だけ。旧版はこれを文章で書いていたので、対称性が見えませんでした。</p>

  <div class="box ok">
    <h3>2つの図を裏返しに描く</h3>
    <p>モデル変換装置は <strong>上流 → 装置 → 下流</strong>、共用サービスは <strong>下流 → 共用サービス → 上流</strong>。注釈で「ちょうど裏返しの位置にある。<strong>変換するのが供給する側か使う側か、置き場所が上流か下流か、この2点だけが両者の違い</strong>」と名指ししています。</p>
  </div>

  <div class="box bad">
    <h3>旧版は「文脈の地図」を実例1件で済ませていました</h3>
    <p>地図から何が読み取れるか（全体の設計・意図の伝わり方・組織上の課題）、最新に保つ方法、そして<strong>地図の限界</strong>——1本の線が1つの連係方法とは限らない——が丸ごと落ちていました。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>なぜ連係の取り決めが要るか</td><td>原則1行</td><td>モデルも言葉も違うから</td></tr>
        <tr><td class="new">連係方法は3つのグループに分かれる</td><td>分類のみ</td><td><strong>図。分ける基準は技術ではなく協力の度合い</strong></td></tr>
        <tr><td>良きパートナー</td><td>分類1行</td><td><strong>図</strong>＋成立条件・離れたチームでは難しい</td></tr>
        <tr><td>モデルの共有</td><td>分類1行</td><td><strong>図</strong>＋子4つ</td></tr>
        <tr><td class="new">　共有する範囲</td><td>アンチパターンに1つ</td><td>理想は契約と、境界を越えるデータの形だけ</td></tr>
        <tr><td class="new">　どう実現するか</td><td><strong>×</strong></td><td><strong>同じ置き場／独立した部品。どちらでも結合の確認を自動で</strong></td></tr>
        <tr><td class="new">　共有するかどうか</td><td>×</td><td><strong>重複の負担と調整の負担を比べる。中核ほど共有は高くつく</strong></td></tr>
        <tr><td class="new">　これは例外的な方法である</td><td><strong>×</strong></td><td><strong>1文脈1チームの原則と矛盾する。使ってよい3状況</strong></td></tr>
        <tr><td>使う側と供給する側の関係</td><td>原則1行</td><td><strong>図。力関係が生まれる構造</strong></td></tr>
        <tr><td>従属する</td><td>分類1行</td><td>下流が選ぶ2つの理由つき</td></tr>
        <tr><td>モデル変換装置</td><td>分類1行</td><td><strong>図</strong>＋使う3場面と効果</td></tr>
        <tr><td>共用サービス</td><td>分類1行</td><td><strong>図</strong>＋子2つ</td></tr>
        <tr><td class="new">　公開された言葉</td><td>×</td><td><strong>内部の同じ言葉に合わせる必要は無い。複数の版を並べられる</strong></td></tr>
        <tr><td class="new">　モデル変換装置との違い</td><td>×</td><td><strong>誰が変換するか・どこに置くか、の2点だけ</strong></td></tr>
        <tr><td>互いに独立</td><td>分類1行</td><td>子4つ</td></tr>
        <tr><td class="new">　意思疎通が難しい／一般的な業務領域／モデルの違いが大きい</td><td>×</td><td>選ぶ理由が3つに分かれる</td></tr>
        <tr><td>　中核どうしには使わない</td><td>アンチパターン</td><td>判断基準としても立てた</td></tr>
        <tr><td class="new">文脈の地図</td><td>実例1件</td><td><strong>図</strong>＋子3つ</td></tr>
        <tr><td class="new">　地図から見えるもの</td><td>×</td><td>全体の設計・意図の伝わり方・組織上の課題</td></tr>
        <tr><td class="new">　最新の状態を保つには</td><td>×</td><td>全チーム共同。各チームが自分の連係を反映する責任</td></tr>
        <tr><td class="new">　地図の限界</td><td><strong>×</strong></td><td><strong>1本の線が1つの方法とは限らない</strong></td></tr>
        <tr><td class="new">6つの連係方法の対比</td><td>分類</td><td>表。決定権・協力の度合い・主な用途</td></tr>
        <tr><td>どの連係方法を選ぶか</td><td>判断基準</td><td><strong>図</strong></td></tr>
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
        <tr><td>3つのグループ</td><td>3つの囲み</td><td>協力の度合いが下がる並びだが、<strong>上ほど良いという意味ではない</strong></td></tr>
        <tr><td>良きパートナー</td><td>2本の矢印</td><td>行き来があることではなく、<strong>どちらにも決定権があること</strong>を表す。他の方法ではこの2本のどちらかが消える</td></tr>
        <tr><td>使う側と供給する側</td><td>上流から下流の矢印</td><td><strong>サービスが流れる向きであって、決定権の向きではない</strong></td></tr>
        <tr><td>共用サービス</td><td>共用サービス</td><td>モデル変換装置と<strong>ちょうど裏返しの位置</strong>にある</td></tr>
        <tr><td>文脈の地図</td><td>配送の文脈から出る2本</td><td>1つのチームが<strong>すべての相手に変換装置を作っている形</strong>が見えたら、相手側のモデルに問題があるという合図。<strong>個々の線ではなく線の集まり方に意味がある</strong></td></tr>
        <tr><td>選び方</td><td>互いに独立</td><td>他の終点と違い<strong>条件つきの終点</strong>。中核どうしには選べない</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された352行を、<strong>省略なしで</strong>並べています。31ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / context-integration</span><span>ノード31 ・ 図8 ・ 原文1</span></div>
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
        <tr><td>実在の道具の名前（地図をコードとして管理する道具）</td><td>役割の説明</td><td>地図をコードとして管理できる、という事実</td></tr>
        <tr><td>文脈の地図の図（書き起こし版に中身が無かった）</td><td>架空の業務で組み立て（受注・在庫・請求・配送・記録）</td><td>読み取る観点——同じ相手へ変換装置が集まる形、孤立した文脈——を再現できる配置にした</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>ここは補完であることを明記しました</h3>
    <p>文脈の地図の例は<strong>書き起こし版に図の中身が残っていなかった</strong>ため、こちらで組み立てています。留保事項にその旨を書きました。読み取る観点は本文に書かれていたので、それが成り立つ配置を選んでいます。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 10本目までの推移</h2>
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
        <tr><td><strong>context-integration</strong></td><td><strong>105</strong></td><td><strong>352</strong></td><td><strong>250</strong></td></tr>
        <tr><td><strong>10本の合計</strong></td><td><strong>1,070</strong></td><td><strong>3,053</strong></td><td><strong>2,743</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>10 / 19本で折り返しました。</strong>残り9本・約2,000行です。</p>
</section>

<footer>
  旧要約版105行・書き起こし版250行・変換後352行（描画結果の実測）。<br>
  実在の道具名は役割の説明へ置き換えた。文脈の地図の例は書き起こし版に中身が無いため補完し、留保事項に明記した。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-context-integration.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))