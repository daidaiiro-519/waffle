"""段2：鍵と値の保管の偽物を1つに寄せ、記録を見せる面の名前を1つに決める。

3つあった。記録を見せる名前が2種類に分かれ、書き込みの失敗を作れるのは
3つのうち1つだけだった——つまり失敗する経路を確かめられない偽物が2つ残っていた。
同じ形の事故が既に一度起きており、その記録が偽物のファイル自身に残っている。
"""
from __future__ import annotations

import pathlib
import re

TESTS = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/tests")

# ── 1. 唯一の偽物を書き直す ──────────────────────────
FAKE = '''class FakeKeyStore:
    """閲覧の面へ渡す鍵の置き場の偽物。書き込みを失敗させることもできる。

    この口に読み取りは無い。業務のLambdaは書くだけで、読むのは別のランタイム
    （閲覧ゲート）だからである。検証が書いたものを見たいときは written を直接見る
    ——口の読み取りとして確かめると、本番に無い経路を固定することになる。
    """

    def __init__(self, written=None, fail=False):
        self.written = dict(written or {})
        self.fail = fail

    def put(self, key, value):
        if self.fail:
            raise RuntimeError("トークンの保管に失敗しました")
        self.written[key] = value
'''

p = TESTS / "fakes.py"
t = p.read_text(encoding="utf-8")
start = t.index("class FakeKeyStore:")
end = t.index("class FakeIdGenerator:")
t = t[:start] + FAKE + "\n\n" + t[end:]
p.write_text(t, encoding="utf-8")
print("書き直した: fakes.py の FakeKeyStore")

# ── 2. 別々に育っていた2つを消し、唯一のものへ向ける ──
p = TESTS / "view_token_setup.py"
t = p.read_text(encoding="utf-8")
t = re.sub(r"class FakeKeys:\n(?:.*\n)*?        return self\.written\[key\]\n\n\n", "", t, count=1)
t = t.replace("gate = KvsViewGate(FakeKeys())", "gate = KvsViewGate(FakeKeyStore())", 1)
if "FakeKeyStore" not in t.split("AID =")[0]:
    t = t.replace("from fakes import FakeIdGenerator  # noqa: E402",
                  "from fakes import FakeIdGenerator, FakeKeyStore  # noqa: E402", 1)
p.write_text(t, encoding="utf-8")
print("消した: view_token_setup.py の FakeKeys")

p = TESTS / "adapters/inbound/contract/test_token_record_contract.py"
t = p.read_text(encoding="utf-8")
t = re.sub(r"class _Collector:\n(?:.*\n)*?        self\.written\[key\] = value\n", "", t, count=1)
t = t.replace("_Collector()", "FakeKeyStore()")
if "from fakes import" not in t:
    t = t.replace("from conftest import SKILL",
                  "from conftest import SKILL\nfrom fakes import FakeKeyStore", 1)
p.write_text(t, encoding="utf-8")
print("消した: test_token_record_contract.py の _Collector")

# ── 3. 口の読み取りで読み返していた箇所を、記録の面へ寄せる ──
changed = 0
for path in sorted(TESTS.rglob("*.py")):
    if "__pycache__" in path.parts:
        continue
    t = original = path.read_text(encoding="utf-8")
    # deps.keys.get(X) / keys.get(X) → .written[X]
    t = re.sub(r"\b(\w+(?:\.\w+)*?)\.keys\.get\(([^()]*(?:\([^()]*\))?[^()]*)\)",
               r"\1.keys.written[\2]", t)
    # .keys.keys → .keys.written（記録そのものを見ている箇所）
    t = t.replace(".keys.keys", ".keys.written")
    # 単独の keys.keys（局所変数）
    t = re.sub(r"(?<![.\w])keys\.keys\b", "keys.written", t)
    t = re.sub(r"(?<![.\w])keys\.get\(([^()]*)\)", r"keys.written[\1]", t)
    if t != original:
        path.write_text(t, encoding="utf-8")
        changed += 1
print(f"記録の面へ寄せた: {changed} ファイル")
