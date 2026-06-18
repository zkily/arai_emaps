# coding: utf-8
"""ファイル監視の起動：PollingObserver + CSV/Excel 別キュー・別ワーカー（相互にブロックしない）"""
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
    MaterialCuttingCsvService,
    STOCK_FILES,
    MATERIAL_FILES,
    PICKING_FILES,
    MATERIAL_CUTTING_CSV_BASENAME,
    run_picking_sync_and_refresh_matched,
)
from app.services.file_watcher.excel_processor import (
    ExcelProcessor,
    EXCEL_FILES,
    is_excel_target_file,
)
from app.services.file_watcher.inspection_excel_processor import (
    InspectionExcelProcessor,
    is_inspection_excel_file,
)
from app.services.file_watcher.inspection_management_sync import sync_inspection_excel_to_management
from app.services.file_watcher.welding_excel_processor import (
    is_welding_excel_file,
)
from app.services.file_watcher.welding_management_sync import sync_welding_excel_to_management
from app.services.file_watcher.utils import wait_for_file_stable
from app.services.file_watcher.enabled_config import (
    is_file_enabled,
    is_excel_watcher_enabled,
    is_inspection_excel_watcher_enabled,
    is_inspection_management_sync_enabled,
    is_welding_excel_watcher_enabled,
    is_welding_management_sync_enabled,
)

logger = logging.getLogger(__name__)

EXCEL_WORKER_COUNT = max(1, getattr(settings, "FILE_WATCH_EXCEL_WORKERS", 3))
CSV_WORKER_COUNT = max(1, getattr(settings, "FILE_WATCH_CSV_WORKERS", 2))
POLL_INTERVAL = getattr(settings, "FILE_WATCH_POLL_INTERVAL", 1.0)  # ネットワークパスは 1 秒ポーリング推奨
STABILITY_POLL_INTERVAL = 0.5  # ファイル安定検知の間隔（秒）
STABILITY_COUNT = 3  # 連続 N 回サイズ不変で安定とみなす


def _inspection_mgmt_sync_enabled() -> bool:
    env = os.environ.get("FILE_WATCH_INSPECTION_MGMT_SYNC_ENABLED", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "FILE_WATCH_INSPECTION_MGMT_SYNC_ENABLED", True)) and is_inspection_management_sync_enabled()


def _welding_mgmt_sync_enabled() -> bool:
    env = os.environ.get("FILE_WATCH_WELDING_MGMT_SYNC_ENABLED", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "FILE_WATCH_WELDING_MGMT_SYNC_ENABLED", True)) and is_welding_management_sync_enabled()


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


def _get_inspection_excel_path():
    """検査管理指標 Excel のフルパス（.env / settings）"""
    raw = (
        os.environ.get("FILE_WATCH_INSPECTION_EXCEL_PATH")
        or getattr(settings, "FILE_WATCH_INSPECTION_EXCEL_PATH", "")
        or ""
    )
    return _norm_path(raw)


def _enqueue_inspection_excel(file_path, task_queue, in_queue_filenames, reason: str = "") -> bool:
    """検査管理指標 Excel を Excel キューへ投入（起動時・手動トリガー用）"""
    if not file_path:
        return False
    filename = os.path.basename(file_path)
    if not is_inspection_excel_file(filename):
        logger.warning(
            "検査管理指標: ファイル名がパターンと一致しません（生産管理指標(YYYY年度-検査).xlsx）: %s",
            filename,
        )
        return False
    if not os.path.isfile(file_path):
        logger.debug("検査管理指標 Excel は未存在のためキュー投入をスキップ: %s", file_path)
        return False
    if filename in in_queue_filenames:
        return False
    in_queue_filenames.add(filename)
    try:
        task_queue.put((file_path, filename))
        suffix = f" ({reason})" if reason else ""
        logger.info("検査管理指標 Excel をキュー投入%s: %s", suffix, filename)
        return True
    except Exception:
        in_queue_filenames.discard(filename)
        return False


