"""uc-render-document の受け入れテスト（ネイティブpytest）。"""
import json
import tempfile

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.render_document import RenderDocument
from waffle.shared.result import Err, Ok


def _engine() -> RenderDocument:
    return RenderDocument(FsDocumentRepository(), PackageSchemaRepository())


def test_検証済み_Document_を成果物に描画する():
    """
    Given 描画対象の Document
    When render する
    Then 成果物が生成され、生成パス一覧が返る
    """
    result = _engine().run(".waffle/documents/skills/tech-lead-advisor.json", deploy=False)
    assert isinstance(result, Ok), result
    assert result.value["format"] == "md"
    assert "# コード配置・レイヤー境界・依存方向の判断を担うadvisor Skill：tech-lead-advisor" in result.value["content"]


def test_schemaRef_を持たない_Document_は描画しない():
    """
    Given schemaRef の無い Document
    When render する
    Then MISSING_SCHEMA_REF エラーが返る
    """
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"documentId": "no-schema-ref"}, f)
        path = f.name

    result = _engine().run(path, deploy=False)
    assert isinstance(result, Err), result
    assert result.details[0] == "MISSING_SCHEMA_REF"



def test_deploy_すると_canonical_と_deploy_先の両方に書く(tmp_path):
    """
    Given deploy 先を持つ Document
    When deploy を有効にして render する
    Then canonical と deploy 先の両方に成果物が書かれる
    """
    schema = {
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "path": str(tmp_path / "canonical" / "{documentId}.md"),
            "deploy": [str(tmp_path / "deploy" / "{documentId}.md")],
        },
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({"documentId": "x", "schemaRef": "Fake/v1", "content": {}}),
        encoding="utf-8",
    )

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=True)
    assert isinstance(result, Ok), result
    assert result.value["path"] == str(tmp_path / "canonical" / "x.md")
    assert str(tmp_path / "deploy" / "x.md") in result.value["deployed"]


class _ConfigStubDocumentRepository:
    """.waffle/config.json の読み出しだけ差し替え、他は実FSへ委譲する（toolMappings経由のsymlink解決テスト用）。"""

    def __init__(self, real: FsDocumentRepository, config_json: str) -> None:
        self._real = real
        self._config_json = config_json

    def read_text(self, path: str) -> str:
        if path == ".waffle/config.json":
            return self._config_json
        return self._real.read_text(path)

    def write_text(self, path: str, text: str) -> None:
        self._real.write_text(path, text)

    def link(self, canonical: str, path: str) -> None:
        self._real.link(canonical, path)

    def load(self, path: str) -> dict:
        return self._real.load(path)


def test_配列のpathVarはtoolMappings経由のdeploy先へfan_outする(tmp_path):
    """
    Given toolMappingsのpathTemplateが参照するpathVarの値が配列であるDocument
    When deployを有効にしてrenderする
    Then 配列の要素ごとに1つずつsymlinkのdeploy先が作られる
    """
    schema = {
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "path": str(tmp_path / "canonical" / "{documentId}.md"),
            "pathVars": {"skillRefs": "doc.skillRefs"},
        },
    }
    config_json = json.dumps({
        "toolMappings": {
            "claude-code": {
                "FakeMulti": {"pathTemplate": str(tmp_path / "links" / "{skillRefs}" / "{documentId}.md"), "mode": "symlink"}
            }
        }
    })
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({
            "documentId": "x", "schemaRef": "Fake/v1", "documentType": "FakeMulti",
            "skillRefs": ["advisor-a", "advisor-b"], "content": {},
        }),
        encoding="utf-8",
    )

    repo = _ConfigStubDocumentRepository(FsDocumentRepository(), config_json)
    engine = RenderDocument(repo, _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=True)
    assert isinstance(result, Ok), result
    assert str(tmp_path / "links" / "advisor-a" / "x.md") in result.value["deployed"]
    assert str(tmp_path / "links" / "advisor-b" / "x.md") in result.value["deployed"]
    assert (tmp_path / "links" / "advisor-a" / "x.md").is_symlink()
    assert (tmp_path / "links" / "advisor-b" / "x.md").is_symlink()


