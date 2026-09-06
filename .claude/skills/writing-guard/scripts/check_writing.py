# -*- coding: utf-8 -*-
"""日本語の文書を、機械で見える範囲で検査する。

  python3 check_writing.py <ファイル...>
  python3 check_writing.py --list
  python3 check_writing.py --synonyms 用語.tsv --terms 複合語.tsv --figures 借用語.tsv <ファイル...>

**この道具は3つの型でできている。**

  単位        文書を切ったもの。種別（本文・見出し・箇条書き・表のセル・引用・コード）と行番号を持つ
  検査        名前・概念・出方・**当てる単位の種別**を持つ。しきい値は検査に属する
  見つけたもの  検査の名前・概念・出方・位置・抜粋

**検査が「当てる種別」を宣言するので、外す範囲が一覧で見える。**
行の先頭で一括して外すと、外したことが誰にも見えない ──
実測（2026-09-06）で、Skill 48ファイル 3,607行のうち 1,968行（54%）が
そうやって黙って外れていた。

**規約は writing-guard Skill にある。**
  SKILL.md                      3つのレーンと3つのゲート
  references/writing-checklist.md   判定の仕方
  references/knowledge/             なぜその検査があるか（9つの概念）

**指摘は壊れている。確認は判断が要る。**
**9つの概念のうち、この検査が触れるのは6つである。**
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ── 単位の種別 ──────────────────────────────────────────────
KINDS = frozenset({"本文", "見出し", "箇条書き", "表のセル", "引用", "コード"})
# 描画されるもの。コード以外のすべて
RENDERED = KINDS - {"コード"}
# 文として読むもの。名詞句が自然な単位を除く
PROSE = frozenset({"本文", "引用"})

EXEMPT_MARK = "<!-- writing-guard: exempt -->"


@dataclass
class Unit:
    """文書を切ったもの。**位置を保つ。**"""
    kind: str
    line: int
    raw: str      # 行そのまま。描画の壊れを見るのに使う
    text: str     # インライン記法を落としたもの。文として読むのに使う


@dataclass
class Finding:
    check: str
    concept: str
    level: str    # 指摘 ／ 確認
    line: int
    excerpt: str


@dataclass
class Check:
    """検査1つ。**概念を持たない検査は置かない。**

    kinds が None のものは、文書全体を受け取る検査である。
    """
    name: str
    concept: str
    level: str
    fn: Callable
    kinds: frozenset[str] | None = None
    note: str = ""


# ── 文書を単位へ切る ────────────────────────────────────────
_HEADING = re.compile(r"^\s*#{1,6}(\s|$)")
_LIST = re.compile(r"^\s*([-*+]|\d+[.)])(\s|$)")
_QUOTE = re.compile(r"^\s*>")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_TABLE = re.compile(r"^\s*\|")
_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$")
_INLINE = re.compile(r"\*\*|`|\[|\]\([^)]*\)|<br\s*/?>")


def _plain(s: str) -> str:
    return _INLINE.sub("", s).strip()


def split_units(text: str) -> list[Unit]:
    """文書を、位置を保ったまま単位へ切る。

    **字下げされた囲いも囲いとして数える。**数えないと、その中の罫線が見えない。
    """
    units: list[Unit] = []
    lines = text.split("\n")
    fence: tuple[str, int] | None = None
    in_front = False
    for i, raw in enumerate(lines, 1):
        if i == 1 and raw.strip() == "---":
            in_front = True
            continue
        if in_front:
            if raw.strip() == "---":
                in_front = False
            continue
        m = _FENCE.match(raw)
        if m:
            run = m.group(1)
            if fence is None:
                fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1]:
                fence = None
            continue
        if fence is not None:
            units.append(Unit("コード", i, raw, raw.strip()))
            continue
        if not raw.strip():
            continue
        s = raw.lstrip()
        if _HEADING.match(s):
            units.append(Unit("見出し", i, raw, _plain(re.sub(r"^\s*#{1,6}\s*", "", s))))
        elif _QUOTE.match(s):
            units.append(Unit("引用", i, raw, _plain(re.sub(r"^\s*>\s*", "", s))))
        elif _TABLE.match(s):
            if _TABLE_SEP.match(s):
                continue
            for cell in s.strip().strip("|").split("|"):
                if cell.strip():
                    units.append(Unit("表のセル", i, raw, _plain(cell)))
        elif _LIST.match(s):
            units.append(Unit("箇条書き", i, raw, _plain(_LIST.sub("", s, count=1))))
        else:
            units.append(Unit("本文", i, raw, _plain(raw)))
    return units


# ── 単位に当てる検査 ────────────────────────────────────────
JA_PUNCT = "。、）」・：；！？"


def _emphasis_broken(u: Unit) -> list[str]:
    """閉じの ** が約物の直後にあり、直後が文字だと、閉じ記号にならない。"""
    parts, idx = [], 0
    while True:
        j = u.raw.find("**", idx)
        if j < 0:
            parts.append(u.raw[idx:])
            break
        parts.append(u.raw[idx:j])
        parts.append("\x00")
        idx = j + 2
    depth, hits = 0, []
    for k, v in enumerate(parts):
        if v != "\x00":
            continue
        depth ^= 1
        if depth:
            continue
        prev = parts[k - 1] if k else ""
        nxt = parts[k + 1] if k + 1 < len(parts) else ""
        if prev and prev[-1] in JA_PUNCT and nxt and nxt[0] not in JA_PUNCT and not nxt[0].isspace():
            hits.append(f"…{prev[-14:]}**{nxt[:10]}…")
    return hits


def _emphasis_punct_start(u: Unit) -> list[str]:
    """開きの ** の直後が約物だと、その約物まで太字になる。"""
    hits, idx, depth = [], 0, 0
    while True:
        j = u.raw.find("**", idx)
        if j < 0:
            break
        depth ^= 1
        if depth:
            nxt = u.raw[j + 2: j + 3]
            if nxt and nxt in JA_PUNCT:
                hits.append(f"…{u.raw[max(0, j - 12):j]}**{u.raw[j + 2:j + 14]}…")
        idx = j + 2
    return hits


# 箱の角と、表の交点。**木構造で使う ├ └ │ は入れない**
#   ── コードブロックは木構造に使ってよい、と規約が認めているためである。
BOX_CORNER = re.compile(r"[┌┐┘┏┓┛╭╮╯┬┴┼┤]")
# 横罫の連なり。二倍ダッシュ「──」は約物なので、4つ以上を図とみなす
BOX_RULE_MIN = 4
BOX_RULE = re.compile(r"[─━]{%d,}" % BOX_RULE_MIN)


def _box_drawing(u: Unit) -> list[str]:
    """箱・表・区切り線を、文字で描いていないかを見る。

    **二倍ダッシュと木構造は図ではない。**
    「残す ── 消すと」の ── は約物であり、`├── src` は規約が認めた木構造である。
    """
    if BOX_CORNER.search(u.raw) or BOX_RULE.search(u.raw):
        return [u.raw.strip()[:28]]
    return []


TAIL_OK = re.compile(
    r"([うくぐすつぬぶむる]|た|だ|ない|ぬ|い|ます|ません|でした|ませんでした|です|である|か|よ|ね)。$")
PAREN_TAIL = re.compile(r"[（(][^（）()]*[）)](?=。$)")
JA_RATIO_MIN = 0.35   # これ未満は日本語の文として読まない


def _ja_ratio(s: str) -> float:
    return len(re.findall(r"[ぁ-んァ-ヶ一-龥]", s)) / len(s) if s else 0.0


def _sentences(u: Unit) -> list[str]:
    if _ja_ratio(u.text) < JA_RATIO_MIN:
        return []
    return [x.strip() for x in re.split(r"(?<=。)", u.text) if x.strip()]


def _nominal_ending(u: Unit) -> list[str]:
    out = []
    for s in _sentences(u):
        s = PAREN_TAIL.sub("", s)
        if s.endswith("。") and not TAIL_OK.search(s):
            out.append(s[:28])
    return out


NOUN_CHAIN = re.compile(r"[一-龥]{6,}")
KNOWN_TERMS: set[str] = set()


def _noun_chain(u: Unit) -> list[str]:
    return [m.group(0) for m in NOUN_CHAIN.finditer(u.text)
            if not any(t in m.group(0) for t in KNOWN_TERMS)]


MAX_CHARS = 60   # 1文の目安


def _long_sentence(u: Unit) -> list[str]:
    return [f"1文が{len(s)}字（目安{MAX_CHARS}）：{s[:24]}" for s in _sentences(u) if len(s) > MAX_CHARS]


# ── 文書全体に当てる検査 ────────────────────────────────────
SYNONYM_PAIRS: list[tuple[str, str]] = []
FIGURES: list[str] = []
DUP_MIN_CHARS = 14   # これ未満の文は、重複として数えない


def _duplicate_sentence(units: list[Unit]) -> list[Finding]:
    seen: Counter = Counter()
    where: dict[str, int] = {}
    for u in units:
        if u.kind not in ("本文", "箇条書き", "引用"):
            continue
        for s in re.split(r"(?<=。)", u.text):
            s = s.strip()
            if len(s) >= DUP_MIN_CHARS:
                seen[s] += 1
                where.setdefault(s, u.line)
    return [Finding("同じ文が2か所にある", "概念1", "確認", where[s], f"{c}か所：{s[:34]}")
            for s, c in seen.items() if c > 1]


def _joined(units: list[Unit]) -> str:
    body = "\n".join(u.text for u in units if u.kind != "コード")
    for t in KNOWN_TERMS:
        body = body.replace(t, "")
    return body


def _synonym(units: list[Unit]) -> list[Finding]:
    body = _joined(units)
    return [Finding("語の揺れ", "語彙2", "指摘", 0, f"「{a}」と「{b}」が同じ文書にある")
            for a, b in SYNONYM_PAIRS if a in body and b in body]


def _figure_word(units: list[Unit]) -> list[Finding]:
    body = _joined(units)
    return [Finding("別の分野から借りた語", "概念9", "確認", 0, f"「{w}」がある")
            for w in FIGURES if w in body]


# ── 検査の名簿 ──────────────────────────────────────────────
CHECKS: list[Check] = [
    Check("強調が描画されない", "概念8", "指摘", _emphasis_broken, RENDERED,
          "閉じの ** が約物の直後にあると、閉じ記号として認められない"),
    Check("強調が句点から始まる", "概念8", "指摘", _emphasis_punct_start, RENDERED,
          "開きの ** の直後が約物だと、その約物まで太字になる"),
    Check("ASCII で図を描いている", "概念2", "指摘", _box_drawing, KINDS,
          "囲いの中でも外でも見る。図は mermaid か SVG で書く"),
    Check("体言止め", "概念5", "確認", _nominal_ending, PROSE,
          "見出し・表のセル・箇条書きでは名詞句が自然なので、当てない"),
    Check("名詞を連ねている", "概念5", "確認", _noun_chain, RENDERED,
          "読みにくさは、置かれた場所で変わらない"),
    Check("1文が長い", "概念6", "確認", _long_sentence, PROSE,
          "散文の1文を測る。見出し・表のセル・箇条書きは、圧縮された項目なので測らない"),
    Check("同じ文が2か所にある", "概念1", "確認", _duplicate_sentence, None,
          "本文・箇条書き・引用だけを数える"),
    Check("語の揺れ", "語彙2", "指摘", _synonym, None, "--synonyms で対を与える"),
    Check("別の分野から借りた語", "概念9", "確認", _figure_word, None, "--figures で一覧を与える"),
]


def all_checks() -> list[Check]:
    return CHECKS


def inspect(path: str | Path) -> list[Finding]:
    """1つの文書を検査し、見つけたものを返す。"""
    raw = Path(path).read_text(encoding="utf-8")
    if EXEMPT_MARK in raw[:400]:
        return []
    units = split_units(raw)
    out: list[Finding] = []
    for c in CHECKS:
        if c.kinds is None:
            out += c.fn(units)
            continue
        for u in units:
            if u.kind not in c.kinds:
                continue
            for ex in c.fn(u):
                out += [Finding(c.name, c.concept, c.level, u.line, ex)]
    # 同じ検査・同じ行・同じ抜粋は1件にする（表のセルで同じ行を何度も見るため）
    seen, uniq = set(), []
    for f in out:
        key = (f.check, f.line, f.excerpt)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(f)
    return uniq


# ── 入口 ────────────────────────────────────────────────────
def load_lines(p: Path) -> list[str]:
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


def load_synonyms(p: Path) -> list[tuple[str, str]]:
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            out.append((parts[0].strip(), parts[1].strip()))
    return out


def print_checks() -> int:
    print(f"{'検査':22}{'概念':6}{'出方':5}{'当てる単位'}")
    for c in CHECKS:
        kinds = "文書全体" if c.kinds is None else " ・ ".join(sorted(c.kinds))
        print(f"{c.name:22}{c.concept:6}{c.level:5}{kinds}")
        if c.note:
            print(f"{'':33}{c.note}")
    return 0


def main(argv: list[str]) -> int:
    global SYNONYM_PAIRS, KNOWN_TERMS, FIGURES
    args = list(argv)

    def take(flag):
        if flag in args:
            i = args.index(flag)
            v = args[i + 1]
            del args[i:i + 2]
            return Path(v)
        return None

    p = take("--synonyms")
    if p:
        SYNONYM_PAIRS = load_synonyms(p)
    p = take("--figures")
    if p:
        FIGURES = load_lines(p)
    p = take("--terms")
    if p:
        KNOWN_TERMS = set(load_lines(p))
    if "--list" in args:
        return print_checks()
    if not args:
        print(__doc__)
        return 2

    issues, notes = [], []
    for a in args:
        for f in inspect(a):
            row = f"{Path(a).name}:{f.line} [{f.concept}] {f.check}：{f.excerpt}"
            (issues if f.level == "指摘" else notes).append(row)
    for x in issues:
        print("指摘  " + x)
    for x in notes:
        print("確認  " + x)
    print(f"\n指摘 {len(issues)} 件 / 確認 {len(notes)} 件 / 対象 {len(args)} ファイル")
    print("**指摘は壊れている。直す。**")
    print("**確認は判断が要る。読んで、そのままでよければ残す。**")
    print("**この検査が触れるのは9つの概念のうち6つである。**"
          "**外している範囲は `--list` で見られる。**")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
