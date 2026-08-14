"""発行の口の実物を、合成ルートで組み立てて配る。"""
from __future__ import annotations

import pathlib

SKILL = pathlib.Path("/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share")
LAMBDA = SKILL / "lambda" / "admin_api"


def patch(path: pathlib.Path, pairs: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"{path} に見つかりません:\n{old}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("直した:", path.relative_to(SKILL))


patch(LAMBDA / "main.py", [
    ("from adapters.outbound.kvs_view_token_store import KvsViewTokenStore",
     "from adapters.outbound.kvs_view_token_store import KvsViewTokenStore\n"
     "from adapters.outbound.random_identifier import RandomIdGenerator"),
    ("    wrapper_template: str = \"\"\n    project_page: str = \"\"",
     "    wrapper_template: str = \"\"\n    project_page: str = \"\"\n"
     "    ids: object = dataclasses.field(default_factory=RandomIdGenerator)"),
    ("PublishArtifact(c.artifacts, c.viewer, c.gate, c.identify, c.now).run(",
     "PublishArtifact(c.artifacts, c.viewer, c.gate, c.identify, c.now, c.ids).run("),
])

patch(LAMBDA / "adapters" / "inbound" / "admin_api.py", [
    ("    \"issue-token\":       lambda d, c, b: IssueViewToken(\n"
     "        d.artifacts, d.projects, d.gate, d.now\n"
     "    ).run(c, subject_from(b), b.get(\"name\", \"\"), b.get(\"ttl\")),",
     "    \"issue-token\":       lambda d, c, b: IssueViewToken(\n"
     "        d.artifacts, d.projects, d.gate, d.now, d.ids\n"
     "    ).run(c, subject_from(b), b.get(\"name\", \"\"), b.get(\"ttl\")),"),
    ("    \"create-project\":  lambda d, c, b: CreateProject(\n"
     "        d.artifacts, d.projects, d.viewer, d.gate, d.now\n"
     "    ).run(c, b.get(\"displayName\", \"\"), b.get(\"scope\", \"\"), b.get(\"projectKey\", \"\")),",
     "    \"create-project\":  lambda d, c, b: CreateProject(\n"
     "        d.artifacts, d.projects, d.viewer, d.gate, d.now, d.ids\n"
     "    ).run(c, b.get(\"displayName\", \"\"), b.get(\"scope\", \"\"), b.get(\"projectKey\", \"\")),"),
])
