"""docstring_syntax — 規約が宣言する構文を、既存lintツールが知っている流儀へ写す純粋なドメインサービス。

規約は「どの綴りでタグを書くか」を宣言する。既存のlintツールは流儀の名前
（google / numpy / sphinx 等）でしか設定を受け取らない。この2つの語彙を繋ぐ
のがここの役目で、繋がらない組み合わせは繋がらないと言い切る。

黙って既定の流儀へ倒さない。倒すと、規約が宣言した綴りとは別の綴りで判定され、
「宣言できるが効かない」欄が残る。
"""
from __future__ import annotations

# タグの綴りの組み合わせから、既存lintツールが知っている流儀への対応。
# 増やすときは、その流儀を実際に受け取れるadapterがあることを先に確かめる。
_BY_TAGS = {
    ("Args:", "Returns:", "Raises:"): "google",
    ("Parameters", "Returns", "Raises"): "numpy",
    (":param", ":returns:", ":raises"): "sphinx",
}


def kind_for(syntax_kind: str, tag_params: str, tag_returns: str,
             tag_raises: str) -> str | None:
    """宣言された構文に対応する、既存lintツールの流儀を返す。

    Args:
        syntax_kind: 宣言された構文の種類（tagged / prose）。
        tag_params: 引数の節を始める綴り。
        tag_returns: 戻り値の節を始める綴り。
        tag_raises: 送出する例外の節を始める綴り。

    Returns:
        対応する流儀の名前。対応するものが無ければ None。

    Raises:
        なし。
    """
    if syntax_kind != "tagged":
        return None
    return _BY_TAGS.get((tag_params, tag_returns, tag_raises))
