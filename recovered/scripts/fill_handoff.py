"""Handoff（domain 3分割）へ値を書き込む。advisor 2体の見解と、未決着の対立を記録する。"""
import json
import subprocess

PATH = ".waffle/documents/handoff/handoff-artifact-share-domain-layout.json"

values = {
    "title": {
        "blockType": "Title",
        "title": "業務の語彙が住む棚を3つに分ける：handoff-artifact-share-domain-layout",
    },
    "specRef": {
        "blockType": "SpecRef",
        "title": "引き継ぎ元spec",
        "specRef": "agg-shared-artifact",
    },
    "handoffKind": {"blockType": "HandoffKind", "value": "specToImplementation"},
    "description": {
        "blockType": "Description",
        "title": "概要",
        "text": (
            "artifact-share の業務の語彙の置き場所を、いまの1つの棚（domain 直下）から、"
            "Waffle 本体と同じ3つの棚（entities / value_objects / services）へ分ける作業を引き継ぐ。"
            "同じヘキサゴナルの流儀を採っておきながら棚の分け方だけが違っており、"
            "そのため宣言された概念（集約・値・業務サービス）を検査が区別できない状態にある。"
            "この引き継ぎが担う仕様は次の4件（agg-shared-artifact / agg-project / agg-comment / "
            "bc-artifact-share の業務サービス ResolveViewability）。"
        ),
    },
    "expectedScope": {
        "blockType": "ExpectedScope",
        "title": "対象範囲の見込み",
        "items": [
            {"path": ".waffle/documents/coding/architecture-artifact-share.json",
             "reason": "conceptPlacement の置き場所を3つへ分け、layout.tree を追随させる。domain-service の pattern も直す"},
            {"path": ".waffle/skills/artifact-share/lambda/admin_api/domain/entities/",
             "reason": "集約ルート SharedArtifact / Project の新しい置き場所"},
            {"path": ".waffle/skills/artifact-share/lambda/admin_api/domain/value_objects/",
             "reason": "宣言済みの値の置き場所。いま集約ファイルの中に同居している8つをここへ出す"},
            {"path": ".waffle/skills/artifact-share/lambda/admin_api/domain/services/",
             "reason": "業務サービスの置き場所。宣言だけあって実装が無い ResolveViewability もここへ"},
            {"path": ".waffle/skills/artifact-share/lambda/admin_api/domain/caller.py",
             "reason": "domain の語彙ではないため、この層から出す"},
            {"path": ".waffle/skills/artifact-share/lambda/admin_api/domain/identifier.py",
             "reason": "推測できない並びを作る手立てが実行環境に結びついているため、この層から出す"},
            {"path": ".waffle/skills/artifact-share/lambda/admin_api/application/ports/",
             "reason": "識別子を発行する口を新しく宣言する。既にある時計の口と同じ形にする"},
            {"path": ".waffle/skills/artifact-share/lambda/admin_api/adapters/outbound/",
             "reason": "識別子を発行する口の実装を置く。同名の別関数（トークンの指紋）の改名もここ"},
            {"path": ".waffle/skills/artifact-share/tests/",
             "reason": "48ファイル・約72箇所の取り込み先の書き換え。振る舞いは変えない"},
        ],
    },
    "designViewpoints": {
        "blockType": "DesignViewpoints",
        "title": "設計観点",
        "items": [
            {"advisor": "ユーザー",
             "viewpoint": "同じ流儀を採るなら棚の分け方も揃える",
             "consideration": "artifact-share と Waffle 本体はどちらもポートとアダプターの流儀を採っている。それでいて業務の語彙の棚だけが片方は1つ、もう片方は3つに分かれている。違える理由がどこにも記録されていない以上、揃える側に倒す。"},
            {"advisor": "tech-lead-advisor",
             "viewpoint": "棚を1つにしていると、検査が概念を見分けられない",
             "consideration": "集約も値も業務サービスも同じ場所を指しているため、そこに置かれたものが何なのかを宣言から機械的に言えない。3つに分けて初めて、宣言した概念ごとに正しい場所と突き合わせられる。宣言だけあって実装の無い業務サービスの置き場所も、これで決まる。"},
            {"advisor": "tech-lead-advisor",
             "viewpoint": "棚へ移す前に、その層にあるべきかを1件ずつ問い直す",
             "consideration": "いま domain にある8つのうち3つは、「domain に置かれている」という事実だけが所属の根拠になっていた。移動先を決めてから所属を追認すると、誤った所属が新しい棚で固定される。棚を増やす作業に見えるが、順序は逆である。"},
            {"advisor": "ddd-advisor",
             "viewpoint": "実装にあって仕様に無い語彙は、仕様が追いついていない合図",
             "consideration": "閲覧トークンで開ける対象は、業務サービスの説明文が既に名前を伏せたまま説明している。名前が仕様に無いだけで、概念は仕様にある。こうした語彙は実装都合ではないので、仕様へ宣言を足す側で解く。"},
            {"advisor": "tech-lead-advisor",
             "viewpoint": "宣言の側が実態より狭いときは、宣言を直す",
             "consideration": "業務サービスの書き方として「複数の集約を跨る判断」とだけ宣言しているが、Waffle 本体の同じ棚には単一の関心事に閉じた計算が20件以上並び、それで検査を通している。つまりこれは定義ではなく代表例の一つである。実装を宣言へ無理に合わせるのではなく、宣言の文言を実態へ広げる。"},
            {"advisor": "tech-lead-advisor",
             "viewpoint": "外から見えない仕組みに結びつく依存だけを、この層から出す",
             "consideration": "判断の基準は「外部の作者が書いたものか」ではなく「実行環境・基盤・枠組みに結びついているか」。同じ入力に同じ答えを返すだけの計算は、標準の部品を使っていてもこの層に残せる。逆に、環境から予測できない値を読むものは残せない。"},
            {"advisor": "ddd-advisor",
             "viewpoint": "素の型のまま扱うと、業務ルールが散る",
             "consideration": "照合できること・読み違えにくいこと・分類の目印が一組で一貫していること。いずれも業務上の約束なのに、文字列や辞書のまま扱われているため、どこか一箇所を直しても他が古いまま残る。"},
        ],
    },
    "implementationViewpoints": {
        "blockType": "ImplementationViewpoints",
        "title": "実装観点",
        "items": [
            {"advisor": "tech-lead-advisor",
             "viewpoint": "ファイルごと動かすだけでは終わらない",
             "consideration": "集約のファイルの中に、宣言済みの値が8つ同居している。ファイルごと集約の棚へ移すと、それらが値の棚ではない場所に取り残され、新しい宣言と食い違う。値を切り出す作業は、棚を分ける以上、避けて通れない。"},
            {"advisor": "tech-lead-advisor",
             "viewpoint": "宣言を先に直してから実装を動かす",
             "consideration": "置き場所の宣言と業務サービスの書き方の宣言を先に直さないと、実装を動かした瞬間に宣言と食い違う。図は宣言の投影なので、宣言を直してから図を追随させる。逆はしない。"},
            {"advisor": "tech-lead-advisor",
             "viewpoint": "1ファイルに1つという宣言は、いまは足さない",
             "consideration": "値について1ファイル1つを宣言すると、2つの集約が共有している閲覧トークンの値をばらばらのファイルへ割ることになり、共有を保つという決定と正面から衝突する。本体側も同じ宣言のまま3つの棚で通しているので、必要になった実例が出てから足せばよい。"},
            {"advisor": "tech-lead-advisor",
             "viewpoint": "識別子を発行する口は、既にある時計の口と同じ形にする",
             "consideration": "同じ形の先例が既にこの中にあるので、新しい設計判断を要しない。閲覧トークンの側は、発行された値を引数で受け取る形へ変えると、この層から発行の仕組みへの依存が消える。テスト規約が求める「決まった値に固定する」も同じ継ぎ目で満たせる。"},
            {"advisor": "tech-lead-advisor",
             "viewpoint": "操作している人を表す値は、書き換えられないようにする",
             "consideration": "許してよいかを判じたあとで、管理者かどうかを差し替えられる経路が残る。判断の入力は動かせない形にする。"},
            {"advisor": "ddd-advisor",
             "viewpoint": "仕様と実装で名前が食い違っている箇所を、同じ機会に直す",
             "consideration": "コメントに添える判定は、仕様の言葉と実装の言葉が別々になっている。指しているものの振る舞いに違いは無いので、これは書き分けではなく単なる言い換えの乱立である。自分たちが動かせる側（実装の名前）を仕様へ寄せる。"},
            {"advisor": "オーケストレータ（実測）",
             "viewpoint": "取り込み先の書き換えは48ファイル・約72箇所",
             "consideration": "実装28・テスト20。配布の仕組みは業務の語彙の置き場所を名指ししておらず、テストの取り込み方も道ごと見る設定になっているため、棚を増やしても壊れない。移動そのものは安全で、判断を要するのは分類だけである。"},
            {"advisor": "オーケストレータ（実測）",
             "viewpoint": "同名の別関数が層をまたいで2つある",
             "consideration": "指紋という同じ名前の関数が、業務の語彙の側と外への出口の側に1つずつあり、指している対象が違う（中身と閲覧トークン）。どちらの層のものか名前から判別できないので、片方を改名する。"},
        ],
    },
    "constraints": {
        "blockType": "Constraints",
        "title": "既知の制約・トレードオフ",
        "items": [
            "宣言と実装の対応を確かめる仕組みは、業務の語彙を1つの根の下からしか探せない。層を持たないと宣言した出荷物（閲覧画面・閲覧ゲート・管理画面・環境の定義）にある実装は、この作業を終えても見えないままである。ここを解くには宣言の側に複数のランタイムを表す手立てが要り、それは別サイクルになる。",
            "閲覧可否の判定は、宣言だけがあって業務の語彙の側に実装が無い。振る舞いはエッジの関門が持っている。棚を作っても、正本をこちらへ置くかエッジを正とするかは別の判断であり、この作業だけでは決まらない。",
            "仕様は補完（最小の手続き）と宣言しているが、実装は不変条件を持つ集約と書き換えられない値を厚く持っている。実装を薄い側へ巻き戻すことはしない。仕様の記述が実装に追いついていないずれとして、別に扱う。",
            "コメントの集約には型が無く、そのため仕様の言葉と実装の言葉のずれが誰にも気づかれていない。棚を3つに分けること自体はこのずれを直さない。型を作って初めて、この種のずれが検知できるようになる。",
            "以前の引き継ぎに『2つの集約が共有する閲覧トークンの値は、既知の非両立として報告され続ける』と記録されているが、これは既に解消済みである。共有される値はディレクトリ単位で探されるようになっており、実際に0件で通る。古い記録を根拠に『緑にしなくてよい』と判断しないこと。",
        ],
    },
    "completionImage": {
        "blockType": "CompletionImage",
        "title": "完成イメージ",
        "layers": [
            {"label": "業務の語彙", "description": "3つの棚に分かれ、宣言された概念ごとに置き場所が決まっている。何が置かれているかを、宣言から機械的に言える",
             "nodes": [
                 {"id": "ent", "title": "整合性の境界を持つもの", "sub": "domain/entities", "status": "new"},
                 {"id": "vo", "title": "書き換えられない値", "sub": "domain/value_objects", "status": "new"},
                 {"id": "svc", "title": "集約の内側に置けない判断", "sub": "domain/services", "status": "new"},
             ]},
            {"label": "業務の語彙から外へ出るもの", "description": "この層の語彙ではないと判定され、別の持ち場へ移ったもの",
             "nodes": [
                 {"id": "caller", "title": "操作している人", "sub": "application", "status": "new"},
                 {"id": "idgen", "title": "識別子を発行する", "sub": "口の宣言と、外への出口の実装", "status": "new"},
             ]},
            {"label": "宣言", "description": "置き場所と書き方を定める側。実装より先に直す",
             "nodes": [
                 {"id": "arch", "title": "配置の宣言", "sub": "architecture-artifact-share", "status": "existing"},
                 {"id": "spec", "title": "語彙の宣言", "sub": "集約仕様・文脈仕様", "status": "existing"},
             ]},
        ],
        "relationships": [
            {"from": "arch", "to": "ent", "kind": "dependency", "label": "どの概念をどこへ置くかを定める"},
            {"from": "arch", "to": "vo", "kind": "dependency", "label": "同上"},
            {"from": "arch", "to": "svc", "kind": "dependency", "label": "同上"},
            {"from": "ent", "to": "vo", "kind": "split", "label": "同居していた値を切り出す"},
        ],
    },
    "usageExamples": {
        "blockType": "UsageExamples",
        "title": "使われ方（実際の呼び出し例）",
        "items": [
            {"scenario": "分け終えたことを確かめる",
             "example": "waffle check-aggregate-class-drift --architectureRef architecture-artifact-share",
             "note": "集約・値のいずれもが、新しい宣言どおりの場所で見つかること。コメントの集約は別の判断（型を作るか）が決まるまで欠落として残る"},
            {"scenario": "層の分かれ方が壊れていないことを確かめる",
             "example": "waffle check-layer-drift --architectureRef architecture-artifact-share",
             "note": "移動の前後で違反0・循環0が変わらないこと"},
            {"scenario": "振る舞いを変えていないことを確かめる",
             "example": "cd .waffle/skills/artifact-share && pytest tests/ -q",
             "note": "310件が緑のままであること。棚を分ける作業で件数が減ったら、取り込み先の書き換え漏れ"},
        ],
    },
    "reviewStatus": {
        "blockType": "ReviewStatus",
        "title": "レビュー状況",
        "requiredAdvisors": ["ddd-advisor", "tech-lead-advisor"],
        "findings": [
            {"advisor": "tech-lead-advisor", "refBlock": "implementationViewpoints", "refIndex": 0,
             "resolutionStatus": "resolved",
             "note": "ファイルごと動かすだけで済むという当初の見込みが誤りだった指摘を受け、集約に同居する値の切り出しを作業に含めた"},
            {"advisor": "ddd-advisor", "refBlock": "designViewpoints", "refIndex": 3,
             "resolutionStatus": "resolved",
             "note": "閲覧トークンで開ける対象が仕様に宣言されていない指摘を受け、仕様へ足す側で解くことを観点に加えた"},
            {"advisor": "tech-lead-advisor", "refBlock": "designViewpoints", "refIndex": 4,
             "resolutionStatus": "resolved",
             "note": "業務サービスの書き方の宣言が実態より狭い指摘を受け、宣言を直す側で解くことにした"},
            {"advisor": "ddd-advisor", "refBlock": "designViewpoints", "refIndex": 6,
             "resolutionStatus": "open",
             "note": "許してよいかの判定をどこへ置くか。ddd-advisor は業務ルールなので集約の内側へ、tech-lead-advisor は操作している人を表す値と一緒に application へ（この層から application へは依存できないため片方だけ残せない）。未決着"},
            {"advisor": "ddd-advisor", "refBlock": "designViewpoints", "refIndex": 6,
             "resolutionStatus": "open",
             "note": "中身の指紋の置き場所。ddd-advisor は書き換えられない値を新しく宣言してその内側へ、tech-lead-advisor は業務サービスの棚へ置き宣言の文言を直す。未決着"},
            {"advisor": "ddd-advisor", "refBlock": "designViewpoints", "refIndex": 5,
             "resolutionStatus": "open",
             "note": "上げられたHTMLの読み取りを割るかどうか。ddd-advisor は読み解きを外への出口へ出し組み立て規則だけを値の側へ、tech-lead-advisor は割らずに業務サービスの棚へ（同じ入力に同じ答えを返すだけなのでこの層に残せる）。未決着"},
            {"advisor": "ddd-advisor", "refBlock": "implementationViewpoints", "refIndex": 3,
             "resolutionStatus": "open",
             "note": "識別子の発行の置き場所。ddd-advisor は宣言済みの値が生成規則を持つべき、tech-lead-advisor は口を立てて外への出口へ。tech-lead-advisor 自身が『確かめるのは値の側、作るのは出口の側』と述べており、合流する余地がある。未決着"},
            {"advisor": "オーケストレータ", "refBlock": "constraints", "refIndex": 1,
             "resolutionStatus": "open",
             "note": "閲覧可否の判定の正本をこちらへ置くか、エッジを正とするか。ddd-advisor はこちらを正本にしエッジは複製として突き合わせるべきとしている。この作業に含めるかを含めて未決着"},
        ],
        "completionImageConfirmedBy": {"confirmed": False, "confirmedBy": "", "confirmedAt": "", "note": ""},
    },
}

result = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill",
     "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd="/home/daidaiiro/workspace/waffle")
print(result.stdout[:3000])
print("STDERR:", result.stderr[:1500])
