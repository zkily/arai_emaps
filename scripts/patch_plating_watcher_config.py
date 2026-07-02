# -*- coding: utf-8
"""Add plating excel watcher hooks (mirror chamfering)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch_file(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in text:
            raise SystemExit(f"pattern not found in {path.name}: {old[:80]!r}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("patched", path.name)


# enabled_config.py
patch_file(
    ROOT / "backend/app/services/file_watcher/enabled_config.py",
    [
        (
            """def is_chamfering_indicator_sync_enabled() -> bool:
    \"\"\"面取管理指標 Excel → chamfering_production_indicator 同期が有効か（未設定は True）。\"\"\"
    raw = _read_raw()
    return raw.get("chamfering_indicator_sync_enabled", True)""",
            """def is_chamfering_indicator_sync_enabled() -> bool:
    \"\"\"面取管理指標 Excel → chamfering_production_indicator 同期が有効か（未設定は True）。\"\"\"
    raw = _read_raw()
    return raw.get("chamfering_indicator_sync_enabled", True)


def is_plating_excel_watcher_enabled() -> bool:
    \"\"\"メッキ管理指標 Excel 監視が有効か（未設定は True）。Excel 計画監視とは独立。\"\"\"
    raw = _read_raw()
    return raw.get("plating_excel_watcher_enabled", True)


def is_plating_indicator_sync_enabled() -> bool:
    \"\"\"メッキ管理指標 Excel → plating_production_indicator 同期が有効か（未設定は True）。\"\"\"
    raw = _read_raw()
    return raw.get("plating_indicator_sync_enabled", True)""",
        ),
    ],
)

# config.py
patch_file(
    ROOT / "backend/app/core/config.py",
    [
        (
            """    FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED: bool = True
    # 材料切断ログ CSV""",
            """    FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED: bool = True
    FILE_WATCH_PLATING_EXCEL_PATH: str = ""
    # 例: \\\\192.168.1.200\\製造部\\11各工程生産管理指標\\6.メッキ工程\\生産管理指標(2026年度-メッキ).xlsx
    # 変更検知時: plating_production_indicator（全件置換同期）
    FILE_WATCH_PLATING_INDICATOR_SYNC_ENABLED: bool = True
    # 材料切断ログ CSV""",
        ),
    ],
)

# env.example
patch_file(
    ROOT / "backend/env.example",
    [
        (
            """FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED=true

# LINE""",
            """FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED=true

# メッキ管理指標 Excel → plating_production_indicator
FILE_WATCH_PLATING_EXCEL_PATH=\\\\192.168.1.200\\製造部\\11各工程生産管理指標\\6.メッキ工程\\生産管理指標(2026年度-メッキ).xlsx
FILE_WATCH_PLATING_INDICATOR_SYNC_ENABLED=true

# LINE""",
        ),
    ],
)

# api.py
patch_file(
    ROOT / "backend/app/modules/production_schedule/api.py",
    [
        (
            """from app.modules.production_schedule.chamfering_production_indicator_registration_api import (
    register_registration_routes as _register_chamfering_indicator_registration_routes,
)

_register_cutting_productivity_routes(router)
_register_cutting_indicator_registration_routes(router)
_register_forming_productivity_routes(router)
_register_chamfering_productivity_routes(router)
_register_chamfering_indicator_registration_routes(router)""",
            """from app.modules.production_schedule.chamfering_production_indicator_registration_api import (
    register_registration_routes as _register_chamfering_indicator_registration_routes,
)
from app.modules.production_schedule.plating_productivity_api import (
    register_routes as _register_plating_productivity_routes,
)

_register_cutting_productivity_routes(router)
_register_cutting_indicator_registration_routes(router)
_register_forming_productivity_routes(router)
_register_chamfering_productivity_routes(router)
_register_chamfering_indicator_registration_routes(router)
_register_plating_productivity_routes(router)""",
        ),
    ],
)

