---
name: project_svg_engine_visual_check_hook_pending
description: svg_engine(design-svg Skillの事業領域)の描画機械チェック(層2)は今は手動pytestコマンド、将来design-svg側で正式化する予定
metadata:
  node_type: memory
  type: project
---

`.claude/skills/design-svg/svg_engine/` に新規実装したSVGコンポーネントエンジン（16の主張の描画部品・Sugiyama法の自動配置・構造/スタイルを分離するトークン設計＋範囲検査・ブーリアン演算・グループの入れ子/クリップ/自由曲線）は、**Waffleの事業領域ではなく`design-svg` Skillの事業領域**として持つ（2026-08-22、ユーザーの明示的な指示）。16の主張という記法自体も含めてdesign-svgが所有し、汎用的に使えるSkillとして提供価値を持たせる。Waffleはそれを利用する側で、間に変換器（インターフェース）を挟む想定 ── 今回はWaffleの持ち物のつもりで作ったため変換器は無いが、今後は「独立したSkillで、インターフェースを合わせれば他所からも使える」という思想で扱う。バックボーンknowledge `asset-authoring-contract-for-component-svg-engines`（KnowledgeSchema/v6、ACTIVE）も`skillRefs: ["design-svg"]`とし、`.claude/skills/design-svg/references/knowledge/`へ配布済み。

design-svgの現行SKILL.mdには「決められた記法（例：waffle の16の主張）に従う仕様の中の図には使わない」という除外規定が残っており、**今回の位置づけと矛盾したまま**になっている。SKILL.md自体の書き換えはまだ行っていない。

テスト戦略は `docs/adr/adr-svg-engine-testing.html`（2026-08-22時点で未承認）で、値の単体テスト（層1）と描画したときの機械チェック（層2）の2層に分けると決めた。**2026-08-22にこの2層を実装済み（160件）**。検査ロジック自体は `examples/` から `svg_engine/verify.py` へ移し、エンジン本体の持ち物にした（アセット追加の契約が「この検査を通ること」を求めているため）。層2は組み立てたSVGの文字列を解析するので resvg/fonttools は不要になり、実行コマンドは：

```
uv run --no-project --with pytest python3 -m pytest .claude/skills/design-svg/svg_engine/tests/
```

テストが実際に赤くなることは、欠陥を注入して確認済み（障害物回避の無効化・ラベル重なり回避の無効化・囲み余白0・部品が例外を投げる、の4通り）。配置戦略は層状・環状に加え**放射木（tree.py）を追加**した ── 層状で枝10本の木を描くと6226×236の帯になり、環状では辺が箱を突っ切ることを実測して決めた（憶測ではない）。

**Why:** ユーザーから「これはいずれ正式なhooksとして作成しようと思っている。他のschema再定義（段1/段2のDomainSchema等）が終わったら、ちゃんとした実装として仕上げたい」という申し送りの後、「16の主張自体をdesign-svgに持たせ、Waffleは変換器越しに利用する側にする」という事業領域の訂正が入った。優先順位として、進行中のDomainSchema再定義（[[project_waffle_own_knowledge_stage]]系の一連の作業）を先に片づけてから着手する意図は変わらない。

**How to apply:** 他のschema再定義作業が一段落したタイミングで、次をまとめて片づける対象として扱う。(1) `.claude/skills/design-svg/svg_engine/`の実体をdesign-svg Skill配下（例: `.claude/skills/design-svg/`配下）へ移す判断、(2) design-svgのSKILL.mdの除外規定を、今回の位置づけと矛盾しない形に書き換える、(3) 上記pytestを毎回自動でかかるhookとして登録する（テスト自体は書けているので、残っているのは登録だけ）、(4) Waffle側に変換器（インターフェース）を作るかどうかの判断。まだ未移設・hook未登録のままだからといって「テスト整備・所有権整理が漏れている」と誤って報告しない — これは合意済みの先送りであり、抜けではない。