def test_toolMappingsがdiscriminatorごとに入れ子で宣言されているときは対応するマッピングだけを使う(tmp_path):
    """
    Given .waffle/config.jsonのtoolMappingsが対象documentTypeについてdiscriminatorの値ごとの入れ子マッピングを持つDocument
    When deployを有効にしてrenderする
    Then そのDocumentのdiscriminator値に対応するマッピングのdeploy先だけに書かれる
    """
    schema = {
        "if": {"properties": {"kind": {"const": "a"}}},
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "path": str(tmp_path / "canonical" / "{documentId}.md"),
        },
    }
    config_json = json.dumps({
        "toolMappings": {
            "claude-code": {
                "FakeMulti": {
                    "a": {"pathTemplate": str(tmp_path / "deploy-a" / "{documentId}.md"), "mode": "symlink"},
                    "b": {"pathTemplate": str(tmp_path / "deploy-b" / "{documentId}.md"), "mode": "symlink"},
                }
            }
        }
    })
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({
            "documentId": "x", "schemaRef": "Fake/v1", "documentType": "FakeMulti",
            "kind": "a", "content": {},
        }),
        encoding="utf-8",
    )

    repo = _ConfigStubDocumentRepository(FsDocumentRepository(), config_json)
    engine = RenderDocument(repo, _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=True)
    assert isinstance(result, Ok), result
    assert str(tmp_path / "deploy-a" / "x.md") in result.value["deployed"]
    assert str(tmp_path / "deploy-b" / "x.md") not in result.value["deployed"]
    assert (tmp_path / "deploy-a" / "x.md").is_symlink()


def test_AgentのtoolMappingsが入れ子化されてもorchestratorとsubagentで別々のdeploy先に解決される(tmp_path):
    """
    Given toolMappings.claude-code.AgentがagentKindごとの入れ子マッピング（orchestrator/subagent）を持つDocument
    When agentKind=orchestratorとagentKind=subagentのそれぞれをdeployを有効にしてrenderする
    Then orchestratorはCLAUDE.md相当のパスへ、subagentは.claude/agents/{documentId}.md相当のパスへ、それぞれ別々に解決される
    （実config.jsonのclaude-code.Agentをフラット→入れ子構造へ移行しても、既存のorchestrator系documentの
    deploy先が変わらないことを保証する回帰テスト）
    """
    schema = {
        "if": {"properties": {"agentKind": {"const": "orchestrator"}}},
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "path": str(tmp_path / "canonical" / "{documentId}.md"),
        },
    }
    config_json = json.dumps({
        "toolMappings": {
            "claude-code": {
                "Agent": {
                    "orchestrator": {"pathTemplate": str(tmp_path / "CLAUDE.md"), "mode": "symlink"},
                    "subagent": {"pathTemplate": str(tmp_path / "agents" / "{documentId}.md"), "mode": "symlink"},
                }
            }
        }
    })

    def _run(agent_kind: str, document_id: str) -> Ok:
        doc_path = tmp_path / f"{document_id}.json"
        doc_path.write_text(
            json.dumps({
                "documentId": document_id, "schemaRef": "Fake/v1", "documentType": "Agent",
                "agentKind": agent_kind, "content": {},
            }),
            encoding="utf-8",
        )
        repo = _ConfigStubDocumentRepository(FsDocumentRepository(), config_json)
        engine = RenderDocument(repo, _FakeSchemaRepository(schema))
        result = engine.run(str(doc_path), deploy=True)
        assert isinstance(result, Ok), result
        return result

    orchestrator_result = _run("orchestrator", "waffle")
    assert str(tmp_path / "CLAUDE.md") in orchestrator_result.value["deployed"]

    subagent_result = _run("subagent", "waffle-subagent")
    assert str(tmp_path / "agents" / "waffle-subagent.md") in subagent_result.value["deployed"]
    assert str(tmp_path / "CLAUDE.md") not in subagent_result.value["deployed"]


