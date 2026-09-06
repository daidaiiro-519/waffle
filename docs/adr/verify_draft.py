"""検証方法を持たない30件へ、案を1件ずつ並べる。

  python3 docs/adr/verify_draft.py

**言明と、いまの欄は実物から取る。**案だけが人の手による。
案が使う道具は、toolchain の規約に宣言されているかを機械で当てる。
"""
import html as H
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SK = HERE.parents[1] / ".waffle/skills/coding-skills"
sys.path.insert(0, str(SK / "scripts"))
from _common import load_all, sections, tables  # noqa: E402

# (走らせる命令, その命令で落ちない部分, 根拠, 根拠の出どころ)
#   命令が在るなら書く。命令で落ちない部分が残るなら、見る箇所を続けて書く。
#   どちらか片方だけになる規則もある。
SRC = ".waffle/skills/coding-skills/sources/"
SC = SRC + "staticcheck.dev_docs_checks"
VET = SRC + "pkg.go.dev_cmd_vet"
CL = SRC + "rust-lang.github.io_rust-clippy_master_index.html"
SIB = "規約 purpose.hook/acceptance.md の HK-AC-01"
TEST = "テストが言明どおりの条件を確かめているかは、命令では落ちない"

DRAFT = {
    # ── 言語層 ──────────────────────────────────────────────────
    "GO-ERR-05": ("`staticcheck -checks ST1005 ./...`", None,
                  "ST1005 - Incorrectly formatted error string ── "
                  "言明が形式だけを定めているので、命令で閉じる", SC),
    "GO-STY-04": ("`staticcheck -checks ST1020,ST1021,ST1022 ./...`",
                  "公開する識別子に doc コメントが付いているか",
                  "ST1020：The documentation of an exported function should start "
                  "with the function's name（型は ST1021・変数と定数は ST1022）。"
                  "始まり方は落ちるが、doc が無いことは落ちない", SC),
    "RS-CON-02": ("`cargo build` と `cargo clippy --all-targets -- -D warnings`",
                  "`unsafe` や生ポインタで、コンパイラの検査を迂回していないか",
                  "素の可変参照を跨がせないことはコンパイラの Send / Sync が決める。"
                  "包み方の側は clippy の arc_with_non_send_sync が見る", CL),
    "GO-CON-02": (None,
                  "外部を呼ぶ公開関数の第1引数が `ctx context.Context` か "
                  "── `go doc <パッケージ>` の出力で見る",
                  "`go vet` の35検査に第1引数を見るものは無い。"
                  "lostcancel は「cancel 関数が呼ばれるか」を見る別の検査", VET),
    "GO-CON-04": (None, "構造体の欄に `context.Context` が無いか",
                  "`go vet` の35検査に、構造体の欄を見るものは無い", VET),
    "GO-ERR-04": (None, "失敗を捨てている箇所が `_ =` で受けられ、"
                        "理由のコメントが在るか",
                  "staticcheck の一覧に、捨てた失敗そのものを見る検査は無い。"
                  "SA4006：A value assigned to a variable is never read before being "
                  "overwritten ── これは別の検査である", SC),
    "GO-STY-02": (None, "`go doc <パッケージ>` に出る識別子が、"
                        "公開したいものと一致するか",
                  "ST1003 が見るのは package 名と mixedCaps であって、"
                  "公開の意図と大文字始まりの一致ではない", SC),
    # ── 構成層 ──────────────────────────────────────────────────
    "GH-TP-03": (None, "`adapter` の中に、出力ポートを満たす型の定義が無いか",
                 "置き場所を見る命令が無い", None),
    "RD-TP-03": (None, "`bundle/tests/` の各ファイルが `use bundle::` だけを使い、"
                       "他の crate を直接呼んでいないか",
                 "置き場所を見る命令が無い", None),
    "DP-TB-01": (None, "`cargo tree -p <写し手>` に `core` が現れないか",
                 "`cargo tree` は依存を出すだけで、合否を決めない", None),
    "DP-TB-02": (None, "`cargo tree -p core` に `contract` 以外の自作 crate が"
                       "現れないか",
                 "`cargo tree` は依存を出すだけで、合否を決めない", None),
    "HX-TB-01": (None, "`cargo tree -p model` に `adapter` と外部 crate が"
                       "現れないか",
                 "`cargo test -p model` が通っても、依存の向きは示さない", None),
    "HX-TB-02": (None, "`cargo tree -p application` に `adapter` が現れないか",
                 "`cargo test -p application` が通っても、依存の向きは示さない", None),
    "HX-TB-03": (None, "出力アダプタのテストと、偽物のテストが"
                       "同じ試験の集合を通っているか",
                 "同じ集合を通っているかを決める命令が無い", None),
    "HX-TB-04": (None, "入力アダプタのテストが、外部の形式から業務操作の入力までを"
                       "通しで確かめているか",
                 "通しかどうかを決める命令が無い", None),
    "DP-TB-03": ("`cargo test -p contract`",
                 "そのテストが、schema の必須・型・列挙のすべてを当てているか",
                 TEST, None),
    "DP-TB-04": ("`cargo test -p bundle`",
                 "そのテストが、すべての写し手を同じ形で呼んでいるか", TEST, None),
    "DP-TB-05": ("`cargo test --workspace`",
                 "共通の試験の集合が、どの写し手からも同じ形で引かれているか",
                 TEST, None),
    # ── 用途層 ──────────────────────────────────────────────────
    "HK-AC-02": ("`cargo test --test hook_stdio broken_request`",
                 "そのテストが、終了コードと診断の両方を確かめているか",
                 "兄弟の規則が既に同じ形の命令を指している。" + TEST, SIB),
    "HK-AC-03": ("`cargo test --test hook_stdio stdout_only`",
                 "そのテストが、応答以外の出力を実際に作り出しているか",
                 "兄弟の規則が既に同じ形の命令を指している。" + TEST, SIB),
    "HK-AC-04": ("`cargo test --test hook_stdio oversized`",
                 "そのテストが、1 MiB の境界の両側を当てているか",
                 "兄弟の規則が既に同じ形の命令を指している。" + TEST, SIB),
    "MC-AC-01": ("`cargo test --test mcp_stdio initialize`",
                 "そのテストが、仕様の初期化のやり取りをそのまま流しているか",
                 "兄弟の規則が既に同じ形の命令を指している。" + TEST, SIB),
    "MC-AC-03": ("`cargo test --test mcp_stdio stdout_only`",
                 "そのテストが、メッセージ以外の出力を実際に作り出しているか",
                 "兄弟の規則が既に同じ形の命令を指している。" + TEST, SIB),
    "MC-AC-04": ("`cargo test --test mcp_stdio tool_error`",
                 "そのテストが、失敗のあとも接続が続くことまで見ているか",
                 "兄弟の規則が既に同じ形の命令を指している。" + TEST, SIB),
    "MC-AC-05": ("`cargo test --test mcp_stdio shutdown`",
                 "そのテストが、標準入力を実際に閉じているか",
                 "兄弟の規則が既に同じ形の命令を指している。" + TEST, SIB),
    "BA-AC-01": ("`go test -race -run TestAcceptance_Contract ./...`",
                 "そのテストが、契約の状態コードと応答の両方を当てているか",
                 TEST, None),
    "BA-AC-02": ("`go test -race -run TestAcceptance_BadRequest ./...`",
                 "そのテストが、どの欄が問題かまで当てているか", TEST, None),
    "BA-AC-04": ("`go test -race -run TestAcceptance_DependencyFailure ./...`",
                 "そのテストが、応答に内部の詳細が出ないことを当てているか",
                 TEST, None),
    "HK-TS-01": (None, "単位ごとのテスト件数を数え、重心の高い単位が最も多いか",
                 "重心の配分どおりかを決める命令が無い", None),
    "HK-TS-02": (None, "変更を取り込む設定に、すべてのテストを走らせる段が在るか",
                 "設定の中身を見る命令が無い", None),
}

