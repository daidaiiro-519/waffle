"""検証の足場を、新しい型と口へ追随させる。確かめている中身は変えない。"""
from __future__ import annotations

import pathlib

TESTS = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/tests")


def patch(rel: str, pairs: list[tuple[str, str]]) -> None:
    path = TESTS / rel
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"{rel} に見つかりません:\n{old}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("直した:", rel)


patch("view_token_setup.py", [
    ("from fakes import ", "from fakes import FakeIdGenerator, "),
    ("    def __init__(self, artifacts, projects, gate, at=None):\n"
     "        self.artifacts, self.projects, self.gate = artifacts, projects, gate\n"
     "        self.comments = self.viewer = self.directory = self.identify = None\n"
     "        self.now = (lambda: at) if at is not None else (lambda: NOW)",
     "    def __init__(self, artifacts, projects, gate, at=None):\n"
     "        self.artifacts, self.projects, self.gate = artifacts, projects, gate\n"
     "        self.comments = self.viewer = self.directory = self.identify = None\n"
     "        self.now = (lambda: at) if at is not None else (lambda: NOW)\n"
     "        self.ids = FakeIdGenerator()"),
    ('artifact_id=ArtifactId(AID), display_name="設計レビュー", content_fingerprint="",',
     'artifact_id=ArtifactId(AID), display_name="設計レビュー",\n'
     '        content_fingerprint=ContentFingerprint(""),'),
])

text = (TESTS / "view_token_setup.py").read_text(encoding="utf-8")
if "ContentFingerprint" not in text.split("AID =")[0]:
    text = text.replace("from domain.entities.shared_artifact import SharedArtifact",
                        "from domain.entities.shared_artifact import SharedArtifact\n"
                        "from domain.value_objects.artifact_content import ContentFingerprint", 1)
    (TESTS / "view_token_setup.py").write_text(text, encoding="utf-8")
    print("取り込みを足した: view_token_setup.py")
