#!/usr/bin/env python
# coding: utf-8
"""
BT-data 受信 CSV ファイル監視エントリ
プロジェクトルートから実行: python run_file_watcher.py
.env に FILE_WATCH_BASE_PATH（監視ディレクトリ）を設定してください。
"""
import os
import sys
import logging

# 确保 backend 为可导入路径（可在此目录执行 python run_file_watcher.py）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# .env 読込（FastAPI と同様、UTF-8 で日本語パスを正しく読む）
try:
    from dotenv import load_dotenv
    import os as _os
    _env_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".env")
    load_dotenv(_env_path, encoding="utf-8")
except Exception as e:
    print(f"[file-watcher] dotenv の読込に失敗しました: {e}", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


def _ensure_openpyxl_if_excel_enabled():
    """Excel 監視有効時、起動前に openpyxl の有無を確認（実行時エラー防止）"""
    if os.environ.get("DISABLE_EXCEL_WATCHER", "").strip().lower() == "true":
        return
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print(
            "[file-watcher] Excel 監視には openpyxl が必要です。次のコマンドでインストールしてください：",
            file=sys.stderr,
        )
        print(f'  "{sys.executable}" -m pip install openpyxl', file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _ensure_openpyxl_if_excel_enabled()
    try:
        from app.services.file_watcher.run import run_watcher
        run_watcher()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import traceback
        print("[file-watcher] 起動に失敗しました:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
