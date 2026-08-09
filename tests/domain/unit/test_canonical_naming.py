"""canonical_naming が、規約の宣言に従って名前を導くことのテスト。

仕様のシナリオには対応しない、規約由来のテスト。
表記規則はコードが持たず coding-standard の naming ブロックが持つ。
ここで確かめるのは「宣言どおりに変換すること」であって、
どの表記を採るかではない。
"""
import pytest

from waffle.domain.services.canonical_naming import apply_case, file_name

PYTHON = {"fileNameDerivedFrom": "type", "fileNameTransform": "pascal-to-snake",
          "fileNameSuffix": ".py"}
JAVA = {"fileNameDerivedFrom": "type", "fileNameTransform": "identity",
        "fileNameSuffix": ".java"}
TYPESCRIPT = {"fileNameDerivedFrom": "type", "fileNameTransform": "pascal-to-kebab",
              "fileNameSuffix": ".ts"}


def test_python_file_name_is_snake_case():
    """pascal-to-snake を宣言したスタックでは、型名がスネークケースになる。"""
    assert file_name("RegisterOrder", PYTHON) == "register_order.py"


def test_java_file_name_matches_type_name():
    """identity を宣言したスタックでは、型名がそのままファイル名になる。

    Javaは公開クラスを含むファイルの名前が型名と一致していないとコンパイル
    できない。表記をコードが決めていると、この言語では必ず外す。
    """
    assert file_name("RegisterOrder", JAVA) == "RegisterOrder.java"


def test_typescript_file_name_is_kebab_case():
    """pascal-to-kebab を宣言したスタックでは、ケバブケースになる。"""
    assert file_name("RegisterOrder", TYPESCRIPT) == "register-order.ts"


def test_unknown_transform_is_rejected():
    """宣言に無い変換を指定されたら、黙って既定へ倒さず拒否する。"""
    with pytest.raises(ValueError):
        file_name("RegisterOrder", {"fileNameTransform": "no-such", "fileNameSuffix": ".py"})


@pytest.mark.parametrize("case,expected", [
    ("snake", "document_id"),
    ("camel", "documentId"),
    ("pascal", "DocumentId"),
    ("kebab", "document-id"),
    ("upper-snake", "DOCUMENT_ID"),
])
def test_apply_case_follows_declaration(case, expected):
    """宣言された表記に従って識別子を変換する。"""
    assert apply_case("documentId", case) == expected


def test_apply_case_rejects_unknown_case():
    """宣言に無い表記を指定されたら拒否する。"""
    with pytest.raises(ValueError):
        apply_case("documentId", "no-such")


@pytest.mark.parametrize("case,expected", [
    ("snake", "uc_check_scenario_drift"),
    ("camel", "ucCheckScenarioDrift"),
    ("pascal", "UcCheckScenarioDrift"),
    ("kebab", "uc-check-scenario-drift"),
    ("upper-snake", "UC_CHECK_SCENARIO_DRIFT"),
])
def test_apply_case_splits_on_separators(case, expected):
    """区切り記号も語の区切りとして扱う。

    大文字小文字の境目しか見ないと、既に区切り記号で綴られた識別子（仕様の
    識別子はこの形）を1語とみなし、どの表記を指定しても変換されないまま返る。
    """
    assert apply_case("uc-check-scenario-drift", case) == expected


@pytest.mark.parametrize("case,expected", [
    ("snake", "already_snake"),
    ("camel", "alreadySnake"),
    ("pascal", "AlreadySnake"),
    ("kebab", "already-snake"),
])
def test_apply_case_handles_underscore_separated_input(case, expected):
    """下線で綴られた識別子も、同じように語へ分ける。"""
    assert apply_case("already_snake", case) == expected


@pytest.mark.parametrize("case", ["snake", "camel", "pascal", "kebab"])
def test_apply_case_is_idempotent(case):
    """一度変換した結果をもう一度変換しても変わらない。

    区切りを増やすと、変換後の綴りが再び分割されうる。分割の規則が
    冪等でないと、通る経路の数だけ違う名前が生まれる。

    全て大文字にする表記は対象外。連続する大文字を1文字ずつの語として
    分けるのが既存の挙動であり、全て大文字の結果は必ず再び分割される。
    そこを変えると、既に通っている頭字語の変換が変わる。
    """
    once = apply_case("uc-check-scenario-drift", case)
    assert apply_case(once, case) == once


def test_apply_case_keeps_a_leading_separator():
    """先頭の区切りは落とさない。

    非公開を先頭の下線で表す規約があるため、正規化して組み立て直す実装に
    すると、その規約と正面から衝突する。
    """
    assert apply_case("_privateField", "snake") == "_private_field"


@pytest.mark.parametrize("name,case,expected", [
    ("documentId", "snake", "document_id"),
    ("documentId", "pascal", "DocumentId"),
    ("HTTPStatus", "snake", "h_t_t_p_status"),
    ("v2Schema", "snake", "v2_schema"),
    ("", "snake", ""),
])
def test_apply_case_keeps_existing_behaviour(name, case, expected):
    """既に通っている入力の結果を変えない。

    区切りを足す変更が、既存の呼び出し元（属性名・型名・操作名の変換）へ
    漏れていないことを、実データと同じ形の入力で確かめる。
    """
    assert apply_case(name, case) == expected
