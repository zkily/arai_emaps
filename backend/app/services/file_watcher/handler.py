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
from app.services.file_watcher.excel_processor import EXCEL_FILES, is_excel_target_file
from app.services.file_watcher.inspection_excel_processor import is_inspection_excel_file
from app.services.file_watcher.enabled_config import is_file_enabled

logger = logging.getLogger(__name__)


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


class UnifiedHandler(FileSystemEventHandler):
    """検知とキュー投入のみ担当。実際の処理は run のワーカーが実行（ポーリングをブロックしない）"""

    def __init__(self, task_queue=None, excel_watcher_enabled=True, in_queue_filenames=None):
        self.task_queue = task_queue  # queue.Queue of (filepath, filename)
        self.excel_watcher_enabled = excel_watcher_enabled  # DISABLE_EXCEL_WATCHER=true のとき False
        self.in_queue_filenames = in_queue_filenames if in_queue_filenames is not None else set()  # キュー内ファイル名（重複入隊防止）
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
        is_cutting_csv = _is_configured_material_cutting_csv(filepath)
        if (
            not is_excel_target_file(filename)
            and not is_inspection_excel_file(filename)
            and filename not in STOCK_FILES
            and filename not in MATERIAL_FILES
            and filename not in PICKING_FILES
            and not is_cutting_csv
        ):
            logger.debug("監視対象外のため無視: %s", filename)
            return
        if is_excel_target_file(filename) or is_inspection_excel_file(filename):
            if not self.excel_watcher_enabled:
                logger.debug("Excel 監視は無効のためスキップ: %s", filename)
                return
            if filename in self.in_queue_filenames:
                logger.debug("キューに同名ファイルが既にあるためスキップ: %s", filename)
                return
        if is_cutting_csv and not is_file_enabled(MATERIAL_CUTTING_CSV_BASENAME):
            logger.debug("材料切断CSV 監視は無効のためスキップ: %s", filename)
            return
        if filename in STOCK_FILES or filename in MATERIAL_FILES or filename in PICKING_FILES:
            if not is_file_enabled(filename):
                return
        if self.task_queue is None:
            return
        self.last_processed[path_key] = now
        if is_excel_target_file(filename) or is_inspection_excel_file(filename):
            self.in_queue_filenames.add(filename)
        logger.info("ファイル変更を検知、キューに投入: %s", filename)
        try:
            self.task_queue.put((filepath, filename))
        except Exception as e:
            if is_excel_target_file(filename) or is_inspection_excel_file(filename):
                self.in_queue_filenames.discard(filename)
            logger.warning("キュー投入失敗 %s: %s", filename, e)
