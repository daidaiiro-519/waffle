"""棚卸しの引き継ぎ文書を、実際にやったことへ追いつかせる。

open のうち2件は作業中に決着した。残る2件は、いま advisor へ投げている。
"""
import json
import subprocess

PATH = ".waffle/documents/handoff/handoff-artifact-share-test-inventory.json"
CWD = "/home/daidaiiro/workspace/waffle"

findings = [
    {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 0,
     "resolutionStatus": "resolved",
     "note": "重複の件数は数え直して確定した。qa-advisor は18件と述べたが自身の表は12行で、そこへ直下どうしの4件と検出力を持たない1件を足して17件。1件ずつ対応先の実在を確かめてから消し、失われる確認は先にシナリオ側へ寄せて、わざと壊して落ちることを確かめた（2741320）"},
    {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 2,
     "resolutionStatus": "resolved",
     "note": "上げられたHTMLの読み取り4件は、qa-advisor の側を採って消した。契約表の9ケースを表駆動で回す検証が上位互換で、契約の欄が全て読み取りに現れることまで見ている。結果、公開の検証は3分割ではなく2つに割れた（業務の操作を走らせるものと、発行の口を直接呼ぶもの）"},
    {"advisor": "qa-advisor", "refBlock": "designViewpoints", "refIndex": 4,
     "resolutionStatus": "open",
     "note": "仕様へ昇格させるべき10件（qa-advisor は9件＋優先度の低い1件を挙げた）。所在は全て tests/application/unit/ 配下として実測済み。ddd-advisor へ1件ずつの判定を依頼中"},
    {"advisor": "qa-advisor", "refBlock": "designViewpoints", "refIndex": 3,
     "resolutionStatus": "open",
     "note": "qa-advisor からの差し戻し2件のうち、宣言された配置に受け皿が無い件（tech-lead-advisor 宛）は解消した——業務の操作の単体と外への出口の2つは実体を持ち、手元で動くプログラムには行を新設した。残るのは、方針が中核と述べる判断がドメインモデルで表されているか（ddd-advisor 宛）。依頼中"},
    {"advisor": "オーケストレータ", "refBlock": "implementationViewpoints", "refIndex": 4,
     "resolutionStatus": "resolved",
     "note": "検証が別の検証を取り込んでいた件は、移動の前提条件として先に済ませ、コミット済み（66591ec）。tech-lead-advisor は1件と見たが実際は2件あった"},
    {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 3,
     "resolutionStatus": "resolved",
     "note": "補助のモジュールは直下に残した。あわせて、スキル直下への道が6ファイルに散っていたのを結線のファイルへ寄せた——実装への道は既に1か所に通してあり、その説明自身が『各テストが自分で数えると階層を1つ変えるたびに全ファイルが壊れる』と述べているのに、出荷物と取り決めを読む道だけが揃っていなかった。実際、移動で2ファイルが読み込めなくなった（1549aa9）"},
    {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 6,
     "resolutionStatus": "open",
     "note": "残った検証の検出力を、証明の検証と保管との翻訳の2箇所に絞って機械的に裏取りする件。未着手"},
]

constraints = [
    "並行して別のセッションが、同じ検証の木のファイル名を一括で変えている（『段A』『段B』と番号が振られ、引き継ぎ書も作られている）。一度その途中の状態を掴んで作業を中断した。再開時に確かめたところ、相手の対象範囲はリポジトリ直下の検証だけで、この文脈は入っていなかった（一度巻き込んだのを戻したように見える）。今後も同じ木に手が入る可能性があるので、着手前に相手の状態を確かめること。",
    "仕様へシナリオを書き足す作業は、検証の整理とは別の判断として切り出した。切り離している間、シナリオの突き合わせが『欠落0件』であることは、シナリオが薄いために緑であるという状態を隠し続ける。",
    "直下の83件を消すと、宣言した重みづけとの乖離は改善せず悪化する。83件のうち41件は実質的に単体ないし契約に相当し、受け皿が空だったために直下に居るだけである。整理の目的は件数を減らすことではない。実際、17件だけを落として残りは移した。",
    "検証ファイルの名前の必須ルールは、対応する仕様の識別子から導くと定めていたが、シナリオに紐づかない検証はどれも確かめている対象で命名されている。既に運用されている限定を明文化した。",
    "手元で動くプログラムを確かめるものには、配置の宣言がどの行にも無かった。層の外にある領域だが、同じく層を持たないブラウザ向けの出荷物には既に行が与えられており、その先例に倣って行を足した。招かれた投稿者として動く受け口にはまだ確かめるものが無いので、行は分けていない。",
    "ランタイムをまたぐ合意の検証を、業務の側の契約の行へ置いてはならない。その行には『本物と偽実装の両方が同じスイートを満たす』という必須ルールが掛かっており、本物1つしか通らない検証を入れると、ルールが形式的には掛かっているのに実際には効いていない状態を作る。",
]

values = {
    "content.reviewStatus.findings": findings,
    "content.constraints.items": constraints,
}

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill",
     "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:500])
print("STDERR:", r.stderr[:300])
