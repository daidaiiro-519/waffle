"""scenario_drift — spec の TestScenarios が宣言するシナリオと、テストコードの
文書コメントを突き合わせる純粋なドメインサービス。

突き合わせのキーは、テストの文書コメントに置かれた宣言行
「Scenario: {シナリオ名}」。テストの名前は突き合わせに使わない。

以前はシナリオ名を識別子へ変換した文字列（非単語文字を _ に置換し test_ を
前置したもの）をキーにしていた。これは仕様の語彙をそのまま識別子にできる
言語でしか成立せず、変換が非可逆なため句読点や空白の違うシナリオが同じキーへ
潰れる余地もあった。宣言行へ移したことで、テストの名前は対象言語の命名慣習に
従った任意の識別子でよくなる。

この層は対象言語の構文解析技術を知らない。テストの名前と文書コメントの
取り出しは TestFunctionExtractor port が担う。
"""
from __future__ import annotations

import re

from waffle.domain.services.canonical_naming import apply_case

_SCENARIO_BLOCK_KEYS = (
    "acceptanceScenarios",
    "guaranteeScenarios",
    "invariantScenarios",
    "domainServiceScenarios",
)

_DECLARATION = re.compile(r"^Scenario(?:\s+Outline)?:\s*(?P<name>.+?)\s*$")

def expected_test_dir(binding: dict, block: str) -> str | None:
    """シナリオ種別に対応するテストの配置を、規約の宣言から導く。

    種別と（層・テスト種別）の対応は scenarioBinding が、その組がどのパスへ
    置かれるかは placementByTarget が宣言する。どちらもコード側には持たない。

    Args:
        binding: 解決済みのシナリオ照合宣言（blockPlacement と placements）。
        block: シナリオブロックの種別。

    Returns:
        配置パス。宣言が無ければ None。
    """
    placements = binding.get("placements", {})
    for row in binding.get("blockPlacement", []):
        if row.get("block") == block:
            return placements.get((row.get("layer"), row.get("testType")))
    return None


REQUIRED_NAMING_FIELDS = ("derivedFrom", "strip", "prefix", "case", "infix", "suffix")


def missing_naming_fields(naming: dict) -> list[str]:
    """テストファイル名を組み立てるのに足りない宣言を返す。

    欠けた宣言を空とみなして続けると、規約の書き損じが正しい名前として通る。
    空が正しい値になる欄（前置・中置）があるため、未宣言と「空を宣言した」を
    区別する必要がある。よってキーの有無を見る。

    Args:
        naming: test-standard の testFileNaming ブロック。

    Returns:
        足りない欄の名前。全て揃っていれば空。
    """
    return [f for f in REQUIRED_NAMING_FIELDS if f not in naming]


def test_file_name(document_id: str, naming: dict) -> str:
    """仕様の識別子から、規約が宣言した形のテストファイル名を組み立てる。

    綴りの規則はここに持たない。落とす接頭辞・前置・表記・中置・末尾は
    すべて宣言から来る。置き場所が既に表している区別（仕様の種別など）は
    落とす接頭辞で取り除く。

    Args:
        document_id: 対応する仕様の識別子。
        naming: test-standard の testFileNaming ブロック。

    Returns:
        拡張子まで含むテストファイル名。

    Raises:
        ValueError: 宣言に無い表記や、対応していない由来を指定された場合。
    """
    derived_from = naming.get("derivedFrom")
    if derived_from != "spec-document-id":
        raise ValueError(
            f"対応していない由来です: {derived_from}"
            "（いま組み立てられるのは spec-document-id のみ）")

    base = document_id
    for prefix in naming.get("strip", []):
        if prefix and base.startswith(prefix):
            base = base[len(prefix):]
            break

    return (naming["prefix"] + apply_case(base, naming["case"])
            + naming["infix"] + naming["suffix"])


def declaration_line(scenario_name: str) -> str:
    """シナリオの名前から、突き合わせのキーとなる宣言行を組み立てる。

    名前を唯一の正とし、gherkin本文中の見出し行は信用しない。名前が二箇所に
    存在すると、片方だけ直されたときにどちらが正しいか機械では決まらない。

    Args:
        scenario_name: シナリオの名前。

    Returns:
        突き合わせのキーとなる宣言行。

    Raises:
        なし。
    """
    return f"Scenario: {scenario_name}"


def declaration_of(doc_text: str) -> str | None:
    """文書コメントから宣言行を取り出す。無ければ None。

    先頭行である必要はない。自分の言葉での説明を前に書いてよい。
    飾り（三重引用符・ブロックコメントの記号等）は adapter が落とし済み。

    Args:
        doc_text: テストの文書コメントの本文。

    Returns:
        見つかった宣言行。無ければ None。

    Raises:
        なし。
    """
    for line in doc_text.splitlines():
        matched = _DECLARATION.match(line.strip())
        if matched:
            return declaration_line(matched.group("name"))
    return None


