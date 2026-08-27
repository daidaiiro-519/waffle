import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, extra

A="https://claude.ai/code/artifact/"
def a(uid,t): return f'<a href="{A}{uid}">{t}</a>'

def ev(when, kind, what, made=None, decided=None, note=None):
    K={"問い":"q","調べ":"probe","決定":"dec","承認":"ok","訂正":"fix","作る":"make"}
    o=f'<div class="ev ev--{K[kind]}"><div class="ev-when">{when}</div>'
    o+=f'<div class="ev-body"><span class="ev-kind">{kind}</span>'
    o+=f'<p class="ev-what">{what}</p>'
    if made: o+=f'<p class="ev-made">成果物 ── {made}</p>'
    if decided: o+=f'<p class="ev-dec">{decided}</p>'
    if note: o+=f'<p class="ev-note">{note}</p>'
    return o+"</div></div>"

TL = "".join([
 ev("08-14<br>18:28","承認","図の語彙を、描き方の名前から主張の名前へ移す",
    made=a("a5b142e3-da78-4de3-87a9-540b3d91c389","図の語彙を、描き方の名前から主張の名前へ移す"),
    decided="<b>書き手は描き方を選ばない。</b>描き方は主張から決まる"),
 ev("08-14<br>23:29","承認","決定の書式が3本まとまって固まる",
    made=a("383983ee-1c48-4a6b-b18c-fa73c1fc12cb","図の宣言を、主張を軸にした形へ")+"／"
        +a("e278fb60-1faf-4406-83f1-1c8670b59be3","理由は論証の連鎖として書く")+"／"
        +a("e8397ab8-292a-4b7a-89f8-0ff1d1dee18e","仕様の下限"),
    note="この時点以降の決定は8節の書式で書かれる。<b>これより前のものは古い書式のまま残る</b>"),
 ev("08-15<br>00:09","訂正","「図の宣言は、切り替えの前に全部移す」を<b>取り下げ</b>",
    note="移行の対象を数えた結果を決め手に据えていた。<b>向きは knowledge から直接導かれ、決めることが残っていない</b>"),
 ev("08-15<br>13:10","承認","描くことと、配ることを分ける",
    made=a("dffe15cf-d4f7-4907-85e8-749bd7df8c85","描くことと、配ることを分ける"),
    decided="受け入れ基準49件のうち12件が配置だった"),
 ev("08-15<br>16:31","承認","値オブジェクトとエンティティを、独立して書ける単位にする",
    made=a("1a0663a7-5c19-433f-a623-899e83d23643","値オブジェクトとエンティティを、独立して書ける単位に")),
 ev("08-15<br>17:42","作る","値オブジェクトとエンティティの完成イメージ",
    made=a("93fd3da5-b0ce-4bc2-8b0d-e569383ad12a","値オブジェクトとエンティティを、独立した文書にすると"),
    note="ここで <code>implementationBinding</code> を勝手に足し、<b>仕様と実装の境界を越えたと指摘された</b>"),
 ev("08-15<br>夕","問い","<b>「Schema が document.json の骨格を作るのは、ユースケースではなく Schema 自身では」</b>",
    note="ここから Schema の再定義が始まる"),
 ev("08-15<br>夜","調べ","30のユースケースのアクターを数え、<code>x-*</code> の使用回数を数えた",
    decided="<b>Schema の実装は27行・コマンド0件。骨格を作るユースケースは412行。</b>"
            "<code>x-render-order</code> は156か所で使われ、仕様に0回"),
 ev("08-15<br>21:23","作る","Schema の形と語彙の完成イメージ（全10節）",
    made=a("908467d6-7ef2-41ca-8585-fb6badd55eb2","Schema を仕様から実装する"),
    decided="段1／段2／段3 の言い方は<b>ここで生まれた</b>。語彙は<b>11語</b>と書かれている"),
 ev("08-15<br>21:52","承認","<b>Schema を仕様から実装し、型は Document として置く</b>",
    made=a("84fffac7-cf0a-42bc-8c3b-c0f0002b6f68","Schema を仕様から実装し、型は Document として置く"),
    decided="JSON Schema は宣言から描かれる成果物になる。<code>x-*</code> は型に置き、実体へ写さない"),
 ev("08-15<br>22:44","作る","索引を50本へ更新",
    made=a("227e331a-b637-473e-b635-78ad8422d635","この作業の記録の索引")),
 ev("08-15<br>23:09","調べ","描ける部品14種を、宣言と描画結果の対で並べた",
    made=a("ce284003-5396-43dd-9ea2-4b6f441a067e","いま描ける14種と、図がこれからどうなるか"),
    note="<b><code>steps</code> は部品ではなかった</b>（引数名を拾っていた）。"
         "「階層と順序が同じ絵になる」という報告も、のちに取り消した"),
 ev("08-15<br>夜","調べ","描き方の6語が<b>2つの高さに分かれる</b>と測った",
    decided="ブロックに付く4語（<code>x-render</code>・順序・深さ・隠す）と、"
            "schema の根に付く2語（<code>x-render-target</code>・<code>x-frontmatter</code>）",
    note="<b>ここが「7語」の元になった測定。ただし、まとめると決めてはいない</b>"),
 ev("08-15<br>23:51","承認","<b>語彙を意味の名前だけにし、構造の部品と共通の欄を主張から分ける</b>",
    made=a("a733ef9b-6ae7-4b7a-bff7-937b7a1c3727","語彙を意味の名前だけにし、構造の部品と共通の欄を主張から分ける"),
    decided="群を3つに分ける。<b>足りない4つ</b>（突き合わせる器・読む必要の度合い・囲み・差分の語彙）",
    note="<b>語彙の数も、<code>x-*</code> の新しい名前も、この決定は定めていない</b>"),
 ev("08-16<br>00:38","調べ","16の主張を、宣言から実際に描いた",
    made=a("3bd1bca9-2441-4452-84fc-1b4376b379be","意味の名前で書いたとき、何がどう出るか"),
    decided="<b>16すべて描けた。</b>描く手の欠陥3件（偏差の負値・囲みの余白・順序の右端）"),
 ev("08-16<br>00:59","承認","<b>コマンドを、判断に要るデータのある場所へ戻す</b>（書き直したうえで）",
    made=a("be62c1c6-4232-40ad-ac40-d61fda778a54","コマンドを、判断に要るデータのある場所へ戻す"),
    decided="Schema は骨格を作る1件、Document は5件",
    note="<b>前の版を上書きした。</b>書き直す前は Schema が3件だった。"
         "<b>段の語彙は入れなかった</b>ので、いまも「集約」で語っている"),
 ev("08-16<br>01:04","作る","再定義の計画",
    made=a("25f4d1b1-6997-4dd6-b2d7-aae5606f834e","何を、どの順で書き直すか"),
    note="<b>決定の題名と承認の状態しか見ずに立てた。</b>"
         "「語彙7語」という<b>決まっていない数</b>を第1手の中身として書いた"),
 ev("08-16<br>01:08","作る","図の置き場所の決定を、いまの書式へ書き直した",
    made=a("f2522925-e9e6-47d7-8894-cd2f493fdd64","図の宣言を、Document の内側の値として置く"),
    decided="<b>未承認のまま。</b>「文章の部品13種は分ける」が語彙の決定とぶつかっていたので落とした"),
 ev("08-16<br>いま","訂正","<b>食い違いが3つ見つかった</b>",
    note="いずれも<b>あなたの指摘で見つかった</b>。私は自分で突き合わせていない"),
])

