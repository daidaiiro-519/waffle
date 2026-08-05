"""引き継ぎのテストが共有する結線。"""
import json

import pytest

import main
from publisher_setup import FakeDirectory
from manage_setup import (
    HTML, NOW, VIEWER_DOMAIN, FakeKeyStore, FakeStore, meta_of,
)
from application.ports import Caller
from application.usecases.publish_artifact import PublishArtifact
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.suspend_artifact import SuspendArtifact
from application.usecases.transfer_artifact import TransferArtifact
from shared.errors import ManageError, PublisherError
from usecase_builder import build

X = Caller("publisher-x")
Y = Caller("publisher-y")
ADMIN = Caller("admin-1", is_admin=True)


def setup():
    """XがAを公開しており、Yも招かれている状態を作る。"""
    store, keys = FakeStore(), FakeKeyStore()
    publishing = main.Connections(
        store=store, keys=keys, identify=lambda _t: X.id,
        wrapper_template="<html>{{アーティファクトID}}</html>",
        now=lambda: NOW, viewer_domain=VIEWER_DOMAIN)
    result = build(publishing, PublishArtifact).run(
        {"html": HTML, "authorization": "Bearer x"})
    deps = main.Connections(
        store=store, keys=keys,
        directory=FakeDirectory({
            X.id: {"email": "x@example.com", "status": "PUBLISHED"},
            Y.id: {"email": "y@example.com", "status": "PUBLISHED"},
            ADMIN.id: {"email": "a@example.com", "status": "PUBLISHED"},
        }),
        now=lambda: NOW + 100, viewer_domain=VIEWER_DOMAIN)
    return deps, result
