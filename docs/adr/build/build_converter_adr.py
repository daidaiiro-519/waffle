import sys, pathlib, re
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S); sys.path.insert(0,"/home/daidaiiro/workspace/waffle/.claude/skills/design-svg")
from _common import CSS, sec, fold, tbl, extra
from svg_engine.compose import render_figure
from svg_engine.tokens import DEFAULT_THEME

FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
def figure(inner, vb, cap, minw="40rem"):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:{minw};width:100%;height:auto;display:block" {FF}>{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')
def txt(x,y,t,size=12,fill="var(--ink)",w=600,anchor="middle"):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{w}" fill="{fill}">{t}</text>')
def band(x,y,w,h,stroke="var(--rule)",dash=""):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" '
            f'stroke="{stroke}" stroke-width="1.3"{d}/>')

# ── 図1 ── 表は2枚あり、持ち主が違う
a  = band(12,30,250,150,"var(--rule)")
a += txt(137,52,"呼ぶ側（仕様を持つ側）",11,"var(--ink-faint)",500)
a += band(30,66,214,44,"var(--infer)") + txt(137,86,"対応表",12,"var(--infer)")
a += txt(137,101,"言い分 → どの部品でどう組むか",9.5,"var(--ink-faint)",400)
a += band(30,122,214,44,"var(--infer)") + txt(137,142,"変換器",12,"var(--infer)")
a += txt(137,157,"宣言を、節点・辺・囲みへ直す",9.5,"var(--ink-faint)",400)
a += band(378,30,250,150,"var(--rule)")
a += txt(503,52,"design-svg（描く側）",11,"var(--ink-faint)",500)
a += band(396,66,214,44,"var(--fact)") + txt(503,86,"目録",12,"var(--fact)")
a += txt(503,101,"何を受け取れるか（実装から導く）",9.5,"var(--ink-faint)",400)
a += band(396,122,214,44,"var(--rule)") + txt(503,142,"エンジン",12)
a += txt(503,157,"部品・トークン・配置戦略",9.5,"var(--ink-faint)",400)
a += (f'<line x1="262" y1="88" x2="376" y2="88" stroke="var(--ink-faint)" stroke-width="1.3"/>'
      f'<polygon points="368,88 360,84.5 360,91.5" fill="var(--ink-faint)"/>')
a += txt(319,80,"見る",9.5,"var(--ink-faint)",400)
a += (f'<line x1="262" y1="144" x2="376" y2="144" stroke="var(--ink-faint)" stroke-width="1.3"/>'
      f'<polygon points="368,144 360,140.5 360,147.5" fill="var(--ink-faint)"/>')
a += txt(319,136,"呼ぶ",9.5,"var(--ink-faint)",400)
FIG1 = figure(a,"0 0 640 196",
  "<b>表は2枚あり、持ち主が違う。</b>目録は「何を受け取れるか」だけを答え、"
  "対応表は「何を表すか」を決める。混ぜると、変化の少ない描く側が、変化の多い仕様側と"
  "同じ速度で動かされる。")

# ── 図2 ── 引っ越しの前と後（エンジン自身に描かせる）
th = dict(DEFAULT_THEME, **{
    "color.box-fill":"var(--surface)","color.box-stroke":"var(--rule)","color.ink":"var(--ink)",
    "color.line":"var(--ink-faint)","color.ink-faint":"var(--ink-faint)",
    "color.accent":"var(--against)","color.accent-bg":"var(--surface)",
    "size.stroke-width-focus":1.6,
    "font.family":"Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"})
_b = render_figure(
    [{"id":"宣言","label":"仕様の宣言"},
     {"id":"conv","label":"変換器","role":"focus"},
     {"id":"表","label":"網羅の表","role":"focus"},
     {"id":"engine","label":"エンジン"}],
    [{"from":"宣言","to":"conv"},{"from":"conv","to":"engine"},{"from":"表","to":"conv"}],
    groups=[{"label":"いま ── design-svg の中に入っている","members":["conv","表","engine"]}],
    direction="LR", theme=th)
FIG2_INNER = re.sub(r'^<svg[^>]*>','',_b)[:-6]
FIG2_VB = re.search(r'viewBox="([^"]+)"',_b).group(1)
FIG2 = figure(FIG2_INNER, FIG2_VB,
  "<b>いま、変換器と網羅の表が描く側の中にある。</b>色を付けた2つが引っ越す対象。"
  "この図はこのエンジン自身が描いている。", "30rem")

