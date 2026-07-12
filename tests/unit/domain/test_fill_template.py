"""fill_template（skeleton/fillTemplateの機械走査とプレースホルダー合成）のネイティブテスト。

uc-render-blank-templateのAcceptanceCriteriaに対応する。純粋なdict操作のみでportを
必要としないため、全件をdomain層に置く。
"""
from waffle.domain.services.fill_template import build_fill_template, overlay_placeholders


def test_単純な文字列フィールドはx_prompt_write本文をプレースホルダーにする():
    """
    Given x-prompt-writeを持つ単純な文字列フィールドのskeleton
    When overlay_placeholdersを実行する
    Then そのフィールドの値が{{x-prompt-write本文}}に置き換わる
    """
    skeleton = {"content": {"title": {"blockType": "Title", "title": ""}}}
    entries = [{"path": "content.title.title", "type": "string", "prompt": "タイトルを書く", "required": True}]

    result = overlay_placeholders(skeleton, entries)

    assert result["content"]["title"]["title"] == "{{タイトルを書く}}"
    assert result["content"]["title"]["blockType"] == "Title"


def test_enumフィールドはプレースホルダーに選択肢を併記する():
    """
    Given enumを持つフィールドのskeleton
    When overlay_placeholdersを実行する
    Then プレースホルダー文字列に選択肢一覧が含まれる
    """
    skeleton = {"status": "CREATED"}
    entries = [{"path": "status", "type": "string", "prompt": "状態", "required": True, "enum": ["CREATED", "VALIDATED"]}]

    result = overlay_placeholders(skeleton, entries)

    assert result["status"] == "{{状態（選択肢: CREATED / VALIDATED）}}"


def test_構造化要素を持つ配列は要素1件分のプレースホルダーオブジェクトの配列にする():
    """
    Given element(構造化された要素)を宣言する配列フィールドのskeleton
    When overlay_placeholdersを実行する
    Then 要素1件分のプレースホルダーオブジェクトを含む配列になる
    """
    skeleton = {"content": {"errors": {"blockType": "Errors", "items": []}}}
    entries = [{
        "path": "content.errors.items", "type": "array", "prompt": "エラーを列挙", "required": False,
        "element": {"code": "エラーコード", "condition": "発生条件"},
    }]

    result = overlay_placeholders(skeleton, entries)

    assert result["content"]["errors"]["items"] == [{"code": "{{エラーコード}}", "condition": "{{発生条件}}"}]


def test_単純な配列フィールドはプレースホルダー文字列を1件だけ含む配列にする():
    """
    Given elementを持たない単純な配列フィールド(例: tags)のskeleton
    When overlay_placeholdersを実行する
    Then 文字列プレースホルダー1件だけを含む配列になる（文字列のまま代入して1文字ずつ
         反復描画されてしまう事故を防ぐ）
    """
    skeleton = {"tags": []}
    entries = [{"path": "tags", "type": "array", "prompt": "タグを列挙", "required": False}]

    result = overlay_placeholders(skeleton, entries)

    assert result["tags"] == ["{{タグを列挙}}"]


def test_配列の中にさらに配列を持つ要素はネストしたプレースホルダー配列にする():
    """
    Given 配列の要素(オブジェクト)自身がさらに構造化された配列(例: Entities.items[].attributes)を宣言するschema
    When build_fill_templateで走査しoverlay_placeholdersで合成する
    Then ネストした配列も1件分のプレースホルダーオブジェクトを含む配列になる（文字列に
         潰れてレンダラの反復描画を壊さない）
    """
    schema = {
        "$defs": {
            "AttributeItem": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "x-prompt-write": "属性名"},
                    "type": {"type": "string", "x-prompt-write": "型"},
                },
            },
        },
    }
    content = {
        "type": "object",
        "required": ["entities"],
        "properties": {
            "entities": {
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "x-prompt-write": "エンティティを列挙",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "x-prompt-write": "エンティティ名"},
                                "attributes": {
                                    "type": "array",
                                    "x-prompt-write": "属性を列挙",
                                    "items": {"$ref": "#/$defs/AttributeItem"},
                                },
                            },
                        },
                    },
                },
            },
        },
    }

    entries = build_fill_template(schema, content)
    skeleton = {"content": {"entities": {"items": []}}}
    result = overlay_placeholders(skeleton, entries)

    assert result["content"]["entities"]["items"] == [
        {"name": "{{エンティティ名}}", "attributes": [{"name": "{{属性名}}", "type": "{{型}}"}]}
    ]