gap = tbl(["食い違い","どこで生まれたか","いま何が正しいか"],[
 ("keyrow",["<b>語彙が7語だという前提</b>",
   "6語→2語の<b>測定</b>から私が計算し、会話で一度言い、計画に書き写した",
   "<b>決まっていない。</b>承認済みの決定が定めているのは群の分け方と、"
   "足りない4つだけ。<code>x-*</code> の名前も数も射程外"]),
 ("keyrow",["<b>決定と完成イメージが別の語彙</b>",
   "段1／段2／段3 は完成イメージで生まれたが、"
   "そのあと書いた決定に持ち込まなかった",
   "<b>決定は「集約」、完成イメージは「段」で語っている。</b>同じことを2通りで言っている"]),
 ("",["<b>コマンドの表と本文</b>",
   "書き直したとき、表の2行だけ直して本文を見直さなかった",
   "本文は「読み方の指針は Schema の<b>別のコマンド</b>が返す」と書くが、"
   "<b>表にそのコマンドが無い</b>"]),
])

why = tbl(["起きた理由","現れ方"],[
 ("keyrow",["<b>決定に「置き換えられた」という状態が無い</b>",
   "Document には終端化があるのに、決定には無い。"
   "<b>古くなった決定が承認済みのまま残り、どれが最新か分からない</b>"]),
 ("keyrow",["<b>書き直しを、同じ場所へ上書きした</b>",
   "コマンドの決定は Schema 3件 → 1件へ書き直したが、"
   "<b>文書からは前の版が辿れない</b>"]),
 ("",["<b>新しい決定のあと、先立つ決定を読み返していない</b>",
   "計画にその規律を書いておきながら、やっていない。"
   "食い違い3つとも、指摘されて初めて見つかった"]),
 ("",["<b>計画を、題名と状態だけで立てた</b>",
   "決定の本文を読み返していないので、決まっていないことを前提にした"]),
])