def declared_tools():
    """toolchain の規約が宣言している道具と命令を集める。"""
    tools, cmds = set(), set()
    for s in load_all():
        if s.kind != "toolchain":
            continue
        for name, body in sections(s.body).items():
            for tb in tables(body):
                for r in tb.rows:
                    for c in ("ツール", "コマンド"):
                        v = r.get(c, "")
                        for m in re.findall(r"`([^`]+)`", v):
                            (cmds if " " in m else tools).add(m)
    return tools, cmds


def targets():
    """規約が既に指している実行コマンド（兄弟の規則が持つもの）。"""
    out = set()
    for s in load_all():
        for m in re.finditer(r"\|\s*実行コマンド\s*\|\s*`([^`]+)`", s.body):
            out.add(m.group(1))
    return out


ROOT = HERE.parents[1]


def norm(s):
    return H.unescape(s).replace("\u2019", "'").replace("\u2018", "'")


def quoted_in_source(why, src):
    """根拠の中の英文が、落とした原文にそのまま在るかを当てる。

    返り値: None＝当てる相手が無い ／ [] ＝全部在った ／ [外れた文字列]
    """
    if not src or not src.startswith(".waffle/"):
        return None
    f = ROOT / src
    if not f.exists():
        return ["原文が無い: " + src]
    body = norm(f.read_text(encoding="utf-8", errors="replace"))
    spans = [x.strip() for x in re.findall(r"[A-Za-z][A-Za-z0-9 ,.'\-]{11,}", norm(why))]
    return [x for x in spans if x not in body]


