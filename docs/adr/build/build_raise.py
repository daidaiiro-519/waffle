"""完成イメージ ── 宣言1本が型1本になるまで、9段を実際に通す。"""
import html
import sys
import pathlib

S = "/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0, S)
from _common import CSS, sec, fold, tbl, extra

e = html.escape
C = lambda s: f"<code>{s}</code>"


def code(s, label=None):
    head = f'<div class="exlbl">{label}</div>' if label else ""
    return f'<div class="scroll">{head}<pre class="ex">{e(s)}</pre></div>'


DECL = """型: MemoSchema/v1
種別: usecase ／ aggregate

共有する組み立て:
  KeyGloss   まとまり { key: 値(文字列), gloss: 値(文字列) }

ブロック:
  title    形=値(文字列)          修飾=必須
           読み方="まず何を扱う文書かを掴むために読む"
  errors   形=並び(KeyGloss)      修飾=最小の個数 1
           読み方="失敗の仕方を読む。条件が重なっていないかを確かめる"
  steps    形=入れ子の木(上限3)   読み方="順序を読む。分岐は誤りの側が持つ"
  figure   形=図                  読み方="何を主張する図かを読む"

枝ごとの必須ブロック:
  usecase   → title, errors, steps
  aggregate → title, figure"""

STEP1 = """{
  "type": "object",
  "properties": {
    "documentId": { "type": "string" },
    "schemaRef":  { "type": "string" },
    "kind":       { "type": "string" },
    "role":       { "type": "string", "enum": ["entity","template"],
                  "default": "entity" },
    "usable":     { "type": "string" },
    "createdAt":  { "type": "string" },
    "updatedAt":  { "type": "string" },
    "tags":       { "type": "array", "items": { "type": "string" } },
    "content":    { "type": "object" }
  },
  "required": ["documentId","schemaRef","kind","usable","createdAt","updatedAt","content"]
}"""

STEP2 = """"kind": { "type": "string", "enum": ["usecase", "aggregate"] }"""

STEP3 = """"$defs": {
  "KeyGloss": {
    "type": "object",
    "properties": { "key": { "type": "string" }, "gloss": { "type": "string" } },
    "required": ["key", "gloss"],
    "additionalProperties": false
  }
}"""

STEP4 = """"content": {
  "type": "object",
  "properties": {
    "title":  {},
    "errors": {},
    "steps":  {},
    "figure": {}
  }
}"""

STEP5 = """"title":  { "type": "string" },

"errors": { "type": "array", "items": { "$ref": "#/$defs/KeyGloss" } },

"steps":  { "$ref": "#/$defs/Tree3" },

"figure": { "$ref": "#/$defs/Figure" }"""

STEP5B = """"Tree3": {
  "type": "object",
  "properties": {
    "name":     { "type": "string" },
    "summary":  { "type": "string" },
    "children": { "type": "array", "items": { "$ref": "#/$defs/Tree2" } }
  },
  "required": ["name", "summary"],
  "additionalProperties": false
}
"Tree2": { … children は Tree1 を指す … }
"Tree1": { … children を持たない … }"""

STEP6 = """"errors": {
  "type": "array",
  "items": { "$ref": "#/$defs/KeyGloss" },
  "minItems": 1
},
"content": {
  "additionalProperties": false
}"""

STEP7 = """"title": {
  "type": "string",
  "description": "まず何を扱う文書かを掴むために読む",
  "x-write": "扱う対象を1文で書く。識別子の言い換えにしない"
}"""

STEP8 = """"allOf": [
  { "if":   { "properties": { "kind": { "const": "usecase" } } },
    "then": { "properties": { "content": {
                "required": ["title", "errors", "steps"] } } } },
  { "if":   { "properties": { "kind": { "const": "aggregate" } } },
    "then": { "properties": { "content": {
                "required": ["title", "figure"] } } } }
]"""

STEP9 = """"content": { "properties": {
  "errors": { "x-render": "table" },
  "steps":  { "x-render": "list" }
} },
"x-target": "docs/{documentId}.md" """

