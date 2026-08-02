"""concept_source_root（architecture文書のsourceRoot/conceptPlacementから
実装ファイルの配置パスを導出する）のネイティブテスト。"""
from waffle.domain.services import concept_source_root


def test_sourceRootとplacementを結合して解決する():
    """
    Given {package}トークンを含むsourceRootと、usecase概念のplacement
    When resolve_source_rootをpackage変数付きで実行する
    Then sourceRoot/placementの形に解決される
    """
    layout = {"sourceRoot": "src/{package}"}
    items = [{"concept": "usecase", "placement": "application/usecases"}]
    result = concept_source_root.resolve_source_root(layout, items, "usecase", package="waffle")
    assert result == "src/waffle/application/usecases"


def test_プレースホルダの無いsourceRootはpackage変数を無視して解決される():
    """
    Given プレースホルダを含まないsourceRoot（TypeScript版の慣習）
    When package変数を渡してresolve_source_rootを実行する
    Then package変数は無視され、sourceRoot/placementがそのまま結合される
    """
    layout = {"sourceRoot": "src"}
    items = [{"concept": "usecase", "placement": "application/usecases"}]
    result = concept_source_root.resolve_source_root(layout, items, "usecase", package="anything")
    assert result == "src/application/usecases"


def test_sourceRootが無ければNoneを返す():
    """
    Given sourceRootフィールドを持たないlayout
    When resolve_source_rootを実行する
    Then Noneが返る
    """
    layout = {}
    items = [{"concept": "usecase", "placement": "application/usecases"}]
    assert concept_source_root.resolve_source_root(layout, items, "usecase") is None


def test_該当conceptが見つからなければNoneを返す():
    """
    Given conceptPlacementに存在しないconcept名
    When resolve_source_rootを実行する
    Then Noneが返る
    """
    layout = {"sourceRoot": "src/{package}"}
    items = [{"concept": "aggregate", "placement": "domain/model"}]
    assert concept_source_root.resolve_source_root(layout, items, "usecase", package="waffle") is None


def test_package_name_from_referenceは接頭辞を剥がす():
    """
    Given "architecture-waffle"のようなarchitectureRef（documentId）とcodingKind
    When package_name_from_referenceを実行する
    Then "architecture-"接頭辞を剥がしたproduct名が返る
    """
    assert concept_source_root.package_name_from_reference("architecture-waffle", "architecture") == "waffle"


def test_package_name_from_referenceはkindプレフィックスが一致しなければNoneを返す():
    """
    Given codingKindのプレフィックスと一致しないarchitectureRef
    When package_name_from_referenceを実行する
    Then Noneが返る
    """
    assert concept_source_root.package_name_from_reference("tech-stack-waffle", "architecture") is None
