"""
アプリケーション設定
環境変数から設定を読み込み
"""
from pydantic_settings import BaseSettings
from typing import List, Optional


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
    
    # JWT設定
    JWT_SECRET: Optional[str] = None  # JWT_SECRET_KEYのエイリアス
    JWT_SECRET_KEY: str = "smart_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
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
    ]
    
    # 開発環境でネットワークアクセスを許可する場合
    # 環境変数 CORS_ALLOW_ALL=true で有効化
    CORS_ALLOW_ALL: bool = False
    
    # タイムゾーン
    TIMEZONE: str = "Asia/Tokyo"
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    # SQL ログ（有効だと起動・処理が重くなるため、デバッグ時のみ True 推奨）
    SQL_ECHO: bool = False

    # ファイル監視：CSV 受信 + 生産計画 Excel（2 ディレクトリを別々に指定可）
    FILE_WATCH_BASE_PATH: str = ""  # CSV 受信ディレクトリ（いずれか必須）
    FILE_WATCH_EXCEL_BASE_PATH: str = ""  # Excel 計画ディレクトリ（省略時は BASE と共用）
    FILE_WATCH_POLL_INTERVAL: float = 1.0  # ネットワークパスは 1 秒推奨
    FILE_WATCH_DEBOUNCE_SEC: int = 2
    FILE_WATCH_EXCEL_WORKERS: int = 3  # 同時処理は最大 3 ファイル
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
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


# 設定インスタンスの作成
settings = Settings()

