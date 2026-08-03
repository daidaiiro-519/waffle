"""layer_assignment — 規約が宣言する層の置き場所から、実装ファイルと依存先を
層へ割り当てる純ロジック。

置き場所への前方一致だけでファイルの層を決める。ディレクトリツリーの図は
投影であって宣言ではないため参照しない（LayersBlock の x-prompt-query が
定める読み方に従う）。

依存の書き方は言語ごとに違う（ドット区切り・相対パス・モジュールパス）。
ここでは書き方の差を「区切り記号で割った並び」まで均し、どの実在ファイルを
指すかの判定は、実在を知っている呼び出し側へ委ねる。
"""
from __future__ import annotations

_SEPARATORS = ("::", ".", "/")


def overlapping_layer_paths(layers: list[dict]) -> list[dict]:
    """ある層の置き場所が、別の層の置き場所を含んでいる組を列挙する。

    含んでいると、配下のファイルがどちらの層かを前方一致で決められない。
    実装を走査する前にこれを弾かないと、走査結果そのものが意味を失う。

    Args:
        layers: layer と path を持つ層の宣言。

    Returns:
        {"outer": 外側の層名, "inner": 内側の層名, "outerPath", "innerPath"} の配列。
    """
    found = []
    for outer in layers:
        for inner in layers:
            if outer is inner:
                continue
            outer_path, inner_path = outer.get("path", ""), inner.get("path", "")
            if outer_path and inner_path and inner_path.startswith(outer_path + "/"):
                found.append({
                    "outer": outer.get("layer"), "outerPath": outer_path,
                    "inner": inner.get("layer"), "innerPath": inner_path,
                })
    return found


def layer_of(relative_path: str, layers: list[dict]) -> str | None:
    """置き場所への前方一致で、そのパスが属する層を決める（最長一致を採る）。

    Args:
        relative_path: sourceRoot からの相対パス。
        layers: layer と path を持つ層の宣言。

    Returns:
        層名。どの置き場所にも入らなければ None。
    """
    best: tuple[int, str] | None = None
    for item in layers:
        path = item.get("path", "")
        if not path:
            continue
        if relative_path == path or relative_path.startswith(path + "/"):
            if best is None or len(path) > best[0]:
                best = (len(path), item.get("layer"))
    return best[1] if best else None


def is_relative_reference(reference: str) -> bool:
    """その依存が、書いた場所からの相対で指されているか。"""
    return reference.startswith(".")


def reference_segments(reference: str) -> list[str]:
    """依存の書き方の差を均し、区切りで割った並びにする。

    Args:
        reference: 取り出したままの依存の参照（例: waffle.domain.x / ../domain/x /
            crate::domain::x / example.com/app/domain）。

    Returns:
        区切りで割った並び。相対を示す先頭のドットは呼び出し側が解釈するため落とす。
    """
    text = reference.split("{")[0].strip().strip("/")
    for separator in _SEPARATORS:
        text = text.replace(separator, "/")
    return [s for s in text.split("/") if s and s != "*"]


def resolve_reference(reference: str, from_dir: str, known_files: set,
                      known_dirs: set) -> str | None:
    """依存の参照が、規約の受け持つ範囲の中のどこを指すかを決める。

    候補を長い順に見て、実在するものを採る。実在を確かめないと、層と同じ名前を持つ
    外部ライブラリ（layers に shared があるプロジェクトでの `import shared` 等）を
    層への依存と取り違える。

    1つの並びだけからなる参照が、ファイルではなくディレクトリにしか当たらない場合は
    解決しない。その形は「規約の中のパッケージ」と「同名の外部ライブラリ」を
    構文からは区別できず、どちらと決めるにはプロジェクトの取り込み規約を
    宣言させる必要があるため。取り違えるより、報告しない方を選ぶ。

    Args:
        reference: 取り出したままの依存の参照。
        from_dir: その依存を書いたファイルがあるディレクトリ（sourceRoot からの相対）。
        known_files: 走査で見つかったファイルの相対パス（拡張子を落としたもの）。
        known_dirs: 上記ファイルの親ディレクトリの相対パス。

    Returns:
        解決した相対パス。範囲の外なら None。
    """
    candidates = candidate_paths(reference, from_dir)
    single_segment = not is_relative_reference(reference) and len(candidates) == 1
    for candidate in candidates:
        stripped = candidate.rsplit(".", 1)[0] if "." in candidate.rsplit("/", 1)[-1] else candidate
        for form in (candidate, stripped):
            if form in known_files:
                return form
            if form in known_dirs and not single_segment:
                return form
    return None


def candidate_paths(reference: str, from_dir: str = "") -> list[str]:
    """その依存が指しうる、sourceRoot からの相対パスの候補を長い順に並べる。

    絶対的な参照は、どこまでが規約の外側（パッケージ名・モジュールのホスト名）かが
    言語と配布形態で変わる。宣言の欄を増やして書かせる代わりに、後ろ側から順に
    候補を作り、実在するものを呼び出し側に選ばせる。

    Args:
        reference: 取り出したままの依存の参照。
        from_dir: その依存を書いたファイルがあるディレクトリ（sourceRoot からの相対）。
            相対で指された依存の解決に使う。

    Returns:
        長い順に並んだ候補パス。
    """
    if is_relative_reference(reference):
        return [_join_relative(reference, from_dir)]
    segments = reference_segments(reference)
    return ["/".join(segments[i:]) for i in range(len(segments))]


def _join_relative(reference: str, from_dir: str) -> str:
    """相対で指された依存を、書いた場所を起点に畳む。"""
    text = reference
    up = 0
    while text.startswith("."):
        # Python の相対 import は先頭のドットの数だけ上へ辿る（1つ目は自分自身）。
        # TypeScript 等の ./ ../ も同じ数え方に収まる。
        up += 1
        text = text[1:]
    text = text.lstrip("/")
    parts = [p for p in from_dir.split("/") if p]
    for _ in range(max(0, up - 1)):
        if parts:
            parts.pop()
    for separator in _SEPARATORS:
        text = text.replace(separator, "/")
    return "/".join([*parts, *(p for p in text.split("/") if p)])
