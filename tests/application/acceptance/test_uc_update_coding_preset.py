"""uc-update-coding-preset の受け入れテスト（ネイティブpytest）。"""
from waffle.application.usecases.update_coding_preset import UpdateCodingPreset
from waffle.shared.result import Err, Ok

_PRESET = "probe-preset"
_FROM = "architecture-probe"
_PATH = f".waffle/documents/coding/{_FROM}." + "json"


def _preset() -> dict:
    return {
        "tech-stack": {"title": {"title": "T"}, "runtime": {"languages": []}},
        "architecture": {
            "title": {"title": "A"},
            "rules": {"blockType": "Rules", "items": [{"level": "必須", "rule": "古い規約"}]},
            "layout": {"sourceRoot": "src/{package}"},
        },
        "coding-standard": {"title": {"title": "C"}},
        "test-standard": {"title": {"title": "S"}},
    }


def _document() -> dict:
    return {
        "documentId": _FROM, "codingKind": "architecture", "stack": "probe",
        "content": {
            "title": {"title": "A"},
            "rules": {"blockType": "Rules", "items": [{"level": "必須", "rule": "直した規約"}]},
            "layout": {"sourceRoot": "src/{package}"},
            # プリセットが持たない、プロダクト固有のブロック
            "coveredContexts": {"blockType": "CoveredContexts", "items": ["bc-probe"]},
        },
    }


class _FakePresets:
    def __init__(self, presets: dict):
        self._presets = presets
        self.saved: list[str] = []

    def load(self, preset_name: str) -> dict:
        if preset_name not in self._presets:
            raise FileNotFoundError(preset_name)
        return self._presets[preset_name]

    def list_names(self) -> list[str]:
        return sorted(self._presets)

    def save(self, preset_name: str, preset: dict) -> None:
        self._presets[preset_name] = preset
        self.saved.append(preset_name)


class _FakeDocuments:
    def __init__(self, documents: dict):
        self._documents = documents

    def load(self, path: str) -> dict:
        if path not in self._documents:
            raise FileNotFoundError(path)
        return self._documents[path]

    def save(self, path, document): raise AssertionError("プロダクトの規約は変更しない")
    def write_text(self, path, text): raise AssertionError("プロダクトの規約は変更しない")
    def link(self, canonical, path): raise AssertionError("使わない")
    def read_text(self, path): raise FileNotFoundError(path)
    def list_json(self, directory): return []
    def list_dirs(self, directory): return []
    def list_files(self, directory, pattern): return []


def _engine(presets=None, documents=None):
    presets = presets if presets is not None else _FakePresets({_PRESET: _preset()})
    documents = documents if documents is not None else _FakeDocuments({_PATH: _document()})
    return UpdateCodingPreset(documents, presets), presets, documents


def test_named_part_is_reflected_into_the_preset():
    """
    Scenario: 指定した部分がプリセットへ反映される
    Given プリセットから作られ、その後に規約を直したプロダクト
    When 直した部分を指定してプリセットへ戻す
    Then プリセットのその部分が、プロダクトの内容と一致する
    """
    engine, presets, _ = _engine()
    result = engine.run(_PRESET, _FROM, ["rules"])
    assert isinstance(result, Ok), result
    assert result.value["changed"] is True
    assert presets.load(_PRESET)["architecture"]["rules"]["items"] == [
        {"level": "必須", "rule": "直した規約"}]


def test_unnamed_parts_are_left_untouched():
    """
    Scenario: 指定しなかった部分は変わらない
    Given プリセットから作られ、その後に複数の箇所を直したプロダクト
    When そのうち1つだけを指定してプリセットへ戻す
    Then 指定しなかった部分はプリセットの元の内容のまま残る
    """
    presets = _FakePresets({_PRESET: _preset()})
    document = _document()
    document["content"]["title"]["title"] = "書き換えたタイトル"
    engine, _, _ = _engine(presets, _FakeDocuments({_PATH: document}))
    result = engine.run(_PRESET, _FROM, ["rules"])
    assert isinstance(result, Ok), result
    assert presets.load(_PRESET)["architecture"]["title"]["title"] == "A"


