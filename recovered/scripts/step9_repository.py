"""保管の欄名と集約の語彙のあいだで、新しく型になった値を移し替える。

保管の欄名も、そこに入る素の形も変えない。既に置かれている記録がそのまま
読めることが、この形を選んだ理由である。
"""
from __future__ import annotations

import pathlib

LAMBDA = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/lambda/admin_api")


def patch(rel: str, pairs: list[tuple[str, str]]) -> None:
    path = LAMBDA / rel
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"{rel} に見つかりません:\n{old}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("直した:", rel)


patch("adapters/outbound/stored_shared_artifact_repository.py", [
    ("from domain.entities.shared_artifact import SharedArtifact",
     "from domain.entities.shared_artifact import SharedArtifact\n"
     "from domain.value_objects.artifact_content import ContentFingerprint"),
    ("    ViewTokenId,\n    ViewTokenStatus,\n)",
     "    ViewTokenFingerprint,\n    ViewTokenId,\n    ViewTokenStatus,\n)"),
    ('        content_fingerprint=record.get("contentHash", ""),',
     '        content_fingerprint=ContentFingerprint(record.get("contentHash", "")),'),
    ('        "contentHash": artifact.content_fingerprint,',
     '        "contentHash": artifact.content_fingerprint.value,'),
    ('        fingerprint=t.get("fingerprint", ""),',
     '        fingerprint=ViewTokenFingerprint(t.get("fingerprint", "")),'),
    ('        "fingerprint": t.fingerprint,',
     '        "fingerprint": t.fingerprint.value,'),
])
