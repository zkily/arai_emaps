# coding: utf-8
"""ファイル監視の起動：PollingObserver + 共通タスクキュー + ワーカースレッド（ポーリングをブロックしない）"""
import os
import time
import logging
import queue
import threading
from watchdog.observers.polling import PollingObserver
from app.core.config import settings
from app.services.file_watcher.handler import UnifiedHandler
from app.services.file_watcher.sync_services import (
    StockService,
    MaterialService,
    PickingLogService,
    STOCK_FILES,
    MATERIAL_FILES,
    PICKING_FILES,
)
from app.services.file_watcher.excel_processor import (
    ExcelProcessor,
    EXCEL_FILES,
    is_excel_target_file,
)
from app.services.file_watcher.utils import wait_for_file_stable
from app.services.file_watcher.enabled_config import is_file_enabled, is_excel_watcher_enabled

logger = logging.getLogger(__name__)

WORKER_COUNT = max(1, getattr(settings, "FILE_WATCH_EXCEL_WORKERS", 3))
POLL_INTERVAL = getattr(settings, "FILE_WATCH_POLL_INTERVAL", 1.0)  # ネットワークパスは 1 秒ポーリング推奨
STABILITY_POLL_INTERVAL = 0.5  # ファイル安定検知の間隔（秒）
STABILITY_COUNT = 3  # 連続 N 回サイズ不変で安定とみなす


def _norm_path(value):
    """取环境变量或 settings 中的路径并规范化"""
    s = (value or "").strip()
    return os.path.normpath(s) if s else ""


def _get_watch_paths():
    """
    (csv_path, excel_path) を返す。
    CSV: FILE_WATCH_BASE_PATH（受信 CSV/材料）。
    Excel: FILE_WATCH_EXCEL_BASE_PATH。未設定なら CSV と同じ。
    """
    csv_path = _norm_path(os.environ.get("FILE_WATCH_BASE_PATH") or getattr(settings, "FILE_WATCH_BASE_PATH", None))
    excel_path = _norm_path(os.environ.get("FILE_WATCH_EXCEL_BASE_PATH") or getattr(settings, "FILE_WATCH_EXCEL_BASE_PATH", None))
    if not excel_path:
        excel_path = csv_path
    return csv_path, excel_path


def _scan_excel_files_at_startup(base_path, task_queue):
    """起動時にディレクトリをスキャンし、監視対象の Excel ファイルを一覧（パス・ファイル名の確認用）"""
    try:
        names = os.listdir(base_path)
    except OSError as e:
        logger.warning("起動時にディレクトリを一覧できません %s: %s", base_path, e)
        return
    found = [n for n in names if is_excel_target_file(n)]
    if found:
        logger.info("📑 ディレクトリ内の Excel 計画ファイル %s 件: %s", len(found), ", ".join(sorted(found)[:5]) + (" ..." if len(found) > 5 else ""))
    else:
        xlsm = [n for n in names if n.endswith(".xlsm")]
        logger.warning("📑 24 種類の計画ファイルは見つかりませんでした。ディレクトリ内の .xlsm: %s", xlsm[:10] if xlsm else "なし")


def _excel_polling_loop(base_path, task_queue, poll_interval, stop_event, in_queue_filenames):
    """Excel 用ポーリングスレッド：mtime で変更検知（ネットワークドライブで watchdog が反応しない場合用）；キュー重複防止"""
    last_mtime = {}
    while not stop_event.is_set():
        try:
            stop_event.wait(timeout=poll_interval)
            if stop_event.is_set():
                break
            try:
                names = os.listdir(base_path)
            except OSError:
                continue
            for name in names:
                if not is_excel_target_file(name):
                    continue
                if name in in_queue_filenames:
                    continue
                path = os.path.join(base_path, name)
                if not os.path.isfile(path):
                    continue
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                key = os.path.normpath(path)
                prev = last_mtime.get(key)
                last_mtime[key] = mtime
                if prev is not None and mtime > prev:
                    logger.info("Excel 轮询检测到变更，已入队: %s", name)
                    in_queue_filenames.add(name)
                    try:
                        task_queue.put((path, name))
                    except Exception:
                        in_queue_filenames.discard(name)
        except Exception as e:
            logger.debug("Excel 轮询异常: %s", e)


