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

def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _language_of(path: str, binding: dict) -> str | None:
    """拡張子から対象言語を決める。対応は tech-stack の宣言が持つ。

    どの拡張子がどの言語かはスタックが宣言する（runtime.languages[].extensions）。
    コード側に表を持つと、言語を足したときに宣言とコードの両方を直すことになる。
    """
    suffix = path.rsplit(".", 1)[-1].lower()
    return binding.get("languageBySuffix", {}).get(suffix)


class CheckScenarioDrift:
    """シナリオの宣言と、テストの文書コメントの食い違いを見つける。"""
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
        """シナリオの宣言と、テストの文書コメントの食い違いを見つける。

        Args:
            spec_path: 対象とする仕様の置き場所。
            test_file_path: その仕様に対応するテストの置き場所。
            documents_root: 突き合わせの対象とする仕様の置き場所。
            tests_root: テストの配置ルート。全体を突き合わせるときに使う。
            binding: シナリオの種別とテストの配置の対応を宣言している規約。

        Returns:
            その操作の結果を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        binding = binding or {}
        pair = spec_path is not None and test_file_path is not None
        sweep = documents_root is not None and tests_root is not None
        one_sided = (spec_path is None) != (test_file_path is None) and documents_root is not None

        if pair and sweep:
            return _err(
                "MISSING_PARAM",
                "1組の指定（specPath と testPath）と全体の指定（documentsRoot と "
                "testsRoot）は同時に渡せません。どちらを意図したか決まらないため。",
            )
        if pair:
            return self._check_pair(spec_path, test_file_path, binding)
        if one_sided:
            # 片側だけ分かっているときは、もう片方を規約の宣言から引く。
            # 呼び出し側に推測させると、呼び出し側ごとに配置の写しが増える
            return self._sweep(documents_root, tests_root, binding,
                               only_spec=spec_path, only_test=test_file_path)
        if sweep:
            return self._sweep(documents_root, tests_root, binding)
        return _err(
            "MISSING_PARAM",
            "1組だけ検査する指定（specPath と testPath）か、"
            "片側だけの指定（specPath または testPath と documentsRoot）か、"
            "全体を検査する指定（documentsRoot と testsRoot）の"
            "いずれかを与えてください。",
        )

    # ── 1組だけ検査する ─────────────────────────────────

    def _check_pair(self, spec_path: str, test_file_path: str, binding: dict) -> Result[dict]:
        spec_loaded = load_document(self._documents, spec_path)
        if isinstance(spec_loaded, Err):
            return spec_loaded

        tests_loaded = self._read_tests(test_file_path, binding)
        if isinstance(tests_loaded, Err):
            return tests_loaded

        return Ok(self._compare(spec_loaded.value, tests_loaded.value,
                                relevant_scenario_block_keys(test_file_path, binding)))

    def _read_tests(self, test_file_path: str, binding: dict) -> Result[list[dict]]:
        if not is_confined(test_file_path):
            return _err("INVALID_PATH", f"パストラバーサルは許可されません: {test_file_path}")

        language = _language_of(test_file_path, binding)
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

    def _sweep(self, documents_root: str, tests_root: str | None, binding: dict,
               only_spec: str | None = None, only_test: str | None = None) -> Result[dict]:
        for path in (documents_root, tests_root, only_spec, only_test):
            if path is not None and not is_confined(path):
                return _err("INVALID_PATH", "パストラバーサルは許可されません")
        try:
            spec_paths = sorted(self._documents.list_files(documents_root, "**/*.json"))
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {documents_root}")

        if only_spec is not None:
            spec_paths = [p for p in spec_paths if p == only_spec or p.endswith(only_spec)]

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
                if only_test is not None and expected != only_test:
                    continue
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

        if only_test is not None and not unique_results and not missing_test_file:
            # どのspecの宣言もこのテストを指していない。黙って通すと、対応の
            # 取れていないテストが「綺麗だった」ことと同じ見た目になる
            missing_test_file.append({
                "documentId": None, "block": None,
                "expectedPath": only_test, "scenarioCount": 0,
            })

        return Ok({"missing_test_file": missing_test_file, "results": unique_results})
