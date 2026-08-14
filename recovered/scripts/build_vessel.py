"""器の具体イメージ ── 中身3種と、場面の扱い2案を並べる。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from figures import render          # noqa: E402
from styles import CSS              # noqa: E402

def term(title, lines):
    return {"title": title, "lines": lines}

C = lambda t: {"kind": "comment", "text": t}     # noqa: E731
O = lambda t: {"kind": "output", "text": t}      # noqa: E731

# 場面1 ── 参照整合の検査
S1_BEFORE = term("check-spec-integrity", [
    C("# 宣言を新しい置き場所へ書き換えたあと"),
    O("$ waffle check-spec-integrity --path …/bc-waffle.json"),
    O('{"declared_subdomains_missing_on_disk": [],'),
    O(' "subdomain_ref_mismatches": []}'),
    C("↑ 古い場所を見て「違反なし」。書き換えが効いていない"),
])
S1_AFTER = term("check-spec-integrity", [
    C("# 同じ操作"),
    O("$ waffle check-spec-integrity --path …/bc-waffle.json"),
    O('{"declared_subdomains_missing_on_disk":'),
    O('   ["sd-validation", "sd-reconciliation", …7件],'),
    O('  "usecase_files_missing_on_disk": [ …28件 ]}'),
    C("↑ 宣言された場所を見て、そこに無いと言う"),
])
# 場面2 ── 実装ファイルの保存
S2_BEFORE = term("保存時の応答", [
    C("# src/waffle/… を保存"),
    O("（何も出ない）"),
    C("↑ 仕様を0件と判定し「対象外」として通した"),
])
S2_AFTER = term("保存時の応答", [
    C("# src/waffle/… を保存"),
    O("✗ 実装の前に引き継ぎが要ります"),
    O("  仕様 28件 に対応する引き継ぎが見つかりません"),
    C("↑ 宣言から仕様を引いたので28件見つかる"),
])

def side(at, label, groups, note=None):
    d = {"at": at, "label": label, "groups": groups}
    if note: d["note"] = note
    return d

# 案A ── 1つの器が、場面を並べて持つ
PLAN_A = {"kind": "comparison", "sides": [
    side("before", "変更前", [
        {"contentKind": "transcript", "label": "場面1 参照整合を確かめる", "content": S1_BEFORE},
        {"contentKind": "transcript", "label": "場面2 実装ファイルを保存する", "content": S2_BEFORE}],
        "止まらなかったことに、誰も気づけない"),
    side("after", "変更後", [
        {"contentKind": "transcript", "label": "場面1 参照整合を確かめる", "content": S1_AFTER},
        {"contentKind": "transcript", "label": "場面2 実装ファイルを保存する", "content": S2_AFTER}],
        "引けなければ止まる"),
]}

# 案B ── 場面ごとに器を分ける
PLAN_B1 = {"kind": "comparison", "sides": [
    side("before", "変更前", [{"contentKind": "transcript", "content": S1_BEFORE}]),
    side("after", "変更後", [{"contentKind": "transcript", "content": S1_AFTER}]),
]}
PLAN_B2 = {"kind": "comparison", "sides": [
    side("before", "変更前", [{"contentKind": "transcript", "content": S2_BEFORE}],
         "止まらなかったことに、誰も気づけない"),
    side("after", "変更後", [{"contentKind": "transcript", "content": S2_AFTER}],
         "引けなければ止まる"),
]}

# 中身3種の見本
INNER_TREE = {"kind": "comparison", "sides": [
    side("before", "変更前", [{"contentKind": "tree", "content": {
        "name": "区切られた文脈", "children": [
            {"name": "業務領域", "role": "removed", "children": [
                {"name": "中核"}, {"name": "一般"}, {"name": "補完"}]},
            {"name": "集約"}, {"name": "業務ユースケース"}]}}],
        "親は1つしか持てない"),
    side("after", "変更後", [{"contentKind": "tree", "content": {
        "name": "事業領域", "children": [
            {"name": "業務領域", "role": "added", "children": [
                {"name": "中核"}, {"name": "一般"}, {"name": "補完"}]}]}}],
        "対応は参照が運ぶ"),
]}

INNER_LIST = {"kind": "comparison", "sides": [
    side("before", "変更前", [{"contentKind": "listing", "label": "ブロック", "content": {"items": [
        {"name": "受け入れ基準"}, {"name": "保証シナリオ"},
        {"name": "操作保証", "role": "removed"}, {"name": "操作の一覧", "role": "removed"},
        {"name": "参照"}]}}]),
    side("after", "変更後", [{"contentKind": "listing", "label": "ブロック", "content": {"items": [
        {"name": "受け入れ基準"}, {"name": "保証シナリオ"},
        {"name": "帰る先", "role": "added"}, {"name": "参照"}]}}],
        "2つ落として1つ足した"),
]}