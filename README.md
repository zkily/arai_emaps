# Smart-EMAPs (ERP+APS+MES) 統合管理システム

製造業のデジタルトランスフォーメーションを実現する次世代統合管理システムです。ERP（企業資源計画）、APS（先進的計画・スケジューリング）、MES（製造実行システム）をシームレスに連携させ、設計から製造、出荷まで一気通貫のデータフローを構築します。

## 🎯 システム概要

Smart-EMAPsは、製造業における経営資源の最適化、高精度な生産計画、現場の実行と可視化を統合的に実現します。各モジュールが緊密に連携し、リアルタイムなデータ共有により、迅速な意思決定と業務効率の最大化を支援します。

## 🚀 技術スタック

### フロントエンド

| カテゴリ           | 技術                                    |
| ------------------ | --------------------------------------- |
| **フレームワーク** | Vue.js 3.4+ (Composition API)           |
| **言語**           | TypeScript 5.3+                         |
| **ビルドツール**   | Vite 6.4+                               |
| **状態管理**       | Pinia (永続化対応)                      |
| **ルーティング**   | Vue Router 4                            |
| **UIライブラリ**   | Element Plus 2.5+                       |
| **チャート**       | ECharts 5.4+, Chart.js 4.5+             |
| **国際化**         | Vue I18n 11.2+                          |
| **日時処理**       | Day.js 1.11+                            |
| **テーブル・DnD**  | vxe-table, xe-utils, vuedraggable, SortableJS |
| **スタイル**       | Sass（`scss`） |
| **その他**         | Axios, XLSX, file-saver, QRCode, html2canvas, jsPDF, markdown-it；Vite 用 unplugin-auto-import / unplugin-vue-components |

### バックエンド

| カテゴリ              | 技術                               |
| --------------------- | ---------------------------------- |
| **言語**              | Python 3.10+                       |
| **Webフレームワーク** | FastAPI 0.109+                     |
| **ASGIサーバー**      | Uvicorn 0.27+                      |
| **ORM**               | SQLAlchemy 2.0+                    |
| **マイグレーション**  | Alembic 1.13+                      |
| **データベース**      | MySQL 8.0+ (aiomysql, PyMySQL)     |
| **認証**              | JWT (python-jose), Passlib, Bcrypt |
| **バリデーション**    | Pydantic 2.5+, Pydantic Settings   |
| **ロギング**          | Loguru 0.7+                        |
| **テスト・品質**      | Pytest 7.4+, pytest-asyncio, httpx；Black / Flake8 / Mypy（開発用） |

### データベース

- **RDBMS**: MySQL 8.0+
- **文字セット**: utf8mb4 (Unicode完全対応)
- **接続**: 非同期接続プール (aiomysql)

### 開発言語・主要ライブラリ

| レイヤー       | 主な言語・ライブラリ                                                                 |
| -------------- | ------------------------------------------------------------------------------------ |
| フロントエンド | TypeScript, Vue 3, Element Plus, Pinia, Vue Router, ECharts, Axios, Vite            |
| バックエンド   | Python, FastAPI, SQLAlchemy, Pydantic, Uvicorn, Alembic, python-jose, Passlib       |
| インフラ       | MySQL, dotenv(.env), systemd/Windows Service (運用環境での常駐化を想定)              |
| ツール         | npm, pip, alembic, pytest, ESLint, Prettier；バックエンドは Black / Flake8 / Mypy を `requirements.txt` に含む |

## 📁 プロジェクト構造

