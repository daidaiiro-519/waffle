"""CodingSkills の全文を、前の版からの変更つきで1枚にする。

  python3 docs/adr/skill_page.py

**差分は git から取る。**手で書くと、写した側が正になる。
「なぜ変えたか」だけを人が書き、どのファイルがどの変更に当たるかは
パターンで割り当てる ── 61ファイルぶんの理由を1つずつ書くと、必ずずれる。
"""
import html as H
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SK = ROOT / ".waffle/skills/coding-skills"
REL = ".waffle/skills/coding-skills"
BASE = "9d99557"          # 第1版（CodingSkills を Skill として据える）

# ── 変更の束。ファイルの当たり方はパターンで決める ──────────────
GROUPS = [
    ("承認の記録", r"^(constraints|templates)/.*\.md$",
     "前置きに <code>approved_by</code> と <code>approved_at</code> を足した。",
     "承認を定めていたのに、記録する場所がどこにも無かった。"
     "承認済みと未承認を、記録から区別できない状態だった。"),
    ("出典の追加", r"^constraints/(arch\.hexagonal/test-boundaries|lang\.rust/concurrency|"
     r"lang\.go/(failure|style)|lang\.go\+arch\.hexagonal/test-placement|"
     r"purpose\.(hook|mcp-server|backend-api)/acceptance|purpose\.hook/test-strategy|"
     r"arch\.data-port/test-boundaries)\.md$",
     "出典の行を14行足した。",
     "66件の規則のうち23件に出典が無いのに、検査が通っていた。"
     "検査が出典の表を回っていたので、行が1つも無い規則を見逃していた。"),
    ("照合の差し替え", r"^constraints/(purpose\.hook/acceptance|purpose\.mcp-server/acceptance|"
     r"lang\.go\+arch\.hexagonal/test-placement|purpose\.backend-api/acceptance)\.md$",
     "照合する文字列を差し替えた（6件）。",
     "原文に在るだけで、規則を裏づけていなかった ── "
     "<code>Exit code</code> は28か所、<code>stdout</code> は3か所に当たる。"
     "入れ子のバッククォートで検査の解釈が壊れるものもあった。"),
    ("規則の組み替え", r"^constraints/(lang\.rust\+arch\.(data-port|hexagonal)/test-placement|"
     r"arch\.data-port/test-boundaries|purpose\.hook/acceptance|purpose\.mcp-server/acceptance)\.md$",
     "規則を割った・新設した・外した。",
     "1文に2つの命題が入っていたものを割り、外部に原典が無いものを"
     "「委譲する判断」へ移した。出典を持たない言明は規則ではない、という定めをそのまま当てた。"),
    ("テストの置き場所", r"^constraints/(lang\.rust\+arch\.(hexagonal|data-port)/test-placement|"
     r"purpose\.(hook|mcp-server)/acceptance)\.md$",
     "テストの置き場所を組み替えた。",
     "<code>include_str!</code> は「そのマクロを書いたソースファイルからの相対」で解決されるので、"
     "単体テストが <code>src/</code> に在るのに実物入力を <code>tests/</code> へ置くと届かなかった。"
     "あわせて <code>tests/</code> を「公開する境界から叩くもの」だけに絞った。"),
    ("参照文書の定め", r"^references/",
     "定めを足した ── 出典の取り方・承認の記録・規則の印・数の扱い。",
     "検査を足すには、守る宣言が先に要る。"
     "「同じ層で印は一意」は検査だけが先に在り、宣言がどこにも無かった。"),
    ("scripts の作り直し", r"^scripts/",
     "読み取り層を1か所へ畳み、検査に宣言を持たせ、テストを足した。",
     "検査ごとに正規表現を書いていて、3か所が<b>落ちずに</b>壊れていた ── "
     "出典の照合が78行すべて素通り、<code>JSON</code> を規則と誤検出、"
     "照合文字列の入れ子で別の語を拾う。"),
    ("索引の作り直し", r"^constraints/INDEX\.md$",
     "数を書き出すようにした。",
     "参照文書に手で書いた数が腐っていた（落とした原文41本のまま）。"
     "索引と同じく、数も生成物にした。"),
]

SKIP = re.compile(r"^(sources/|__pycache__|scripts/__pycache__)")


def git_show(path):
    r = subprocess.run(["git", "show", f"{BASE}:{REL}/{path}"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def files():
    out = []
    for p in sorted(SK.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(SK))
        if SKIP.match(rel) or rel.endswith((".pyc", ".bak")):
            continue
        out.append(rel)
    order = {"README.md": 0, "SKILL.md": 1}
    return sorted(out, key=lambda r: (order.get(r, 2), not r.startswith("references/"),
                                      not r.startswith("templates/"),
                                      not r.startswith("scripts/"), r))


# ── Markdown を、最小限だけ HTML にする ────────────────────────

def inline(s):
    s = H.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = s.replace("&lt;br&gt;", "<br>").replace("&lt;small&gt;", "<small>") \
         .replace("&lt;/small&gt;", "</small>")
    return s


def md2html(text):
    out, lines, i = [], text.splitlines(), 0
    if lines and lines[0] == "---":
        j = lines.index("---", 1) if "---" in lines[1:] else 0
        if j:
            out.append('<pre class="fm">' + H.escape("\n".join(lines[1:j])) + "</pre>")
            i = j + 1
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre><code>" + H.escape("\n".join(lines[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4}) (.+)$", ln)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n+1}>{inline(m.group(2))}</h{n+1}>")
            i += 1
            continue
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-: |]+\|$", lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                         for r in rows)
            out.append(f'<div class="scroll"><table><tr>{th}</tr>{tb}</table></div>')
            i = j
            continue
        if re.match(r"^[-*] ", ln):
            items, j = [], i
            while j < len(lines) and re.match(r"^[-*] ", lines[j]):
                items.append(f"<li>{inline(lines[j][2:])}</li>")
                j += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            i = j
            continue
        if ln.strip() == "":
            i += 1
            continue
        if ln.strip() == "---":
            out.append("<hr>")
            i += 1
            continue
        para, j = [], i
        while j < len(lines) and lines[j].strip() and not lines[j].startswith(("|", "#", "```", "- ")):
            para.append(inline(lines[j]))
            j += 1
        out.append("<p>" + "<br>".join(para) + "</p>")
        i = j
    return "".join(out)


def code2html(text):
    return "<pre><code>" + H.escape(text) + "</code></pre>"


def diff_html(old, new, path):
    import difflib
    d = list(difflib.unified_diff(old.splitlines(), new.splitlines(),
                                  fromfile=f"第1版/{path}", tofile=f"第2版/{path}",
                                  lineterm="", n=2))
    if not d:
        return ""
    body = []
    for ln in d:
        cls = ("a" if ln.startswith("+") and not ln.startswith("+++") else
               "d" if ln.startswith("-") and not ln.startswith("---") else
               "h" if ln.startswith("@@") else "")
        body.append(f'<span class="{cls}">{H.escape(ln)}</span>')
    add = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
    rm = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
    return (f'<details class="dif"><summary>変更を見る'
            f'<span class="cnt">＋{add} ／ −{rm}</span></summary>'
            f'<pre class="diff">{"".join(body)}</pre></details>')
