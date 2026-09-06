"""CodingSkills のブレストを1枚へ畳む。

  python3 docs/adr/board_merge.py

論点1〜12 は既に組まれた盤面（`brainstorm-coding-skills.html`）に在り、
**その生成元は失われている**。だから節の HTML をそのまま取り出して使う ──
書き写すと、写した側が正になってしまう。

論点13〜17 は `board_contracts.py` が持つ Topic から組む。
"""
import html as _h
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, "/home/daidaiiro/workspace/waffle/.claude/skills/brainstorm/references")
sys.path.insert(0, str(HERE))

from build_board import CSS, HEAD, SCRIPT, _sec, _sections, _table  # noqa: E402
import board_contracts as BC  # noqa: E402

# 基は論点1〜12 の盤面。生成元が失われているので、成果物そのものを入力にする
BASE = HERE / "brainstorm-coding-skills-1-12.html"
OUT = HERE / "brainstorm-coding-skills.html"
THEME = "CodingSkills ── 制約と、その作用域"

NEW = [BC.t13, BC.t14, BC.t15, BC.t16, BC.t17, BC.t18, BC.t19, BC.t20]

NOTE = (
    "<b>これは正本ではない。ブレストの記録である。</b>"
    "論点1〜12 で <b>制約と作用域の枠</b>を決め、その形で Skill を組んだ"
    "（<code>.waffle/skills/coding-skills/</code>）。"
    "論点13 以降は<b>組んだあとに出てきたもの</b>である ── "
    "検査は何を対象にするか、検査が宣言から導かれていることを何が担保するか、"
    "出典の照合をどう選ぶか、規則1件をどんな形で書くか。"
    "<b>既存の実装や既にある規約の形は、ここでの根拠に使っていない</b> ── "
    "あるべき形から導き直した。数えた事実は、問題が実在することの証拠としてだけ引いている。"
)

ARTIFACTS = _table(
    ["成果物", "何が在るか", "この盤面との関係"],
    [["CodingSkills 第1版の全文<br><small>Artifact <code>24732a71</code></small>",
      "SKILL.md ・ 参照文書 ・ 雛形15本 ・ 規約37本のダンプ",
      "<b>決定は載っていない。</b>論点1〜12 を通した<b>結果</b>である"],
     ["出典の点検<br><small><code>docs/adr/needles.html</code></small>",
      "出典100件を「その原文を特定できているか」で測った結果",
      "<b>論点17 の実測</b>"],
     ["出典の書き方<br><small><code>docs/adr/source-rule.html</code></small>",
      "3つの原則と、実データの実例2件",
      "<b>論点17 の決定</b>を、図と実例で示したもの"]])


def base_parts():
    """既に組まれた盤面から、タブと節をそのまま取り出す。"""
    src = BASE.read_text(encoding="utf-8")
    tabs = re.findall(r'(<button role="tab"[^>]*data-t="p\d+"[^>]*>.*?</button>)',
                      src, re.S)
    panels = {}
    for m in re.finditer(r'<section id="(p\d+)" role="tabpanel"[^>]*>(.*?)</section>',
                         src, re.S):
        panels[m.group(1)] = m.group(2)
    rows = re.search(
        r'<h2><span class="sn">1</span>論点の現在地</h2><div class="scroll">'
        r'<table class="">(.*?)</table></div>', panels["p0"], re.S).group(1)
    old_rows = re.findall(r"(<tr><td><span class=\"n\">\d+</span>.*?</tr>)", rows, re.S)
    return tabs, panels, old_rows


def main():
    tabs, panels, old_rows = base_parts()
    assert len(old_rows) == 12, f"論点1〜12 の行が {len(old_rows)} 件しか取れていない"

    new_rows = [
        f'<tr><td><span class="n">{t.no}</span></td>'
        f'<td>{_h.escape(t.question)}</td>'
        f'<td><span class="st {"done" if t.status == "決着" else "open"}">'
        f'{_h.escape(t.status)}</span></td><td>{t.answer}</td></tr>'
        for t in NEW]

    now = (f'<p class="eyebrow">現在地</p><h1>{_h.escape(THEME)}</h1>'
           f'<div class="note">{NOTE}</div>'
           + _sec(1, "論点の現在地",
                  '<div class="scroll"><table class="">'
                  '<tr><th>#</th><th>論点</th><th>状態</th><th>いまの答え</th></tr>'
                  + "".join(old_rows + new_rows) + '</table></div>'))

    # 既にある「この枠で、何が言えているか」「この盤面で使わない根拠」を、番号を振り直して残す
    kept = re.findall(r'<h2><span class="sn">\d+</span>(.*?)</h2>(.*?)(?=<h2>|$)',
                      panels["p0"], re.S)[1:]
    n = 1
    for title, body in kept:
        n += 1
        now += _sec(n, re.sub(r"<[^>]+>", "", title), body)
    now += _sec(n + 1, "散らばっている成果物",
                "<p class='lead'><b>決定の出どころは、この盤面だけに置く。</b>"
                "外に在るのは、ここで決めたことの成果か、実測の記録である。</p>" + ARTIFACTS)

    out_tabs = ['<button role="tab" aria-selected="true" data-t="p0">現在地</button>']
    out_panels = [f'<section id="p0" role="tabpanel">{now}</section>']

    for i, tab in enumerate(tabs[1:], start=1):        # 論点1〜12
        out_tabs.append(re.sub(r'data-t="p\d+"', f'data-t="p{i}"', tab))
        out_panels.append(
            f'<section id="p{i}" role="tabpanel" hidden>{panels[f"p{i}"]}</section>')

    for j, t in enumerate(NEW, start=13):              # 論点13〜17
        cls = "done" if t.status == "決着" else "open"
        out_tabs.append(f'<button role="tab" aria-selected="false" data-t="p{j}">'
                        f'<span class="tn">{t.no}</span>{_h.escape(t.label)}'
                        f'<span class="st {cls}">{_h.escape(t.status)}</span></button>')
        out_panels.append(
            f'<section id="p{j}" role="tabpanel" hidden>{_sections(t)}</section>')

    head = (f'<div class="hd"><div class="t">{_h.escape(THEME)}'
            f'<small>色の付いた箇所を押すと、変更前と理由が開きます'
            f'（<span id="n">0</span>か所）</small></div>'
            f'<button id="all" type="button">すべて開く</button></div>'
            f'<div class="tabs" role="tablist">{"".join(out_tabs)}</div>')
    body = f'{head}<main>{"".join(out_panels)}</main>{SCRIPT}'
    page = f"<title>{_h.escape(THEME)}</title>{HEAD}<style>{CSS}</style>{body}"
    OUT.write_text(page, encoding="utf-8")
    done = sum(1 for t in NEW if t.status == "決着") + 12
    print(f"{OUT} ── 論点 {12 + len(NEW)} 件（決着 {done} ／ 開 {12 + len(NEW) - done}）")


if __name__ == "__main__":
    main()
