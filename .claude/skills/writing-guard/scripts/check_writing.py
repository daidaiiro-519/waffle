"""日本語の文書を、機械で見える範囲で検査する。

検査は1つずつ、knowledge の概念に紐づいている。
概念を持たない検査は置かない。

規約は writing-guard Skill にある。
  .claude/skills/writing-guard/SKILL.md            5つの観点
  .claude/skills/writing-guard/references/         判定の仕方と知識

  指摘  壊れているもの。概念2・概念8・語彙2
  確認  判断が要るもの。概念1・概念5・概念6・概念9

9つの概念のうち、この検査が触れるのは6つである。
**概念3・4・7には触れない。読み手を立てて確かめること。**

使い方
  python3 check_writing.py <ファイル...>
  python3 check_writing.py --synonyms 用語.tsv --figures 借用語.tsv <ファイル...>

  用語.tsv   は、同じ意味に当ててはいけない語の対を、タブ区切りで1行1対。
  借用語.tsv は、別の分野から借りた語を1行1語。現れたら確認を出す。
"""
import re, sys
from pathlib import Path

MAX_CHARS = 60

# 同じものを指す語の対。両方が同じ文書に現れたら知らせる。
# --synonyms で外から与える。既定は空にする。
SYNONYM_PAIRS: list[tuple[str, str]] = []

# 別の分野から借りた語。現れたら確認を出す。
# あえて例えると断れば使ってよいので、指摘ではなく確認にする。
# --figures で外から与える。既定は空にする。
FIGURES: list[str] = []

# ASCII で図を描いた跡。罫線素片だけを見る。
# 一覧の注記に使う矢印は図ではないので拾わない。
BOX_DRAWING = re.compile(r"[─│┌┐└┘├┤┬┴┼━┃┏┓┗┛╭╮╰╯╱╲]")

# 述語で終わっているか。動詞の終止形・形容詞・断定・否定を認める
TAIL_OK = re.compile(r"([うくぐすつぬぶむる]|た|だ|ない|ぬ|い|ます|ません|でした|ませんでした|です|である|か|よ|ね)。$")
# 末尾の括弧書きは判定の前に外す
PAREN_TAIL = re.compile(r"[（(][^（）()]*[）)](?=。$)")
# 名詞の連結。漢字が6字以上続くものを疑う。
# ただし定着した複合語は連結ではない。--terms で外から与える。
NOUN_CHAIN = re.compile(r"[一-龥]{6,}")
KNOWN_TERMS: set[str] = set()


def japanese_ratio(text: str) -> float:
    if not text:
        return 0.0
    return len(re.findall(r"[ぁ-んァ-ヶ一-龥]", text)) / len(text)


SYNONYM_EXEMPT: set[str] = set()

# 和文の約物。強調の閉じ記号がこの直後にあると、描画されないことがある
JA_PUNCT = "。、）」・：；！？"


def broken_emphasis(line: str) -> list[str]:
    """描画されない強調を探す。

    CommonMark では、閉じの ** が約物の直後にあり、
    かつ直後が文字であるとき、閉じ記号として認められない。
      壊れる    **文である。**続き
      描画される **文である**。続き
    """
    idx = 0
    toks: list[str] = []
    while idx < len(line):
        j = line.find("**", idx)
        if j < 0:
            toks.append(line[idx:])
            break
        toks.append(line[idx:j])
        toks.append("\x00")
        idx = j + 2
    depth = 0
    hits = []
    for k, v in enumerate(toks):
        if v != "\x00":
            continue
        depth ^= 1
        if depth:
            continue
        prev = toks[k - 1] if k else ""
        nxt = toks[k + 1] if k + 1 < len(toks) else ""
        if prev and prev[-1] in JA_PUNCT and nxt and nxt[0] not in JA_PUNCT and not nxt[0].isspace():
            hits.append(f"…{prev[-14:]}**{nxt[:10]}…")
    return hits


def emphasis_starts_with_punct(line: str) -> list[str]:
    """句点から始まる強調を探す。

    強調が約物から始まると、その約物まで太字になる。
      壊れる    …出てこない**。偏りを均すために…である**
      描画される …出てこない。**偏りを均すために…である**
    """
    hits = []
    idx = 0
    depth = 0
    while True:
        j = line.find("**", idx)
        if j < 0:
            break
        depth ^= 1
        if depth:  # 開きの **
            nxt = line[j + 2 : j + 3]
            if nxt and nxt in JA_PUNCT:
                hits.append(f"…{line[max(0, j - 12):j]}**{line[j + 2:j + 14]}…")
        idx = j + 2
    return hits

# この印を先頭に持つ文書は、悪い例を引用するため検査から外す
EXEMPT_MARK = "<!-- writing-guard: exempt -->"


def strip_frontmatter(raw: str) -> tuple[str, int]:
    """YAML frontmatter を外す。外した行数を返す。"""
    if not raw.startswith("---\n"):
        return raw, 0
    end = raw.find("\n---\n", 4)
    if end < 0:
        return raw, 0
    head = raw[: end + 5]
    return raw[end + 5 :], head.count("\n")


