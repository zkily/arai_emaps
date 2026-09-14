"""lot_forecast_attribution の無効版（is_current=0）を archive 表へ退避する。

業務照会・再計算は is_current=1 のみ参照するため、無効行の移動は機能に影響しない。
DELETE は常に is_current=0 を条件に含め、現行行を誤って消さない。
"""
from __future__ import annotations

import logging
import random
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Optional

from app.services.file_watcher.sync_services import get_db_connection

logger = logging.getLogger(__name__)

HOT_TABLE = "lot_forecast_attribution"
ARCHIVE_TABLE = "lot_forecast_attribution_archive"

_ARCHIVE_CHUNK = 3000
_LOCK_WAIT_TIMEOUT_SEC = 15
_BATCH_PAUSE_SEC = 0.02
_TX_RETRIES = 5
_RETRYABLE_LOCK_ERRNOS = {1205, 1213}
_THREAD_LOCK = threading.Lock()

_ARCHIVE_TASKS: dict[str, dict[str, Any]] = {}
_ARCHIVE_TASKS_LOCK = threading.Lock()

ProgressCb = Callable[[int, str, int, int], None]


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _is_retryable_lock_error(exc: BaseException) -> bool:
    errno = getattr(exc, "errno", None)
    if errno in _RETRYABLE_LOCK_ERRNOS:
        return True
    msg = str(exc)
    return "1205" in msg or "1213" in msg or "Lock wait timeout" in msg or "Deadlock" in msg


def _sleep_lock_backoff(attempt: int) -> None:
    time.sleep(0.15 * (2**attempt) + random.uniform(0, 0.25))


def _table_exists(cursor, name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (name,),
    )
    row = cursor.fetchone()
    val = row[0] if row and not isinstance(row, dict) else 0
    return int(val or 0) > 0