def test_allOf合成された配列要素もオブジェクト配列として扱う():
    """
    Given 配列の要素がtype:objectを明示せずallOfで合成されているschema
        （_merge_allofの返り値はtypeキーを持たずpropertiesキーだけを持つ）
    When build_fill_templateで走査しoverlay_placeholdersで合成する
    Then 単純な配列と誤認せず、プレースホルダーオブジェクトを含む配列になる
    """
    schema = {
        "$defs": {
            "StepFields": {
                "properties": {
                    "title": {"type": "string", "x-prompt-write": "タイトル"},
                },
            },
        },
    }
    content = {
        "type": "object",
        "required": ["steps"],
        "properties": {
            "steps": {
                "type": "array",
                "x-prompt-write": "手順を列挙",
                "items": {"allOf": [{"$ref": "#/$defs/StepFields"}]},
            },
        },
    }

    entries = build_fill_template(schema, content)
    skeleton = {"content": {"steps": []}}
    result = overlay_placeholders(skeleton, entries)

    assert result["content"]["steps"] == [{"title": "{{タイトル}}"}]


def test_プロンプトの無いオブジェクト配列要素も空オブジェクトを含む配列にする():
    """
    Given 配列の要素はobject型だが、どのプロパティもx-prompt-writeを宣言していないschema
    When build_fill_templateで走査しoverlay_placeholdersで合成する
    Then 単純な配列と誤認して文字列プレースホルダーにせず、空オブジェクトを含む配列にする
         （table/section描画がAttributeErrorにならないようにするため）
    """
    content = {
        "type": "object",
        "required": ["metrics"],
        "properties": {
            "metrics": {
                "type": "array",
                "x-prompt-write": "指標を列挙",
                "items": {"type": "object", "properties": {"name": {"type": "string"}}},
            },
        },
    }

    entries = build_fill_template({}, content)
    skeleton = {"content": {"metrics": []}}
    result = overlay_placeholders(skeleton, entries)

    assert result["content"]["metrics"] == [{}]


def test_自己参照的な配列は無限再帰せず有限の深さでネストした配列のままにする():
    """
    Given 配列の要素が自分自身と同じ構造の配列(children)を持つ自己参照的なschema
        （例: AgentSchemaのSubStep）
    When build_fill_templateで走査しoverlay_placeholdersで合成する
    Then 無限再帰にならず、途中で文字列に潰れることもなく、最深部までネストした配列のままになる
    """
    schema = {
        "$defs": {
            "SubStep": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "x-prompt-write": "タイトル"},
                    "children": {
                        "type": "array",
                        "x-prompt-write": "さらに分割する場合のSubStep",
                        "items": {"$ref": "#/$defs/SubStep"},
                    },
                },
            },
        },
    }
    content = {
        "type": "object",
        "required": ["steps"],
        "properties": {
            "steps": {
                "type": "array",
                "x-prompt-write": "手順を列挙",
                "items": {"$ref": "#/$defs/SubStep"},
            },
        },
    }

    entries = build_fill_template(schema, content)
    skeleton = {"content": {"steps": []}}
    result = overlay_placeholders(skeleton, entries)

    top = result["content"]["steps"][0]
    assert top["title"] == "{{タイトル}}"
    assert isinstance(top["children"], list)
    nested = top["children"][0]
    assert isinstance(nested["children"], list)  # 打ち切り後も必ずlistのまま(文字列に潰れない)


def test_元のskeletonを変更しない():
    """
    Given 元のskeleton
    When overlay_placeholdersを実行する
    Then 元のskeletonオブジェクトは変更されない（副作用なし）
    """
    skeleton = {"content": {"title": {"blockType": "Title", "title": ""}}}
    entries = [{"path": "content.title.title", "type": "string", "prompt": "タイトル", "required": True}]

    overlay_placeholders(skeleton, entries)

    assert skeleton["content"]["title"]["title"] == ""
