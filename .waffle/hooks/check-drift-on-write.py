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
import fnmatch
import re
import subprocess
import sys

_BASH_FILL_PATH = re.compile(r"waffle\s+scaffold\s+--operation\s+fill\b.*?--path\s+(\S+)")
# tests/ という区画の中にありながら、突き合わせの対象になる配置に無いもの。
# 対象外であることを黙って見過ごさないために見る。
#
# ファイル名だけで判定してはいけない。test_ で始まる名前のソースファイル
# （例: ports/test_function_extractor.py）はテストではなく、実際に誤検知した
_TEST_BASENAME = re.compile(r"(?:^|/)tests?/(?:.*/)?test_[^/]*\.py$")
_SPEC_FILE = re.compile(r"\.waffle/documents/specs/.*/(?:usecase|aggregate)/[^/]+\.json$")

# 概念ごとに、その概念のずれを見る検査。どの概念がどこに置かれるかは
# architecture が宣言しており、ここには書かない
_CHECKS_BY_CONCEPT = {
    "usecase": ("check-usecase-class-drift", "check-operation-drift"),
    "aggregate": ("check-aggregate-class-drift",),
    "domain-service": ("check-domain-service-drift",),
}

# 規約documentの名前は、それが従うアーキテクチャと接尾辞を共有する。
# この対応をここで推測せず、配置を宣言している規約そのものから引く
_TEST_STANDARD = "test-standard-"


def _project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def _relative(file_path: str) -> str:
    """リポジトリ直下からの道にする。

    規約が宣言する配置は直下からの道で書かれており、検査はそれをそのまま
    探す。絶対パスのまま渡すと、どの宣言とも一致せず「宣言が無い」に見える。
    """
    try:
        return os.path.relpath(os.path.realpath(file_path), _project_root())
    except ValueError:  # pragma: no cover — 別ドライブ（Windows）
        return file_path


def _architecture_for(rel_path: str) -> str | None:
    """そのテストの配置を宣言している規約を探し、対応するアーキテクチャを返す。

    アーキテクチャは1つではない（このリポジトリ自身と、出荷物である
    artifact-share は別の配置ルールを持つ）。1つに決め打つと、片方の
    テストは何を書いても「どのspecにも対応が無い」と報告され続ける。

    どの規約も宣言していない道なら None を返す。既定のアーキテクチャへ
    寄せて答えを作らない——見当違いの相手と突き合わせた結果は、
    突き合わせ先が無いことより質が悪い。
    """
    directory = os.path.dirname(rel_path)
    if not directory:
        return None
    data = _run_waffle("query-collection", "--operation", "grep_documents",
                       "--path", ".waffle/documents/coding",
                       "--pattern", re.escape(directory + "/"))
    for doc_path, hits in (data or {}).get("value", {}).items():
        doc_id = os.path.basename(doc_path).removesuffix(".json")
        if not doc_id.startswith(_TEST_STANDARD):
            continue
        # 部分一致では足りない。tests/domain/unit/ は、別のアーキテクチャが
        # 宣言する .../lambda/admin_api/tests/domain/unit/ の一部でもある。
        # 宣言そのものと一致した規約だけを、その配置の持ち主とみなす
        if any(str(h.get("value", "")).rstrip("/") == directory for h in hits):
            return "architecture-" + doc_id[len(_TEST_STANDARD):]
    return None


def _architecture_of_spec(spec_path: str) -> str | None:
    """その仕様が属するコンテキストの実装を受け持つアーキテクチャを返す。

    どのコンテキストを受け持つかは architecture の coveredContexts が宣言する。
    対をここに書くと、宣言を変えたときフックだけが古い範囲を見続ける。
    """
    parts = _relative(spec_path).split("/")
    if "specs" not in parts:
        return None
    context = parts[parts.index("specs") + 1]
    for ref in _architecture_refs():
        data = _run_waffle("query", "--operation", "query_path",
                           "--path", f".waffle/documents/coding/{ref}.json",
                           "--expression", "@")
        for block in (data or {}).get("results", []):
            if block["blockKey"] == "coveredContexts":
                if context in block["value"].get("items", []):
                    return ref
    return None


