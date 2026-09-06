"""規則1件が、3案それぞれでどう書かれるかを並べる。

  python3 docs/adr/shapes_page.py

**値は実物から取る。**並べ替えだけを見せ、内容は作らない ──
作ると、比べているものが実物でなくなる。
"""
import html as H
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SK = HERE.parents[1] / ".waffle/skills/coding-skills"
sys.path.insert(0, str(SK / "scripts"))
from _common import load_all, sections, tables  # noqa: E402


def pick(kind, layer, rid):
    """実物から、その規則の欄を全部取る。"""
    s = next(x for x in load_all() if x.kind == kind and x.layer == layer)
    row = src = None
    for name, body in sections(s.body).items():
        for tb in tables(body):
            if not tb.has("ID"):
                continue
            for r in tb.rows:
                if r["ID"] != rid:
                    continue
                if name == "出典":
                    src = r
                elif tb.has("規則") or tb.has("振る舞い"):
                    row = r
    m = re.search(rf"^### {rid}　(.*?)$(.*?)(?=^### |^## |\Z)", s.body, re.S | re.M)
    detail = {}
    ex = {}
    if m:
        for t in tables(m.group(2)):
            if t.has("項目", "内容"):
                for r in t.rows:
                    detail[r["項目"]] = r["内容"]
        for tag in ("適合例", "違反例"):
            g = re.search(rf"\*\*{tag}\*\*\n\n```(?:\w+)?\n(.*?)```", m.group(2), re.S)
            if g:
                ex[tag] = g.group(1).rstrip()
    return dict(where=f"{layer}/{kind}.md", rid=rid, row=row or {},
                detail=detail, src=src or {}, ex=ex)


def md(s):
    s = H.escape(s or "")
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s.replace("&lt;br&gt;", "<br>")


def fields(d, keys):
    return "".join(f"<tr><td>{H.escape(k)}</td><td>{md(v)}</td></tr>"
                   for k, v in ((k, d.get(k, "")) for k in keys) if v)


def block(title, rows, note="", cls=""):
    return (f'<div class="blk {cls}"><b class="bt">{title}</b>'
            + (f'<p class="bn">{note}</p>' if note else "")
            + f'<table>{rows}</table></div>')


def code(ex):
    return "".join(f'<div class="ex"><span>{t}</span><pre>{H.escape(c)}</pre></div>'
                   for t, c in ex.items())


def now_view(r, kinds):
    """いまの姿 ── 3か所に散る。"""
    a = fields(r["row"], kinds["list"])
    b = fields(r["detail"], kinds["detail"])
    c = fields(r["src"], ["種類", "原典", "版・取得日", "何を裏づけるか"])
    dup = kinds["dup"]
    warn = (f'<p class="warn">この2つは <b>## 規則一覧</b> にも在る ── '
            f'{"・".join(dup)}</p>' if dup else "")
    return (block("## 規則一覧　の1行", a)
            + block("## 規則の詳細　の節", b, "") + warn + code(r["ex"])
            + block("## 出典　の1行", c))


def a_view(r, kinds):
    all_keys = ["言明"] + kinds["list"][1:] + kinds["detail"] + ["失敗したときの現れ方",
                                                                "前提条件", "水準", "根拠", "例外"]
    seen, keys = set(), []
    for k in all_keys:
        if k not in seen:
            seen.add(k)
            keys.append(k)
    merged = dict(r["detail"])
    merged.update({k: v for k, v in r["row"].items() if v and k != "ID"})
    merged["言明"] = r["row"].get("規則") or r["row"].get("振る舞い", "")
    merged.update({f"出典・{k}": v for k, v in r["src"].items() if k != "ID"})
    rows = fields(merged, ["言明"] + [k for k in keys if k not in ("言明", "規則", "振る舞い")]
                  + [f"出典・{k}" for k in ("種類", "原典", "版・取得日", "何を裏づけるか")])
    empty = [k for k in ("水準", "根拠", "例外", "失敗したときの現れ方", "前提条件")
             if not merged.get(k)]
    note = (f'<b class="miss">空で並ぶ欄</b>：{"・".join(empty)}' if empty else "")
    if merged.get("前提条件") and merged.get("前提"):
        note += ('<br><b class="miss">同じことに2つの名前</b>：'
                 '「前提条件」と「前提」が並ぶ')
    return block(f"### {r['rid']}", rows, note, "one") + code(r["ex"])