def rows():
    tools, cmds = declared_tools()
    known = targets()
    out = []
    for s in load_all():
        lst = {}
        for name, body in sections(s.body).items():
            if name == "出典":
                continue
            for tb in tables(body):
                if tb.has("ID") and (tb.has("規則") or tb.has("振る舞い")):
                    for r in tb.rows:
                        lst[r["ID"]] = r
        det = set(re.findall(r"^### ([A-Z][A-Z0-9-]+)　", s.body, re.M))
        for rid, r in lst.items():
            if rid in det or rid not in DRAFT:
                continue
            cmd, eye, why, src = DRAFT[rid]
            used = re.findall(r"`([^`]+)`", cmd or "")
            head = [u.split()[0] for u in used if " " in u or u in tools]
            ok = [u for u in head if u in tools or u in {c.split()[0] for c in cmds}]
            new_test = any((" --test " in u or " -run " in u) and u not in known
                           for u in used)
            out.append(dict(where=s.where.replace("constraints/", ""), rid=rid,
                            stmt=r.get("規則") or r.get("振る舞い", ""),
                            old=r.get("検証方法") or r.get("検証の単位", "─"),
                            cmd=cmd, eye=eye, why=why, src=src,
                            tools=sorted(set(ok)), new=new_test,
                            hit=quoted_in_source(why, src)))
    return sorted(out, key=lambda x: (x["where"], x["rid"]))


CSS = """
:root{ --paper:#FBFAF7; --ink:#1C1A17; --muted:#6B665D; --card:#FFF; --panel:#F2EFE8;
  --line:#D8D3C7; --key:#2F6F5E; --add:#9A5B2C; --code:#EFEBE2; }
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#16150F; --ink:#ECE7DC; --muted:#98918A; --card:#1D1B14; --panel:#211F18;
  --line:#38342A; --key:#6FBFA4; --add:#D99B62; --code:#2B281F; } }
:root[data-theme="dark"]{ --paper:#16150F; --ink:#ECE7DC; --muted:#98918A; --card:#1D1B14;
  --panel:#211F18; --line:#38342A; --key:#6FBFA4; --add:#D99B62; --code:#2B281F; }
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.75;font-size:15px;
  font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",system-ui,sans-serif}
main{max-width:62rem;margin:0 auto;padding:2rem 1.2rem 5rem;display:flex;
  flex-direction:column;gap:2rem}
h1{font-size:1.4rem;margin:0;line-height:1.4}
h2{font-size:1.02rem;margin:0 0 .6rem;font-family:ui-monospace,monospace;color:var(--muted)}
p{margin:0 0 .8rem}
.eyebrow{font-size:11px;letter-spacing:.16em;color:var(--muted);margin:0 0 .4rem}
.lede{color:var(--muted);margin:.6rem 0 0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:.7rem}
.tile{background:var(--card);border:1px solid var(--line);border-radius:.4rem;padding:.7rem .9rem}
.tile .k{font-size:.74rem;color:var(--muted);display:block}
.tile .v{font-size:1.7rem;font-weight:700;line-height:1.2;font-variant-numeric:tabular-nums}
.tile.m .v{color:var(--key)} .tile.h .v{color:var(--add)}
.r{background:var(--card);border:1px solid var(--line);border-radius:.45rem;
  padding:.8rem 1rem;margin:0 0 .7rem;display:grid;grid-template-columns:7.5rem 1fr;gap:.2rem .9rem}
.r .id{font-family:ui-monospace,monospace;font-size:.82rem;color:var(--key);font-weight:700}
.r .st{font-size:.95rem}
.r .lbl{font-size:.74rem;color:var(--muted);padding-top:.15rem}
.r .old{font-size:.82rem;color:var(--muted)}
.r .how{font-size:.88rem}
.r .why{font-size:.8rem;color:var(--muted)}
.r .eye{color:var(--add)}
.r .src{font-family:ui-monospace,monospace;font-size:.72rem;color:var(--key)}
.who{font-size:.68rem;font-weight:700;letter-spacing:.06em;padding:.1em .5em;
  border-radius:.2rem;white-space:nowrap}
.who.m{background:var(--key);color:var(--paper)}
.who.h{background:var(--panel);color:var(--add);border:1px solid var(--add)}
.meta{grid-column:2;font-size:.74rem;color:var(--muted);margin-top:.25rem}
.meta b{color:var(--key)}
.meta .new{color:var(--add)}
code{background:var(--code);border-radius:.2rem;padding:.06em .35em;font-size:.88em;
  font-family:ui-monospace,SFMono-Regular,monospace}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--add);
  border-radius:.35rem;padding:.8rem 1rem;font-size:.88rem}
.foot{color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:.9rem}
"""


def md(s):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", H.escape(s))


