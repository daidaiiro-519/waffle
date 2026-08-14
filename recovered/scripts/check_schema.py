"""16の主張それぞれについて、schemaが規則どおりに通し・落とすかを見る。"""
import sys, pathlib, jsonschema
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "notation"))
from figure_schema import build, NEED

S = build()
FILL = {"items": [{"name": "あ"}, {"name": "い"}],
        "links": [{"from": "あ", "to": "い"}],
        "frame": {"axes": [{"unit": "第1"}]}}

def ok(doc):
    try:
        jsonschema.validate(doc, S); return True
    except jsonschema.ValidationError:
        return False

fails = []
for claim, rule in NEED.items():
    base = {"asserts": claim, "reading": "読み方"}
    for k in rule["+"]:
        base[k] = FILL[k]
    if not ok(base):
        fails.append(f"{claim}: 必須だけの形が通らない")
    for k in rule["+"]:                      # 必須を欠いたら落ちるか
        d = dict(base); d.pop(k)
        if ok(d):
            fails.append(f"{claim}: {k} が無くても通ってしまう")
    for k in rule["-"]:                      # 禁止を書いたら落ちるか
        d = dict(base); d[k] = FILL[k]
        if ok(d):
            fails.append(f"{claim}: {k} を書いても通ってしまう")

# 木の深さに上限が無いこと ── 子を10段
deep = {"name": "根"}
cur = deep
for i in range(10):
    cur["children"] = [{"name": f"{i}段目"}]
    cur = cur["children"][0]
if not ok({"asserts": "階層", "reading": "読み方", "items": [deep]}):
    fails.append("子を10段にすると落ちる（木に上限があってはいけない）")

# 図の入れ子は3段まで、4段目は落ちる
def nest(n):
    f = {"asserts": "包含", "reading": "読み方", "items": [{"name": "端"}]}
    for _ in range(n - 1):
        f = {"asserts": "包含", "reading": "読み方", "items": [{"name": "外", "figure": f}]}
    return f
if not ok(nest(3)):
    fails.append("図の入れ子3段が通らない")
if ok(nest(4)):
    fails.append("図の入れ子4段が通ってしまう")

print("\n".join(fails) if fails else
      f"{len(NEED)}種すべて規則どおり／木は無制限・図の入れ子は3段まで")