def c_view(r, kinds):
    core = {"ID": r["rid"],
            "言明": r["row"].get("規則") or r["row"].get("振る舞い", ""),
            "出典": f'{r["src"].get("種類","")}　'
                    f'{re.sub(r"<br>.*", "", r["src"].get("原典",""))}　'
                    f'（{r["src"].get("何を裏づけるか","")}）',
            "検証方法": " ／ ".join(
                x for x in (r["detail"].get("検証方法")
                            or r["detail"].get("実行コマンド", ""),
                            r["detail"].get("命令で落ちない部分", "")) if x)
                      or r["row"].get("検証方法", "")}
    drop = ("検証方法", "実行コマンド", "命令で落ちない部分", "規則", "振る舞い")
    extra = {k: v for k, v in r["detail"].items() if k not in drop and v}
    for k in kinds["list"][1:]:
        if r["row"].get(k) and k not in extra and k not in drop:
            extra.setdefault(k, r["row"][k])
    return (block("芯　── 全種類で同じ", fields(core, list(core)), "", "core")
            + block(f"＋ {kinds['name']} の欄　── 雛形が定める",
                    fields(extra, list(extra)), "", "plus")
            + code(r["ex"]))


RULE = dict(name="規則型", list=["ID", "規則", "水準", "検証方法", "適用範囲"],
            detail=["水準", "根拠", "検証方法", "例外", "既存コードへの適用"],
            dup=["水準", "検証方法"])
GUARD = dict(name="保証型", list=["ID", "振る舞い", "検証の単位", "前提条件", "失敗したときの現れ方"],
             detail=["前提", "入力", "期待する結果", "検証の単位", "実行コマンド",
                     "命令で落ちない部分", "失敗の切り分け"],
             dup=["検証の単位"])


CSS = """
:root{ --paper:#FBFAF7; --ink:#1C1A17; --muted:#6B665D; --card:#FFF; --panel:#F2EFE8;
  --line:#D8D3C7; --key:#2F6F5E; --add:#9A5B2C; --code:#EFEBE2; }
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#16150F; --ink:#ECE7DC; --muted:#98918A; --card:#1D1B14; --panel:#211F18;
  --line:#38342A; --key:#6FBFA4; --add:#D99B62; --code:#2B281F; } }
:root[data-theme="dark"]{ --paper:#16150F; --ink:#ECE7DC; --muted:#98918A; --card:#1D1B14;
  --panel:#211F18; --line:#38342A; --key:#6FBFA4; --add:#D99B62; --code:#2B281F; }
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.8;font-size:15px;
  font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",system-ui,sans-serif}
main{max-width:74rem;margin:0 auto;padding:2rem 1.2rem 5rem;display:flex;
  flex-direction:column;gap:2.4rem}
h1{font-size:1.45rem;margin:0;line-height:1.4}
h2{font-size:1.12rem;margin:0 0 .9rem;padding-bottom:.35rem;border-bottom:1px solid var(--line)}
p{margin:0 0 .8rem}
.lede{color:var(--muted);margin:.6rem 0 0}
.eyebrow{font-size:11px;letter-spacing:.16em;color:var(--muted);margin:0 0 .4rem}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(19rem,1fr));gap:1rem;
  align-items:start}
.col{background:var(--card);border:1px solid var(--line);border-radius:.45rem;padding:1rem}
.col.now{border-color:var(--muted)}
.col.pick{border-color:var(--key);border-width:2px}
.col>h3{margin:0 0 .2rem;font-size:1rem}
.col>h3 .tag{font-size:.68rem;font-weight:700;letter-spacing:.08em;padding:.1em .45em;
  border-radius:.2rem;margin-left:.4rem;vertical-align:.15em}
.col.now .tag{background:var(--panel);color:var(--muted);border:1px solid var(--line)}
.col.pick .tag{background:var(--key);color:var(--paper)}
.col>p.k{color:var(--muted);font-size:.82rem;margin:0 0 .8rem}
.blk{margin:0 0 .9rem}
.blk .bt{display:block;font-size:.74rem;letter-spacing:.05em;color:var(--muted);
  margin-bottom:.25rem;font-family:ui-monospace,monospace}
.blk.core .bt{color:var(--key)}
.blk.plus .bt{color:var(--add)}
.blk table{border-collapse:collapse;width:100%;font-size:.82rem}
.blk td{border:1px solid var(--line);padding:.3rem .5rem;vertical-align:top}
.blk td:first-child{width:8.5rem;color:var(--muted);white-space:nowrap;background:var(--panel)}
.blk.core td:first-child{color:var(--key)}
.blk .bn{font-size:.78rem;color:var(--muted);margin:0 0 .4rem}
.miss{color:var(--add)}
.warn{font-size:.78rem;color:var(--add);margin:-.5rem 0 .9rem}
.ex{margin:0 0 .7rem}
.ex span{font-size:.72rem;color:var(--muted);display:block}
pre{background:var(--code);border-radius:.3rem;padding:.5rem .7rem;overflow-x:auto;
  font-size:.76rem;line-height:1.6;margin:.2rem 0 0}
code{background:var(--code);border-radius:.2rem;padding:.05em .3em;font-size:.9em;
  font-family:ui-monospace,SFMono-Regular,monospace}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--add);
  border-radius:.35rem;padding:.8rem 1rem;font-size:.88rem}
.foot{color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:.9rem}
"""