steps = tbl(["順", "すること", "できるもの"], [
 ("keyrow", ["<b>1</b>", "<b>表紙を置く</b>", "外側の欄と、その必須。<b>どの型でも同じ</b>"]),
 ("keyrow", ["<b>2</b>", "<b>種別の枝を作る</b>", "<code>kind</code> に選択肢が付く"]),
 ("", ["<b>3</b>", "<b>共有する組み立てを置く</b>", "<code>$defs</code> ができる"]),
 ("keyrow", ["<b>4</b>", "<b>ブロックの器を、宣言の順に並べる</b>", "中身はまだ空"]),
 ("", ["<b>5</b>", "各ブロックの中身を、文法に従って組む", "形が入る"]),
 ("", ["<b>6</b>", "修飾を当てる", "取れる値が狭まる"]),
 ("keyrow", ["<b>7</b>", "<b>説明を、鍵の隣に置く</b>", "読み方と記入の指針が付く"]),
 ("", ["<b>8</b>", "枝ごとの必須ブロックを当てる", "枝によって必須が変わる"]),
 ("", ["<b>9</b>", "描き方と宛先を置く", "成果物の作り方が決まる"]),
])

check = tbl(["確かめること", "どう確かめるか", "外れたら何が言えるか"], [
 ("keyrow", ["<b>同じ宣言からは、同じ型になる</b>",
   "同じ宣言を2回起こして、<b>文字単位で比べる</b>",
   "<b>手順のどこかが順序に依っていない</b> ── 欄の並びが辞書順で揺れる、など"]),
 ("keyrow", ["<b>段を飛ばすと壊れる</b>",
   "段3 を飛ばして起こすと、段5 の <code>$ref</code> が指す先を失う",
   "<b>順序が本物である</b>。飛ばして通るなら、その順序に根拠が無い"]),
 ("", ["部品だけで組める",
   "起こす手順のどこにも、<b>型ごとの分岐が現れない</b>",
   "現れたら、<b>段1 の部品が足りていない</b>"]),
 ("", ["起こした型で、実物が通る",
   "その型を指す文書を、起こした型で判定する",
   "通らなければ、宣言か手順のどちらかが実物と合っていない"]),
])

decided = tbl(["決めたこと", "中身", "なぜ"], [
 ("keyrow", ["<b>読み方は <code>description</code> へ置く</b>",
   "JSON Schema の標準の欄をそのまま使う",
   "<b>ほかの道具も読める。</b>独自の名前にすると、Waffle の外から見えなくなる"]),
 ("keyrow", ["<b>記入の指針は <code>x-write</code> へ置く</b>",
   "標準に対応する欄が無いので、独自の名前にする",
   "<b>読み方と混ぜない。</b>読むための言葉と、書くための言葉は宛先が違う"]),
 ("", ["<b>入れ子は展開する</b>",
   "上限のぶんだけ <code>Tree3</code>／<code>Tree2</code>／<code>Tree1</code> を作る",
   "<b>自分自身への <code>$ref</code> だと、上限を守る仕掛けが別に要る。</b>"
   "展開すれば、守るまでもなく成り立つ"]),
 ("", ["<b>枝は <code>allOf</code> と <code>if</code>/<code>then</code> で当てる</b>",
   "枝ごとに <code>required</code> だけを足す",
   "<b>名前つきの入れ物を作らない。</b>枝が言うのは「この枝ではこれらが要る」だけ"]),
])

open_q = tbl(["項目", "何が決まっていないか", "どこで決めるか"], [
 ("keyrow", ["<b>図の中身</b>", "<code>$defs.Figure</code> の形",
   "<b>図の仕様</b> ── <b>第1段の中</b>。段1 の実装より前"]),
 ("", ["描き方の語", "<code>x-render</code> に何が書けるか", "<b>段2 の仕様</b>"]),
 ("", ["宛先の書き方", "<code>{documentId}</code> のような差し込みをどこまで許すか",
   "<b>段2 の仕様</b>"]),
])

