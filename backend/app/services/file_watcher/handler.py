# coding: utf-8
"""ファイルイベントハンドラ：デバウンス + キュー投入、監視スレッドをブロックしない"""
import os
import time
import logging
from watchdog.events import FileSystemEventHandler
from app.core.config import settings
from app.services.file_watcher.sync_services import (
    STOCK_FILES,
    MATERIAL_FILES,
    PICKING_FILES,
    MATERIAL_CUTTING_CSV_BASENAME,
)
from app.services.file_watcher.excel_processor import is_excel_target_file
from app.services.file_watcher.inspection_excel_processor import is_inspection_excel_file
from app.services.file_watcher.welding_excel_processor import is_welding_excel_file
from app.services.file_watcher.cutting_excel_processor import is_cutting_excel_file
from app.services.file_watcher.forming_excel_processor import is_forming_excel_file
from app.services.file_watcher.chamfering_excel_processor import is_chamfering_excel_file
from app.services.file_watcher.plating_excel_processor import is_plating_excel_file
from app.services.file_watcher.enabled_config import is_file_enabled

logger = logging.getLogger(__name__)


def is_inspection_watch_task(filepath: str, filename: str, configured_path: str = "") -> bool:
    """設定パスと一致する検査管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）"""
    if not is_inspection_excel_file(filename):
        return False
    cfg = (configured_path or "").strip()
    if not cfg:
        return True
    try:
        return _normalize_path(filepath) == _normalize_path(cfg)
    except Exception:
        return False


def is_welding_watch_task(filepath: str, filename: str, configured_path: str = "") -> bool:
    """設定パスと一致する溶接管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）"""
    if not is_welding_excel_file(filename):
        return False
    cfg = (configured_path or "").strip()
    if not cfg:
        return True
    try:
        return _normalize_path(filepath) == _normalize_path(cfg)
    except Exception:
        return False


def is_cutting_watch_task(filepath: str, filename: str, configured_path: str = "") -> bool:
    """設定パスと一致する切断管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）"""
    if not is_cutting_excel_file(filename):
        return False
    cfg = (configured_path or "").strip()
    if not cfg:
        return True
    try:
        return _normalize_path(filepath) == _normalize_path(cfg)
    except Exception:
        return False


def is_forming_watch_task(filepath: str, filename: str, configured_path: str = "") -> bool:
    """設定パスと一致する成形管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）"""
    if not is_forming_excel_file(filename):
        return False
    cfg = (configured_path or "").strip()
    if not cfg:
        return True
    try:
        return _normalize_path(filepath) == _normalize_path(cfg)
    except Exception:
        return False


def is_chamfering_watch_task(filepath: str, filename: str, configured_path: str = "") -> bool:
    """設定パスと一致する面取管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）"""
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
    """設定パスと一致するメッキ管理指標 Excel か（同一フォルダ内の他年度ファイルを除外）"""
    if not is_plating_excel_file(filename):
        return False
    cfg = (configured_path or "").strip()
    if not cfg:
        return True
    try:
        return _normalize_path(filepath) == _normalize_path(cfg)
    except Exception:
        return False


def _normalize_path(path):
    """パスを正規化し、同一ファイルの重複処理を防ぐ"""
    if not path:
        return ""
    return os.path.normpath(os.path.abspath(path))


def _is_configured_material_cutting_csv(filepath: str) -> bool:
    """settings.get_material_cutting_csv_path() と同一ファイルか（名前変更 .env 対応）"""
    try:
        cfg = os.path.normpath(settings.get_material_cutting_csv_path())
        return os.path.normpath(filepath) == cfg
    except Exception:
        return False


def is_csv_watch_task(filename: str, filepath: str) -> bool:
    """在庫/材料/ピッキング/材料切断 CSV か（Excel 専用キューではなく CSV キューへ）"""
    if filename in STOCK_FILES or filename in MATERIAL_FILES or filename in PICKING_FILES:
        return True
    return _is_configured_material_cutting_csv(filepath)


def is_excel_plan_watch_task(filename: str) -> bool:
    return is_excel_target_file(filename)


