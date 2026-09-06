"""規約のファイルを読み、前置き・節・表に分ける。

このファイルは、collect ・ check ・ index が共有する読み取りだけを持つ。
判断はここに置かない ── 何を集め、何を落とすかは、呼ぶ側が決める。

**読み取りは1か所に畳む。**
以前は検査ごとに正規表現を書いていて、静かに壊れた ──
出典の URL を `<small>` で探して1行も拾えず、規則の ID をハイフンの数で
判定して表の1列目の `JSON` を規則と数えていた。どちらも落ちずに通った。
表はヘッダ行で列名を宣言しているので、**位置ではなく列名で読む。**
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONSTRAINTS = ROOT / "constraints"
REFERENCES = ROOT / "references"
TEMPLATES = ROOT / "templates"
SOURCES = ROOT / "sources"


# ── 読み取り層 ────────────────────────────────────────────────

def sections(text: str) -> dict[str, str]:
    """本文を `## 見出し` で切り、見出し → 中身 を返す。"""
    out, name, buf = {}, "", []
    for line in text.splitlines():
        m = re.match(r"^## (.+)$", line)
        if m:
            if name:
                out[name] = "\n".join(buf)
            name, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if name:
        out[name] = "\n".join(buf)
    return out


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


@dataclass
class MdTable:
    """Markdown の表1つ。ヘッダ行が列名を宣言している。"""
    columns: list[str]
    rows: list[dict]

    def has(self, *names: str) -> bool:
        return all(n in self.columns for n in names)

    def col(self, name: str) -> list[str]:
        return [r[name] for r in self.rows if r.get(name)]


def tables(text: str) -> list[MdTable]:
    """本文に在る表を、ヘッダ行から読む。

    区切り行（`|---|`）の直前の行を列名とし、続く行を辞書にする。
    列数がヘッダと合わない行は、表の一部として扱わない。
    """
    out, lines = [], text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|") or "---" not in line or i == 0:
            continue
        if set(line.replace("|", "").replace(" ", "")) - set("-:"):
            continue
        head = lines[i - 1]
        if not head.startswith("|"):
            continue
        cols = _cells(head)
        rows = []
        for row in lines[i + 1:]:
            if not row.startswith("|"):
                break
            cs = _cells(row)
            if len(cs) != len(cols):
                break
            rows.append(dict(zip(cols, cs)))
        out.append(MdTable(cols, rows))
    return out


# ── 軸と前置き ────────────────────────────────────────────────

AXIS_PREFIX = {"lang": "language", "arch": "architecture",
               "purpose": "purpose", "runtime": "runtime"}

SOURCE_SECTION = "出典"
ID_COLUMN = "ID"
ORIGIN_COLUMN = "原典"


def shape_of(layer: str) -> str:
    """層の名前から、その形（言語／アーキテクチャ／…）を返す。"""
    if "+" in layer:
        return "言語 × アーキテクチャ"
    head = layer.split(".", 1)[0]
    return {"lang": "言語", "arch": "アーキテクチャ",
            "purpose": "用途"}.get(head, "")


def kinds_by_shape() -> dict[str, list[str]]:
    """層の形 → その形が必ず持つ規約の種類。

    **file-catalog.md の表が正である。**写しを持たない ──
    写しを持つと写しがずれ、そのずれを守る検査が要ることになる。
    """
    out: dict[str, list[str]] = {}
    text = (REFERENCES / "file-catalog.md").read_text(encoding="utf-8")
    for tb in tables(text):
        if not tb.has("雛形", "置かれる層"):
            continue
        for row in tb.rows:
            kind = row["雛形"].strip("`").removeprefix("templates/").removesuffix(".md")
            out.setdefault(row["置かれる層"], []).append(kind)
    return out


@dataclass
class Spec:
    """規約1本。前置きの欄と、本文の節・表を持つ。"""
    path: pathlib.Path
    front: dict = field(default_factory=dict)
    axes: dict = field(default_factory=dict)     # 軸の名前 → 値
    provides: dict = field(default_factory=dict)  # この規約が指定する、他の軸の値
    body: str = ""

    @property
    def layer(self) -> str:
        return self.path.parent.name

    @property
    def kind(self) -> str:
        return self.path.stem

    @property
    def where(self) -> str:
        return str(self.path.relative_to(ROOT))

    @property
    def sections(self) -> list[str]:
        return list(sections(self.body))

    @property
    def dir_axes(self) -> dict:
        """ディレクトリ名から読み取った軸。前置きとの食い違いを見るために使う。"""
        out = {}
        for part in self.layer.split("+"):
            if "." not in part:
                continue
            prefix, value = part.split(".", 1)
            if prefix in AXIS_PREFIX:
                out[AXIS_PREFIX[prefix]] = value
        return out

    def _split(self) -> tuple[str, str]:
        """本文を、出典の節より前と、出典の節に分ける。"""
        secs = sections(self.body)
        head = "\n".join(v for k, v in secs.items() if k != SOURCE_SECTION)
        return head, secs.get(SOURCE_SECTION, "")

    @property
    def rule_ids(self) -> list[str]:
        """規則の ID。`ID` 列を持つ表のうち、出典の表を除いたものから取る。"""
        head, _ = self._split()
        ids = [v for tb in tables(head) if tb.has(ID_COLUMN) for v in tb.col(ID_COLUMN)]
        return sorted(set(ids))

    @property
    def sourced_ids(self) -> set[str]:
        """出典の表に行を持つ規則の ID。"""
        _, src = self._split()
        return {v for tb in tables(src) if tb.has(ID_COLUMN) for v in tb.col(ID_COLUMN)}

def _parse_front(text: str) -> tuple[dict, dict, dict, str]:
    """前置き（--- で囲まれた部分）を、単純な形だけ読む。

    値は文字列とし、`axes:` と `provides:` だけを写像として取り出す。
    外部の依存を持たないため、入れ子は1段だけを扱う。
    """
    if not text.startswith("---"):
        return {}, {}, {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, {}, {}, text
    head, body = text[3:end], text[end + 4:]
    front, axes, provides = {}, {}, {}
    axis_name = None
    mode = None
    for line in head.splitlines():
        if not line.strip():
            continue
        if line.startswith("axes:"):
            mode = "axes"
            continue
        if line.startswith("provides:"):
            mode = "provides"
            continue
        if mode == "axes" and line.startswith(("  - axis:", "    axis:")):
            axis_name = line.split(":", 1)[1].strip()
            continue
        if mode == "axes" and line.strip().startswith("value:"):
            axes[axis_name] = line.split(":", 1)[1].strip()
            continue
        if mode == "provides" and line.startswith("  "):
            key, _, value = line.strip().partition(":")
            provides[key.strip()] = value.strip()
            continue
        if not line.startswith(" "):
            mode = None
            key, _, value = line.partition(":")
            front[key.strip()] = value.strip()
    return front, axes, provides, body


def load_all() -> list[Spec]:
    """constraints/ 配下の規約を、すべて読む。"""
    specs = []
    for path in sorted(CONSTRAINTS.rglob("*.md")):
        if path.name == "INDEX.md":   # 生成物は規約ではない
            continue
        front, axes, provides, body = _parse_front(path.read_text(encoding="utf-8"))
        specs.append(Spec(path=path, front=front, axes=axes,
                          provides=provides, body=body))
    return specs


def load_templates() -> dict[str, str]:
    """雛形を、種類 → 本文 で返す。"""
    return {p.stem: _parse_front(p.read_text(encoding="utf-8"))[3]
            for p in sorted(TEMPLATES.glob("*.md"))}


def _slug(url: str) -> str:
    """落とした原典のファイル名。source-fidelity の付け方に合わせる。"""
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")
    return s[:120]


