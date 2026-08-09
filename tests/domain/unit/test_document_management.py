"""筋書きに対応しない、補助的なテスト。

業務サービスの筋書きに対応するテストは test_waffle.py にある。ここに残して
あるのは、仕様がまだ振る舞いとして宣言していない場合分け（配列でない値を
受け取ったときの拒否、表示名への写像、逆解析で同じ変数名が複数回現れる場合、
配列セルの箇条書きと結合の優先順位）。

宣言されていないので、突き合わせの対象にならない。宣言する価値があるかは
別に判断する。
"""
from waffle.domain.services import path_template
from waffle.domain.services.part_renderer import MalformedContentError, render_parts
from waffle.domain.services.schema_discriminator import discriminator_key








def test_reverse_parse_duplicate_variable_name_self_contained():
    """subdomain の自己格納パターン（フォルダ名=ファイル名=documentId）は同名変数が2回登場する。"""
    template = ".waffle/documents/specs/{contextRef}/subdomain/{documentId}/{documentId}.json"
    path = ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/sd-document-management.json"
    assert path_template.reverse_parse(template, path) == {
        "contextRef": "bc-waffle", "documentId": "sd-document-management",
    }


def test_reverse_parse_duplicate_variable_name_requires_consistent_value():
    """同名変数の2回目はバックリファレンス＝両方の値が食い違うパスは不一致になる。"""
    template = ".waffle/documents/specs/{contextRef}/subdomain/{documentId}/{documentId}.json"
    inconsistent_path = ".waffle/documents/specs/bc-waffle/subdomain/sd-a/sd-b.json"
    assert path_template.reverse_parse(template, inconsistent_path) is None


# --- 整形描画（part_renderer）: Schema集約の値オブジェクト(x-render宣言)とDocument集約の
# contentにまたがる計算のため業務サービスとしてここに置く ---



# --- 描画 ---



def test_list_raises_on_non_array_value():
    """
    Given listを宣言するx-renderと、対応するcontent値が配列でなく文字列
    When renderする
    Then 1文字ずつの箇条書きになる代わりにMalformedContentErrorが送出される
    """
    try:
        render_parts([{"as": "list", "from": "items"}], {"items": "配列でない文字列"}, 3)
        assert False, "例外が送出されなかった"
    except MalformedContentError as e:
        assert "items" in str(e)


def test_table_raises_on_non_array_value():
    """
    Given tableを宣言するx-renderと、対応するcontent値が配列でなく文字列
    When renderする
    Then MalformedContentErrorが送出される
    """
    parts = [{"as": "table", "from": "items", "columns": [{"field": "name"}]}]
    try:
        render_parts(parts, {"items": "配列でない文字列"}, 3)
        assert False, "例外が送出されなかった"
    except MalformedContentError as e:
        assert "items" in str(e)


def test_section_raises_on_non_array_value():
    """
    Given sectionを宣言するx-renderと、対応するcontent値が配列でなく文字列
    When renderする
    Then MalformedContentErrorが送出される
    """
    parts = [{"as": "section", "from": "items", "each": [{"as": "paragraph", "from": "text"}]}]
    try:
        render_parts(parts, {"items": "配列でない文字列"}, 3)
        assert False, "例外が送出されなかった"
    except MalformedContentError as e:
        assert "items" in str(e)


def test_paragraph_maps_value_to_display_label():
    """
    Given labelMapを宣言したparagraph部品と、labelMapのキーに一致するfrom値
    When renderする
    Then 生値ではなくlabelMapが示す表示ラベルが描画される
    """
    md = render_parts(
        [{"as": "paragraph", "from": "classification", "labelMap": {"core": "中核", "generic": "一般"}}],
        {"classification": "core"}, 3,
    )
    assert md == "中核"


def test_section_maps_title_to_display_label():
    """
    Given labelMapを宣言したsection部品と、titleFromが指すitemフィールドの値
    When renderする
    Then 各itemの見出しに生値ではなくlabelMapが示す表示ラベルが使われる
    """
    parts = [{"as": "section", "from": "items", "titleFrom": "kind",
              "labelMap": {"subdomain": "サブドメイン", "usecase": "業務ユースケース"},
              "each": [{"as": "list", "from": "members"}]}]
    data = {"items": [{"kind": "subdomain", "members": ["sd-a"]}, {"kind": "usecase", "members": ["uc-a"]}]}
    md = render_parts(parts, data, 3)
    assert "### サブドメイン" in md
    assert "### 業務ユースケース" in md
    assert "### subdomain" not in md






























def test_table_join_leaves_absent_field_empty():
    """joinテンプレートが参照するキーを要素が持たなければ、その箇所は空になる。

    任意のフィールドは、値が無い要素で欄そのものを消せるようにする。無い方が
    普通である場合（1か所にしか置かない概念の役割 等）に、既定値の語を
    全行へ並べずに済む。
    """
    parts = [{"as": "table", "from": "items", "columns": [
        {"field": "name", "header": "概念"},
        {"field": "places", "header": "配置", "join": "{role} {path}", "sep": " / "}]}]
    data = {"items": [{"name": "usecase", "places": [{"path": "application/usecases"}]}]}
    md = render_parts(parts, data, 3)
    assert "| usecase | application/usecases |" in md


def test_table_renders_array_cell_as_bullet_list():
    """
    Given bullet:trueを指定したcolumns宣言と複数要素の配列値を持つセル
    When renderする
    Then 各要素が"- "接頭辞つきで<br>区切りの箇条書きとしてセル内に描画される
    """
    parts = [{"as": "table", "from": "items", "columns": [
        {"field": "code", "header": "コード", "code": True},
        {"field": "condition", "header": "条件", "bullet": True}]}]
    data = {"items": [{"code": "UNSUPPORTED_ROOT_DISPATCH_SHAPE", "condition": [
        "ルート直下のkind分岐が、既知の形状に適合しない",
        "if/then/else形式でありながら、elseの暗黙値を一意に逆算できない"]}]}
    md = render_parts(parts, data, 3)
    assert "- ルート直下のkind分岐が、既知の形状に適合しない<br>- if/then/else形式でありながら、elseの暗黙値を一意に逆算できない" in md


def test_table_prefers_bullet_over_join_when_both_given():
    """
    Given bullet:trueとjoin/sepの両方を指定したcolumns宣言と、dict要素の配列値
    When renderする
    Then join/sepによる1行連結（"name: type"形式）ではなくbulletによる箇条書きが描画される
    """
    parts = [{"as": "table", "from": "items", "columns": [
        {"field": "name", "header": "エンティティ"},
        {"field": "attributes", "header": "属性", "bullet": True, "join": "{name}: {type}", "sep": " / "}]}]
    data = {"items": [{"name": "Order", "attributes": [
        {"name": "status", "type": "OrderStatus"},
        {"name": "total", "type": "Money"}]}]}
    md = render_parts(parts, data, 3)
    assert "status: OrderStatus / total: Money" not in md