class UnifiedHandler(FileSystemEventHandler):
    """検知とキュー投入のみ。CSV と Excel は別キューへ投入しワーカー競合を避ける。"""

    def __init__(
        self,
        csv_task_queue=None,
        excel_task_queue=None,
        excel_watcher_enabled=True,
        inspection_watcher_enabled=True,
        inspection_excel_path: str = "",
        welding_watcher_enabled=True,
        welding_excel_path: str = "",
        cutting_watcher_enabled=True,
        cutting_excel_path: str = "",
        forming_watcher_enabled=True,
        forming_excel_path: str = "",
        chamfering_watcher_enabled=True,
        chamfering_excel_path: str = "",
        plating_watcher_enabled=True,
        plating_excel_path: str = "",
        in_queue_excel_filenames=None,
        in_queue_csv_paths=None,
        # 後方互換（単一キュー）。指定時は CSV/Excel ともにこのキューへ（非推奨）
        task_queue=None,
    ):
        if task_queue is not None and csv_task_queue is None and excel_task_queue is None:
            csv_task_queue = task_queue
            excel_task_queue = task_queue
        self.csv_task_queue = csv_task_queue
        self.excel_task_queue = excel_task_queue
        self.excel_watcher_enabled = excel_watcher_enabled
        self.inspection_watcher_enabled = inspection_watcher_enabled
        self.inspection_excel_path = (inspection_excel_path or "").strip()
        self.welding_watcher_enabled = welding_watcher_enabled
        self.welding_excel_path = (welding_excel_path or "").strip()
        self.cutting_watcher_enabled = cutting_watcher_enabled
        self.cutting_excel_path = (cutting_excel_path or "").strip()
        self.forming_watcher_enabled = forming_watcher_enabled
        self.forming_excel_path = (forming_excel_path or "").strip()
        self.chamfering_watcher_enabled = chamfering_watcher_enabled
        self.chamfering_excel_path = (chamfering_excel_path or "").strip()
        self.plating_watcher_enabled = plating_watcher_enabled
        self.plating_excel_path = (plating_excel_path or "").strip()
        self.in_queue_excel_filenames = (
            in_queue_excel_filenames if in_queue_excel_filenames is not None else set()
        )
        self.in_queue_csv_paths = in_queue_csv_paths if in_queue_csv_paths is not None else set()
        self.last_processed = {}
        self.debounce_sec = getattr(settings, "FILE_WATCH_DEBOUNCE_SEC", 3)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._enqueue(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        self._enqueue(event.src_path)

    def _enqueue(self, filepath):
        if not filepath:
            return
        if os.path.isdir(filepath):
            return
        path_key = _normalize_path(filepath)
        filename = os.path.basename(filepath)
        now = time.time()
        if now - self.last_processed.get(path_key, 0) < self.debounce_sec:
            logger.debug("デバウンスのためスキップ: %s (%.1fs 以内に発生)", filename, self.debounce_sec)
            return
        is_inspection = is_inspection_watch_task(
            filepath, filename, self.inspection_excel_path
        )
        is_welding = is_welding_watch_task(filepath, filename, self.welding_excel_path)
        is_cutting = is_cutting_watch_task(filepath, filename, self.cutting_excel_path)
        is_forming = is_forming_watch_task(filepath, filename, self.forming_excel_path)
        is_chamfering = is_chamfering_watch_task(filepath, filename, self.chamfering_excel_path)
        is_plating = is_plating_watch_task(filepath, filename, self.plating_excel_path)
        is_excel_plan = is_excel_plan_watch_task(filename)
        is_csv = is_csv_watch_task(filename, filepath)
        if not is_inspection and not is_welding and not is_cutting and not is_forming and not is_chamfering and not is_plating and not is_excel_plan and not is_csv:
            logger.debug("監視対象外のため無視: %s", filename)
            return
        if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_plating or is_excel_plan:
            if is_inspection:
                if not self.inspection_watcher_enabled:
                    logger.debug("検査管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif is_welding:
                if not self.welding_watcher_enabled:
                    logger.debug("溶接管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif is_cutting:
                if not self.cutting_watcher_enabled:
                    logger.debug("切断管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif is_forming:
                if not self.forming_watcher_enabled:
                    logger.debug("成形管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif is_chamfering:
                if not self.chamfering_watcher_enabled:
                    logger.debug("面取管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif is_plating:
                if not self.plating_watcher_enabled:
                    logger.debug("メッキ管理指標 Excel 監視は無効のためスキップ: %s", filename)
                    return
            elif not self.excel_watcher_enabled:
                logger.debug("Excel 計画監視は無効のためスキップ: %s", filename)
                return
            if filename in self.in_queue_excel_filenames:
                logger.debug("Excel キューに同名が既にあるためスキップ: %s", filename)
                return
            target_queue = self.excel_task_queue
            if target_queue is None:
                return
        else:
            if filename in STOCK_FILES or filename in MATERIAL_FILES or filename in PICKING_FILES:
                if not is_file_enabled(filename):
                    return
            elif _is_configured_material_cutting_csv(filepath) and not is_file_enabled(
                MATERIAL_CUTTING_CSV_BASENAME
            ):
                logger.debug("材料切断CSV 監視は無効のためスキップ: %s", filename)
                return
            if path_key in self.in_queue_csv_paths:
                logger.debug("CSV キューに同一路径が既にあるためスキップ: %s", filename)
                return
            target_queue = self.csv_task_queue
            if target_queue is None:
                return
        self.last_processed[path_key] = now
        if is_inspection:
            queue_label = "検査Excel"
        elif is_welding:
            queue_label = "溶接Excel"
        elif is_cutting:
            queue_label = "切断Excel"
        elif is_forming:
            queue_label = "成形Excel"
        elif is_chamfering:
            queue_label = "面取Excel"
        elif is_plating:
            queue_label = "メッキExcel"
        elif is_excel_plan:
            queue_label = "Excel"
        else:
            queue_label = "CSV"
        if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_plating or is_excel_plan:
            self.in_queue_excel_filenames.add(filename)
        else:
            self.in_queue_csv_paths.add(path_key)
        logger.info("ファイル変更を検知、%s キューに投入: %s", queue_label, filename)
        try:
            target_queue.put((filepath, filename))
        except Exception as e:
            if is_inspection or is_welding or is_cutting or is_forming or is_chamfering or is_plating or is_excel_plan:
                self.in_queue_excel_filenames.discard(filename)
            else:
                self.in_queue_csv_paths.discard(path_key)
            logger.warning("キュー投入失敗 %s: %s", filename, e)
