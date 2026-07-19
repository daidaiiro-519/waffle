---
name: "skill-router"
description: "role skill（Investigation/Spec-authoring/Handoff-authoring/Implementation）が単独では目的を完結できない場面で、どのadvisor Skillと組み合わせる必要があるかをルーティング表に基づいて判断する際に使う。CLAUDE.md（Orchestrator）がrole skillのライフサイクルの中で必要な回数呼び、判断材料となるadvisorの結果をrole skillへの入力として渡す。ルーティング表は「誰と組み合わせるか（WHO）」のみを扱い、「いつ呼ぶか（WHEN：執筆前の判断材料収集か、執筆後の十分性ゲートチェックか、あるいはその両方か）」はOrchestrator側の責務とし、skill-router自身はタイミングを一切保持しない。"
---

# schemaごとに必要なadvisorの組み合わせを振り分けるrouter Skill：skill-router

## 目的

role skill（Investigation/Spec-authoring/Handoff-authoring/Implementation）が単独では目的を完結できない場面で、どのadvisor Skillと組み合わせる必要があるかをルーティング表に基づいて判断する際に使う。CLAUDE.md（Orchestrator）がrole skillのライフサイクルの中で必要な回数呼び、判断材料となるadvisorの結果をrole skillへの入力として渡す。ルーティング表は「誰と組み合わせるか（WHO）」のみを扱い、「いつ呼ぶか（WHEN：執筆前の判断材料収集か、執筆後の十分性ゲートチェックか、あるいはその両方か）」はOrchestrator側の責務とし、skill-router自身はタイミングを一切保持しない。

---

## 役割

- role skillが単独では完結できない場面を、ルーティング表に基づいて判定する
- 併用が必要なadvisor Skillの組み合わせと、その強制力（block/nudge）を示す
- 併用が必要なadvisor Skillをgoal-dispatch構造で並列にSubagent起動できるよう、対象advisor名の一覧を返す
- role skill・advisor Skill同士が互いを呼ぶ構造を避け、Orchestrator（CLAUDE.md）に代わって組み合わせ判断の一次窓口になる

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| 呼び出し元のrole skill名 | 明示されなければ、これから実行しようとしている作業内容（spec作成・handoff作成・実装等）から推測し、不明な場合は呼び出し元に確認する。 |
| 対象のschemaRefまたは作業目的 | role skillがSpec-authoringの場合は必須（schemaRef単位でルーティング表を引くため）。Handoff-authoring/Implementationの場合は「前段階で実際に参加したadvisor」を別途受け取る（動的引き継ぎ、固定リストではない）。 |

---

## ルーティング表

| Skill | 併用が必要な条件 | 併用するadvisor Skill | 強度 |
|---|---|---|---|
| Spec-authoring | DomainSpecSchemaのdocument作成 | `ddd-advisor / tech-lead-advisor` | block |
| Spec-authoring | CodingSchema（tech-stack/architecture/coding-standard）のdocument作成 | `tech-lead-advisor` | block |
| Spec-authoring | CodingSchema（test-standard）のdocument作成 | `tech-lead-advisor / qa-advisor` | block |
| Spec-authoring | PlatformSpecのdocument作成 | `platform-advisor` | block |
| Spec-authoring | PresentationSpecSchemaのdocument作成 | `ux-advisor` | nudge |
| Handoff-authoring | HandoffSchemaのdocument作成（前段階Spec-authoringで実際に参加したadvisorを動的に引き継ぐ。固定リストではない） | `ddd-advisor` | block |
| Implementation | 実装（Handoffのdesign/implementationViewpointsに記録されたadvisorを動的に引き継ぐ。固定リストではない） | `ddd-advisor` | block |

---

## ガードレール

- combinedSkillsに指定できるのは常にskillKind: advisorのSkillのみ。advisor以外のSkillを併用したくなった場合は、role skillの境界の切り方自体が細かすぎる設計ミスのサインであり、この表に逃がさない
- ルーティング表にエントリが無いSkill（例: Investigation）は単独で完結するとみなし、advisorのdispatchを行わない
- strengthがblockのエントリは、対象advisorの結果を得るまでrole skillの実行を進めない。nudgeのエントリは、対象advisorの結果を推奨情報としてrole skillに渡すが、role skillの実行をブロックしない
- Handoff-authoring/Implementationの行は固定のadvisor一覧ではなく「前段階で実際に参加したadvisor」を動的に引き継ぐ。この表のcombinedSkillsは引き継ぎ元が無い場合のデフォルトとして扱う
- skill-router自身はrole skillやadvisor Skillの内部手順を一切知らない。判断結果（併用すべきadvisor名の一覧）を返すだけで、実際のgoal-dispatch組み立てとSubagent起動はOrchestrator（CLAUDE.md）側が行う
- ルーティング表の各行は「いつ呼ぶか」を持たない。同じ行（同じskill/purpose/combinedSkills）を、role skillのライフサイクル内でOrchestratorが執筆前・執筆後の複数回にわたって呼び出してよい。この表に執筆前用・執筆後用の行を別々に作らない

---

## 参照

- `docs/brainstorm/brainstorm-advisor-di-and-subagent-roles.md`: skill-routerという概念に収束するまでの設計経緯（訂正の連鎖）とroutingTableの列構成・ガードレールの確定根拠
