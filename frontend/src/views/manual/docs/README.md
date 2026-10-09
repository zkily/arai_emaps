# マニュアル Markdown（`docs/`）

操作説明の正本は **このフォルダ直下** に置きます。画像は `../images/` に配置してください。

## ファイル一覧

| ファイル | 内容 | 画像フォルダ |
|----------|------|----------------|
| `forming-instruction_ja.md` | 成型工程 生産指示・実績収集 | `../images/FormingInstructionManual/` |
| `forming-planning_ja.md` | 成型工程 計画作成（受注→在庫→計画→指示→実績→日次サイクル） | `../images/FormingPlanningManual/` |
| `welding-instruction_ja.md` | 溶接工程 生産指示・実績収集（PLC 手順なし） | `../images/WeldingInstructionManual/` |
| `welding-planning_ja.md` | 溶接工程 計画作成（受注→在庫→計画→指示→実績→日次サイクル） | `../images/WeldingPlanningManual/` |
| `cutting-instruction_ja.md` | 切断面取 生産指示・実績収集 | `../images/CuttingInstructionManual/` |
| `inspection-actual_ja.md` | 検査実績収集（Web） | `../images/InspectionActualDataCollection/` |
| `inspection-actual-android_ja.md` | 検査実績収集（Android アプリ） | `../images/InspectionActualAndroid/` |
| `inspection-actual-registration_ja.md` | 検査実績収集登録 | `../images/InspectionActualRegistration/` |
| `inspection-monitor_ja.md` | 検査モニタ | `../images/InspectionMonitor/` |
| `inspection-productivity_ja.md` | 検査工程 — 生産性分析 | `../images/InspectionProductivity/` |

生産計画ベースライン管理は PDF 正本です（`../pdfs/plan-baseline.pdf`、`/manuals/plan-baseline`）。`plan-baseline_ja.md` は旧稿です。

## 新規マニュアル追加（Markdown）

1. 本フォルダに `{slug}_ja.md` を追加。
2. 画像は `../images/YourFolder/` に配置し、MD 内は `./images/YourFolder/xxx.png` を使用。
3. `frontend/src/config/operationManuals.ts` の `OPERATION_MANUALS` にエントリを追加（`category`: `planning` / `instructionActual` / `mes` / `pageOperation`）。

## 画面操作説明 PDF（`pageOperation`）— 必須パターン

**ページ操作関連**の新規・更新は、補給品管理 / 生産計画ベースラインと同型の PDF とする（Markdown 正本にしない）。

| ステップ | 内容 |
|----------|------|
| 1. 原稿 | `docs/{slug}-manual_ja.html`（表紙・目次・章立て・赤青コールアウト・実画面スクショ） |
| 2. 画像 | `docs/images/{slug}/`（実 UI。模式図のみ禁止） |
| 3. PDF 化 | Chrome/Edge `--headless=new --print-to-pdf=... --no-pdf-header-footer`（`file://`） |
| 4. Outline | `docs/images/{slug}/_add_bookmarks.py` で PyMuPDF `set_toc`（目次ページ以降から見出し検索） |
| 5. 配置 | `frontend/src/views/manual/pdfs/{slug}.pdf` |
| 6. 登録 | `pdfFile` + `category: 'pageOperation'` + `pageMenuCode`。画面 help → `/manuals/{slug}` |

- 目次は **PDF 内** と **PDF ブックマーク（アウトライン）** のみ。ManualHome に PDF 用 TOC サイドバーを作らない。
- HTML を再印刷したら、必ずブックマークを再付与する。
- 詳細は `.cursor/rules/page-operation-pdf-manual.mdc`。

```ts
{
  slug: 'equipment-efficiency',
  menuCode: 'OP_MANUAL_EQUIPMENT_EFFICIENCY',
  pageTitle: '設備能率管理',
  pdfFile: 'equipment-efficiency.pdf',
  sortOrder: 12,
  category: 'pageOperation',
  pageMenuCode: 'MASTER_EQUIPMENT_EFFICIENCY', // menuConfig.ts の画面コード
},
```

`pageMenuCode` 未指定（または menuConfig に存在しないコード）の場合は「ページ操作関連」の直下に表示される。

## 表示

ヘッダーのマニュアルアイコン → `/manuals/{slug}`（例: `/manuals/forming-instruction`）

**ログイン不要**（新規タブでも閲覧可）。ログイン済みの場合も追加のトークン検証は行いません。