def _inspection_excel_polling_loop(file_path, task_queue, poll_interval, stop_event, in_queue_filenames):
    """検査管理指標 Excel の mtime ポーリング（ネットワークドライブ対応）"""
    last_mtime = None
    filename = os.path.basename(file_path)
    missing_logged = False
    while not stop_event.is_set():
        try:
            stop_event.wait(timeout=poll_interval)
            if stop_event.is_set():
                break
            if not os.path.isfile(file_path):
                if not missing_logged:
                    logger.warning("検査管理指標 Excel が見つかりません（到達可能になるまで待機）: %s", file_path)
                    missing_logged = True
                continue
            if missing_logged:
                logger.info("検査管理指標 Excel を検出しました: %s", file_path)
                missing_logged = False
            if filename in in_queue_filenames:
                continue
            try:
                mtime = os.path.getmtime(file_path)
            except OSError:
                continue
            if last_mtime is not None and mtime > last_mtime:
                logger.info("検査管理指標 Excel 変更検知: %s", filename)
                _enqueue_inspection_excel(file_path, task_queue, in_queue_filenames, reason="mtime変更")
            last_mtime = mtime
        except Exception as e:
            logger.debug("検査管理指標ポーリング異常: %s", e)


def _get_welding_excel_path():
    """溶接管理指標 Excel のフルパス（.env / settings）"""
    raw = (
        os.environ.get("FILE_WATCH_WELDING_EXCEL_PATH")
        or getattr(settings, "FILE_WATCH_WELDING_EXCEL_PATH", "")
        or ""
    )
    return _norm_path(raw)


def _enqueue_welding_excel(file_path, task_queue, in_queue_filenames, reason: str = "") -> bool:
    """溶接管理指標 Excel を Excel キューへ投入（起動時・手動トリガー用）"""
    if not file_path:
        return False
    filename = os.path.basename(file_path)
    if not is_welding_excel_file(filename):
        logger.warning(
            "溶接管理指標: ファイル名がパターンと一致しません（生産管理指標(YYYY年度-溶接).xlsx）: %s",
            filename,
        )
        return False
    if not os.path.isfile(file_path):
        logger.debug("溶接管理指標 Excel は未存在のためキュー投入をスキップ: %s", file_path)
        return False
    if filename in in_queue_filenames:
        return False
    in_queue_filenames.add(filename)
    try:
        task_queue.put((file_path, filename))
        suffix = f" ({reason})" if reason else ""
        logger.info("溶接管理指標 Excel をキュー投入%s: %s", suffix, filename)
        return True
    except Exception:
        in_queue_filenames.discard(filename)
        return False


def _welding_excel_polling_loop(file_path, task_queue, poll_interval, stop_event, in_queue_filenames):
    """溶接管理指標 Excel の mtime ポーリング（ネットワークドライブ対応）"""
    last_mtime = None
    filename = os.path.basename(file_path)
    missing_logged = False
    while not stop_event.is_set():
        try:
            stop_event.wait(timeout=poll_interval)
            if stop_event.is_set():
                break
            if not os.path.isfile(file_path):
                if not missing_logged:
                    logger.warning("溶接管理指標 Excel が見つかりません（到達可能になるまで待機）: %s", file_path)
                    missing_logged = True
                continue
            if missing_logged:
                logger.info("溶接管理指標 Excel を検出しました: %s", file_path)
                missing_logged = False
            if filename in in_queue_filenames:
                continue
            try:
                mtime = os.path.getmtime(file_path)
            except OSError:
                continue
            if last_mtime is not None and mtime > last_mtime:
                logger.info("溶接管理指標 Excel 変更検知: %s", filename)
                _enqueue_welding_excel(file_path, task_queue, in_queue_filenames, reason="mtime変更")
            last_mtime = mtime
        except Exception as e:
            logger.debug("溶接管理指標ポーリング異常: %s", e)


