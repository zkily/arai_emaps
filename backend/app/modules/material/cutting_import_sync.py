"""
材料切断 CSV → material_cutting_logs 同期（file_watcher 用・同期・mysql.connector）
API の import_cutting_csv（デフォルトモード）と同一ロジック。
"""
import csv
import io
import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

import mysql.connector

from app.core.config import settings
from app.modules.material.cutting_import_api import (
    JST,
    RETENTION_DAYS,
    CUTTING_LOG_MANUAL_SOURCE_PREFIX,
    _parse_date,
    _parse_time,
    _read_csv_file,
)

logger = logging.getLogger(__name__)


def _get_conn():
    return mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )


def sync_material_cutting_csv(
    filepath: str,
    *,
    retain_days: int = RETENTION_DAYS,
) -> dict[str, Any]:
    """
    共有パスの materialCutting.csv を読み、material_cutting_logs に反映する。
    full_replace は行わない（API と同じデフォルト戦略）。
    """
    path = filepath
    raw_text = _read_csv_file(path)

    reader = csv.reader(io.StringIO(raw_text))
    header: Optional[list[str]] = None
    errors: list[str] = []
    rows_to_insert: list[tuple] = []
    csv_dates: list[date] = []

    for row_idx, row in enumerate(reader, start=1):
        if not any(cell.strip() for cell in row):
            continue
        if header is None:
            header = [c.strip() for c in row]
            continue
        raw_line = ",".join(row)
        try:

            def _col(name: str) -> str:
                idx = header.index(name) if name in header else -1
                return row[idx].strip() if 0 <= idx < len(row) else ""

            log_date = _parse_date(_col("日付"))
            log_time = _parse_time(_col("時間"))
            rows_to_insert.append(
                (
                    _col("項目") or None,
                    log_date,
                    log_time,
                    _col("HDNo") or None,
                    _col("担当者") or None,
                    _col("材料コード") or None,
                    _col("管理コード") or None,
                    raw_line,
                    path,
                )
            )
            if log_date is not None:
                csv_dates.append(log_date)
        except Exception as exc:
            errors.append(f"行 {row_idx}: {exc}")
            if len(errors) >= 50:
                errors.append("... エラーが多すぎるため省略")
                break

    today_jst = datetime.now(JST).date()
    cutoff: Optional[date] = None
    if retain_days > 0:
        cutoff = today_jst - timedelta(days=retain_days)

    d_min = min(csv_dates) if csv_dates else None
    d_max = max(csv_dates) if csv_dates else None

    deleted_prune = 0
    deleted_window = 0
    skipped_retention = 0
    imported = 0

    conn = _get_conn()
    conn.autocommit = False
    cur = conn.cursor()
    insert_sql = """
        INSERT INTO material_cutting_logs
        (item, log_date, log_time, hd_no, operator_name, material_cd, management_code, raw_line, source_file)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        _manual_like = CUTTING_LOG_MANUAL_SOURCE_PREFIX + "%"
        if retain_days > 0 and cutoff is not None:
            cur.execute(
                """
                DELETE FROM material_cutting_logs
                WHERE log_date < %s
                  AND (source_file IS NULL OR source_file NOT LIKE %s)
                """,
                (cutoff, _manual_like),
            )
            deleted_prune = cur.rowcount

        if d_min is not None and d_max is not None and d_min <= d_max:
            cur.execute(
                """
                DELETE FROM material_cutting_logs
                WHERE log_date >= %s AND log_date <= %s
                  AND (source_file IS NULL OR source_file NOT LIKE %s)
                """,
                (d_min, d_max, _manual_like),
            )
            deleted_window = cur.rowcount

        batch: list[tuple] = []
        for tup in rows_to_insert:
            log_date = tup[1]
            if log_date is not None and cutoff is not None and log_date < cutoff:
                skipped_retention += 1
                continue
            batch.append(tup)
            imported += 1

        if batch:
            cur.executemany(insert_sql, batch)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    return {
        "success": True,
        "imported": imported,
        "errors_count": len(errors),
        "errors": errors[:20],
        "deleted_prune": deleted_prune,
        "deleted_window": deleted_window,
        "retain_days": retain_days,
        "csv_date_min": d_min.isoformat() if d_min else None,
        "csv_date_max": d_max.isoformat() if d_max else None,
        "skipped_before_retention": skipped_retention,
    }
