"""8本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("design-heuristics の変換 ── 7本目",
                    "architecture-patterns の変換 ── 8本目")
frag = pathlib.Path(f"{S}/ap_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 8本目</span>
  <h1><code>architecture-patterns</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版104行 → <strong>349行</strong>。<strong>3.4倍</strong>で、これまでで最大の増分です。7本目の <code>design-heuristics</code> が技術方式の詳細をここへ委ねていたので、その受け皿が揃いました。</p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">24</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">6</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">6</span><span class="l">原文（表5・C#1）</span></div>
    <div class="stat"><span class="n">349</span><span class="l">行（旧104 / 書起し268）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 旧版は「原則8項目」で3つの方式を語っていました</h2>
  <p class="narrow">旧版の見出しは<strong>7つだけ</strong>（概要・原則・分類・判断基準・実例・アンチパターン・関連概念）。3つの技術方式それぞれの中身が、原則の箇条書き8項目に押し込まれていました。</p>

  <div class="box bad">
    <h3>依存の向きが、文章1行になっていました</h3>
    <p>旧版は<strong>「依存の向きをレイヤードから逆転させることで、業務ロジックを基盤コンポーネントから独立させる」</strong>の1行。何から何への向きが、どう変わるのかは書かれていません。</p>
    <p>この概念の核心は<strong>矢印1本の向き</strong>です。文章にすると、読み手はそれを図に起こし直さないと理解できません。</p>
  </div>

  <div class="box ok">
    <h3>2つの図を並べて、その1本を見せる</h3>
    <p>レイヤードの図で<strong>業務ロジック層 → データアクセス層</strong>を描き、注釈に「この向きがこの方式の弱点にあたる。ポートとアダプターは、ここだけを逆にする」と書く。ポートとアダプターの図では<strong>アダプター → ポート</strong>だけが外から中へ向かい、注釈で「この1本だけが外から中へ向かう」と名指しする。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>技術方式とは何か</td><td>原則2行</td><td>定義として1ノードに集約</td></tr>
        <tr><td>レイヤードアーキテクチャ</td><td>原則1行＋分類1行</td><td><strong>図</strong>＋子5つ</td></tr>
        <tr><td class="new">　3つの層</td><td>×</td><td><strong>表。層ごとの別名と役割</strong></td></tr>
        <tr><td>　層のあいだの通信</td><td>原則に一部</td><td>層を飛ばして依存しない、を独立させた</td></tr>
        <tr><td class="new">　サービス層</td><td><strong>×</strong></td><td><strong>図。物理的に独立したサービスではない</strong></td></tr>
        <tr><td class="new">　層と段の違い</td><td><strong>×</strong></td><td><strong>表。論理の境界と物理の境界。層数と段数は一致しない</strong></td></tr>
        <tr><td class="new">　いつ使うか</td><td>×</td><td>ドメインモデルに向かない理由つき</td></tr>
        <tr><td>ポートとアダプター</td><td>原則2行＋分類1行</td><td><strong>図</strong>＋子3つ</td></tr>
        <tr><td class="new">　依存の向きを逆にする</td><td>原則1行</td><td><strong>＋コード（ポートとアダプターの分かれ方）</strong></td></tr>
        <tr><td class="new">　同じものを指す別の呼び名</td><td>括弧書き</td><td>表。3種類の呼び分け</td></tr>
        <tr><td class="new">　いつ使うか</td><td>×</td><td>基盤から独立させたい場合</td></tr>
        <tr><td>CQRS</td><td>原則1行＋分類1行</td><td>子5つ</td></tr>
        <tr><td class="new">　なぜ複数のモデルが要るか</td><td>×</td><td>1つのモデルで全要求に応えるのは難しい</td></tr>
        <tr><td class="new">　2つのモデル</td><td>一部</td><td><strong>表。強い一貫性・競合の扱い・複製の位置づけ</strong></td></tr>
        <tr><td class="new">　読み取りモデルの作り方</td><td><strong>×</strong></td><td><strong>図。同期と非同期。同期から始める</strong></td></tr>
        <tr><td class="new">　コマンドはデータを返せる</td><td><strong>×</strong></td><td><strong>よくある誤解の訂正。ただし元はコマンド実行モデル</strong></td></tr>
        <tr><td class="new">　いつ使うか</td><td>一部</td><td>イベント履歴式では必須になる理由つき</td></tr>
        <tr><td class="new">技術方式が及ぶ範囲</td><td><strong>×</strong></td><td><strong>図。1つの文脈の中で業務領域ごとに混在させてよい</strong></td></tr>
        <tr><td class="new">3つの対比</td><td>分類3項目</td><td>表として整理</td></tr>
        <tr><td>どの技術方式を選ぶか</td><td>判断基準</td><td><strong>図</strong></td></tr>
        <tr><td>アンチパターン ×3</td><td>あり</td><td>そのまま維持</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅲ. 注釈の例</h2>
  <p class="narrow">6つの図それぞれに、図の要素を名指しした注釈を付けています。</p>
  <div class="tablewrap">
    <table>
      <thead><tr><th>図</th><th>どこの話か</th><th>図に載せきれないこと</th></tr></thead>
      <tbody>
        <tr><td>レイヤード</td><td>2本の矢印</td><td>層を1つ飛ばして下へ向かう線を描いていないのは、<strong>描き忘れではなく規則</strong></td></tr>
        <tr><td>ポートとアダプター</td><td>ポート（抽象）</td><td>中心側に置いてあるのは、<strong>抽象を定義するのが業務ロジック層だから</strong>。外側が「こう呼んでほしい」と決めるのではない</td></tr>
        <tr><td>読み取りモデル</td><td>同期で作る／非同期で作る</td><td>選択肢だが<strong>対等ではない</strong>。同期から始め、非同期は要求が出てから足す</td></tr>
        <tr><td>及ぶ範囲</td><td>1つの区切られた文脈</td><td>囲みの中に線が1本も無いが、<strong>無関係という意味ではない</strong>。この図は割り当てだけを示す</td></tr>
        <tr><td>選び方</td><td>レイヤードへ入る2本</td><td>同じ終点に見えるが<strong>層の数が違う</strong>（3層と4層）</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された349行を、<strong>省略なしで</strong>並べています。24ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / architecture-patterns</span><span>ノード24 ・ 図6 ・ 原文6</span></div>
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
        <tr><td>広告配信の区切られた文脈（4つの業務領域）</td><td>配送手配の区切られた文脈（料金の最適化・集荷の受付・荷姿のカタログ・経路の最適化）</td><td>1つの文脈に4領域、技術方式は3種類が混在（同じ方式が2回出る）</td></tr>
        <tr><td>実在のメッセージ基盤を含むコード例</td><td>役割を表す一般的な名前（<code>IEventPublisher</code> / <code>QueueEventPublisher</code>）</td><td>抽象を業務ロジック層に、具体をインフラ層に置く分かれ方</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>機械で確認しました</h3>
    <p>書籍固有の語（販売促進・広告・キャンペーン・実在の基盤名）を grep して<strong>0件</strong>。「ヘキサゴナル／オニオン／クリーン」は業界で通用する別名の一覧なので残しています。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 8本目までの推移</h2>
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
        <tr><td><strong>architecture-patterns</strong></td><td><strong>104</strong></td><td><strong>349</strong></td><td><strong>268</strong></td></tr>
        <tr><td><strong>8本の合計</strong></td><td><strong>858</strong></td><td><strong>2,200</strong></td><td><strong>2,085</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>8 / 19本</strong>。残り11本・約2,600行です。</p>
</section>

<footer>
  旧要約版104行・書き起こし版268行・変換後349行（描画結果の実測）。<br>
  実例は架空の業務へ置き換え、実在の基盤名は役割を表す名前に置き換えた。図が示す依存の向きと分岐の構造は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-architecture-patterns.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))