def test_入れ子のtoolMappingsに含まれないdiscriminator値はdeployされない(tmp_path):
    """
    Given documentType向けのtoolMappingsが入れ子だが、対象Documentのdiscriminator値に対応するキーを持たない
    When deployを有効にしてrenderする
    Then そのtoolのdeploy先には何も書かれない（他のdiscriminator値へのdeploy先を誤って共有しない）

    実装時に発見した回帰: .waffle/config.jsonのtoolMappings.codex.Agentがフラット
    （{"pathTemplate": "AGENTS.md", ...}）のまま残っていたため、agentKind=subagentの
    document（本来はcodex向けdeploy対象外）もAGENTS.mdへdeployされ、既存のagentKind=orchestrator
    向けAGENTS.mdシンボリックリンクを誤って上書きした。この回帰を防ぐため、入れ子マッピングに
    存在しないdiscriminator値は明示的に対象外になることを確認する。
    """
    schema = {
        "if": {"properties": {"agentKind": {"const": "orchestrator"}}},
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "path": str(tmp_path / "canonical" / "{documentId}.md"),
        },
    }
    config_json = json.dumps({
        "toolMappings": {
            "codex": {
                "Agent": {
                    "orchestrator": {"pathTemplate": str(tmp_path / "AGENTS.md"), "mode": "symlink"},
                }
            }
        }
    })
    doc_path = tmp_path / "waffle-subagent.json"
    doc_path.write_text(
        json.dumps({
            "documentId": "waffle-subagent", "schemaRef": "Fake/v1", "documentType": "Agent",
            "agentKind": "subagent", "content": {},
        }),
        encoding="utf-8",
    )

    repo = _ConfigStubDocumentRepository(FsDocumentRepository(), config_json)
    engine = RenderDocument(repo, _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=True)
    assert isinstance(result, Ok), result
    assert result.value["deployed"] == []
    assert not (tmp_path / "AGENTS.md").exists()


class _FakeSchemaRepository:
    def __init__(self, schema: dict) -> None:
        self._schema = schema

    def load(self, schema_ref: str) -> dict:
        return self._schema

    def list_versions(self, name: str) -> list[str]:
        return []


def test_discriminatorごとに異なるdeploy先へ書き分ける(tmp_path):
    """
    Given deploy先がdiscriminatorの値ごとに異なる配列として宣言されたschemaのDocument
    When deployを有効にしてrenderする
    Then そのDocumentのdiscriminator値に対応する配列のdeploy先だけに書かれる
    """
    schema = {
        "if": {"properties": {"kind": {"const": "a"}}},
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "path": {"a": str(tmp_path / "canonical-a.md"), "b": str(tmp_path / "canonical-b.md")},
            "deploy": {"a": [str(tmp_path / "deploy-a.md")], "b": [str(tmp_path / "deploy-b.md")]},
        },
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({"documentId": "x", "schemaRef": "Fake/v1", "kind": "a", "content": {}}),
        encoding="utf-8",
    )

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=True)
    assert isinstance(result, Ok), result
    assert result.value["path"] == str(tmp_path / "canonical-a.md")
    assert str(tmp_path / "deploy-a.md") in result.value["deployed"]
    assert str(tmp_path / "deploy-b.md") not in result.value["deployed"]


def test_pathVarsで宣言したcontent値をパステンプレートの変数として使う(tmp_path):
    """
    Given x-render-target.pathVarsでcontentのドットパスを宣言したschemaのDocument
    When renderする
    Then そのcontent値がパステンプレートの変数として解決され、対応するパスに書かれる
    """
    schema = {
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "pathVars": {"scope": "doc.content.scope.path"},
            "path": str(tmp_path / "{scope}-canonical.md"),
            "deploy": [str(tmp_path / "{scope}-deploy.md")],
        },
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({
            "documentId": "x", "schemaRef": "Fake/v1",
            "content": {"scope": {"blockType": "Scope", "title": "scope", "path": "waffle"}},
        }),
        encoding="utf-8",
    )

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=True)
    assert isinstance(result, Ok), result
    assert result.value["path"] == str(tmp_path / "waffle-canonical.md")
    assert str(tmp_path / "waffle-deploy.md") in result.value["deployed"]


def test_pathVarsが解決できないdeploy先はスキップしcanonicalへは書く(tmp_path):
    """
    Given x-render-target.pathVarsが参照するcontentのドットパスを持たないDocument
    When renderする
    Then canonicalへは書かれるが、解決できないdeploy先はクラッシュせずスキップされる
    """
    schema = {
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "pathVars": {"skillRef": "doc.skillRef"},
            "path": str(tmp_path / "{documentId}.md"),
            "deploy": [str(tmp_path / "{skillRef}" / "{documentId}.md")],
        },
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({"documentId": "x", "schemaRef": "Fake/v1", "content": {}}),
        encoding="utf-8",
    )

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=True)
    assert isinstance(result, Ok), result
    assert result.value["path"] == str(tmp_path / "x.md")
    assert result.value["deployed"] == []


