# coding: utf-8
"""ファイル監視の「有効/無効」設定の読書き（JSON、API と watcher で共用）"""
import json
import os
from pathlib import Path

from app.services.file_watcher.sync_services import STOCK_FILES, MATERIAL_FILES

# backend/data/file_watcher_enabled.json（与 run_file_watcher 同进程或 API 进程均可使用）
_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_ENABLED_JSON = _BACKEND_ROOT / "data" / "file_watcher_enabled.json"


def get_enabled_path() -> Path:
    return _ENABLED_JSON


def _read_raw() -> dict:
    """JSON を読む。存在しないか異常時は空 dict"""
    if not _ENABLED_JSON.exists():
        return {}
    try:
        with open(_ENABLED_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_enabled() -> dict:
    """{ "StockIn.csv": True, ... } を返す。未設定のキーは True（既定で有効）"""
    raw = _read_raw()
    all_files = list(STOCK_FILES) + list(MATERIAL_FILES)
    result = {}
    for name in all_files:
        result[name] = raw.get(name, True)
    return result


def set_enabled(enabled: dict) -> None:
    """有効設定を書き込む（STOCK_FILES + MATERIAL_FILES のキーのみ保存）"""
    all_names = set(STOCK_FILES) | set(MATERIAL_FILES)
    to_save = {k: bool(v) for k, v in enabled.items() if k in all_names}
    _ENABLED_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(_ENABLED_JSON, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=2)


def is_file_enabled(filename: str) -> bool:
    """監視プロセス用：そのファイル名が有効か（未設定・キーなしは True）"""
    raw = _read_raw()
    return raw.get(filename, True)