```
Smart-EMAPs/
├── backend/                    # バックエンド（FastAPI + Python）
│   ├── app/
│   │   ├── core/              # コア機能（設定、DB、セキュリティ、日時処理）
│   │   ├── modules/           # 機能モジュール
│   │   │   ├── auth/          # 認証・認可
│   │   │   ├── erp/           # ERP（販売、購買、在庫、原価、受注）
│   │   │   ├── aps/           # APS（生産計画、スケジューリング）
│   │   │   ├── mes/           # MES（製造実行、品質管理）
│   │   │   ├── master/        # マスタデータ管理
│   │   │   ├── system/        # システム管理
│   │   │   └── websocket/     # WebSocket通信
│   │   ├── models/            # データモデル
│   │   ├── schemas/           # Pydanticスキーマ
│   │   └── main.py            # アプリケーションエントリーポイント
│   ├── database/              # データベース初期化スクリプト
│   ├── alembic/               # マイグレーション
│   ├── requirements.txt       # Python依存関係
│   └── .env                   # 環境変数設定
│
├── frontend/                   # フロントエンド（Vue.js 3 + TypeScript）
│   └── src/
│       ├── api/               # APIクライアント
│       ├── shared/            # 共有（例: api/request、router 拡張）
│       ├── components/        # 共通コンポーネント
│       ├── layouts/           # レイアウトコンポーネント
│       ├── locales/           # 国際化リソース（ja / zh / vi 等）
│       ├── modules/           # ドメイン別モジュール（例: auth）
│       ├── router/            # ルーティング・メニュー設定
│       ├── stores/            # Piniaストア
│       ├── types/             # TypeScript型定義
│       ├── utils/             # ユーティリティ
│       ├── views/             # ページビュー
│       │   ├── account/       # アカウント・プロフィール
│       │   ├── erp/           # ERP画面（受注・販売・購買・在庫・出荷・原価 等）
│       │   ├── aps/           # APS画面（切断・溶接・成形計画 等）
│       │   ├── mes/           # MES画面（工程別作業指示 等）
│       │   ├── master/        # マスタ（品目・BOM・工程・材料検査 等）
│       │   └── system/        # システム管理画面
│       ├── App.vue            # ルートコンポーネント
│       └── main.ts            # アプリケーションエントリーポイント
│
├── docs/                       # ドキュメント
│   ├── PROJECT_STRUCTURE.md   # プロジェクト構造・規約
│   ├── BUILD_AND_DEPLOY.md    # ビルド・デプロイ
│   ├── ORDER_MODULE_GUIDE.md  # 受注モジュール
│   ├── WEBSOCKET_IMPLEMENTATION.md
│   └── （その他）操作説明・設計メモ
│
├── Master/                     # マスタデータファイル
├── logs/                       # ログファイル
├── start.py                    # 統合起動スクリプト
├── start.bat                   # Windows起動スクリプト
├── start.sh                    # Linux/Mac起動スクリプト
└── README.md                   # このファイル
```

詳細なプロジェクト構造については、[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) を参照してください。

### リポジトリ規約（要約）

- **タイムゾーン**: JST（`Asia/Tokyo`）で統一。バックエンドは `app.core.datetime_utils`、フロントは Day.js + Element Plus `ja` を使用。
- 詳細は [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) の冒頭「プロジェクト規約」を参照。

## 🧩 アーキテクチャ詳細

### フロントエンド詳細

- **エントリーポイント**: `frontend/src/main.ts`, ルートコンポーネントは `App.vue`
- **ルーティング**: `frontend/src/router` で画面ごとにルートを定義し、ERP / APS / MES / System などドメイン単位でモジュール分割
- **状態管理**: `frontend/src/stores` の Pinia ストアでグローバル状態（ログイン情報、権限、共通マスタなど）を集中管理
- **API クライアント**: `frontend/src/api` で Axios ベースの API ラッパを定義し、エラーハンドリング・トークン付与・共通レスポンス形式を統一
- **UI コンポーネント**:
  - 共通フォーム・検索条件パネル・一覧テーブル・ダイアログなどを `components` に共通化
  - `views/erp` 以下は販売・購買・在庫・生産などドメインごとの画面を配置

### バックエンド詳細

