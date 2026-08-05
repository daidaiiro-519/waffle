"""管理操作の受け口。

操作の名前と行き先を表にしてあるのは、どれにも当たらなかったときの行き先を
持たせないため。以前はここが連なった分岐で、最後の1つが名簿からの削除だった。
操作を1つ増やして行き先を書き忘れると、その操作は黙って削除を実行していた。
表であれば、行き先の無い操作は下で落ちる。

ここは判断を持たない。誰が何をしてよいかはユースケースが決め、ここはその結果を
外の言葉へ写すだけ。
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass

from application.ports import Caller
from application.usecases.assign_artifact_to_project import AssignArtifactToProject
from application.usecases.browse_projects import BrowseProjects
from application.usecases.control_project_access import ControlProjectAccess
from application.usecases.create_project import CreateProject
from application.usecases.export_artifact import ExportArtifact
from application.usecases.invite_publisher import InvitePublisher
from application.usecases.issue_view_token import IssueViewToken
from application.usecases.list_my_artifacts import ListMyArtifacts
from application.usecases.list_publishers import ListPublishers
from application.usecases.list_view_tokens import ListViewTokens
from application.usecases.read_comments import ReadComments
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.resume_artifact import ResumeArtifact
from application.usecases.revoke_all_view_tokens import RevokeAllViewTokens
from application.usecases.revoke_view_token import RevokeViewToken
from application.usecases.suspend_artifact import SuspendArtifact
from application.usecases.transfer_artifact import TransferArtifact
from application.view_token_access import ViewTokenError
from domain.view_subject import ViewSubject
from shared.errors import ManageError, ProjectError, PublisherError, PublishError

def _subject(body: dict):
    """要求が指している対象を読む。共有アーティファクトかプロジェクトのどちらか。"""
    if body.get("projectId"):
        return ViewSubject.project(body["projectId"])
    return ViewSubject.artifact(body.get("artifactId", ""))


# 操作の名前と、その行き先。
#
# 表にしてあるのは、どれにも当たらなかったときの行き先を持たせないため。
# 以前はここが連なった分岐で、最後の1つが名簿からの削除だった。操作を
# 1つ増やして行き先を書き忘れると、その操作は黙って削除を実行していた。
# 表であれば、行き先の無い操作は下で落ちる。
ROUTES = {
    "list":        lambda d, c, b: ListMyArtifacts(d.artifacts, d.comments).run(c),
    "replace":     lambda d, c, b: ReplaceArtifactContent(
        d.artifacts, d.projects, d.comments, d.viewer, d.now
    ).run(c, b.get("artifactId", ""), b.get("html", "")),
    "disable":     lambda d, c, b: SuspendArtifact(d.artifacts, d.gate, d.now).run(
        c, b.get("artifactId", "")),
    "enable":      lambda d, c, b: ResumeArtifact(d.artifacts, d.viewer, d.gate, d.now).run(
        c, b.get("artifactId", "")),
    "assign":      lambda d, c, b: _assign(d).run(
        "assign", c, b.get("artifactId", ""), b.get("projectId", "")),
    "unassign":    lambda d, c, b: _assign(d).run(
        "unassign", c, b.get("artifactId", ""), b.get("projectId", "")),
    "transfer":    lambda d, c, b: TransferArtifact(d.artifacts, d.directory, d.now).run(
        c, b.get("artifactId", ""), b.get("toPublisher", "")),

    "issue-token":       lambda d, c, b: IssueViewToken(
        d.artifacts, d.projects, d.gate, d.now
    ).run(c, _subject(b), b.get("name", ""), b.get("ttl")),
    "view-tokens":       lambda d, c, b: ListViewTokens(
        d.artifacts, d.projects, d.now).run(c, _subject(b)),
    "revoke-token":      lambda d, c, b: RevokeViewToken(
        d.artifacts, d.projects, d.gate, d.now).run(c, _subject(b), b.get("tokenId", "")),
    "revoke-all-tokens": lambda d, c, b: RevokeAllViewTokens(
        d.artifacts, d.projects, d.gate, d.now).run(c, _subject(b)),

    "comments":    lambda d, c, b: ReadComments(d.artifacts, d.comments).run(
        c, b.get("artifactId", "")),
    "export":      lambda d, c, b: ExportArtifact(d.artifacts, d.comments, d.viewer).run(
        c, b.get("artifactId", "")),

    "invite":           lambda d, c, b: _publishers(d).run("invite", c, email=b.get("email", "")),
    "resend-invite":    lambda d, c, b: _publishers(d).run(
        "resend", c, publisher_id=b.get("publisherId", "")),
    "remove-publisher": lambda d, c, b: _publishers(d).run(
        "remove", c, publisher_id=b.get("publisherId", "")),
    "publishers":       lambda d, c, b: {"publishers": ListPublishers(d.directory).run(c)},

    "projects":        lambda d, c, b: _browse(d).run("list", c),
    "project":         lambda d, c, b: _browse(d).run("detail", c, b.get("projectId", "")),
    "create-project":  lambda d, c, b: CreateProject(
        d.artifacts, d.projects, d.viewer, d.gate, d.now
    ).run(c, b.get("displayName", ""), b.get("scope", ""), b.get("projectKey", "")),
    "disable-project": lambda d, c, b: _project_access(d).run("suspend", c, b.get("projectId", "")),
    "enable-project":  lambda d, c, b: _project_access(d).run("resume", c, b.get("projectId", "")),
}


# 複数の操作を持つユースケースは、組み立てを1か所にまとめる。
# 同じ結線を行き先ごとに書くと、口を1つ足したときの直し漏れが出る
def _assign(d) -> AssignArtifactToProject:
    return AssignArtifactToProject(d.artifacts, d.projects, d.viewer, d.gate, d.now)


def _publishers(d) -> InvitePublisher:
    return InvitePublisher(d.artifacts, d.directory)


def _browse(d) -> BrowseProjects:
    return BrowseProjects(d.artifacts, d.projects, d.viewer)


def _project_access(d) -> ControlProjectAccess:
    return ControlProjectAccess(d.projects, d.viewer, d.gate, d.now)



# 受け付ける操作。ここに無いものは受け付けない。
# 表から導くのは、受け付ける操作と行き先を持つ操作を必ず一致させるため


ACTIONS = set(ROUTES) | {"publish"}


def _dispatch(action, deps, caller, body):
    route = ROUTES.get(action)
    if route is None:
        raise ManageError("UNKNOWN_ACTION", "その操作はありません。")
    return route(deps, caller, body)


# 業務の語と、外へ返す綴りの対応。管理画面はこの綴りで分岐している
OUTWARD_STATUS = {"PUBLISHED": "active", "SUSPENDED": "disabled"}


def dispatch(action: str, connections, caller: Caller, body: dict):
    """操作の名前から行き先を引き、そこへ渡し、答えを外の言葉へ直す。"""
    route = ROUTES.get(action)
    if route is None:
        raise ManageError("UNKNOWN_ACTION", "その操作はありません。")
    return _outward(route(connections, caller, body))


def _outward(value):
    """ユースケースが返した型を、外が読む形へ直す。

    直すのは2つ。欄の名前（業務は artifact_id、外は artifactId）と、公開の状態
    （業務は PUBLISHED / SUSPENDED、外は active / disabled）。同じ概念の別の層の
    綴りであり、どちらかへ寄せるのではなく、この境界で翻訳する。

    欄の名前は機械的に直せるが、そうならないものもある（引き継ぎの from / to は
    Python の予約語と重なるため別の名前で持つ）。その場合は型の側が外向きの名前を
    宣言し、ここはそれに従う。
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {_outward_name(f): _outward_value(f.name, getattr(value, f.name))
                for f in fields(value)}
    if isinstance(value, (list, tuple)):
        return [_outward(v) for v in value]
    if isinstance(value, dict):
        return {k: _outward(v) for k, v in value.items()}
    return value


def _outward_name(f) -> str:
    """外が読む欄の名前。型が宣言していればそれを使い、無ければ機械的に直す。"""
    declared = f.metadata.get("json")
    if declared:
        return declared
    head, *rest = f.name.split("_")
    return head + "".join(w.capitalize() for w in rest)


def _outward_value(name: str, value):
    if name == "status" and isinstance(value, str):
        return OUTWARD_STATUS.get(value, value)
    return _outward(value)


# 業務上の失敗を、外の言葉へ写す。既定は400で、それ以外はここに並べる
STATUS = {
    PublishError: {"NOT_INVITED": 403},
    ProjectError: {"PROJECT_NOT_FOUND": 404},
    ViewTokenError: {"TARGET_NOT_FOUND": 404, "TOKEN_NOT_FOUND": 404},
    PublisherError: {"NOT_ADMINISTRATOR": 403},
    ManageError: {"ARTIFACT_NOT_FOUND": 404, "NOT_ADMINISTRATOR": 403,
                  "NOT_THE_PUBLISHER": 403},
}


def status_of(error) -> int:
    """その失敗を、外の言葉のどれで返すか。"""
    for kind, codes in STATUS.items():
        if isinstance(error, kind):
            return codes.get(error.code, 400)
    return 400
