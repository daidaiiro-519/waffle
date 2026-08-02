"""check scenario drift — spec の TestScenarios と、対応するネイティブテストの
文書コメントを突き合わせる application use case。

突き合わせのキーは、テストの文書コメントに置かれた宣言行
「Scenario: {シナリオ名}」。テストの名前は突き合わせに使わない。

呼び方は2系統ある。1組だけ検査する呼び方（その場の検査。書き込み起点の
Hookが使う）と、置き場所を渡して全体を走査する呼び方（一通り作り終えた
ときの品質確認）。書き込みのたびに全体を走査すると重いため、両方を残す。

実行/意味理解はしない（構文解析のみ）。検出した差分の中身の妥当性評価はAIが担う。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.test_function_extractor import (
    TestFunctionExtractor,
    UnsupportedLanguage,
)
from waffle.application.services.document_loading import load_document
from waffle.domain.services.scenario_drift import (
    contains_subsequence,
    declaration_of,
    docstring_lines,
    expected_test_dir,
    relevant_scenario_block_keys,
    scenario_blocks,
    scenario_declarations,
    spec_internal_mismatches,
)
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result

# ファイルの拡張子から対象言語を決める
_LANGUAGE_BY_SUFFIX = {
    "py": "python",
    "java": "java",
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
}


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _language_of(path: str) -> str | None:
    return _LANGUAGE_BY_SUFFIX.get(path.rsplit(".", 1)[-1].lower())


class CheckScenarioDrift:
    def __init__(self, documents: DocumentRepository, extractor: TestFunctionExtractor) -> None:
        self._documents = documents
        self._extractor = extractor

    def run(
        self,
        spec_path: str | None = None,
        test_file_path: str | None = None,
        documents_root: str | None = None,
        tests_root: str | None = None,
        binding: dict | None = None,
    ) -> Result[dict]:
        binding = binding or {}
        pair = spec_path is not None and test_file_path is not None
        sweep = documents_root is not None and tests_root is not None

        if pair == sweep:
            return _err(
                "MISSING_PARAM",
                "1組だけ検査する指定（specPath と testPath）か、"
                "全体を検査する指定（documentsRoot と testsRoot）の"
                "どちらか一方を与えてください。",
            )

        if pair:
            return self._check_pair(spec_path, test_file_path, binding)
        return self._sweep(documents_root, tests_root, binding)

    # ── 1組だけ検査する ─────────────────────────────────

    def _check_pair(self, spec_path: str, test_file_path: str, binding: dict) -> Result[dict]:
        spec_loaded = load_document(self._documents, spec_path)
        if isinstance(spec_loaded, Err):
            return spec_loaded

        tests_loaded = self._read_tests(test_file_path)
        if isinstance(tests_loaded, Err):
            return tests_loaded

        return Ok(self._compare(spec_loaded.value, tests_loaded.value,
                                relevant_scenario_block_keys(test_file_path, binding)))

    def _read_tests(self, test_file_path: str) -> Result[list[dict]]:
        if not is_confined(test_file_path):
            return _err("INVALID_PATH", f"パストラバーサルは許可されません: {test_file_path}")

        language = _language_of(test_file_path)
        if language is None:
            return _err("UNSUPPORTED_LANGUAGE",
                        f"文書コメントの取り出しに対応していない言語です: {test_file_path}")
        try:
            source = self._documents.read_text(test_file_path)
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ファイルが見つかりません: {test_file_path}")

        try:
            return Ok(self._extractor.test_functions(source, language))
        except UnsupportedLanguage:
            return _err("UNSUPPORTED_LANGUAGE",
                        f"文書コメントの取り出しに対応していない言語です: {language}")
        except SyntaxError:
            return _err("INVALID_SOURCE", f"構文解析できません: {test_file_path}")

    def _compare(self, spec_doc: dict, tests: list[dict],
                 block_keys: tuple[str, ...]) -> dict:
        declared = scenario_declarations(spec_doc, block_keys)

        claimed: dict[str, list[str]] = {}
        orphaned: list[str] = []
        for test in tests:
            declaration = declaration_of(test["doc"])
            if declaration is None or declaration not in declared:
                orphaned.append(test["name"])
                continue
            claimed.setdefault(declaration, []).append(test["name"])

        matched = []
        mismatches = []
        for declaration, names in claimed.items():
            if len(names) > 1:
                continue
            scenario = declared[declaration]
            matched.append({"scenarioName": scenario["name"], "testName": names[0]})
            doc = next(t["doc"] for t in tests if t["name"] == names[0])
            if not contains_subsequence(docstring_lines(doc), scenario["gherkin"]):
                mismatches.append(scenario["name"])

        duplicates = sorted(d for d, names in claimed.items() if len(names) > 1)
        # 重複した宣言行は、どちらへも割り当てない。割り当て順という本質と
        # 無関係な要因で検知結果が変わるのを避ける
        for declaration in duplicates:
            orphaned.extend(claimed[declaration])

        return {
            # 重複して名乗られたシナリオは未実装ではない。実装が2件あって
            # どちらか決まらないだけなので、duplicate_declarations で報告する
            "missing_in_tests": sorted(
                declared[d]["name"] for d in declared if d not in claimed),
            "orphaned_in_tests": sorted(orphaned),
            "matched": sorted(matched, key=lambda m: m["scenarioName"]),
            "gherkin_mismatches": sorted(mismatches),
            "duplicate_declarations": duplicates,
            "spec_declaration_mismatches": sorted(spec_internal_mismatches(spec_doc, block_keys)),
        }

    # ── 全体を走査する ──────────────────────────────────

    def _sweep(self, documents_root: str, tests_root: str, binding: dict) -> Result[dict]:
        if not is_confined(documents_root) or not is_confined(tests_root):
            return _err("INVALID_PATH", "パストラバーサルは許可されません")
        try:
            spec_paths = sorted(self._documents.list_files(documents_root, "**/*.json"))
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {documents_root}")

        missing_test_file: list[dict] = []
        results: list[dict] = []
        for spec_path in spec_paths:
            loaded = load_document(self._documents, spec_path)
            if isinstance(loaded, Err):
                continue
            spec_doc = loaded.value
            document_id = spec_doc.get("documentId", "")

            for block, count in scenario_blocks(spec_doc).items():
                placement = expected_test_dir(binding, block)
                if placement is None:
                    continue
                stem = ("test_" + document_id.replace("-", "_")
                        + binding.get("fileNameSuffix", ""))
                # 配置は placementByTarget が宣言した位置をそのまま使う。
                # tests_root は全体走査を選ぶ指定であって、パスの前置ではない。
                expected = f"{placement}/{stem}"
                try:
                    self._documents.read_text(expected)
                except FileNotFoundError:
                    missing_test_file.append({
                        "documentId": document_id, "block": block,
                        "expectedPath": expected, "scenarioCount": count,
                    })
                    continue

                checked = self._check_pair(spec_path, expected, binding)
                if isinstance(checked, Err):
                    continue
                results.append({"documentId": document_id, "specPath": spec_path,
                                "testPath": expected, **checked.value})

        # 同じテストファイルを指すブロックが複数あっても、判定は1件にまとめる
        seen: set[str] = set()
        unique_results = []
        for entry in results:
            if entry["testPath"] in seen:
                continue
            seen.add(entry["testPath"])
            unique_results.append(entry)

        return Ok({"missing_test_file": missing_test_file, "results": unique_results})