- **エントリーポイント**: `backend/app/main.py`
- **ミドルウェア**: `/api/*` の API 連携ログ記録（`ApiLogMiddleware` → `api_logs` テーブル）
- **設定**: `backend/app/core/config.py` の `Settings` クラスで `.env` を読み込み、DB 接続・CORS・ファイル監視などの設定を一元管理
- **DB 接続**: `backend/app/core/database.py`（存在する場合）で SQLAlchemy セッションおよび接続プールを管理
- **ドメインモジュール** (`backend/app/modules`):
  - `auth` / `system`: 認証・ユーザー・権限・設定
  - `erp`: 販売・在庫・受払ログ・生産実績など ERP 領域
  - `aps`: APS（計画・モデル）
  - `cutting_planning`: 切断計画作成
  - `mes`: MES
  - `master`: 各種マスタ（品目・工程・取引先・BOM 関連 等）
  - `order`: 受注ロット・日次/月次オーダー
  - `database`: DB ユーティリティ・在庫 KPI 等
  - `outsourcing`: 外注（溶接・仕入先・在庫 等）
  - `material`: 材料・受入・検査・在庫・予測 等
  - `material_data_generation` / `part_data_generation`: 在庫データ生成
  - `part` / `part_order`: 部品購買・在庫・部品注文
  - `shipping`: 出荷・ピッキング・宛先グループ・印刷履歴 等
  - `excel_monitor`: Excel 監視・計画データ連携
  - `machine_work_time_config`: 設備運行時間設定
  - `production_schedule`: 生産状況・スケジュール（`/api` 配下にルート集約）
  - `plan_baseline`: 生産計画ベースライン
  - `websocket`: `/ws` でリアルタイム通信（`main.py` で登録）
- **スキーマとモデル**:
  - `models/`: SQLAlchemy モデル（テーブル定義）
  - `schemas/`: Pydantic スキーマ（リクエスト/レスポンス、内部 DTO）

#### 現行 API プレフィックス一覧（`backend/app/main.py`）

| プレフィックス | 説明（tags） |
|----------------|--------------|
| `/api/auth` | 認証 |
| `/api/erp` | ERP |
| `/api/aps` | APS |
| `/api/cutting-planning` | 切断計画作成 |
| `/api/mes` | MES |
| `/api/master` | マスタ管理 |
| `/api/system` | システム管理 |
| `/api/order` | 受注ロット |
| `/api/database` | データベース |
| `/api/outsourcing` | 外注管理 |
| `/api/material` | 材料管理 |
| `/api/material-data-generation` | 材料在庫データ生成 |
| `/api/part` | 部品購買・在庫 |
| `/api/part-data-generation` | 部品在庫データ生成 |
| `/api/part-order` | 部品注文 |
| `/api/shipping` | 出荷管理 |
| `/api/excel-monitor` | Excel監視・計画データ |
| `/api/machine-work-time-config` | 設備運行時間設定 |
| `/api` | 生産状況・スケジュール（`production_schedule`：`/processing-status`、`/schedule`、`/plan/batch/...` 等） |
| `/api/plan-baseline` | 生産計画ベースライン |
| `/ws` | WebSocket |

- **ファイル監視サービス**:
  - `app/services/file_watcher/` 以下で CSV / Excel ファイル監視と DB 同期を実装
  - `inspection_excel_processor.py`: 検査工程 Excel から `stock_transaction_logs` への取り込みロジック

### データベース詳細

- **マイグレーション管理**: `backend/alembic` と `backend/database/migrations` でテーブル・インデックス・トリガーなどを管理
- **主なテーブル例**:
  - `stock_transaction_logs`: 在庫受払履歴（製品/材料/仕掛品の入出庫・実績・不良）
  - `materials`, `products`, `machines`, `processes`: 基本マスタ群
  - `production_orders`, `production_schedules`, `production_results`: 生産指図・スケジュール・実績
- **接続文字列**: `.env` の `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` から生成（`Settings.get_database_url()`）

## ✨ 主要機能

### 📊 1. ERP：販売管理 (Sales / SD)

顧客からの注文を受け、出荷し、売上を立てるまでのプロセス。

- **見積管理**
  - 見積作成、版数管理、承認ワークフロー
  - 原価積算シミュレーション（過去実績や標準原価に基づいた利益率試算）
