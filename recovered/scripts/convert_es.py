"""書き起こし版 event-sourced-domain-model.md を KnowledgeSchema/v6 へ変換する（9本目）。

書籍の実例（見込み客の履歴・人名・サポートチケット）は、架空の業務（配送の依頼）へ置き換える。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = ".waffle/documents/knowledge/event-sourced-domain-model." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def n(name, kind, summary, *, src=None, figure=None, verbatim=None, children=None):
    d = {"name": name, "kind": kind, "summary": summary}
    for k, v in (("sourceRef", src), ("figure", figure), ("verbatim", verbatim),
                 ("children", children)):
        if v:
            d[k] = v
    return d


def e(f, t, label=None):
    d = {"from": f, "to": t}
    if label:
        d["label"] = label
    return d


def fig(intent, reading, nodes, edges, *, direction="LR", groups=(), notes=()):
    return {"intent": intent, "reading": reading, "direction": direction,
            "groups": [{"label": g, "nodes": ns} for g, ns in groups],
            "nodes": list(nodes), "edges": edges,
            "notes": [{"anchor": a, "note": t} for a, t in notes]}


def code(intent, reading, lang, source):
    return {"intent": intent, "reading": reading, "lang": lang, "source": source}


# ── 図 ────────────────────────────────────────────────────────────────

FIG_STORE = fig(
    "イベントストアと集約のあいだで、何が行き来するかを示す",
    "集約はイベントストアから履歴を読んで自分を組み立て、実行の結果として生まれたイベントを書き戻す。",
    ["イベントストア", "集約", "新しいイベント"],
    [e("イベントストア", "集約", "履歴を読んで状態を作り直す"),
     e("集約", "新しいイベント", "コマンドを実行した結果"),
     e("新しいイベント", "イベントストア", "追記する")],
    notes=[
     ("新しいイベントからイベントストア",
      "追記だけで、書き換えも削除も無い。図では他の線と同じ矢印に見えるが、"
      "この線だけが一方通行で取り消せない。"),
     ("イベントストアから集約",
      "読み込むのは履歴の全部であって、保存された状態ではない。"
      "状態というものはどこにも保存されておらず、毎回この線の上で作り直される。"),
     ("集約",
      "図では1つの箱だが、実体は集約のインスタンス1件ぶんである。"
      "イベントストアの中身は集約のインスタンスごとに分かれている。"),
    ])

FIG_STEPS = fig(
    "イベント履歴式の集約への操作が、4つの手順を踏むことを示す",
    "読み込む・作り直す・実行する・書き戻す。従来のドメインモデルと違うのは、"
    "2番目と4番目が加わっていることである。",
    ["業務イベントの履歴を読み込む", "ある時点の状態を作り直す",
     "コマンドを実行し、業務イベントを生む", "新しい業務イベントをイベントストアへ書き戻す"],
    [e("業務イベントの履歴を読み込む", "ある時点の状態を作り直す"),
     e("ある時点の状態を作り直す", "コマンドを実行し、業務イベントを生む"),
     e("コマンドを実行し、業務イベントを生む",
       "新しい業務イベントをイベントストアへ書き戻す")],
    notes=[
     ("ある時点の状態を作り直す",
      "この手順が従来のドメインモデルには無い。従来は保存された状態をそのまま読むだけだった。"),
     ("コマンドを実行し、業務イベントを生む",
      "状態を直接書き換えないのがこの方式の核心である。"
      "従来は状態を変えて終わりだったが、ここではイベントを生み、"
      "そのイベントを適用した結果として状態が変わる。"),
     ("新しい業務イベントをイベントストアへ書き戻す",
      "書き戻すのはイベントだけで、作り直した状態は保存しない。"
      "状態は毎回捨てられる。"),
    ])

FIG_SNAPSHOT = fig(
    "履歴が大きいときに、途中結果を控えておく形を示す",
    "投影済みの状態を控えておき、その後に足されたイベントだけを重ねる。控えは別のしくみが裏で作る。",
    ["アプリケーション", "控えの置き場", "イベントストア", "控えを作る別のしくみ"],
    [e("アプリケーション", "控えの置き場", "1. 投影済みの状態を取る"),
     e("アプリケーション", "イベントストア", "2. 控えより後のイベントだけ取る"),
     e("控えを作る別のしくみ", "イベントストア", "履歴を読む"),
     e("控えを作る別のしくみ", "控えの置き場", "控えを作り直す")],
    notes=[
     ("控えの置き場",
      "真実を語る拠り所ではない。捨てても履歴から作り直せるので、"
      "失われても業務上の損失は無い。"),
     ("控えを作る別のしくみ",
      "アプリケーションと別に描いてあるのは、操作の裏で動くためである。"
      "利用者の操作を待たせない。"),
     ("この図全体",
      "使ってよい場面は限られる。1つの集約のイベントが1万を超えると性能に響くが、"
      "百を超えるシステムはほとんど無い。控えを入れたくなったら、"
      "先に集約の境界の設計を見直すほうがよい。"),
    ])

FIG_SHARD = fig(
    "イベントストアを、集約の識別子で分割できることを示す",
    "1つの集約に属するイベントは必ず同じ区画へ入る。区画をまたいだ操作が起きないので、そのまま増やせる。",
    ["アプリケーション", "区画A", "区画B", "区画C", "区画D"],
    [e("アプリケーション", "区画A"), e("アプリケーション", "区画B"),
     e("アプリケーション", "区画C"), e("アプリケーション", "区画D")],
    direction="TD",
    notes=[
     ("区画A／区画B／区画C／区画D",
      "分ける基準は集約の識別子である。"
      "1つの集約のイベントが複数の区画に散らないことが、この形が成り立つ条件になる。"),
     ("4本の矢印",
      "どれか1つを選ぶのではなく、扱う集約に応じて行き先が決まる。"
      "集約への操作はインスタンスごとに閉じているので、区画をまたぐ操作は起きない。"),
    ])

FIG_CHOICE = fig(
    "イベント履歴式ドメインモデルを使うかどうかを、順に問うて決める",
    "中核であることが前提で、そのうえで時間軸の必要があるかを問う。",
    ["業務ロジックは複雑か（中核か）", "時間軸での分析・監査記録・過去の再現が要るか",
     "チームに経験があるか",
     "ドメインモデル以外を使う", "ドメインモデルを使う",
     "イベント履歴式ドメインモデルを検討する", "学習にかかる時間を見込んで判断する"],
    [e("業務ロジックは複雑か（中核か）", "ドメインモデル以外を使う", "いいえ"),
     e("業務ロジックは複雑か（中核か）", "時間軸での分析・監査記録・過去の再現が要るか", "はい"),
     e("時間軸での分析・監査記録・過去の再現が要るか", "ドメインモデルを使う", "いいえ"),
     e("時間軸での分析・監査記録・過去の再現が要るか",
       "イベント履歴式ドメインモデルを検討する", "はい"),
     e("イベント履歴式ドメインモデルを検討する", "チームに経験があるか"),
     e("チームに経験があるか", "学習にかかる時間を見込んで判断する", "いいえ")],
    direction="TD",
    notes=[
     ("チームに経験があるか",
      "他の分岐と性質が違う。技術的な適合ではなく、導入の是非を左右する条件を問う。"
      "「いいえ」でも採用してよいが、そのぶんの時間を見込む必要がある。"),
     ("業務ロジックは複雑か（中核か）",
      "この問いに「はい」であることが前提で、"
      "補完や一般の業務領域では以降の問いに進まない。"),
     ("時間軸での分析・監査記録・過去の再現が要るか",
      "3つのうち1つでも当てはまれば「はい」になる。3つとも必要という意味ではない。"),
    ])

# ── 原文（コード・表） ────────────────────────────────────────────────

HISTORY = code(
    "1件の集約について、イベントの履歴がどう並ぶかを示す",
    "1行が1つの出来事にあたる。並びを追うと、受け付けてから支払いが済むまでの経緯が読める。"
    "状態はどこにも書かれていない。",
    "json",
    '{ "request-id": 12, "event-id": 0, "event-type": "受付", '
    '"shipper": "北山物流", "phone": "000-0000", "at": "2026-05-20T09:52:55Z" }\n'
    '{ "request-id": 12, "event-id": 1, "event-type": "連絡", "at": "2026-05-20T12:32:08Z" }\n'
    '{ "request-id": 12, "event-id": 2, "event-type": "再連絡の予定を置く", '
    '"followup-on": "2026-05-27T12:00:00Z", "at": "2026-05-20T12:32:08Z" }\n'
    '{ "request-id": 12, "event-id": 3, "event-type": "連絡先の変更", '
    '"shipper": "北山物流", "phone": "000-1111", "at": "2026-05-20T12:40:11Z" }\n'
    '{ "request-id": 12, "event-id": 4, "event-type": "連絡", "at": "2026-05-27T12:02:12Z" }\n'
    '{ "request-id": 12, "event-id": 5, "event-type": "引受", '
    '"payment-deadline": "2026-05-30T12:02:12Z", "at": "2026-05-27T12:02:12Z" }\n'
    '{ "request-id": 12, "event-id": 6, "event-type": "支払完了", '
    '"status": "成立", "at": "2026-05-27T12:38:44Z" }')

PROJ_STATE = code(
    "履歴から最新の状態を作る投影を示す",
    "イベントの種類ごとに1つの適用手続きがある。版番号を毎回増やしているのが、"
    "過去の時点を再現できる根拠になる。",
    "csharp",
    "public class RequestStateProjection\n"
    "{\n"
    "    public long RequestId { get; private set; }\n"
    "    public string Shipper { get; private set; }\n"
    "    public RequestStatus Status { get; private set; }\n"
    "    public int Version { get; private set; }\n\n"
    "    public void Apply(RequestInitialized @event)      // 受付\n"
    "    {\n"
    "        RequestId = @event.RequestId;\n"
    "        Status = RequestStatus.NEW;\n"
    "        Shipper = @event.Shipper;\n"
    "        Version = 0;\n"
    "    }\n"
    "    public void Apply(ContactDetailsChanged @event)   // 連絡先の変更\n"
    "    {\n"
    "        Shipper = @event.Shipper;\n"
    "        PhoneNumber = @event.PhoneNumber;\n"
    "        Version += 1;\n"
    "    }\n"
    "    public void Apply(PaymentConfirmed @event)        // 支払完了\n"
    "    {\n"
    "        Status = RequestStatus.SETTLED;\n"
    "        Version += 1;\n"
    "    }\n"
    "}")

PROJ_SEARCH = code(
    "同じ履歴から、変更前の値も残す投影を作れることを示す",
    "上書きせず足していく。最新状態の投影と違うのは、この一点だけである。",
    "csharp",
    "public class RequestSearchProjection\n"
    "{\n"
    "    public HashSet<string> Shippers { get; private set; }\n"
    "    public HashSet<PhoneNumber> PhoneNumbers { get; private set; }\n\n"
    "    public void Apply(RequestInitialized @event)\n"
    "    {\n"
    "        Shippers = new HashSet<string>();\n"
    "        PhoneNumbers = new HashSet<PhoneNumber>();\n"
    "        Shippers.Add(@event.Shipper);\n"
    "        PhoneNumbers.Add(@event.PhoneNumber);\n"
    "    }\n"
    "    public void Apply(ContactDetailsChanged @event)\n"
    "    {\n"
    "        Shippers.Add(@event.Shipper);          // 上書きではなく追加\n"
    "        PhoneNumbers.Add(@event.PhoneNumber);\n"
    "    }\n"
    "}\n"
    "// 結果: PhoneNumbers: ['000-0000', '000-1111']")

PROJ_ANALYSIS = code(
    "同じ履歴から、数を数える投影も作れることを示す",
    "業務の分析に必要な値を、履歴を数え直すだけで得られる。あらかじめ数えておく必要は無い。",
    "csharp",
    "public class RequestAnalysisProjection\n"
    "{\n"
    "    public int Followups { get; private set; }   // 再連絡の予定を置いた回数\n"
    "    public RequestStatus Status { get; private set; }\n\n"
    "    public void Apply(FollowupSet @event)\n"
    "    {\n"
    "        Status = RequestStatus.FOLLOWUP_SET;\n"
    "        Followups += 1;\n"
    "    }\n"
    "}\n"
    "// 結果: Followups: 1, Status: 成立")

STORE_IF = code(
    "イベントストアに最低限必要な操作を示す",
    "取り出すことと、追記すること。この2つだけで足りる。",
    "csharp",
    "interface IEventStore\n"
    "{\n"
    "    IEnumerable<Event> Fetch(Guid instanceId);\n"
    "    void Append(Guid instanceId, Event[] newEvents, int expectedVersion);\n"
    "}")

APP_LAYER = code(
    "アプリケーション層が4つの手順をどう呼ぶかを示す",
    "読み込む・作り直す・実行する・書き戻す、が1つのメソッドの中に順に並ぶ。",
    "csharp",
    "public class ShipmentAPI\n"
    "{\n"
    "    private IShipmentsRepository _repository;   // イベントストア\n\n"
    "    public void RequestPriority(ShipmentId id, PriorityReason reason)\n"
    "    {\n"
    "        var events = _repository.LoadEvents(id);            // 手順1\n"
    "        var shipment = new Shipment(events);                // 手順2（状態を作り直す）\n"
    "        var originalVersion = shipment.Version;\n"
    "        var cmd = new RequestPriority(reason);\n"
    "        shipment.Execute(cmd);                              // 手順3（コマンドを実行）\n"
    "        _repository.CommitChanges(shipment, originalVersion); // 手順4\n"
    "    }\n"
    "}")

AGG_CODE = code(
    "イベント履歴式の集約が、状態をどう変えるかを示す",
    "コマンドの中で状態を直接書き換えていない。イベントを作って渡し、"
    "その適用の結果として状態が変わる。",
    "csharp",
    "public class Shipment\n"
    "{\n"
    "    private List<DomainEvent> _domainEvents = new List<DomainEvent>();\n"
    "    private ShipmentState _state;\n\n"
    "    public Shipment(IEnumerable<IDomainEvent> events)\n"
    "    {\n"
    "        _state = new ShipmentState();\n"
    "        foreach (var e in events)\n"
    "        {\n"
    "            AppendEvent(e);        // 既存の全イベントを適用して状態を作り直す\n"
    "        }\n"
    "    }\n\n"
    "    private void AppendEvent(IDomainEvent @event)\n"
    "    {\n"
    "        _domainEvents.Append(@event);\n"
    "        ((dynamic)_state).Apply((dynamic)@event);\n"
    "    }\n\n"
    "    public void Execute(RequestPriority cmd)\n"
    "    {\n"
    "        if (!_state.IsPrioritized && _state.RemainingTimePercentage <= 0)\n"
    "        {\n"
    "            var prioritized = new ShipmentPrioritized(_id, cmd.Reason);\n"
    "            AppendEvent(prioritized);   // 状態を変えるのではなくイベントを生む\n"
    "        }\n"
    "    }\n"
    "}")

STATE_CODE = code(
    "状態を持つクラスが、イベントごとの適用手続きだけを持つことを示す",
    "業務ロジックはここには無い。イベントを受けて値を書き換えるだけの、単純な変換に徹している。",
    "csharp",
    "public class ShipmentState\n"
    "{\n"
    "    public ShipmentId Id { get; private set; }\n"
    "    public int Version { get; private set; }\n"
    "    public bool IsPrioritized { get; private set; }\n\n"
    "    public void Apply(ShipmentInitialized @event)   // 受付\n"
    "    {\n"
    "        Id = @event.Id;\n"
    "        Version = 0;\n"
    "        IsPrioritized = false;\n"
    "    }\n"
    "    public void Apply(ShipmentPrioritized @event)   // 優先扱いへ引き上げ\n"
    "    {\n"
    "        IsPrioritized = true;\n"
    "        Version += 1;\n"
    "    }\n"
    "}")

COMPARE = {
    "intent": "4つの実装方法を、何を保存するかと対象領域で対比する",
    "reading": "分かれ目は2つ。保存するのが最新状態か履歴か、そして業務ロジックが複雑かどうか。",
    "lang": "markdown",
    "source": "| 実装方法 | 保存するもの | 業務ロジックの複雑さ | 対象領域 |\n"
              "|---|---|---|---|\n"
              "| 手続きとして書く | 最新の状態 | 単純 | 補完・一般 |\n"
              "| 1行のオブジェクトを介する | 最新の状態 | 単純（データ構造が複雑） | 補完・一般 |\n"
              "| ドメインモデル | 最新の状態 | 複雑 | 中核 |\n"
              "| イベント履歴式ドメインモデル | イベントの履歴 | 複雑（時間軸の洞察が要る） | 中核 |",
}

# ── ノード ────────────────────────────────────────────────────────────

NODES = [
    n("イベント履歴式ドメインモデルとは何か", "定義",
      "集約の状態を保存するのではなく、集約の状態が変化したことを業務イベントで表し、"
      "その履歴を保存する実装方法。ドメインモデルの部品（値オブジェクト・集約・業務イベント）は"
      "そのまま同じで、対象も複雑な業務ロジックと中核の業務領域で変わらない。"
      "違うのは、何を保存するかの一点である。", children=[
        n("この呼び名を選ぶ理由", "補足",
          "イベントの履歴を真実の拠り所にする考え方そのものは、集約の状態管理に限らず"
          "さまざまな状態管理へ使える。"
          "ここでの話は集約の一生の状態管理に限った適用なので、"
          "その範囲を示すためにこの呼び名を使う。"),
    ]),
    n("イベントの履歴を保存する", "定義",
      "状態そのものを保存する代わりに、状態を変化させたイベントの履歴を保存する。"
      "履歴を順に適用すれば、任意の時点の状態を作り直せる。"
      "会計の記録に似ている——残高そのものを持たなくても、取引の記録があればいつでも算出できる。",
      src="7.1", children=[
        n("履歴の例", "実例",
          "1件の依頼について、受付から支払完了までのイベントが順に並ぶ。",
          verbatim=HISTORY),
        n("投影", "判断基準",
          "履歴の1つ1つに単純な変換を順に当てていくと、状態が組み上がる。"
          "版番号をイベントごとに増やしておくのがこの実装の要で、"
          "先頭からいくつぶんだけ適用するかを選べば、過去のどの時点の状態も取り出せる。",
          verbatim=PROJ_STATE),
        n("検索のための投影", "実例",
          "同じ履歴に別の変換を当てれば、変更前の値も残る投影が作れる。"
          "上書きせずに足していくだけで、古い連絡先も検索の対象にできる。",
          src="7.1.1", verbatim=PROJ_SEARCH),
        n("分析のための投影", "実例",
          "同じ履歴から、業務の分析に使う値も作れる。"
          "あらかじめ数えておかなくても、履歴を数え直せば得られる。",
          src="7.1.2", verbatim=PROJ_ANALYSIS),
        n("真実を語る唯一の拠り所", "定義",
          "この方式が成り立つ条件は1つ——状態の変化をすべてイベントとして表し、保存すること。"
          "保存されたイベントが真実を語る唯一の拠り所になる。"
          "イベントを保存するデータベースをイベントストアと呼ぶ。",
          src="7.1.3", figure=FIG_STORE),
        n("イベントストア", "定義",
          "追記だけを受け付ける。記録したイベントの書き換えも削除もできない"
          "（データの移行など特殊な場合を除く）。"
          "必要な機能は2つだけで、あるインスタンスのイベントをすべて取り出すことと、追記すること。"
          "追記のときに期待する版番号を渡すのは、競合を検出するためである——"
          "渡した版番号がイベントストア側の最新より古ければ、"
          "誰かが先に追記したということなので、書き込みを失敗させる。",
          src="7.1.4", verbatim=STORE_IF),
    ]),
    n("集約への操作の手順", "判断基準",
      "4つの手順を踏む。", src="7.2", figure=FIG_STEPS, children=[
        n("アプリケーション層", "実例",
          "4つの手順が、そのまま1つのメソッドの中に並ぶ。", verbatim=APP_LAYER),
        n("集約の実装", "実例",
          "従来のドメインモデルとの違いがここに出る。"
          "従来は状態を直接書き換えていたが、ここではイベントを作って渡し、"
          "その適用の結果として状態が変わる。",
          verbatim=AGG_CODE),
        n("状態を持つクラス", "実例",
          "イベントごとの適用手続きだけを持ち、業務ロジックは持たない。",
          verbatim=STATE_CODE),
    ]),
    n("利点", "分類", "この方式が持つ4つの利点。", src="7.2.1", children=[
        n("過去のどの時点でも再現できる", "補足",
          "最新の状態を組み立てるのと同じやり方で、過去のあらゆる時点の状態を再現できる。"
          "使い道は、システムの使われ方の分析、システムが下した判定の検査、"
          "業務ロジックの改善、そして障害や不具合の調査——"
          "障害が起きた時点の集約の状態を、そのまま作り直せる。"),
        n("後から新しい見方を足せる", "補足",
          "1つの履歴から、いくつでも別の状態を作れる。"
          "投影する変換を後からいつでも足せるので、"
          "すでに溜まっている履歴から、業務について新しい見方を得られる。"),
        n("監査の記録になる", "補足",
          "業務イベントの履歴は、厳密な一貫性を持つ監査の記録そのものである。"
          "集約の状態を変えたすべての業務活動の正確な記録になる。"
          "事業領域によっては、この種の記録の保存が法令で義務づけられている。"
          "金銭や金融の取引を扱うシステムでとくに効く。"),
        n("競合の判定を業務の視点で行える", "判断基準",
          "従来の競合検出では、読み込んでから書き込むまでのあいだに"
          "誰かが同じデータを書き換えていれば、それだけで失敗させる。"
          "イベントの履歴があると、そのあいだに何が起きたかを正確に把握できるので、"
          "追記しようとしている操作が本当に衝突しているのか、"
          "それとも無関係で続けても安全かを、業務の視点で判定する仕組みを組み込める。"),
    ]),
    n("欠点", "分類", "この方式が抱える3つの欠点。", src="7.2.2", children=[
        n("学ぶのに時間がかかる", "補足",
          "従来のデータの扱い方とまったく違うやり方なので、正しく実装するには訓練が要る。"
          "チームにこの方式の開発経験が無いなら、その時間を見込まなければならない。"),
        n("モデルを変えにくい", "補足",
          "厳密には、イベントは変わらないものとして扱う。"
          "一度決めたイベントのデータ構造を変える作業は、"
          "表の設計を変えるのに比べてはるかに難しい。"),
        n("仕組みが増える", "補足",
          "実装にはさまざまな仕組みが必要になり、システム全体の設計が複雑になる。"),
    ]),
    n("よくある質問", "補足", "性能・規模・削除・代替手段について。", src="7.3", children=[
        n("イベントが増えると遅くならないか", "判断基準",
          "履歴から状態を作るにはそれなりの処理が要るので、"
          "履歴が大きくなるほど性能は落ちる。"
          "そこで途中結果を控えておく手がある——投影済みの状態を控えから取り、"
          "それより後に追記されたイベントだけを取って、メモリ上で重ねる。"
          "ただし使ってよい場面は限られる。"
          "多くのシステムでは1つの集約のイベントが1万を超えると性能に響くが、"
          "実際には百を超えるシステムがほとんど無い。"
          "控えを入れたくなったら、まず集約の境界の設計を見直すほうがよい。",
          src="7.3.1", figure=FIG_SNAPSHOT),
        n("規模を大きくできるか", "判断基準",
          "できる。集約への操作はインスタンスごとに閉じているので、"
          "イベントストアを集約の識別子で分割できる。"
          "1つのインスタンスに属するイベントを必ず同じ区画へ書き込めばよい。",
          figure=FIG_SHARD),
        n("追記だけなのに、削除を求められたら", "判断基準",
          "忘れられる中身、という形で解く。"
          "イベントに含まれる慎重に扱うべき情報をすべて暗号化し、"
          "その鍵をイベントストアとは別の置き場に、集約の識別子と対にして保存する。"
          "削除を求められたら鍵のほうを消す——"
          "イベントは残るが、守るべき情報は二度と読めなくなる。",
          src="7.3.2"),
        n("他のやり方ではだめか", "判断基準",
          "近いことをする代替手段が3つあるが、どれも同じものにはならない。",
          src="7.3.3", children=[
            n("記録をファイルに書き出して監査の記録にする", "アンチパターン",
              "データベースへの書き込みとファイルへの書き込みは、"
              "全部成るか全部成らないかの扱いが別々になる。"
              "片方が失敗すると食い違ったまま残る。"),
            n("状態と履歴を、ひと塊の変更として同時に書き込む", "アンチパターン",
              "技術的には一貫性を保てる。しかしプログラムを変えるときに、"
              "保守する人が履歴側への反映を忘れる余地が残る。"
              "状態の側を真実の拠り所にすると、履歴側の扱いはどうしても雑になる。"),
            n("状態の表から履歴の表へ、自動で複製する", "アンチパターン",
              "書き忘れは起きない。しかしこれは値の変化を写しているだけで、"
              "業務の文脈——なぜその値が変わったのかという理由——が落ちる。"
              "理由が残っていないと、新しい投影を作れる見込みはほとんど無くなる。"),
        ]),
    ]),
    n("4つの実装方法の対比", "分類",
      "何を保存するかと、対象となる業務領域で並べる。", verbatim=COMPARE),
    n("イベント履歴式ドメインモデルを使うか", "判断基準",
      "中核であることを前提に、時間軸の必要とチームの経験で決める。", figure=FIG_CHOICE),
    n("アンチパターン", "アンチパターン",
      "イベント履歴式ドメインモデルでよく起きる誤り。", children=[
        n("補完・一般の業務領域に使う", "アンチパターン",
          "事業活動の視点で設計を判断する、という原則から外れる。"
          "使う正当な理由が無く、もっと単純なやり方で足りるなら、"
          "欠点（学ぶ時間・仕組みの複雑さ・モデルの変えにくさ）だけが重くのしかかる。"),
        n("記録のファイルを監査の記録として使う", "アンチパターン",
          "データベースとファイルでは、全部成るか全部成らないかの扱いが別々なので、"
          "一貫性が保証されない。"),
        n("状態が変わった理由を記録しない", "アンチパターン",
          "自動の複製による履歴は値の変化だけを写し、業務の文脈が落ちる。"
          "理由が残っていないと、新しい投影を足せない。"),
    ]),
]

vals = {
    "content.title.title": "イベント履歴式ドメインモデルを扱う概念：event-sourced-domain-model",
    "content.nodes.title": "イベント履歴式ドメインモデル",
    "content.nodes.items": NODES,
    "content.description.text":
        "集約の状態を保存する代わりに、状態が変化したことを業務イベントで表し、"
        "その履歴を保存する実装方法。履歴が真実を語る唯一の拠り所になり、"
        "状態はそこから毎回作り直される。"
        "過去のどの時点でも再現でき、後から新しい見方を足せる一方、"
        "学ぶ時間・仕組みの複雑さ・モデルの変えにくさという代償を伴う。",
    "content.description.questions": [
        "従来のドメインモデルと、何が違うのか",
        "状態を保存しないで、どうやって業務判断をするのか",
        "イベント履歴式ドメインモデルを使うべきか、通常のドメインモデルで足りるか",
        "履歴が増えたときの性能と、規模の拡大にどう対処するか",
        "追記しかできないのに、情報の削除を求められたらどうするか",
        "監査の記録なら、履歴の表や記録のファイルでは代われないのか",
    ],
    "content.provenance.source":
        "『ドメイン駆動設計をはじめよう』第7章の書き起こしを、粒度を保ったまま構造へ移したもの。"
        "見出しそれぞれにノードを1つ対応させ、"
        "書き起こし版で図として書かれていたものは、すべて図として持たせている。",
    "content.provenance.caveats":
        "実例は著作権への配慮から架空の業務（配送の依頼）へ置き換え、"
        "個人名を含む履歴の例は法人名と伏せた番号に差し替えた。"
        "特定の法令の名称は、その法令が求める内容の説明に置き換えている。"
        "コードが示す構造（イベントを生んでから適用する順序・投影の作り方）は保っている。",
    "content.relatedConcepts.items": [
        {"conceptId": "domain-model",
         "note": "この方式の基礎。値オブジェクト・集約・業務イベントは同じ部品を使う"},
        {"conceptId": "business-logic-simple",
         "note": "手続きとして書く・1行のオブジェクトを介する、との対比"},
        {"conceptId": "subdomain", "note": "この方式を使うのは中核の業務領域に限る"},
        {"conceptId": "architecture-patterns",
         "note": "投影した状態を保存するには CQRS が要る。この方式では必須になる"},
        {"conceptId": "design-heuristics", "note": "実装方法を選ぶ経験則の全体像"},
    ],
    "content.relatedConcepts.emptyReason": "",
}

print(run("scaffold", "--operation", "migrate_schema", "--path", P,
          "--schemaRef", "KnowledgeSchema/v6")[:110])
for old in ("principles", "classifications", "decisionCriteria", "examples", "antiPatterns"):
    run("scaffold", "--operation", "clear_field", "--path", P, "--fieldPath", f"content.{old}")
print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps(vals, ensure_ascii=False))[:130])
print(run("validate", "--path", P)[:220])
print(run("render", "--path", P)[:100])
