import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, extra
from card_kit import OUT, zone, pair, head, two, note

def f(k, v):
    return f'<div class="f"><div class="f-k">{k}</div><div class="f-v">{v}</div></div>'

def lbl(cx, y, text, chars):
    w = chars*10*0.98 + 10
    return (f'<rect class="wf-label-bg" fill="#F5F7F9" x="{cx-w/2:.1f}" y="{y-11:.1f}" '
            f'width="{w:.1f}" height="14" rx="3"/>'
            f'<text class="wf-edge-label" text-anchor="middle" fill="#79828F" '
            f'font-size="10" x="{cx}" y="{y}">{text}</text>')

SEQ = ('<svg class="wf-fig" viewBox="-10 -10 580 296" width="580" height="296" '
 'style="width:100%;max-width:900px;height:auto" role="img" '
 'aria-label="指示の置かれ方を確かめるやり取り">'
 '<defs><marker id="wf-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" '
 'markerHeight="8" orient="auto-start-reverse">'
 '<path class="wf-arrow" d="M0,0 L10,5 L0,10 z" fill="#C3CAD2"/></marker></defs>'
 '<g font-family="Noto Sans JP">'
 '<rect fill="#F5F7F9" stroke="#C3CAD2" x="0" y="0" width="150" height="30" rx="5"/>'
 '<text class="wf-name" text-anchor="middle" fill="#171B23" font-size="12" x="75" y="19">スキーマを書き換える者</text>'
 '<rect fill="#E2EFF0" stroke="#16636B" x="250" y="0" width="100" height="30" rx="5"/>'
 '<text class="wf-name" text-anchor="middle" fill="#171B23" font-size="12" x="300" y="19">スキーマ一式</text>'
 '<rect fill="#F5F7F9" stroke="#C3CAD2" x="470" y="0" width="90" height="30" rx="5"/>'
 '<text class="wf-name" text-anchor="middle" fill="#171B23" font-size="12" x="515" y="19">雛形の走査</text>'
 '<g stroke="#C3CAD2" stroke-width="1.2" stroke-dasharray="3 4">'
 '<line x1="75" y1="30" x2="75" y2="266"/><line x1="300" y1="30" x2="300" y2="266"/>'
 '<line x1="515" y1="30" x2="515" y2="266"/></g>'
 '<path class="wf-edge" d="M75,66 L296,66" fill="none" stroke="#C3CAD2" stroke-width="1.2" marker-end="url(#wf-arrow)"/>'
 + lbl(185, 60, "確認を依頼する", 7) +
 '<path class="wf-edge" d="M300,90 L338,90 L338,108 L304,108" fill="none" stroke="#C3CAD2" stroke-width="1.2" marker-end="url(#wf-arrow)"/>'
 '<text class="wf-edge-label" fill="#79828F" font-size="10" x="348" y="103">最新の版だけを選ぶ</text>'
 '<path class="wf-edge" d="M300,140 L511,140" fill="none" stroke="#C3CAD2" stroke-width="1.2" marker-end="url(#wf-arrow)"/>'
 + lbl(407, 134, "指示が読まれる場所を集める", 13) +
 '<path class="wf-edge" d="M515,172 L304,172" fill="none" stroke="#C3CAD2" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#wf-arrow)"/>'
 + lbl(410, 166, "指示の有無を返す", 8) +
 '<path class="wf-edge" d="M300,196 L338,196 L338,214 L304,214" fill="none" stroke="#C3CAD2" stroke-width="1.2" marker-end="url(#wf-arrow)"/>'
 '<text class="wf-edge-label" fill="#79828F" font-size="10" x="348" y="209">実在する指示と突き合わせる</text>'
 '<path class="wf-edge" d="M300,246 L79,246" fill="none" stroke="#C3CAD2" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#wf-arrow)"/>'
 + lbl(190, 240, "観点ごとの一覧を返す", 10) +
 '</g></svg>')

