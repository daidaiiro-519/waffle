"""uc-lint-docstring の受け入れテスト（ネイティブpytest）。"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.pydoclint_linter import PydoclintLinter
from waffle.adapters.outbound.python_ast_source_scanner import PythonAstSourceScanner
from waffle.application.usecases.lint_docstring import LintDocstring
from waffle.application.usecases.scan_source_code import ScanSourceCode
from waffle.shared.result import Err, Ok


def _engine(executable: str = "pydoclint") -> LintDocstring:
    scan_engine = ScanSourceCode(FsDocumentRepository(), PythonAstSourceScanner())
    return LintDocstring(scan_engine, PydoclintLinter(executable))


def test_all_elements_conform_to_the_standard(tmp_path):
    """
    Scenario: 全要素が規約に適合するとき違反なしと判定する
    Given DocstringSchema の google kind に適合する docstring だけを持つコードベース
    When 適合判定を実行する
    Then 違反は空配列で返り、エラーにはならない
    """
    (tmp_path / "sample.py").write_text(
        'def greet(name):\n'
        '    """挨拶を返す。\n\n'
        '    Args:\n'
        '        name: 相手の名前。\n\n'
        '    Returns:\n'
        '        挨拶文。\n'
        '    """\n'
        '    return f"hello {name}"\n',
        encoding="utf-8",
    )

    result = _engine().run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Ok), result
    assert result.value == []


def test_public_element_without_docstring(tmp_path):
    """
    Scenario: docstring が無い公開要素を検出する
    Given docstring を持たない公開関数を含むコードベース
    When 適合判定を実行する
    Then その要素について MISSING_DOC_COMMENT 違反が報告される
    """
    (tmp_path / "sample.py").write_text("def undocumented(x):\n    return x\n", encoding="utf-8")

    result = _engine().run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Ok), result
    violation = next(v for v in result.value if v["name"] == "undocumented")
    assert violation["code"] == "MISSING_DOC_COMMENT"


def test_args_names_do_not_match_signature(tmp_path):
    """
    Scenario: Args の引数名がシグネチャと不一致な要素を検出する
    Given Args セクションの引数名が実シグネチャと異なる関数を含むコードベース
    When 適合判定を実行する
    Then その要素について ARGS_MISMATCH 違反が報告される
    """
    (tmp_path / "sample.py").write_text(
        'def mismatched(a, b):\n'
        '    """要約。\n\n'
        '    Args:\n'
        '        a: first.\n'
        '        c: wrong name.\n'
        '    """\n'
        '    return a\n',
        encoding="utf-8",
    )

    result = _engine().run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Ok), result
    violation = next(v for v in result.value if v["name"] == "mismatched")
    assert violation["code"] == "ARGS_MISMATCH"


def test_missing_args_section_in_summary_only_docstring(tmp_path):
    """
    Scenario: 要約行のみの短いdocstringでもArgsセクション欠落を検出する
    Given 引数を持つ公開関数が、要約行のみでArgsセクションを持たない短いdocstringを持つコードベース
    When 適合判定を実行する
    Then その要素について MISSING_ARGS_SECTION 違反が報告される
    """
    (tmp_path / "sample.py").write_text(
        'def f(a, b):\n'
        '    """要約。"""\n'
        '    return a\n',
        encoding="utf-8",
    )

    result = _engine().run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Ok), result
    assert any(v["name"] == "f" and v["code"] == "MISSING_ARGS_SECTION" for v in result.value)


def test_missing_returns_section(tmp_path):
    """
    Scenario: Returnsセクションの欠落を検出する
    Given 戻り値を持つ公開関数が、Returnsセクションを持たないdocstringを持つコードベース
    When 適合判定を実行する
    Then その要素について MISSING_RETURNS_SECTION 違反が報告される
    """
    (tmp_path / "sample.py").write_text(
        'def f():\n'
        '    """要約。"""\n'
        '    return 1\n',
        encoding="utf-8",
    )

    result = _engine().run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Ok), result
    assert any(v["name"] == "f" and v["code"] == "MISSING_RETURNS_SECTION" for v in result.value)


def test_missing_raises_section(tmp_path):
    """
    Scenario: Raisesセクションの欠落を検出する
    Given 例外を送出する公開関数が、Raisesセクションを持たないdocstringを持つコードベース
    When 適合判定を実行する
    Then その要素について MISSING_RAISES_SECTION 違反が報告される
    """
    (tmp_path / "sample.py").write_text(
        'def f():\n'
        '    """要約。"""\n'
        '    raise ValueError("bad")\n',
        encoding="utf-8",
    )

    result = _engine().run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Ok), result
    assert any(v["name"] == "f" and v["code"] == "MISSING_RAISES_SECTION" for v in result.value)


