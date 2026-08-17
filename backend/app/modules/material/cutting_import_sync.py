"""
材料切断 CSV → material_cutting_logs 同期（file_watcher 用・同期・mysql.connector）
API の import_cutting_csv（デフォルト：削除せず追記＋重複スキップ）と同一ロジック。
"""
import logging
from datetime import date
from typing import Any, Optional

import mysql.connector

from app.core.config import settings
from app.modules.material.cutting_import_api import (
    RETENTION_DAYS,
    cutting_log_dedupe_key,
    dedupe_rows_keep_last,
    parse_material_cutting_csv_text,
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


def _load_existing_keys(cur, d_min: Optional[date], d_max: Optional[date]) -> set:
    if d_min is not None and d_max is not None:
        cur.execute(
            """
            SELECT log_date, log_time, hd_no, material_cd, management_code
            FROM material_cutting_logs
            WHERE log_date IS NULL
               OR (log_date >= %s AND log_date <= %s)
            """,
            (d_min, d_max),
        )
    else:
        cur.execute(
            """
            SELECT log_date, log_time, hd_no, material_cd, management_code
            FROM material_cutting_logs
            """
        )
    keys = set()
    for row in cur.fetchall():
        keys.add(
            cutting_log_dedupe_key(
                {
                    "log_date": row[0],
                    "log_time": row[1],
                    "hd_no": row[2],
                    "material_cd": row[3],
                    "management_code": row[4],
                }
            )
        )
    return keys


def sync_material_cutting_csv(
    filepath: str,
    *,
    retain_days: int = RETENTION_DAYS,
) -> dict[str, Any]:
    """
    共有パスの materialCutting.csv を読み、material_cutting_logs に追記する。
    既存行は削除しない。CSV内・DB既存の同一キーはスキップ。
    """
    path = filepath
    raw_text = _read_csv_file(path)
    parsed = parse_material_cutting_csv_text(raw_text, source_path=path)
    rows = parsed["rows"]
    errors = list(parsed["errors"])
    csv_dates = list(parsed["csv_dates"])
    unique_rows, skipped_csv_dup = dedupe_rows_keep_last(rows)

    d_min = min(csv_dates) if csv_dates else None
    d_max = max(csv_dates) if csv_dates else None

    deleted_prune = 0
    skipped_db_dup = 0
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
        # 非推奨互換: retain_days>0 のときだけ古い行削除
        if retain_days > 0:
            from datetime import datetime, timedelta
            from app.modules.material.cutting_import_api import JST, CUTTING_LOG_MANUAL_SOURCE_PREFIX

            cutoff = datetime.now(JST).date() - timedelta(days=retain_days)
            cur.execute(
                """
                DELETE FROM material_cutting_logs
                WHERE log_date < %s
                  AND (source_file IS NULL OR source_file NOT LIKE %s)
                """,
                (cutoff, CUTTING_LOG_MANUAL_SOURCE_PREFIX + "%"),
            )
            deleted_prune = cur.rowcount

        existing = _load_existing_keys(cur, d_min, d_max)
        batch: list[tuple] = []
        for rec in unique_rows:
            key = cutting_log_dedupe_key(rec)
            if key in existing:
                skipped_db_dup += 1
                continue
            batch.append(
                (
                    rec.get("item"),
                    rec.get("log_date"),
                    rec.get("log_time"),
                    rec.get("hd_no"),
                    rec.get("operator_name"),
                    rec.get("material_cd"),
                    rec.get("management_code"),
                    rec.get("raw_line"),
                    rec.get("source_file") or path,
                )
            )
            existing.add(key)
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

    result: dict[str, Any] = {
        "success": True,
        "imported": imported,
        "parsed_rows": len(rows),
        "unique_rows": len(unique_rows),
        "skipped_csv_dup": skipped_csv_dup,
        "skipped_db_dup": skipped_db_dup,
        "errors_count": len(errors),
        "errors": errors[:20],
        "deleted_prune": deleted_prune,
        "deleted_window": 0,
        "retain_days": retain_days,
        "csv_date_min": d_min.isoformat() if d_min else None,
        "csv_date_max": d_max.isoformat() if d_max else None,
        "skipped_before_retention": 0,
        "delimiter": parsed.get("delimiter"),
    }
    if imported == 0 and skipped_db_dup > 0:
        result["warning"] = (
            f"新規取込 0 件（DB 既存と重複 {skipped_db_dup} 件をスキップ）。すでに取り込み済みです。"
        )
    return result
