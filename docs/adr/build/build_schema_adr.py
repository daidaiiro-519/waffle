import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra

# 公開版から取り戻した、adr-schema-from-spec の図2枚
FIG_WHERE = '''<figure class="fig"><div class="scroll"><svg viewBox="0 0 772 215" role="img" style="min-width:44rem;width:100%;height:auto;display:block" font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"><defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs><text x="12" y="20" font-size="11.5" fill="var(--against)">変更前 ── 宣言と成果物が同じものなので、突き合わせる相手がいない</text><rect x="12" y="32" width="190" height="50" rx="3" fill="var(--surface)" stroke="var(--against)" stroke-width="1"/><text x="107.0" y="62.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">人が手で書く</text><line x1="202" y1="57" x2="280" y2="57" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/><rect x="280" y="32" width="220" height="50" rx="3" fill="var(--surface)" stroke="var(--against)" stroke-width="1"/><text x="390.0" y="54.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">JSON Schema ファイル</text><text x="390.0" y="73.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">宣言でもあり成果物でもある</text><line x1="500" y1="57" x2="578" y2="57" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/><rect x="578" y="32" width="180" height="50" rx="3" fill="var(--surface)" stroke="var(--rule)" stroke-width="1"/><text x="668.0" y="62.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">Document を検査する</text><text x="12" y="140" font-size="11.5" fill="var(--infer)">変更後 ── 宣言と成果物が別なので、突き合わせられる</text><rect x="12" y="152" width="190" height="50" rx="3" fill="var(--surface)" stroke="var(--infer)" stroke-width="2"/><text x="107.0" y="174.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">Schema の宣言</text><text x="107.0" y="193.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">document.json</text><line x1="202" y1="177" x2="280" y2="177" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/><text x="241" y="169" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">描く</text><rect x="280" y="152" width="220" height="50" rx="3" fill="var(--surface)" stroke="var(--infer)" stroke-width="1"/><text x="390.0" y="174.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">JSON Schema ファイル</text><text x="390.0" y="193.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">成果物</text><line x1="500" y1="177" x2="578" y2="177" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/><rect x="578" y="152" width="180" height="50" rx="3" fill="var(--surface)" stroke="var(--rule)" stroke-width="1"/><text x="668.0" y="182.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">Document を検査する</text></svg></div><figcaption>Document を成果物へ描くのと同じ関係を、Schema にも当てる。<b>突き合わせる相手ができるので、ドリフト検知が Schema にも効く。</b></figcaption></figure>'''

FIG_LAYOUT = '''<figure class="fig"><div class="scroll"><svg viewBox="0 0 900 372" role="img" style="min-width:44rem;width:100%;height:auto;display:block" font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"><defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs><rect x="16" y="30" width="330" height="184" rx="4" fill="none" stroke="var(--assume)" stroke-width="1" stroke-dasharray="4 3"/><text x="24" y="24" font-size="11.5" fill="var(--assume)">段1 ── Waffle の実装。変えるにはプロダクトを変える</text><rect x="36" y="48" width="290" height="54" rx="3" fill="var(--surface)" stroke="var(--assume)" stroke-width="1"/><text x="181.0" y="72.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">Schema の仕様</text><text x="181.0" y="91.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">Document として書く</text><line x1="181" y1="102" x2="181" y2="140" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/><text x="232" y="125" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">実装する</text><rect x="36" y="140" width="290" height="54" rx="3" fill="var(--surface)" stroke="var(--assume)" stroke-width="2"/><text x="181.0" y="164.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">Schema エンティティ</text><text x="181.0" y="183.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">Python</text><rect x="420" y="30" width="460" height="330" rx="4" fill="none" stroke="var(--infer)" stroke-width="1" stroke-dasharray="4 3"/><text x="428" y="24" font-size="11.5" fill="var(--infer)">段2・段3 ── Document。利用者が増やせる</text><rect x="440" y="60" width="190" height="54" rx="3" fill="var(--surface)" stroke="var(--infer)" stroke-width="1"/><text x="535.0" y="84.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">DomainSpecSchema</text><text x="535.0" y="103.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">仕様を書く型</text><rect x="650" y="60" width="190" height="54" rx="3" fill="var(--surface)" stroke="var(--infer)" stroke-width="1"/><text x="745.0" y="84.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">KnowledgeSchema ほか</text><text x="745.0" y="103.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">知識を書く型</text><line x1="326" y1="167" x2="440" y2="110" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/><text x="383" y="152" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">実体を作る</text><line x1="535" y1="114" x2="535" y2="190" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/><line x1="745" y1="114" x2="745" y2="190" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/><text x="596" y="158" font-size="11.5" fill="var(--ink-faint)">骨格を作る</text><rect x="440" y="190" width="190" height="54" rx="3" fill="var(--surface)" stroke="var(--infer)" stroke-width="1"/><text x="535.0" y="214.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">uc-render-document</text><text x="535.0" y="233.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">仕様1本</text><rect x="650" y="190" width="190" height="54" rx="3" fill="var(--surface)" stroke="var(--infer)" stroke-width="1"/><text x="745.0" y="214.0" text-anchor="middle" font-size="14" font-weight="600" fill="var(--ink)">spec-implementation-…</text><text x="745.0" y="233.0" text-anchor="middle" font-size="11.5" fill="var(--ink-faint)">知識1本</text><text x="440" y="286" font-size="11.5" fill="var(--ink-faint)">型を1つ足すのは Document を1本書くこと。</text><text x="440" y="306" font-size="11.5" fill="var(--ink-faint)">Waffle の実装には触らない。</text></svg></div><figcaption><b>線は段1 と段2 の間に引かれる。</b>段1 は Waffle というプロダクトの仕様なので実装になり、段2 から下は利用者が増やしていくデータになる。</figcaption></figure>'''


axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th>構造に仕様がある</th>
<th>型を増やすのに実装を触らない</th>
<th class="keycol">宣言と成果物が別で、突き合わせられる<br><span class="sub">決め手</span></th>
<th>いまの実装を動かさずに済む</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">仕様から実装し、型は Document として置く<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">いまのまま置く</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
<tr><td class="cond">型は手で書いたまま、説明する仕様だけ足す</td>
<td>{ok}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['宣言と成果物が別で、突き合わせられる<span class="keytag">決め手</span>',
      "突き合わせる相手が無いと、宣言が守られているかを機械で確かめられない。"
      "Waffle が Document に対してやっていることを、Schema に対してもできるかどうかがここで決まる",
      "<b>いまのまま</b>／<b>説明する仕様だけ足す</b> ── "
      "どちらも JSON Schema が宣言そのものなので、突き合わせる相手が存在しない"]),
    ("",["構造に仕様がある",
      "構造は、その型の Document すべてへ波及する。波及するものに仕様が無いと、"
      "何が正しいかを誰も言えない",
      "<b>いまのまま</b> 最も使われている語が、最も説明されていない"]),
    ("",["型を増やすのに実装を触らない",
      "型は利用者が足していくもの。足すたびにプロダクトを変えるなら、利用者は足せない",
      "<b>いまのまま</b>／<b>説明する仕様だけ足す</b> ── どちらも JSON Schema を手で書き足す"]),
    ("",["いまの実装を動かさずに済む",
      "動かす範囲が広いほど、途中で止まったときに新旧が混ざる",
      "<b>仕様から実装する（採る）</b> 段1 を書き直すことになる"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("evidence","測った",
    "<code>x-render-order</code> は最新版の schema で<b>156か所</b>使われ、仕様には<b>0回</b>現れない。"
    "最も使われている <code>x-prompt-write</code> は<b>623か所</b>で、言及は19回である"),
  joint("さらに"),
  step("evidence","測った",
    "<b>読む相手のいない語が2つある</b>。"
    "<code>x-prompt-interpret</code> と <code>x-extraction-rules</code> は、"
    "最新版での使用が0で、読む実装も無い"),
  joint("だから"),
  step("conclude","言えること",
    "語彙に仕様が無いので、<b>誰かが消しても何も落ちない</b>。"
    "使われなくなった語が残り続けるのも、同じことの現れである"),
  joint("何が波及するかを見ると"),
  step("premise","前提",
    "schema が持つのは値ではなく<b>構造</b>である。"
    "構造はその型の Document すべてへ波及する"),
  joint("だから"),
  step("conclude","言えること",
    "<b>波及するものに仕様が無い状態は成り立たない。</b>"
    "何が正しいかを誰も言えないまま、全部の Document が従うことになる"),
  joint("置き場所も見た"),
  step("evidence","測った",
    "図の宣言の形が <code>KnowledgeSchema</code> の <code>$defs.Figure</code> にあり、"
    "ほかの型にも図の欄が散らばっている。"
    "<b>どの型でも同じであるべき形が、型ごとに置かれている</b>"),
  joint("合わせると"),
  step("conclude","結論",
    "Schema を仕様から実装し、型は Document として置く。"
    "JSON Schema は手で書かず、宣言から描く"),
  joint("なお"),
  step("premise","前提",
    "Schema の仕様を書く時点では、それを検査する実装がまだ無い。"
    "<b>この行き違いは最初の1回だけで、以後は起きない</b>——"
    "自分自身を自分で組み立てる仕組みがどれも通る道である"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（5件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["156か所で使われ、仕様に0回",'<span class="kindtag unv">実測</span>',
      "最新版の schema 10本と、仕様の全文を数えた","—"]),
    ("",["読む相手のいない語が2つ",'<span class="kindtag unv">実測</span>',
      "最新版での出現数と、読む実装の有無を突き合わせた","—"]),
    ("",["schema が持つのは構造である",'<span class="kindtag unv">実測</span>',
      "<code>patch-schema</code> の操作が "
      "<code>add_block</code>・<code>rename_block</code>・<code>add_def</code>・"
      "<code>add_kind_branch</code> であること","—"]),
    ("",["図の形が段2 に置かれている",'<span class="kindtag unv">実測</span>',
      "<code>KnowledgeSchema</code> の <code>$defs.Figure</code>","—"]),
    ("",["最初の1回だけ検査できない",'<span class="kindtag lim">確立された型</span>',
      "自分自身を自分で組み立てる仕組みに共通する起動の手順",
      "2回目以降も検査できない形になったとき"]),
  ]))

