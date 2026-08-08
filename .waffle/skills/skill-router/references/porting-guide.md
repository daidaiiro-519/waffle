# skill-routerを他プロジェクトへ移植する手順

## 前提: 既に「完璧な抽象化」の条件を満たしている

skill-routerが機能するために必要な情報は2箇所にしか無い。

1. **Orchestrator側の委譲パターン**（いつ呼ぶか＝WHEN）
2. **skill-router自身のルーティング表・境界マップ**（誰と組むか＝WHO）

このどちらも、自由記述のプローズではなく**schemaで構造化されたブロック**として
既に定義されている。

- Orchestrator側は`AgentSchema`の`delegationPatterns`ブロック
  （`target`/`timing`/`targetScope`/`action`/`why`の5フィールド）
- skill-router側は`SkillSchema/v2`の`RouterContent`（`routingTable`・
  `advisorBoundaries`ブロック）

つまり「オーケストレーターに決められたフォーマットで書く」「skill-router自体に
組み合わせ方を書く」の両方が、既にスキーマとして固定された形式を持っている。
移植作業は自由記述のドキュメントを一から書くことではなく、**この2つの
構造化データを対象プロジェクトの実物で埋めるだけ**で完結する。

## 手順

### 1. skill-routerのSKILL.mdをそのまま配置する

機構部分（役割・入力の想定・ガードレール）は書き換えずコピーする。

```
対象プロジェクト/.claude/skills/skill-router/SKILL.md
```

Waffleを対象プロジェクトにも導入する場合は、`waffle scaffold --operation create
--schemaRef SkillSchema/v2 --discriminator skillKind=router`で雛形を作り、
以下の表だけをfillする。Waffleを導入しない場合は、SKILL.mdを直接手編集する
（`routingTable`・`advisorBoundaries`はMarkdownの表として埋め込まれているだけ
なので、手編集でも機構としては同じように動く。ただしdrift検知・整合性チェック
等のWaffleの恩恵は受けられない）。

### 2. ルーティング表を対象プロジェクトの実在Skill名で書き直す

例（対象プロジェクトが`code-review`という役割Skillと、`security-advisor`・
`perf-advisor`という2つの助言Skillを持つ場合）:

```
| Skill | 併用が必要な条件 | 併用するadvisor | 強度 |
|---|---|---|---|
| code-review | 認証・権限まわりのコード変更を含む | security-advisor | 必須 |
| code-review | パフォーマンスに影響しうる変更を含む | perf-advisor | 推奨 |
```

`advisorBoundaries`（advisor間の境界・委譲マップ）も同様に、対象プロジェクトの
advisor同士に範囲外の関係があれば埋める。無ければ空のままでよい。

### 3. 対象プロジェクトのOrchestrator（AgentSchema/CLAUDE.md相当）に委譲パターンを追加する

`delegationPatterns`へ以下のようなエントリを追加する（`waffle scaffold fill`
経由、またはAgentSchemaを使わない場合は同等の構造化情報を手動で追記する）。

```json
{
  "target": "skill-router",
  "timing": "before",
  "targetScope": "category",
  "action": "code-reviewを使う前に、まずskill-routerへ問い合わせ、routingTableが示すadvisorとの組み合わせ（WHO）を確認する",
  "why": "role skillとadvisor Skillが互いを呼ぶ構造を避け、組み合わせ判断の一次窓口をOrchestrator側に置くため"
}
```

## 前提として必要なもの

skill-routerが価値を発揮するのは、対象プロジェクトのSkillが「実行するSkill
（役割Skill）」と「判断材料を提供するSkill（advisor Skill）」に分かれている
場合に限られる。この分類が無いプロジェクトでは、機構自体は動くが恩恵は薄い。

## 未検証の注記

この手順は2026-07-25時点で理論的に組み立てたものであり、実際に他プロジェクトへ
移植した実例はまだ無い。実際に移植を試みた際に、ここに書かれていない障害が
見つかる可能性がある（evidence-based-scope: 実例が出たらこの文書を更新する）。
