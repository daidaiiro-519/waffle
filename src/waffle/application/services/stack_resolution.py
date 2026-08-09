"""stack_resolution — architectureRef から、同じスタックの他の規約文書を引く。

CodingSchema は1スタック＝複数の codingKind document を stack フィールドで
束ねる。検査がファイル名を組み立てるための表記規則は coding-standard が持ち、
配置は architecture が持つため、片方の参照からもう片方を辿る必要がある。

この引き当てをコード側の固定表にすると、スタックが増えるたびに写しが増える。
stack フィールドという既にある宣言を辿ることで、対応を持たずに済ませる。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.shared.result import Err, Ok, Result

__all__ = ["resolve_naming", "resolve_scenario_binding", "resolve_layer_graph"]

CODING_ROOT = ".waffle/documents/coding"


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _load_coding_documents(documents: DocumentRepository) -> list[dict]:
    try:
        paths = documents.list_files(CODING_ROOT, "**/*." + "json")
    except FileNotFoundError:
        return []
    loaded = []
    for path in paths:
        try:
            loaded.append(documents.load(path))
        except FileNotFoundError:
            continue
    return loaded


def resolve_naming(documents: DocumentRepository, architecture_ref: str) -> Result[dict]:
    """architectureRef が属するスタックの coding-standard から naming ブロックを返す。

    Args:
        documents: 規約文書を読むための DocumentRepository。
        architecture_ref: architecture document の documentId。

    Returns:
        naming ブロックを持つ Ok、または失敗を表す Err。
        失敗のコードは ARCHITECTURE_REF_NOT_FOUND / CODING_STANDARD_NOT_FOUND。
    """
    coding_documents = _load_coding_documents(documents)
    architecture = next(
        (d for d in coding_documents if d.get("documentId") == architecture_ref), None)
    if architecture is None:
        return _err("ARCHITECTURE_REF_NOT_FOUND",
                    f"architecture document が見つかりません: {architecture_ref}")
    stack = architecture.get("stack")
    standard = next(
        (d for d in coding_documents
         if d.get("codingKind") == "coding-standard" and d.get("stack") == stack), None)
    if standard is None:
        return _err("CODING_STANDARD_NOT_FOUND",
                    f"stack={stack} の coding-standard が見つかりません"
                    f"（{architecture_ref} と同じスタックの命名規約が必要）")
    return Ok(standard.get("content", {}).get("naming", {}))


def _find_by_kind(coding_documents: list[dict], kind: str, stack: str) -> dict | None:
    return next((d for d in coding_documents
                 if d.get("codingKind") == kind and d.get("stack") == stack), None)


def resolve_scenario_binding(documents: DocumentRepository, architecture_ref: str) -> Result[dict]:
    """architectureRef が属するスタックの test-standard から、シナリオ照合の宣言を返す。

    シナリオ種別と（層・テスト種別）の対応は scenarioBinding が持ち、その
    （層・テスト種別）が実際にどのパスへ置かれるかは placementByTarget が持つ。
    2つを辿って「シナリオ種別 → 配置パス」を組み立てる。片方だけを写した表を
    コードへ置くと、置き方を変えたときに追従しない。

    Args:
        documents: 規約文書を読むための DocumentRepository。
        architecture_ref: architecture document の documentId。

    Returns:
        declarationLine / blockPlacement / placements（(層, 種別) → パス）を
        持つ Ok、または失敗を表す Err。
        失敗のコードは ARCHITECTURE_REF_NOT_FOUND / TEST_STANDARD_NOT_FOUND。
    """
    coding_documents = _load_coding_documents(documents)
    architecture = next(
        (d for d in coding_documents if d.get("documentId") == architecture_ref), None)
    if architecture is None:
        return _err("ARCHITECTURE_REF_NOT_FOUND",
                    f"architecture document が見つかりません: {architecture_ref}")
    stack = architecture.get("stack")
    standard = _find_by_kind(coding_documents, "test-standard", stack)
    if standard is None:
        return _err("TEST_STANDARD_NOT_FOUND",
                    f"stack={stack} の test-standard が見つかりません"
                    f"（{architecture_ref} と同じスタックのテスト規約が必要）")
    content = standard.get("content", {})
    binding = content.get("scenarioBinding", {})
    placements = {}
    for row in content.get("placementByTarget", {}).get("items", []):
        path = row.get("path")
        if path:
            placements[(row.get("layer"), row.get("testType"))] = path.rstrip("/")
    standard_naming = _find_by_kind(coding_documents, "coding-standard", stack) or {}
    tech_stack = _find_by_kind(coding_documents, "tech-stack", stack) or {}
    language_by_suffix = {
        suffix.lstrip("."): entry["language"]
        for entry in (tech_stack.get("content", {})
                      .get("runtime", {}).get("languages", []))
        for suffix in entry.get("extensions", [])
    }
    return Ok({
        "languageBySuffix": language_by_suffix,
        "declarationLine": binding.get("declarationLine", ""),
        "blockPlacement": binding.get("blockPlacement", []),
        "placements": placements,
        # テストファイルの名前の作り方は test-standard が持つ。実装ファイルの
        # 拡張子（coding-standard の naming）を流用しない——テストファイルの
        # 末尾が実装ファイルの拡張子と同じとは限らない
        "testFileNaming": content.get("testFileNaming", {}),
    })


SPECS_ROOT = ".waffle/documents/specs"


def resolve_covered_documents_root(documents: DocumentRepository,
                                   architecture_ref: str) -> Result[str]:
    """architectureRef が実装を受け持つコンテキストの仕様の置き場所を返す。

    検査は実装側（architectureRef が決める配置）と仕様側（この関数が決める
    範囲）を対で見る必要がある。対応を呼び出し側が知っていると、片方を渡し
    忘れた瞬間に別のコンテキストの仕様まで巻き込んで誤報を出す。

    Args:
        documents: 規約文書を読むための DocumentRepository。
        architecture_ref: architecture document の documentId。

    Returns:
        仕様の置き場所を持つ Ok、または失敗を表す Err。
        失敗のコードは ARCHITECTURE_REF_NOT_FOUND / COVERED_CONTEXTS_NOT_DECLARED。
        受け持つコンテキストが複数ある場合は、共通の親である仕様ルートを返す。
    """
    coding_documents = _load_coding_documents(documents)
    architecture = next(
        (d for d in coding_documents if d.get("documentId") == architecture_ref), None)
    if architecture is None:
        return _err("ARCHITECTURE_REF_NOT_FOUND",
                    f"architecture document が見つかりません: {architecture_ref}")
    contexts = (architecture.get("content", {})
                .get("coveredContexts", {}).get("items", []))
    if not contexts:
        return _err("COVERED_CONTEXTS_NOT_DECLARED",
                    f"{architecture_ref} が実装を受け持つコンテキストを宣言していません"
                    "（coveredContexts）。検査の仕様側の範囲が決まりません")
    if len(contexts) == 1:
        return Ok(f"{SPECS_ROOT}/{contexts[0]}")
    return Ok(SPECS_ROOT)


def resolve_layer_graph(documents: DocumentRepository, architecture_ref: str) -> Result[dict]:
    """architectureRef から、層の突き合わせに要る宣言を1つにまとめて返す。

    層・置き場所・依存してよい先は architecture が、走査対象の拡張子は同じスタックの
    tech-stack が宣言する。検査ごとにこの引き当てを書き直すと、宣言の読み方が
    検査ごとに食い違う余地が生まれる。

    Args:
        documents: 規約文書を読むための DocumentRepository。
        architecture_ref: 参照する architecture document の documentId。

    Returns:
        srcRoot / layers / compositionRootPaths / languageBySuffix を持つ Ok、
        または失敗を表す Err。失敗のコードは ARCHITECTURE_REF_NOT_FOUND /
        ARCHITECTURE_REF_UNRESOLVED のいずれか。
    """
    from waffle.domain.services import path_template
    from waffle.domain.services.concept_source_root import package_name_from_reference

    coding_documents = _load_coding_documents(documents)
    architecture = next((d for d in coding_documents
                         if d.get("documentId") == architecture_ref), None)
    if architecture is None:
        return _err("ARCHITECTURE_REF_NOT_FOUND",
                    f"architecture document が見つかりません: {architecture_ref}")

    content = architecture.get("content", {})
    layout = content.get("layout", {})
    layers = content.get("layers", {}).get("items", [])
    source_root = layout.get("sourceRoot")
    if not source_root or not layers:
        return _err("ARCHITECTURE_REF_UNRESOLVED",
                    f"{architecture_ref} が layout.sourceRoot または layers を宣言していません")

    package = package_name_from_reference(architecture_ref, "architecture") or ""
    src_root = path_template.resolve(source_root, package=package)

    # 走査対象の拡張子は tech-stack が宣言する。検査コードに拡張子の表を持たない
    stack = architecture.get("stack")
    tech_stack = _find_by_kind(coding_documents, "tech-stack", stack) or {}
    language_by_suffix = {}
    for language in tech_stack.get("content", {}).get("runtime", {}).get("languages", []):
        for extension in language.get("extensions", []):
            language_by_suffix[extension.lstrip(".").lower()] = language.get("language")

    return Ok({
        "srcRoot": src_root,
        "layers": layers,
        "compositionRootPaths": layout.get("compositionRootPaths", []),
        "languageBySuffix": language_by_suffix,
    })