def case(r, kinds):
    stmt = r["row"].get("規則") or r["row"].get("振る舞い", "")
    return (f'<section><h2>{H.escape(r["rid"])}　{md(stmt)}'
            f'<span style="color:var(--muted);font-size:.8rem;font-weight:400">'
            f'　{H.escape(r["where"])}（{kinds["name"]}）</span></h2>'
            f'<div class="cols">'
            f'<div class="col now"><h3>いま<span class="tag">3か所に散る</span></h3>'
            f'<p class="k">同じ欄が2か所にある</p>{now_view(r, kinds)}</div>'
            f'<div class="col"><h3>A　共通1つの形<span class="tag">1つの塊</span></h3>'
            f'<p class="k">全種類で同じ欄を持つ</p>{a_view(r, kinds)}</div>'
            f'<div class="col pick"><h3>C　芯 ＋ 種類ごとの欄<span class="tag">推し</span></h3>'
            f'<p class="k">芯は全種類で同じ。残りは雛形が足す</p>{c_view(r, kinds)}</div>'
            f'</div></section>')


def main():
    go = pick("style", "lang.go", "GO-STY-01")
    hk = pick("acceptance", "purpose.hook", "HK-AC-01")
    page = f"""<title>規則1件は、どう書かれるか</title><style>{CSS}</style>
<main>
<header>
  <p class="eyebrow">CODING-SKILLS ／ 論点18</p>
  <h1>規則1件は、どう書かれるか</h1>
  <p class="lede">実物の規則を2件、いまの姿と2つの案で並べた。
  <b>値はすべて実物から取っている</b> ── 並べ替えだけを見せている。
  B（種類ごとの形）は<b>いまの姿から「散る」をやめただけ</b>なので、
  A と C の違いが見えるように2つを置いた。</p>
</header>
{case(go, RULE)}
{case(hk, GUARD)}
<section>
  <h2>この2件で見えること</h2>
  <div class="note">
  <p><b>A は、規則型と保証型で使わない欄が空で並ぶ。</b>
  <code>GO-STY-01</code> には「失敗したときの現れ方」「前提条件」が無く、
  <code>HK-AC-01</code> には「水準」「根拠」「例外」が無い。
  「埋まらない欄が残るなら、まだ規約になっていない」という定めと衝突する。</p>
  <p style="margin:0"><b>C は、芯の4欄がどちらでも埋まる。</b>
  埋まらないのは種類ごとの欄で、そこは雛形が「その種類に要る欄」として定める ──
  <b>空欄が「まだ書いていない」を意味するようになる。</b></p>
  </div>
</section>
<p class="foot">この頁は <code>docs/adr/shapes_page.py</code> が、
<code>.waffle/skills/coding-skills/constraints/</code> の実物から書き出す。</p>
</main>"""
    out = HERE / "rule-shapes.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out} ── GO-STY-01（規則型）と HK-AC-01（保証型）")


if __name__ == "__main__":
    main()
