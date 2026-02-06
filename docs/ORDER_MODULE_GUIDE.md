# 受注管理モジュール 導入ガイド
# Order Management Module Implementation Guide

## 📋 概要 (Overview)

受注管理モジュールがSmart-EMAPシステムに正常に統合されました。このガイドでは、モジュールのセットアップと使用方法について説明します。

## 🎯 実装された機能

### 1. フロントエンド (Frontend)

#### ページ一覧
- **OrderHome** - 受注管理ホーム画面
- **OrderMonthlyList** - 月別受注管理
- **OrderDailyList** - 日別受注管理
- **OrderDashboardPage** - 受注ダッシュボード
- **OrderKpiDashboard** - KPIダッシュボード
- **OrderDailyHistoryPage** - 日別受注履歴
- **OrderCustomerHistory** - 顧客別受注履歴
- **OrderDestinationHistory** - 納入先別受注履歴
- **OrderHistoryComparison** - 受注履歴比較
- **OrderDailyPrintPage** - 受注印刷ページ

#### コンポーネント
- `AverageUnitPriceChart.vue` - 平均単価チャート
- `BarChart.vue` - 棒グラフ
- `DestinationSelectDialog.vue` - 納入先選択ダイアログ
- `ForecastDiffRank.vue` - 内示差異ランキング
- `KpiFilters.vue` - KPIフィルター
- `KpiSummaryCards.vue` - KPIサマリーカード
- `LineChart.vue` - 折れ線グラフ
- `OrderDailyAddDialog.vue` - 日別受注追加ダイアログ
- `OrderDailyBatchEditDialog.vue` - 日別受注一括編集ダイアログ
- `OrderDailyBatchImportDialog.vue` - 日別受注一括インポートダイアログ
- `OrderDailyEditDialog.vue` - 日別受注編集ダイアログ
- `OrderLogList.vue` - 受注ログリスト

#### ファイル配置
```
frontend/src/views/erp/order/
├── components/           # 共通コンポーネント
├── OrderHome.vue        # ホーム画面
├── OrderMonthlyList.vue # 月別受注管理
├── OrderDailyList.vue   # 日別受注管理
└── ... その他のページ
```

#### API クライアント
- `frontend/src/api/order.ts` - 受注管理用APIクライアント

### 2. バックエンド (Backend)

#### データモデル
- **OrderMonthly** - 月別受注
- **OrderDaily** - 日別受注
- **Customer** - 顧客マスタ
- **Destination** - 納入先マスタ
- **Product** - 製品マスタ
- **OrderLog** - 受注ログ

#### API エンドポイント

##### 月別受注 API
```
GET    /api/erp/orders/monthly          - 月別受注一覧取得
GET    /api/erp/orders/monthly/summary  - 月別受注集計取得
GET    /api/erp/orders/monthly/{id}     - 月別受注詳細取得
POST   /api/erp/orders/monthly          - 月別受注作成
PUT    /api/erp/orders/monthly/{id}     - 月別受注更新
DELETE /api/erp/orders/monthly/{id}     - 月別受注削除
```

##### 日別受注 API
```
GET    /api/erp/orders/daily            - 日別受注一覧取得
GET    /api/erp/orders/daily/summary    - 日別受注集計取得
GET    /api/erp/orders/daily/{id}       - 日別受注詳細取得
POST   /api/erp/orders/daily            - 日別受注作成
POST   /api/erp/orders/daily/batch      - 日別受注一括作成
PUT    /api/erp/orders/daily/{id}       - 日別受注更新
DELETE /api/erp/orders/daily/{id}       - 日別受注削除
```

##### マスタ管理 API
```
GET    /api/erp/customers               - 顧客一覧取得
POST   /api/erp/customers               - 顧客作成
GET    /api/erp/destinations            - 納入先一覧取得
POST   /api/erp/destinations            - 納入先作成
GET    /api/erp/products                - 製品一覧取得
POST   /api/erp/products                - 製品作成
```

##### ログ API
```
GET    /api/erp/orders/logs             - 受注ログ取得
```