# handler.py
patch_file(
    ROOT / "backend/app/services/file_watcher/handler.py",
    [
        (
            "from app.services.file_watcher.chamfering_excel_processor import is_chamfering_excel_file",
            "from app.services.file_watcher.chamfering_excel_processor import is_chamfering_excel_file\nfrom app.services.file_watcher.plating_excel_processor import is_plating_excel_file",
        ),
        (
            """def is_chamfering_watch_task(filepath: str, filename: str, configured_path: str = "") -> bool:
    \"\"\"設定パスと一致する面取管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）\"\"\"
    if not is_chamfering_excel_file(filename):
        return False
    cfg = (configured_path or "").strip()
    if not cfg:
        return True
    try:
        return _normalize_path(filepath) == _normalize_path(cfg)
    except Exception:
        return False""",
            """def is_chamfering_watch_task(filepath: str, filename: str, configured_path: str = "") -> bool:
    \"\"\"設定パスと一致する面取管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）\"\"\"
    if not is_chamfering_excel_file(filename):
        return False
    cfg = (configured_path or "").strip()
    if not cfg:
        return True
    try:
        return _normalize_path(filepath) == _normalize_path(cfg)
    except Exception:
        return False


def is_plating_watch_task(filepath: str, filename: str, configured_path: str = "") -> bool:
    \"\"\"設定パスと一致するメッキ管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）\"\"\"
    if not is_plating_excel_file(filename):
        return False
    cfg = (configured_path or "").strip()
    if not cfg:
        return True
    try:
        return _normalize_path(filepath) == _normalize_path(cfg)
    except Exception:
        return False""",
        ),
        (
            """        chamfering_watcher_enabled=True,
        chamfering_excel_path: str = "",
        in_queue_excel_filenames=None,""",
            """        chamfering_watcher_enabled=True,
        chamfering_excel_path: str = "",
        plating_watcher_enabled=True,
        plating_excel_path: str = "",
        in_queue_excel_filenames=None,""",
        ),
        (
            """        self.chamfering_watcher_enabled = chamfering_watcher_enabled
        self.chamfering_excel_path = (chamfering_excel_path or "").strip()
        self.in_queue_excel_filenames = (""",
            """        self.chamfering_watcher_enabled = chamfering_watcher_enabled
        self.chamfering_excel_path = (chamfering_excel_path or "").strip()
        self.plating_watcher_enabled = plating_watcher_enabled
        self.plating_excel_path = (plating_excel_path or "").strip()
        self.in_queue_excel_filenames = (""",
        ),
        (
            """        is_chamfering = is_chamfering_watch_task(filepath, filename, self.chamfering_excel_path)
        is_excel_plan = is_excel_plan_watch_task(filename)
        is_csv = is_csv_watch_task(filename, filepath)
        if not is_inspection and not is_welding and not is_cutting and not is_forming and not is_chamfering and not is_excel_plan and not is_csv:""",
            """        is_chamfering = is_chamfering_watch_task(filepath, filename, self.chamfering_excel_path)
        is_plating = is_plating_watch_task(filepath, filename, self.plating_excel_path)
        is_excel_plan = is_excel_plan_watch_task(filename)
        is_csv = is_csv_watch_task(filename, filepath)
        if not is_inspection and not is_welding and not is_cutting and not is_forming and not is_chamfering and not is_plating and not is_excel_plan and not is_csv:""",
        ),
        (
            """        if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_excel_plan:""",
            """        if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_plating or is_excel_plan:""",
        ),
        (
            """            elif is_chamfering:
                if not self.chamfering_watcher_enabled:
                    logger.debug("面取管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif not self.excel_watcher_enabled:""",
            """            elif is_chamfering:
                if not self.chamfering_watcher_enabled:
                    logger.debug("面取管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif is_plating:
                if not self.plating_watcher_enabled:
                    logger.debug("メッキ管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif not self.excel_watcher_enabled:""",
        ),
        (
            """        elif is_chamfering:
            queue_label = "面取Excel"
        elif is_excel_plan:""",
            """        elif is_chamfering:
            queue_label = "面取Excel"
        elif is_plating:
            queue_label = "メッキExcel"
        elif is_excel_plan:""",
        ),
        (
            """        if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_excel_plan:
            self.in_queue_excel_filenames.add(filename)""",
            """        if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_plating or is_excel_plan:
            self.in_queue_excel_filenames.add(filename)""",
        ),
        (
            """            if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_excel_plan:
                self.in_queue_excel_filenames.discard(filename)""",
            """            if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_plating or is_excel_plan:
                self.in_queue_excel_filenames.discard(filename)""",
        ),
    ],
)

print("watcher config patches done")
