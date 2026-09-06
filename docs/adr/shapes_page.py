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
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)


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
    c = fields(r["src"], ["種類", "原典", "版・取得日", "照合する文字列"])
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
                  + [f"出典・{k}" for k in ("種類", "原典", "版・取得日", "照合する文字列")])
    empty = [k for k in ("水準", "根拠", "例外", "失敗したときの現れ方", "前提条件")
             if not merged.get(k)]
    note = (f'<b class="miss">空で並ぶ欄</b>：{"・".join(empty)}' if empty else "")
    return block(f"### {r['rid']}", rows, note, "one") + code(r["ex"])


def c_view(r, kinds):
    core = {"印": r["rid"],
            "言明": r["row"].get("規則") or r["row"].get("振る舞い", ""),
            "出どころ": f'{r["src"].get("種類","")}　{re.sub(r"<br>.*", "", r["src"].get("原典",""))}'
                        f'　{r["src"].get("照合する文字列","")}',
            "検め方": r["detail"].get("検証方法") or r["detail"].get("実行コマンド")
                      or r["row"].get("検証方法", "")}
    extra = {k: v for k, v in r["detail"].items()
             if k not in ("検証方法", "実行コマンド") and v}
    for k in kinds["list"][1:]:
        if r["row"].get(k) and k not in extra and k not in ("検証方法",):
            extra.setdefault(k, r["row"][k])
    return (block("芯　── 全種類で同じ", fields(core, list(core)), "", "core")
            + block(f"＋ {kinds['name']} の欄　── 雛形が定める",
                    fields(extra, list(extra)), "", "plus")
            + code(r["ex"]))


RULE = dict(name="規則型", list=["ID", "規則", "水準", "検証方法", "適用範囲"],
            detail=["水準", "根拠", "検証方法", "例外", "既存コードへの適用"],
            dup=["水準", "検証方法"])
GUARD = dict(name="保証型", list=["ID", "振る舞い", "検証の単位", "前提条件", "失敗したときの現れ方"],
             detail=["前提", "入力", "期待する結果", "検証の単位", "実行コマンド", "失敗の切り分け"],
             dup=["検証の単位"])
