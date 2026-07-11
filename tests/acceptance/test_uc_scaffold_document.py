"""uc-scaffold-document の受け入れテスト（ネイティブpytest）。"""
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.jsonschema_validator import JsonSchemaValidator
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.scaffold_document import ScaffoldDocument
from waffle.application.usecases.validate_document import ValidateDocument
from waffle.shared.result import Err, Ok

_SKILL_SCHEMA = "SkillSchema/v1"
_TEST_DOC_ID = "test-acceptance-poc-migration"
_TEST_DOC_PATH = f".waffle/documents/skills/{_TEST_DOC_ID}.json"
_CUSTOM_DOC_ID = "test-acceptance-scaffold-custom"
_CUSTOM_DOC_PATH = f".waffle/documents/skills/{_CUSTOM_DOC_ID}.json"
_TEMPLATE_SCHEMA = "TemplateSchema/v1"
_TEMPLATE_DOC_ID = "test-acceptance-scaffold-template"
_TEMPLATE_DOC_PATH = f".waffle/documents/templates/{_TEMPLATE_DOC_ID}.json"


def _engine() -> ScaffoldDocument:
    return ScaffoldDocument(FsDocumentRepository(), PackageSchemaRepository())


def setup_function():
    Path(_TEST_DOC_PATH).unlink(missing_ok=True)
    Path(_CUSTOM_DOC_PATH).unlink(missing_ok=True)
    Path(_TEMPLATE_DOC_PATH).unlink(missing_ok=True)


def teardown_function():
    Path(_TEST_DOC_PATH).unlink(missing_ok=True)
    Path(_CUSTOM_DOC_PATH).unlink(missing_ok=True)
    Path(_TEMPLATE_DOC_PATH).unlink(missing_ok=True)


def test_生成した骨格は自分の_schema_で_valid():
    """
    Given advisor 種別の Document（discriminator 指定済み）
    When create する
    Then 骨格は schema に適合し、status は schema の初期値である
    """
    result = _engine().run(
        "create",
        {"schemaRef": _SKILL_SCHEMA, "documentId": _TEST_DOC_ID, "discriminator": {"skillKind": "advisor"}},
    )
    assert isinstance(result, Ok), result
    assert result.value["skeleton"]["status"] == "DRAFT"

    validate_result = ValidateDocument(
        FsDocumentRepository(), PackageSchemaRepository(), JsonSchemaValidator()
    ).run(result.value["path"])
    assert isinstance(validate_result, Ok), getattr(validate_result, "details", validate_result)


def test_構造を変える値は拒否される():
    """
    Given 作成済みの Document
    When const フィールドへ値を書き込もうとする
    Then 書き込まれず skipped に記録される
    """
    create_result = _engine().run(
        "create",
        {"schemaRef": _SKILL_SCHEMA, "documentId": _TEST_DOC_ID, "discriminator": {"skillKind": "advisor"}},
    )
    assert isinstance(create_result, Ok), create_result

    fill_result = _engine().run(
        "fill",
        {"documentPath": create_result.value["path"], "values": {"documentType": "Hacked"}},
    )
    assert isinstance(fill_result, Ok), fill_result
    assert "documentType" in fill_result.value["skipped"]


def test_宣言済みの値フィールドに書き込まれる():
    """
    Given 作成済みの Document
    When 宣言済みの値フィールドへ値を書き込む
    Then written に記録され、ファイルに反映される
    """
    create_result = _engine().run(
        "create",
        {"schemaRef": _SKILL_SCHEMA, "documentId": _TEST_DOC_ID, "discriminator": {"skillKind": "advisor"}},
    )
    assert isinstance(create_result, Ok), create_result

    fill_result = _engine().run(
        "fill",
        {"documentPath": create_result.value["path"], "values": {"content.purpose.text": "ドメインを分析する"}},
    )
    assert isinstance(fill_result, Ok), fill_result
    assert "content.purpose.text" in fill_result.value["written"]

    doc = FsDocumentRepository().load(create_result.value["path"])
    assert doc["content"]["purpose"]["text"] == "ドメインを分析する"


def test_discriminator_が無いと候補を案内する():
    """
    Given 分岐のある schema
    When discriminator を指定せずに create する
    Then MISSING_DISCRIMINATOR エラーが候補つきで返る
    """
    result = _engine().run("create", {"schemaRef": _SKILL_SCHEMA, "documentId": _TEST_DOC_ID})
    assert isinstance(result, Err), result
    assert result.details[0] == "MISSING_DISCRIMINATOR"



def test_createはadvisor_skillの骨格を生成する():
    """
    Given schemaRef, documentId, discriminator(skillKind=advisor)
    When createを実行する
    Then documentType/schemaRef/skillKind/statusが正しく設定され、content配下にresponseTypes/knowledgeRefsがある骨格が生成される
    """
    result = _engine().run(
        "create",
        {"schemaRef": _SKILL_SCHEMA, "documentId": _TEST_DOC_ID, "discriminator": {"skillKind": "advisor"}},
    )
    assert isinstance(result, Ok), result
    skeleton = result.value["skeleton"]
    assert skeleton["documentType"] == "Skill"
    assert skeleton["schemaRef"] == _SKILL_SCHEMA
    assert skeleton["skillKind"] == "advisor"
    assert skeleton["status"] == "DRAFT"
    assert "responseTypes" in skeleton["content"]
    assert "knowledgeRefs" in skeleton["content"]


