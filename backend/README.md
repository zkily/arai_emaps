# Smart-EMAPs Backend

FastAPI バックエンド。エントリは `app/main.py`、環境変数テンプレートは `env.example`。

## ディレクトリ構成

```
backend/
├── app/
│   ├── main.py              # FastAPI エントリ・ルータ登録・バックグラウンドタスク
│   ├── core/                # 設定・DB・認証・ログ・ミドルウェア・例外
│   ├── modules/             # ドメイン別 API（下表参照）
│   └── services/            # モジュール横断サービス
├── database/
│   ├── init/                # 初回セットアップ SQL
│   └── migrations/          # 番号付き差分マイグレーション（README 参照）
├── data/                    # ファイル監視の永続設定（例: file_watcher_enabled.json）
├── certs/                   # 開発用 TLS（.gitkeep のみコミット、証明書はローカル生成）
├── env.example              # .env のひな形
├── requirements.txt
├── pyproject.toml           # Black / isort / mypy / pytest
├── run_file_watcher.py      # CSV/Excel 監視のスタンドアロン起動
└── .flake8
```

### `app/modules/` 一覧（`main.py` 登録順）

| ディレクトリ | API プレフィックス | 役割 |
|-------------|-------------------|------|
| `auth` | `/api/auth` | 認証・ユーザー |
| `erp` | `/api/erp` | 販売・在庫・原価・生産実績など ERP 統合 |
| `aps` | `/api/aps` | 生産計画・スケジューリング |
| `cutting_planning` | `/api/cutting-planning` | 切断計画 |
| `mes` | `/api/mes` | 製造実行 |
| `master` | `/api/master` | マスタ（製品・材料・工程・BOM 等） |
| `system` | `/api/system` | システム・設定・DB バックアップ |
| `order` | `/api/order` | 受注ロット |
| `database` | `/api/database` | 生産サマリ・KPI・成形日次計画 |
| `outsourcing` | `/api/outsourcing` | 外注 |
| `material` | `/api/material` | 材料在庫・受入・検品 |
| `material_data_generation` | `/api/material-data-generation` | 材料在庫データ生成 |
| `part` | `/api/part` | 部品購買・在庫 |
| `part_data_generation` | `/api/part-data-generation` | 部品在庫データ生成 |
| `part_order` | `/api/part-order` | 部品注文 |
| `shipping` | `/api/shipping` | 出荷・ピッキング |
| `excel_monitor` | `/api/excel-monitor` | Excel 監視・計画データ |
| `machine_work_time_config` | `/api/machine-work-time-config` | 設備運行時間 |
| `production_schedule` | `/api` | 生産状況・スケジュール |
| `plan_baseline` | `/api/plan-baseline` | 生産計画ベースライン |
| `websocket` | `/ws` | WebSocket（`main.py` で直接マウント） |

### `app/services/` 横断サービス

| パス | 用途 |
|------|------|
| `mysql_backup.py` | mysqldump・バックアップパス正規化 |
| `full_database_backup.py` | 自動/手動フル DB バックアップ |
| `backup_paths.py` | バックアップ保存先 |
| `data_management_io.py` | データ入出力（システム設定から利用） |
| `file_watcher/` | BT-data CSV / Excel 同期 |
| `access_sync/` | Access 向け生産計画 Excel 同期 |

### モジュール内のファイル命名

- **`api.py`** または **`*_api.py`**: FastAPI `APIRouter`（エンドポイント）
- **`models.py` / `schemas.py`**: SQLAlchemy モデル・Pydantic スキーマ
- **`engine.py`**: 計画・切断などのドメインロジック
- **`services/`**: 当該モジュール専用のビジネスロジック（例: `master/services/`）

`master` モジュールはルーターを `routers/` に集約しています（`models.py` / `schemas.py` はルートに配置）。

## 起動

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy env.example .env          # 編集して DB 接続等を設定
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

ファイル監視のみ別プロセスで動かす場合: `python run_file_watcher.py`

## ローカル専用・コミットしないもの

- `venv/`、`.env`、`logs/`、`__pycache__/`
- `certs/dev-lan.*`（`start.py` が生成する開発用証明書）

リポジトリに含めない空モジュール（過去の実験残骸など）は削除済みです。新規モジュール追加時は必ず `main.py` に `include_router` を登録してください。
