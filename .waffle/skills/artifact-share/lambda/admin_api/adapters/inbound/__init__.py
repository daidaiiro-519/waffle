"""外から届いた要求を、ユースケースの呼び出しへ変える。

判断を持たない。受け取った値をそのまま行き先へ渡し、返ってきたものと、投げら
れた業務上の失敗を、外の言葉（HTTPの状態）へ写すだけ。

architecture: architecture-artifact-share の conceptPlacement（inbound-adapter）
"""
