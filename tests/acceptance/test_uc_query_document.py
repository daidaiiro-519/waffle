"""uc-query-document の受け入れテスト（ネイティブpytest）。"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.query_document import QueryDocument
from waffle.shared.result import Err, Ok

_TARGET = ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json"


def _engine() -> QueryDocument:
    return QueryDocument(FsDocumentRepository(), PackageSchemaRepository())


def test_ブロックを丸ごと取得する():
    """
    Given query システム と対象 Document
    When operation get_block を blockKey interface で実行する
    Then value は対象ブロックであり、prompt に読み方の指針が付く
    """
    result = _engine().run("get_block", _TARGET, {"blockKey": "title"})
    assert isinstance(result, Ok), result
    assert result.value["prompt"] is not None


def test_解釈指針を宣言したブロックはcautionを持つ():
    """
    Given x-prompt-interpret（値の解釈指針）を宣言したブロック
    When operation get_block を実行する
    Then valueの読み方の指針とは別に、誤読を防ぐcautionが返る
    """
    result = _engine().run("get_block", _TARGET, {"blockKey": "acceptanceCriteria"})
    assert isinstance(result, Ok), result
    assert result.value.get("caution")


def test_解釈指針を宣言していないブロックはcautionを持たない():
    """
    Given x-prompt-interpretを宣言していないブロック
    When operation get_block を実行する
    Then cautionキー自体が省略される（値が無いフィールドは持たせない）
    """
    result = _engine().run("get_block", _TARGET, {"blockKey": "title"})
    assert isinstance(result, Ok), result
    assert "caution" not in result.value


def test_条件に一致する配列要素だけを絞り込む():
    """
    Given query システム と対象 Document
    When operation filter_items で required=true を指定する
    Then value には required な要素だけが含まれる
    """
    result = _engine().run(
        "filter_items", _TARGET,
        {"blockKey": "acceptanceScenarios", "arrayField": "scenarios", "key": "category", "value": "異常系"},
    )
    assert isinstance(result, Ok), result
    assert all(item["category"] == "異常系" for item in result.value["value"])


def test_一致が無くても正常系で空配列を返す():
    """
    When 一致しないフィルタ条件で filter_items を実行する
    Then value は空配列で、エラーにはならない
    """
    result = _engine().run(
        "filter_items", _TARGET,
        {"blockKey": "acceptanceScenarios", "arrayField": "scenarios", "key": "category", "value": "存在しないカテゴリ"},
    )
    assert isinstance(result, Ok), result
    assert result.value["value"] == []


def test_未知の_operation_はエラーを返す():
    """
    When 未知の operation を実行する
    Then INVALID_OPERATION エラーが返る
    """
    result = _engine().run("unknown_op", _TARGET, {})
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_OPERATION"



def test_必須パラメータの欠落はエラーを返す():
    """
    When blockKey を指定せずに get_block を実行する
    Then MISSING_PARAM エラーが返る
    """
    result = _engine().run("get_block", _TARGET, {})
    assert isinstance(result, Err), result
    assert result.details[0] == "MISSING_PARAM"


def test_存在しないblockKeyはエラーを返す():
    """
    When 存在しない blockKey を指定して get_block を実行する
    Then NOT_FOUND エラーが返る
    """
    result = _engine().run("get_block", _TARGET, {"blockKey": "no_such_block"})
    assert isinstance(result, Err), result
    assert result.details[0] == "NOT_FOUND"


def test_不正な正規表現はエラーを返す():
    """
    When 不正な正規表現で filter_pattern を実行する
    Then INVALID_PATTERN エラーが返る
    """
    result = _engine().run(
        "filter_pattern", _TARGET,
        {"blockKey": "acceptanceScenarios", "arrayField": "scenarios", "field": "name", "pattern": "("},
    )
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATTERN"


def test_scanは生テキストを返す():
    """
    Given query システム と対象 Document
    When operation scan を実行する
    Then value は生テキストであり、prompt にはこの値の読み方の指針が入る
    """
    result = _engine().run("scan", _TARGET)
    assert isinstance(result, Ok), result
    assert result.value["prompt"]
    assert "documentId" in result.value["value"]


def test_get_metaはメタ情報を返す():
    """
    Given query システム と対象 Document
    When operation get_meta を実行する
    Then value にはdocumentId等のメタフィールドのみが含まれ、prompt にはこの値の読み方の指針が入る
    """
    result = _engine().run("get_meta", _TARGET)
    assert isinstance(result, Ok), result
    assert result.value["value"]["documentId"] == "uc-query-document"
    assert result.value["prompt"]


def test_index_scanはblockTypeとpromptをschemaから動的算出する():
    """
    Given query システム と対象 Document
    When operation index_scan を実行する
    Then 各blockのblockTypeとx-prompt-query由来のpromptが返り、トップレベルのpromptには各要素のpromptを参照する案内が入る
    """
    result = _engine().run("index_scan", _TARGET)
    assert isinstance(result, Ok), result
    assert result.value["value"]["mainFlow"]["blockType"] == "MainFlow"
    assert result.value["value"]["mainFlow"]["prompt"]
    assert result.value["prompt"]


def test_get_fieldはblockの1フィールドを返す():
    """
    Given query システム と対象 Document
    When operation get_field を blockKey, field で実行する
    Then value は指定フィールドの値である
    """
    result = _engine().run("get_field", _TARGET, {"blockKey": "title", "field": "title"})
    assert isinstance(result, Ok), result
    assert result.value["value"] == "Documentから必要な意味単位だけを取得する：QueryDocument"


def test_get_by_idは単一オブジェクトを返す():
    """
    Given query システム と対象 Document
    When operation get_by_id を idField, idValue で実行する
    Then 一致した単一の要素がvalueとして返る（配列ではない）
    """
    result = _engine().run(
        "get_by_id", _TARGET,
        {"blockKey": "acceptanceScenarios", "arrayField": "scenarios", "idField": "name", "idValue": "ブロックを丸ごと取得する"},
    )
    assert isinstance(result, Ok), result
    assert result.value["value"]["name"] == "ブロックを丸ごと取得する"


def test_find_allは全階層を再帰収集する():
    """
    Given query システム と対象 Document
    When operation find_all を fieldName で実行する
    Then 全階層に出現するfieldNameの値がvalueとして返り、prompt にはこの値の読み方の指針が入る
    """
    result = _engine().run("find_all", _TARGET, {"fieldName": "category"})
    assert isinstance(result, Ok), result
    assert "異常系" in result.value["value"]
    assert result.value["prompt"]


def test_get_itemsは配列フィールドをそのまま返す():
    """
    Given query システム と対象 Document
    When operation get_items を実行する
    Then value は対象の配列フィールドそのものである
    """
    result = _engine().run("get_items", _TARGET, {"blockKey": "acceptanceScenarios", "arrayField": "scenarios"})
    assert isinstance(result, Ok), result
    assert isinstance(result.value["value"], list) and len(result.value["value"]) > 0


def test_get_item_fieldは配列要素から指定フィールドだけを取り出す():
    """
    Given query システム と対象 Document
    When operation get_item_field を実行する
    Then 各要素の指定フィールドの値だけがvalueとして返る
    """
    result = _engine().run(
        "get_item_field", _TARGET,
        {"blockKey": "acceptanceScenarios", "arrayField": "scenarios", "field": "name"},
    )
    assert isinstance(result, Ok), result
    assert "ブロックを丸ごと取得する" in result.value["value"]


def test_get_items_sliceは配列の指定範囲だけを返す():
    """
    Given query システム と対象 Document
    When operation get_items_slice を実行する
    Then その範囲の要素だけがvalueとして返る
    """
    result = _engine().run(
        "get_items_slice", _TARGET,
        {"blockKey": "acceptanceScenarios", "arrayField": "scenarios", "start": 0, "end": 2},
    )
    assert isinstance(result, Ok), result
    assert len(result.value["value"]) == 2


def test_filter_existsは指定フィールドを持つ要素だけを絞り込む():
    """
    Given query システム と対象 Document
    When operation filter_exists を実行する
    Then 指定フィールドを持つ要素だけがvalueに含まれる
    """
    result = _engine().run(
        "filter_exists", _TARGET,
        {"blockKey": "acceptanceScenarios", "arrayField": "scenarios", "field": "operation"},
    )
    assert isinstance(result, Ok), result
    assert all("operation" in item for item in result.value["value"])
    assert len(result.value["value"]) > 0


def _write_custom_skill_with_children(path) -> None:
    import json

    doc = {
        "documentId": "test-query-nested",
        "schemaRef": "SkillSchema/v1",
        "skillKind": "custom",
        "content": {
            "steps": {
                "blockType": "CustomSteps",
                "title": "実行手順",
                "items": [
                    {
                        "stepId": "step-1", "title": "手順1",
                        "children": [
                            {"stepId": "step-1a", "title": "サブ手順1"},
                            {"stepId": "step-1b", "title": "サブ手順2"},
                        ],
                    },
                    {"stepId": "step-2", "title": "手順2", "children": []},
                ],
            },
        },
    }
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def test_get_nested_itemsは各要素の入れ子配列を1段展開して集約する(tmp_path):
    """
    Given query システム と、配列要素それぞれが入れ子配列を持つ対象 Document
    When operation get_nested_items を実行する
    Then 全要素の入れ子配列を1段展開して集約したものがvalueとして返る
    """
    import json

    path = tmp_path / "test-query-nested.json"
    _write_custom_skill_with_children(path)

    result = _engine().run(
        "get_nested_items", str(path),
        {"blockKey": "steps", "arrayField": "items", "nestedField": "children"},
    )
    assert isinstance(result, Ok), result
    assert [c["stepId"] for c in result.value["value"]] == ["step-1a", "step-1b"]


def test_get_childrenは識別子で特定した要素のchildren配列を返す(tmp_path):
    """
    Given query システム と、children配列を持つ要素を含む対象 Document
    When operation get_children を実行する
    Then 識別子で特定した要素のchildren配列がvalueとして返る
    """
    path = tmp_path / "test-query-nested.json"
    _write_custom_skill_with_children(path)

    result = _engine().run(
        "get_children", str(path),
        {"blockKey": "steps", "arrayField": "items", "idField": "stepId", "idValue": "step-1"},
    )
    assert isinstance(result, Ok), result
    assert [c["stepId"] for c in result.value["value"]] == ["step-1a", "step-1b"]


def test_resolve_refは参照先Documentのpathを算出する():
    """
    Given query システム と、subdomainRefフィールドを持つ対象 Document
    When operation resolve_ref を field subdomainRef, targetSchemaRef DomainSpecSchema/v5, targetDiscriminator specKind=subdomain で実行する
    Then 参照先Documentのpathがvalueとして返る（中身は取得されない）
    """
    result = _engine().run(
        "resolve_ref", _TARGET,
        {
            "field": "subdomainRef",
            "targetSchemaRef": "DomainSpecSchema/v5",
            "targetDiscriminator": {"specKind": "subdomain"},
        },
    )
    assert isinstance(result, Ok), result
    assert result.value["value"]["path"] == (
        ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/sd-document-management.json"
    )
    assert "content" not in result.value["value"]


def test_resolve_refはテンプレート変数を解決できないときエラーを返す(tmp_path):
    """
    Given 参照先テンプレートが要求する変数を持たない対象 Document
    When operation resolve_ref を実行する
    Then MISSING_TEMPLATE_VAR エラーが返る
    """
    import json

    doc = {
        "documentId": "orphan-usecase",
        "documentType": "DomainSpec",
        "schemaRef": "DomainSpecSchema/v5",
        "specKind": "usecase",
        "subdomainRef": "sd-document-management",
    }
    path = tmp_path / "orphan-usecase.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    result = _engine().run(
        "resolve_ref", str(path),
        {
            "field": "subdomainRef",
            "targetSchemaRef": "DomainSpecSchema/v5",
            "targetDiscriminator": {"specKind": "subdomain"},
        },
    )
    assert isinstance(result, Err), result
    assert result.details[0] == "MISSING_TEMPLATE_VAR"


def test_query_pathでblockKey指定時は単一ブロックの評価結果を返す():
    """
    Given query システム と対象 Document
    When operation query_path を blockKey summary, path "items[?length(@) > `0`]" で実行する
    Then value は指定ブロック内でのJMESPath評価結果であり、prompt に読み方の指針が付く
    """
    result = _engine().run(
        "query_path", _TARGET,
        {"blockKey": "acceptanceScenarios", "expression": "scenarios[?length(name) > `0`].name"},
    )
    assert isinstance(result, Ok), result
    assert result.value["documentId"] == "uc-query-document"
    assert result.value["prompt"]
    assert "ブロックを丸ごと取得する" in result.value["value"]


def test_query_pathでblockKey省略時はヒットしたブロックだけを配列で返す():
    """
    Given query システム と対象 Document
    When operation query_path を blockKey を指定せず path "items[?priority=='high']" で実行する
    Then results にはヒットしたブロックだけが { blockKey, prompt, value } として含まれ、ヒットしなかったブロックは省略される
    """
    result = _engine().run(
        "query_path", _TARGET,
        {"expression": "scenarios[?category=='異常系']"},
    )
    assert isinstance(result, Ok), result
    assert result.value["documentId"] == "uc-query-document"
    hit = next(r for r in result.value["results"] if r["blockKey"] == "acceptanceScenarios")
    assert hit["prompt"]
    assert all(item["category"] == "異常系" for item in hit["value"])
    assert "title" not in [r["blockKey"] for r in result.value["results"]]


def test_query_pathはフィルタ条件を式内で表現できる():
    """
    Given query システム と対象 Document
    When operation query_path を blockKey, path "items[?required==`true`]" で実行する
    Then value には required な要素だけが含まれる
    """
    result = _engine().run(
        "query_path", _TARGET,
        {"blockKey": "acceptanceScenarios", "expression": "scenarios[?category=='異常系']"},
    )
    assert isinstance(result, Ok), result
    assert all(item["category"] == "異常系" for item in result.value["value"])


def test_query_pathは配列の範囲指定をスライス式で表現できる():
    """
    Given query システム と対象 Document
    When operation query_path を blockKey, path "items[2:5]" で実行する
    Then value にはその範囲の要素だけが含まれる
    """
    result = _engine().run(
        "query_path", _TARGET,
        {"blockKey": "acceptanceScenarios", "expression": "scenarios[0:2]"},
    )
    assert isinstance(result, Ok), result
    assert len(result.value["value"]) == 2


def test_query_pathは正規表現カスタム関数で絞り込める():
    """
    Given query システム と対象 Document
    When operation query_path を blockKey, path "items[?regex_match(name, 'foo.*')]" で実行する
    Then value には正規表現に一致する要素だけが含まれる
    """
    result = _engine().run(
        "query_path", _TARGET,
        {"blockKey": "acceptanceScenarios", "expression": "scenarios[?regex_match(name, '.*丸ごと.*')].name"},
    )
    assert isinstance(result, Ok), result
    assert result.value["value"] == ["ブロックを丸ごと取得する"]


def test_query_pathの構文エラーはWaffle独自のエラーへ変換される():
    """
    Given query システム と対象 Document
    When 構文的に不正なJMESPath式を path に指定して operation query_path を実行する
    Then jmespath の生例外ではなく、Waffle独自のエラーコード・メッセージが返る
    """
    result = _engine().run(
        "query_path", _TARGET,
        {"blockKey": "acceptanceScenarios", "expression": "scenarios[?"},
    )
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_JMESPATH_EXPRESSION"


def test_query_pathでblockKey省略時_式の形に合わないブロックは静かにスキップされる():
    """
    Given query システム と、items配列を持つブロックと持たないブロックが混在する対象 Document
    When operation query_path を blockKey を指定せず path "items[?contains(rule, 'CLI')]" で実行する
    Then results には items を持つブロックの評価結果だけが含まれ、items を持たず評価時型エラーになったブロックはエラーにならず黙って省略される
    """
    result = _engine().run(
        "query_path", ".waffle/documents/agent/waffle.json",
        {"expression": "items[?contains(rule, 'CLI')] || items[?contains(rule, 'memory')]"},
    )
    assert isinstance(result, Ok), result
    hit = next((r for r in result.value["results"] if r["blockKey"] == "operatingRules"), None)
    assert hit is not None
    assert any("CLI" in item["rule"] for item in hit["value"])
    # title/role等、itemsを持たない・rule項目を持たないブロックはエラーにならず省略される
    assert "title" not in [r["blockKey"] for r in result.value["results"]]
    assert "role" not in [r["blockKey"] for r in result.value["results"]]


def test_query_pathでblockKey指定時_式の評価時型エラーはエラーを返す():
    """
    Given query システム と、items配列は持つがruleフィールドは持たない対象ブロック
    When operation query_path を blockKey で明示指定し、ruleフィールドを前提とした path "items[?contains(rule, 'CLI')]" で実行する
    Then エラーコード INVALID_JMESPATH_EXPRESSION が返る
    """
    result = _engine().run(
        "query_path", ".waffle/documents/agent/waffle.json",
        {"blockKey": "keyCommands", "expression": "items[?contains(rule, 'CLI')]"},
    )
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_JMESPATH_EXPRESSION"


def test_schemaRefを持たないファイルはrawで返す():
    """
    Given schemaRefを持たない対象ファイル
    When scan以外の任意のoperationを実行する
    Then 戻り値は{ prompt, value }ではなく{ type: "raw", content: <生テキスト> }という別形状で返る
    """
    import json
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"hello": "world"}, f)
        path = f.name

    result = _engine().run("get_meta", path)
    assert isinstance(result, Ok), result
    assert result.value["type"] == "raw"
