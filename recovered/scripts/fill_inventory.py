"""テストの棚卸しの引き継ぎ文書へ、advisor 2体の判定を書き込む。

並行セッションが同じ木のファイル名を一括変更している最中なので、作業は着手せず
判断材料だけを残す。相手の「段A」の続きと合流させられる形にする。
"""
import json
import subprocess

PATH = ".waffle/documents/handoff/handoff-artifact-share-test-inventory.json"
CWD = "/home/daidaiiro/workspace/waffle"

values = {
    "tags": ["context:artifact-share"],
    "content.title.title":
        "テストの棚卸しを、重複の除去から配置の是正へ通す：handoff-artifact-share-test-inventory",
    "content.specRef.specRef": "uc-read-comments",
    "content.handoffKind.value": "specToImplementation",
    "content.description.text": (
        "検証の置き場所を宣言どおりに直す作業を引き継ぐ。tests/ 直下に12ファイル・83件が"
        "溜まっており、テスト規約の必須ルール『tests/ 配下は architecture が宣言する"
        "レイヤーを第一階層とし、テスト種別を第二階層とする』を満たしていない。ただし"
        "調べたところ、移す前に片付けるものがある。この引き継ぎが担う仕様は次の7件"
        "（uc-read-comments / uc-export-artifact / uc-list-my-artifacts / uc-transfer-artifact / "
        "uc-replace-content / uc-create-project / uc-invite-publisher）。"
    ),
    "content.expectedScope.items": [
        {"path": ".waffle/skills/artifact-share/tests/",
         "reason": "直下の12ファイル・83件を、宣言された階層へ移す。移す前に重複と足場の写しを片付ける"},
        {"path": ".waffle/documents/coding/test-standard-artifact-share.json",
         "reason": "手元で動くプログラムを確かめる行が無い。テストファイル名の必須ルールの対象範囲も実態と食い違っている"},
        {"path": ".waffle/documents/specs/bc-artifact-share/subdomain/sd-artifact-sharing/usecase/",
         "reason": "同型のシナリオが他のユースケースには在るのにここだけ欠けている、という非対称が9件ある"},
        {"path": ".waffle/skills/artifact-share/tests/manage_setup.py",
         "reason": "直下の4ファイルが同じ足場を private に写し持っている。寄せ先はここ"},
    ],
    "content.designViewpoints.items": [
        {"advisor": "tech-lead-advisor",
         "viewpoint": "契約の検証の置き場所は、層ではなく境界で決まる",
         "consideration": "これは持ち込んだ基準ではなく、宣言自身が書いていること。契約の対象として挙がっているものの1つは層の名前ではなく、配置の宣言がその食い違いを明示的に説明している。確かめている実装がどの層にあるかではなく、その合意が誰との間で結ばれているかで置き場所が決まる。"},
        {"advisor": "tech-lead-advisor",
         "viewpoint": "宣言に受け皿が無いものは、直下に溜まり続ける",
         "consideration": "宣言されているのに実体が無いディレクトリが2つあり、そこへ入るべきものが全部直下に紛れている。ディレクトリが実在しないことは、宣言が余分だった証拠ではなく、移動が済んでいない証拠である。逆に、手元で動くプログラムを確かめるものには宣言そのものが無く、これも溜まる原因になっている。"},
        {"advisor": "qa-advisor",
         "viewpoint": "移動という操作は、足場の重複を別の場所へ固定して見えにくくする",
         "consideration": "直下の4ファイルが、足場のファイルと同じものを写し持っている。偽物が別々に育ち片方だけが失敗を作れる状態になっていた、という事故が既に一度起きており、その記録が足場のファイル自身に残っている。写しを抱えたまま運ぶと同じ経路が再現する。統合が先、移動が後。"},
        {"advisor": "qa-advisor",
         "viewpoint": "宣言した重みづけと実態が逆向きに傾いている",
         "consideration": "方針はピラミッド型で単体を厚くすると宣言しているが、実測では単体が最も薄く、受け入れがその6倍ある。ただし原因は検証の書き方ではなく、単体の受け皿が空でそこへ入るべきものが直下に紛れていること。直下の83件はむしろ宣言へ引き戻す錘であり、消すと乖離は悪化する。"},
        {"advisor": "qa-advisor",
         "viewpoint": "非シナリオの検証が多いこと自体が、仕様の抜けを指している",
         "consideration": "同型のシナリオが他のユースケースには在るのに、ここだけ欠けているという非対称が9件ある。これは仕様がそう決めた結果ではなく、書き落としの兆候として読める。ただし仕様を書き足すのは検証の整理とは別の作業なので、切り分ける。"},
        {"advisor": "オーケストレータ（実測）",
         "viewpoint": "検証自身が古びることを止めている検証が2件ある",
         "consideration": "受け付ける操作はすべて行き先を持つこと、そしてその確認が表の全部を見ていること。後者は、この検証自身が対象の増加に追いつかなくなることを検知する。行き先を書き忘れた操作がすべて黙って名簿からの削除を実行していた、という実際の事故の再発防止でもある。移動の際に失わないこと。"},
    ],
    "content.implementationViewpoints.items": [
        {"advisor": "qa-advisor",
         "viewpoint": "移す前に、重複16件を消す",
         "consideration": "切り出し済みの受け入れシナリオと同じことを確かめているものが12件、直下どうしで重なっているものが4件。うち3件は、消すと失われる確認（表示名・冪等の比較・欄の名前ごと見る形）だけをシナリオ側へ寄せてから消す。1件ずつ対応先の実在を確かめてから消すこと。"},
        {"advisor": "qa-advisor",
         "viewpoint": "空疎な2件を直す",
         "consideration": "壊れた記録を1件も作らずに『壊れていない』を確かめているものが1件。数え上げを丸ごと定数へ変えても落ちない。もう1件は置かれた個数を見ており、順序という確かめたい性質ではなく、無関係な書き込みが1つ増えるだけで落ちる。順序の検出力は前段が既に担っている。"},
        {"advisor": "tech-lead-advisor",
         "viewpoint": "1ファイルに3つの関心が同居しているものは割る",
         "consideration": "公開の検証のうち、業務の操作を走らせるもの・読み取りの関数を直接呼ぶもの・発行の口を直接呼ぶものが1つのファイルに同居している。偶然3層に触れているのではなく、独立した3つの関心が同居している。分けると小さなファイルになるが、行数は配置の判断材料にならない——層の分け方の基準は『同じ理由で変更されるものをまとめる』であって大きさではない。"},
        {"advisor": "tech-lead-advisor",
         "viewpoint": "補助のファイルは直下に残す",
         "consideration": "足場のファイルは、直下を取り込みの道に載せる仕掛けに依存しており、既に全ての下層がそれを使って動いている。移すと下層が全部壊れる。これらは検証ではないので、階層の必須ルールの対象外。フックがこれらも警告するなら、直すのはファイルの位置ではなくルール本文の対象範囲。"},
        {"advisor": "オーケストレータ（実測）",
         "viewpoint": "検証が別の検証を足場として取り込んでいた",
         "consideration": "2つのファイルが、別の検証ファイルから足場を取り込んでいた。取り込みの道に載っているのは直下だけなので、取り込み元が別の階層へ動いた瞬間に無関係な2つが読み込めなくなる。移動の前提条件として先に断ち、寄せ先の足場のファイルに同じものが在ることを文字列の一致で確かめた。この1件は既に済ませてある。"},
        {"advisor": "qa-advisor",
         "viewpoint": "切り出しの残骸を一緒に運ばない",
         "consideration": "誰からも呼ばれない補助が2つ、足場から取り込んだ直後の再定義、足場のファイル自身の二重定義、中身が空の見出しだけが残っている箇所。いずれも読み手を惑わせる材料で、移す前に落とす。"},
        {"advisor": "qa-advisor",
         "viewpoint": "残ったものの検出力を、2箇所に絞って機械的に裏取りする",
         "consideration": "証明の検証と、保管と集約の翻訳の2ファイル。どちらも壊れても他のどの検証も落ちない領域なので、検出力が本物かを確かめる価値が高い。全体へ一律に掛けるのは費用が見合わない。"},
    ],
    "content.constraints.items": [
        "並行して別のセッションが、同じ検証の木のファイル名を一括で変えている（『段A』と番号が振られ、引き継ぎ書も作られている）。この引き継ぎが扱う移動と改名は、まったく同じ対象に手を入れる。着手前に相手の作業の状態を確かめ、合流させること。実際に一度、改名の途中の状態を掴んで作業を中断している。",
        "仕様へシナリオを書き足す作業（9件）は、この引き継ぎの対象に含めない。検証の整理とは別の判断で、仕様の変更にあたる。ただし切り離すことで、シナリオの突き合わせが『欠落0件』である現在の緑が、シナリオが薄いために緑であることを隠し続ける状態は残る。",
        "直下の83件を消すと、宣言した重みづけとの乖離は改善せず悪化する。83件のうち41件は実質的に単体ないし契約に相当し、受け皿が空だったために直下に居るだけである。整理の目的は件数を減らすことではない。",
        "検証ファイルの名前の必須ルールは、対応する仕様の識別子から導くと定めているが、直下の12ファイルはどれも仕様の識別子ではない。既存の非シナリオの検証2件も、確かめている対象で命名されている。ルール本文が実態に追いついていない状態で、これは今回生じる問題ではなく既に運用されている限定の明文化にあたる。",
        "手元で動くプログラムを確かめるものには、配置の宣言がどの行にも無い。層の外にある領域だが、同じく層を持たないブラウザ向けの出荷物には既に行が与えられており、先例はある。",
    ],
    "content.completionImage.layers": [
        {"label": "宣言", "description": "どこへ置くかを定める側。受け皿が無いものは足す",
         "nodes": [
             {"id": "place", "title": "テスト対象別の配置", "sub": "手元で動くプログラムの行を足す", "status": "existing"},
             {"id": "naming", "title": "検証ファイルの名づけ", "sub": "対象範囲をシナリオ対応分へ限定する", "status": "existing"},
         ]},
        {"label": "片付け", "description": "移す前に済ませるもの。移動はこれを別の場所へ固定してしまう",
         "nodes": [
             {"id": "dup", "title": "重複を消す", "sub": "16件（うち3件は先に寄せる）", "status": "new"},
             {"id": "scaffold", "title": "足場を1つに寄せる", "sub": "4ファイルの写しと残骸", "status": "new"},
         ]},
        {"label": "配置", "description": "宣言された階層へ移す。1ファイルは3つに割る",
         "nodes": [
             {"id": "appunit", "title": "業務の操作の単体", "sub": "application/unit（受け皿が空）", "status": "new"},
             {"id": "outint", "title": "外への出口", "sub": "adapters/outbound/integration（受け皿が空）", "status": "new"},
             {"id": "incontract", "title": "入口の契約", "sub": "adapters/inbound/contract", "status": "existing"},
             {"id": "cli", "title": "手元で動くプログラム", "sub": "宣言そのものが無い", "status": "new"},
         ]},
    ],
    "content.completionImage.relationships": [
        {"from": "place", "to": "cli", "kind": "dependency", "label": "行を足して初めて置き場所が決まる"},
        {"from": "dup", "to": "appunit", "kind": "dependency", "label": "消してから移す"},
        {"from": "scaffold", "to": "appunit", "kind": "dependency", "label": "寄せてから移す"},
        {"from": "naming", "to": "incontract", "kind": "dependency", "label": "限定しないと、宣言に反して見えるファイルが並ぶ"},
    ],
    "content.reviewStatus.requiredAdvisors": ["tech-lead-advisor", "qa-advisor"],
    "content.reviewStatus.findings": [
        {"advisor": "qa-advisor", "refBlock": "implementationViewpoints", "refIndex": 0,
         "resolutionStatus": "open",
         "note": "重複と判定された12件は1件ずつ対応先の実在を確かめ済み。ただし qa-advisor の件数の内訳が自身の表と合っていなかった（18件と述べているが表は12行）。着手時に再度数え直すこと"},
        {"advisor": "tech-lead-advisor", "refBlock": "implementationViewpoints", "refIndex": 2,
         "resolutionStatus": "open",
         "note": "公開の検証のうち読み取りの関数を直接呼ぶ4件について、tech-lead-advisor は割って移す、qa-advisor は契約表が上位互換なので消す、と判定が割れた。オーケストレータは消す側に寄ったが、着手前に確定させること"},
        {"advisor": "qa-advisor", "refBlock": "designViewpoints", "refIndex": 4,
         "resolutionStatus": "open",
         "note": "仕様へ昇格させるべき9件。この引き継ぎの対象外として切り出したが、どこかで扱う必要がある"},
        {"advisor": "qa-advisor", "refBlock": "designViewpoints", "refIndex": 3,
         "resolutionStatus": "open",
         "note": "qa-advisor から2件の差し戻しがある。方針が中核と述べる判断がドメインモデルで表されているのか（ddd-advisor へ）、宣言された配置に受け皿が無いこと（tech-lead-advisor へ）。前者は未確認"},
        {"advisor": "オーケストレータ", "refBlock": "implementationViewpoints", "refIndex": 4,
         "resolutionStatus": "resolved",
         "note": "検証が別の検証を取り込んでいた件は、移動の前提条件として先に済ませ、コミット済み（66591ec）。tech-lead-advisor は1件と見たが実際は2件あった"},
    ],
    "content.reviewStatus.completionImageConfirmedBy.confirmed": False,
}

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill",
     "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:900])
print("STDERR:", r.stderr[:400])