def _material_csv_polling_loop(task_queue, poll_interval, stop_event):
    """材料受入 CSV の実パス（.env 解決済み）を mtime ポーリングし、変更時にキュー投入"""
    last_mtime = {}
    while not stop_event.is_set():
        stop_event.wait(timeout=poll_interval)
        if stop_event.is_set():
            break
        entries = settings.get_material_receiving_csv_entries()
        for path, name in entries:
            if not is_file_enabled(name):
                continue
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
                logger.info("材料 CSV mtime 変更を検知、キュー投入: %s (%s)", name, path)
                try:
                    task_queue.put((path, name))
                except Exception as e:
                    logger.warning("材料 CSV キュー投入失敗 %s: %s", name, e)


def _material_cutting_csv_polling_loop(task_queue, poll_interval, stop_event):
    """MATERIAL_CUTTING_CSV_PATH の mtime をポーリングし、変更時にキュー投入（ネットワーク共有向け）"""
    path = settings.get_material_cutting_csv_path()
    last_mtime = None
    filename = os.path.basename(path) or MATERIAL_CUTTING_CSV_BASENAME
    while not stop_event.is_set():
        stop_event.wait(timeout=poll_interval)
        if stop_event.is_set():
            break
        if not is_file_enabled(MATERIAL_CUTTING_CSV_BASENAME):
            continue
        if not os.path.isfile(path):
            continue
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        if last_mtime is not None and mtime > last_mtime:
            logger.info("材料切断CSV mtime 変更を検知、キュー投入: %s (%s)", filename, path)
            try:
                task_queue.put((path, filename))
            except Exception as e:
                logger.warning("材料切断CSV キュー投入失敗: %s", e)
        last_mtime = mtime


def _csv_worker(csv_task_queue, in_queue_csv_paths):
    """在庫/材料/ピッキング CSV 専用ワーカー（Excel キューと独立）"""
    stock_svc = StockService()
    material_svc = MaterialService()
    cutting_csv_svc = MaterialCuttingCsvService()
    while True:
        try:
            item = csv_task_queue.get()
        except Exception:
            break
        filepath, filename = item if isinstance(item, (list, tuple)) and len(item) >= 2 else (None, None)
        path_key = os.path.normpath(os.path.abspath(filepath)) if filepath else ""
        try:
            if filepath is None or filename is None:
                continue
            in_queue_csv_paths.discard(path_key)
            wait_for_file_stable(
                filepath,
                timeout=10,
                poll_interval=STABILITY_POLL_INTERVAL,
                stable_count=STABILITY_COUNT,
            )
            if not os.path.isfile(filepath):
                logger.warning("ファイルが存在しないためスキップ: %s", filename)
                continue
            logger.info("[CSV] 処理開始: %s", filename)
            if filename in PICKING_FILES:
                if is_file_enabled(filename):
                    run_picking_sync_and_refresh_matched(filepath, filename)
                else:
                    logger.debug("ピッキングファイル監視は無効のためスキップ: %s", filename)
            elif filename in STOCK_FILES:
                if is_file_enabled(filename):
                    stock_svc.sync(filepath, filename)
                else:
                    logger.debug("在庫ファイル監視は無効のためスキップ: %s", filename)
            elif os.path.normpath(filepath) == os.path.normpath(
                settings.get_material_cutting_csv_path()
            ):
                if is_file_enabled(MATERIAL_CUTTING_CSV_BASENAME):
                    cutting_csv_svc.sync(filepath, filename)
                else:
                    logger.debug("材料切断CSV 監視は無効のためスキップ: %s", filename)
            elif filename in MATERIAL_FILES:
                if is_file_enabled(filename):
                    material_svc.sync(filepath, filename)
                else:
                    logger.debug("材料ファイル監視は無効のためスキップ: %s", filename)
            else:
                logger.warning("[CSV] 未対応ファイルのためスキップ: %s", filename)
        except Exception as e:
            logger.error("[CSV] 処理失敗 %s: %s", filename, e, exc_info=True)
        finally:
            try:
                csv_task_queue.task_done()
            except Exception:
                pass