def _file_worker(task_queue, in_queue_filenames, processing_excel, excel_lock):
    """ワーカー：キューから (filepath, filename) を取得し、ファイル安定後に種別で処理；同一 Excel は 1 ワーカーのみ"""
    stock_svc = StockService()
    material_svc = MaterialService()
    picking_svc = PickingLogService()
    excel_processor = ExcelProcessor()
    while True:
        try:
            item = task_queue.get()
        except Exception:
            break
        filepath, filename = item if isinstance(item, (list, tuple)) and len(item) >= 2 else (None, None)
        try:
            if filepath is None or filename is None:
                continue
            in_queue_filenames.discard(filename)
            if is_excel_target_file(filename):
                with excel_lock:
                    if filename in processing_excel:
                        logger.debug("Excel は他ワーカーで処理中のためスキップ: %s", filename)
                        try:
                            task_queue.task_done()
                        except Exception:
                            pass
                        continue
                    processing_excel.add(filename)
            wait_for_file_stable(
                filepath,
                timeout=10,
                poll_interval=STABILITY_POLL_INTERVAL,
                stable_count=STABILITY_COUNT,
            )
            if not os.path.isfile(filepath):
                logger.warning("ファイルが存在しないためスキップ: %s", filename)
                continue
            logger.info("処理開始: %s", filename)
            if is_excel_target_file(filename):
                excel_processor.process_file(filepath)
            elif filename in PICKING_FILES:
                if is_file_enabled(filename):
                    picking_svc.sync(filepath, filename)
                else:
                    logger.debug("ピッキングファイル監視は無効のためスキップ: %s", filename)
            elif filename in STOCK_FILES:
                if is_file_enabled(filename):
                    stock_svc.sync(filepath, filename)
                else:
                    logger.debug("在庫ファイル監視は無効のためスキップ: %s", filename)
            elif filename in MATERIAL_FILES:
                if is_file_enabled(filename):
                    material_svc.sync(filepath, filename)
                else:
                    logger.debug("材料ファイル監視は無効のためスキップ: %s", filename)
        except Exception as e:
            logger.error("処理失敗 %s: %s", filename, e, exc_info=True)
        finally:
            if is_excel_target_file(filename):
                processing_excel.discard(filename)
            try:
                task_queue.task_done()
            except Exception:
                pass


def run_watcher():
    """ファイル監視サービスを起動：CSV 受信ディレクトリと生産計画 Excel ディレクトリを同時監視（別々に指定可）"""
    csv_path, excel_path = _get_watch_paths()
    if not csv_path:
        logger.error("❌ FILE_WATCH_BASE_PATH 未配置，请在 .env 中设置（CSV 受信目录）")
        return
    if not os.path.exists(csv_path):
        logger.error("❌ CSV 監視パスが存在しません: %s", csv_path)
        return
    if excel_path and excel_path != csv_path and not os.path.exists(excel_path):
        logger.error("❌ Excel 監視パスが存在しません: %s", excel_path)
        return
    logger.info("🚀 ファイル監視サービスを起動しています...")
    logger.info("📂 CSV 受信監視パス: %s", csv_path)
    if excel_path and excel_path != csv_path:
        logger.info("📂 Excel 計画監視パス: %s", excel_path)
    else:
        logger.info("📂 Excel 計画与 CSV 共用路径")
    logger.info("📊 ポーリング間隔: %.1f 秒、ワーカー: %s 個", POLL_INTERVAL, WORKER_COUNT)
    logger.info("📑 監視対象: 在庫 %s 件、材料 %s 件、ピッキング %s 件、Excel 計画 %s 件", len(STOCK_FILES), len(MATERIAL_FILES), len(PICKING_FILES), len(EXCEL_FILES))
    excel_watcher_enabled = (os.environ.get("DISABLE_EXCEL_WATCHER", "").strip().lower() != "true") and is_excel_watcher_enabled()
    if not excel_watcher_enabled:
        logger.info("📌 Excel 監視は無効です（環境変数またはシステム設定）")
    if excel_watcher_enabled and excel_path:
        _scan_excel_files_at_startup(excel_path, None)

    task_queue = queue.Queue()
    in_queue_filenames = set()
    processing_excel = set()  # 処理中の Excel ファイル名（同一ファイルの複数ワーカーによるデッドロック防止）
    excel_lock = threading.Lock()
    for _ in range(WORKER_COUNT):
        t = threading.Thread(
            target=_file_worker,
            args=(task_queue, in_queue_filenames, processing_excel, excel_lock),
            daemon=True,
        )
        t.start()

    handler = UnifiedHandler(
        task_queue=task_queue,
        excel_watcher_enabled=excel_watcher_enabled,
        in_queue_filenames=in_queue_filenames,
    )
    observer = PollingObserver(timeout=POLL_INTERVAL)
    observer.schedule(handler, csv_path, recursive=False)
    if excel_path and excel_path != csv_path:
        observer.schedule(handler, excel_path, recursive=False)
    observer.start()

    stop_polling = threading.Event()
    if excel_watcher_enabled and excel_path:
        excel_poll_thread = threading.Thread(
            target=_excel_polling_loop,
            args=(excel_path, task_queue, POLL_INTERVAL, stop_polling, in_queue_filenames),
            daemon=True,
        )
        excel_poll_thread.start()
        logger.info("✅ ポーリング開始（2 ディレクトリ Watchdog + Excel mtime）、ファイル変更を待機中...")
    else:
        logger.info("✅ ポーリング開始、ファイル変更を待機中...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_polling.set()
        observer.stop()
        logger.info("🛑 服务停止")
    observer.join()
