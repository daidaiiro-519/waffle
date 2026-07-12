"""operation_drift（specが宣言するoperation名と実装のoperation文字列の突き合わせ）のネイティブテスト。"""
from waffle.domain.services import operation_drift


def test_declared_operationsはscenarioのoperationフィールドを集める():
    """
    Given operationフィールドを持つシナリオといくつか持たないシナリオ
    When declared_operationsを実行する
    Then operationフィールドを持つシナリオの値だけが集合として返る
    """
    doc = {
        "content": {
            "acceptanceScenarios": {
                "scenarios": [
                    {"name": "a", "operation": "get_block"},
                    {"name": "b", "operation": "filter_items"},
                    {"name": "c"},
                ]
            }
        }
    }
    assert operation_drift.declared_operations(doc) == {"get_block", "filter_items"}


def test_declared_operationsはacceptanceScenariosが無ければ空集合():
    """
    Given acceptanceScenariosブロックを持たないDocument
    When declared_operationsを実行する
    Then 空集合が返る
    """
    assert operation_drift.declared_operations({"content": {}}) == set()


def test_implemented_operationsはoperation等価比較の文字列を集める():
    """
    Given if operation == "..." 形式の分岐を含むソースコード
    When implemented_operationsを実行する
    Then 全ての比較対象文字列が集合として返る
    """
    source = '''
def run(self, operation, params):
    if operation == "get_block":
        pass
    elif operation == "filter_items":
        pass
    if operation == "get_block":
        pass
'''
    assert operation_drift.implemented_operations(source) == {"get_block", "filter_items"}


def test_implemented_operationsはoperation分岐が無ければ空集合():
    """
    Given operation比較を含まないソースコード
    When implemented_operationsを実行する
    Then 空集合が返る
    """
    assert operation_drift.implemented_operations("def run(self): pass") == set()
