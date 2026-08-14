"""7本目のアーティファクトを組み立てる。プレビューは描画物から機械生成したものを使う。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
head = pathlib.Path(f"{S}/style_head.html").read_text(encoding="utf-8")
head = head.replace("evolving-design の変換 ── 5本目",
                    "design-heuristics の変換 ── 7本目")
frag = pathlib.Path(f"{S}/dh_preview.html").read_text(encoding="utf-8")

BODY = """<div class="wrap">

<header>
  <span class="eyebrow">Waffle / knowledge の変換 7本目</span>
  <h1><code>design-heuristics</code> を書き起こし版から移す</h1>
  <p class="standfirst">旧要約版120行 → <strong>341行</strong>。書き起こし版203行を上回りました。この本の中身は<strong>ほぼ全部が判断の流れ</strong>で、旧版はそれを分岐点と遷移の一覧という平らな形に潰していました。<strong>5つの図</strong>として立て直しています。</p>
</header>

<section>
  <div class="tally">
    <div class="stat"><span class="n">21</span><span class="l">ノード</span></div>
    <div class="stat ok"><span class="n">5</span><span class="l">図（旧版は0）</span></div>
    <div class="stat"><span class="n">2</span><span class="l">原文（表）</span></div>
    <div class="stat"><span class="n">341</span><span class="l">行（旧120 / 書起し203）</span></div>
  </div>
</section>

<section>
  <h2>Ⅰ. この本だけ、旧版の壊れ方が違いました</h2>
  <p class="narrow">これまでの6本は「節が丸ごと落ちている」という欠落でした。<code>design-heuristics</code> は<strong>節はほぼ残っていて、形が潰れていた</strong>という壊れ方です。</p>

  <div class="box bad">
    <h3>旧版は、4つの判定を1つの決定木に押し込んでいました</h3>
    <p>書き起こし版には <strong>判定の流れが4つ</strong>（実装方法・技術方式・テスト方針・そして総合）あります。旧版はこれを <code>decisionCriteria</code> という単一のブロックに入れたため、<strong>13個の分岐点と14本の遷移が1つの木に混ざり</strong>、どこからどこまでが1つの判定なのか読めなくなっていました。</p>
    <p>しかも <code>q1</code>（文脈の大きさ）と <code>q5</code>（永続化モデルは複数か）は、<strong>どの遷移からも到達できない孤立点</strong>として残っていました。形式が持てる構造が1つしかなかったので、入れ場所が無かったものが宙に浮いたのだと思います。</p>
  </div>

  <div class="box ok">
    <h3>4つを、4つの図として分けました</h3>
    <p>加えて「4つの判断が連鎖する」こと自体を<strong>5つ目の図</strong>として立てました。これは書き起こし版では地の文で述べられていて、旧版では原則の1項目になっていたものです。<strong>後段の判断で違和感が出たら前段を疑う</strong>という、この本の使い方そのものにあたります。</p>
  </div>
</section>