def test_missing_block_selection_is_rejected():
    """
    Scenario: 戻す部分を指定しないと拒否される
    Given プリセットから作られたプロダクト
    When 戻す部分を指定せずにプリセットへ戻そうとする
    Then 拒否される
    """
    engine, presets, _ = _engine()
    result = engine.run(_PRESET, _FROM, [])
    assert isinstance(result, Err), result
    assert "MISSING_PARAM" in result.details
    assert presets.saved == []


def test_block_absent_from_the_preset_cannot_be_reflected():
    """
    Scenario: プリセットが持たない部分は戻せない
    Given プリセットが持たない項目を持つプロダクトの規約
    When その項目を指定してプリセットへ戻そうとする
    Then 拒否され、プリセットは変わらない
    """
    engine, presets, _ = _engine()
    result = engine.run(_PRESET, _FROM, ["coveredContexts"])
    assert isinstance(result, Err), result
    assert "UNKNOWN_BLOCK" in result.details
    assert presets.saved == []


def test_block_absent_from_the_document_cannot_be_reflected():
    """
    Scenario: プロダクトが持たない部分は戻せない
    Given 指定した部分を持たないプロダクトの規約
    When その部分を指定してプリセットへ戻そうとする
    Then 拒否され、プリセットは変わらない
    """
    document = _document()
    del document["content"]["rules"]
    engine, presets, _ = _engine(_FakePresets({_PRESET: _preset()}),
                                 _FakeDocuments({_PATH: document}))
    result = engine.run(_PRESET, _FROM, ["rules"])
    assert isinstance(result, Err), result
    assert "UNKNOWN_BLOCK" in result.details
    assert presets.saved == []


def test_reflecting_identical_content_changes_nothing():
    """
    Scenario: 同じ内容を戻してもプリセットは変わらない
    Given プリセットとプロダクトで内容が既に一致している部分
    When その部分を指定してプリセットへ戻す
    Then プリセットは変更されず、変更が無かったことが分かる
    """
    engine, presets, _ = _engine()
    result = engine.run(_PRESET, _FROM, ["layout"])
    assert isinstance(result, Ok), result
    assert result.value["changed"] is False
    assert presets.saved == []


def test_reflected_content_is_returned():
    """
    Scenario: 反映した部分の内容が返る
    Given プリセットから作られ、その後に規約を直したプロダクト
    When 直した部分を指定してプリセットへ戻す
    Then 反映した部分について、反映前の内容と反映後の内容が返る
    """
    engine, _, _ = _engine()
    result = engine.run(_PRESET, _FROM, ["rules"])
    assert isinstance(result, Ok), result
    assert result.value["reflected"] == [{
        "block": "rules",
        "before": {"blockType": "Rules", "items": [{"level": "必須", "rule": "古い規約"}]},
        "after": {"blockType": "Rules", "items": [{"level": "必須", "rule": "直した規約"}]},
    }]


def test_confirmation_only_leaves_the_preset_untouched():
    """
    Scenario: 確認だけを求めるとプリセットは変わらない
    Given プリセットから作られ、その後に規約を直したプロダクト
    When 確認だけを求めて、直した部分を指定する
    Then 変わる内容が返り、プリセットは変更されない
    """
    engine, presets, _ = _engine()
    result = engine.run(_PRESET, _FROM, ["rules"], dry_run=True)
    assert isinstance(result, Ok), result
    # 何が変わるかは分かる
    assert [r["block"] for r in result.value["reflected"]] == ["rules"]
    assert result.value["changed"] is True
    # しかし書き換えていない
    assert presets.saved == []
    assert presets.load(_PRESET)["architecture"]["rules"]["items"] == [
        {"level": "必須", "rule": "古い規約"}]
