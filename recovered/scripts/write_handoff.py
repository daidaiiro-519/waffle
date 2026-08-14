"""受け入れ条件と振る舞いのシナリオの対応を宣言する変更の、実装への引き継ぎ書。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
PATH = ".waffle/documents/handoff/handoff-criteria-scenario-link.json"

values = {
    "tags": ["context:waffle", "topic:traceability"],
    "content.title.title":
        "受け入れ条件と振る舞いのシナリオの対応を宣言できるようにする："
        "handoff-criteria-scenario-link",
    "content.specRef.specRef": "uc-check-criteria-coverage",
    "content.handoffKind.value": "specToImplementation",
    "content.description.text":
        "uc-check-criteria-coverage の実装と、それが読む宣言（受け入れ条件の識別子と、"
        "振る舞いのシナリオが満たす条件の並び）をスキーマへ入れるための引き継ぎ。"
        "既存の全仕様文書の移行手順を含む。",

    "content.designViewpoints.items": [
        {"advisor": "ddd-advisor",
         "viewpoint": "対応が多対多になるのは定義からの帰結である",
         "consideration":
             "受け入れ条件は「主張」で切り、振る舞いのシナリオは「流れ」で切る。"
             "切り口が違う2つの分割の間の対応は一般に多対多になる。"
             "既存文書にそう書かれているからではなく、定義からそうなる。"},

        {"advisor": "ddd-advisor",
         "viewpoint": "1つの条件は1つの主張である",
         "consideration":
             "「控え、かつ尋ねない」のように1項目に主張が2つ入っているものは、条件が2つある状態。"
             "識別子を振る前に割らないと、1つの識別子が2つの契約を指す状態が固定され、"
             "以後その識別子が何を指すかが読み手ごとに変わる。"
             "1項目に含まれる shall の個数は文字列だけで数えられる。"},

        {"advisor": "ddd-advisor",
         "viewpoint": "既定の多重度を、受け入れ条件と不変条件で分ける",
         "consideration":
             "受け入れ条件は When/If のトリガを持つため1対1が既定になる。"
             "不変条件は「常に」であり、1つの筋書きが示せるのは反例の起きない一断面にすぎないため、"
             "1対多が既定になる。同じ既定を当てると集約側がほぼ全件逸脱扱いになる。"},

        {"advisor": "ddd-advisor",
         "viewpoint": "識別子は業務の言葉ではない",
         "consideration":
             "識別子はどう名付けても業務語彙ではないため、"
             "それが仕様を指す一次的な手段になると、業務に詳しい人が参加できない語彙が中心に座る。"
             "人が読む成果物と会話では、識別子ではなく条件の文そのものを引用する。"
             "『受け入れ基準: 〜』という短縮ラベルの慣習も、この機会に廃止する。"},

        {"advisor": "ddd-advisor",
         "viewpoint": "0件禁止の趣旨は、不要物の排除ではなく条件の欠けの発見である",
         "consideration":
             "どの条件も指さないシナリオが0件で弾かれたとき、書き手が取るべき行動は"
             "シナリオを消すことではなく条件を書き足すこと。"
             "この趣旨を書き手向けの指示に明記しないと、規則が逆向きに働く。"},
    ],

    "content.implementationViewpoints.items": [
        {"advisor": "tech-lead-advisor",
         "viewpoint": "同型の実装が既にあり、新しい検知の考え方は要らない",
         "consideration":
             "check_spec_integrity の orphaned_value_objects が、"
             "「同一文書内で宣言された名前の集合から、別のブロックが参照した名前の集合を引く」"
             "という一字一句同じ演算をしている。これを写せばよい。"},

        {"advisor": "tech-lead-advisor",
         "viewpoint": "純ロジックと取得を層で分ける",
         "consideration":
             "domain/services/criteria_coverage.py に document の dict だけを受け取る純関数を置き、"
             "application/usecases/check_criteria_coverage.py が port 経由で読んで回す。"
             "scenario_drift.py と check_scenario_drift.py の対がそのまま手本になる。"
             "check_spec_integrity.py は集合演算をアプリケーション層に直書きしているが、これは真似ない。"},

        {"advisor": "tech-lead-advisor",
         "viewpoint": "対の表を2箇所に持たない",
         "consideration":
             "どの条件ブロックがどの筋書きブロックと対をなすかの表は、"
             "scenario_drift.py の _SCENARIO_BLOCK_KEYS を拡張して1箇所に置く。"
             "同じ知識を2箇所に持つと、対を増やしたとき片方だけが古くなる。"},

        {"advisor": "tech-lead-advisor",
         "viewpoint": "実在検査は validate では実現できない",
         "consideration":
             "同一文書内の別配列に値が実在するかは、いまの検証器（JSON Schema 単体）の語彙では表現できない。"
             "識別子の重複も uniqueItems では弾けない（要素オブジェクト全体の同一性しか見ないため）。"
             "どちらも新設する検査の結果キーとして実装する。"},

        {"advisor": "tech-lead-advisor",
         "viewpoint": "未記入を一括で報告しない",
         "consideration":
             "「黙って対象外にしない」作法は既に3箇所に実装されているが、"
             "いずれも報告範囲が書き込み対象に絞られている。"
             "移行中の未記入が毎回すべて鳴る形は同型ではなく、3回目には読まれなくなる。"
             "未記入は件数の要約に留め、実データの列挙は明示的な全体走査のときだけにする。"},

        {"advisor": "tech-lead-advisor",
         "viewpoint": "識別子の不変性は機械では強制できない",
         "consideration":
             "書き込み保護はトップレベル欄にしか効かず、配列要素の中のフィールドには仕組みが無い。"
             "また前の版と比べる実装が存在しない（既存の検査はすべて現在のツリーだけを見る）。"
             "不変性は規約として運用に回すしかない。"},

        {"advisor": "tech-lead-advisor",
         "viewpoint": "既存の照合には干渉しない",
         "consideration":
             "筋書きと検証コードの照合が読むのは name と gherkin の2欄だけで、"
             "欄を1つ増やしても変化しない。既に operation 欄という前例もある。"
             "一方、描画側は影響を受ける——条件が構造になるため、"
             "x-render の宣言を箇条書きから表へ変える必要がある（レンダラ側の変更は不要）。"},

        {"advisor": "tech-lead-advisor",
         "viewpoint": "操作保証も同時に構造を決める",
         "consideration":
             "操作保証とその筋書きも同じ形をしている。別々にやると、"
             "版を2回上げ、全文書を2回移行し、対の表を2回書くことになる。"
             "構造は同時に、データの移行は後の波でよい。"},
    ],

    "content.constraints.items": [
        "業務サービスは対象外とする。受け入れ条件の欄そのものが存在せず（責務の散文だけ）、"
        "対の片側が無い。欄を設けるかどうかは別の判断が要る。",

        "この検査が担保するのは「対応が書かれていること」までで、「その対応が正しいこと」は担保しない。"
        "シナリオの Then が指した条件を実際に確かめているかは機械には判定できない。"
        "位置づけは品質のゲートではなく、読むべき箇所の当たり付けとする。",

        "識別子は読んでも正しく見えるため、無関係な対応を書かれても気づけない。"
        "この点は廃止する自由文の欄より悪化する（散文なら読めば言い換えだと分かる）。"
        "対応の妥当性は読み手の責務であることを、書き手向けの指示に残す。",

        "移行中は識別子を必須にできない。必須にした瞬間、移行が済むまで全文書が検証不適合になる。"
        "スキーマ上は任意とし、未記入は新設する検査が報告する分担にする。",

        "廃止する対応欄の値は、全体では約88%が記入されている。"
        "識別子への翻訳の下書きとして使えるため、欄の削除は移行完了後の最後の手順とする。"
        "先に消すと、唯一の人手の対応情報を失う。",
    ],

    "content.completionImage.layers": [
        {"label": "呼出口",
         "nodes": [
             {"id": "cli", "title": "受け入れ条件の被覆を確かめる", "sub": "CLI / MCP"},
         ]},
        {"label": "アプリケーション",
         "nodes": [
             {"id": "uc", "title": "被覆の確認", "sub": "CheckCriteriaCoverage"},
         ]},
        {"label": "ドメイン",
         "nodes": [
             {"id": "svc", "title": "被覆の突き合わせ", "sub": "criteria_coverage（純関数）"},
             {"id": "keys", "title": "条件と筋書きの対の表", "sub": "scenario_drift（拡張）"},
         ]},
        {"label": "宣言",
         "nodes": [
             {"id": "crit", "title": "受け入れ条件", "sub": "識別子を持つ構造"},
             {"id": "scen", "title": "振る舞いのシナリオ", "sub": "満たす条件の並び"},
         ]},
    ],
    "content.completionImage.relationships": [
        {"from": "svc", "to": "keys", "kind": "dependency",
         "label": "対の表を1箇所から読む"},
        {"from": "uc", "to": "cli", "kind": "split",
         "label": "文書1件と走査範囲の2系統を持つ"},
    ],

    "content.usageExamples.items": [
        "waffle check-criteria-coverage --path <仕様文書> → "
        "{unreferenced, dangling, duplicate_ids, unlinked_scenarios, uncovered_by_omission}",
        "waffle check-criteria-coverage --documentsRoot <走査範囲> → 配下の全仕様文書をまとめて確かめる",
        "指されていない条件が1件も無ければ unreferenced は空配列で返る",
    ],

    "content.expectedScope.items": [
        {"path": "src/waffle/domain/model/DomainSpecSchema/v9.json",
         "reason": "受け入れ条件・操作保証に識別子を足し、筋書きの covers を satisfies へ置き換える"},
        {"path": "src/waffle/domain/services/criteria_coverage.py",
         "reason": "宣言された識別子の集合と参照された識別子の集合を突き合わせる純関数（新規）"},
        {"path": "src/waffle/domain/services/scenario_drift.py",
         "reason": "条件ブロックと筋書きブロックの対の表を、ここへ拡張して1箇所に持つ"},
        {"path": "src/waffle/application/usecases/check_criteria_coverage.py",
         "reason": "port 経由で文書を読み、純関数を回す編成（新規）"},
        {"path": "src/waffle/adapters/inbound/cli/main.py",
         "reason": "コマンドの登録"},
        {"path": "src/waffle/adapters/inbound/mcp/main.py",
         "reason": "コマンドの登録"},
        {"path": ".waffle/documents/specs/",
         "reason": "全仕様文書の移行（識別子の付与と、対応欄からの翻訳）。文書単位で進める"},
        {"path": ".waffle/templates/blank/DomainSpecSchema/v9/",
         "reason": "空欄テンプレートの再生成。版を上げても自動では追随しない"},
        {"path": ".waffle/hooks/check-drift-on-write.py",
         "reason": "仕様文書への書き込みを捕まえる既存の分岐へ、新しい検査を足す"},
    ],

    "content.reviewStatus.requiredAdvisors": ["ddd-advisor", "tech-lead-advisor"],
    "content.reviewStatus.findings": [
        {"advisor": "ddd-advisor", "refBlock": "designViewpoints", "refIndex": 1,
         "resolutionStatus": "open",
         "note": "複合文を割る手順を、移行の第1段階として実施するか未決。"
                 "1項目の shall の個数を数える手段を持つかどうかも決まっていない。"},
        {"advisor": "ddd-advisor", "refBlock": "designViewpoints", "refIndex": 3,
         "resolutionStatus": "open",
         "note": "短縮ラベルの慣習を廃止する範囲（描画・書き手向けの指示のどこまで）が未決。"},
        {"advisor": "tech-lead-advisor", "refBlock": "implementationViewpoints", "refIndex": 4,
         "resolutionStatus": "open",
         "note": "未記入の報告先を、書き込み範囲に絞る形と全体走査で分ける方針は決まったが、"
                 "具体的な出し分けは未決。"},
        {"advisor": "tech-lead-advisor", "refBlock": "implementationViewpoints", "refIndex": 7,
         "resolutionStatus": "resolved",
         "note": "操作保証は構造を同時に決め、データの移行は後の波とする。"},
    ],
    "content.reviewStatus.completionImageConfirmedBy.confirmed": False,
    "content.reviewStatus.completionImageConfirmedBy.confirmedBy": "",
    "content.reviewStatus.completionImageConfirmedBy.confirmedAt": "",
    "content.reviewStatus.completionImageConfirmedBy.note": "",
}

r = subprocess.run(["uv", "run", "waffle", "scaffold", "--operation", "fill",
                    "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
                   capture_output=True, text=True, cwd=CWD)
print((r.stdout or r.stderr).strip()[:500])

v = subprocess.run(["uv", "run", "waffle", "validate", "--path", PATH],
                   capture_output=True, text=True, cwd=CWD)
print((v.stdout or v.stderr).strip()[:400])
