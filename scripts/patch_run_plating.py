# -*- coding: utf-8
"""Add plating excel watcher to run.py (mirror chamfering)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "backend/app/services/file_watcher/run.py"
t = p.read_text(encoding="utf-8")

blocks = [
    (
        "from app.services.file_watcher.chamfering_production_indicator_sync import sync_chamfering_excel_to_indicator",
        """from app.services.file_watcher.chamfering_production_indicator_sync import sync_chamfering_excel_to_indicator
from app.services.file_watcher.plating_excel_processor import (
    is_plating_excel_file,
)
from app.services.file_watcher.plating_production_indicator_sync import sync_plating_excel_to_indicator""",
    ),
    (
        "    is_chamfering_indicator_sync_enabled,\n)",
        """    is_chamfering_indicator_sync_enabled,
    is_plating_excel_watcher_enabled,
    is_plating_indicator_sync_enabled,
)""",
    ),
    (
        """def _chamfering_indicator_sync_enabled() -> bool:
    env = os.environ.get("FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED", True)) and is_chamfering_indicator_sync_enabled()


def _norm_path(value):""",
        """def _chamfering_indicator_sync_enabled() -> bool:
    env = os.environ.get("FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "FILE_WATCH_CHAMFERING_INDICATOR_SYNC_ENABLED", True)) and is_chamfering_indicator_sync_enabled()


def _plating_indicator_sync_enabled() -> bool:
    env = os.environ.get("FILE_WATCH_PLATING_INDICATOR_SYNC_ENABLED", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return bool(getattr(settings, "FILE_WATCH_PLATING_INDICATOR_SYNC_ENABLED", True)) and is_plating_indicator_sync_enabled()


def _norm_path(value):""",
    ),
    (
        """            logger.debug("面取管理指標ポーリング異常: %s", e)


def _material_csv_polling_loop(task_queue, poll_interval, stop_event):""",
        """            logger.debug("面取管理指標ポーリング異常: %s", e)


def _get_plating_excel_path():
    raw = (
        os.environ.get("FILE_WATCH_PLATING_EXCEL_PATH")
        or getattr(settings, "FILE_WATCH_PLATING_EXCEL_PATH", "")
        or ""
    )
    return _norm_path(raw)


def _enqueue_plating_excel(file_path, task_queue, in_queue_filenames, reason: str = "") -> bool:
    if not file_path:
        return False
    filename = os.path.basename(file_path)
    if not is_plating_excel_file(filename):
        logger.warning(
            "メッキ管理指標: ファイル名がパターンと一致しません（生産管理指標(YYYY年度-メッキ).xlsx）: %s",
            filename,
        )
        return False
    if not os.path.isfile(file_path):
        logger.debug("メッキ管理指標 Excel は未存在のためキュー投入をスキップ: %s", file_path)
        return False
    if filename in in_queue_filenames:
        return False
    in_queue_filenames.add(filename)
    try:
        task_queue.put((file_path, filename))
        suffix = f" ({reason})" if reason else ""
        logger.info("メッキ管理指標 Excel をキュー投入%s: %s", suffix, filename)
        return True
    except Exception:
        in_queue_filenames.discard(filename)
        return False


def _plating_excel_polling_loop(file_path, task_queue, poll_interval, stop_event, in_queue_filenames):
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
                    logger.warning("メッキ管理指標 Excel が見つかりません（到達可能になるまで待機）: %s", file_path)
                    missing_logged = True
                continue
            if missing_logged:
                logger.info("メッキ管理指標 Excel を検出しました: %s", file_path)
                missing_logged = False
            if filename in in_queue_filenames:
                continue
            try:
                mtime = os.path.getmtime(file_path)
            except OSError:
                continue
            if last_mtime is not None and mtime > last_mtime:
                logger.info("メッキ管理指標 Excel 変更検知: %s", filename)
                _enqueue_plating_excel(file_path, task_queue, in_queue_filenames, reason="mtime変更")
            last_mtime = mtime
        except Exception as e:
            logger.debug("メッキ管理指標ポーリング異常: %s", e)


def _material_csv_polling_loop(task_queue, poll_interval, stop_event):""",
    ),
    (
        """            elif is_chamfering_excel_file(filename):
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
        """            elif is_chamfering_excel_file(filename):
                if _chamfering_indicator_sync_enabled():
                    mgmt_result = sync_chamfering_excel_to_indicator(filepath)
                    logger.info(
                        "[Excel] chamfering_production_indicator 同期: inserted=%s deleted=%s parsed=%s (%s)",
                        mgmt_result.inserted,
                        mgmt_result.deleted,
                        mgmt_result.parsed,
                        filename,
                    )
            elif is_plating_excel_file(filename):
                if _plating_indicator_sync_enabled():
                    mgmt_result = sync_plating_excel_to_indicator(filepath)
                    logger.info(
                        "[Excel] plating_production_indicator 同期: inserted=%s deleted=%s parsed=%s (%s)",
                        mgmt_result.inserted,
                        mgmt_result.deleted,
                        mgmt_result.parsed,
                        filename,
                    )
            elif is_excel_target_file(filename):""",
    ),
    (
        "or is_chamfering_excel_file(filename):",
        "or is_chamfering_excel_file(filename) or is_plating_excel_file(filename):",
    ),
    (
        "    chamfering_excel_path = _get_chamfering_excel_path()",
        "    chamfering_excel_path = _get_chamfering_excel_path()\n    plating_excel_path = _get_plating_excel_path()",
    ),
    (
        """    chamfering_watcher_enabled = (
        os.environ.get("DISABLE_CHAMFERING_EXCEL_WATCHER", "").strip().lower() != "true"
    ) and is_chamfering_excel_watcher_enabled()
    excel_queue_needed = excel_watcher_enabled or (""",
        """    chamfering_watcher_enabled = (
        os.environ.get("DISABLE_CHAMFERING_EXCEL_WATCHER", "").strip().lower() != "true"
    ) and is_chamfering_excel_watcher_enabled()
    plating_watcher_enabled = (
        os.environ.get("DISABLE_PLATING_EXCEL_WATCHER", "").strip().lower() != "true"
    ) and is_plating_excel_watcher_enabled()
    excel_queue_needed = excel_watcher_enabled or (""",
    ),
    (
        ") or (chamfering_watcher_enabled and bool(chamfering_excel_path))",
        ") or (chamfering_watcher_enabled and bool(chamfering_excel_path)) or (plating_watcher_enabled and bool(plating_excel_path))",
    ),
    (
        """    if chamfering_excel_path:
        logger.info("📂 面取管理指標 Excel パス: %s", chamfering_excel_path)
        if _chamfering_indicator_sync_enabled():
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 無件同期: 無効")
    logger.info(""",
        """    if chamfering_excel_path:
        logger.info("📂 面取管理指標 Excel パス: %s", chamfering_excel_path)
        if _chamfering_indicator_sync_enabled():
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 無効")
    if plating_excel_path:
        logger.info("📂 メッキ管理指標 Excel パス: %s", plating_excel_path)
        if _plating_indicator_sync_enabled():
            logger.info("📋 メッキ管理指標 → plating_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 メッキ管理指標 → plating_production_indicator 全件同期: 無効")
    logger.info(""",
    ),
]

