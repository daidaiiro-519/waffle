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
