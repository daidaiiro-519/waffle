PRE = ('background:rgba(128,128,128,.10);padding:.7rem .9rem;border-radius:.3rem;'
       'overflow-x:auto;font-size:.82rem;line-height:1.6;margin:.6rem 0;white-space:pre')

def pre(s, tone=""):
    st = PRE + (f";border-left:3px solid {tone}" if tone else "")
    return f'<pre style="{st}">{s}</pre>'

WANT = """<p class="lead">Waffle の仕様文書に、いま書きたい規則が4件あるとする。
<b>この4件が、案Aと案Bでどう書き分かれるか</b>を見る。</p>"""

TBL = """<table><tr><th>規則</th><th>言いたいこと</th><th>答えを出すのに要るもの</th></tr>
<tr><td><code>SPEC-REF-RESOLVES</code></td><td>シナリオが指す spec の節が、実在する</td><td>この文書と、指された節</td></tr>
<tr><td><code>VALIDATED-HAS-RESULTS</code></td><td>状態が VALIDATED なら、検証結果の置き場所を持つ</td><td>この文書だけ</td></tr>
<tr><td><code>SCENARIO-MATCHES-CODE</code></td><td>シナリオに対応する実装が在る</td><td><b>ソースの木ぜんぶ</b></td></tr>
<tr><td><code>TITLE-READS-AS-BEHAVIOR</code></td><td>シナリオの題が、振る舞いを述べる文になっている</td><td><b>人の判断</b></td></tr></table>"""

A = pre("""<b>concrete schema（案A）</b>
"x-rules": [
  { "ruleId": "SPEC-REF-RESOLVES",
    "対象":   "scenarios[].specRef",
    "述語":   { "参照が解決する": true } },

  { "ruleId": "VALIDATED-HAS-RESULTS",
    "対象":   "meta.status",
    "述語":   { "VALIDATED 以上なら": { "在る": "meta.testResultsPath" } } }
]

<span style="opacity:.7">// 残り2件は、ここに書けない。
// scenario-drift はコマンドとして別に在り、題の検めは誰も持たない</span>""", "var(--muted)")

AOUT = pre("""<b>走らせた結果（案A）</b>
規則 2 件を検査した
  SPEC-REF-RESOLVES        違反 0
  VALIDATED-HAS-RESULTS    違反 1   uc-render-blank-template

<span style="opacity:.7">検めていないもの: 出ない（規則の一覧に無いので、数えようがない）</span>""", "var(--muted)")

B = pre("""<b>concrete schema（案B）</b>
"x-rules": [
  { "ruleId": "SPEC-REF-RESOLVES",
    "対象":   "scenarios[].specRef",
    "述語":   { "参照が解決する": true } },

  { "ruleId": "VALIDATED-HAS-RESULTS",
    "対象":   "meta.status",
    "述語":   { "VALIDATED 以上なら": { "在る": "meta.testResultsPath" } } },

  { "ruleId": "SCENARIO-MATCHES-CODE",
    "対象":     "scenarios[]",
    "検めること": "scenario-drift",     <span style="color:var(--add)">← 名簿の名前</span>
    "誰が":     "機械" },

  { "ruleId": "TITLE-READS-AS-BEHAVIOR",
    "対象":     "scenarios[].title",
    "検めること": "human-review",
    "誰が":     "人" }
]""", "var(--key)")

BOOK = pre("""<b>abstract schema が持つ名簿</b>
"x-checks": {
  "reference-resolves": { "入力": "この文書",              "返す": "届かない参照の印" },
  "scenario-drift":     { "入力": "この文書 ＋ ソースの木", "返す": "対応の無いシナリオの印" },
  "text-in-original":   { "入力": "この文書 ＋ 落とした原文", "返す": "原文に無い文字列" },
  "human-review":       { "走らせない",                   "返す": "未検として数える" }
}

<span style="opacity:.7">// concrete が書けるのは、この名簿に在る名前だけである</span>""", "currentColor")

BOUT = pre("""<b>走らせた結果（案B）</b>
規則 4 件を検査した
  SPEC-REF-RESOLVES        述語             違反 0
  VALIDATED-HAS-RESULTS    述語             違反 1   uc-render-blank-template
  SCENARIO-MATCHES-CODE    scenario-drift   違反 2   SC-01J7Q4K ・ SC-01J8M2P
  TITLE-READS-AS-BEHAVIOR  human-review     <span style="color:var(--add)">未検 12  人が見る規則。走らせられない</span>""", "var(--key)")

CONCRETE = (WANT + TBL
 + '<h3>案A ── 述語だけを持つ</h3>' + A + AOUT
 + '<h3>案B ── 述語 ＋ 検めることの名前を持つ</h3>' + B + BOOK + BOUT
 + '<p class="lead">差は最後の1行に出る。<b>案Bは「まだ検めていない12件」を出力できるが、案Aはそれを数えられない</b>'
   ' ── その規則が一覧に無いからである。'
   '<b>検査の中身が外にあることは、どちらも変わらない。</b>違うのは、外にあるものを規則から名前で指せるかどうかである。</p>')
