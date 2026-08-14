"""spec を直す：値の宣言を足し、素の文字列だった欄に型を与え、文脈マップを訂正し、事前条件の文言を揃える。"""
import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SPECS = ".waffle/documents/specs/bc-artifact-share"
AGG = f"{SPECS}/aggregate"
UC = f"{SPECS}/subdomain/sd-artifact-sharing/usecase"


def q(path, block, expr="@"):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


def fill(path, values):
    r = subprocess.run(
        ["uv", "run", "waffle", "scaffold", "--operation", "fill",
         "--path", path, "--values", json.dumps(values, ensure_ascii=False)],
        capture_output=True, text=True, cwd=CWD)
    out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"raw": r.stdout}
    print(path, "->", json.dumps(out, ensure_ascii=False)[:400])
    if r.stderr.strip():
        print("  STDERR:", r.stderr[:300])


def retype(entities, entity_name, attr_name, new_type):
    """宣言済みの欄に型を与える。素の文字列のままだと取り違えが型で塞げない。"""
    for e in entities:
        if e["name"] != entity_name:
            continue
        for a in e.get("attributes", []):
            if a["name"] == attr_name:
                a["type"] = new_type
                return True
    raise SystemExit(f"見つかりません: {entity_name}.{attr_name}")


VIEW_SUBJECT = {
    "name": "ViewSubject",
    "represents": "1本の閲覧トークンで開ける対象",
    "behavior": "不変。共有アーティファクト1件を指すか、プロジェクト1つを指すかのいずれか。どちらも同じ形の閲覧トークンで開き、同じように止められるが、指しているものは別なので取り違えられないよう種別を持つ。閲覧の面がこれをどう見分けるか（鍵の付け方）は、この値には現れない。",
    "attributes": [{"name": "kind", "type": "string"}, {"name": "id", "type": "string"}],
}

VIEW_TOKEN_FINGERPRINT = {
    "name": "ViewTokenFingerprint",
    "represents": "1本の閲覧トークンが本物かを照合するための形",
    "behavior": "不変。閲覧トークンそのものは渡した相手の手元にしか無く、こちらは照合できる形だけを残す。中身の指紋とは別の概念なので、同じ語で呼ばない。どう作りどう並べるかは閲覧の面との取り決めであり、この値には現れない。",
    "attributes": [{"name": "value", "type": "string"}],
}

CONTENT_FINGERPRINT = {
    "name": "ContentFingerprint",
    "represents": "公開された中身が同じものかを確かめるための形",
    "behavior": "不変。中身そのものは集約の一貫性の境界の外にあり、集約はこの形だけを持つ。手元へ取り出したものが公開した中身と一致することを、あとから確かめるために使う。閲覧トークンの指紋とは別の概念なので、同じ語で呼ばない。",
    "attributes": [{"name": "value", "type": "string"}],
}

# --- agg-shared-artifact -------------------------------------------------
path = f"{AGG}/agg-shared-artifact.json"
vos = q(path, "valueObjects", "items")
vos.extend([VIEW_SUBJECT, VIEW_TOKEN_FINGERPRINT, CONTENT_FINGERPRINT])
ents = q(path, "entities", "items")
retype(ents, "SharedArtifact", "contentFingerprint", "ContentFingerprint")
retype(ents, "ArtifactViewToken", "fingerprint", "ViewTokenFingerprint")
fill(path, {"content.valueObjects.items": vos, "content.entities.items": ents})

# --- agg-project ---------------------------------------------------------
path = f"{AGG}/agg-project.json"
vos = q(path, "valueObjects", "items")
vos.extend([VIEW_SUBJECT, VIEW_TOKEN_FINGERPRINT])
ents = q(path, "entities", "items")
retype(ents, "ProjectViewToken", "fingerprint", "ViewTokenFingerprint")
fill(path, {"content.valueObjects.items": vos, "content.entities.items": ents})

# --- bc-artifact-share: 文脈マップの訂正 ---------------------------------
# 空は「他と直接やり取りしないという決定」を意味する。事実に反するので訂正する。
fill(f"{SPECS}/bc-artifact-share.json", {
    "content.contextMap.items": [{
        "counterpart": "招かれている人の名簿",
        "relationship": "従属（腐敗防止層を置く）",
        "content": "誰が招かれているかと、その人が管理者かどうかを名簿から受け取る。名簿はこの文脈の集約ではなく、役割の区分を決めているのも名簿の側である。名簿の語彙は PublisherDirectory の口で自分の言葉へ移し替える",
    }],
})

# --- 事前条件の文言を揃える ---------------------------------------------
# 同じ規則が2つの言い回しで宣言されていた。指しているものに違いは無い。
ADMIN = "操作する者が管理者であること"
fill(f"{UC}/uc-list-publishers.json", {"content.preconditions.items": [ADMIN]})
fill(f"{UC}/uc-invite-publisher.json", {
    "content.preconditions.items": [ADMIN, "外すときは、対象の人が現に招かれていること"]})