def gherkin_lines(gherkin: str) -> list[str]:
    """gherkin文字列を、前後の空白を落とした非空行の並びにする。

    見出し行を除かない。見出し行は突き合わせのキーそのものであり、転記の
    対象から外すと、キーがテストの中に現れなくなる。

    Args:
        gherkin: シナリオのgherkin本文。

    Returns:
        前後の空白を落とした非空行の並び。

    Raises:
        なし。
    """
    return [line.strip() for line in gherkin.strip().splitlines() if line.strip()]


def relevant_scenario_block_keys(test_file_path: str, binding: dict) -> tuple[str, ...]:
    """テストの配置から、突き合わせ対象のシナリオ種別を絞り込む。

    どの配置がどの種別に対応するかは規約が宣言する。いずれの配置にも
    当てはまらないパスは絞り込まず全種を対象にする（ケースバイケースの
    判定はしない）。

    Args:
        test_file_path: テストファイルのパス。
        binding: 解決済みのシナリオ照合宣言。

    Returns:
        対象とするシナリオブロック種別。
    """
    placements = binding.get("placements", {})
    matched = tuple(
        row["block"] for row in binding.get("blockPlacement", [])
        if (path := placements.get((row.get("layer"), row.get("testType"))))
        and path in test_file_path)
    return matched or _SCENARIO_BLOCK_KEYS


def scenario_declarations(
    spec_doc: dict, block_keys: tuple[str, ...] = _SCENARIO_BLOCK_KEYS
) -> dict[str, dict]:
    """spec document から 宣言行 -> {name, gherkin} のマップを作る。

    Args:
        spec_doc: 対象のspec document。
        block_keys: 対象とするシナリオブロックの種別。省略すると全種。

    Returns:
        宣言行をキーに、シナリオの名前とgherkin本文の行を持つマップ。

    Raises:
        なし。
    """
    content = spec_doc.get("content", {})
    result: dict[str, dict] = {}
    for block_key in block_keys:
        block = content.get(block_key)
        if not block:
            continue
        for scenario in block.get("scenarios", []):
            name = scenario["name"]
            result[declaration_line(name)] = {
                "name": name,
                "gherkin": gherkin_lines(scenario.get("gherkin", "")),
            }
    return result


def spec_internal_mismatches(
    spec_doc: dict, block_keys: tuple[str, ...] = _SCENARIO_BLOCK_KEYS
) -> list[str]:
    """spec自身の gherkin 先頭の宣言行が、シナリオの名前と食い違うものを返す。

    名前が二箇所に存在するため、どちらが正かを機械が決められる状態を保つ。

    Args:
        spec_doc: 対象のspec document。
        block_keys: 対象とするシナリオブロックの種別。省略すると全種。

    Returns:
        食い違っているシナリオの説明の一覧。食い違いが無ければ空配列。

    Raises:
        なし。
    """
    content = spec_doc.get("content", {})
    mismatched: list[str] = []
    for block_key in block_keys:
        block = content.get(block_key)
        if not block:
            continue
        for scenario in block.get("scenarios", []):
            lines = gherkin_lines(scenario.get("gherkin", ""))
            # Scenario Outline: も Gherkin の正規の書き方なので受け入れる。
            # 見出しの種類ではなく、そこに書かれた名前が正と一致するかを見る
            declared = declaration_of(lines[0]) if lines else None
            if declared != declaration_line(scenario["name"]):
                mismatched.append(scenario["name"])
    return mismatched


def scenario_blocks(spec_doc: dict) -> dict[str, int]:
    """この document が宣言しているシナリオブロックと、その件数を返す。

    Args:
        spec_doc: 対象のspec document。

    Returns:
        シナリオを持つブロックの種別をキーに、その件数を持つマップ。

    Raises:
        なし。
    """
    content = spec_doc.get("content", {})
    return {
        key: len(content[key].get("scenarios", []))
        for key in _SCENARIO_BLOCK_KEYS
        if content.get(key) and content[key].get("scenarios")
    }


def docstring_lines(docstring: str) -> list[str]:
    """文書コメントを、前後の空白を落とした非空行の並びにする。

    Args:
        docstring: テストの文書コメントの本文。

    Returns:
        前後の空白を落とした非空行の並び。

    Raises:
        なし。
    """
    return [ln.strip() for ln in docstring.splitlines() if ln.strip()]


def contains_subsequence(haystack: list[str], needle: list[str]) -> bool:
    """needle が haystack の中に連続した部分列として（順序通り）出現するか。

    Args:
        haystack: 探される側の行の並び。
        needle: 探す側の行の並び。

    Returns:
        連続した部分列として現れれば True。needle が空なら常に True。

    Raises:
        なし。
    """
    if not needle:
        return True
    n = len(needle)
    return any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))