def test_discriminatorごとに異なるpathVarsを解決する(tmp_path):
    """
    Given discriminatorの値ごとに異なるpathVars宣言（kindごとの変数マップ）を持つschemaのDocument
    When renderする
    Then そのDocumentのdiscriminator値に対応する変数マップだけが解決され、パステンプレートに反映される
    """
    schema = {
        "if": {"properties": {"kind": {"const": "orchestrator"}}},
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {
            "formats": ["md"],
            "pathVars": {
                "orchestrator": {"scope": "doc.content.scope.path"},
                "subagent": {},
            },
            "path": str(tmp_path / "{documentId}.md"),
            "deploy": {
                "orchestrator": [str(tmp_path / "{scope}-CLAUDE.md")],
                "subagent": [str(tmp_path / "agents" / "{documentId}.md")],
            },
        },
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({
            "documentId": "x", "schemaRef": "Fake/v1", "kind": "orchestrator",
            "content": {"scope": {"blockType": "Scope", "title": "scope", "path": "waffle"}},
        }),
        encoding="utf-8",
    )

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=True)
    assert isinstance(result, Ok), result
    assert str(tmp_path / "waffle-CLAUDE.md") in result.value["deployed"]

    doc_path2 = tmp_path / "doc2.json"
    doc_path2.write_text(
        json.dumps({"documentId": "y", "schemaRef": "Fake/v1", "kind": "subagent", "content": {}}),
        encoding="utf-8",
    )
    result2 = engine.run(str(doc_path2), deploy=True)
    assert isinstance(result2, Ok), result2
    assert str(tmp_path / "agents" / "y.md") in result2.value["deployed"]


def test_discriminatorごとに異なるx_frontmatterを生成する(tmp_path):
    """
    Given discriminatorの値ごとに異なるx-frontmatter宣言（kindごとのフィールドマップ）を持つschemaのDocument
    When renderする
    Then そのDocumentのdiscriminator値に対応するフィールドマップだけからfrontmatterが生成される
    """
    schema = {
        "if": {"properties": {"kind": {"const": "subagent"}}},
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-frontmatter": {
            "subagent": {"name": "doc.documentId", "description": "doc.content.description.text"},
            "orchestrator": {},
        },
        "x-render-target": {"formats": ["md"], "path": str(tmp_path / "{documentId}.md")},
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({
            "documentId": "x", "schemaRef": "Fake/v1", "kind": "subagent",
            "content": {"description": {"blockType": "Description", "title": "d", "text": "when to use"}},
        }),
        encoding="utf-8",
    )

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=False)
    assert isinstance(result, Ok), result
    assert 'name: "x"' in result.value["content"]
    assert 'description: "when to use"' in result.value["content"]

    doc_path2 = tmp_path / "doc2.json"
    doc_path2.write_text(
        json.dumps({"documentId": "y", "schemaRef": "Fake/v1", "kind": "orchestrator", "content": {}}),
        encoding="utf-8",
    )
    result2 = engine.run(str(doc_path2), deploy=False)
    assert isinstance(result2, Ok), result2
    assert "---" not in result2.value["content"]


def test_存在しないx_frontmatterのドットパスは省略する(tmp_path):
    """
    Given x-frontmatterが宣言するドットパスに対応するcontentブロックを持たない、または値が空であるDocument
    When renderする
    Then そのフィールドはfrontmatterから省略される
    """
    schema = {
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-frontmatter": {
            "name": "doc.documentId",
            "model": "doc.content.runtimeConfig.model",
            "permissionMode": "doc.content.runtimeConfig.permissionMode",
        },
        "x-render-target": {"formats": ["md"], "path": str(tmp_path / "{documentId}.md")},
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({
            "documentId": "x", "schemaRef": "Fake/v1",
            "content": {"runtimeConfig": {"blockType": "RuntimeConfig", "title": "t", "permissionMode": ""}},
        }),
        encoding="utf-8",
    )

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=False)
    assert isinstance(result, Ok), result
    assert 'name: "x"' in result.value["content"]
    assert "model" not in result.value["content"]
    assert "permissionMode" not in result.value["content"]


