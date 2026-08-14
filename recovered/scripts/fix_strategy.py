"""重心の宣言を、この文脈のために初めて決める。

いままで入っていたのは既定値で、3つの規約文書に一字一句同じものが並んでいた。
実測に合わせるのではなく、行われていなかった判断をいま行って記録する。
"""
import json
import subprocess

PATH = ".waffle/documents/coding/test-standard-artifact-share.json"
CWD = "/home/daidaiiro/workspace/waffle"

RATIONALE = (
    "手入れの可否——公開する・止める・再開する・引き継ぐ——は集約のメソッドとして表し、"
    "ユースケースはそれを呼ぶだけにする。だからその判断は集約の単体で確かめる。"
    "一方、閲覧してよいかの判断は、閲覧者が来たその瞬間に答える必要があるため、"
    "層を持たない閲覧ゲートのランタイムに宿る。業務のLambdaの側には無いので、"
    "そちらは入口の取り決めとして確かめる。可否の判断が2か所に分かれているこの非対称のため、"
    "重心は集約の単体へは寄らない。"
    "\n\n"
    "最も厚くなるのはユースケースである。検証を仕様のシナリオへ1対1で束ねると決めている以上、"
    "その数は仕様の量で決まる。偽物を相手に手元で走るので、厚くても帰りは速い。"
    "\n\n"
    "外への出口を厚くするのは、証明の検証が破れると、招かれていない者が他人の文書を"
    "開けるようになるため。この文脈で影響が最も大きい。実際のAWSに触れる検証は費用と"
    "実行時間が乗るので行わず、境界の取り決めと偽物相手の検証で代える。"
)

values = {
    "content.testStrategy.shape": "diamond",
    "content.testStrategy.weights": [
        {"testType": "unit", "emphasis": "medium"},
        {"testType": "integration", "emphasis": "high"},
        {"testType": "acceptance", "emphasis": "high"},
        {"testType": "contract", "emphasis": "medium"},
        {"testType": "e2e", "emphasis": "none"},
    ],
    "content.testStrategy.rationale": RATIONALE,
}

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill",
     "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:400])
print("STDERR:", r.stderr[:300])