# Fix typo in replacement - I had 無件同期 in one block, let me fix the block above
blocks[9] = (
    """    if chamfering_excel_path:
        logger.info("📂 面取管理指標 Excel パス: %s", chamfering_excel_path)
        if _chamfering_indicator_sync_enabled():
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 無効")
    logger.info(""",
    """    if chamfering_excel_path:
        logger.info("📂 面取管理指標 Excel パス: %s", chamfering_excel_path)
        if _chamfering_indicator_sync_enabled():
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 面取管理指標 → chamfering_production_indicator 全件同期: 無効")
    if plating_excel_path:
        logger.info("📂 メッキ管理指標 Excel パス: %s", plating_excel_path)
        if _plating_indicator_sync_enabled():
            logger.info("📋 メッキ管理指標 → plating_production_indicator 全件同期: 有効")
        else:
            logger.info("📋 メッキ管理指標 → plating_production_indicator 全件同期: 無効")
    logger.info(""",
)

blocks.extend([
    (
        "面取管理指標 %s",
        "面取管理指標 %s、メッキ管理指標 %s",
    ),
    (
        '"有効" if (chamfering_watcher_enabled and chamfering_excel_path) else "未設定/無効",\n    )',
        '"有効" if (chamfering_watcher_enabled and chamfering_excel_path) else "未設定/無効",\n        "有効" if (plating_watcher_enabled and plating_excel_path) else "未設定/無効",\n    )',
    ),
    (
        """    if chamfering_excel_path and not chamfering_watcher_enabled:
        logger.info("📌 面取管理指標 Excel 監視は無効です（環境変数またはシステム設定）")
    if excel_watcher_enabled and excel_path:""",
        """    if chamfering_excel_path and not chamfering_watcher_enabled:
        logger.info("📌 面取管理指標 Excel 監視は無効です（環境変数またはシステム設定）")
    if plating_excel_path and not plating_watcher_enabled:
        logger.info("📌 メッキ管理指標 Excel 監視は無効です（環境変数またはシステム設定）")
    if excel_watcher_enabled and excel_path:""",
    ),
    (
        """        chamfering_watcher_enabled=chamfering_watcher_enabled,
        chamfering_excel_path=chamfering_excel_path,
        in_queue_excel_filenames=in_queue_excel_filenames,""",
        """        chamfering_watcher_enabled=chamfering_watcher_enabled,
        chamfering_excel_path=chamfering_excel_path,
        plating_watcher_enabled=plating_watcher_enabled,
        plating_excel_path=plating_excel_path,
        in_queue_excel_filenames=in_queue_excel_filenames,""",
    ),
    (
        """    if chamfering_excel_path:
        chamfering_dir = os.path.dirname(chamfering_excel_path)
        if chamfering_dir and chamfering_dir not in (csv_path, excel_path):
            try:
                observer.schedule(handler, chamfering_dir, recursive=False)
            except Exception as e:
                logger.warning("面取管理指標ディレクトリの watchdog 登録失敗（ポーリングで補完）: %s", e)
    watched_roots = {os.path.normpath(csv_path)}""",
        """    if chamfering_excel_path:
        chamfering_dir = os.path.dirname(chamfering_excel_path)
        if chamfering_dir and chamfering_dir not in (csv_path, excel_path):
            try:
                observer.schedule(handler, chamfering_dir, recursive=False)
            except Exception as e:
                logger.warning("面取管理指標ディレクトリの watchdog 登録失敗（ポーリングで補完）: %s", e)
    if plating_excel_path:
        plating_dir = os.path.dirname(plating_excel_path)
        if plating_dir and plating_dir not in (csv_path, excel_path):
            try:
                observer.schedule(handler, plating_dir, recursive=False)
            except Exception as e:
                logger.warning("メッキ管理指標ディレクトリの watchdog 登録失敗（ポーリングで補完）: %s", e)
    watched_roots = {os.path.normpath(csv_path)}""",
    ),
    (
        """    if chamfering_excel_path:
        chdir = os.path.dirname(chamfering_excel_path)
        if chdir:
            watched_roots.add(os.path.normpath(chdir))
    for fullpath, _bn in settings.get_material_receiving_csv_entries():""",
        """    if chamfering_excel_path:
        chdir = os.path.dirname(chamfering_excel_path)
        if chdir:
            watched_roots.add(os.path.normpath(chdir))
    if plating_excel_path:
        pdir = os.path.dirname(plating_excel_path)
        if pdir:
            watched_roots.add(os.path.normpath(pdir))
    for fullpath, _bn in settings.get_material_receiving_csv_entries():""",
    ),
    (
        """                chamfering_excel_path,
            )
    if excel_watcher_enabled and excel_path:
        logger.info("✅ ポーリング開始（Watchdog + Excel mtime）、ファイル変更を待機中...""",
        """                chamfering_excel_path,
            )
    if plating_watcher_enabled and plating_excel_path:
        plating_poll_thread = threading.Thread(
            target=_plating_excel_polling_loop,
            args=(
                plating_excel_path,
                excel_task_queue,
                POLL_INTERVAL,
                stop_polling,
                in_queue_excel_filenames,
            ),
            daemon=True,
            name="PlatingExcelMtimePoll",
        )
        plating_poll_thread.start()
        logger.info("✅ メッキ管理指標 Excel ポーリング開始: %s", os.path.basename(plating_excel_path))
        if os.path.isfile(plating_excel_path):
            _enqueue_plating_excel(
                plating_excel_path,
                excel_task_queue,
                in_queue_excel_filenames,
                reason="起動時",
            )
        else:
            logger.warning(
                "⚠️ メッキ管理指標 Excel は起動時に未検出（ネットワーク復旧後に自動監視）: %s",
                plating_excel_path,
            )
    if excel_watcher_enabled and excel_path:
        logger.info("✅ ポーリング開始（Watchdog + Excel mtime）、ファイル変更を待機中...""",
    ),
])

for old, new in blocks:
    if old not in t:
        raise SystemExit(f"run.py pattern missing: {old[:100]!r}")
    t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")
print("patched run.py")
