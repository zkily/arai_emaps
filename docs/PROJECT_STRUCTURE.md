# プロジェクト構造

## プロジェクト規約（日本時区・日本語）

- **タイムゾーン**: すべて **日本標準時（JST, Asia/Tokyo）** で統一する。
- **言語**: ユーザー向けの表示・メッセージ・API の説明は **日本語** で記述する。

### バックエンド
- 現在時刻の取得: `app.core.datetime_utils` の `now_jst()` または `JST` を使用する（`datetime.now()` は使わない）。
- 設定: `app.core.config` の `TIMEZONE = "Asia/Tokyo"` を変更しない。

### フロントエンド
- dayjs: `dayjs.locale('ja')`、`dayjs.tz.setDefault('Asia/Tokyo')` で日本語・日本時区を既定とする。
- 日時の表示は `dayjs().tz('Asia/Tokyo')` でフォーマットする。
- Element Plus の locale は `ja`（日本語）を使用する。

---

## 概要

Smart-EMAP システムは、機能モジュールごとに整理された構造を持っています。各モジュールは、関連するファイル（API、モデル、ビュー、ストアなど）を同じディレクトリに配置することで、保守性と拡張性を向上させています。

## ディレクトリ構造

```
Smart-EMAPs/
├── backend/                    # バックエンド（FastAPI + Python）
│   ├── app/
│   │   ├── core/               # コア機能（設定、データベース、セキュリティ）
│   │   │   ├── config.py       # アプリケーション設定
│   │   │   ├── database.py    # データベース接続
│   │   │   └── security.py     # セキュリティ（JWT、パスワードハッシュ）
│   │   ├── modules/            # 機能モジュール
│   │   │   ├── auth/           # 認証モジュール
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py      # 認証API（ログイン、ログアウト、ユーザー情報）
│   │   │   │   └── models.py   # ユーザーモデル
│   │   │   ├── erp/            # ERPモジュール
│   │   │   │   ├── __init__.py
│   │   │   │   └── api.py      # ERP API（販売、購買、在庫管理）
│   │   │   ├── aps/            # APSモジュール
│   │   │   │   ├── __init__.py
│   │   │   │   └── api.py      # APS API（生産計画、スケジューリング）
│   │   │   ├── mes/            # MESモジュール
│   │   │   │   ├── __init__.py
│   │   │   │   └── api.py      # MES API（製造実行、品質管理）
│   │   │   └── websocket/      # WebSocketモジュール
│   │   │       ├── __init__.py
│   │   │       └── api.py       # WebSocket API（リアルタイム通信）
│   │   └── main.py             # アプリケーションエントリーポイント
│   ├── database/
│   │   └── init/
│   │       └── 01_init.sql     # データベース初期化スクリプト
│   ├── requirements.txt        # Python依存関係
│   └── env.example             # 環境変数サンプル
│
├── frontend/                   # フロントエンド（Vue.js 3 + TypeScript）
│   └── src/
│       ├── modules/            # 機能モジュール
│       │   ├── auth/           # 認証モジュール
│       │   │   ├── api.ts       # 認証APIクライアント
│       │   │   ├── stores/      # Piniaストア
│       │   │   │   └── user.ts  # ユーザーストア
│       │   │   └── views/       # ビューコンポーネント
│       │   │       └── Login.vue
│       │   ├── erp/            # ERPモジュール
│       │   │   └── views/      # ERPビュー
│       │   │       ├── Sales.vue
│       │   │       ├── Purchase.vue
│       │   │       └── Inventory.vue
│       │   ├── aps/            # APSモジュール
│       │   │   └── views/      # APSビュー
│       │   │       ├── Planning.vue
│       │   │       └── Scheduling.vue
│       │   ├── mes/            # MESモジュール
│       │   │   └── views/      # MESビュー
│       │   │       ├── Execution.vue
│       │   │       └── Quality.vue
│       │   └── websocket/      # WebSocketモジュール
│       │       └── utils.ts    # WebSocketユーティリティ
│       ├── shared/             # 共有機能（唯一のルーター・リクエスト入口）
│       │   ├── api/
│       │   │   └── request.ts  # Axiosインスタンス（APIリクエスト）
│       │   └── router/
│       │       └── index.ts    # Vue Router 定義（main.ts で使用）
│       ├── views/              # ページビュー（Dashboard、Home、erp/order など）
│       │   └── erp/order/      # 受注管理サブモジュール（OrderHome、月別/日別一覧等）
│       ├── App.vue             # ルートコンポーネント
│       └── main.ts             # アプリケーションエントリーポイント
│
├── docs/                       # ドキュメント
│   ├── PROJECT_STRUCTURE.md   # このファイル
│   └── WEBSOCKET_IMPLEMENTATION.md
│
├── logs/                       # ログファイル
├── start.py                    # 起動スクリプト
├── start.bat                   # Windows起動スクリプト
├── start.sh                    # Linux/Mac起動スクリプト
└── README.md                   # プロジェクト説明

```

