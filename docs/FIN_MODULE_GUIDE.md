# FIN（経理・人事）モジュールガイド

freee 風の経理・人事クラウドを Smart-EMAPs に統合するための **顶级 FIN ドメイン**。
ERP/APS/MES と並列に位置し、製造原価は ERP_COSTING に残しつつ、法人会計・債権債務・
経費・勤怠・給与・人事を FIN に集約する。

全アーティファクトは **領域清单 + コードジェネレータ** で一括生成する（[`scripts/fin/README.md`](../scripts/fin/README.md)）。

## 構成

```
docs/fin/fin-domain-manifest.yaml      単一ソース（実体・画面・メニュー・集成）
scripts/fin/fin_codegen.py             ジェネレータ（PyYAML のみ）
backend/database/migrations/36_fin_full_schema.sql   41 表 + 種子データ
backend/app/modules/fin/               ドメイン別 models/schemas/api + common/crud
  ├─ accounting/services/posting_service.py   仕訳転記・試算表（手書き）
  ├─ payroll/services/calc_engine.py          給与計算（手書きスケルトン）
  ├─ attendance/services/attendance_calc.py   勤怠集計（手書きスケルトン）
  ├─ integration/erp_events.py                ERP→仕訳ソース連携（手書き）
  └─ services_api.py                          中核エンドポイント（手書き）
frontend/src/views/fin/                 45 画面（6 種テンプレート）
  └─ components/                        汎用 Fin*Page.vue（手書き）
frontend/src/api/fin/index.ts           CRUD クライアントファクトリ
frontend/src/router/finMenuConfig.ts    メニュー定義（生成）
frontend/src/shared/router/finRoutes.ts ルート定義（生成・redirect 含む）
frontend/src/locales/fin/               多言語（生成）
frontend/src/composables/useMenuTree.ts menuConfig → ツリー（手書き）
frontend/src/components/layout/MenuTreeItem.vue 再帰メニュー描画（手書き）
```

## メニュー（顶级 FIN, sortOrder=3.5 — MES の下・マスタの上）

```
FIN 経理・人事
├─ 会計（仕訳帳 / 総勘定元帳 / 試算表 / BS・PL / 決算 / 取込）
├─ 売上・請求 AR（請求書 / 入金消込 / 売掛年齢）
├─ 仕入・支払 AP（仕入請求 / 支払 / 買掛年齢）
├─ 経費精算（申請 / 承認 / 規程）
├─ 勤怠（記録 / 休暇 / シフト / カレンダー）
├─ 給与（計算 / 明細 / 振込 / 項目）
├─ 人事（社員 / 契約 / 年末調整）
├─ 経理マスタ（勘定科目 / 税区分 / 取引先 / 銀行口座）
├─ 従業員ポータル
└─ 設定（会計設定 / 承認フロー）
```

サイドバーは `menuConfig` から `useMenuTree('FIN')` で再帰描画され、手書きの
`el-menu-item` 二重管理を解消している。

## API

汎用 CRUD（生成）: `/api/fin/<domain>/<resource>`（list/get/create/update/delete）。
中核処理（手書き `services_api.py`）:

| メソッド | パス | 用途 |
|---------|------|------|
| POST | `/api/fin/accounting/journals/{id}/post` | 仕訳転記（借貸バランス検証） |
| GET  | `/api/fin/accounting/trial-balance?period_ym=YYYY-MM` | 試算表 |
| POST | `/api/fin/integration/events` | ERP イベント記録（仕訳ソース化） |
| POST | `/api/fin/integration/generate-journals?period_ym=YYYY-MM` | 仕訳一括生成 |
| POST | `/api/fin/payroll/runs/{id}/calculate` | 給与計算 |
| POST | `/api/fin/attendance/records/{id}/recalc` | 勤怠再計算 |

## ERP → FIN 仕訳連携

業務イベントを `fin_journal_source`（status=pending）として記録し、月次で
`generate_journals` が仕訳（draft）へ一括変換する。テンプレートは
[`erp_events.py`](../backend/app/modules/fin/integration/erp_events.py) の `JOURNAL_TEMPLATES`。

| event_type | 借方 | 貸方 |
|------------|------|------|
| SALES_POSTED / INVOICE_ISSUED | 売掛金 | 売上高 |
| PURCHASE_RECEIVED | 仕入高 | 買掛金 |
| OUTSOURCING_RECEIVED | 外注加工費 | 買掛金 |
| INVENTORY_ADJUST | 棚卸資産 | 棚卸差額 |
| COSTING_CLOSE | 製品 | 仕掛品 |
| DEPRECIATION | 減価償却費 | 減価償却累計額 |
| PAYROLL_POSTED | 給与手当 | 未払費用 |
| EXPENSE_APPROVED | 旅費交通費 | 未払金 |

ERP 側の呼び出し例（売上計上時）:

```python
from app.modules.fin.integration import erp_events
await erp_events.record_event(
    db, source_type="SALES_POSTED", source_ref=order_no,
    amount=total, event_date=sales_date, created_by=user.username,
)
```

## ERP_COSTING との分担

| ERP に残す | FIN へ移管 |
|-----------|-----------|
| 標準/実際原価、差異、配賦、WIP、減価償却（製造側） | 仕訳帳・試算表・決算 |
| — | 法人 AR/AP・請求消込・会計ソフト出力 |

旧 ERP パス（`/erp/costing/journal|accounting-export|billing|payment`）は
`finRoutes.ts` の redirect で `/fin/*` へ転送（ブックマーク互換）。

## 権限

- `RolePermission.vue` の操作モジュールに **`経理・人事`** を追加済み。
- メニュー code（`FIN_*`）はシステム管理「ルート定義から取り込み」で `menus` テーブルへ同期。

## 生成 vs 手書きと残作業

| 能力 | 状態 |
|------|------|
| 表/Model/CRUD/一覧・フォーム UI/メニュー/ルート | 生成済み（動作） |
| 仕訳転記・試算表 | 実装済み（`posting_service`） |
| ERP 仕訳ソース連携・一括生成 | 実装済み（`erp_events`） |
| 給与計算・勤怠集計 | スケルトン実装（料率・残業規則は要拡張） |
| 経費承認 | ワークフロー UI で承認/却下可 |
| BS/PL・年末調整・freee/弥生 API 出力 | 画面骨架のみ（集計・連携は要実装） |

> 給与の社会保険料率・源泉徴収税額は法令改定が頻繁。`fin_withholding_tax_table` 等の
> バージョン付きデータから取得し、コードに直接ハードコードしないこと。