#### ファイル配置
```
backend/app/modules/erp/
├── __init__.py
├── api.py         # APIエンドポイント
├── models.py      # データモデル
└── schemas.py     # Pydantic スキーマ
```

### 3. データベース

#### テーブル一覧
- `customer` - 顧客マスタ
- `destination` - 納入先マスタ
- `product` - 製品マスタ
- `order_monthly` - 月別受注
- `order_daily` - 日別受注
- `order_log` - 受注ログ

#### ビュー
- `v_order_monthly_summary` - 月別受注サマリー
- `v_order_daily_summary` - 日別受注サマリー
- `v_customer_order_stats` - 顧客別受注統計

## 🚀 セットアップ手順

### 1. データベースマイグレーション実行

```bash
# MySQLにログイン
mysql -u root -p

# データベース選択
USE smart_emap;

# マイグレーション実行
source backend/database/migrations/002_create_order_tables.sql;
```

または、Pythonスクリプトから実行：

```bash
cd backend
python -c "
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def run_migration():
    async with engine.begin() as conn:
        with open('database/migrations/002_create_order_tables.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
            # SQLステートメントを分割して実行
            for statement in sql.split(';'):
                if statement.strip():
                    await conn.execute(text(statement))
    print('Migration completed successfully!')

asyncio.run(run_migration())
"
```

### 2. バックエンド起動

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. フロントエンド起動

```bash
cd frontend
npm install  # 初回のみ
npm run dev
```

### 4. アクセス

ブラウザで以下のURLにアクセス：
- フロントエンド: http://localhost:5173
- バックエンドAPI: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

## 📍 ルーティング

### フロントエンドルート

| パス | コンポーネント | 説明 |
|------|---------------|------|
| `/erp/order` | OrderHome | 受注管理ホーム |
| `/erp/order/monthly` | OrderMonthlyList | 月別受注管理 |
| `/erp/order/daily` | OrderDailyList | 日別受注管理 |
| `/erp/order/dashboard` | OrderDashboardPage | 受注ダッシュボード |
| `/erp/order/kpi` | OrderKpiDashboard | KPIダッシュボード |
| `/erp/order/daily-history` | OrderDailyHistoryPage | 日別受注履歴 |
| `/erp/order/customer-history` | OrderCustomerHistory | 顧客別受注履歴 |
| `/erp/order/destination-history` | OrderDestinationHistory | 納入先別受注履歴 |
| `/erp/order/comparison` | OrderHistoryComparison | 受注履歴比較 |
| `/erp/order/print` | OrderDailyPrintPage | 受注印刷 |

## 💻 使用例

### フロントエンドでの使用例

```typescript
import { 
  getMonthlyOrders, 
  getDailyOrders,
  createMonthlyOrder,
  updateDailyOrder 
} from '@/api/order'

// 月別受注一覧取得
const fetchMonthlyOrders = async () => {
  try {
    const response = await getMonthlyOrders({
      year: 2026,
      month: 1,
      page: 1,
      page_size: 50
    })
    console.log('Total:', response.data.total)
    console.log('Orders:', response.data.items)
  } catch (error) {
    console.error('Error:', error)
  }
}

// 日別受注作成
const createOrder = async () => {
  try {
    const newOrder = {
      year: 2026,
      month: 1,
      day: 7,
      order_date: '2026-01-07',
      customer_code: 'C001',
      product_code: 'P001',
      confirmed_units: 100
    }
    const response = await createDailyOrder(newOrder)
    console.log('Created:', response.data)
  } catch (error) {
    console.error('Error:', error)
  }
}
```

### バックエンドでの使用例

```python
from app.modules.erp import models, schemas
from sqlalchemy import select

# 月別受注取得
async def get_orders(db: AsyncSession):
    query = select(models.OrderMonthly).where(
        models.OrderMonthly.year == 2026,
        models.OrderMonthly.month == 1
    )
    result = await db.execute(query)
    orders = result.scalars().all()
    return orders

# 日別受注作成
async def create_order(db: AsyncSession):
    order = models.OrderDaily(
        year=2026,
        month=1,
        day=7,
        order_date=date(2026, 1, 7),
        customer_code='C001',
        product_code='P001',
        confirmed_units=100
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order
```

