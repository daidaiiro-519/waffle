"""招かれている人の顔ぶれを、誰が扱ってよいか。

判じる材料は、名簿が定める役割だけである。この文脈のどの集約の状態も読まない
——名簿はこの文脈の集約ではなく、扱う対象は口の向こう側にある。だから集約にも
業務サービスにも置かず、名簿の語彙を移し替える口のすぐ内側に方針として置く。

規則そのものと、その理由（共有の相手を社外へ広げたときに社内の顔ぶれまで
伝わらないようにする）は、uc-list-publishers / uc-invite-publisher の事前条件と
存在意義が正本として持つ。ここはその実行にすぎない。

この割り当ては、いまの規則の形に対して正しい。見える顔ぶれが公開範囲によって
変わるようになれば、判定は集約の状態を読み始め、その時点で業務サービスへ戻る。
隣のプロジェクトには既に、公開範囲を読んで可否を決める判定が実在する。

対象の仕様: uc-list-publishers / uc-invite-publisher
"""
from __future__ import annotations

from application.caller import Caller


def may_manage_publishers(caller: Caller) -> bool:
    """招かれている人の顔ぶれを出し入れしてよいか。

    管理者だけ。誰が招かれているかは、共有の相手を社外へ広げたときに社内の
    顔ぶれまで伝わらないよう、投稿者どうしにも見せない。

    Args:
        caller: 要求してきた人。

    Returns:
        顔ぶれを出し入れしてよければ True。

    Raises:
        なし。
    """
    return caller.is_admin
