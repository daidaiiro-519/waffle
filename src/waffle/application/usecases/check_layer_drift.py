"""check layer drift — 規約が宣言する層・置き場所・依存してよい先と、実装が実際に
持っている依存を突き合わせる application use case。

宣言だけが唯一の基準。検査コードは層の名前も、言語ごとの拡張子の表も持たない。
どちらもコード側に持つと、規約を直したときに二箇所を直すことになり、
やがて宣言とコードが食い違う。

実行/意味理解はしない（構文解析のみ）。検出した差分の中身の妥当性評価はAIが担う。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.import_extractor import ImportExtractor, UnsupportedLanguage
from waffle.application.services.stack_resolution import resolve_layer_graph
from waffle.domain.services.layer_assignment import (
    layer_of,
    overlapping_layer_paths,
    resolve_reference,
)
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class CheckLayerDrift:
    def __init__(self, documents: DocumentRepository, extractor: ImportExtractor) -> None:
        self._documents = documents
        self._extractor = extractor

    def run(self, architecture_ref: str | None = None) -> Result[dict]:
        if not architecture_ref:
            return _err("MISSING_PARAM", "architectureRef が必要です")

        graph = resolve_layer_graph(self._documents, architecture_ref)
        if isinstance(graph, Err):
            return graph
        graph = graph.value

        layers = graph["layers"]
        overlapping = overlapping_layer_paths(layers)
        if overlapping:
            # 実装を走査する前に弾く。含んでいる状態では、配下のファイルがどちらの層かを
            # 置き場所から決められず、走査結果そのものが意味を失う
            described = "／".join(
                f"{o['outer']}（{o['outerPath']}）が {o['inner']}（{o['innerPath']}）を含んでいます"
                for o in overlapping)
            return _err("OVERLAPPING_LAYER_PATHS", described)

        src_root = graph["srcRoot"]
        may_depend_on = {i.get("layer"): set(i.get("mayDependOn") or []) for i in layers}
        composition_roots = set(graph["compositionRootPaths"])
        language_by_suffix = graph["languageBySuffix"]

        missing_layer_dirs = []
        for item in layers:
            path = item.get("path", "")
            try:
                self._documents.list_files(f"{src_root}/{path}", "**/*")
            except FileNotFoundError:
                # 宣言した置き場所がまだ無いことは、引数の誤りではなく未実装のドリフト。
                # 規約を先に書いて実装を後から合わせる進め方では、この状態が正常に起きる
                missing_layer_dirs.append({"layer": item.get("layer"), "path": path})

        # 走査はsourceRoot全体に対して行う。層の置き場所ごとに集めると、どの層にも
        # 属さないファイルが最初から集まらず、宣言漏れを原理的に報告できなくなる
        try:
            files = self._documents.list_files(src_root, "**/*")
        except FileNotFoundError:
            files = []

        # 依存先が規約の範囲の中に実在するかを確かめるための索引。実在を見ないと、
        # 層と同じ名前を持つ外部ライブラリを層への依存と取り違える
        known_files: set = set()
        known_dirs: set = set()
        for path in files:
            if not path.startswith(src_root + "/"):
                continue
            relative = path[len(src_root) + 1:]
            known_files.add(relative.rsplit(".", 1)[0])
            parts = relative.split("/")[:-1]
            for i in range(1, len(parts) + 1):
                known_dirs.add("/".join(parts[:i]))

        violations = []
        unassigned = []
        for path in sorted(set(files)):
            relative = path[len(src_root) + 1:] if path.startswith(src_root + "/") else path
            if relative in composition_roots:
                continue  # 合成ルートは層のグラフの外にある
            language = language_by_suffix.get(path.rsplit(".", 1)[-1].lower())
            if language is None:
                continue  # 規約が宣言していない拡張子は走査対象外
            try:
                source = self._documents.read_text(path)
            except FileNotFoundError:
                continue
            if not source.strip():
                # 何も宣言していないファイルは、依存の規則を破りようがなく、
                # 置き場所を問う対象でもない（パッケージの目印等）。所見に混ぜると
                # 常に同じ顔ぶれが並び、報告そのものが読まれなくなる
                continue
            layer = layer_of(relative, layers)
            if layer is None:
                unassigned.append({"path": path})
                continue
            violations.extend(self._violations_of(
                source, path, relative, layer, language, layers, may_depend_on,
                known_files, known_dirs))

        return Ok({
            "violations": violations,
            "unassigned": unassigned,
            "missing_layer_dirs": missing_layer_dirs,
        })

    def _violations_of(self, source: str, path: str, relative: str, layer: str,
                       language: str, layers: list[dict], may_depend_on: dict,
                       known_files: set, known_dirs: set) -> list[dict]:
        try:
            references = self._extractor.imports(source, language)
        except (UnsupportedLanguage, SyntaxError):
            # 解析できないファイルは違反ではない。宣言と実装の食い違いを見る検査であって、
            # 解析器の対応範囲を報告する検査ではない
            return []

        from_dir = "/".join(relative.split("/")[:-1])
        allowed = may_depend_on.get(layer, set())
        found = []
        for reference in references:
            resolved = resolve_reference(reference, from_dir, known_files, known_dirs)
            target = layer_of(resolved, layers) if resolved is not None else None
            if target is None or target == layer:
                # 解決できない参照は規約の受け持つ範囲の外（標準・外部ライブラリ）。
                # 同じ層の中の依存は、mayDependOn の宣言を要さない
                continue
            if target not in allowed:
                found.append({"path": path, "layer": layer,
                              "imports": reference, "importedLayer": target})
        return found