body = "".join([
 '<header><p class="eyebrow">完成イメージ ── 段1</p>'
 '<h1>宣言1本が、型1本になるまで</h1>'
 '<p class="lede">段1 の仕様で、<b>承認済みの決定から出ていないのはここだけ</b>である。'
 '9段を実際に通して、<b>各段で何が足されるか</b>を見る。</p></header>',

 sec("01", "使う宣言",
   "<b>部品を一通り使う、小さな型ひとつ。</b>値・まとまり・並び・入れ子・図を含む。",
   code(DECL, "宣言（人が書く）")),

 sec("02", "1 ── 表紙を置く",
   "<b>どの型でも同じ。</b>中身より先に器が要る。",
   code(STEP1)),

 sec("03", "2 ── 種別の枝を作る",
   "<b>content の形が枝ごとに変わる</b>ので、content を組む前に枝が決まっている必要がある。",
   code(STEP2, "1 の kind を置き換える")),

 sec("04", "3 ── 共有する組み立てを置く",
   "<b>指す先が無いと <code>$ref</code> が書けない。</b>だから参照より先に置く。",
   code(STEP3)),

 sec("05", "4 ── ブロックの器を並べる",
   "<b>宣言の順が、そのまま読む順になる。</b>並べ替える根拠が無い。",
   code(STEP4)),

 sec("06", "5 ── 中身を、文法に従って組む",
   "<b>文法ひとつに、行き先がひとつ対応する。</b>ここに型ごとの分岐は現れない。",
   code(STEP5, "content の中") + code(STEP5B, "入れ子は、上限のぶんだけ展開する"),
   fold("なぜ自分自身への参照にしないのか",
     '<p class="blob">自分自身を <code>$ref</code> で指すと、'
     '<b>深さの上限を守る仕掛けが別に要る</b>。'
     '上限のぶんだけ展開すれば、<b>守るまでもなく成り立つ</b>。</p>'
     '<p class="foldnote">代償は型が大きくなること。'
     '上限3なら3つ、10なら10になる ── <b>上限を型ごとに宣言する理由でもある</b>。</p>')),

 sec("07", "6 ── 修飾を当てる",
   "<b>修飾は形に付く</b>ので、形が決まってからしか当たらない。",
   code(STEP6)),

 sec("08", "7 ── 説明を、鍵の隣に置く",
   "<b>鍵が全部出そろってからでないと、置き漏らしが分からない。</b>",
   code(STEP7),
   fold("2つの指針を、どこへ置くか",
     '<p class="blob"><b>読み方</b>は <code>description</code> へ置く ── '
     'JSON Schema の標準の欄なので、<b>Waffle の外の道具も読める</b>。</p>'
     '<p class="blob"><b>記入の指針</b>は対応する標準の欄が無いので '
     '<code>x-write</code> にする。<b>読むための言葉と書くための言葉は、宛先が違う</b> ── '
     '前者は文書を引く人へ、後者は文書を書く人へ向く。</p>'
     '<p class="foldnote">索引の2段目は <code>description</code> から組み立てる。</p>')),

 sec("09", "8 ── 枝ごとの必須ブロックを当てる",
   "<b>ブロックが全部在ってからでないと、一覧が指す先を確かめられない。</b>",
   code(STEP8)),

 sec("10", "9 ── 描き方と宛先を置く",
   "<b>型が組み上がってからでないと、どこへ置くかが決まらない。</b>実体へは写さない。",
   code(STEP9)),

 sec("11", "この手順が本物かを、どう確かめるか",
   "<b>4つ。うち2つは機械で確かめられる。</b>",
   check),

 sec("12", "ここで決めたこと",
   "<b>4つ。いずれも通してみて初めて決める必要が出た。</b>",
   decided),

 sec("13", "まだ決めていないこと",
   "<b>3つ。行き先はすべて決まっている</b> ── ただし図の仕様だけ、いつ書くかが空いている。",
   open_q),

 sec("14", "承認", None,
   '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-17 承認。段1 の仕様 節06 の中身にあたる</span></div>'),
])

extra2 = extra + """
pre.ex{margin:0;padding:.9rem 1rem;font-family:var(--mono);font-size:.78rem;line-height:1.7;
       white-space:pre;color:var(--ink-soft);background:var(--surface)}
.exlbl{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;color:var(--ink-faint);
       padding:.5rem 1rem .1rem;background:var(--surface-2);border-bottom:1px solid var(--rule-soft)}
"""
out = ("<title>宣言1本が、型1本になるまで</title>"
       f'<style>{CSS}\n{extra2}</style><div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/raise-walkthrough.html").write_text(out, encoding="utf-8")
print("書いた", len(out))