- **受注管理**
  - 受注データ登録
  - 内示・フォーキャスト管理（確定前の需要予測をAPSへ連携）
  - 与信管理（受注時の限度額チェック・アラート）
  - 契約単価管理（期間別・数量別ボリュームディスカウント）
- **出荷管理**
  - 出荷指示、ピッキングリスト、分納（分割出荷）管理
  - 預かり在庫出荷（売上計上済み製品の出荷指示）
- **売上・請求管理**
  - 売上計上（出荷基準/検収基準の切替）、請求書発行（インボイス対応）
  - 赤黒訂正処理（返品・値引き時の伝票修正）

### 🛒 2. ERP：購買・外注管理 (Procurement & Subcontracting)

材料の調達だけでなく、協力工場への加工依頼（外注）を強化。

- **発注管理**
  - 発注書発行、承認フロー、納期回答入力（納期遵守率管理）
  - 定期発注・都度発注の自動計算（MRP連携）
- **外注加工管理** (★重要)
  - 有償/無償支給管理（自社材料を外注先に送る処理）
  - 外注加工指示書発行、外注先在庫管理（外注先にある自社資産の把握）
  - 加工費単価管理
- **受入・検収管理**
  - 入荷予定管理、受入登録、受入検査（良品/不良/保留判定）
  - ロット番号付与（トレーサビリティの開始点）
- **債務管理**
  - 請求書照合、支払予定表作成、FBデータ（銀行振込）作成

### 📦 3. ERP：在庫管理 (Inventory / WMS)

「帳簿在庫」と「実在庫」を一致させるための機能。

- **在庫・ロケーション管理**
  - リアルタイム在庫照会、マルチ倉庫・ロケーション管理
  - 有効在庫照会（現在庫 - 引当済 + 入荷予定）
- **入出庫・移動管理**
  - 入出庫履歴、倉庫間移動、セット品組立・分解
  - ロット・トレーサビリティ（正展開：製品→材料、逆展開：材料→製品）
- **棚卸管理**
  - 一斉棚卸、循環棚卸（サイクルカウント）
  - 棚卸差異分析・修正、滞留在庫（デッドストック）アラート

### 🏭 4. ERP：生産管理 (Production Control / PP)

製造の「基準」と「指示」を管理し、APS/MESへつなぐハブ。

- **エンジニアリング（基準情報）**
  - 設計変更(ECO)管理（BOMの版数管理、切替日設定）
  - BOM正展開・逆展開（構成部品検索・使用先検索）
- **生産計画 (ERP側)**
  - MRP (所要量計算)、生産オーダー生成
  - 製番管理（個別受注生産向け：オーダー別原価管理用の番号発行）
- **製造指示**
  - 製造指図書（現品票）発行、材料出庫指示（先入れ先出し）
- **生産実績 (ERP側)**
  - 完成報告（製品入庫）、材料消費実績（バックフラッシュ/実消費）

### 💰 5. ERP：原価・財務連携 (Costing & Finance)

製造現場の活動をお金に換算し、経営判断を支援。

- **原価計算**
  - 標準原価 vs 実際原価の差異分析
  - 配賦計算（労務費・製造経費・光熱費の製品別配賦）
  - 仕掛品(WIP)評価（月末時点の工程内在庫の評価額算出）
- **固定資産管理**
  - 設備台帳、減価償却計算（製造原価への連携）
- **会計連携**
  - 自動仕訳生成（売上・仕入・移動・製造振替）、会計ソフト出力

### 🎯 6. APS：先進的計画・スケジューリング

「いつ・どこで・誰が」作るかを最適化する頭脳。

- **スケジューリング**
  - 有限能力スケジューリング（設備・人の制約を考慮）
  - 段取最適化（色替え、型替えを最小にする順序並べ替え）
  - 緊急割込計画（特急オーダー時の再計算）
- **負荷計画**
  - 山積み・山崩しチャート（負荷調整）、ボトルネック特定
- **シミュレーション**
  - 納期回答シミュレーション、設備故障時の影響分析

### 🖥️ 7. MES：製造実行システム

