"""
BT-data 受信 CSV ファイル監視サービス
指定ディレクトリの Stock*.csv / Material_*.csv を監視し、stock_transaction_logs / material_logs に同期。
"""
from app.services.file_watcher.run import run_watcher

__all__ = ["run_watcher"]
