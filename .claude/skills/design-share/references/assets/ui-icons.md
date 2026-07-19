# インラインSVGアイコン集（自己完結アセット層）

商用UIの「素通り感」を消すための、統一されたストロークアイコン。外部依存ゼロ（インラインSVG）。
方針: **24×24 viewBox / stroke ベース / `stroke-width` は共通 / `round` linecap・linejoin / fill は none / 色は `currentColor`**。
下の共通クラスを1つ置き、各アイコンは `<path>` 等の中身だけ差し替える。emoji・絵文字をアイコン代わりにしない。

```css
.ic{width:18px;height:18px;stroke:currentColor;stroke-width:1.8;fill:none;stroke-linecap:round;stroke-linejoin:round}
```

各アイコンは `<svg class="ic" viewBox="0 0 24 24">…</svg>` の中身:

| 用途 | 中身 |
|---|---|
| overview（グリッド） | `<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>` |
| box（荷物・在庫） | `<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>` |
| route（経路・レーン） | `<circle cx="5" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 6h7a4 4 0 0 1 0 8H10a4 4 0 0 0 0 8"/>` |
| truck（輸送・キャリア） | `<path d="M3 7h11v8H3z"/><path d="M14 10h4l3 3v2h-7z"/><circle cx="7" cy="17" r="1.6"/><circle cx="17.5" cy="17" r="1.6"/>` |
| alert（例外・警告） | `<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h0"/>` |
| bars（レポート・分析） | `<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>` |
| gear（設定） | `<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>` |
| search（検索） | `<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>` |
| calendar（期間） | `<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/>` |
| filter（絞り込み） | `<path d="M3 5h18M6 12h12M10 19h4"/>` |
| plus（新規追加） | `<path d="M12 5v14M5 12h14"/>` |
| chevron-right（前進・詳細） | `<path d="M9 6l6 6-6 6"/>` |
| chevron-up（増加） | `<path d="M7 14l5-5 5 5"/>` |
| chevron-down（減少・展開） | `<path d="M7 10l5 5 5-5"/>` |
| clock（時刻・ETA） | `<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>` |
| check-circle（完了・OK） | `<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>` |
| x（閉じる） | `<path d="M6 6l12 12M18 6L6 18"/>` |
| user（アカウント） | `<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>` |
| download（書き出し・export） | `<path d="M12 4v10M8 11l4 4 4-4M5 20h14"/>` |
| external（外部リンク） | `<path d="M14 5h5v5M19 5l-8 8M11 5H6a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5"/>` |

注意:
- **矢印の向きは意味に一致させる**（増加=up、減少=down）。悪化を赤で示す場合も、増えたなら up を使う（色で良し悪し、向きで増減）。
- ブランドのロゴマークは nav アイコンと**別の形**にする（署名と機能アイコンを見分けられるように）。
- サイズは `.ic` の width/height で調整（16〜20px を基本、装飾的に大きくしない）。
