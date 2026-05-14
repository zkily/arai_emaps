"""
アプリケーション設定
環境変数から設定を読み込み
"""
import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Tuple


class Settings(BaseSettings):
    """アプリケーション設定クラス"""
    
    # アプリケーション基本設定
    APP_NAME: str = "Smart-EMAP"
    SERVER_NAME: str = "生産管理システム"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # データベース設定
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "136228508"
    DB_NAME: str = "eams_db"
    DATABASE_URL: Optional[str] = None  # 自動生成（未設定の場合）
    # データベース全件バックアップ（mysqldump）の既定保存先（UNC 可）。UI 未設定時のデフォルト。
    BACKUP_DEFAULT_STORAGE_PATH: str = (
        r"\\192.168.1.200\社内共有\02_生産管理部\バックアップ\Mysql-backup"
    )
    # mysqldump 実行ファイル。空または "mysqldump" のとき PATH と Windows 標準インストール先を自動探索
    MYSQLDUMP_BIN: str = "mysqldump"
    # .env による日次自動全庫バックアップ（FastAPI プロセス内 asyncio）。TIMEZONE（既定 Asia/Tokyo）で解釈。
    DB_AUTO_BACKUP_ENABLED: bool = False
    DB_AUTO_BACKUP_TIME: str = "02:00"  # HH:MM（24 時間制）
    DB_AUTO_BACKUP_CATCHUP_ON_START: bool = True
    DB_AUTO_BACKUP_RETENTION: int = 7
    DB_AUTO_BACKUP_COMPRESS: bool = True
    
    # JWT設定
    JWT_SECRET: Optional[str] = None  # JWT_SECRET_KEYのエイリアス
    JWT_SECRET_KEY: str = "smart_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 12 小时
    
    # CORS設定
    # 開発環境ではすべてのオリジンを許可（ネットワークアクセス対応）
    # 本番環境では特定のオリジンのみ許可することを推奨
    CORS_ORIGINS: List[str] = [
        "http://localhost:5000",
        "http://localhost:3000",
        "http://localhost:3005",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3005",
        "http://192.168.1.59:3005",
        "https://localhost:5000",
        "https://127.0.0.1:5000",
        "https://localhost:3005",
        "https://127.0.0.1:3005",
    ]
    
    # 開発環境でネットワークアクセスを許可する場合
    # 環境変数 CORS_ALLOW_ALL=true で有効化
    CORS_ALLOW_ALL: bool = False

    # HTTPS（uvicorn 直接起動時。証明書パスはプロジェクトルートまたは絶対パス）
    HTTPS_ENABLED: bool = False
    SSL_CERTFILE: Optional[str] = None
    SSL_KEYFILE: Optional[str] = None
    
    # タイムゾーン
    TIMEZONE: str = "Asia/Tokyo"
    
    # フロント「api-config.js」の window.__API_BASE__（空＝相対パスで同一オリジンの /api を利用）
    PUBLIC_API_BASE: str = ""

    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    # SQL ログ（有効だと起動・処理が重くなるため、デバッグ時のみ True 推奨）
    SQL_ECHO: bool = False

    # ファイル監視：CSV 受信 + 生産計画 Excel（2 ディレクトリを別々に指定可）
    FILE_WATCH_BASE_PATH: str = ""  # CSV 受信ディレクトリ（いずれか必須）
    # True: FastAPI 起動時に run_file_watcher と同等の監視をバックグラウンドスレッドで開始（別途 python run_file_watcher.py 不要）
    FILE_WATCH_START_WITH_API: bool = False
    FILE_WATCH_EXCEL_BASE_PATH: str = ""  # Excel 計画ディレクトリ（省略時は BASE と共用）
    FILE_WATCH_POLL_INTERVAL: float = 1.0  # ネットワークパスは 1 秒推奨
    FILE_WATCH_DEBOUNCE_SEC: int = 2
    FILE_WATCH_EXCEL_WORKERS: int = 3  # 同時処理は最大 3 ファイル
    FILE_WATCH_INSPECTION_EXCEL_PATH: str = ""  # 検査管理指標 Excel のフルパス
    # 材料切断ログ CSV（material_cutting_logs 取込・監視）。空なら FILE_WATCH_BASE_PATH/materialCutting.csv
    MATERIAL_CUTTING_CSV_PATH: str = ""
    # 材料受入ログ：フルパスをカンマ区切りで指定（最優先。位置変更時はここだけ直せばよい）
    # 例（Windows）: MATERIAL_RECEIVING_CSV_PATHS=\\server\share\受信\Material_Maruiti.csv,\\server\share\受信\Material_Nagoya.csv
    MATERIAL_RECEIVING_CSV_PATHS: str = ""
    # 材料受入 CSV のディレクトリ（MATERIAL_RECEIVING_CSV_PATHS 未指定時に使用）。空＝FILE_WATCH_BASE_PATH と同じ
    MATERIAL_RECEIVING_WATCH_BASE_PATH: str = ""
    # 上記ディレクトリ内のファイル名（カンマ区切り）。空＝デフォルト4種（Maruiti/Nagoya/JFE/Okajima）
    MATERIAL_RECEIVING_WATCH_FILES: str = ""
    # Access 同期（production_plan_excel -> Access）
    ACCESS_PRODUCTION_PLAN_DB_PATH: str = r"\\192.168.1.200\社内共有\02_生産管理部\Data\subdata.accdb"
    ACCESS_PRODUCTION_PLAN_TABLE: str = "A生産予定"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @field_validator("DB_AUTO_BACKUP_TIME")
    @classmethod
    def validate_db_auto_backup_time(cls, v: str) -> str:
        s = (v or "").strip()
        parts = s.split(":")
        if len(parts) != 2:
            raise ValueError("DB_AUTO_BACKUP_TIME は HH:MM（24 時間制）で指定してください")
        try:
            h, m = int(parts[0]), int(parts[1])
        except ValueError as e:
            raise ValueError("DB_AUTO_BACKUP_TIME の時・分が数値ではありません") from e
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("DB_AUTO_BACKUP_TIME の時刻が範囲外です")
        return f"{h:02d}:{m:02d}"
    
    def get_database_url(self) -> str:
        """DATABASE_URLを取得（自動生成または設定値）"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    def get_jwt_secret_key(self) -> str:
        """JWT_SECRET_KEYを取得（JWT_SECRETが設定されている場合は優先）"""
        if self.JWT_SECRET:
            return self.JWT_SECRET
        return self.JWT_SECRET_KEY

    def get_material_cutting_csv_path(self) -> str:
        """materialCutting.csv の絶対パス（UNC 可）。MATERIAL_CUTTING_CSV_PATH 優先。"""
        explicit = (self.MATERIAL_CUTTING_CSV_PATH or "").strip()
        if explicit:
            return explicit
        base = (self.FILE_WATCH_BASE_PATH or "").strip()
        if base:
            return str(Path(base) / "materialCutting.csv")
        return r"\\192.168.1.200\社内共有\02_生産管理部\Data\BT-data\受信\materialCutting.csv"

    def get_material_receiving_watch_base(self) -> str:
        """材料受入 CSV のベースディレクトリ（フルパス一覧未使用時）。"""
        p = (self.MATERIAL_RECEIVING_WATCH_BASE_PATH or "").strip()
        if p:
            return os.path.normpath(os.path.expandvars(p))
        fb = (self.FILE_WATCH_BASE_PATH or "").strip()
        return os.path.normpath(os.path.expandvars(fb)) if fb else ""

    def get_material_receiving_csv_entries(self) -> List[Tuple[str, str]]:
        """
        材料受入 CSV の (絶対パスに正規化したパス, ファイル名) のリスト。
        MATERIAL_RECEIVING_CSV_PATHS がある場合はそのフルパス一覧。
        ない場合は get_material_receiving_watch_base() + ファイル名。
        """
        paths_raw = (self.MATERIAL_RECEIVING_CSV_PATHS or "").strip()
        if paths_raw:
            out: List[Tuple[str, str]] = []
            for part in paths_raw.split(","):
                p = part.strip().strip('"').strip("'")
                if not p:
                    continue
                full = os.path.normpath(os.path.expandvars(p))
                out.append((full, os.path.basename(full)))
            return out

        base = self.get_material_receiving_watch_base()
        raw_names = (self.MATERIAL_RECEIVING_WATCH_FILES or "").strip()
        if raw_names:
            name_list = [x.strip() for x in raw_names.split(",") if x.strip()]
        else:
            name_list = [
                "Material_Maruiti.csv",
                "Material_Nagoya.csv",
                "Material_JFE.csv",
                "Material_Okajima.csv",
            ]
        if not base:
            return []
        nb = os.path.normpath(os.path.expandvars(base))
        return [(os.path.normpath(os.path.join(nb, n)), n) for n in name_list]

    def get_material_receiving_watch_filenames(self) -> List[str]:
        """監視・有効フラグ用のファイル名一覧（ベース名）。"""
        return [b for _, b in self.get_material_receiving_csv_entries()]


# 設定インスタンスの作成
settings = Settings()

