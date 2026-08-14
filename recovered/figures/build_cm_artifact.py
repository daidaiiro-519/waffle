"""11本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "communication の変換 ── 11本目")
frag = pathlib.Path(f"{S}/cm_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 11本目</span>
  <h1><code>communication</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版114行 → <strong>303行</strong>。<code>context-integration</code> が「モデル変換装置の実装方法は次章」と委ね、<code>architecture-patterns</code> も末尾でここへ送っていた先です。</p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">25</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">5</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">3</span><span class="l">原文（表2・C#1）</span></div>
    <div class="stat"><span class="n">303</span><span class="l">行（旧114 / 書起し234）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 送信箱は「描かれていない線」が主張です</h2>
  <p class="narrow">送信箱の図には <strong>アプリケーション → メッセージの通信基盤</strong> の線がありません。これは省略ではなく、<strong>そう書いてはいけないという規則そのもの</strong>です。図だけ見ると気づけないので、注釈で名指ししました。</p>

  <div class="box ok">
    <h3>注釈に書いたこと</h3>
    <p><strong>アプリケーション</strong> ── メッセージの通信基盤へ直接つながる線が無い。描き忘れではなく、集約の内部から直接発行してはいけないという規則がある。</p>
    <p><strong>アプリケーションからデータベース</strong> ── この1本がひと塊の変更になっていることが、この形が成り立つ唯一の条件である。状態だけ書けてイベントが書けない、という中途半端な結果が起きない。</p>
    <p><strong>中継する役からメッセージの通信基盤</strong> ── 送ったあとに印をつけるまでのあいだに落ちると、同じイベントをもう一度送る。この形が保証するのは「少なくとも1回」までで、受け取る側は同じものが二度来ても平気なように作る必要がある。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>この概念が扱う範囲</td><td>概要</td><td>境界を越えたつなぎ方に限る、と明示</td></tr>
        <tr><td>モデルの変換</td><td>原則1行</td><td>装置と共用サービスを区別せず扱う理由つき</td></tr>
        <tr><td class="new">　状態を持たない変換：同期</td><td>×</td><td><strong>図。行きも返りも変換する</strong></td></tr>
        <tr><td class="new">　状態を持たない変換：非同期</td><td>×</td><td><strong>図。内部のイベントと外向けのイベントを分ける位置</strong></td></tr>
        <tr><td>　内部のモデルをそのまま外へ出さない</td><td>アンチパターン</td><td>判断基準としても立てた</td></tr>
        <tr><td class="new">　状態を持つ変換</td><td><strong>×</strong></td><td><strong>子2つ。まとめる／複数の発生元を統合する</strong></td></tr>
        <tr><td>送信箱</td><td>分類1行</td><td><strong>図</strong>＋子3つ。直接発行してはいけない2つの理由つき</td></tr>
        <tr><td class="new">　どこへ書くか</td><td>×</td><td>表を持つDB／持たないDBで書き方が変わる</td></tr>
        <tr><td class="new">　まだ送っていないイベントをどう読むか</td><td>×</td><td>繰り返し探す／変更の記録を追う</td></tr>
        <tr><td class="new">　同じものが二度届く</td><td>×</td><td><strong>保証は「少なくとも1回」まで。受け手側の作りが要る</strong></td></tr>
        <tr><td>サーガ</td><td>分類1行</td><td><strong>コード</strong>＋子2つ。「長く続く」は時間ではなく塊の数</td></tr>
        <tr><td class="new">　一貫性の前提</td><td>×</td><td><strong>集約の内側は強く整合、外側は結果的に整合</strong></td></tr>
        <tr><td>　境界の不備を補うために使わない</td><td>アンチパターン</td><td>判断基準としても立てた</td></tr>
        <tr><td>プロセスマネージャー</td><td>分類1行</td><td><strong>図</strong>＋対比表</td></tr>
        <tr><td class="new">　サーガとの違い</td><td>×</td><td><strong>表。複雑さ・起動・状態・枝分かれの4観点</strong></td></tr>
        <tr><td class="new">5つの形の対比</td><td>×</td><td>表。後半2つの土台は送信箱</td></tr>
        <tr><td>サーガかプロセスマネージャーか</td><td>判断基準</td><td><strong>図</strong></td></tr>
        <tr><td>アンチパターン ×3</td><td>あり</td><td>そのまま維持</td></tr>
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
        <tr><td>同期の変換</td><td>代理役</td><td><strong>どちら側に置くかはこの図では決まらない。</strong>上流が置けば共用サービス、下流が置けばモデル変換装置</td></tr>
        <tr><td>非同期の変換</td><td>内部のイベント／外向けのイベント</td><td>2つを分ける線が要点。<strong>内部のモデルをそのまま外へ出すのはよくある誤った設計</strong></td></tr>
        <tr><td>プロセスマネージャー</td><td>明示的に起動する</td><td><strong>サーガとの決定的な違いがこの1本。</strong>サーガは特定の出来事を見つけて勝手に動き出す</td></tr>
        <tr><td>プロセスマネージャー</td><td>相手1／相手2／相手3</td><td>同時に指示を出すという意味ではない。<strong>どれへいつ指示を出すかを決めるのが仕事で、そこに業務ロジックが入る</strong></td></tr>
        <tr><td>選び方</td><td>サーガ</td><td>選ぶ前にもう1つ確認がある。<strong>集約の境界の不備を補うために使おうとしていないか</strong></td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された303行を、<strong>省略なしで</strong>並べています。25ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / communication</span><span>ノード25 ・ 図5 ・ 原文3</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅴ. 置き換えたもの</h2>
  <p class="narrow">この本は書き起こし版に<strong>実在の製品名が12個</strong>並んでいました。これまでで最多です。</p>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書き起こし版</th><th>置き換え先</th><th>保った内容</th></tr></thead>
      <tbody>
        <tr><td>外部との入口を担う製品 ×5</td><td>「外部との入口を担う一般的な仕組み」</td><td>低い費用で実現できること、独立した文脈として立てられること</td></tr>
        <tr><td>データを流し続ける製品 ×2 / ためて処理する製品 ×3</td><td>「流れ続けるデータとして扱う仕組み／ためてから一括で処理する仕組み」</td><td>2通りのやり方があるという分岐</td></tr>
        <tr><td>変更の記録を追う仕組みの製品 ×2</td><td>「データベース側の変更の記録を追いかける形」</td><td>繰り返し探す形との対比</td></tr>
        <tr><td>広告キャンペーンの掲載（サーガのコード）</td><td>配送の集荷手配</td><td>3つの出来事に1対1で処理が対応し、<strong>条件による枝分かれが1つも無い</strong>という構造</td></tr>
        <tr><td>画面向けの中継層を指す略語</td><td>「画面が複数のサービスからデータを集めて組み立てる状況」</td><td>典型例としての位置づけ</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>機械で確認しました</h3>
    <p>実在の製品名12個と書籍の実例（広告キャンペーン）を grep して<strong>0件</strong>。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 11本目までの推移</h2>
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
        <tr><td><strong>communication</strong></td><td><strong>114</strong></td><td><strong>303</strong></td><td><strong>234</strong></td></tr>
        <tr><td><strong>11本の合計</strong></td><td><strong>1,184</strong></td><td><strong>3,356</strong></td><td><strong>2,977</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>11 / 19本。</strong>残り8本・約1,750行です。<strong>設計編（第4〜10章）がこれで揃いました。</strong></p>
</section>

<footer>
  旧要約版114行・書き起こし版234行・変換後303行（描画結果の実測）。<br>
  実在の製品名12個は役割の説明へ、実例は架空の業務へ置き換えた。図が示す位置関係と、描かれていない線の意味は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-communication.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))