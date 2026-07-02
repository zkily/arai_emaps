# -*- coding: utf-8
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "backend/app/services/file_watcher/run.py"
t = p.read_text(encoding="utf-8")

blocks = [
    (
        "from app.services.file_watcher.forming_production_indicator_sync import sync_forming_excel_to_indicator",
        """from app.services.file_watcher.forming_production_indicator_sync import sync_forming_excel_to_indicator
from app.services.file_watcher.chamfering_excel_processor import (
    is_chamfering_excel_file,
)
from app.services.file_watcher.chamfering_production_indicator_sync import sync_chamfering_excel_to_indicator""",
    ),
    (
        "    is_forming_indicator_sync_enabled,\n)",
        """    is_forming_indicator_sync_enabled,
    is_chamfering_excel_watcher_enabled,
    is_chamfering_indicator_sync_enabled,
)""",
    ),
    (
        """def _forming_indicator_sync_enabled() -> bool:
    env = os.environ.get("FILE_WATCH_FORMING_INDICATOR_SYNC_ENABLED", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "FILE_WATCH_FORMING_INDICATOR_SYNC_ENABLED", True)) and is_forming_indicator_sync_enabled()


def _norm_path(value):""",
        """def _forming_indicator_sync_enabled() -> bool:
    env = os.environ.get("FILE_WATCH_FORMING_INDICATOR_SYNC_ENABLED", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "FILE_WATCH_FORMING_INDICATOR_SYNC_ENABLED", True)) and is_forming_indicator_sync_enabled()


def _chamfering_indicator_sync_enabled() -> bool:
    env = os.environ.get("FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED", True)) and is_chamfering_indicator_sync_enabled()


def _norm_path(value):""",
    ),
    (
        """            logger.debug("成形管理指標ポーリング異常: %s", e)


def _material_csv_polling_loop(task_queue, poll_interval, stop_event):""",
        """            logger.debug("成形管理指標ポーリング異常: %s", e)


def _get_chamfering_excel_path():
    raw = (
        os.environ.get("FILE_WATCH_CHAMFERING_EXCEL_PATH")
        or getattr(settings, "FILE_WATCH_CHAMFERING_EXCEL_PATH", "")
        or ""
    )
    return _norm_path(raw)


def _enqueue_chamfering_excel(file_path, task_queue, in_queue_filenames, reason: str = "") -> bool:
    if not file_path:
        return False
    filename = os.path.basename(file_path)
    if not is_chamfering_excel_file(filename):
        logger.warning(
            "面取管理指標: ファイル名がパターンと一致しません（生産管理指標(YYYY年度-面取).xlsx）: %s",
            filename,
        )
        return False
    if not os.path.isfile(file_path):
        logger.debug("面取管理指標 Excel は未存在のためキュー投入をスキップ: %s", file_path)
        return False
    if filename in in_queue_filenames:
        return False
    in_queue_filenames.add(filename)
    try:
        task_queue.put((file_path, filename))
        suffix = f" ({reason})" if reason else ""
        logger.info("面取管理指標 Excel をキュー投入%s: %s", suffix, filename)
        return True
    except Exception:
        in_queue_filenames.discard(filename)
        return False


def _chamfering_excel_polling_loop(file_path, task_queue, poll_interval, stop_event, in_queue_filenames):
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
                    logger.warning("面取管理指標 Excel が見つかりません（到達可能になるまで待機）: %s", file_path)
                    missing_logged = True
                continue
            if missing_logged:
                logger.info("面取管理指標 Excel を検出しました: %s", file_path)
                missing_logged = False
            if filename in in_queue_filenames:
                continue
            try:
                mtime = os.path.getmtime(file_path)
            except OSError:
                continue
            if last_mtime is not None and mtime > last_mtime:
                logger.info("面取管理指標 Excel 変更検知: %s", filename)
                _enqueue_chamfering_excel(file_path, task_queue, in_queue_filenames, reason="mtime変更")
            last_mtime = mtime
        except Exception as e:
            logger.debug("面取管理指標ポーリング異常: %s", e)


def _material_csv_polling_loop(task_queue, poll_interval, stop_event):""",
    ),
    (
        """            elif is_forming_excel_file(filename):
                if _forming_indicator_sync_enabled():
                    mgmt_result = sync_forming_excel_to_indicator(filepath)
                    logger.info(
                        "[Excel] forming_production_indicator 同期: inserted=%s deleted=%s parsed=%s (%s)",
                        mgmt_result.inserted,
                        mgmt_result.deleted,
                        mgmt_result.parsed,
                        filename,
                    )
            elif is_excel_target_file(filename):""",
        """            elif is_forming_excel_file(filename):
                if _forming_indicator_sync_enabled():
                    mgmt_result = sync_forming_excel_to_indicator(filepath)
                    logger.info(
                        "[Excel] forming_production_indicator 同期: inserted=%s deleted=%s parsed=%s (%s)",
                        mgmt_result.inserted,
                        mgmt_result.deleted,
                        mgmt_result.parsed,
                        filename,
                    )
            elif is_chamfering_excel_file(filename):
                if _chamfering_indicator_sync_enabled():
                    mgmt_result = sync_chamfering_excel_to_indicator(filepath)
                    logger.info(
                        "[Excel] chamfering_production_indicator 同期: inserted=%s deleted=%s parsed=%s (%s)",
                        mgmt_result.inserted,
                        mgmt_result.deleted,
                        mgmt_result.parsed,
                        filename,
                    )
            elif is_excel_target_file(filename):""",
    ),
    (
        "or is_cutting_excel_file(filename) or is_forming_excel_file(filename):",
        "or is_cutting_excel_file(filename) or is_forming_excel_file(filename) or is_chamfering_excel_file(filename):",
    ),
    (
        "    forming_excel_path = _get_forming_excel_path()",
        "    forming_excel_path = _get_forming_excel_path()\n    chamfering_excel_path = _get_chamfering_excel_path()",
    ),
    (
        """    forming_watcher_enabled = (
        os.environ.get("DISABLE_FORMING_EXCEL_WATCHER", "").strip().lower() != "true"
    ) and is_forming_excel_watcher_enabled()
    excel_queue_needed = excel_watcher_enabled or (""",
        """    forming_watcher_enabled = (
        os.environ.get("DISABLE_FORMING_EXCEL_WATCHER", "").strip().lower() != "true"
    ) and is_forming_excel_watcher_enabled()
    chamfering_watcher_enabled = (
        os.environ.get("DISABLE_CHAMFERING_EXCEL_WATCHER", "").strip().lower() != "true"
    ) and is_chamfering_excel_watcher_enabled()
    excel_queue_needed = excel_watcher_enabled or (""",
    ),
    (
        ") or (forming_watcher_enabled and bool(forming_excel_path))",
        ") or (forming_watcher_enabled and bool(forming_excel_path)) or (chamfering_watcher_enabled and bool(chamfering_excel_path))",
    ),
    (
        """    if forming_excel_path:
        logger.info("📂 成形管理指標 Excel パス: %s", forming_excel_path)
        if _forming_indicator_sync_enabled():
            logger.info("📋 成形管理指標 → forming_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 成形管理指標 → forming_production_indicator 全件同期: 無効")
    logger.info(""",
        """    if forming_excel_path:
        logger.info("📂 成形管理指標 Excel パス: %s", forming_excel_path)
        if _forming_indicator_sync_enabled():
            logger.info("📋 成形管理指標 → forming_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 成形管理指標 → forming_production_indicator 全件同期: 無効")
    if chamfering_excel_path:
        logger.info("📂 面取管理指標 Excel パス: %s", chamfering_excel_path)
        if _chamfering_indicator_sync_enabled():
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 無効")
    logger.info(""",
    ),
    (
        "切断管理指標 %s、成形管理指標 %s",
        "切断管理指標 %s、成形管理指標 %s、面取管理指標 %s",
    ),
    (
        '"有効" if (forming_watcher_enabled and forming_excel_path) else "未設定/無効",\n    )',
        '"有効" if (forming_watcher_enabled and forming_excel_path) else "未設定/無効",\n        "有効" if (chamfering_watcher_enabled and chamfering_excel_path) else "未設定/無効",\n    )',
    ),
    (
        """    if forming_excel_path and not forming_watcher_enabled:
        logger.info("📌 成形管理指標 Excel 監視は無効です（環境変数またはシステム設定）")
    if excel_watcher_enabled and excel_path:""",
        """    if forming_excel_path and not forming_watcher_enabled:
        logger.info("📌 成形管理指標 Excel 監視は無効です（環境変数またはシステム設定）")
    if chamfering_excel_path and not chamfering_watcher_enabled:
        logger.info("📌 面取管理指標 Excel 監視は無効です（環境変数またはシステム設定）")
    if excel_watcher_enabled and excel_path:""",
    ),
    (
        """        forming_watcher_enabled=forming_watcher_enabled,
        forming_excel_path=forming_excel_path,
        in_queue_excel_filenames=in_queue_excel_filenames,""",
        """        forming_watcher_enabled=forming_watcher_enabled,
        forming_excel_path=forming_excel_path,
        chamfering_watcher_enabled=chamfering_watcher_enabled,
        chamfering_excel_path=chamfering_excel_path,
        in_queue_excel_filenames=in_queue_excel_filenames,""",
    ),
    (
        """    if forming_excel_path:
        forming_dir = os.path.dirname(forming_excel_path)
        if forming_dir and forming_dir not in (csv_path, excel_path):
            try:
                observer.schedule(handler, forming_dir, recursive=False)
            except Exception as e:
                logger.warning("成形管理指標ディレクトリの watchdog 登録失敗（ポーリングで補完）: %s", e)
    watched_roots = {os.path.normpath(csv_path)}""",
        """    if forming_excel_path:
        forming_dir = os.path.dirname(forming_excel_path)
        if forming_dir and forming_dir not in (csv_path, excel_path):
            try:
                observer.schedule(handler, forming_dir, recursive=False)
            except Exception as e:
                logger.warning("成形管理指標ディレクトリの watchdog 登録失敗（ポーリングで補完）: %s", e)
    if chamfering_excel_path:
        chamfering_dir = os.path.dirname(chamfering_excel_path)
        if chamfering_dir and chamfering_dir not in (csv_path, excel_path):
            try:
                observer.schedule(handler, chamfering_dir, recursive=False)
            except Exception as e:
                logger.warning("面取管理指標ディレクトリの watchdog 登録失敗（ポーリングで補完）: %s", e)
    watched_roots = {os.path.normpath(csv_path)}""",
    ),
    (
        """    if forming_excel_path:
        fdir = os.path.dirname(forming_excel_path)
        if fdir:
            watched_roots.add(os.path.normpath(fdir))
    for fullpath, _bn in settings.get_material_receiving_csv_entries():""",
        """    if forming_excel_path:
        fdir = os.path.dirname(forming_excel_path)
        if fdir:
            watched_roots.add(os.path.normpath(fdir))
    if chamfering_excel_path:
        chdir = os.path.dirname(chamfering_excel_path)
        if chdir:
            watched_roots.add(os.path.normpath(chdir))
    for fullpath, _bn in settings.get_material_receiving_csv_entries():""",
    ),
    (
        """                forming_excel_path,
            )
    if excel_watcher_enabled and excel_path:
        logger.info("✅ ポーリング開始（Watchdog + Excel mtime）、ファイル変更を待機中...""",
        """                forming_excel_path,
            )
    if chamfering_watcher_enabled and chamfering_excel_path:
        chamfering_poll_thread = threading.Thread(
            target=_chamfering_excel_polling_loop,
            args=(
                chamfering_excel_path,
                excel_task_queue,
                POLL_INTERVAL,
                stop_polling,
                in_queue_excel_filenames,
            ),
            daemon=True,
            name="ChamferingExcelMtimePoll",
        )
        chamfering_poll_thread.start()
        logger.info("✅ 面取管理指標 Excel ポーリング開始: %s", os.path.basename(chamfering_excel_path))
        if os.path.isfile(chamfering_excel_path):
            _enqueue_chamfering_excel(
                chamfering_excel_path,
                excel_task_queue,
                in_queue_excel_filenames,
                reason="起動時",
            )
        else:
            logger.warning(
                "⚠️ 面取管理指標 Excel は起動時に未検出（ネットワーク復旧後に自動監視）: %s",
                chamfering_excel_path,
            )
    if excel_watcher_enabled and excel_path:
        logger.info("✅ ポーリング開始（Watchdog + Excel mtime）、ファイル変更を待機中...""",
    ),
]

for old, new in blocks:
    if old not in t:
        raise SystemExit(f"run.py pattern missing: {old[:100]!r}")
    t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")
print("patched run.py")
