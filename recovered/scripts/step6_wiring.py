"""発行の口を、ユースケースの組み立てへ通す。生成は合成ルートだけが行う。"""
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


patch("application/usecases/issue_view_token.py", [
    ("    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, gate: ViewGatePort, clock: Clock) -> None:\n"
     "        self._artifacts = artifacts\n"
     "        self._projects = projects\n"
     "        self._gate = gate\n"
     "        self._clock = clock\n",
     "    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, gate: ViewGatePort, clock: Clock, ids: IdGenerator) -> None:\n"
     "        self._artifacts = artifacts\n"
     "        self._projects = projects\n"
     "        self._gate = gate\n"
     "        self._clock = clock\n"
     "        self._ids = ids\n"),
    ("        return _issue(self._artifacts, self._projects, self._gate, self._clock, caller, subject, name, ttl)",
     "        return _issue(self._artifacts, self._projects, self._gate, self._clock, self._ids, caller, subject, name, ttl)"),
])

patch("application/usecases/create_project.py", [
    ("    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock) -> None:\n"
     "        self._artifacts = artifacts\n"
     "        self._projects = projects\n"
     "        self._viewer = viewer\n"
     "        self._gate = gate\n"
     "        self._clock = clock\n",
     "    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, ids: IdGenerator) -> None:\n"
     "        self._artifacts = artifacts\n"
     "        self._projects = projects\n"
     "        self._viewer = viewer\n"
     "        self._gate = gate\n"
     "        self._clock = clock\n"
     "        self._ids = ids\n"),
    ("        return _create(self._artifacts, self._projects, self._viewer, self._gate, self._clock, caller, display_name, scope, project_key)",
     "        return _create(self._artifacts, self._projects, self._viewer, self._gate, self._clock, self._ids, caller, display_name, scope, project_key)"),
])