def _excel_worker(excel_task_queue, in_queue_excel_filenames, processing_excel, excel_lock):
    """生産計画 Excel 専用ワーカー；同一 Excel は 1 ワーカーのみ処理"""
    excel_processor = ExcelProcessor()
    inspection_processor = InspectionExcelProcessor()
    while True:
        try:
            item = excel_task_queue.get()
        except Exception:
            break
        filepath, filename = item if isinstance(item, (list, tuple)) and len(item) >= 2 else (None, None)
        try:
            if filepath is None or filename is None:
                continue
            in_queue_excel_filenames.discard(filename)
            with excel_lock:
                if filename in processing_excel:
                    logger.debug("Excel は他ワーカーで処理中のためスキップ: %s", filename)
                    try:
                        excel_task_queue.task_done()
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
            logger.info("[Excel] 処理開始: %s", filename)
            if is_inspection_excel_file(filename):
                inspection_processor.process_file(filepath)
                if _inspection_mgmt_sync_enabled():
                    mgmt_result = sync_inspection_excel_to_management(filepath)
                    logger.info(
                        "[Excel] inspection_management 同期: inserted=%s dup_skip=%s parsed=%s (%s)",
                        mgmt_result.inserted,
                        mgmt_result.skipped_duplicate,
                        mgmt_result.parsed,
                        filename,
                    )
                    if mgmt_result.unmapped_inspectors:
                        logger.warning(
                            "[Excel] 作業者未匹配 users.full_name: %s",
                            ", ".join(
                                f"{n}({c})"
                                for n, c in sorted(
                                    mgmt_result.unmapped_inspectors.items(),
                                    key=lambda x: -x[1],
                                )[:10]
                            ),
                        )
            elif is_welding_excel_file(filename):
                if _welding_mgmt_sync_enabled():
                    mgmt_result = sync_welding_excel_to_management(filepath)
                    logger.info(
                        "[Excel] welding_management 同期: inserted=%s dup_skip=%s parsed=%s (%s)",
                        mgmt_result.inserted,
                        mgmt_result.skipped_duplicate,
                        mgmt_result.parsed,
                        filename,
                    )
                    if mgmt_result.unmapped_operators:
                        logger.warning(
                            "[Excel] 溶接作業者未匹配 users.full_name: %s",
                            ", ".join(
                                f"{n}({c})"
                                for n, c in sorted(
                                    mgmt_result.unmapped_operators.items(),
                                    key=lambda x: -x[1],
                                )[:10]
                            ),
                        )
            elif is_excel_target_file(filename):
                excel_processor.process_file(filepath)
            else:
                logger.warning("[Excel] 未対応ファイルのためスキップ: %s", filename)
        except Exception as e:
            logger.error("[Excel] 処理失敗 %s: %s", filename, e, exc_info=True)
        finally:
            if is_excel_target_file(filename) or is_inspection_excel_file(filename) or is_welding_excel_file(filename):
                processing_excel.discard(filename)
            try:
                excel_task_queue.task_done()
            except Exception:
                pass


