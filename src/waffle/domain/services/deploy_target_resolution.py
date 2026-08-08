"""配置先の解決と所有権の判定を行う純ロジック。

配置先は3つの軸で決まる。どのツール向けか（tool）、その文書が実体か雛形か
（documentRole）、同じdocumentType内のどの種別か（discriminator）である。
雛形が配置されないのは「雛形なら飛ばす」という条件分岐の結果ではなく、
解決キーに対応する宣言が toolMappings に存在しないためである（配置先が
定義できないという構造上の帰結）。

所有権は「1つの配置先は、ちょうど1つのDocumentに所有される」という不変条件を
守るための判定。配置先が指す実体がcanonicalテンプレートに逆マッチすれば、
そのcanonicalを持つDocumentがその配置先の所有者である。

ファイルI/Oは一切行わない。config・schemaは読み込み済みのdictとして受け取り、
実体パスの解決（symlinkの追跡）は呼び出し側がアダプター経由で済ませて渡す。
"""
from __future__ import annotations

from waffle.domain.services import path_template

DEFAULT_DOCUMENT_ROLE = "instance"

UNRESOLVED_PATH_VAR = "UNRESOLVED_PATH_VAR"


def select_mappings(
    tool_mappings: dict,
    document_type: str | None,
    document_role: str,
    spec_kind: str | None,
) -> list[dict]:
    """toolMappingsから、解決キーに対応するマッピングを集める。

    解決キーは (tool, documentRole, documentType, discriminator)。どの段でも
    キーが見つからなければ、その分岐は配置先を持たない。同じdocumentTypeに
    複数のマッピング（例: skillRefs用・agentRefs用）を並べてもよい。

    Args:
        tool_mappings: config.jsonのtoolMappings（ツール名→役割→documentType→宣言）。
        document_type: 対象DocumentのdocumentType。
        document_role: 対象DocumentのdocumentRole（instance / template）。
        spec_kind: 対象Documentのdiscriminator値。持たなければNone。

    Returns:
        解決キーに対応するマッピングの一覧。1つも無ければ空配列。
    """
    if not document_type:
        return []
    found: list[dict] = []
    for tool_config in tool_mappings.values():
        mapping = tool_config.get(document_role, {}).get(document_type)
        if isinstance(mapping, dict) and not mapping.get("pathTemplate"):
            # discriminatorごとの入れ子宣言（kind→{pathTemplate, mode}）
            mapping = mapping.get(spec_kind) if spec_kind else None
        if not mapping:
            continue
        found.extend(mapping if isinstance(mapping, list) else [mapping])
    return found


def resolve_targets(mapping: dict, path_vars: dict) -> tuple[list[tuple[str, str]], list[dict]]:
    """1つのマッピングから配置先を解決する。

    pathTemplateが参照する配列値のpathVar（例: skillRefs）だけを見て要素ごとに
    fan-outする。同じdocumentTypeに複数マッピングが並んでいても、各マッピングは
    自分のpathTemplateが参照する配列変数だけを見るため互いに干渉しない。

    Args:
        mapping: pathTemplate（必須）とmode（省略時はrender）を持つ宣言。
        path_vars: パステンプレートへ当てはめる変数。

    Returns:
        (解決できた配置先とモードの組の一覧, 解決できなかった宣言と理由の一覧)。
    """
    template = mapping["pathTemplate"]
    mode = mapping.get("mode", "render")
    array_vars = {
        k: v for k, v in path_vars.items() if isinstance(v, list) and f"{{{k}}}" in template
    }
    targets: list[tuple[str, str]] = []
    skipped: list[dict] = []
    if array_vars:
        var_name, values = next(iter(array_vars.items()))
        for value in values:
            scalar_vars = {**path_vars, var_name: value}
            try:
                targets.append((path_template.resolve(template, **scalar_vars), mode))
            except KeyError:
                skipped.append({"path": template, "reason": UNRESOLVED_PATH_VAR})
    else:
        try:
            targets.append((path_template.resolve(template, **path_vars), mode))
        except KeyError:
            skipped.append({"path": template, "reason": UNRESOLVED_PATH_VAR})
    return targets, skipped


def canonical_templates(schemas: list[dict]) -> list[tuple[str, str]]:
    """schemaの集合から、canonicalパスのテンプレートとdocumentTypeの組を取り出す。

    x-render-target.path は、フラットな文字列としても、discriminatorごとの
    辞書としても書けるため、どちらの形からも文字列だけを集める。

    Args:
        schemas: 対象のschema一覧。

    Returns:
        (canonicalパスのテンプレート, そのschemaのdocumentType) の一覧（重複は除く）。
    """
    pairs: list[tuple[str, str]] = []
    for schema in schemas:
        document_type = (schema.get("properties", {}).get("documentType") or {}).get("const", "")
        path = (schema.get("x-render-target") or {}).get("path")
        candidates = list(path.values()) if isinstance(path, dict) else [path]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate:
                pair = (candidate, document_type)
                if pair not in pairs:
                    pairs.append(pair)
    return pairs


def find_projection(templates: list[tuple[str, str]], real_path: str) -> tuple[str, str] | None:
    """実体パスがどのDocumentのcanonical成果物かを判定する。

    Args:
        templates: (canonicalパスのテンプレート, documentType) の一覧。
        real_path: symlink解決済みの実体パス。

    Returns:
        (documentType, documentId)。どのテンプレートにも当てはまらなければ None
        （＝canonical成果物ではない＝まだ誰のものでもない）。
    """
    for template, document_type in templates:
        match = path_template.reverse_parse(template, real_path)
        if match and "documentId" in match:
            return document_type, match["documentId"]
    return None