<section>
  <h2>Ⅱ. 何が戻ったか</h2>
  <div class="tablewrap">
    <table>
      <thead><tr><th>ノード</th><th>旧要約版</th><th>中身</th></tr></thead>
      <tbody>
        <tr><td>経験則とは何か</td><td>原則6項目に分散</td><td>定義として1ノードに集約</td></tr>
        <tr><td class="new">4つの判断は連鎖する</td><td>原則の1行</td><td><strong>図。食い違ったら前段へ戻る経路を含む</strong></td></tr>
        <tr><td>区切られた文脈の大きさ</td><td>孤立した分岐点1つ</td><td>子3つに展開</td></tr>
        <tr><td class="new">　最適な大きさはない</td><td>×</td><td>モデルが先、大きさは結果</td></tr>
        <tr><td class="new">　最初は広い範囲で区切る</td><td>×</td><td><strong>引き直しはほぼ放置される、が理由</strong></td></tr>
        <tr><td class="new">　中核とよくやりとりする相手も同じ側に</td><td>×</td><td>垂直の境界・大きな泥団子の回避</td></tr>
        <tr><td>業務ロジックの実装方法</td><td>分岐点として一部</td><td><strong>図</strong>＋子2つ</td></tr>
        <tr><td class="new">　複雑さをどう判定するか</td><td>×</td><td>不変条件を含むか／検証が中心か。同じ言葉の複雑さも材料</td></tr>
        <tr><td>　カテゴリーとの食い違いを見つける</td><td>アンチパターンに1つ</td><td><strong>実装を選び直すのではなく、カテゴリー判断を見直す機会</strong></td></tr>
        <tr><td>技術方式</td><td>分岐点として一部</td><td><strong>図</strong>＋子2つ</td></tr>
        <tr><td class="new">　そうなる理由</td><td>分岐点のラベルに括弧書き</td><td><strong>表として独立（4方式ぶんの根拠）</strong></td></tr>
        <tr><td class="new">　永続化が複数なら CQRS</td><td>孤立した分岐点</td><td>対応表への例外として位置づけ直した</td></tr>
        <tr><td>テストの基本方針</td><td>分岐点として一部</td><td><strong>図</strong>＋対比表</td></tr>
        <tr><td class="new">総合的な判定</td><td><strong>×</strong></td><td><strong>図。実装方法／技術方式／テスト方針の3つの枠で括った14ノード</strong></td></tr>
        <tr><td class="new">　この判定方法の使い方</td><td><strong>×</strong></td><td><strong>厳格な規則ではない。独自の判定方法を作るのは自由。複雑な手段は最後の手段</strong></td></tr>
        <tr><td>アンチパターン ×4</td><td>あり</td><td>そのまま維持</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Ⅲ. 完全プレビュー</h2>
  <p class="narrow">描画された341行を、<strong>省略なしで</strong>並べています。21ノードすべてです。</p>

  <div class="doc">
    <div class="doc-head"><span>knowledge / design-heuristics</span><span>ノード21 ・ 図5 ・ 原文2</span></div>
    <div class="doc-body">

__PREVIEW__

    </div>
  </div>
</section>

<section>
  <h2>Ⅳ. 置き換えたもの</h2>
  <p class="narrow">この本は書き起こし版の時点で具体的な事例をほとんど持たず、置き換えが要ったのは1箇所だけでした。</p>
  <div class="tablewrap">
    <table>
      <thead><tr><th>書き起こし版</th><th>置き換え先</th><th>保った内容</th></tr></thead>
      <tbody>
        <tr><td>著者以外の人物に帰した一句（引用符・人名つき）</td><td>主張そのものへの言い換え</td><td>「大きさは、設計の手がかりとしてもっとも役に立たないものの一つ」という主張</td></tr>
        <tr><td>旧要約版の実例（架空のオンライン書店）</td><td>削除</td><td>実例が担っていた「同じ文脈の中でも業務領域ごとに方式が違ってよい」は、総合的な判定の図が構造として示す</td></tr>
      </tbody>
    </table>
  </div>
  <div class="box ok">
    <h3>機械で確認しました</h3>
    <p>人名・引用符つきの一句・旧版の架空事例を grep して<strong>0件</strong>。加えて外来語のまま残っていた用語（表題の「ヒューリスティクス」）も、この文書自身が使っている「設計の経験則」へ揃えました。</p>
  </div>
</section>

<section>
  <h2>Ⅴ. 7本目までの推移</h2>
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
        <tr><td><strong>design-heuristics</strong></td><td><strong>120</strong></td><td><strong>341</strong></td><td><strong>203</strong></td></tr>
        <tr><td><strong>7本の合計</strong></td><td><strong>754</strong></td><td><strong>1,919</strong></td><td><strong>1,817</strong></td></tr>
      </tbody>
    </table>
  </div>
  <p class="narrow"><strong>7 / 19本</strong>。残り12本・約2,900行です。</p>
</section>

<footer>
  旧要約版120行・書き起こし版203行・変換後341行（描画結果の実測）。<br>
  人物に帰した一句は主張そのものへ言い換えた。図が示す判断の分岐と連鎖の構造は保っている。<br>
  プレビューは描画物から機械で生成した（手で書き写すと取りこぼすため）。
</footer>

</div>
"""

out = head + BODY.replace("__PREVIEW__", frag)
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/"
             "knowledge-conversion-design-heuristics.html").write_text(out, encoding="utf-8")
print("生成完了 / ノード数:", out.count('class="nm"'))