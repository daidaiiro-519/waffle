import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, extra

A = "https://claude.ai/code/artifact/"
CARDS = [
 ("1","事業領域","Business Domain","0471e3e5-f19e-4507-9385-b6fb862e9525",
  "顧客に何を提供している事業か。<b>業務領域の分類の基準</b>になる","0 → 1"),
 ("2","業務領域","Subdomain","bbff2e22-40f6-4d2e-9b04-1377360775e1",
  "中核・一般・補完の分類と、その根拠。<b>境界は導く</b>","7 → 7"),
 ("3","区切られた文脈","Bounded Context","719c98c5-b1f5-4f4c-94ee-ab9245d82cc2",
  "言葉が一貫する範囲。持つのは<b>通じる言葉の定義だけ</b>","1 → 1"),
 ("4","集約","Aggregate","7754906c-ab81-4c29-8c55-78f1841438da",
  "<b>いちばん変わる。</b>定義が出て、状態と遷移が消える","2 → 2"),
 ("5","エンティティ","Entity","a01cd642-9885-4dfa-926b-aeb35a2c6c10",
  "<b>新設。</b>同一性を持ち、状態が変わるもの","0 → 2"),
 ("6","値オブジェクト","Value Object","de9fa721-f9d6-4a08-96dc-6e6e33529745",
  "<b>新設。</b>値で等しさが決まり、変わらないもの","0 → 10"),
 ("7","業務ユースケース","Use Case","16369065-66b1-496a-a1d0-aaa0c1093c23",
  "外から呼ばれる用事。<b>基準とシナリオの対応</b>が見える","30 → 30"),
 ("8","業務サービス","Domain Service","db0885b5-af9d-42f1-8a6f-09a39b4d2812",
  "集約をまたぐ判断。<b>唯一、欄が変わらない</b>","4 → 4"),
]

cards = '<div class="grid">' + "".join(
 f'<a class="card" href="{A}{u}"><div class="c-h">'
 f'<span class="c-n">{n}</span><span class="c-cnt">{cnt}</span></div>'
 f'<p class="c-ja">{ja}</p><p class="c-en">{en}</p><p class="c-d">{d}</p></a>'
 for n, ja, en, u, d, cnt in CARDS) + "</div>"

added = tbl(["新しい欄","どの種別に","何のために"],[
 ("keyrow",["名前の英語表記","<b>全種別</b>",
   "規約が綴りの流儀を導く元になる。<b>実装の型名は書かない</b>"]),
 ("keyrow",["この事業が顧客へ提供しているもの","事業領域",
   "中核・一般・補完は<b>事業領域を基準にした相対評価</b>。基準が無いと分類に根拠が無い"]),
 ("",["属する事業領域","業務領域","所属をディレクトリではなく宣言が運ぶ"]),
 ("",["属する業務領域","業務ユースケース","同上。<b>業務領域の境界はここから導く</b>"]),
 ("keyrow",["確かめる単位","シナリオ",
   "仕様と実装を結ぶ<b>三角形の1辺</b>。指すのは仕様自身の識別子"]),
 ("",["<span class='sub'>（変える内側のエンティティ）</span>","<span class='sub'>集約の操作</span>",
   "<span class='sub'>任意。階層を持つ集約でだけ書く ── bc-waffle では全部空になる</span>"]),
])

body = "".join([
 '<header><p class="eyebrow">完成イメージ ── 索引</p>'
 '<h1>Domain の8種別</h1>'
 '<p class="lede">型を承認する前に、<b>実際に描かれる文書</b>を8種別ぶん。'
 '中身は bc-waffle の実物から取っている。'
 '<b>いずれも手で描いたもので、描画の機能はまだ無い。</b></p></header>',

 sec("01","8枚","1枚ずつ開く。<b>44本から57本</b>になる。", cards),

 sec("02","足した欄は5つだけ",
  "8種別ぜんぶ描いても、新しい欄は<b>5つ</b>しか出てこない。"
  "<b>実装の語彙は1つも入っていない。</b>",
  added),

 '<p class="foot">いまとの差と、そう決めた理由は'
 '<a href="https://claude.ai/code/artifact/e0e51605-4fd9-4212-ace1-28fa5bf1075d">Domain の型</a>'
 'が持つ。<b>この索引は、8枚の中身を持たない</b> ── 同じことを2か所に書かないため。</p>',
])

EXTRA = extra + """
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));gap:.9rem}
.card{display:flex;flex-direction:column;gap:.15rem;text-decoration:none;color:inherit;
      border:1px solid var(--rule);border-radius:3px;background:var(--surface);
      padding:1rem 1.1rem 1.1rem;transition:border-color .12s,background .12s}
.card:hover{border-color:var(--infer);background:var(--infer-bg)}
.c-h{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.35rem}
.c-n{font-family:var(--mono);font-size:.72rem;color:var(--ink-faint)}
.c-cnt{font-family:var(--mono);font-size:.7rem;color:var(--ink-faint);
       border:1px solid var(--rule);border-radius:2px;padding:.2em .45em}
.c-ja{font-family:var(--serif);font-size:1.1rem;font-weight:600;margin:0}
.c-en{font-family:var(--mono);font-size:.76rem;color:var(--ink-faint);margin:0}
.c-d{font-size:.85rem;line-height:1.75;color:var(--ink-soft);margin:.45rem 0 0}
.c-d b{color:var(--ink)}
.foot{font-size:.82rem;line-height:1.75;color:var(--ink-faint);
      border-top:1px solid var(--rule);padding-top:1rem}
"""
html = ("<title>Domain の8種別</title>"
        f"<style>{CSS}\n{EXTRA}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/tier2-domain-preview.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")
