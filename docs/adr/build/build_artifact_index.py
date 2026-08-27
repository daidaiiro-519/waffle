"""索引 ── いま生きているものだけを、Schema と Document の構造で並べる。

各頁の h1 と決定の本文は、docs/adr/*.html から読む。手で写さない。
"""
import re, sys, pathlib
S = "/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0, S)
from _common import CSS, sec, fold, tbl, extra

ADR = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr")
A = "https://claude.ai/code/artifact/"

# 群 → [(ファイル名 または None, 成果物ID, 手で書く題（ファイルが無いとき）, 種別)]
GROUPS = [
 ("01", "型 ── Schema",
  "<b>型が何から作られ、何を持ち、何を宣言するか。</b>この作業の中心である。",
  [("adr-schema-from-spec.html",   "84fffac7-cf0a-42bc-8c3b-c0f0002b6f68", None, "決定"),
   ("adr-tier1-tier2.html",        "849ba715-aa46-46b7-b639-815651367236", None, "決定"),
   ("adr-schema-operations.html",  "995af0c1-5501-4330-87ea-f456f2684da5", None, "決定"),
   ("adr-parts-key-and-gloss.html","25de7e5a-52b3-498e-9865-def7dfc5837f", None, "決定"),
   ("adr-vocabulary-by-meaning.html","a733ef9b-6ae7-4b7a-bff7-937b7a1c3727", None, "決定"),
   (None, "b0ce79f9-bea8-4487-adbb-d02b8ba7c4fe", "種別の鍵を、1つにするか群ごとに分けるか", "比較"),
   (None, "adea2af3-1d5f-48de-b061-f481ddedea6f", "索引を2段にすると、どう引けるか", "完成イメージ")]),

 ("02", "文書 ── Document",
  "<b>文書が何を持ち、どう呼ばれるか。</b>型に照らして判定される側である。",
  [("adr-document-holds.html",        "2362b93b-a1a8-4111-8b58-eff36eb61594", None, "決定"),
   ("adr-value-object-as-a-unit.html","1a0663a7-5c19-433f-a623-899e83d23643", None, "決定"),
   ("adr-aggregate-holds-its-inside.html","2e293712-115f-48f0-8a3d-b54858e8b1c8", None, "決定"),
   ("adr-render-and-deploy-split.html","dffe15cf-d4f7-4907-85e8-749bd7df8c85", None, "決定"),
   (None, "df54f985-bf86-4931-b0be-de128ee32978", "Document は何を持ち、どう呼ばれるか", "完成イメージ"),
   (None, "93fd3da5-b0ce-4bc2-8b0d-e569383ad12a", "値オブジェクトとエンティティの完成イメージ", "完成イメージ")]),

 ("03", "図",
  "<b>図を何で表し、どこに置くか。</b>文字と図をひとつの語彙として扱う。",
  [("adr-figure-vocabulary.html","a5b142e3-da78-4de3-87a9-540b3d91c389", None, "決定"),
   ("adr-figure-schema.html",    "383983ee-1c48-4a6b-b18c-fa73c1fc12cb", None, "決定"),
   ("adr-figure-placement.html", "f2522925-e9e6-47d7-8894-cd2f493fdd64", None, "決定"),
   (None, "3bd1bca9-2441-4452-84fc-1b4376b379be", "語彙ごとの描画イメージ", "材料"),
   (None, "ce284003-5396-43dd-9ea2-4b6f441a067e", "部品ごとの描画結果", "材料")]),

 ("04", "仕様と実装の境界",
  "<b>仕様がどこまでを言い、規約がどこからを担うか。</b>型と文書の外側にある線である。",
  [("adr-convention-is-not-a-layer.html",   "e788d4ac-12e7-48d7-a12c-001ba5d944af", None, "決定"),
   ("adr-no-spelling-in-spec.html",         "b730c638-0e75-4bdb-9790-29f20f408d50", None, "決定"),
   ("adr-split-rule.html",                  "e8397ab8-292a-4b7a-89f8-0ff1d1dee18e", None, "決定"),
   ("adr-knowledge-reference-direction.html","55e89066-bf5e-4fb2-a7d6-ff94f3df798c", None, "決定")]),

 ("05", "決定の記録そのものの形",
  "<b>ADR をどう書き、どう配るか。</b>次に型として起こす対象でもある。",
  [("adr-reason-as-a-chain.html",  "e278fb60-1faf-4406-83f1-1c8670b59be3", None, "決定"),
   ("adr-self-contained-html.html", "022f8ace-ae02-4015-adb7-c24d35572829", None, "決定"),
   ("adr-vessel-mock.html",         "fa0808db-9a86-4e2a-ad20-99fd48c3dbe2", None, "決定"),
   (None, "2fccd226-16c1-41e7-a12c-2b87319472c8", "判断を分けた軸の見せ方", "材料")]),

 ("06", "段1 ── 仕様と、その通し",
  "<b>部品と、それを組み立てる手順。</b>ここまでが承認済みで、次は段2 の仕様。",
  [(None, "e4dff1ad-6fe2-404d-aa19-2c59c3208efa", "段1 ── すべての型に共通する契約", "仕様"),
   (None, "ff27b786-35ac-46e2-9011-77a9cebd04b6", "宣言1本が、型1本になるまで", "完成イメージ"),
   (None, "2adde2ae-48a0-40a9-829c-443df674bbc8", "図解の記法", "一次資料")]),

 ("07", "移す",
  "<b>決定と仕様を、実物へ行き渡らせる。</b>",
  [(None, "c3155dc8-b7b7-4a7f-90d0-08887eff4c3b", "8つの型を段2 として立て、179本を移す", "計画")]),
 ("08", "段2 ── Domain の型",
  "<b>8つの型のうち、最初の1本。</b>種別8つと、それぞれの完成イメージ。<b>まだ承認されていない。</b>",
  [(None, "e0e51605-4fd9-4212-ace1-28fa5bf1075d", "Domain の型", "仕様", "未承認"),
   (None, "d0f94d9d-9ba8-4c0b-aab7-fd93afab866d", "事業領域が持つ欄", "決定", "未承認"),
   (None, "03177d1b-e558-4bdd-9619-df96e9d4e906", "Domain の8種別", "索引", "—"),
   (None, "0471e3e5-f19e-4507-9385-b6fb862e9525", "事業領域 ── 完成イメージ", "完成イメージ", "—"),
   (None, "bbff2e22-40f6-4d2e-9b04-1377360775e1", "業務領域 ── 完成イメージ", "完成イメージ", "—"),
   (None, "719c98c5-b1f5-4f4c-94ee-ab9245d82cc2", "区切られた文脈 ── 完成イメージ", "完成イメージ", "—"),
   (None, "7754906c-ab81-4c29-8c55-78f1841438da", "集約 ── 完成イメージ", "完成イメージ", "—"),
   (None, "a01cd642-9885-4dfa-926b-aeb35a2c6c10", "エンティティ ── 完成イメージ", "完成イメージ", "—"),
   (None, "de9fa721-f9d6-4a08-96dc-6e6e33529745", "値オブジェクト ── 完成イメージ", "完成イメージ", "—"),
   (None, "16369065-66b1-496a-a1d0-aaa0c1093c23", "業務ユースケース ── 完成イメージ", "完成イメージ", "—"),
   (None, "db0885b5-af9d-42f1-8a6f-09a39b4d2812", "業務サービス ── 完成イメージ", "完成イメージ", "—"),
   (None, "1ebe3dff-e9dd-4967-b736-ca725fd59f59", "仕様と実装を、どこで結ぶか", "設計", "—"),
   (None, "fc3626b7-6755-4848-810a-a2c7799dd3bf", "ずれたとき、何が赤くなるか", "完成イメージ", "—")]),
]