## 🔧 カスタマイズ

### 新しいフィールドの追加

1. **モデル更新** (`backend/app/modules/erp/models.py`)
```python
class OrderMonthly(Base):
    # ... 既存のフィールド
    new_field = Column(String(100), comment="新しいフィールド")
```

2. **スキーマ更新** (`backend/app/modules/erp/schemas.py`)
```python
class OrderMonthlyBase(BaseModel):
    # ... 既存のフィールド
    new_field: Optional[str] = None
```

3. **マイグレーション作成**
```sql
ALTER TABLE order_monthly 
ADD COLUMN new_field VARCHAR(100) DEFAULT NULL COMMENT '新しいフィールド';
```

### 新しいAPIエンドポイントの追加

`backend/app/modules/erp/api.py` に追加：

```python
@router.get("/orders/custom")
async def custom_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """カスタムエンドポイント"""
    # カスタムロジック
    return {"message": "Custom endpoint"}
```

## 📊 データフロー

```
┌─────────────┐     HTTP/REST     ┌─────────────┐     SQL      ┌──────────┐
│  Frontend   │ ←───────────────→ │   Backend   │ ←──────────→ │ Database │
│   (Vue.js)  │    JSON Data      │  (FastAPI)  │   Async      │  (MySQL) │
└─────────────┘                   └─────────────┘              └──────────┘
      │                                   │
      │                                   │
      ├─ order.ts (API Client)           ├─ api.py (Endpoints)
      ├─ OrderHome.vue                   ├─ models.py (ORM)
      ├─ OrderMonthlyList.vue            ├─ schemas.py (Validation)
      └─ OrderDailyList.vue              └─ database.py (Connection)
```

## 🐛 トラブルシューティング

### 問題: データベース接続エラー

**解決策:**
1. MySQL サーバーが起動していることを確認
2. データベース接続設定を確認 (`backend/app/core/config.py`)
3. データベースが作成されていることを確認

### 問題: APIが404エラーを返す

**解決策:**
1. バックエンドサーバーが起動していることを確認
2. APIエンドポイントのパスを確認
3. ルーターが正しく登録されていることを確認 (`backend/app/main.py`)

### 問題: フロントエンドでデータが表示されない

**解決策:**
1. ブラウザのコンソールでエラーを確認
2. ネットワークタブでAPIリクエストを確認
3. CORS設定を確認 (`backend/app/main.py`)

## 📝 今後の拡張案

- [ ] エクスポート機能（CSV, Excel）
- [ ] レポート生成機能
- [ ] メール通知機能
- [ ] 承認ワークフロー
- [ ] リアルタイム更新（WebSocket）
- [ ] モバイル対応
- [ ] 多言語対応

## 📚 参考資料

- FastAPI ドキュメント: https://fastapi.tiangolo.com/
- Vue.js ドキュメント: https://vuejs.org/
- SQLAlchemy ドキュメント: https://docs.sqlalchemy.org/
- Element Plus ドキュメント: https://element-plus.org/

## 👥 サポート

問題が発生した場合は、以下の方法でサポートを受けることができます：

1. プロジェクトのIssueを作成
2. 開発チームに連絡
3. ドキュメントを確認

---

## ✅ チェックリスト

セットアップが完了したら、以下を確認してください：

- [ ] データベースマイグレーションが正常に実行された
- [ ] バックエンドサーバーが起動している
- [ ] フロントエンドが起動している
- [ ] `/erp/order` にアクセスできる
- [ ] APIドキュメント (`/docs`) が表示される
- [ ] サンプルデータが表示される

すべてにチェックが入れば、受注管理モジュールは正常に動作しています！🎉

---

**バージョン:** 1.0.0  
**最終更新:** 2026年1月7日  
**作成者:** Smart-EMAP Development Team