## モジュール構造の利点

### 1. **機能の集約**
- 関連するファイルが同じディレクトリに配置される
- モジュールの責任が明確になる
- コードの可読性が向上する

### 2. **保守性の向上**
- 機能追加・修正時に影響範囲が明確
- モジュール単位でのテストが容易
- コードレビューが効率的

### 3. **拡張性**
- 新しい機能モジュールを追加しやすい
- モジュール間の依存関係が明確
- マイクロサービス化への移行が容易

## モジュール説明

### 認証モジュール (`auth`)
- **バックエンド**: `backend/app/modules/auth/`
  - `api.py`: ログイン、ログアウト、ユーザー情報取得API
  - `models.py`: ユーザーモデル（User）
- **フロントエンド**: `frontend/src/modules/auth/`
  - `api.ts`: 認証APIクライアント
  - `stores/user.ts`: ユーザー状態管理（Pinia）
  - `views/Login.vue`: ログインページ

### ERPモジュール (`erp`)
- **バックエンド**: `backend/app/modules/erp/`
  - `api.py`: 販売、購買、在庫管理API
- **フロントエンド**: `frontend/src/modules/erp/`
  - `views/`: ERP関連ビューコンポーネント

### APSモジュール (`aps`)
- **バックエンド**: `backend/app/modules/aps/`
  - `api.py`: 生産計画、スケジューリングAPI
- **フロントエンド**: `frontend/src/modules/aps/`
  - `views/`: APS関連ビューコンポーネント

### MESモジュール (`mes`)
- **バックエンド**: `backend/app/modules/mes/`
  - `api.py`: 製造実行、品質管理API
- **フロントエンド**: `frontend/src/modules/mes/`
  - `views/`: MES関連ビューコンポーネント

### WebSocketモジュール (`websocket`)
- **バックエンド**: `backend/app/modules/websocket/`
  - `api.py`: WebSocket接続管理、リアルタイム通知
- **フロントエンド**: `frontend/src/modules/websocket/`
  - `utils.ts`: WebSocket接続ユーティリティ

## インポートパス

### バックエンド
```python
# モジュール間のインポート
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.websocket.api import notify_user_logged_in_elsewhere

# コア機能のインポート
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
```

### フロントエンド
```typescript
// モジュール間のインポート
import { login, getUserInfo } from '@/modules/auth/api'
import { useUserStore } from '@/modules/auth/stores/user'
import { connectWebSocket } from '@/modules/websocket/utils'

// 共有機能のインポート
import request from '@/shared/api/request'
import router from '@/shared/router'
```

## 今後の拡張

新しい機能モジュールを追加する場合：

1. **バックエンド**: `backend/app/modules/新機能名/` ディレクトリを作成
2. **フロントエンド**: `frontend/src/modules/新機能名/` ディレクトリを作成
3. 各モジュールに必要なファイル（API、ビュー、ストアなど）を配置
4. バックエンド: `main.py` にルーターを登録。フロントエンド: `shared/router/index.ts` にルートを追加（main.ts は `shared/router` を参照）

この構造により、システムの成長に合わせて柔軟に拡張できます。

