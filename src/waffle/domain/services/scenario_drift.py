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

_SCENARIO_BLOCK_KEYS = (
    "acceptanceScenarios",
    "guaranteeScenarios",
    "invariantScenarios",
    "domainServiceScenarios",
)

_DECLARATION = re.compile(r"^Scenario(?:\s+Outline)?:\s*(?P<name>.+?)\s*$")

# シナリオブロックの種別と、対応するテストの配置。
# scenarioBinding（test-standard）が定める対応をコード側で表したもの
BLOCK_PLACEMENT = {
    "acceptanceScenarios": "acceptance",
    "guaranteeScenarios": "integration",
    "invariantScenarios": "unit",
    "domainServiceScenarios": "unit",
}


def declaration_line(scenario_name: str) -> str:
    """シナリオの名前から、突き合わせのキーとなる宣言行を組み立てる。

    名前を唯一の正とし、gherkin本文中の見出し行は信用しない。名前が二箇所に
    存在すると、片方だけ直されたときにどちらが正しいか機械では決まらない。
    """
    return f"Scenario: {scenario_name}"


def declaration_of(doc_text: str) -> str | None:
    """文書コメントから宣言行を取り出す。無ければ None。

    先頭行である必要はない。自分の言葉での説明を前に書いてよい。
    飾り（三重引用符・ブロックコメントの記号等）は adapter が落とし済み。
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
    """
    return [line.strip() for line in gherkin.strip().splitlines() if line.strip()]


def relevant_scenario_block_keys(test_file_path: str) -> tuple[str, ...]:
    """test_file_pathのパスパターンから、scenarioBinding（test-standard）が定める
    配置ルールに沿って対象シナリオブロックを機械的に絞り込む。いずれのパターンにも
    一致しないパスは、絞り込まず全種を対象にする（ケースバイケース判定はしない）。"""
    if "tests/acceptance/" in test_file_path:
        return ("acceptanceScenarios",)
    if "tests/integration/" in test_file_path:
        return ("guaranteeScenarios",)
    if "tests/unit/" in test_file_path:
        return ("invariantScenarios", "domainServiceScenarios")
    return _SCENARIO_BLOCK_KEYS


def scenario_declarations(
    spec_doc: dict, block_keys: tuple[str, ...] = _SCENARIO_BLOCK_KEYS
) -> dict[str, dict]:
    """spec document から 宣言行 -> {name, gherkin} のマップを作る。"""
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
    """
    content = spec_doc.get("content", {})
    mismatched: list[str] = []
    for block_key in block_keys:
        block = content.get(block_key)
        if not block:
            continue
        for scenario in block.get("scenarios", []):
            lines = gherkin_lines(scenario.get("gherkin", ""))
            heading = lines[0] if lines else ""
            if heading != declaration_line(scenario["name"]):
                mismatched.append(scenario["name"])
    return mismatched


def scenario_blocks(spec_doc: dict) -> dict[str, int]:
    """この document が宣言しているシナリオブロックと、その件数を返す。"""
    content = spec_doc.get("content", {})
    return {
        key: len(content[key].get("scenarios", []))
        for key in _SCENARIO_BLOCK_KEYS
        if content.get(key) and content[key].get("scenarios")
    }


def docstring_lines(docstring: str) -> list[str]:
    return [ln.strip() for ln in docstring.splitlines() if ln.strip()]


def contains_subsequence(haystack: list[str], needle: list[str]) -> bool:
    """needle が haystack の中に連続した部分列として（順序通り）出現するか。"""
    if not needle:
        return True
    n = len(needle)
    return any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))