def test_x_frontmatterが指すブロックがitemsを持つときスペース区切りで結合する(tmp_path):
    """
    Given x-frontmatterが指すドットパスの解決値が、text/itemsを持つブロック形状のdict
      （DomainSpecSchemaのSummaryBlock等、箇条書きitemsで概要を持つ形）であるDocument
    When renderする
    Then textが無い場合はitemsを半角スペースで結合した1つの文字列がfrontmatter値になる
    """
    schema = {
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-frontmatter": {"description": "doc.content.description"},
        "x-render-target": {"formats": ["md"], "path": str(tmp_path / "{documentId}.md")},
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(
        json.dumps({
            "documentId": "x", "schemaRef": "Fake/v1",
            "content": {"description": {"blockType": "Summary", "title": "概要", "items": ["論点1です", "論点2です"]}},
        }),
        encoding="utf-8",
    )

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=False)
    assert isinstance(result, Ok), result
    assert 'description: "論点1です 論点2です"' in result.value["content"]


def test_DomainSpecSchemaのusecase_Specはfrontmatterでid_type_title_description_tagsを持つ():
    """
    Given usecase specKindのDomainSpecSchema Document
    When renderする
    Then document-graph Skillの契約（id/type/title/description/tags）に沿ったfrontmatterが出力される
    """
    result = _engine().run(
        ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        deploy=False,
    )
    assert isinstance(result, Ok), result
    content = result.value["content"]
    assert content.startswith("---\n")
    assert 'id: "uc-query-document"' in content
    assert 'type: "usecase"' in content
    assert "title:" in content
    assert "description:" in content


def test_SkillSchemaをMarkdownにレンダリングする():
    """
    Given SkillSchemaのDocument
    When renderする
    Then 見出し・目的・相談種別テーブル・実行手順・参照knowledgeが全て出力に含まれる
    """
    result = _engine().run(".waffle/documents/skills/tech-lead-advisor.json", deploy=False)
    assert isinstance(result, Ok), result
    content = result.value["content"]
    assert "# コード配置・レイヤー境界・依存方向の判断を担うadvisor Skill：tech-lead-advisor" in content
    assert "## 目的" in content
    assert "| 相談種別 | 判定条件 | テンプレート |" in content
    assert "### Step 1: サブドメイン分類を確認する" in content
    assert "## 参照knowledge" in content


def test_frontmatterはx_frontmatterのドットパスを解決して生成する():
    """
    Given x-frontmatterを宣言するSchemaのDocument
    When renderする
    Then 出力冒頭にname/description等を含むYAML frontmatterが生成される
    """
    result = _engine().run(".waffle/documents/skills/tech-lead-advisor.json", deploy=False)
    assert isinstance(result, Ok), result
    content = result.value["content"]
    assert "name:" in content
    assert "description:" in content
    assert "tech-lead-advisor" in content


def test_CodingSchemaはMarkdownとして描画できる():
    """
    Given CodingSchemaのDocument
    When renderする
    Then Markdown形式で見出しを含む出力が生成される
    """
    result = _engine().run(".waffle/documents/coding/tech-stack-waffle.json", deploy=False)
    assert isinstance(result, Ok), result
    assert result.value["format"] == "md"
    assert "# " in result.value["content"]


def test_usecase_Specは基本フローをシーケンス図に受け入れシナリオをMarkdownに出す():
    """
    Given usecase SpecのDocument
    When renderする
    Then 出力にmermaidのsequenceDiagramとテストシナリオ節が含まれる
    """
    result = _engine().run(
        ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-query-document.json",
        deploy=False,
    )
    assert isinstance(result, Ok), result
    content = result.value["content"]
    assert result.value["format"] == "md"
    assert "：QueryDocument" in content
    assert "sequenceDiagram" in content
    assert "mermaid" in content
    assert "## 受け入れシナリオ" in content
    assert "Scenario: 未知の operation はエラーを返す" in content


def test_aggregate_Specは集約の構造とライフサイクルをMarkdownに出す():
    """
    Given aggregate SpecのDocument
    When renderする
    Then 出力にコマンド節・ドメインイベント名・mermaidのstateDiagram-v2が含まれる
    """
    result = _engine().run(
        ".waffle/documents/specs/bc-waffle/aggregate/agg-document.json", deploy=False,
    )
    assert isinstance(result, Ok), result
    content = result.value["content"]
    assert "## コマンド" in content
    assert "DocumentRendered" in content
    assert "stateDiagram-v2" in content


