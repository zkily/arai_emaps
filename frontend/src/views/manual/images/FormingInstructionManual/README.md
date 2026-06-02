# 成型工程生産指示及び実績収集マニュアル — スクリーンショット

操作説明 Markdown：`frontend/src/views/manual/docs/forming-instruction_ja.md`

本フォルダ（`frontend/src/views/manual/images/FormingInstructionManual/`）にスクリーンショットを配置してください。Markdown 内では **`./images/FormingInstructionManual/`** を参照しています。

## 推奨ファイル一覧

| ファイル名 | 内容 |
|------------|------|
| `01_workflow_overview.png` | 全体フロー（任意・参考用。本文は A〜K の HTML 図式を使用） |
| `02_menu_forming_instruction.png` | メニュー：MES管理メニュー → 生産指示 → 成型指示（3 段シェブロン） |
| `03_forming_instruction_overview.png` | 成型指示書発行管理 画面全体 |
| `04_forming_date_nextday.png` | 生産日を「翌日」に設定した検索バー |
| `05_instruction_issue_button.png` | 「指示書発行」ボタン（緑色）を強調 |
| `06_instruction_print_preview.png` | 指示書印刷プレビュー／QRコード読込中 |
| `07_instruction_printed_sample.png` | 印刷された成型生産指示書（現物または PDF） |
| `08_site_exchange.png` | 現場での指示書交換（新規発行分と記入済み分） |
| `09_plc_print.png` | PLC 収集データ印刷画面（参考 PDF 相当） |
| `10_handy_terminal.png` | HT：起動・ログイン・実績入力・送信（操作手順画像） |
| `11_menu_actual_management.png` | メニュー：生産実績管理 |
| `12_actual_management_filter.png` | 生産実績管理：成型タブ・フィルタ |
| `13_actual_reconcile.png` | PLC／HT と ERP 実績の照合例 |
| `14_menu_data_management.png` | メニュー：生産データ管理 |
| `15_all_batch_update.png` | 「各種更新機能」→「全部一括更新」 |
| `16_inventory_tab.png` | 生産データ管理：下部タブ列の「在庫」位置 |
| `16_inventory_tab_dblclick.png` | 在庫 TAB・セルダブルクリック |
| `17_menu_forming_plan_list.png` | メニュー：成型計画一覧 |
| `18_replan_button.png` | 「成型ライン順で再計算」ボタン |
| `19_remain_check_gantt.png` | ガント／一覧で「残」が 50 未満または次品種着手の例 |
| `20_forming_planning_total_qty.png` | 成型計画作成：合計(本) ダブルクリック編集 |
| `21_setup_schedule_print.png` | 段取表印刷ボタン |
| `22_setup_schedule_sample.png` | 成型生産計画段替予定表（印刷物） |
| `23_site_posting.png` | 現場掲示（翌日・翌々稼働日分） |

## 撮影のポイント

- 個人情報・機密情報（製品名の一部など）が写る場合はぼかし処理を行う。
- ボタン説明用は対象 UI を赤枠などで強調した画像を別途用意すると読みやすい。
- 印刷物は A4 横向（段替予定表）・A5 横向（指示書）の向きが分かるように撮影する。
