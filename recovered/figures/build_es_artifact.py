"""9本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "event-sourced-domain-model の変換 ── 9本目")
frag = pathlib.Path(f"{S}/es_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 9本目</span>
  <h1><code>event-sourced-domain-model</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版107行 → <strong>501行</strong>。<strong>4.7倍</strong>で、これまでで最大です。書き起こし版408行も上回りました。実装方法の系列（手続き → ドメインモデル → イベント履歴式）が、これで揃いました。</p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">36</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">5</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">9</span><span class="l">原文（C#7・JSON1・表1）</span></div>
    <div class="stat"><span class="n">501</span><span class="l">行（旧107 / 書起し408）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. 旧版が落としていたもの</h2>
  <p class="narrow">旧版の見出しは7つ。原則の箇条書きと分類だけで、<strong>この方式が実際にどう動くのかを示すものが1つもありませんでした。</strong></p>

  <div class="box bad">
    <h3>4つの手順が無い</h3>
    <p>イベント履歴式の集約への操作は <strong>読み込む → 状態を作り直す → コマンドを実行してイベントを生む → 書き戻す</strong> の4手順を踏みます。旧版にはこの手順がありません。手順が無いと、従来のドメインモデルとの違い（2番目と4番目が加わること）も言えません。</p>
  </div>

  <div class="box bad">
    <h3>「よくある質問」が丸ごと無い</h3>
    <p>性能・規模・削除・代替手段の4節、計7ノードぶんが落ちていました。とくに<strong>「追記だけなのに削除を求められたらどうするか」</strong>は、この方式を採用してよいかの判断に直結します。</p>
  </div>

  <div class="box ok">
    <h3>1つの履歴から3つの投影</h3>
    <p>この本の中心は<strong>同じ履歴に別の変換を当てれば別の状態が得られる</strong>ことで、書き起こし版はそれをコード3本（最新状態・検索・分析）で見せています。旧版はコードを全部落としていたので、この主張が「後から新しい見方を足せる」という一文だけになっていました。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>イベント履歴式ドメインモデルとは</td><td>原則2行</td><td>違うのは何を保存するかの一点だけ</td></tr>
        <tr><td class="new">　この呼び名を選ぶ理由</td><td>×</td><td>集約の一生の状態管理に限った適用だから</td></tr>
        <tr><td>イベントの履歴を保存する</td><td>原則1行</td><td>子6つ</td></tr>
        <tr><td class="new">　履歴の例</td><td>×</td><td><strong>原文。受付から支払完了まで7件</strong></td></tr>
        <tr><td class="new">　投影</td><td>×</td><td><strong>コード。版番号が過去の再現を可能にする</strong></td></tr>
        <tr><td class="new">　検索のための投影</td><td>×</td><td>コード。上書きせず足すだけで古い値も残る</td></tr>
        <tr><td class="new">　分析のための投影</td><td>×</td><td>コード。あらかじめ数えておかなくてよい</td></tr>
        <tr><td class="new">　真実を語る唯一の拠り所</td><td>用語のみ</td><td><strong>図。集約とイベントストアの往復</strong></td></tr>
        <tr><td class="new">　イベントストア</td><td>×</td><td><strong>コード。追記専用・期待する版番号で競合を検出</strong></td></tr>
        <tr><td class="new">集約への操作の手順</td><td><strong>×</strong></td><td><strong>図＋コード3本（アプリケーション層・集約・状態クラス）</strong></td></tr>
        <tr><td>利点 ×4</td><td>原則に2つ</td><td>過去の再現・新しい見方・監査の記録・<strong>競合の判定を業務の視点で</strong></td></tr>
        <tr><td>欠点 ×3</td><td>一部</td><td>学ぶ時間・モデルの変えにくさ・仕組みの複雑さ</td></tr>
        <tr><td class="new">よくある質問</td><td><strong>×</strong></td><td><strong>子4つ（うち1つはさらに子3つ）</strong></td></tr>
        <tr><td class="new">　イベントが増えると遅くならないか</td><td>×</td><td><strong>図。ただし1万を超える集約はほぼ無い。先に境界を見直す</strong></td></tr>
        <tr><td class="new">　規模を大きくできるか</td><td>×</td><td>図。集約の識別子で区画を分けられる</td></tr>
        <tr><td class="new">　追記だけなのに、削除を求められたら</td><td><strong>×</strong></td><td><strong>暗号化して、鍵のほうを消す</strong></td></tr>
        <tr><td class="new">　他のやり方ではだめか</td><td>×</td><td>子3つ。ファイル・同時書き込み・自動複製</td></tr>
        <tr><td class="new">4つの実装方法の対比</td><td>×</td><td>表。保存するものと対象領域</td></tr>
        <tr><td>使うか</td><td>判断基準</td><td><strong>図。チームの経験だけ性質が違う分岐</strong></td></tr>
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
        <tr><td>イベントストア</td><td>新しいイベントからイベントストア</td><td>他の線と同じ矢印に見えるが、<strong>この線だけが一方通行で取り消せない</strong></td></tr>
        <tr><td>イベントストア</td><td>イベントストアから集約</td><td>読むのは履歴の全部。<strong>状態はどこにも保存されておらず、毎回この線の上で作り直される</strong></td></tr>
        <tr><td>4つの手順</td><td>コマンドを実行し、業務イベントを生む</td><td><strong>状態を直接書き換えないのが核心。</strong>イベントを生み、その適用の結果として状態が変わる</td></tr>
        <tr><td>控えの置き場</td><td>控えの置き場</td><td>真実の拠り所ではない。<strong>捨てても履歴から作り直せる</strong></td></tr>
        <tr><td>使うか</td><td>チームに経験があるか</td><td>他と性質が違う。<strong>技術的な適合ではなく導入の是非を左右する条件</strong>。「いいえ」でも採用してよい</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された501行を、<strong>省略なしで</strong>並べています。36ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / event-sourced-domain-model</span><span>ノード36 ・ 図5 ・ 原文9</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅴ. 置き換えたもの</h2>
  <p class="narrow">この本は書き起こし版の時点で実例が多く、これまでで最も置き換えが要りました。</p>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書き起こし版</th><th>置き換え先</th><th>保った構造</th></tr></thead>
      <tbody>
        <tr><td>見込み客の履歴（実在しそうな人名・電話番号）</td><td>配送の依頼の履歴（法人名・伏せた番号）</td><td>受付 → 連絡 → 予定を置く → 連絡先の変更 → 連絡 → 引受 → 支払完了 の7件。<strong>連絡先が途中で変わる</strong>ことが検索の投影の要点なので、その位置は動かしていない</td></tr>
        <tr><td>サポートのチケットとエスカレーション</td><td>配送の依頼と優先扱いへの引き上げ</td><td>コマンド実行時の条件（すでに引き上げ済みでないこと・残り時間が尽きていること）</td></tr>
        <tr><td>特定の法令の名称</td><td>その法令が求める内容の説明</td><td>「追記しかできない置き場から、情報を消せるか」という問いの形</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>機械で確認しました</h3>
    <p>書籍固有の語（見込み客・人名・電話番号・チケット・エスカレーション・法令名）を grep して<strong>0件</strong>。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 9本目までの推移</h2>
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
        <tr><td><strong>event-sourced-domain-model</strong></td><td><strong>107</strong></td><td><strong>501</strong></td><td><strong>408</strong></td></tr>
        <tr><td><strong>9本の合計</strong></td><td><strong>965</strong></td><td><strong>2,701</strong></td><td><strong>2,493</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>9 / 19本</strong>。残り10本・約2,200行です。<strong>業務ロジックの実装方法の系列（第5〜8章）と、設計の経験則（第10章）が揃いました。</strong></p>
</section>

<footer>
  旧要約版107行・書き起こし版408行・変換後501行（描画結果の実測）。<br>
  実例は架空の業務へ置き換え、人名は法人名に、法令の名称はその内容の説明に置き換えた。コードが示す構造は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-event-sourced-domain-model.html").write_text(
    out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))