def check(path: Path) -> tuple[list[str], list[str]]:
    found: list[str] = []
    notes: list[str] = []
    raw = path.read_text(encoding="utf-8")
    if EXEMPT_MARK in raw[:400]:
        return found, notes
    body, offset = strip_frontmatter(raw)
    lines = body.split("\n")

    in_block = False
    for n0, line in enumerate(lines, 1):
        n = n0 + offset
        if line.startswith("```"):
            in_block = not in_block
            continue
        if in_block:
            if BOX_DRAWING.search(line):
                found.append(f"{path.name}:{n} [概念2] ASCII で図を描いている")
            continue
        stripped_line = line.lstrip()
        # 箇条書きは「- 」「* 」。`**強調**` を箇条書きと見なさない
        if (not line.strip()
                or stripped_line.startswith(("#", ">"))
                or re.match(r"[-*]\s", stripped_line)):
            continue
        is_table = line.lstrip().startswith("|")
        if is_table:
            # 表の区切り行は見ない
            if set(line.replace("|", "").replace(" ", "")) <= {"-", ":"}:
                continue
            # セルは1つずつ見る。つなぐと、セルの境目に無い文を作ってしまう
            raw_units = [c for c in line.strip().strip("|").split("|") if c.strip()]
        else:
            raw_units = [line]
        for unit in raw_units:
            text = re.sub(r"\*\*|`|\[|\]\([^)]*\)|<br>|<br/>", "", unit).strip()
            if japanese_ratio(text) < 0.35:
                continue
            sentences = [x for x in re.split(r"(?<=。)", text) if x.strip()]
            if not is_table:
                # 規約は1文。行ではなく文で測る
                for sentence in sentences:
                    if len(sentence) > MAX_CHARS:
                        notes.append(
                            f"{path.name}:{n} [概念6] 1文が{len(sentence)}字（目安{MAX_CHARS}）")
            # 文ごとに見る。行の最後の文だけを見ると、途中の断片を見逃す
            for sentence in sentences:
                stripped = PAREN_TAIL.sub("", sentence.strip())
                if stripped.endswith("。") and not TAIL_OK.search(stripped):
                    notes.append(f"{path.name}:{n} [概念5] 述語で終わっていない：{stripped[:28]}")
            # 描画されない強調
            for h in broken_emphasis(line):
                found.append(f"{path.name}:{n} [概念8] 強調が描画されない：{h}")
            for h in emphasis_starts_with_punct(line):
                found.append(f"{path.name}:{n} [概念8] 強調が句点から始まる：{h}")
            # 名詞の連結。定着した複合語は外す
            for m in NOUN_CHAIN.finditer(text):
                if any(t in m.group(0) for t in KNOWN_TERMS):
                    continue
                notes.append(f"{path.name}:{n} [概念5] 名詞を連ねている：{m.group(0)}")

    # 定着した複合語を先に外す。型変換のように、別の意味で同じ字を使う語があるため
    stripped = raw
    for t in KNOWN_TERMS:
        stripped = stripped.replace(t, "")
    for a, b in SYNONYM_PAIRS:
        if path.name in SYNONYM_EXEMPT:
            break
        if a in stripped and b in stripped:
            found.append(f"{path.name} [語彙2] 語の揺れ「{a}」と「{b}」が同じ文書にある")
    for w in FIGURES:
        if w in stripped:
            notes.append(f"{path.name} [概念9] 別の分野から借りた語「{w}」がある")
    return found, notes



def check_duplicates(path: Path) -> list[str]:
    """同じ文が2か所に無いかを見る。観点2の一部。"""
    from collections import Counter
    raw = path.read_text(encoding="utf-8")
    if EXEMPT_MARK in raw[:400]:
        return []
    body, _ = strip_frontmatter(raw)
    lines = body.split("\n")
    in_block = False
    seen: Counter = Counter()
    for line in lines:
        if line.startswith("```"):
            in_block = not in_block
            continue
        if in_block or not line.strip() or line.lstrip().startswith(("|", "#", ">")):
            continue
        text = re.sub(r"\*\*|`", "", line)
        for s in re.split(r"(?<=。)", text):
            s = s.strip()
            if len(s) >= 14:
                seen[s] += 1
    return [f"{path.name} [概念1] 同じ文が{c}か所にある：{s[:34]}"
            for s, c in seen.items() if c > 1]


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


def main(argv: list[str]) -> int:
    global SYNONYM_PAIRS, KNOWN_TERMS, FIGURES
    args = list(argv)
    if "--synonyms" in args:
        i = args.index("--synonyms")
        SYNONYM_PAIRS = load_synonyms(Path(args[i + 1]))
        del args[i:i + 2]
    if "--figures" in args:
        i = args.index("--figures")
        FIGURES = load_lines(Path(args[i + 1]))
        del args[i:i + 2]
    if "--terms" in args:
        i = args.index("--terms")
        KNOWN_TERMS = set(load_lines(Path(args[i + 1])))
        del args[i:i + 2]
    if not args:
        print(__doc__)
        return 2
    targets = [Path(a) for a in args]
    issues: list[str] = []
    notes: list[str] = []
    for p in targets:
        i, n = check(p)
        issues += i
        notes += n
        notes += check_duplicates(p)
    for x in issues:
        print("指摘  " + x)
    for x in notes:
        print("確認  " + x)
    print(f"\n指摘 {len(issues)} 件 / 確認 {len(notes)} 件 / 対象 {len(targets)} ファイル")
    print("**指摘は壊れている。直す。**")
    print("**確認は判断が要る。読んで、そのままでよければ残す。**")
    print("**9つの概念のうち触れるのは6つである。概念3・4・7は読み手を立てて確かめる。**")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
