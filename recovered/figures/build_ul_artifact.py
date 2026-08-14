"""6本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "ubiquitous-language の変換 ── 6本目")
frag = pathlib.Path(f"{S}/ul_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 6本目</span>
  <h1><code>ubiquitous-language</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版99行 → <strong>240行</strong>。書き起こし版177行を超えました。<strong>今日の語彙の議論の出どころ</strong>——一語一義・同義語を使わない・言語化されていない知識へどうたどりつくか——がすべて戻っています。</p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">23</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">+15</span><span class="l">旧要約版で落ちていた節</span></div>
    <div class="stat"><span class="n">3</span><span class="l">図</span></div>
    <div class="stat"><span class="n">2</span><span class="l">原文（表1・記法1）</span></div>
    <div class="stat"><span class="n">240</span><span class="l">行（旧99 / 書起し177）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 今日の議論に、何度も出てきた基準です</h2>

  <div class="box ok">
    <h3>「同義語を作らない」の正確な形</h3>
    <p>ddd が今日、<code>sd-document-management</code> の「取り下げ」と <code>sd-schema-management</code> の「除去」を<strong>同義語の乱立</strong>だと指摘しました。その根拠がこの節です。</p>
    <p>ただし片側だけではありません——<strong>「意図が異なるなら、あえて別の用語を使う」</strong>とも書かれています。「利用者」「訪問者」「管理者」「会員」は技術的には同じ利用者でも、<strong>行動・データ・機能が異なるなら別の用語として扱う</strong>。統一と分離のどちらへ倒すかは、意図の違いで決まります。</p>
  </div>

  <div class="box ok">
    <h3>言語化されていない知識へたどりつく唯一の方法</h3>
    <p>「重要な業務知識の多くは言語化されておらず、業務エキスパートの頭の中だけにある。たどりつく唯一の方法は<strong>質問すること</strong>」。そして質問は一方通行ではなく、<strong>業務エキスパート自身が気づいていなかった曖昧さや未定義の概念を明らかにする</strong>——とくに中核の業務領域で起きやすい、と続きます。</p>
    <p>今日、私が語彙を勝手に発明して2度差し戻された場面がありました。この節は、その代わりに何をすべきだったかを述べています。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>同じ言葉とは</td><td>あり</td><td>関係者全員が使う単一の言語</td></tr>
        <tr><td class="new">なぜ必要か</td><td>×</td><td>子2つ。翻訳のたびに意図が変質する</td></tr>
        <tr><td class="new">　人を介するたびに意図が変質する</td><td>×</td><td>図2-1。往復でずれが積み上がる</td></tr>
        <tr><td class="new">　モデルの変換のたびに情報が欠落する</td><td>×</td><td>図2-2。3回の変換</td></tr>
        <tr><td>3つのルール</td><td>一部</td><td>子3つに分解</td></tr>
        <tr><td>　業務用語のみで構成する</td><td>あり</td><td>技術用語を含めない</td></tr>
        <tr><td class="new">　一貫性（一語一義）</td><td>一部</td><td>＋あいまいな用語を分解する例（表）</td></tr>
        <tr><td class="new">　<strong>同義語を使わない</strong></td><td>一部</td><td><strong>意図が異なるならあえて別の用語を使う</strong></td></tr>
        <tr><td class="new">この用語は同じ言葉として適切か</td><td>×</td><td>3つの問い（図）</td></tr>
        <tr><td class="new">業務の言葉と技術の言葉</td><td>×</td><td>同じことを述べても別物になる</td></tr>
        <tr><td class="new">継続的に取り組む</td><td>×</td><td>一度作ったら終わりではない</td></tr>
        <tr><td class="new">道具の利用</td><td><strong>×</strong></td><td>子3つ。用語の場所・読める記法・検査</td></tr>
        <tr><td class="new">　用語をまとめる場所</td><td>×</td><td><strong>全員が更新できること。振る舞いは表現できない</strong></td></tr>
        <tr><td class="new">　振る舞いを読める形で書く記法</td><td>×</td><td>業務エキスパートは読めるだけ、書けはしない</td></tr>
        <tr><td class="new">　使われ方を検査する仕組み</td><td>×</td><td>ソースコードでの一貫性を見る</td></tr>
        <tr><td class="new">困難に立ち向かう</td><td><strong>×</strong></td><td>子3つ</td></tr>
        <tr><td class="new">　<strong>言語化されていない知識へたどりつく</strong></td><td><strong>×</strong></td><td><strong>唯一の方法は質問すること</strong></td></tr>
        <tr><td class="new">　既存のシステムへ取り込む</td><td>×</td><td>基本手段は忍耐。動かしやすい場所から</td></tr>
        <tr><td class="new">　言語の選択</td><td>×</td><td>コード上の名前と業務の名前の対応づけ</td></tr>
        <tr><td>アンチパターン ×3</td><td>あり</td><td>翻訳を挟む／コードだけ／あいまいなままモデル化</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅲ. 完全プレビュー</h2>
  <p class="narrow">描画された240行を、<strong>省略なしで</strong>並べています。23ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / ubiquitous-language</span><span>ノード23 ・ 図3 ・ 原文2</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅳ. 置き換えたもの</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書籍の題材</th><th>置き換え先</th><th>保った構造</th></tr></thead>
      <tbody>
        <tr><td>Policy（統制ルール／保険契約）</td><td>区分（荷姿区分／料金区分）</td><td>1語が2つの意味を持つ状態と、分解した状態の対比</td></tr>
        <tr><td>広告キャンペーン管理システムの例</td><td>配送の依頼の例</td><td>業務側の表現と技術側の表現が別物になること</td></tr>
        <tr><td>人名を含む記法の例</td><td>荷主・担当者（役割で表す）</td><td>前提・操作・結果の3つで書く形</td></tr>
        <tr><td>実在ツールの製品名 ×3</td><td>役割の説明（用語をまとめる場所／読める記法／検査する仕組み）</td><td>3種類の道具とそれぞれの限界</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>機械で確認しました</h3>
    <p>書籍固有の語（Policy・保険契約・広告キャンペーン・iframe・実在ツール名・人名・コンバージョン・販売報奨金）を grep して<strong>0件</strong>。</p>
  </div>
</section>

<section>
  <h2>Ⅴ. 気づいたこと</h2>
  <div class="box bad">
    <h3>書き起こし版より長くなりました</h3>
    <p>177行に対して240行。図に<strong>意図・読み取り・関係の表</strong>を添えたぶんと、本文に埋もれていたものを独立したノードとして立てたぶんです。<code>subdomain</code> でも同じことが起きています（222行→279行）。<strong>粒度を保つと、多くの場合は長くなります</strong>。</p>
  </div>
  <div class="tablewrap">
    <table>
      <thead><tr><th>本</th><th>旧要約版</th><th>変換後</th><th>書き起こし版</th></tr></thead>
      <tbody>
        <tr><td>subdomain</td><td>112</td><td>279</td><td>222</td></tr>
        <tr><td>bounded-context</td><td>93</td><td>191</td><td>291</td></tr>
        <tr><td>domain-model</td><td>112</td><td>382</td><td>431</td></tr>
        <tr><td>business-logic-simple</td><td>107</td><td>209</td><td>210</td></tr>
        <tr><td>evolving-design</td><td>111</td><td>277</td><td>283</td></tr>
        <tr><td>ubiquitous-language</td><td>99</td><td>240</td><td>177</td></tr>
        <tr><td><strong>6本の合計</strong></td><td><strong>634</strong></td><td><strong>1,578</strong></td><td><strong>1,614</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>6 / 19本</strong>。残り13本・約3,100行です。</p>
</section>

<footer>
  旧要約版99行・書き起こし版177行・変換後240行（描画結果の実測）。<br>
  実例は架空の業務へ置き換え、実在の製品名は役割の説明に置き換えた。図が示す関係の構造は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-ubiquitous-language.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))