body="".join([
 '<header><p class="eyebrow">やり取りの記録</p>'
 '<h1>Schema の再定義は、どう進んだか</h1>'
 '<p class="lede">成果物の更新時刻を軸に、何を問い、何を測り、何を決めたかを並べる。'
 '<b>食い違いがどこで生まれたかも、同じ線の上に置く。</b></p></header>',

 f'<section><h2><span class="num">01</span>時間の順に見る</h2>'
 f'<p class="lead">左の時刻は成果物の更新時刻。時刻の無いものは、前後の成果物から位置を決めた。</p>'
 f'<div class="tl">{TL}</div></section>',

 sec("02","食い違いは、どこで生まれたか",
   "3つとも<b>決定と決定の間</b>ではなく、<b>決定と、その周りで書いたものの間</b>で生まれている。",
   gap),

 sec("03","なぜ気づけなかったか",
   "仕組みの側に2つ、進め方の側に2つ、原因がある。",
   why),

 sec("04","いま確かなこと",
   "承認済みの決定が<b>実際に定めていること</b>だけを並べる。会話で言っただけのものは含めない。",
   tbl(["決定","定めていること","定めていないこと"],[
     ("keyrow",["Schema を仕様から実装し、型は Document として置く",
       "JSON Schema は宣言から描かれる成果物になる／"
       "<code>x-*</code> は型に置き実体へ写さない／図は形が段1・値が Document",
       "<b>語彙の名前と数</b>"]),
     ("keyrow",["語彙を意味の名前だけにし、構造の部品と共通の欄を主張から分ける",
       "群を3つに分ける／文字の意味は4つ／図は主張8つ／"
       "<b>足りない4つ</b>／<code>divider</code> を落とす",
       "<b><code>x-*</code> をどうまとめ、どう名づけるか</b>"]),
     ("",["コマンドを、判断に要るデータのある場所へ戻す",
       "Schema は骨格を作る／Document は5件／参照は持つが解決しない",
       "<b>どの段の話か</b>／読み方の指針を返す操作の扱い"]),
     ("",["図の宣言を、Document の内側の値として置く",
       "図の宣言は値オブジェクト／主張は属性であって種別ではない／守り手は schema ひとつ",
       "<b>未承認</b>"]),
   ])),

 sec("05","次に決めること",
   "計画を立て直す前に、<b>決まっていない3つ</b>を先に決める。",
   tbl(["決めること","なぜ先か"],[
     ("keyrow",["<code>x-*</code> をまとめるか、どう名づけるか",
       "<b>計画の第1手の中身そのもの。</b>ここが決まらないと Schema の仕様が書けない"]),
     ("",["決定に「置き換えられた」を入れるか",
       "入れないと、今回と同じことがまた起きる"]),
     ("",["図の置き場所の決定を承認するか",
       "Schema の仕様に図の宣言が入るので、その入力になる"]),
   ])),
])

extra2 = extra + """
.tl{display:flex;flex-direction:column;gap:0;border-left:2px solid var(--rule);margin-left:.4rem}
.ev{display:grid;grid-template-columns:5.2rem 1fr;gap:1rem;padding:.9rem 0 .9rem 1.1rem;position:relative}
.ev+.ev{border-top:1px solid var(--rule-soft)}
.ev::before{content:"";position:absolute;left:-6px;top:1.3rem;width:10px;height:10px;
            border-radius:50%;background:var(--surface);border:2px solid var(--rule)}
.ev--ok::before{border-color:var(--infer);background:var(--infer)}
.ev--dec::before{border-color:var(--infer)}
.ev--fix::before{border-color:var(--against);background:var(--against)}
.ev--probe::before{border-color:var(--fact)}
.ev--q::before{border-color:var(--assume);background:var(--assume)}
.ev-when{font-family:var(--mono);font-size:.72rem;color:var(--ink-faint);line-height:1.5;padding-top:.15rem}
.ev-body{display:flex;flex-direction:column;gap:.3rem;min-width:0}
.ev-kind{font-family:var(--mono);font-size:.63rem;letter-spacing:.1em;color:var(--ink-faint)}
.ev--ok .ev-kind{color:var(--infer)} .ev--fix .ev-kind{color:var(--against)}
.ev--probe .ev-kind{color:var(--fact)} .ev--q .ev-kind{color:var(--assume)}
.ev-what{font-size:.95rem;line-height:1.65;font-weight:600}
.ev-made{font-size:.82rem;color:var(--ink-faint);line-height:1.7}
.ev-made a{color:var(--fact);text-decoration:none;border-bottom:1px solid var(--rule)}
.ev-dec{font-size:.86rem;color:var(--ink-soft);line-height:1.75}
.ev-note{font-size:.84rem;color:var(--ink-soft);line-height:1.75;
         border-left:2px solid var(--against);padding-left:.7rem}
.lead{font-family:var(--serif);font-size:1.02rem;font-weight:600;line-height:1.65;
      border-left:3px solid var(--ink);padding-left:.85rem}
"""
html=("<title>Schema の再定義は、どう進んだか</title>"
      f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/redefinition-timeline.html").write_text(html,encoding="utf-8")
print("書いた",len(html))