現場（Shop Floor）の「今」を可視化し、品質を作り込む。

- **製造実行 (Execution)**
  - **電子作業手順書(SOP)** 表示（図面・動画）
  - タブレット実績入力（開始/終了/中断/再開）、作業者スキル認証
- **品質管理 (Quality / QMS)**
  - 工程内検査記録、SPC（統計的工程管理）チャート
  - 不適合品管理 (NC)（不良発生時の処置・原因・対策フロー）
- **設備・保全管理**
  - 金型・治具管理（ショット数管理、所在管理、メンテ期限）
  - 設備稼働監視（信号灯連携）、OEE（設備総合効率）分析
  - アンドン（異常発生時の管理者呼び出し通知）

### ⚙️ 8. 共通基盤・システム管理

システム全体を支えるインフラ機能。

- **マスタデータ管理 (MDM)**
  - カレンダーマスタ（工場カレンダー、シフトパターン）
  - 単位換算マスタ（仕入単位kg → 消費単位g などの変換）
  - 取引先・品目・BOM・工程・設備・社員マスタ
- **システム管理**
  - ロールベース権限管理(RBAC)（5段階権限設定）
  - API連携監視（ERP⇔APS⇔MES間のデータ転送ログ・エラー通知）
  - 多言語・多通貨対応（海外拠点展開用）
  - 監査ログ（誰がいつデータを変更したかの追跡）

## 🔄 システム間連携

### 計画の連鎖 (ERP → APS → MES)

1. **受注登録** (ERP) → 受注情報がAPSに連携
2. **生産計画** (APS) → 需要に基づき最適な生産計画を立案
3. **スケジューリング** (APS) → 詳細な作業スケジュールを生成
4. **作業指示** (MES) → 現場に作業指示を配信

### 実績のフィードバック (MES → APS → ERP)

1. **実績収集** (MES) → 作業実績、品質データをリアルタイム収集
2. **計画調整** (APS) → 実績に基づき計画を動的に再調整
3. **在庫更新** (ERP) → 生産実績に基づき在庫を自動更新
4. **原価計算** (ERP) → 実際原価を計算、差異分析

## 🛠️ セットアップ手順

### 前提条件

- **Node.js**: 18.0以上
- **Python**: 3.10以上
- **MySQL**: 8.0以上

### クイックスタート（推奨）

プロジェクトルートで以下のコマンドを実行すると、バックエンドとフロントエンドを同時に起動できます：

**Windows:**

```bash
start.bat
```

**Linux/Mac:**

```bash
chmod +x start.sh
./start.sh
```

**または直接Pythonスクリプトを実行:**

```bash
python start.py
```

起動スクリプトは以下を自動的に実行します：

- ✅ 環境チェック（Python、Node.js、MySQL）
- ✅ 依存関係の確認とインストール
- ✅ ポートの使用状況確認と解放
- ✅ バックエンドサーバーの起動（ポート: 8005）
- ✅ フロントエンド開発サーバーの起動（ポート: 5000）
- ✅ フロントエンド本番サーバーの起動（ポート: 3005）
- ✅ **ファイル監視**（`start.py` 内のプロセス名「ファイル監視」）：`.env` の `FILE_WATCH_*` で共有フォルダ上の CSV / 生産計画 Excel を監視する場合に利用（パス未設定・到達不能時はスキップやエラーになることがあります）。API プロセス内で監視を起動する場合は `FILE_WATCH_START_WITH_API=true`（`backend/app/core/config.py`）を参照。
- ✅ **HTTPS（任意）**: ルートの `.env` または `backend/.env` で `HTTPS_ENABLED=true` かつ `SSL_CERTFILE` / `SSL_KEYFILE` を指定すると、`start.py` 経由でバックエンド（8005）およびフロント dist 本番（3005）を TLS で待ち受け可能。HTTPS 時、プレーン HTTP のフォールバックは **3004**（`frontend_prod_http_fallback_port`）。

起動後、以下のURLでアクセスできます：

