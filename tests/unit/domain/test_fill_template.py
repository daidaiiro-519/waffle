"""fill_template（skeleton/fillTemplateの機械走査とプレースホルダー合成）のネイティブテスト。

uc-render-blank-templateのAcceptanceCriteriaに対応する。純粋なdict操作のみでportを
必要としないため、全件をdomain層に置く。
"""
from waffle.domain.services.fill_template import overlay_placeholders


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
