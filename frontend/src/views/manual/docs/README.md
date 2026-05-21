# マニュアル Markdown（`docs/`）

操作説明の正本は **このフォルダ直下** に置きます。画像は `../images/` に配置してください。

## ファイル一覧

| ファイル | 内容 | 画像フォルダ |
|----------|------|----------------|
| `forming-instruction_ja.md` | 成型工程 生産指示・実績収集 | `../images/FormingInstructionManual/` |
| `cutting-instruction_ja.md` | 切断・面取指示管理 | `../images/CuttingInstruction/`（要追加） |
| `plan-baseline_ja.md` | 生産計画ベースライン管理 | `../images/ProductionPlanBaselineManagement/` |
| `inspection-actual_ja.md` | 検査実績収集 | `../images/InspectionActualDataCollection/` |

## 新規マニュアル追加

1. 本フォルダに `{slug}_ja.md` を追加。
2. 画像は `../images/YourFolder/` に配置し、MD 内は `./images/YourFolder/xxx.png` を使用。
3. `frontend/src/config/operationManuals.ts` の `OPERATION_MANUALS` にエントリを追加。

## 表示

ヘッダーのマニュアルアイコン → `/manuals/{slug}`（例: `/manuals/forming-instruction`）

**ログイン不要**（新規タブでも閲覧可）。ログイン済みの場合も追加のトークン検証は行いません。
