"""同じ8つの欄で、関門1と関門2のADRを1本ずつ組み立てる。形が同じことを見えるようにする。"""
from __future__ import annotations

import pathlib

S = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
     "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
STYLE = pathlib.Path(f"{S}/adr_style.html").read_text(encoding="utf-8")
EXTRA = """
<style>
  .cap { color: var(--ink-soft); font-size: .93rem; margin: 0; max-width: 42rem; }
  .fig { border: 1px solid var(--rule); border-radius: 2px; background: var(--surface); padding: 1.3rem 1.5rem; }
  .fig .one { font-family: var(--serif); font-size: 1.12rem; font-weight: 600; margin: 0; line-height: 1.6; }
  h2 .blk { margin-left: auto; font-family: var(--mono); font-size: .62rem; letter-spacing: .1em;
            text-transform: uppercase; color: var(--ink-faint); font-weight: 400; }
  .gate { display:inline-block; font-family: var(--mono); font-size: .66rem; letter-spacing:.08em;
          padding:.2em .6em; border-radius:2px; background: var(--flow-bg); color: var(--flow); }
  ol.reasons { margin:0; padding-left:1.3rem; font-size:.95rem; line-height:1.9; }
  ol.reasons li { margin-bottom:.3rem; }
  .tail { display:block; font-size:.78rem; color: var(--ink-faint); line-height:1.6; margin-top:.3rem; }
  table.cmp td.no { color: var(--warn); } table.cmp td.yes { color: var(--solution); }
  table.cmp td.no .tail, table.cmp td.yes .tail { color: var(--ink-faint); }
  td.name { white-space: normal; }
  .approve { border:2px solid var(--flow); border-radius:2px; background:var(--surface);
             padding:1.1rem 1.3rem; display:flex; flex-direction:column; gap:.4rem; }
  .approve .k { font-family:var(--mono); font-size:.66rem; letter-spacing:.12em;
                text-transform:uppercase; color:var(--flow); }
  .approve .v { font-family:var(--serif); font-size:1.06rem; font-weight:600; }
</style>"""

SEC = ['01 決定', '02 理由', '03 変更前と変更後', '04 判断を分けた軸',
       '05 付随して決めたこと', '06 答えないこと', '07 承認', '08 関連']


def doc(title, lede, gate, blocks):
    out = [f'<title>{title}</title>', STYLE, EXTRA, '', '<div class="wrap">', '',
           '  <header>',
           '    <div class="meta"><span>決定の記録</span>'
           '<span class="st">状態：承認待ち</span><span>2026-08-11</span></div>',
           f'    <h1>{title}</h1>',
           f'    <p class="lede">{lede}</p>',
           f'    <p><span class="gate">{gate}</span></p>',
           '  </header>', '']
    for i, (name, body) in enumerate(zip(SEC, blocks)):
        num, label = name.split(" ", 1)
        out += ['  <section>',
                f'    <h2><span class="num">{num}</span>{label}'
                f'<span class="blk">block {num}</span></h2>',
                body, '  </section>', '']
    out += ['</div>']
    return "\n".join(out)


def table(head, rows, cls="cmp"):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = ""
    for r in rows:
        cells = "".join(
            (f'<td class="name">{c[1:]}</td>' if c.startswith("*") else
             f'<td class="no">{c[1:]}</td>' if c.startswith("-") else
             f'<td class="yes">{c[1:]}</td>' if c.startswith("+") else
             f"<td>{c}</td>")
            for c in r)
        b += f"<tr>{cells}</tr>"
    return (f'    <div class="gapwrap"><table class="{cls}"><thead><tr>{h}</tr></thead>'
            f'<tbody>{b}</tbody></table></div>')


# ══════════ 関門1 ══════════
A = doc(
  "業務領域を、区切られた文脈の外へ出す",
  "業務領域の仕様文書の置き場所を決める。仕様を書き換える前の判断。",
  "関門1 ── 仕様へ落とす手前",
  [
    '    <div class="fig"><p class="one">業務領域の仕様文書を、区切られた文脈の配下から出し、'
    '事業領域の配下へ置く。所属はディレクトリの位置ではなく、業務ユースケースが持つ参照が運ぶ。'
    '集約・業務ユースケース・業務サービスは区切られた文脈の配下に残す。</p></div>',

    '    <ol class="reasons">'
    '<li>業務領域と区切られた文脈の関係は、knowledge が<strong>対応</strong>として述べている。包含ではない。</li>'
    '<li>入れ子は業務領域に親を1つしか与えず、knowledge が名指しでアンチパターンとする'
    '「1つの業務領域に1つのモデル」を構造として強制する。</li>'
    '<li>業務領域は事業が決めるもの、区切られた文脈は技術者が動かせるもの。'
    'いまは後者を動かすと前者の文書が動く。</li>'
    '<li>同じ文脈のユースケース28件が7つに分かれており、'
    '「同じデータを操作する集まりを割らない」という制約が文脈の内側で破れている。</li>'
    '</ol>',

    '    <p class="cap">概念の関係がどう変わるか。</p>\n' + table(
      ["", "変更前", "変更後"],
      [["*業務領域の親", "-区切られた文脈（1つだけ）", "+事業領域"],
       ["*所属を運ぶもの", "-ディレクトリの位置", "+宣言（参照）"],
       ["*事業領域という層", "-存在しない", "+立てる"],
       ["*文脈を切り直したとき", "-業務領域の文書が動く", "+動かない"],
       ["*同じ文脈のユースケース", "-7つに分散", "+1箇所に集まる"]]),

    '    <p class="cap">入れ子のまま据え置く案と並べる。</p>\n' + table(
      ["軸", "入れ子のまま", "参照へ移す"],
      [["*業務領域が持てる親の数", "-1つだけ", "+制限なし"],
       ["*所属の宣言が唯一の正になるか", "-ならない", "+なる"],
       ["*文脈の切り直しへの耐性", "-無い", "+ある"],
       ["*ユースケースの集まりが割れないか", "-割れている", "+割れない"],
       ["*移行にかかる手間の少なさ", "+要らない", "-文書70件・テスト62箇所"]]),

    table(["論点", "決定"],
      [["*業務領域の器", "平らにせず、事業領域を2つ立てて配下に置く"],
       ["*参照の必須", "必須にする"],
       ["*多重度", "単一値のまま。制限したことを明記する"],
       ["*逆向きの一覧", "畳む"],
       ["*インフラ仕様", "動かさない"],
       ["*関門の持ち方", "分類のラベルとして持ち、種別で構造を分岐させない"]], cls=""),

    table(["論点", "状態"],
      [["*7分割の是非", "別論点。疑わしいのは3つという裁定は出ている"],
       ["*事業領域の中身", "器は立てる。分類の根拠などは移動後に埋める"],
       ["*原本の確認", "書き起こし版までの確認に留まる。該当ページを画像で見ていない"]], cls=""),

    '    <div class="approve"><span class="k">承認</span>'
    '<span class="v">未承認</span>'
    '<span style="font-size:.9rem;color:var(--ink-soft)">'
    '事業領域という種別を新しく立てるため、承認を待つ。</span></div>',

    table(["種類", "対象"],
      [["*縛る仕様", "DomainSpecSchema（置き場所の宣言）"],
       ["*影響する文書", "specs 配下のドメイン仕様 70件"],
       ["*後続の決定", "置き場所の宣言を、実装が読むようにする（関門2）"]], cls=""),
  ])

