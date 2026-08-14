"""14本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "event-storming の変換 ── 14本目")
frag = pathlib.Path(f"{S}/ev_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 14本目</span>
  <h1><code>event-storming</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版108行 → <strong>301行</strong>。<code>domain-expert</code> から自然に続く実践編です。<strong>10の段が、旧版では判断基準の箇条書き数行に潰れていました。</strong></p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">26</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">5</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">2</span><span class="l">原文（表）</span></div>
    <div class="stat"><span class="n">301</span><span class="l">行（旧108 / 書起し262）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. この本は「手順書」なので、段が落ちると使えません</h2>
  <p class="narrow">これまで変換した13本は考え方を述べる本でした。この本だけは<strong>実際に場を開いて回すための手順書</strong>で、10の段それぞれに「何を出すか」「何色で書くか」「どこに貼るか」が決まっています。</p>

  <div class="box bad">
    <h3>旧版に残っていたのは判断基準3つだけ</h3>
    <p>「実施すべきか」「初回は何段か」「何人呼ぶか」。<strong>肝心の10の段が1つも無い</strong>ので、この文書を読んでも場を開けません。要素の見分け方（付箋の色と形の対応）も落ちていました。</p>
  </div>

  <div class="box ok">
    <h3>順序そのものが主張です</h3>
    <p>10の段は、1種類ずつ要素を足していく積み上げになっています。注釈で名指ししました ── <strong>「10. 区切られた文脈に分ける」</strong> が最後に来るのが要点である。境界を先に決めてから中身を並べるのではなく、<strong>並べ終えた結果として境界が浮かび上がる。</strong></p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>イベントストーミングとは何か</td><td>概要</td><td><strong>価値は成果物ではなく活動そのもの</strong></td></tr>
        <tr><td class="new">誰が参加するか</td><td>判断基準に人数のみ</td><td>6つの立場＋人数の目安と、その理由</td></tr>
        <tr><td class="new">必要なもの</td><td>×</td><td>広い面・付箋・書くもの・軽食・<strong>椅子の無い部屋</strong></td></tr>
        <tr><td class="new">要素の見分け方</td><td><strong>×</strong></td><td><strong>表。9種類の色と形の対応</strong></td></tr>
        <tr><td class="new">10の段</td><td><strong>×</strong></td><td><strong>図＋子10つ。各段に何をするかが入った</strong></td></tr>
        <tr><td class="new">　2. 時系列に並べる</td><td>×</td><td><strong>図。正常系が先、枝分かれは後</strong></td></tr>
        <tr><td class="new">　3. 問題点を洗い出す</td><td>×</td><td>詰まり・未自動化・未文書化・知識不足の4種</td></tr>
        <tr><td class="new">　4. 転換する出来事を見つける</td><td>×</td><td><strong>区切られた文脈を見つける手がかりになる</strong></td></tr>
        <tr><td class="new">　6. 自動で動く決まりを定める</td><td>×</td><td><strong>図。人が結びつかない指示の空白を埋める</strong></td></tr>
        <tr><td class="new">　8. 外部のシステムを足す</td><td>×</td><td><strong>この段の終わりに、すべての指示が3通りのどれかになる</strong></td></tr>
        <tr><td class="new">　9. 集約を見つける</td><td>×</td><td><strong>図。5種類の要素の並び順</strong></td></tr>
        <tr><td class="new">進め方は決まっていない</td><td>判断基準に一部</td><td>初回の勧め＋<strong>成果物がイベント履歴式の土台になる</strong></td></tr>
        <tr><td class="new">いつ使うか</td><td>判断基準1つ</td><td><strong>表（5つの目的）＋図＋向かない場面</strong></td></tr>
        <tr><td class="new">進行のこつ</td><td><strong>×</strong></td><td><strong>子3つ。始める前・最中・離れた場所から</strong></td></tr>
        <tr><td>アンチパターン ×4</td><td>あり</td><td>そのまま維持</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅲ. 注釈の例</h2>
  <p class="narrow">この本の図は<strong>順序と空欄</strong>に意味があるので、注釈がとくに効きました。</p>
  <div class="tablewrap">
    <table>
      <thead><tr><th>図</th><th>どこの話か</th><th>図に載せきれないこと</th></tr></thead>
      <tbody>
        <tr><td>10の段</td><td>10. 区切られた文脈に分ける</td><td><strong>最後に来るのが要点。</strong>並べ終えた結果として境界が浮かび上がる</td></tr>
        <tr><td>要素の並び</td><td>実行する人</td><td><strong>ここが空欄になる指示がある。</strong>そのときは決まりか外部のシステムが入るはずで、3つのどれも入らないなら、まだ見つけていないものがある</td></tr>
        <tr><td>要素の並び</td><td>判断の材料</td><td>指示より前に置くのは、人が指示を出す前にこれを見るから。<strong>順序が意味を持っていて、装飾ではない</strong></td></tr>
        <tr><td>時系列</td><td>6つの箱すべて</td><td>すべて過去形。<strong>現在形で書いてあるものは、業務イベントではなく指示であることが多い</strong></td></tr>
        <tr><td>自動で動く決まり</td><td>決まりから指示</td><td>条件が書き出せないなら、<strong>その条件がまだ言語化されていないということになる</strong></td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅳ. 完全プレビュー</h2>
  <p class="narrow">描画された301行を、<strong>省略なしで</strong>並べています。26ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / event-storming</span><span>ノード26 ・ 図5 ・ 原文2</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅴ. 置き換えたもの</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書き起こし版</th><th>置き換え先</th><th>保った内容</th></tr></thead>
      <tbody>
        <tr><td>考案者の氏名（2箇所）</td><td>「考案者」</td><td>厳密な規則ではなく指針として定義されたこと、離れた場所からの実施に異議を唱えてきたこと</td></tr>
        <tr><td>共同編集ツールの製品名</td><td>「共同で書き込める画面を使う道具」</td><td>そういう道具が現れたという事実</td></tr>
        <tr><td>特定の出来事の名称</td><td>「同じ場所に集まりにくい状況が広がったこと」</td><td>リモート実施が広がった経緯</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>機械で確認しました</h3>
    <p>考案者名・道具名・出来事名を grep して<strong>0件</strong>。</p>
  </div>
</section>

<section>
  <h2>Ⅵ. 14本目までの推移</h2>
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
        <tr><td><strong>event-storming</strong></td><td><strong>108</strong></td><td><strong>301</strong></td><td><strong>262</strong></td></tr>
        <tr><td><strong>14本の合計</strong></td><td><strong>1,451</strong></td><td><strong>3,912</strong></td><td><strong>3,347</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>14 / 19本。</strong>残り5本・約1,400行 ── 現場への導入、マイクロサービス、イベント駆動、データメッシュ、締めの経験則です。</p>
</section>

<footer>
  旧要約版108行・書き起こし版262行・変換後301行（描画結果の実測）。<br>
  考案者名・道具名・出来事名は役割や状況の説明へ置き換えた。段の順序、要素の並び順、境界が最後に浮かび上がることは保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-event-storming.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))