def run_watcher():
    """ファイル監視サービスを起動：CSV 受信ディレクトリと生産計画 Excel ディレクトリを同時監視（別々に指定可）"""
    csv_path, excel_path = _get_watch_paths()
    if not csv_path:
        entries_fb = settings.get_material_receiving_csv_entries()
        if entries_fb:
            parent = os.path.normpath(os.path.dirname(entries_fb[0][0]))
            if parent and os.path.isdir(parent):
                csv_path = parent
                logger.info(
                    "FILE_WATCH_BASE_PATH 未設定のため、材料受入 CSV の親フォルダを監視ルートに使用: %s",
                    csv_path,
                )
    if not csv_path:
        logger.error(
            "❌ FILE_WATCH_BASE_PATH 未配置です。.env に設定するか、MATERIAL_RECEIVING_CSV_PATHS で材料 CSV のフルパスを指定してください。"
        )
        return
    if not os.path.exists(csv_path):
        logger.error("❌ CSV 監視パスが存在しません: %s", csv_path)
        return
    if excel_path and excel_path != csv_path and not os.path.exists(excel_path):
        logger.error("❌ Excel 監視パスが存在しません: %s", excel_path)
        return
    inspection_excel_path = _get_inspection_excel_path()
    welding_excel_path = _get_welding_excel_path()
    excel_watcher_enabled = (os.environ.get("DISABLE_EXCEL_WATCHER", "").strip().lower() != "true") and is_excel_watcher_enabled()
    inspection_watcher_enabled = (
        os.environ.get("DISABLE_INSPECTION_EXCEL_WATCHER", "").strip().lower() != "true"
    ) and is_inspection_excel_watcher_enabled()
    welding_watcher_enabled = (
        os.environ.get("DISABLE_WELDING_EXCEL_WATCHER", "").strip().lower() != "true"
    ) and is_welding_excel_watcher_enabled()
    excel_queue_needed = excel_watcher_enabled or (
        inspection_watcher_enabled and bool(inspection_excel_path)
    ) or (welding_watcher_enabled and bool(welding_excel_path))
    logger.info("🚀 ファイル監視サービスを起動しています...")
    logger.info("📂 CSV 受信監視パス: %s", csv_path)
    if excel_path and excel_path != csv_path:
        logger.info("📂 Excel 計画監視パス: %s", excel_path)
    else:
        logger.info("📂 Excel 計画与 CSV 共用路径")
    if inspection_excel_path:
        logger.info("📂 検査管理指標 Excel パス: %s", inspection_excel_path)
        if _inspection_mgmt_sync_enabled():
            logger.info("📋 検査管理指標 → inspection_management 增量同期: 有効")
        else:
            logger.info("📋 検査管理指標 → inspection_management 增量同期: 無効")
    if welding_excel_path:
        logger.info("📂 溶接管理指標 Excel パス: %s", welding_excel_path)
        if _welding_mgmt_sync_enabled():
            logger.info("📋 溶接管理指標 → welding_management 增量同期: 有効")
        else:
            logger.info("📋 溶接管理指標 → welding_management 增量同期: 無効")
    logger.info(
        "📊 ポーリング間隔: %.1f 秒、CSV ワーカー: %s、Excel ワーカー: %s",
        POLL_INTERVAL,
        CSV_WORKER_COUNT,
        EXCEL_WORKER_COUNT if excel_queue_needed else 0,
    )
    cutting_csv_display = os.path.basename(settings.get_material_cutting_csv_path()) or MATERIAL_CUTTING_CSV_BASENAME
    logger.info(
        "📑 監視対象: 在庫 %s 件、材料 %s 件、材料切断 %s、ピッキング %s 件、Excel 計画 %s 件、検査管理指標 %s、溶接管理指標 %s",
        len(STOCK_FILES),
        len(MATERIAL_FILES),
        cutting_csv_display,
        len(PICKING_FILES),
        len(EXCEL_FILES),
        "有効" if (inspection_watcher_enabled and inspection_excel_path) else "未設定/無効",
        "有効" if (welding_watcher_enabled and welding_excel_path) else "未設定/無効",
    )
    if not excel_watcher_enabled:
        logger.info("📌 Excel 計画監視は無効です（環境変数またはシステム設定）")
    if inspection_excel_path and not inspection_watcher_enabled:
        logger.info("📌 検査管理指標 Excel 監視は無効です（環境変数またはシステム設定）")
    if welding_excel_path and not welding_watcher_enabled:
        logger.info("📌 溶接管理指標 Excel 監視は無効です（環境変数またはシステム設定）")
    if excel_watcher_enabled and excel_path:
        _scan_excel_files_at_startup(excel_path, None)

    csv_task_queue = queue.Queue()
    excel_task_queue = queue.Queue()
    in_queue_excel_filenames = set()
    in_queue_csv_paths = set()
    processing_excel = set()
    excel_lock = threading.Lock()
    for i in range(CSV_WORKER_COUNT):
        threading.Thread(
            target=_csv_worker,
            args=(csv_task_queue, in_queue_csv_paths),
            daemon=True,
            name=f"FileWatcher-CsvWorker-{i + 1}",
        ).start()
    if excel_queue_needed:
        for i in range(EXCEL_WORKER_COUNT):
            threading.Thread(
                target=_excel_worker,
                args=(
                    excel_task_queue,
                    in_queue_excel_filenames,
                    processing_excel,
                    excel_lock,
                ),
                daemon=True,
                name=f"FileWatcher-ExcelWorker-{i + 1}",
            ).start()
    logger.info("✅ CSV / Excel 別キュー・別ワーカーで起動（相互ブロックなし）")

    handler = UnifiedHandler(
        csv_task_queue=csv_task_queue,
        excel_task_queue=excel_task_queue,
        excel_watcher_enabled=excel_watcher_enabled,
        inspection_watcher_enabled=inspection_watcher_enabled,
        inspection_excel_path=inspection_excel_path,
        welding_watcher_enabled=welding_watcher_enabled,
        welding_excel_path=welding_excel_path,
        in_queue_excel_filenames=in_queue_excel_filenames,
        in_queue_csv_paths=in_queue_csv_paths,
    )
    observer = PollingObserver(timeout=POLL_INTERVAL)
    observer.schedule(handler, csv_path, recursive=False)
    if excel_path and excel_path != csv_path:
        observer.schedule(handler, excel_path, recursive=False)
    if inspection_excel_path:
        inspection_dir = os.path.dirname(inspection_excel_path)
        if inspection_dir and inspection_dir not in (csv_path, excel_path):
            try:
                observer.schedule(handler, inspection_dir, recursive=False)
            except Exception as e:
                logger.warning("検査管理指標ディレクトリの watchdog 登録失敗（ポーリングで補完）: %s", e)
    if welding_excel_path:
        welding_dir = os.path.dirname(welding_excel_path)
        if welding_dir and welding_dir not in (csv_path, excel_path):
            try:
                observer.schedule(handler, welding_dir, recursive=False)
            except Exception as e:
                logger.warning("溶接管理指標ディレクトリの watchdog 登録失敗（ポーリングで補完）: %s", e)
    watched_roots = {os.path.normpath(csv_path)}
    if excel_path:
        watched_roots.add(os.path.normpath(excel_path))
    if inspection_excel_path:
        idir = os.path.dirname(inspection_excel_path)
        if idir:
            watched_roots.add(os.path.normpath(idir))
    if welding_excel_path:
        wdir = os.path.dirname(welding_excel_path)
        if wdir:
            watched_roots.add(os.path.normpath(wdir))
    for fullpath, _bn in settings.get_material_receiving_csv_entries():
        parent = os.path.normpath(os.path.dirname(fullpath))
        if not parent or parent in watched_roots:
            continue
        if not os.path.isdir(parent):
            continue
        try:
            observer.schedule(handler, parent, recursive=False)
            watched_roots.add(parent)
            logger.info("材料受入 CSV 用にディレクトリを追加監視: %s", parent)
        except Exception as e:
            logger.warning("材料追加監視の登録に失敗 %s: %s", parent, e)
    cutting_full = os.path.normpath(settings.get_material_cutting_csv_path())
    cutting_parent = os.path.normpath(os.path.dirname(cutting_full))
    if (
        cutting_parent
        and cutting_parent not in watched_roots
        and os.path.isdir(cutting_parent)
    ):
        try:
            observer.schedule(handler, cutting_parent, recursive=False)
            watched_roots.add(cutting_parent)
            logger.info("材料切断CSV 用にディレクトリを追加監視: %s", cutting_parent)
        except Exception as e:
            logger.warning("材料切断CSV ディレクトリの watchdog 登録失敗（mtime ポーリングで補完）: %s", e)
    observer.start()

    stop_polling = threading.Event()
    material_poll_thread = threading.Thread(
        target=_material_csv_polling_loop,
        args=(csv_task_queue, POLL_INTERVAL, stop_polling),
        daemon=True,
        name="MaterialCsvMtimePoll",
    )
    material_poll_thread.start()
    logger.info(
        "✅ 材料受入 CSV mtime ポーリング開始（対象 %s 種・間隔 %.1fs）",
        len(MATERIAL_FILES),
        POLL_INTERVAL,
    )
    cutting_poll_thread = threading.Thread(
        target=_material_cutting_csv_polling_loop,
        args=(csv_task_queue, POLL_INTERVAL, stop_polling),
        daemon=True,
        name="MaterialCuttingCsvMtimePoll",
    )
    cutting_poll_thread.start()
    logger.info(
        "✅ 材料切断CSV mtime ポーリング開始: %s（間隔 %.1fs）",
        cutting_csv_display,
        POLL_INTERVAL,
    )
    if excel_watcher_enabled and excel_path:
        excel_poll_thread = threading.Thread(
            target=_excel_polling_loop,
            args=(
                excel_path,
                excel_task_queue,
                POLL_INTERVAL,
                stop_polling,
                in_queue_excel_filenames,
            ),
            daemon=True,
        )
        excel_poll_thread.start()
    if inspection_watcher_enabled and inspection_excel_path:
        inspection_poll_thread = threading.Thread(
            target=_inspection_excel_polling_loop,
            args=(
                inspection_excel_path,
                excel_task_queue,
                POLL_INTERVAL,
                stop_polling,
                in_queue_excel_filenames,
            ),
            daemon=True,
            name="InspectionExcelMtimePoll",
        )
        inspection_poll_thread.start()
        logger.info("✅ 検査管理指標 Excel ポーリング開始: %s", os.path.basename(inspection_excel_path))
        if os.path.isfile(inspection_excel_path):
            _enqueue_inspection_excel(
                inspection_excel_path,
                excel_task_queue,
                in_queue_excel_filenames,
                reason="起動時",
            )
        else:
            logger.warning(
                "⚠️ 検査管理指標 Excel は起動時に未検出（ネットワーク復旧後に自動監視）: %s",
                inspection_excel_path,
            )
    if welding_watcher_enabled and welding_excel_path:
        welding_poll_thread = threading.Thread(
            target=_welding_excel_polling_loop,
            args=(
                welding_excel_path,
                excel_task_queue,
                POLL_INTERVAL,
                stop_polling,
                in_queue_excel_filenames,
            ),
            daemon=True,
            name="WeldingExcelMtimePoll",
        )
        welding_poll_thread.start()
        logger.info("✅ 溶接管理指標 Excel ポーリング開始: %s", os.path.basename(welding_excel_path))
        if os.path.isfile(welding_excel_path):
            _enqueue_welding_excel(
                welding_excel_path,
                excel_task_queue,
                in_queue_excel_filenames,
                reason="起動時",
            )
        else:
            logger.warning(
                "⚠️ 溶接管理指標 Excel は起動時に未検出（ネットワーク復旧後に自動監視）: %s",
                welding_excel_path,
            )
    if excel_watcher_enabled and excel_path:
        logger.info("✅ ポーリング開始（Watchdog + Excel mtime）、ファイル変更を待機中...")
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


