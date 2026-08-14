"""棚卸しの引き継ぎ文書を、完了状態へ追いつかせる。"""
import json
import subprocess

PATH = ".waffle/documents/handoff/handoff-artifact-share-test-inventory.json"
CWD = "/home/daidaiiro/workspace/waffle"

findings = [
    {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 0,
     "resolutionStatus": "resolved",
     "note": "重複17件を落とした。qa-advisor は18件と述べたが自身の表は12行で、そこへ直下どうしの4件と検出力を持たない1件を足して17件。1件ずつ対応先の実在を確かめてから消し、失われる確認は先にシナリオ側へ寄せて、わざと壊して落ちることを確かめた（2741320）"},
    {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 2,
     "resolutionStatus": "resolved",
     "note": "上げられたHTMLの読み取り4件は qa-advisor の側を採って消した。結果、公開の検証は3分割ではなく2つに割れた。契約表の9ケースを表駆動で回す検証が上位互換で、契約の欄が全て読み取りに現れることまで見ている"},
    {"advisor": "qa-advisor", "refBlock": "designViewpoints", "refIndex": 4,
     "resolutionStatus": "resolved",
     "note": "昇格候補10件を ddd-advisor が1件ずつ判定し、7件を昇格した（85b93b2）。3件は既に別のブロックが同じことを述べていた。非対称の指摘は候補を挙げる力は強いが、宣言の欠落と宣言の所在違いを区別できない——受け入れシナリオだけを見ていれば2件を誤って足していた。あわせて、公開の『空の文書は公開できない』が無関係な基準を covers に書いていた壊れも直した"},
    {"advisor": "qa-advisor", "refBlock": "designViewpoints", "refIndex": 3,
     "resolutionStatus": "open",
     "note": "差し戻し2件のうち、配置に受け皿が無い件は解消した。もう1件（方針が中核と述べる判断がドメインモデルで表されているか）は ddd-advisor が『モデルは妥当。食い違っているのは方針の理由づけの文言で、閲覧可否は層を持たないランタイムに宿る』と判定し、形の測り方は qa-advisor の管轄として差し戻した。qa-advisor へ依頼中"},
    {"advisor": "オーケストレータ", "refBlock": "implementationViewpoints", "refIndex": 4,
     "resolutionStatus": "resolved",
     "note": "検証が別の検証を取り込んでいた件は、移動の前提条件として先に済ませた（66591ec）。tech-lead-advisor は1件と見たが実際は2件あった"},
    {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 3,
     "resolutionStatus": "resolved",
     "note": "補助のモジュールは直下に残した。あわせて、スキル直下への道が6ファイルに散っていたのを結線のファイルへ寄せた——実装への道は既に1か所に通してあり、その説明自身が『各テストが自分で数えると階層を1つ変えるたびに全ファイルが壊れる』と述べているのに、出荷物と取り決めを読む道だけが揃っていなかった。実際、移動で2ファイルが読み込めなくなった（1549aa9）"},
    {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 6,
     "resolutionStatus": "resolved",
     "note": "リスクが最も高い2箇所へ変異を11件注入し、10件は仕留められた。生き残った1件——署名方式の検査を外しても落ちない——は本物の穴だった。alg を none にする筋書きは署名も空にしてあるため、方式の検査を外しても署名の検証が拒む。通ってはいたが、説明が述べる理由とは別の理由で通っていた。方式の検査だけが拒む理由になる筋書きを足し、同じ変異が落ちることを確かめた（a3162d2）"},
]

values = {"content.reviewStatus.findings": findings}

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill",
     "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:400])
print("STDERR:", r.stderr[:200])