def _architecture_refs() -> list[str]:
    """宣言されているアーキテクチャの名前を集める。中身はここでは読まない。"""
    coding = os.path.join(_project_root(), ".waffle", "documents", "coding")
    try:
        names = os.listdir(coding)
    except OSError:  # pragma: no cover — 規約の置き場所が無い環境
        return []
    return sorted(n.removesuffix(".json") for n in names
                  if n.startswith("architecture-") and n.endswith(".json"))


def _same_place(directory: str, source_root: str, placement: str) -> bool:
    """書かれた道が、宣言された配置そのものかを判定する。

    sourceRoot は {package} のような差し替え箇所を持つことがある。
    そこはどの名前でも一致させる（実際の名前は言語側の都合で決まり、
    どの概念を置くかという宣言とは別の話）。
    """
    declared = f"{source_root.rstrip('/')}/{placement.strip('/')}"
    return fnmatch.fnmatch(directory, re.sub(r"\{[^}]+\}", "*", declared))


def _concepts_at(rel_path: str) -> list[tuple[str, str]]:
    """その道に何を置くと宣言されているかを、architecture から引く。

    概念と配置の対応は architecture document が宣言しており、検知本体も
    そこから導いている（application/services/source_root_resolution.py）。
    フックだけが同じ知識を別の形で持つと、アーキテクチャを増やしたときに
    片方だけが古くなる。実際にそうなっていた——出荷物側の実装は、
    書いても一度も検査されていなかった。

    Returns:
        (概念, architectureRef) の一覧。宣言のどれとも一致しなければ空。
    """
    directory = os.path.dirname(rel_path)
    if not directory:
        return []
    found: list[tuple[str, str]] = []
    for ref in _architecture_refs():
        data = _run_waffle("query", "--operation", "query_path",
                           "--path", f".waffle/documents/coding/{ref}.json",
                           "--expression", "@")
        blocks = {b["blockKey"]: b["value"] for b in (data or {}).get("results", [])}
        source_root = (blocks.get("layout") or {}).get("sourceRoot", "")
        for item in (blocks.get("conceptPlacement") or {}).get("items", []):
            for placement in item.get("placements", []):
                if _same_place(directory, source_root, placement.get("path", "")):
                    found.append((item["concept"], ref))
    return found


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

    # 書かれた道に何を置くと宣言されているかを引き、その概念の検査だけを回す。
    # どの道にどの概念が住むかをここに書かない——それは architecture の宣言であり、
    # 検知本体も同じ宣言から導いている
    if file_path:
        fired: set[tuple[str, str]] = set()
        for concept, ref in _concepts_at(_relative(file_path)):
            for cmd in _CHECKS_BY_CONCEPT.get(concept, ()):
                if (cmd, ref) in fired:
                    continue
                fired.add((cmd, ref))
                _collect(cmd, f"{concept}:{ref}", "--architectureRef", ref)

    # どのspecに対応するかは規約が宣言している。フックは推測せず、
    # 分かっている側だけを渡して残りを検査側に解決させる
    if _TEST_BASENAME.search(file_path):
        rel = _relative(file_path)
        ref = _architecture_for(rel)
        if ref:
            _collect("check-scenario-drift", "scenario-drift",
                     "--testPath", rel, "--architectureRef", ref)
        else:
            unpaired.append(f"{rel} は、どの規約もテストの置き場所として"
                            "宣言していない道にあります")

    fm = _BASH_FILL_PATH.search(command)
    spec_path = fm.group(1).strip("'\"") if fm else ""
    if spec_path and _SPEC_FILE.search(spec_path):
        ref = _architecture_of_spec(spec_path)
        if ref:
            _collect("check-scenario-drift", f"scenario-drift:{spec_path}",
                     "--specPath", spec_path, "--architectureRef", ref)
        else:
            unpaired.append(f"{spec_path} が属するコンテキストの実装を、"
                            "どのアーキテクチャも受け持つと宣言していません")

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