def test_配列値の列をbullet指定でセル内改行の箇条書きにする():
    """
    Given bullet:trueを宣言する列を持つtable部品と、その対象フィールドが複数要素の配列であるDocument
    When renderする
    Then そのセルは各要素が<br>で区切られた箇条書きとして描画される
    """
    result = _engine().run(
        ".waffle/documents/specs/bc-waffle/subdomain/sd-schema-management/usecase/uc-patch-schema.json", deploy=False,
    )
    assert isinstance(result, Ok), result
    content = result.value["content"]
    assert "<br>- " in content
    assert "- add_kind_branchの対象となるルート直下のkind分岐が、既知の形状（if/then/else形式・allOf形式）に適合しない" in content
    assert "- if/then/else形式でありながら、elseの暗黙値を一意に逆算できない" in content


def test_bulletとjoin_sepが同時指定されたときbulletを優先する(tmp_path):
    """
    Given bulletとjoin/sepの両方を宣言する列を持つtable部品
    When renderする
    Then join/sepによる1行連結ではなくbulletによる箇条書きが描画される
    """
    schema = {
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {"formats": ["md"], "path": str(tmp_path / "{documentId}.md")},
        "$defs": {
            "RowsBlock": {
                "x-render-level": 2,
                "x-render": [{
                    "as": "table", "from": "items",
                    "columns": [{
                        "field": "attributes", "header": "属性",
                        "bullet": True, "join": "{name}: {type}", "sep": " / ",
                    }],
                }],
            },
        },
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(json.dumps({
        "documentId": "x", "schemaRef": "Fake/v1",
        "content": {"rows": {
            "blockType": "Rows", "title": "行",
            "items": [{"attributes": [
                {"name": "status", "type": "OrderStatus"},
                {"name": "total", "type": "Money"},
            ]}],
        }},
    }), encoding="utf-8")

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=False)
    assert isinstance(result, Ok), result
    content = result.value["content"]
    assert "status: OrderStatus / total: Money" not in content


def test_配列を期待する部品が配列でない値を受け取るとMALFORMED_CONTENTを返す(tmp_path):
    """
    Given listを宣言する部品に対応するcontent値が配列でなく文字列であるDocument
    When renderする
    Then MALFORMED_CONTENTエラーが返り、成果物は書き出されない
    """
    schema = {
        "properties": {"content": {"type": "object", "properties": {}}},
        "x-render-target": {"formats": ["md"], "path": str(tmp_path / "{documentId}.md")},
        "$defs": {
            "GuardrailsBlock": {
                "x-render-level": 2,
                "x-render": [{"as": "list", "from": "items"}],
            },
        },
    }
    doc_path = tmp_path / "doc.json"
    doc_path.write_text(json.dumps({
        "documentId": "x", "schemaRef": "Fake/v1",
        "content": {"guardrails": {
            "blockType": "Guardrails", "title": "ガードレール",
            "items": "配列でない文字列",
        }},
    }), encoding="utf-8")

    engine = RenderDocument(FsDocumentRepository(), _FakeSchemaRepository(schema))
    result = engine.run(str(doc_path), deploy=False)
    assert isinstance(result, Err), result
    assert result.details[0] == "MALFORMED_CONTENT"
    assert not (tmp_path / "x.md").exists()


def test_未検証ではrenderできない():
    """
    Given schemaがrenderをVALIDATED起点の遷移として宣言しているのに、CREATED状態のDocument
    When renderする
    Then INVALID_TRANSITIONエラーが返り、成果物は書き出されない
    """
    doc = {
        "documentId": "unvalidated-spec",
        "documentType": "DomainSpec",
        "schemaRef": "DomainSpecSchema/v2",
        "specKind": "bounded-context",
        "status": "CREATED",
        "content": {},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(doc, f)
        path = f.name

    result = _engine().run(path, deploy=False)
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_TRANSITION"


def test_x_render_targetを持たないschemaはNO_RENDER_TARGETを返す():
    """
    Given x-render-target.pathを宣言していないschemaのDocument
    When renderを実行する
    Then NO_RENDER_TARGETエラーが返り描画されない
    """
    result = _engine().run(".waffle/documents/handoff/handoff-concept-source-root-resolution.json", deploy=False)
    assert isinstance(result, Err), result
    assert result.details[0] == "NO_RENDER_TARGET"


def test_不正なJSONはINVALID_JSON():
    """
    Given 不正なJSONの対象ファイル
    When renderする
    Then INVALID_JSONエラーが返る
    """
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write("{not valid json")
        path = f.name

    result = _engine().run(path, deploy=False)
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_JSON"
