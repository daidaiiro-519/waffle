"""規約のファイルを読み、前置きと本文に分ける。

このファイルは、collect ・ check ・ index が共有する読み取りだけを持つ。
判断はここに置かない ── 何を集め、何を落とすかは、呼ぶ側が決める。
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONSTRAINTS = ROOT / "constraints"

# 軸の名前と、ディレクトリ名での接頭辞
AXIS_PREFIX = {"lang": "language", "arch": "architecture",
               "purpose": "purpose", "runtime": "runtime"}


@dataclass
class Spec:
    """規約1本。前置きの欄と、本文の見出しを持つ。"""
    path: pathlib.Path
    front: dict = field(default_factory=dict)
    axes: dict = field(default_factory=dict)     # 軸の名前 → 値
    provides: dict = field(default_factory=dict)  # この規約が指定する、他の軸の値
    sections: list = field(default_factory=list)  # 本文の見出し
    body: str = ""

    @property
    def layer(self) -> str:
        return self.path.parent.name

    @property
    def kind(self) -> str:
        return self.path.stem

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
        text = path.read_text(encoding="utf-8")
        front, axes, provides, body = _parse_front(text)
        sections = re.findall(r"^## (.+)$", body, re.M)
        specs.append(Spec(path=path, front=front, axes=axes, provides=provides,
                          sections=sections, body=body))
    return specs


def rule_ids(spec: Spec) -> list[str]:
    """規則一覧の表から、ID を取り出す。"""
    ids = []
    for line in spec.body.splitlines():
        m = re.match(r"^\|\s*([A-Z][A-Z0-9-]{2,})\s*\|", line)
        if m:
            ids.append(m.group(1))
    return sorted(set(ids))
