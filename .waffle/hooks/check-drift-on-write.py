#!/usr/bin/env python3
"""候補2（testファイル側）・候補4: 書き込み直後のdrift自動発火（PostToolUse）。

書き込まれたファイルのパスパターンから、対応する既存driftチェックusecase
（check-usecase-class-drift / check-operation-drift / check-aggregate-class-drift /
check-domain-service-drift / check-scenario-drift）をCLI経由で自動実行し、
検出があったときだけ結果をモデルへ返す（クリーンなときは沈黙する——必要な
情報だけを返すという方針、docs/brainstorm/brainstorm-waffle-hooks.md参照）。

新しいdrift検知ロジックは一切持たない。既存usecaseをトリガーするだけの薄い
ラッパー。

Edit|Writeに加えBashもmatcher対象にする（process-reliability論点3）。
document.jsonへの書き込みはprotect-document-json.pyによりEdit/Writeでは
常に拒否され、`waffle scaffold fill`（Bash経由）だけが正規の書き込み経路で
あるため、usecase specのacceptanceScenarios等がBash経由のfillで更新された
ときも、対応するtestファイルとのscenario-driftをその場で能動的にチェックする
（Edit|Writeのmatcherだけでは、document.json自体の更新イベントを一切検知
できないため）。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

_USECASE_IMPL = re.compile(r"src/waffle/application/usecases/.*\.py$")
_ENTITY_IMPL = re.compile(r"src/waffle/domain/entities/.*\.py$")
_SERVICE_IMPL = re.compile(r"src/waffle/domain/services/.*\.py$")
_BASH_FILL_PATH = re.compile(r"waffle\s+scaffold\s+--operation\s+fill\b.*?--path\s+(\S+)")
# tests/ という区画の中にありながら、突き合わせの対象になる配置に無いもの。
# 対象外であることを黙って見過ごさないために見る。
#
# ファイル名だけで判定してはいけない。test_ で始まる名前のソースファイル
# （例: ports/test_function_extractor.py）はテストではなく、実際に誤検知した
_TEST_BASENAME = re.compile(r"(?:^|/)tests?/(?:.*/)?test_[^/]*\.py$")
# 実装の配置ルールを持つ architecture document と、それが実現する範囲。
#
# 実装の置き場所は architecture document に1つだけ定義されており、境界づけ
# られたコンテキストからスタックを辿る手段がまだ無い。範囲を絞らないと、
# 別のスタックに載っているコンテキスト（実装を伴うSkill）の集約が
# 「実装が無い」と誤って報告される——実際にはあり、探す場所が違うだけ。
#
# 絞っていること自体は静的な既知の事実なので、書き込みのたびには報告しない
# （毎回鳴る警報は鳴らない警報と同じになる）。この制限は
# .waffle/memory/ に作業項目として記録してある
ARCHITECTURE_REF = "architecture-waffle"

_SPEC_FILE = re.compile(r"\.waffle/documents/specs/.*/(?:usecase|aggregate)/[^/]+\.json$")


def _project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def _run_waffle(*args: str) -> dict | None:
    result = subprocess.run(
        ["uv", "run", "--project", ".", "waffle", *args],
        cwd=_project_root(), capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


# 検知結果に含まれるが、driftではないもの。突き合わせが成立した組を
# 報告するための情報であり、これが非空であることは「綺麗」を意味する。
# ここを除かないと、driftゼロでも常に「検出しました」と鳴る
_INFORMATIONAL = {"matched", "matched_test_names"}


def _has_findings(data: dict | None) -> bool:
    if data is None:
        return False
    if "results" in data:
        # 全体走査・片側指定の形。results は判定済みの組の一覧であって
        # driftではない。driftは各組の中にある
        return any(_has_findings(entry) for entry in data["results"])
    return any(v for k, v in data.items()
               if k not in _INFORMATIONAL and isinstance(v, list) and v)


def _unpaired_of(data: dict | None) -> list[str]:
    """突き合わせ先が見つからなかったものを取り出す。

    driftとは別の状態。宣言のどれもそのテストを指していない場合、
    documentIdが空で並ぶ。
    """
    if not data or "missing_test_file" not in data:
        return []
    out = []
    for entry in data["missing_test_file"]:
        if entry.get("documentId"):
            out.append(f"{entry['documentId']} の {entry['block']} に対応するテストが "
                       f"{entry['expectedPath']} に見つかりません")
        else:
            out.append(f"{entry['expectedPath']} を指す宣言がどのspecにもありません")
    return out


def _uncheckable(data: dict | None) -> str | None:
    """検査そのものが実行できなかったときの理由を返す。

    エラーは list ではないため、findingsの判定からは常に漏れる。漏れた結果
    沈黙すると、検査できなかったことが綺麗だったことと同じ見た目になる。
    """
    if data is None:
        return "結果を解釈できませんでした"
    if isinstance(data.get("error"), str):
        return f"{data['error']}: {data.get('message', '')}".strip()
    return None


def check(payload: dict) -> str | None:
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    command = tool_input.get("command", "")

    reports: list[str] = []
    # 突き合わせ先が見つからなかったもの。driftとは別の状態として扱う
    unpaired: list[str] = []

    def _collect(cmd: str, label: str, *args: str) -> None:
        data = _run_waffle(cmd, *args)
        if _has_findings(data):
            reports.append(f"[{label}] {json.dumps(data, ensure_ascii=False)}")
            return
        unpaired.extend(_unpaired_of(data))
        reason = _uncheckable(data)
        if reason:
            unpaired.append(f"{label} を実行できませんでした（{reason}）")

    # 実装の配置は architecture document から導く。引数なしで呼ぶと
    # MISSING_PARAM が返るだけで、この4つは書かれて以来ずっと空振りしていた
    # 仕様側の範囲は architecture の coveredContexts が宣言する。
    # 対をここに書くと、宣言を変えたときフックだけが古い範囲を見続ける。
    arch = ("--architectureRef", ARCHITECTURE_REF)


    if _USECASE_IMPL.search(file_path):
        _collect("check-usecase-class-drift", "usecase-class-drift", *arch)
        _collect("check-operation-drift", "operation-drift", *arch)

    if _ENTITY_IMPL.search(file_path):
        _collect("check-aggregate-class-drift", "aggregate-class-drift", *arch)

    if _SERVICE_IMPL.search(file_path):
        _collect("check-domain-service-drift", "domain-service-drift", *arch)

    # どのspecに対応するかは規約が宣言している。フックは推測せず、
    # 分かっている側だけを渡して残りを検査側に解決させる
    if _TEST_BASENAME.search(file_path):
        _collect("check-scenario-drift", "scenario-drift",
                 "--testPath", file_path, *arch)

    fm = _BASH_FILL_PATH.search(command)
    spec_path = fm.group(1).strip("'\"") if fm else ""
    if spec_path and _SPEC_FILE.search(spec_path):
        _collect("check-scenario-drift", f"scenario-drift:{spec_path}",
                 "--specPath", spec_path, *arch)

    target = file_path or spec_path
    if reports:
        return f"[Hook] {target} への書き込み後にdriftを検出しました: " + " / ".join(reports)
    # 「突き合わせて綺麗だった」と「突き合わせ先が見つからなかった」は別の状態。
    # 前者は沈黙してよいが、後者まで沈黙すると、対応が取れていないことが
    # 綺麗であることと同じ見た目になる。2026-08-01に実際に取り違えた——
    # 132シナリオが誰とも突き合わされていない状態を「drift無し」と読んだ。
    # 沈黙してよいのは「検査した結果、綺麗だった」ときだけにする。
    if unpaired:
        return ("[Hook] driftは検出していません。突き合わせが行われていないためです: "
                + " / ".join(unpaired))
    return None


def main() -> None:
    payload = json.load(sys.stdin)
    message = check(payload)
    if message:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": message,
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