item_tbl = tbl(["","変更前","変更後"],[
 ("keyrow",["JSON Schema ファイル","<b>人が手で書く（10本）</b>","<b>宣言から描かれる成果物</b>"]),
 ("keyrow",["手で書くもの","<b>すべての schema</b>","<b>Schema の仕様1本のみ</b>"]),
 ("",["Schema を説明する仕様","<b>無い</b>","<b>ある。</b>Document として書かれ、実装へ転写される"]),
 ("",["型を増やすとき","schema ファイルを手で書き足す",
   "<b>Document を1本書く。</b>Waffle の実装は変わらない"]),
 ("",["ドリフト検知","<b>Schema には効かない</b>","<b>効く。</b>宣言と成果物を突き合わせられる"]),
 ("",["エンティティ","Document と Schema","<b>変えない。</b>Schema の中身を仕様から書き直すだけ"]),
])

vocab_tbl = tbl(["語","変更前","変更後"],[
 ("keyrow",["<code>x-prompt-write</code>","623か所で使用。仕様での言及19回",
   "<b>語彙として定義される。</b>述べる内容・書ける場所・落ちる先の3つを持つ"]),
 ("keyrow",["<code>x-render-order</code>","156か所で使用。<b>仕様での言及0回</b>","同上"]),
 ("",["<code>x-frontmatter</code>","<b>Markdown の表紙欄に縛られている</b>",
   "<b>表紙の語へ抽象化する。</b>落とし方は描き先ごとに実装が持つ"]),
 ("",["描き先（Markdown / HTML / SVG）","<b>語が無い</b>","<b>足す</b>"]),
 ("",["図の宣言の形","<b>段2 の <code>$defs.Figure</code></b>","<b>段1 の語彙。</b>値は Document のまま"]),
 ("",["<code>x-prompt-interpret</code>・<code>x-extraction-rules</code>",
   "使用0・読む実装も無し","<b>落とす</b>"]),
])

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>Schema を仕様から実装し、型は Document として置く</h1>'
 '<p class="lede"><code>x-render-order</code> は156か所で使われ、仕様には0回しか現れない。'
 '<b>誰かが消しても何も落ちない。</b>'
 'schema が持つのは構造で、構造はその型の Document すべてへ波及する。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle は、'
  '<b>Schema を仕様から実装し、型（<code>DomainSpecSchema</code> など）は Document として置く</b>。'
  'JSON Schema ファイルは手で書かず、宣言から描いた成果物とする。'
  '手で書くのは Schema の仕様1本だけになる。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt">いまは <b>JSON Schema が宣言そのもの</b>なので、'
  '突き合わせる相手が存在しない。宣言と成果物を分ければ、'
  'Waffle が Document に対してやっていることを Schema に対してもできる。</span></div></div>'),

 sec("02","変更前と変更後",
  "変わるのは<b>手で書く場所</b>である。エンティティは増やさない。",
  FIG_WHERE +
  '<h3 class="sub-h">項目で見る</h3>' + item_tbl +
  '<h3 class="sub-h">語彙で見る</h3>' + vocab_tbl +
  '<h3 class="sub-h">変更後、何がどこに並ぶか</h3>' + FIG_LAYOUT),

 sec("03","理由",
  "最も使われている語が、最も説明されていない。"
  "<b>schema が持つのは構造であり、構造は全ての Document へ波及する。</b>",
  reason, reason_fold),

 sec("04","判断を分けた軸",
  "採る案は4つの条件のうち3つを満たす。落とすのは1つで、<b>段1 を書き直すことになる</b>。",
  axis, axis_fold),

 sec("05","付随して決めたこと",
  "型と実体の境目が決まると、どの値がどちらに属するかも決まる。3点を同時に決めた。",
  tbl(["論点","決定"],[
    ("keyrow",["<code>x-*</code> は型と実体のどちらに置くか",
      "<b>型。実体へは写さない。</b>描くときは schema を引数で受け取る"]),
    ("keyrow",["図はどちらに置くか",
      "<b>形は段1、値は Document。</b>書ける欄と主張の一覧は全型で同じ、"
      "何を描くかは文書ごとに違う"]),
    ("",["読む相手のいない2語",
      "<b>落とす。</b>語彙に入れない"]),
  ]),
  fold("それぞれの根拠を開く（3件）",
    tbl(["論点","根拠"],[
      ("keyrow",["<code>x-*</code> は型と実体のどちらに置くか",
        "<b>同じ schema から作られるものは、構造が同じでなければ困る。</b>"
        "実体へ写すと、一致が「成り立っていること」から「保たせること」へ変わる。"
        "直し漏れは機械で埋められるが、食い違いうる状態そのものが型を型でなくする。"
        "<code>x-prompt-write</code> も同じで、各欄に何を書くべきかは型が決める"]),
      ("keyrow",["図はどちらに置くか",
        "書ける欄は全型で同じでなければならないが、何を描くかは文書ごとに違う。"
        "<b>形と値で属する場所が分かれる。</b>"
        "いまは形のほうが <code>KnowledgeSchema</code> の中にあり、置き場所を間違えている"]),
      ("",["読む相手のいない2語",
        "使用0・読む実装も無い。<b>語彙に仕様が無かったから残った</b>ので、"
        "仕様を持つ時点で入る理由が無い"]),
    ]))),

 sec("06","答えないこと",
  "語彙の中身と、移す手順は、この決定では扱わない。",
  tbl(["項目","種別","行き先"],[
    ("",["語彙の粒度",'<span class="kindtag out">範囲外</span>',
      "描き方の6語を1つにまとめる余地があるかは、まだ見ていない"]),
    ("",["足りない3語の形",'<span class="kindtag out">範囲外</span>',
      "描き先・表紙・図をどう宣言するか。名前も欄の形も決めていない"]),
    ("",["移す順序",'<span class="kindtag out">範囲外</span>',
      "いまの schema を段2 の Document として書き直す順序と、その間の互換"]),
  ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-15</span></div></section>',

 sec("08","関連","この決定は、Schema の仕様を書き始めるための前提になる。","",
  fold("縛る対象と、前後の決定を開く（5件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象","JSON Schema ファイルの作り方と、<code>x-*</code> の置き場所"]),
      ("",["先立つ決定","図の語彙を、描き方の名前から主張の名前へ移す（承認済み）"]),
      ("",["先立つ決定","図の宣言を、主張を軸にした形へ置き換える（承認済み）"]),
      ("",["関わる決定","図の宣言を、Document の内側の値として置く（<b>未承認</b>）── "
        "この決定の「形は段1、値は Document」と噛み合う"]),
      ("",["この決定を使う予定",
        "Schema の仕様を書く。そこに語彙11語（2語を落とし、3語を足す）の"
        "述べる内容・書ける場所・落ちる先を並べる"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
""" + """
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
"""
html = ("<title>Schema を仕様から実装し、型は Document として置く</title>"
        f"<style>{CSS}\n{extra2}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-schema-from-spec.html").write_text(html, encoding="utf-8")
print("書いた", len(html))