DESC = {'b0ce79f9': '軸を1つにする案と群ごとに分ける案を、4つの条件で当てた', 'adea2af3': '1段目は全文の4%、当たりを付けて1ブロック取っても7%', 'df54f985': '持ち物・操作7つの入出力・型の解決のされ方・併用の要否', '93fd3da5': '独立して書ける単位にしたとき、実物がどう見えるか', '2adde2ae': '欄は3つ、書ける名前は16、主張は16。どの欄が必須・禁止かは主張が決める', '3bd1bca9': '語彙ごとに、どう描かれるかを並べたもの', 'ce284003': '描画部品ごとに、実際の出力を並べたもの', '2fccd226': '同じ判断を6通りの表で組み比べ、いまの形に落ち着いた', 'c3155dc8': '8つの型を段2 として立て、179本を移す順序と、その間の互換', 'e4dff1ad': '表紙・文法6・修飾6・標準の組み立て・鍵と説明・型を起こす9段の手順', 'ff27b786': '9段を小さな型1本で実際に通し、各段で JSON がどう育つかを見る', 'e0e51605': '種別8つ・宛先・指針。DomainSpecSchema/v11 から DomainSchema/v1 へ改名する案を含む', 'd0f94d9d': '4欄（なぜ／届けている価値／競っている相手／やらないこと）と、その出どころ', '03177d1b': '8種別の索引。ここから各完成イメージへ辿る', '0471e3e5': '事業領域。札は増え、欄は増えない', 'bbff2e22': '業務領域。中核・一般・補完の判定を3問のフローで示す', '719c98c5': '区切られた文脈', '7754906c': '集約。境界の内側・外・不変条件・公開する操作・出す出来事', 'a01cd642': 'エンティティ', 'de9fa721': '値オブジェクト', '16369065': '業務ユースケース', 'db0885b5': '業務サービス。8種別で唯一、欄が変わらない', '1ebe3dff': '宣言→シナリオ／実装→名乗り／シナリオ→テストの3辺', 'fc3626b7': 'ずれたときに、どこがどう赤くなるか'}

