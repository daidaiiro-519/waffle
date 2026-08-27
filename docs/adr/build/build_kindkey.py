import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, ok, ng, extra
C=lambda s: f"<code>{s}</code>"

cmp_tbl = f'''<div class="scroll"><table>
<thead><tr><th>比べる点</th>
<th>A ── 鍵を1つにする<br><span class="sub">{C('kind')}</span></th>
<th>B ── 群ごとの名前を残す<br><span class="sub">{C('specKind')} ほか6つ</span></th></tr></thead>
<tbody>
<tr class="keyrow"><td class="cond"><b>新しい型を足すとき、決めることがあるか</b><span class="keytag">決め手</span></td>
<td>{ok} <b>無い。</b>鍵は1つしかない</td>
<td>{ng} <b>ある。</b>既存の鍵を使うか、新しい鍵を作るかを毎回決める。<b>その基準が無い</b></td></tr>
<tr><td class="cond">鍵の名前が読み手へ伝えること</td>
<td>{ng} 伝えない。型は {C('schemaRef')} を見る</td>
<td>{ok} 「仕様の種別」「規約の種別」と分かる</td></tr>
<tr><td class="cond">その情報は他にもあるか</td>
<td>{ok} {C('schemaRef')} と {C('documentType')} が持つ</td>
<td>{ng} <b>重複している。</b>同じことを3か所が言う</td></tr>
<tr><td class="cond">実装が鍵の名前を使うか</td>
<td>{ok} 使わない</td>
<td>{ok} <b>使わない。</b>分岐の形から機械的に取り出している</td></tr>
<tr><td class="cond">段2 が宣言することの数</td>
<td>{ok} 枝の一覧だけ</td>
<td>{ng} 枝の一覧＋<b>鍵の名前</b></td></tr>
<tr><td class="cond">移す手間</td>
<td>{ng} <b>文書253本と型10本</b>の鍵名を変える</td>
<td>{ok} 何もしない</td></tr>
</tbody></table></div>'''

facts = tbl(["測ったこと","結果","どちらに効くか"],[
 ("keyrow",["鍵ごとに、何本の型が使っているか",
   f"{C('specKind')} だけが<b>3本</b>で共有。ほか5つは<b>1本ずつ</b>",
   "<b>A。</b>「群を表す」という読みは、6つのうち1つでしか成り立っていない"]),
 ("keyrow",["実装は鍵の名前を知っているか",
   "<b>知らない。</b>分岐の形（<code>allOf</code>＋<code>if</code>）から機械的に取り出している",
   "<b>A。</b>名前は機械にとって何の意味も持たない"]),
 ("",["1本の型に、分岐の軸はいくつあるか","<b>すべて0か1つ。</b>2つ持つ型は無い",
   "<b>A。</b>軸が1つなら、名前で軸を指す必要が無い"]),
 ("",["枝の名前は鍵をまたいで重複するか","<b>しない。</b><code>usecase</code> は仕様の側だけ",
   "<b>A。</b>名前空間を分ける必要が無い"]),
 ("",["<code>documentRole</code> は分岐に使われるか","<b>使われない。</b>配置先の解決にだけ使う",
   "どちらでもない。<b>直交する軸だという説明は、分岐の話ではなかった</b>"]),
])

body="".join([
 '<header><p class="eyebrow">比較</p>'
 '<h1>種別の鍵を、1つにするか群ごとに分けるか</h1>'
 '<p class="lede">私は「型ごとに自分の名前を付けているだけ」と言ったが、'
 '<b>それは誤りだった</b> ── <code>specKind</code> は3本が共有している。'
 'измеり直して、両方を並べる。</p></header>',

 sec("01","並べて比べる",
   "<b>分かれ目は「新しい型を足すとき、決めることがあるか」</b>である。"
   "ほかの点は、どちらにも言い分がある。",
   cmp_tbl),

 sec("02","測ったこと",
   "5つ測って、<b>4つが A に効いた</b>。",
   facts),

 sec("03","私の推し ── A",
   "決め手は<b>「決めることが無い」</b>である。",
   tbl(["理由","中身"],[
     ("keyrow",["<b>B は毎回、決めることが増える</b>",
       "新しい型を足すたびに「既存の鍵を使うか、新しい鍵を作るか」を決める。"
       "<b>その基準が無い</b>ので、実測でも揃っていない ── "
       "6つのうち5つが1本しか使っておらず、共有されているのは1つだけ"]),
     ("keyrow",["<b>名前が伝える情報は、既に3か所にある</b>",
       f"{C('schemaRef')}／{C('documentType')}／鍵の名前。"
       "<b>同じことを3か所が言っている</b>"]),
     ("",["<b>機械は名前を見ていない</b>",
       "実装は分岐の形から鍵を取り出している。名前を変えても実装は動く"]),
   ])),

 sec("04","B を採るなら、こう言える",
   "私は A を推すが、<b>B にも成り立つ言い分がある</b>ので、そのまま置く。",
   tbl(["B の言い分","どこまで成り立つか"],[
     ("",["鍵だけで型の群が分かる",
       f"{C('specKind: usecase')} は {C('kind: usecase')} より読み手に多くを伝える。"
       "<b>ただし同じ行に <code>schemaRef</code> が並んでいる</b>"]),
     ("",["移す手間がかからない",
       "<b>これは強い。</b>A なら文書253本の鍵名を変えることになる"]),
     ("keyrow",["将来、軸が2つになったとき",
       "そのときは名前で分ける必要が出る。<b>ただし A でも、そのとき名前を足せばよい</b> ── "
       "1つから2つへ増やすほうが、6つを揃えるより易しい"]),
   ])),

 sec("05","私が外したこと",
   "決定に「無駄」と書いたが、その理由は誤っていた。",
   tbl(["書いたこと","実際"],[
     ("keyrow",["型ごとに自分の名前を付けているだけ",
       "<b>誤り。</b><code>specKind</code> は3本が共有している"]),
     ("",["だから無駄である",
       "<b>結論は変わらないが、理由が変わる。</b>"
       "無駄なのは「型ごとの名前」だからではなく、"
       "<b>新しい型を足すたびに決めることが増え、その基準が無い</b>から"]),
   ])),
])
out=("<title>種別の鍵を、1つにするか群ごとに分けるか</title>"
     f"<style>{CSS}\n{extra}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/kind-key-comparison.html").write_text(out,encoding="utf-8")
print("書いた",len(out))