- **フロントエンド（開発）**: http://localhost:5000
- **フロントエンド（本番）**: http://localhost:3005
- **バックエンドAPI**: http://localhost:8005
- **APIドキュメント**: http://localhost:8005/docs

### 手動セットアップ

#### 1. データベースの初期化

```bash
mysql -u root -p
```

MySQL クライアント内でユーザーを作成します（**データベース名は `backend/.env` の `DB_NAME` と一致**させてください。`env.example` では `eams_db` の例です）。

```sql
CREATE DATABASE eams_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'emap_user'@'localhost' IDENTIFIED BY 'emap_password';
GRANT ALL PRIVILEGES ON eams_db.* TO 'emap_user'@'localhost';
FLUSH PRIVILEGES;
```

シェルから初期化スクリプトを流します。

```bash
mysql -u emap_user -p eams_db < backend/database/init/01_init.sql
```

続けて `backend/database/migrations/` 配下の SQL を**番号順**に適用します。APS まわりの新規環境では基線 `200_unified_aps_schema.sql` とその後の増分をどう扱うか、[backend/database/migrations/README.md](backend/database/migrations/README.md) を参照してください。

#### 2. バックエンドセットアップ

```bash
cd backend

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp env.example .env
# .envファイルを編集してデータベース接続情報を設定

# サーバーの起動
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

#### 3. フロントエンドセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev

# または本番ビルド
npm run build
npm run preview

# 品質チェック（任意）
npm run lint
npm run type-check
npm run build:check
```

### バックエンド・フロントエンドの接続

- **開発時**: `frontend/vite.config.ts` の `server.proxy` で `/api` と WebSocket を `http://localhost:8005`（および `ws://localhost:8005`）へ転送します。Axios のベース URL は空（相対パス）でプロキシ経由になります（`frontend/src/shared/api/request.ts`）。
- **本番ビルド**: 環境変数 `VITE_API_BASE_URL`、または配布時に注入する `api-config.js` の `__API_BASE__` で API の基底 URL を上書きできます。

## 📋 環境変数（バックエンド）

`backend/env.example` を `backend/.env` にコピーして編集します（**本番では `SECRET_KEY` / JWT 系を必ず変更**）。

| 変数 | 説明 |
|------|------|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL 接続。DB 名は作成したデータベースと一致させる |
| `SECRET_KEY`, `JWT_SECRET` / `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | 認証トークン関連 |
| `CORS_ORIGINS`, `CORS_ALLOW_ALL` | フロントエンドオリジンの許可（LAN から開発する場合は調整） |
| `TIMEZONE` | 既定 `Asia/Tokyo` |
| `LOG_LEVEL`, `LOG_FILE` | ログ出力 |
| `HTTPS_ENABLED`, `SSL_CERTFILE`, `SSL_KEYFILE` | `start.py` 利用時の TLS（自己署名可）。未使用なら `HTTPS_ENABLED=false` |
| `FILE_WATCH_BASE_PATH`, `FILE_WATCH_EXCEL_BASE_PATH`, `FILE_WATCH_POLL_INTERVAL`, `FILE_WATCH_DEBOUNCE_SEC` | 共有フォルダ上の CSV / 生産計画 Excel 監視（未使用なら空またはコメントアウトでよい） |
| `FILE_WATCH_START_WITH_API` | `true` のとき API 起動時にファイル監視バックグラウンドを有効化（`FILE_WATCH_BASE_PATH` 等が有効な場合） |

`.env` は **UTF-8** で保存してください（ファイル監視コメントの通り）。

## 🧪 テスト・静的解析

- **フロントエンド**: `npm run lint`、`npm run type-check`、`npm run build:check`
- **バックエンド**: `requirements.txt` に Pytest 系および Black / Flake8 / Mypy が含まれます。例: `cd backend && pytest`；整形・静的解析は各ツールの標準コマンドで実行します。

## 🔧 トラブルシューティング（よくある件）

| 現象 | 確認すること |
|------|----------------|
| フロントから API が 404 / 接続不可 | バックエンドが `8005` で起動しているか、`vite` 開発サーバを経由しているか（直に `file://` で開いていないか） |
| CORS エラー | `backend/.env` の `CORS_ORIGINS` にフロントの URL（例: `http://localhost:5000`）が含まれるか。開発のみなら `CORS_ALLOW_ALL=true` の是非を検討 |
| ポート使用中 | `start.py` が解放を試みます。手動の場合は `8005` / `5000` / `3005` を占有しているプロセスを終了 |
| ファイル監視が失敗する | `FILE_WATCH_*` のパスが存在し、実行ユーザーから読み取れるか（UNC パスは権限・ネットワークに注意） |

