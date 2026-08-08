"""lint docstring — 対象コードベースの docstring が規約どおりの構造か
（必須セクションの有無・引数名と実シグネチャの整合）を、既存 lint ツールを
呼び出して判定する application use case。自前の照合ロジックは持たない。

どの構文で判定するかを決める権限は規約にある。この操作は規約のdocstringブロックが
宣言する綴りを読み、既存lintツールが知っている流儀へ写すだけにする。写せない宣言を
黙って既定へ倒すと、宣言できるが効かない欄が残る。

MISSING_DOC_COMMENT は uc-scan-source-code の結果（hasDocstring）から導出し、
ARGS_MISMATCH は DocstringLinter port（kind ごとの既存lintツール）に委ねる。
"""
from __future__ import annotations

import json

from waffle.application.ports.docstring_linter import DocstringLinter, ToolNotAvailable
from waffle.application.ports.docstring_linter import UnsupportedKind as LinterUnsupportedKind
from waffle.application.usecases.scan_source_code import ScanSourceCode
from waffle.domain.services.docstring_syntax import kind_for
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class LintDocstring:
    """docstringが規約どおりの形をしているかを確かめる。"""
    def __init__(self, scan_source_code: ScanSourceCode, linter: DocstringLinter) -> None:
        self._scan_source_code = scan_source_code
        self._linter = linter

    def _declared_syntax(self, standard_ref: str) -> Result[dict]:
        """規約が宣言する docstring の構文を読む。

        Args:
            standard_ref: 規約のdocumentの置き場所。

        Returns:
            syntaxKindとタグ3欄を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        try:
            with open(standard_ref, encoding="utf-8") as f:
                document = json.load(f)
        except (OSError, json.JSONDecodeError):
            return _err("INVALID_PATH", f"規約が読めません: {standard_ref}")
        block = document.get("content", {}).get("docstring")
        if not block:
            return _err("INVALID_PATH", f"規約がdocstringを宣言していません: {standard_ref}")
        return Ok(block)

    def run(self, target_path: str, standard_ref: str) -> Result[list[dict]]:
        """docstringが規約どおりの形をしているかを確かめる。

        Args:
            target_path: 確かめる対象のコードベースの置き場所。
            standard_ref: どの構文で判定するかを宣言している規約の置き場所。

        Returns:
            違反の一覧を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        declared = self._declared_syntax(standard_ref)
        if isinstance(declared, Err):
            return declared
        block = declared.value

        kind = kind_for(block.get("syntaxKind", ""), block.get("tagParams", ""),
                        block.get("tagReturns", ""), block.get("tagRaises", ""))
        if kind is None:
            return _err(
                "UNSUPPORTED_SYNTAX",
                "規約が宣言する構文へ、対応する既存lintツールが追随できません"
                f"（{block.get('syntaxKind')} / {block.get('tagParams')} / "
                f"{block.get('tagReturns')} / {block.get('tagRaises')}）")

        scan_result = self._scan_source_code.run(target_path, kind)
        if isinstance(scan_result, Err):
            return scan_result

        violations = [
            {
                "path": e["path"], "elementKind": e["elementKind"], "name": e["name"],
                "code": "MISSING_DOC_COMMENT", "detail": "docstringがありません",
            }
            for e in scan_result.value
            if not e["hasDocstring"] and e["elementKind"] != "module"
        ]

        try:
            violations.extend(self._linter.lint(target_path, kind))
        except LinterUnsupportedKind:
            return _err("UNSUPPORTED_KIND", f"対応していないkindです: {kind}")
        except ToolNotAvailable as e:
            return _err("TOOL_NOT_AVAILABLE", f"lintツールが実行環境にありません: {e}")

        return Ok(violations)
