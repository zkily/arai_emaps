from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _format_access_date(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = str(v).strip()
    return s or None


def sync_production_plan_excel_to_access(
    rows: list[dict[str, Any]],
    access_db_path: str,
    access_table: str,
) -> int:
    """
    production_plan_excel 全量覆盖写入 Access 表。
    返回写入行数。
    """
    try:
        import pyodbc  # type: ignore[import-not-found]
    except Exception as e:  # pragma: no cover
        raise RuntimeError("pyodbc 未安装，请先在 backend 环境安装 pyodbc") from e

    conn_str = (
        r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={access_db_path};"
    )
    conn = pyodbc.connect(conn_str, autocommit=False)
    try:
        cur = conn.cursor()
        tbl = f"[{access_table}]"
        cur.execute(f"DELETE FROM {tbl}")
        insert_sql = (
            f"INSERT INTO {tbl} "
            "([検索], [日付], [加工機], [製品CD], [製品名], [加工計画], [生産順番], [順番]) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )
        payload = []
        for r in rows:
            payload.append(
                (
                    r.get("検索"),
                    _format_access_date(r.get("日付")),
                    r.get("加工機"),
                    r.get("製品CD"),
                    r.get("製品名"),
                    int(r.get("加工計画") or 0),
                    str(r.get("生産順番") or ""),
                    int(r.get("順番") or 0),
                )
            )
        if payload:
            # Access ODBC で fast_executemany は不安定（クラッシュ要因）なため使用しない
            batch_size = 500
            for i in range(0, len(payload), batch_size):
                cur.executemany(insert_sql, payload[i : i + batch_size])
        conn.commit()
        return len(payload)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

