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


def is_csv_watch_task(filename: str, filepath: str) -> bool:
    """在庫/材料/ピッキング/材料切断 CSV か（Excel 専用キューではなく CSV キューへ）"""
    if filename in STOCK_FILES or filename in MATERIAL_FILES or filename in PICKING_FILES:
        return True
    return _is_configured_material_cutting_csv(filepath)


def is_excel_watch_task(filename: str) -> bool:
    return is_excel_target_file(filename) or is_inspection_excel_file(filename)


class UnifiedHandler(FileSystemEventHandler):
    """検知とキュー投入のみ。CSV と Excel は別キューへ投入しワーカー競合を避ける。"""

    def __init__(
        self,
        csv_task_queue=None,
        excel_task_queue=None,
        excel_watcher_enabled=True,
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
        is_excel = is_excel_watch_task(filename)
        is_csv = is_csv_watch_task(filename, filepath)
        if not is_excel and not is_csv:
            logger.debug("監視対象外のため無視: %s", filename)
            return
        if is_excel:
            if not self.excel_watcher_enabled:
                logger.debug("Excel 監視は無効のためスキップ: %s", filename)
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
        queue_label = "Excel" if is_excel else "CSV"
        if is_excel:
            self.in_queue_excel_filenames.add(filename)
        else:
            self.in_queue_csv_paths.add(path_key)
        logger.info("ファイル変更を検知、%s キューに投入: %s", queue_label, filename)
        try:
            target_queue.put((filepath, filename))
        except Exception as e:
            if is_excel:
                self.in_queue_excel_filenames.discard(filename)
            else:
                self.in_queue_csv_paths.discard(path_key)
            logger.warning("キュー投入失敗 %s: %s", filename, e)