# ══════════ 関門2 ══════════
B = doc(
  "置き場所の宣言を、実装が読むようにする",
  "置き場所を決め打ちしている3箇所を直す。ファイルは動かさない。",
  "関門2 ── 実装へ落とす手前",
  [
    '    <div class="fig"><p class="one">置き場所を決め打ちしている3箇所を、'
    'スキーマの宣言から解決する形へ直す。解決はアプリケーション層に1つ置き、'
    'テンプレートの展開はドメイン層の既存の部品へ委ねる。仕様文書は動かさない。</p></div>',

    '    <ol class="reasons">'
    '<li>置き場所はスキーマが宣言しているのに、実装がその写しを持っている。'
    '<strong>宣言を変えても、探索先が変わらない。</strong></li>'
    '<li>3箇所のうち1つは、壊れても鳴らない。'
    '引き継ぎを求めるゲートが、仕様を見つけられないと黙って通す。</li>'
    '<li>同じ解決を行う実装が既に3箇所にあり、4つ目の写しを作ることになる。</li>'
    '<li>この修正は挙動を変えず、取り消せる。'
    '<strong>置き場所を動かす判断を見送っても、残す価値がある。</strong></li>'
    '</ol>',

    '    <p class="cap">何ができるようになるか。</p>\n' + table(
      ["", "変更前", "変更後"],
      [["*置き場所を変えたいとき", "-宣言を書き換えても探索先は変わらない", "+変わる"],
       ["*検査が緑を返したとき", "-「適合している」か「見ていない」か区別できない", "+区別できる"],
       ["*引き継ぎのゲート", "-仕様を見つけられないと黙って通す", "+鳴る"],
       ["*置き場所を知る場所", "-スキーマ＋実装3箇所", "+スキーマだけ"]]),

    '    <p class="cap">置き場所を動かすのと同時に直す案と並べる。</p>\n' + table(
      ["軸", "移動と同時に直す", "先に単独で直す"],
      [["*修正の前後で出力を突き合わせられるか", "-できない<span class=\"tail\">出力が変わった原因を切り分けられない</span>", "+できる"],
       ["*黙る故障が塞がる時点", "-移動のあと", "+移動の前"],
       ["*移動を見送ったときに残るか", "-残らない", "+残る"],
       ["*作業の回数", "+1回", "-2回"]]),

    table(["論点", "決定"],
      [["*解決を置く層", "アプリケーション層。スキーマの取得が口越しの操作であり、その口を持つのはこの層"],
       ["*テンプレートの展開", "ドメイン層の既存の部品へ委ねる。作り直さない"],
       ["*既存3箇所の置き換え", "この決定では行わない。後追いでよい"],
       ["*直す順序", "3箇所を同時に。1つ残すと、黙る故障が黙ったまま残る"]], cls=""),

    table(["論点", "状態"],
      [["*仕様文書の移動", "この決定には含まない。関門1の決定に従って別途行う"],
       ["*既存3箇所の写しの解消", "行える状態にはなるが、着手は別の判断"],
       ["*版の扱い", "この修正は版に触れない"]], cls=""),

    '    <div class="approve"><span class="k">承認</span>'
    '<span class="v">未承認</span>'
    '<span style="font-size:.9rem;color:var(--ink-soft)">'
    '挙動を変えず取り消せるが、実装へ入る手前なので承認を待つ。</span></div>',

    table(["種類", "対象"],
      [["*実装する仕様", "uc-check-spec-integrity ほか、置き場所を解決する経路"],
       ["*先行する決定", "業務領域を、区切られた文脈の外へ出す（関門1）"],
       ["*この決定に依存するもの", "仕様文書70件の移動。この修正が済むまで着手しない"]], cls=""),
  ])

pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/sample-gate1-subdomain.html").write_text(A, encoding="utf-8")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/sample-gate2-declaration.html").write_text(B, encoding="utf-8")
print("関門1:", len(A), "bytes /", A.count("<section>"), "節")
print("関門2:", len(B), "bytes /", B.count("<section>"), "節")