def main():
    rs = rows()
    m = sum(1 for r in rs if r["cmd"])
    both = sum(1 for r in rs if r["cmd"] and r["eye"])
    checked = [r for r in rs if r["hit"] is not None]
    missed = [x for r in checked for x in r["hit"]]
    newt = [r for r in rs if r["new"]]
    by = {}
    for r in rs:
        by.setdefault(r["where"], []).append(r)

    secs = ""
    for w, g in by.items():
        secs += f'<section><h2>{H.escape(w)}</h2>'
        for r in g:
            meta = []
            if r["tools"]:
                meta.append("宣言済みの道具：" + "・".join(f"<b>{H.escape(t)}</b>"
                                                          for t in r["tools"]))
            if r["new"]:
                meta.append('<span class="new">まだ書かれていないテストを指す</span>')
            if r["hit"] == []:
                meta.append("原文で照合済み")
            secs += (f'<div class="r">'
                     + f'<span class="id">{H.escape(r["rid"])}</span>'
                     + f'<span class="st">{md(r["stmt"])}</span>'
                     + f'<span class="lbl">いまの欄</span>'
                     + f'<span class="old">{H.escape(r["old"])}　'
                     + f'<span style="color:var(--add)">検証方法は空</span></span>'
                     + (f'<span class="lbl">走らせる命令</span>'
                        f'<span class="how">{md(r["cmd"])}</span>' if r["cmd"] else "")
                     + (f'<span class="lbl">命令で落ちない部分</span>'
                        f'<span class="how eye">{md(r["eye"])}</span>' if r["eye"] else "")
                     + f'<span class="lbl">なぜそう言えるか</span>'
                     + f'<span class="why">{md(r["why"])}'
                     + (f'<br><span class="src">{H.escape(r["src"])}</span>'
                        if r["src"] else "") + '</span>'
                     + (f'<span class="meta">{"　／　".join(meta)}</span>' if meta else "")
                     + '</div>')
        secs += "</section>"

    page = f"""<title>検証方法の案　30件</title><style>{CSS}</style>
<main>
<header>
  <p class="eyebrow">CODING-SKILLS ／ 論点18</p>
  <h1>検証方法を持たない30件に、案を当てる</h1>
  <p class="lede"><b>言明と「いまの欄」は実物から取っている。</b>案だけが人の手による。
  <b>欄は1つである。</b>命令が在るなら書き、その命令で落ちない部分が残るなら、
  見る箇所を続けて書く。<b>機械が落とせるのは形だけで、言明の意味は落ちない。</b></p>
</header>
<section>
  <div class="tiles">
    <div class="tile m"><span class="k">走らせる命令がある</span><span class="v">{m}</span></div>
    <div class="tile h"><span class="k">当たる命令が無い</span><span class="v">{len(rs)-m}</span></div>
    <div class="tile"><span class="k">命令と、見る箇所の両方</span><span class="v">{both}</span></div>
    <div class="tile"><span class="k">原文で照合した根拠</span>
      <span class="v">{len(checked)}</span></div>
    <div class="tile"><span class="k">まだ無いテストを指す</span><span class="v">{len(newt)}</span></div>
  </div>
</section>
<section>
  <div class="note"><b>前の版から2つ変わった。</b>
  <b>1つ目 ── 機械と人の札を外した。</b>札を立てると排他になり、
  命令が在る規則は「もう人が見なくてよい」と読めてしまう。
  実際には <b>{both} 件で、命令と見る箇所の両方が要る。</b>
  <b>2つ目 ── 道具の検査を原文で当て直した。</b>
  <code>go vet</code> に第1引数を見る検査は無く（35検査の一覧で確認）、
  <code>staticcheck</code> に捨てた失敗を見る検査も、公開と大文字始まりの一致を見る
  検査も無かった。命令を持つ規則は 24 件から {m} 件へ減った。
  残した命令には道具の原文の1行を根拠として添え、
  その文字列が落とした原文にそのまま在ることを機械で当てている（{len(checked)}件）。</div>
</section>
<section>
  <div class="note"><b>まだ書かれていないテストを指す {len(newt)} 件について。</b>
  兄弟の <code>HK-AC-01</code> が既に <code>cargo test --test hook_stdio</code> を
  指しているのと同じ形である ── <b>規約が先、実装が後</b>（論点5）。
  規約の側は、指す先の名前を決める。</div>
</section>
{secs}
<p class="foot">この頁は <code>docs/adr/verify_draft.py</code> が、
<code>.waffle/skills/coding-skills/constraints/</code> の実物と、案の表から書き出す。</p>
</main>"""
    out = HERE / "verify-draft.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out} ── {len(rs)} 件"
          f"（命令あり {m} ／ 命令なし {len(rs)-m} ／ 両方 {both}"
          f" ／ まだ無いテスト {len(newt)}）")


if __name__ == "__main__":
    main()
