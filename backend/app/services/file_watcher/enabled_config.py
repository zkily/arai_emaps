# coding: utf-8
"""ファイル監視の「有効/無効」設定の読書き（JSON、API と watcher で共用）"""
import json
import os
from pathlib import Path

from app.services.file_watcher.sync_services import STOCK_FILES, MATERIAL_FILES, PICKING_FILES

# backend/data/file_watcher_enabled.json（API と watcher で共用）
_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_ENABLED_JSON = _BACKEND_ROOT / "data" / "file_watcher_enabled.json"

_ALL_FILE_NAMES = list(STOCK_FILES) + list(MATERIAL_FILES) + list(PICKING_FILES)


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
    """{ "StockIn.csv": True, ..., "PickingLog.csv": True, "excel_watcher_enabled": True } を返す。未設定は True"""
    raw = _read_raw()
    result = {}
    for name in _ALL_FILE_NAMES:
        result[name] = raw.get(name, True)
    result["excel_watcher_enabled"] = raw.get("excel_watcher_enabled", True)
    return result


def set_enabled(enabled: dict, excel_watcher_enabled: bool = True) -> None:
    """有効設定を書き込む（STOCK + MATERIAL + PICKING のキーと excel_watcher_enabled）"""
    all_names = set(STOCK_FILES) | set(MATERIAL_FILES) | set(PICKING_FILES)
    to_save = {k: bool(v) for k, v in enabled.items() if k in all_names}
    to_save["excel_watcher_enabled"] = bool(excel_watcher_enabled)
    _ENABLED_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(_ENABLED_JSON, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=2)


def is_file_enabled(filename: str) -> bool:
    """監視プロセス用：そのファイル名が有効か（未設定・キーなしは True）"""
    raw = _read_raw()
    return raw.get(filename, True)


def is_excel_watcher_enabled() -> bool:
    """Excel 計画監視が有効か（未設定は True）。環境変数 DISABLE_EXCEL_WATCHER は run 側で別途参照。"""
    raw = _read_raw()
    return raw.get("excel_watcher_enabled", True)