_watcher_bg_lock = threading.Lock()
_file_watcher_bg_started = False


def start_file_watcher_background() -> None:
    """
    FastAPI 起動時用：ファイル監視をデーモンスレッドで開始する。
    settings.FILE_WATCH_START_WITH_API=True かつ FILE_WATCH_BASE_PATH が有効なときのみ main から呼ぶ。
    """
    global _file_watcher_bg_started
    with _watcher_bg_lock:
        if _file_watcher_bg_started:
            logger.info("ファイル監視バックグラウンドは既に起動済みのためスキップします")
            return
        csv_path, _ = _get_watch_paths()
        if not csv_path:
            entries_fb = settings.get_material_receiving_csv_entries()
            if entries_fb:
                parent = os.path.normpath(os.path.dirname(entries_fb[0][0]))
                if parent and os.path.isdir(parent):
                    csv_path = parent
        if not csv_path:
            logger.warning(
                "FILE_WATCH_START_WITH_API=true ですが FILE_WATCH_BASE_PATH（または MATERIAL_RECEIVING_CSV_PATHS）が未設定のため監視を開始しません"
            )
            return
        if not os.path.exists(csv_path):
            logger.warning("CSV 監視ルートが存在しません: %s", csv_path)
            return
        _file_watcher_bg_started = True
        t = threading.Thread(
            target=run_watcher,
            name="SmartEMAP-FileWatcher",
            daemon=True,
        )
        t.start()
        logger.info("ファイル監視を API プロセス内のバックグラウンドスレッドで開始しました")
