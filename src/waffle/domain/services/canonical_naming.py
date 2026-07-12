"""canonical_naming — PascalCase/camelCaseの識別子から、対応する実装側の
snake_case識別子を導出する純粋なドメインサービス。
check_usecase_class_drift.py（operationName→モジュール名）・
check_aggregate_class_drift.py（属性名→dataclassフィールド名）が、宣言と
実装の対応関係を機械的に検証するために使う（coding-standardの命名規約の
コード側実装）。
"""
from __future__ import annotations

import re

_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def to_snake_case(name: str) -> str:
    """'CheckScenarioDrift' -> 'check_scenario_drift'、'schemaId' ->
    'schema_id' のようにPascalCase/camelCaseをsnake_caseへ変換する。"""
    return _BOUNDARY.sub("_", name).lower()


def operation_name_to_module_name(operation_name: str) -> str:
    """'CheckScenarioDrift' -> 'check_scenario_drift' のようにPascalCaseを
    snake_caseへ変換する。"""
    return to_snake_case(operation_name)
