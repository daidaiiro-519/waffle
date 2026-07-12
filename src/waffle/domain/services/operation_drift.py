"""operation_drift — usecase specのacceptanceScenariosが宣言するoperation名と、
対応する実装が実際に持つoperation分岐の文字列が一致しているかを機械的に突き合わせる
純粋なドメインサービス。「モデルはコードに宿る」原則をoperationレベルにも適用する。
"""
from __future__ import annotations

import re

_OPERATION_COMPARISON = re.compile(r'operation\s*==\s*"([a-zA-Z_]+)"')


def declared_operations(doc: dict) -> set[str]:
    scenarios = doc.get("content", {}).get("acceptanceScenarios", {}).get("scenarios", [])
    return {s["operation"] for s in scenarios if s.get("operation")}


def implemented_operations(source: str) -> set[str]:
    return set(_OPERATION_COMPARISON.findall(source))