def _hot_columns(cursor) -> list[str]:
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """,
        (HOT_TABLE,),
    )
    names: list[str] = []
    for row in cursor.fetchall() or []:
        name = row[0] if not isinstance(row, dict) else next(iter(row.values()))
        if name:
            names.append(str(name))
    if not names:
        raise RuntimeError(f"{HOT_TABLE} の列を取得できませんでした")
    return names


def archive_stale_lot_forecast_attributions_sync(progress_cb: ProgressCb | None = None) -> dict:
    """is_current=0 の行を lot_forecast_attribution_archive へ移動する。"""
    archived = 0
    total_candidates = 0

    def _notify(percent: int, message: str) -> None:
        if progress_cb is None:
            return
        try:
            progress_cb(int(percent), str(message), int(archived), int(total_candidates))
        except Exception:
            pass

    with _THREAD_LOCK:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        try:
            if not _table_exists(cursor, ARCHIVE_TABLE):
                raise RuntimeError(
                    "lot_forecast_attribution_archive テーブルが存在しません。"
                    "backend/database/migrations/130_lot_forecast_attribution_archive.sql を適用してください。"
                )

            columns = _hot_columns(cursor)
            col_sql = ", ".join(f"`{c}`" for c in columns)
            cursor.execute(f"SET SESSION innodb_lock_wait_timeout = {_LOCK_WAIT_TIMEOUT_SEC}")

            _notify(3, "無効版（is_current=0）の件数を集計中")
            cursor.execute(
                f"SELECT COUNT(*) FROM `{HOT_TABLE}` WHERE is_current = 0"
            )
            row = cursor.fetchone()
            total_candidates = int((row[0] if row and not isinstance(row, dict) else 0) or 0)
            conn.commit()
            if total_candidates <= 0:
                _notify(100, "退避対象なし")
                return {"archived": 0, "total_candidates": 0}

            _notify(6, f"退避対象 {total_candidates} 件を処理開始")
            last_id = 0
            while True:
                ids: list[int] = []
                moved = False
                for attempt in range(_TX_RETRIES):
                    try:
                        cursor.execute(
                            f"""
                            SELECT id
                            FROM `{HOT_TABLE}`
                            WHERE id > %s AND is_current = 0
                            ORDER BY id
                            LIMIT {_ARCHIVE_CHUNK}
                            """,
                            (last_id,),
                        )
                        ids = [int(r[0]) for r in cursor.fetchall() if r and r[0] is not None]
                        if not ids:
                            conn.commit()
                            break

                        placeholders = ",".join(["%s"] * len(ids))
                        cursor.execute(
                            f"""
                            INSERT IGNORE INTO `{ARCHIVE_TABLE}` ({col_sql})
                            SELECT {col_sql}
                            FROM `{HOT_TABLE}`
                            WHERE id IN ({placeholders})
                              AND is_current = 0
                            """,
                            ids,
                        )
                        cursor.execute(
                            f"""
                            DELETE FROM `{HOT_TABLE}`
                            WHERE id IN ({placeholders})
                              AND is_current = 0
                            """,
                            ids,
                        )
                        conn.commit()
                        archived += len(ids)
                        last_id = ids[-1]
                        moved = True
                        pct = min(99, 6 + int(archived * 93 / max(total_candidates, 1)))
                        _notify(pct, f"{archived} / {total_candidates} 件を退避中")
                        break
                    except Exception as e:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        if _is_retryable_lock_error(e) and attempt < _TX_RETRIES - 1:
                            logger.warning(
                                "lot_forecast_attribution アーカイブでロック競合 再試行 %s/%s（退避済み: %s）",
                                attempt + 1,
                                _TX_RETRIES,
                                archived,
                            )
                            _sleep_lock_backoff(attempt)
                            continue
                        raise

                if not ids:
                    break
                if not moved:
                    raise RuntimeError("lot_forecast_attribution アーカイブのチャンク処理に失敗しました")
                if _BATCH_PAUSE_SEC > 0:
                    time.sleep(_BATCH_PAUSE_SEC)

            logger.info(
                "lot_forecast_attribution アーカイブ完了: %s 件を %s へ退避",
                archived,
                ARCHIVE_TABLE,
            )
            _notify(100, f"{archived} 件の退避が完了しました")
            return {"archived": archived, "total_candidates": total_candidates}
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(
                "lot_forecast_attribution アーカイブ失敗（退避済み: %s）: %s",
                archived,
                e,
                exc_info=True,
            )
            raise
        finally:
            cursor.close()
            conn.close()


def create_archive_task() -> str:
    task_id = uuid.uuid4().hex
    with _ARCHIVE_TASKS_LOCK:
        _ARCHIVE_TASKS[task_id] = {
            "task_id": task_id,
            "status": "queued",
            "progress_percent": 0,
            "message": "queued",
            "archived": 0,
            "total_candidates": 0,
            "created_at": _utc_now_iso(),
            "started_at": None,
            "finished_at": None,
            "error": None,
        }
    return task_id


def _update_archive_task(task_id: str, **patch: Any) -> None:
    with _ARCHIVE_TASKS_LOCK:
        task = _ARCHIVE_TASKS.get(task_id)
        if not task:
            return
        task.update(patch)


def get_archive_task(task_id: str) -> Optional[dict[str, Any]]:
    with _ARCHIVE_TASKS_LOCK:
        task = _ARCHIVE_TASKS.get(task_id)
        return dict(task) if task else None


def run_archive_task(task_id: str) -> None:
    _update_archive_task(
        task_id,
        status="running",
        progress_percent=1,
        message="アーカイブ開始",
        started_at=_utc_now_iso(),
    )

    def _progress(percent: int, message: str, archived: int, total: int) -> None:
        _update_archive_task(
            task_id,
            progress_percent=max(0, min(99, int(percent))),
            message=message,
            archived=int(archived or 0),
            total_candidates=int(total or 0),
        )

    try:
        result = archive_stale_lot_forecast_attributions_sync(progress_cb=_progress)
        archived = int(result.get("archived") or 0)
        total = int(result.get("total_candidates") or 0)
        _update_archive_task(
            task_id,
            status="completed",
            progress_percent=100,
            message=f"{archived} 件の無効版を {ARCHIVE_TABLE} へ退避しました",
            archived=archived,
            total_candidates=total,
            finished_at=_utc_now_iso(),
        )
    except Exception as e:
        logger.error("lot_forecast_attribution アーカイブタスク失敗: %s", e, exc_info=True)
        _update_archive_task(
            task_id,
            status="failed",
            progress_percent=100,
            message="failed",
            error=str(e),
            finished_at=_utc_now_iso(),
        )
