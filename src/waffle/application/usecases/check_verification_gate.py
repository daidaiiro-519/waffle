"""check verification gate — 実装完了→検証フェーズへ進んでよいかを機械的に判定する
application use case。

既存のCheckScenarioDrift（spec⇄テストの対応関係の検知）をコンポジションで内部利用し、
テスト実行結果（testResultsPath、特定テストランナー非依存の抽象形式）と組み合わせて
ready/blocked/needs_humanを優先順位（missing_in_tests > orphaned/mismatch > failed > ready）
で判定する。テスト自体は実行しない（実行結果は既に生成済みのものを読むのみ）。
"""
from __future__ import annotations

import json

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.usecases.check_scenario_drift import CheckScenarioDrift
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class CheckVerificationGate:
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents
        self._scenario_drift = CheckScenarioDrift(documents)

    def run(self, spec_path: str, test_file_path: str, test_results_path: str) -> Result[dict]:
        drift_result = self._scenario_drift.run(spec_path, test_file_path)
        if isinstance(drift_result, Err):
            return drift_result
        drift = drift_result.value

        if drift["missing_in_tests"]:
            reasons = [f"missing_in_tests: {name}" for name in drift["missing_in_tests"]]
            return Ok({"status": "blocked", "reasons": reasons})

        if drift["orphaned_in_tests"] or drift["gherkin_mismatches"]:
            reasons = [f"orphaned_in_tests: {n}" for n in drift["orphaned_in_tests"]]
            reasons += [f"gherkin_mismatches: {n}" for n in drift["gherkin_mismatches"]]
            return Ok({"status": "needs_human", "reasons": reasons})

        if not is_confined(test_results_path):
            return _err("INVALID_TEST_RESULTS", f"パストラバーサルは許可されません: {test_results_path}")
        try:
            results = self._documents.load(test_results_path)
        except FileNotFoundError:
            return _err("INVALID_TEST_RESULTS", f"ファイルが見つかりません: {test_results_path}")
        except json.JSONDecodeError:
            return _err("INVALID_TEST_RESULTS", f"JSON として解釈できません: {test_results_path}")

        failed = set(results.get("failed", [])) if isinstance(results, dict) else set()
        relevant_failed = sorted(failed & set(drift["matched"]))
        if relevant_failed:
            reasons = [f"failed: {name}" for name in relevant_failed]
            return Ok({"status": "blocked", "reasons": reasons})

        return Ok({"status": "ready", "reasons": []})