def test_private_element_is_skipped(tmp_path):
    """
    Scenario: 非公開要素はセクション欠落判定の対象外とする
    Given 引数・戻り値・例外を持つがdocstringのセクションを欠く非公開関数を含むコードベース
    When 適合判定を実行する
    Then MISSING_ARGS_SECTION・MISSING_RETURNS_SECTION・MISSING_RAISES_SECTIONのいずれも報告されない
    """
    (tmp_path / "sample.py").write_text(
        'def _f(a):\n'
        '    """要約。"""\n'
        '    if a:\n'
        '        raise ValueError("bad")\n'
        '    return a\n',
        encoding="utf-8",
    )

    result = _engine().run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Ok), result
    codes = {"MISSING_ARGS_SECTION", "MISSING_RETURNS_SECTION", "MISSING_RAISES_SECTION"}
    assert not any(v["name"] == "_f" and v["code"] in codes for v in result.value)


def test_unsupported_kind_is_rejected(tmp_path):
    """
    Scenario: 対応する kind が無い言語は UNSUPPORTED_KIND
    Given DocstringSchemaに定義の無い言語、またはgoogle以外の未実装kindのコードベース
    When 適合判定を実行する
    Then UNSUPPORTED_KINDエラーが返る
    """
    (tmp_path / "sample.py").write_text("def f():\n    pass\n", encoding="utf-8")

    result = _engine().run(str(tmp_path), _standard(tmp_path, tags=("Parameters", "Returns", "Raises")))
    assert isinstance(result, Err), result
    assert result.details[0] == "UNSUPPORTED_KIND"


def test_missing_tool_is_reported(tmp_path):
    """
    Scenario: 対応するツールが実行環境に無いとき TOOL_NOT_AVAILABLE
    Given kind に対応する lint ツールがインストールされていない環境
    When 適合判定を実行する
    Then TOOL_NOT_AVAILABLE エラーが返る
    """
    (tmp_path / "sample.py").write_text(
        'def greet(name):\n    """挨拶。\n\n    Args:\n        name: 名前。\n    """\n    pass\n',
        encoding="utf-8",
    )

    result = _engine(executable="no-such-lint-tool").run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Err), result
    assert result.details[0] == "TOOL_NOT_AVAILABLE"


def _standard(tmp_path, tags=("Args:", "Returns:", "Raises:"), syntax="tagged"):
    """規約のdocstringブロックだけを持つ、最小のcoding-standardを作る。"""
    import json
    path = tmp_path / "documents" / "coding" / "coding-standard-fake.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "documentId": "coding-standard-fake", "codingKind": "coding-standard",
        "content": {"docstring": {
            "blockType": "Docstring", "title": "docstring",
            "syntaxKind": syntax, "tagParams": tags[0],
            "tagReturns": tags[1], "tagRaises": tags[2],
        }},
    }, ensure_ascii=False), encoding="utf-8")
    return str(path)


def test_syntax_comes_from_the_standard(tmp_path):
    """
    Scenario: 構文は規約の宣言から決まる
    Given docstringブロックがタグの綴りを宣言している規約
    When その規約でdocstringの適合を確かめる
    Then 宣言された構文に対応する道具の設定で判定される
    """
    (tmp_path / "sample.py").write_text(
        'def greet(name):\n'
        '    """挨拶を返す。\n\n'
        '    Args:\n'
        '        name: 相手の名前。\n\n'
        '    Returns:\n'
        '        挨拶文。\n'
        '    """\n'
        '    return f"hello {name}"\n',
        encoding="utf-8",
    )
    result = _engine().run(str(tmp_path), _standard(tmp_path))
    assert isinstance(result, Ok), result
    assert result.value == []


def test_syntax_the_tool_cannot_follow_is_reported(tmp_path):
    """
    Scenario: 宣言に道具が追随できないことを黙って通さない
    Given 既存lintツールが持たない構文を宣言している規約
    When その規約でdocstringの適合を確かめる
    Then UNSUPPORTED_SYNTAXとして報告される
    And 呼び出しの誤りを表すUNSUPPORTED_KINDとは区別されている
    """
    standard = _standard(tmp_path, tags=("@param", "@returns", "@throws"))
    result = _engine().run(str(tmp_path), standard)
    assert isinstance(result, Err), result
    assert result.details == ["UNSUPPORTED_SYNTAX"]
