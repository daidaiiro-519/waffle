"""発行を口へ通す。作る手立ては外へ出し、業務の語彙の側は形だけを決める。"""
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


# ── プロジェクトを作る ────────────────────────────────
patch("application/usecases/create_project.py", [
    ("from domain.identifier import new_project_id\n", ""),
    ("from application.ports.shared_artifact_repository import SharedArtifactRepository",
     "from application.ports.identifier import IdGenerator\n"
     "from application.ports.shared_artifact_repository import SharedArtifactRepository"),
    ("def _create(artifacts: SharedArtifactRepository, projects: ProjectRepository, "
     "viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, "
     "display_name: str, scope: str, project_key: str = \"\") -> CreatedProject:",
     "def _create(artifacts: SharedArtifactRepository, projects: ProjectRepository, "
     "viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, ids: IdGenerator, "
     "caller: Caller, display_name: str, scope: str, project_key: str = \"\") -> CreatedProject:"),
    ("    project_id = new_project_id()\n"
     "    token = view_token.new_token()\n"
     "    now = clock()\n"
     "    first = view_token.issued(FIRST_TOKEN_NAME, gate.fingerprint_of(token),\n"
     "                              view_token.expires_at(now), now)\n",
     "    project_id = ids.new_project_id()\n"
     "    token = ids.new_view_token_secret()\n"
     "    now = clock()\n"
     "    first = view_token.issued(ids.new_view_token_id(), FIRST_TOKEN_NAME,\n"
     "                              gate.fingerprint_of(token),\n"
     "                              view_token.expires_at(now), now)\n"),
    ("        project_id=ProjectId(project_id),", "        project_id=project_id,"),
    ("    place_project_page(viewer, project_id)", "    place_project_page(viewer, project_id.value)"),
    ("    gate.replace_grants(ViewSubject.project(project_id),",
     "    gate.replace_grants(ViewSubject.project(project_id.value),"),
    ("    return CreatedProject(project_id=project_id, token=token,\n"
     "                          url=viewer.project_url(project_id), name=name, scope=scope)",
     "    return CreatedProject(project_id=project_id.value, token=token,\n"
     "                          url=viewer.project_url(project_id.value), name=name, scope=scope)"),
])

# ── 閲覧トークンを発行する ────────────────────────────
patch("application/usecases/issue_view_token.py", [
    ("from application.ports.project_repository import ProjectRepository",
     "from application.ports.identifier import IdGenerator\n"
     "from application.ports.project_repository import ProjectRepository"),
    ("    token = view_token.new_token()\n"
     "    issued = view_token.issued(name, gate.fingerprint_of(token), expiry, now)",
     "    token = ids.new_view_token_secret()\n"
     "    issued = view_token.issued(ids.new_view_token_id(), name,\n"
     "                               gate.fingerprint_of(token), expiry, now)"),
])

# ── 中身を差し替える ──────────────────────────────────
patch("application/usecases/replace_artifact_content.py", [
    ("from domain.artifact_content import fingerprint as content_fingerprint",
     "from domain.value_objects.artifact_content import ContentFingerprint"),
    ("artifact.with_content(content_fingerprint(html), descriptor,",
     "artifact.with_content(ContentFingerprint.of(html), descriptor,"),
])

# ── 閲覧トークンの指紋に型を与える ────────────────────
patch("application/ports/view_gate.py", [
    ("from domain.value_objects.view_subject import ViewSubject",
     "from domain.value_objects.view_subject import ViewSubject\n"
     "from domain.value_objects.view_token import ViewTokenFingerprint"),
    ("    def fingerprint_of(self, token: str) -> str:",
     "    def fingerprint_of(self, token: str) -> ViewTokenFingerprint:"),
])

patch("adapters/outbound/kvs_view_gate.py", [
    ("from domain.value_objects.view_subject import ARTIFACT, PROJECT, ViewSubject",
     "from domain.value_objects.view_subject import ARTIFACT, PROJECT, ViewSubject\n"
     "from domain.value_objects.view_token import ViewTokenFingerprint"),
    ("    def fingerprint_of(self, token: str) -> str:\n"
     "        \"\"\"閲覧トークンを、照合にだけ使える形へ変える。元へは戻せない。\"\"\"\n"
     "        return fingerprint(token)",
     "    def fingerprint_of(self, token: str) -> ViewTokenFingerprint:\n"
     "        \"\"\"閲覧トークンを、照合にだけ使える形へ変える。元へは戻せない。\"\"\"\n"
     "        return ViewTokenFingerprint(view_token_fingerprint(token))"),
    ("def fingerprint(token: str) -> str:\n"
     "    \"\"\"閲覧トークンから、照合にだけ使える形を作る。元へは戻せない。",
     "def view_token_fingerprint(token: str) -> str:\n"
     "    \"\"\"閲覧トークンから、照合にだけ使える形を作る。元へは戻せない。\n\n"
     "    中身の指紋とは別の対象を指す。同じ綴りにすると、どちらの層のものか\n"
     "    名前から判別できない。"),
])