docu = (
 '<div class="rdoc">'

 # ── 表紙。利用者と目的も、ここに含める
 '<div class="rh">'
 '<div class="rchips"><span class="chip kind">業務ユースケース</span>'
 '<span class="chip id">uc-check-prompt-contract</span></div>'
 '<h3 class="rt">指示の置かれ方を確かめる</h3>'
 '<p class="ren">Check Prompt Contract</p>'
 '<p class="rlede">型が持つ指示が、実際に読まれる場所に置かれているかを突き合わせて返す。</p>'
 '<div class="actor"><p class="ac-who">スキーマを書き換える者</p>'
 '<p class="ac-want">自分が足した指示が、実際に読まれる場所に置かれているかを確かめたい。</p></div>'
 '<div class="rchips foot-chips"><span class="chip lbl">属する業務領域</span>'
 '<span class="chip ref">sd-reconciliation</span></div>'
 '</div>'

 # ── 受け取るものと、返すもの（入口と出口を隣に置く）
 + zone("受け取るものと、返すもの", None,
    '<div class="io">'
    '<div class="io-c"><p class="io-h">受け取る</p>'
    + '<div class="io-r"><code>schemaRef</code>'
      '<span class="sub">確かめる対象の型</span></div></div>'
    '<div class="io-a">→</div>'
    '<div class="io-c"><p class="io-h">終わったとき、返っている</p>'
    '<ul class="post"><li>読み方の指示が無い定義の一覧</li>'
    '<li>書き方の指示が無い記入対象の一覧</li>'
    '<li class="sub">ほか2件</li></ul></div>'
    '</div>')

 # ── どう動くか（図が主役。表は番号の詳細として畳む）
 + zone("どう動くか", None,
    '<div class="figwrap">' + SEQ + '</div>'
    + fold("やり取りを1件ずつ見る（6件）",
       tbl(["","誰から","誰へ","何を"],[
        ("",["1","スキーマを書き換える者","スキーマ一式","確認を依頼する"]),
        ("",["2","スキーマ一式","<span class='sub'>自分</span>","最新の版だけを選ぶ"]),
        ("",["3","スキーマ一式","雛形の走査","指示が読まれる場所を集める"]),
        ("",["4","雛形の走査","スキーマ一式","指示の有無を返す"]),
        ("",["5","スキーマ一式","<span class='sub'>自分</span>","実在する指示と突き合わせる"]),
        ("",["6","スキーマ一式","スキーマを書き換える者","観点ごとの一覧を返す"]),
       ])))

 # ── 約束すること（基準・シナリオ・外れ方をひとまとまりに）
 + zone("約束すること", "基準 7 ／ シナリオ 11 ／ 覆えていない基準 0",
    '<div class="crit">' + tbl(["","いつ","何が","どうなる","覆うシナリオ"],[
       ("",["<b>1</b>","求められたとき","読み方の指示が無い定義","<b>返る</b>","3件"]),
       ("",["<b>2</b>","求められたとき","書き方の指示が無い記入対象","<b>返る</b>","2件"]),
       ("",["<b>3</b>","求められたとき","契約が認めない名前の指示","<b>返る</b>","2件"]),
       ("",["<b>4</b>","確認の間ずっと","指示の中身の良し悪し","<b>判定しない</b>","1件"]),
       ("",["<b>5</b>","常に","記入対象","既存の走査から決まる","1件"]),
       ("",["<span class='sub'>6・7</span>","<span class='sub'>ほか2件</span>",
         "<span class='sub'>—</span>","<span class='sub'>—</span>","<span class='sub'>2件</span>"]),
     ]) + '</div>'
    + '<pre class="gk">Scenario: 読み方の指示が無い定義が返る\n'
      '  Given  読み方の指示を持たない定義がある型\n'
      '  When   指示の置かれ方の確認を依頼する\n'
      '  Then   その定義が一覧に含まれる\n'
      '  覆う基準      1\n'
      '  確かめる単位  uc-check-prompt-contract</pre>'
    + '<div class="errs"><p class="errs-h">うまくいかないとき</p>'
      + pair('<code>SCHEMA_NOT_FOUND</code>', "対象の型が1つも見つからない")
      + '</div>')

 + '</div>')

from card_kit import page
page("usecase", 7, "業務ユースケース", "Use Case",
 "外から呼ばれる、業務としてひとまとまりの用事。"
 "<b>受け入れ基準とシナリオの対応</b>が、そのまま読める。",
 docu)
print("usecase ok")