def read(name):
    """頁から、題と決定の一文と承認の状態を取る。"""
    s = (ADR / name).read_text(encoding="utf-8")
    h1 = re.search(r"<h1>(.*?)</h1>", s, re.S)
    main = re.search(r'<p class="main">(.*?)</p>', s, re.S)
    if main is None:
        main = re.search(r'<p class="lede">(.*?)</p>', s, re.S)
    st = re.search(r'<span class="k">状態</span><span class="v">([^<]*)</span>', s)
    strip = lambda m: re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    return strip(h1), strip(main), (st.group(1) if st else "状態の節が無い")

def cut(t, n=110):
    return t if len(t) <= n else t[: n - 1] + "…"

rows_by_group, counts = [], {}
for num, title, lead, items in GROUPS:
    rows = []
    for item in items:
        name, aid, manual, kind = item[:4]
        override = item[4] if len(item) > 4 else None
        if name:
            h1, main, state = read(name)
        else:
            h1, main, state = manual, DESC.get(aid[:8], ""), "—"
        if override:
            state = override
        link = f'<a href="{A}{aid}">{h1}</a>' if aid else h1
        badge = f'<span class="kindtag {"unv" if state=="承認済み" else "lim"}">{state}</span>'
        rows.append(("keyrow" if kind == "決定" else "",
                     [f"<b>{link}</b>" if kind == "決定" else link,
                      kind, badge, cut(main) if main else ""]))
        counts[kind] = counts.get(kind, 0) + 1
    rows_by_group.append((num, title, lead, rows))

body = ["".join([
 '<header><p class="eyebrow">索引</p>'
 '<h1>いま生きている決定と成果物</h1>'
 '<p class="lede">Schema と Document の構造で並べる。'
 '<b>取り下げた決定と、置き換えられた決定は載せない。</b>'
 '別の作業の記録も載せない ── それぞれ独立した索引を持つ。</p></header>'
])]

for num, title, lead, rows in rows_by_group:
    body.append(sec(num, title, lead,
        tbl(["成果物", "種別", "状態", "何を決めたか"], rows)))

body.append(sec("09", "載せていないもの",
  "<b>数だけ残す。</b>中身を辿る必要が出たら、そのとき戻す。",
  tbl(["区分", "件数", "なぜ載せないか"], [
    ("", ["取り下げた決定", "2", "<b>誤っていた</b>ので、読むと迷う"]),
    ("", ["置き換えられた決定", "1", "<b>正しかったが範囲が足りなくなった。</b>判断は置き換え先へ引き継がれている"]),
    ("", ["廃止した記録", "1", "決まっていないことを前提に立てた計画"]),
    ("", ["別の作業の記録", "6", "<b>独立した索引を持つ</b>"]),
    ("", ["途中の実験・測定", "多数", "決定へ畳まれ、決定の側から辿れる"]),
  ]),
  fold("この索引の作り方",
    '<p class="blob">題と決定の一文は、<b>各頁から読んでいる</b>。手で写していないので、'
    '頁を直せばここも変わる。</p>'
    '<p class="foldnote">組み立ては <code>docs/adr/build/build_artifact_index.py</code>。'
    '<b>この頁を直接編集しない</b> ── 次に生成したときに消える。</p>')))

extra2 = extra + """
a{color:var(--fact)}
a:hover{text-decoration:none}
"""
out = ("<title>いま生きている決定と成果物</title>"
       f'<style>{CSS}\n{extra2}</style><div class="wrap">{"".join(body)}</div>')
(ADR / "artifact-index.html").write_text(out, encoding="utf-8")
print("書いた", len(out), "／", counts)