## 🧰 開発環境・推奨エディタ/プラグイン

### 推奨エディタ

- **Visual Studio Code / Cursor**（本リポジトリ想定）

### VSCode/Cursor 推奨拡張機能

- **フロントエンド**
  - Vue Language Features (Volar)
  - TypeScript Vue Plugin
  - ESLint
  - Prettier - Code formatter
  - Stylelint
- **バックエンド**
  - Python
  - Pylance
  - isort
- **共通**
  - GitLens — Git 履歴と差分確認
  - Error Lens — エラー・警告のインライン表示
  - TODO Highlight — TODO/FIXME の可視化

### コードフォーマット・Lint

- **フロントエンド**
  - ESLint + Prettier による統一フォーマット（`.eslintrc` / `.prettierrc` に準拠）
- **バックエンド**
  - `black` / `isort` / `flake8`（または同等ツール）による Python コード整形・静的解析（導入済み/導入予定の環境に応じて利用）

## 🎨 モダンUI/UXデザイン

Smart-EMAPsは、最先端のグラスモーフィズム（Glassmorphism）デザインを採用した、プレミアムで洗練されたユーザーインターフェースを提供します：

### デザインシステム

- **🌈 グラスモーフィズム**: 半透明のガラス効果とブラー（ぼかし）による奥行き感のあるレイヤー構造
- **✨ グラデーション**: 紫・青・ピンク系の美しいグラデーション配色
- **💎 プレミアム感**: 洗練されたシャドウ、ハイライト、トランジション効果
- **📐 コンパクトレイアウト**: 情報密度を最適化し、無駄な空白を削減
- **📱 完全レスポンシブ**: デスクトップ（1920px）、タブレット（768px）、モバイル（480px）に完全対応

### 主要UIコンポーネント

- **ツールバー**: グラデーション背景 + ガラスエフェクト + 浮遊感のあるボタン
- **フィルターバー**: インライン配置 + ガラス背景 + アイコンベースのUI
- **データテーブル**: ガラス背景 + ホバーエフェクト + 純黒テキスト
- **ダイアログ**: グラデーションヘッダー + セクション分割 + コンパクトフォーム
- **サマリーカード**: アニメーション + ホバー効果 + カラフルなアイコン
- **サイドバーメニュー**: ファビコンロゴ + スムーズな展開/折りたたみ
- **タブナビゲーション**: ガラス効果 + アクティブ状態の視覚的フィードバック

### アニメーション・インタラクション

- **マイクロアニメーション**: ボタンホバー、カードホバー、ページ遷移
- **スムーズトランジション**: 0.2s～0.3sの心地よい動き
- **視覚的フィードバック**: クリック、ホバー、フォーカス時の即座な反応

## 🌍 国際化・タイムゾーン

- **タイムゾーン**: 日本標準時（JST, Asia/Tokyo）で統一
- **言語**: 既定は日本語。`frontend/src/locales` に **日本語（ja）・中国語（zh）・ベトナム語（vi）** 等のリソースがあり、Vue I18n で切替可能（画面・メニューによっては ja 中心の箇所あり）。
- **日時フォーマット**: Day.jsによる柔軟な日時処理
- **ロケール**: Element Plus のロケールとあわせて利用

## 📝 ライセンス

このプロジェクトは独自のライセンスの下でライセンスされています。

## 👥 開発チーム

Smart-EMAPs開発チーム

---

**最終更新日時**: 2026年4月19日（日本時間）
