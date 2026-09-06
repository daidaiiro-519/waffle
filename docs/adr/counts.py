"""第1版と第2版の数を、両方から数える。

**手で書かない。**第1版の `references/file-catalog.md` は
「落とした原文 41」と書いていたが、実際は 81 本だった ── 手書きの数は腐る。
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
REL = ".waffle/skills/coding-skills"
SK = ROOT / REL
BASE = "9d99557"

sys.path.insert(0, str(SK / "scripts"))
from _common import SOURCES, Spec, _parse_front, load_all  # noqa: E402


def _sh(*a):
    return subprocess.run(a, cwd=ROOT, capture_output=True, text=True).stdout


def old_state():
    ls = _sh("git", "ls-tree", "-r", "--name-only", BASE, "--", REL).splitlines()
    cons = [p for p in ls if "/constraints/" in p and not p.endswith("INDEX.md")]
    srcs = [p for p in ls if "/sources/" in p and not p.endswith(".meta.json")]
    specs = []
    for p in cons:
        front, _, _, body = _parse_front(_sh("git", "show", f"{BASE}:{p}"))
        specs.append(Spec(path=ROOT / p, front=front, body=body))
    return specs, len(srcs)


def _unsourced(specs):
    return sum(len([r for r in s.rule_ids if r not in s.sourced_ids]) for s in specs)


def rows():
    o, o_src = old_state()
    n = load_all()
    n_src = len([p for p in SOURCES.iterdir()
                 if p.is_file() and not p.name.endswith(".meta.json")])
    tests = len(re.findall(r"\n    def test_",
                           (SK / "scripts/tests.py").read_text(encoding="utf-8")))
    return [
        ("規約", f"{len(o)} 本", f"{len(n)} 本"),
        ("規則", f"{sum(len(s.rule_ids) for s in o)} 件",
         f"{sum(len(s.rule_ids) for s in n)} 件"),
        ("出典を持たない規則", f"{_unsourced(o)} 件", f"{_unsourced(n)} 件"),
        ("出典の行", f"{sum(len(s.source_rows) for s in o)} 行",
         f"{sum(len(s.source_rows) for s in n)} 行"),
        ("承認が記録された規約",
         f"{sum(1 for s in o if s.front.get('approved_by'))} / {len(o)} 本",
         f"{sum(1 for s in n if s.front.get('approved_by'))} / {len(n)} 本"),
        ("落としてある原文", f"{o_src} 本", f"{n_src} 本"),
        ("scripts のテスト", "0 件", f"{tests} 件"),
    ]


if __name__ == "__main__":
    for k, a, b in rows():
        print(f"  {k:<22} {a:>12} → {b}")