def test_createはx_source_targetに骨格を書き出す():
    """
    Given schemaRef, documentId, discriminator
    When createを実行する
    Then schemaのx-source-target宣言どおりのパスにファイルが書き出される
    """
    result = _engine().run(
        "create",
        {"schemaRef": _SKILL_SCHEMA, "documentId": _TEST_DOC_ID, "discriminator": {"skillKind": "advisor"}},
    )
    assert isinstance(result, Ok), result
    assert Path(_TEST_DOC_PATH).exists()


def test_fillTemplateは値フィールドのpathとprompt_x_prompt_writeを持つ():
    """
    Given schemaRef, documentId, discriminator
    When createを実行する
    Then fillTemplateには値フィールドのpathとx-prompt-write由来のpromptを持つエントリが含まれる
    """
    result = _engine().run(
        "create",
        {"schemaRef": _SKILL_SCHEMA, "documentId": _TEST_DOC_ID, "discriminator": {"skillKind": "advisor"}},
    )
    assert isinstance(result, Ok), result
    entries = {e["path"]: e for e in result.value["fillTemplate"]}
    assert "content.purpose.text" in entries
    assert entries["content.purpose.text"]["prompt"]


def test_createはCLIから渡されたrefパラメータをdocument本体にも反映する():
    """
    Given schemaが宣言する任意のトップレベルフィールド(subdomainRef等)に対応するCLIパラメータ
    When createを実行する
    Then そのパラメータはパス計算だけでなくdocument本体にも書き込まれる
    （--subdomainRefを渡してもcreate直後のdocument.jsonにsubdomainRefが無い、という
    このセッション中に繰り返し起きた不具合の再発防止）
    """
    result = _engine().run(
        "create",
        {
            "schemaRef": "DomainSpecSchema/v4",
            "documentId": "test-acceptance-scaffold-subdomain-ref",
            "discriminator": {"specKind": "usecase"},
            "contextRef": "bc-waffle",
            "subdomainRef": "sd-reconciliation",
        },
    )
    assert isinstance(result, Ok), result
    assert result.value["skeleton"]["subdomainRef"] == "sd-reconciliation"
    Path(result.value["path"]).unlink(missing_ok=True)


def test_fillTemplateにはcontent外のトップレベルのx_prompt_writeフィールドも含まれる():
    """
    Given content外にx-prompt-writeを持つトップレベルフィールド(skillRef)を宣言するschema
    When createを実行する
    Then fillTemplateにcontent.以外のパス(skillRef)のエントリが含まれる
    """
    result = _engine().run(
        "create",
        {"schemaRef": _TEMPLATE_SCHEMA, "documentId": _TEMPLATE_DOC_ID, "discriminator": {"templateKind": "judgment"}},
    )
    assert isinstance(result, Ok), result
    entries = {e["path"]: e for e in result.value["fillTemplate"]}
    assert "skillRef" in entries
    assert entries["skillRef"]["prompt"]


def test_fillはcontent外のトップレベルのx_prompt_writeフィールドにも書き込める():
    """
    Given 作成済みのDocument
    When content外のトップレベルフィールド(skillRef)へ値を書き込む
    Then written に記録され、ファイルに反映される
    """
    create_result = _engine().run(
        "create",
        {"schemaRef": _TEMPLATE_SCHEMA, "documentId": _TEMPLATE_DOC_ID, "discriminator": {"templateKind": "judgment"}},
    )
    assert isinstance(create_result, Ok), create_result

    fill_result = _engine().run(
        "fill",
        {"documentPath": create_result.value["path"], "values": {"skillRef": "qa-advisor"}},
    )
    assert isinstance(fill_result, Ok), fill_result
    assert "skillRef" in fill_result.value["written"]

    doc = FsDocumentRepository().load(create_result.value["path"])
    assert doc["skillRef"] == "qa-advisor"


def test_fillはdocumentIdとdiscriminatorキーへの書き込みを拒否する():
    """
    Given 作成済みのDocument
    When documentId・discriminatorキー(templateKind)へ値を書き込もうとする
    Then 書き込まれずskippedに記録される(識別子・構造分岐は書き換え禁止)
    """
    create_result = _engine().run(
        "create",
        {"schemaRef": _TEMPLATE_SCHEMA, "documentId": _TEMPLATE_DOC_ID, "discriminator": {"templateKind": "judgment"}},
    )
    assert isinstance(create_result, Ok), create_result

    fill_result = _engine().run(
        "fill",
        {"documentPath": create_result.value["path"], "values": {"documentId": "hacked", "templateKind": "hacked"}},
    )
    assert isinstance(fill_result, Ok), fill_result
    assert "documentId" in fill_result.value["skipped"]
    assert "templateKind" in fill_result.value["skipped"]


def test_customはadvisorと構成が異なる():
    """
    Given discriminator(skillKind=custom)
    When createを実行する
    Then advisorとは異なりcontent配下にprocessingTargetを持つ骨格が生成される
    """
    result = _engine().run(
        "create",
        {"schemaRef": _SKILL_SCHEMA, "documentId": _CUSTOM_DOC_ID, "discriminator": {"skillKind": "custom"}},
    )
    assert isinstance(result, Ok), result
    assert "processingTarget" in result.value["skeleton"]["content"]