body="".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>変換器は仕様の側が持ち、描く側は目録だけを公開する</h1>'
 '<p class="lede">描く側の実装は完成し、目録も公開された。残っているのは、仕様の語彙から'
 'その目録へ橋を架けることである。<b>いまその橋は描く側の中にあり、網羅の試験もそこから'
 '仕様の語彙を借りている。</b>橋を仕様の側へ移し、描く側には一般名詞だけを残す。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">'
  '<b>言い分から部品への対応表と、それを実行する変換器は、仕様を持つ側が所有する。</b>'
  '描く側が公開するのは目録だけで、<b>何を表せるかは知らない</b>。</p>'
  '<div class="key"><span class="lbl">判定の基準</span>'
  '<span class="txt">仕様に言い分を1つ足したとき、<b>描く側のファイルを1つでも触るなら'
  '境界が漏れている</b>。この基準で、いま触ることになる4ファイルを引っ越しの対象とする。</span></div>'
  '<div class="key"><span class="lbl">同時に決めること</span>'
  '<span class="txt">対応表は<b>部品名までではなく、渡す値まで</b>書く。目録が'
  '必須・任意を機械で答えられるようになったので、承認したらそのまま変換器が書ける粒度にする。</span></div></div>'),

 sec("02","表は2枚あり、持ち主が違う",
  "目録は「何を受け取れるか」、対応表は「何を表すか」。同じ表に見えるが、変わる速度が違う。",
  FIG1 + tbl(["表","答えること","持ち主","変わるとき"],[
    ("keyrow",["目録","どの部品があり、何を読み、どんなトークンで見た目が決まるか",
      "描く側","部品を足したとき（実装から導かれるので、書き忘れが起きない）"]),
    ("keyrow",["対応表","どの言い分を、どの部品でどう組むか",
      "仕様の側","言い分が増減したとき・組み方を変えたとき"]),
  ])),

 sec("03","引っ越すもの",
  "判定の基準（言い分を1つ足したときに触るか）で選ぶと、4つになる。",
  FIG2 + tbl(["対象","いまどこにあるか","なぜ引っ越すか"],[
    ("keyrow",["変換器 <code>convert()</code>","描く側の例の中",
      "<b>腐敗防止層は下流が持ち、下流に置くもの</b>。いまは上流の内部にある"]),
    ("keyrow",["網羅の表（言い分×倍率）","描く側の例の中",
      "<b>描く側の「崩れていない」の定義が、仕様の語彙で書かれている</b>。"
      "言い分が1つ増えると試験の一覧が動く"]),
    ("",["網羅の試験","描く側の試験の中",
      "上の表を読んでいる。試験の識別子が仕様の語彙になっている"]),
    ("",["言い分の宣言たち","描く側の例の中","仕様側のデータであって、描く側の例ではない"]),
  ]),
  fold("描く側に残すものを開く",
   '<p>描く側の試験には、<b>描き方の言葉で名づけた回帰の表</b>を別に用意する'
   '（格子の配置・輪の配置・長いラベル・入れ子の群・多段をまたぐ辺…）。'
   '網羅の必要性は描く側のものだが、<b>網羅の数え方は仕様側のもの</b>である。'
   'いまは1つの表が両方を担っているので、そこで分ける。</p>')),

 sec("04","「対応」だけが2通りに分かれる",
  "他の言い分は1つの部品へ落ちるが、これだけは成果物の形が2つある。",
  tbl(["条件","何になるか","なぜ"],[
    ("keyrow",["交点が図を持たない","<b>成果物の書式そのもの</b>（Markdown・HTMLの表）",
      "縦横の対応を読ませるのに、絵である必要が無い。書式の表のほうが読みやすく、"
      "検索も引用もできる"]),
    ("keyrow",["交点が図を持つ","<b>格子の配置＋入れ子</b>",
      "交点の中身が図なら、書式の表には入らない。画像として表現したいときだけ、絵にする"]),
  ]),
  fold("いまの実装との食い違いを開く",
   '<p>いまの変換器は<b>常にSVGの表を作る</b>。上の分岐は後から決まったもので、'
   '試作にしか実装されていない（その試作は版に入れていない）。'
   '引っ越しのときに、この分岐を含めて書き直す。</p>')),

 sec("05","対応表の粒度",
  "部品名までしか書かないと、書く段でもう一度調べ直すことになる。",
  '<p>目録が、部品ごとの<b>必須の鍵と任意の鍵</b>を機械で答えられるようになった。'
  'だから対応表は「どの部品を使うか」ではなく、<b>「どの部品に、どの値を、どこから取って渡すか」</b>'
  'まで書く。渡す値の名前と要否は目録から引くので、対応表が持つのは'
  '<b>仕様の欄から部品の鍵への割り当て</b>だけになる。</p>'
  '<p>こうすると、部品の入力が変わったときに<b>目録と対応表の突き合わせで機械的に検出できる</b>'
  '── 対応表が目録に無い鍵を指していたら落とす、という形にできる。</p>'),

 sec("06","答えないこと",None,
  '<p>この決定は<b>持ち主と粒度だけを決める</b>。'
  'どの言い分をどの部品へ割り当てるかという中身は、対応表そのものが持つ'
  '（既にある案を、上の粒度へ更新して別途承認する）。</p>'
  '<p>変換器を仕様側のどの層へ置くか（ポートの位置・アダプタの置き場所）も、'
  'この決定の外にある。仕様側の構成に従う。</p>'),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span>'
 '<span class="m">2026-08-30</span></div></section>',

 sec("08","関連","この決定は、描く側の規律を決めた判断と対になる。","",
  fold("前後の決定を開く（4件）",
    tbl(["種類","対象"],[
      ("keyrow",["先立つ判断","描く側にヘキサゴナル層構成を敷かず、3規約と試験で縛る（承認済み）"
        " ── <b>その規約の1つが「呼ぶ側の語彙を持たない」で、この決定はその続き</b>"]),
      ("",["先立つ事実","目録の公開（実装から導かれるので、部品を直せば目録も直る）"]),
      ("",["後続の作業","対応表を、渡す値まで書いた粒度へ更新して承認する"]),
      ("",["縛る対象","変換器・網羅の表・網羅の試験・言い分の宣言たち（4件）"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.2rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
"""
out=("<title>変換器は仕様の側が持ち、描く側は目録だけを公開する</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-converter-ownership.html").write_text(out,encoding="utf-8")
print("書いた",len(out))
