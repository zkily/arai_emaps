"""
部品日次使用数（part_stock.planned_usage）の集計ソース:

- 主ソース: stock_transaction_logs（process_cd=KT07、実績+不良）を日付× target_cd（製品）で合算し、
  当日有効の製品 BOM 明細のうち consume_process_cd='KT07' の行の component_product_cd（部品）へ、
  その合算数量をそのまま planned_usage とする（qty_per による換算はしない）。
- 使用計画（usage_plan_qty）: production_summarys.molding_actual_plan × BOM
  （ComponentRequirements「日別・部品別需要」と同じ算出式）
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ユーザー入力不可（SQL インジェクション対策のため定数のみ使用）
_WELDING_USE_DRIVER_SQL = "(COALESCE(ps.welding_actual, 0) + COALESCE(ps.welding_defect, 0))"
_MOLDING_ACTUAL_PLAN_DRIVER_SQL = "COALESCE(ps.molding_actual_plan, 0)"

# stock_transaction_logs 由来の溶接（KT07）実績+不良 → planned_usage 用
_STL_PROCESS_CD_WELD = "KT07"
_STL_USAGE_TRANSACTION_TYPES = ("実績", "不良")


def _usage_int(v) -> int:
    if v is None:
        return 0
    if isinstance(v, Decimal):
        return int(round(float(v)))
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return 0


def normalize_part_stock_cd(part_cd: str | None) -> str:
    s = (part_cd or "").strip()
    return s if s else "(未設定)"


def calendar_date_only(v) -> date | None:
    """DB / ORM が返す date・datetime を dict キー用の date に統一する（datetime と date の不一致で lookup 失敗を防ぐ）。"""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


async def fetch_part_daily_usage_from_stock_transaction_logs(
    db: AsyncSession,
    d_start: date,
    d_end: date,
) -> Dict[Tuple[str, date], int]:
    """
    1) stock_transaction_logs: process_cd=KT07、transaction_type IN (実績, 不良) を
       DATE(transaction_time) × target_cd（製品）で SUM(ABS(quantity))（例: 600+5=605）。
    2) target_cd を parent_product_cd とし当日有効の product_bom_headers に繋ぎ、
       product_bom_lines で TRIM(consume_process_cd)='KT07' の行の component_product_cd を部品とする。
    3) その部品×日付に対し planned_usage は上記合計数量をそのまま用いる（同一部品×日で複数製品からは SUM）。

    戻り: (部品CD, 日付) -> 使用数（整数）。部品CD は TRIM 後の component_product_cd（空は '(未設定)'）。
    """
    params = {"d_start": d_start, "d_end": d_end}
    types_sql = ", ".join([f"'{t}'" for t in _STL_USAGE_TRANSACTION_TYPES])
    dsql = text(
        f"""
        SELECT
            t.eff_date AS eff_date,
            COALESCE(NULLIF(TRIM(t.component_cd), ''), '(未設定)') AS component_cd,
            SUM(t.product_qty) AS required_qty
        FROM (
            SELECT
                stl.eff_date AS eff_date,
                stl.product_cd AS product_cd,
                NULLIF(TRIM(l.component_product_cd), '') AS component_cd,
                stl.product_qty AS product_qty
            FROM (
                SELECT
                    DATE(transaction_time) AS eff_date,
                    NULLIF(TRIM(target_cd), '') AS product_cd,
                    SUM(ABS(COALESCE(quantity, 0))) AS product_qty
                FROM stock_transaction_logs
                WHERE LOWER(TRIM(COALESCE(process_cd, ''))) = LOWER(:proc_cd)
                  AND transaction_type IN ({types_sql})
                  AND DATE(transaction_time) >= :d_start
                  AND DATE(transaction_time) <= :d_end
                  AND target_cd IS NOT NULL
                  AND TRIM(target_cd) <> ''
                GROUP BY DATE(transaction_time), NULLIF(TRIM(target_cd), '')
            ) stl
            INNER JOIN product_bom_headers h
              ON h.id = (
                  SELECT h2.id
                  FROM product_bom_headers h2
                  WHERE h2.parent_product_cd = stl.product_cd
                    AND h2.status = 'active'
                    AND (h2.effective_from IS NULL OR h2.effective_from <= stl.eff_date)
                    AND (h2.effective_to IS NULL OR h2.effective_to >= stl.eff_date)
                  ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
                  LIMIT 1
              )
            INNER JOIN product_bom_lines l
              ON l.header_id = h.id
              AND LOWER(TRIM(COALESCE(l.consume_process_cd, ''))) = LOWER(:proc_cd)
              AND l.component_product_cd IS NOT NULL
              AND TRIM(l.component_product_cd) <> ''
              AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
            WHERE stl.product_cd IS NOT NULL
        ) t
        GROUP BY
            t.eff_date,
            COALESCE(NULLIF(TRIM(t.component_cd), ''), '(未設定)')
        """
    )
    params_with_proc = {**params, "proc_cd": _STL_PROCESS_CD_WELD}

    result = await db.execute(dsql, params_with_proc)
    rows = result.mappings().fetchall()
    out: Dict[Tuple[str, date], int] = {}
    for r in rows:
        cd = normalize_part_stock_cd(r.get("component_cd"))
        eff_d = calendar_date_only(r.get("eff_date"))
        if eff_d is None:
            continue
        rq = _usage_int(r.get("required_qty"))
        key = (cd, eff_d)
        out[key] = rq
    return out


async def fetch_part_daily_usage_from_production_summarys(
    db: AsyncSession,
    d_start: date,
    d_end: date,
) -> Dict[Tuple[str, date], int]:
    """
    戻り: (部品CD, 日付) -> 使用数（整数）
    部品CD は BOM 集計と同じく TRIM 後の component_product_cd（空は '(未設定)'）。

    注: 在庫計算の planned_usage は fetch_part_daily_usage_from_stock_transaction_logs を
    使う想定。本関数は production_summarys ベースの参照用に残す。
    """
    conditions = [
        "ps.date >= :d_start",
        "ps.date <= :d_end",
    ]
    params = {"d_start": d_start, "d_end": d_end}

    dsql = text(
        f"""
        SELECT
            ps.date AS eff_date,
            COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)') AS component_cd,
            SUM(
                ({_WELDING_USE_DRIVER_SQL})
                * COALESCE(l.qty_per, 0)
                / NULLIF(COALESCE(h.base_quantity, 1), 0)
                * (1 + COALESCE(l.scrap_rate, 0) / 100)
            ) AS required_qty
        FROM production_summarys ps
        JOIN product_bom_headers h
          ON h.id = (
              SELECT h2.id
              FROM product_bom_headers h2
              WHERE h2.parent_product_cd = ps.product_cd
                AND h2.status = 'active'
                AND (h2.effective_from IS NULL OR h2.effective_from <= ps.date)
                AND (h2.effective_to IS NULL OR h2.effective_to >= ps.date)
              ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
              LIMIT 1
          )
        JOIN product_bom_lines l
          ON l.header_id = h.id
         AND l.component_product_cd IS NOT NULL
         AND TRIM(l.component_product_cd) <> ''
         AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
        WHERE {" AND ".join(conditions)}
        GROUP BY
            ps.date,
            COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)')
    """
    )

    result = await db.execute(dsql, params)
    rows = result.mappings().fetchall()
    out: Dict[Tuple[str, date], int] = {}
    for r in rows:
        cd = normalize_part_stock_cd(r.get("component_cd"))
        eff_d = calendar_date_only(r.get("eff_date"))
        if eff_d is None:
            continue
        rq = _usage_int(r.get("required_qty"))
        key = (cd, eff_d)
        out[key] = rq
    return out


async def fetch_part_daily_usage_plan_from_welding_actual_plan(
    db: AsyncSession,
    d_start: date,
    d_end: date,
) -> Dict[Tuple[str, date], int]:
    """
    production_summarys.molding_actual_plan × BOM（部品行）から部品CD・日付ごとの使用計画数量を集計。
    ComponentRequirements「日別・部品別需要」と同一の式を part_stock.usage_plan_qty の同期ソースにする。
    """
    conditions = [
        "ps.date >= :d_start",
        "ps.date <= :d_end",
    ]
    params = {"d_start": d_start, "d_end": d_end}

    dsql = text(
        f"""
        SELECT
            ps.date AS eff_date,
            COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)') AS component_cd,
            SUM(
                ({_MOLDING_ACTUAL_PLAN_DRIVER_SQL})
                * COALESCE(l.qty_per, 0)
                / NULLIF(COALESCE(h.base_quantity, 1), 0)
                * (1 + COALESCE(l.scrap_rate, 0) / 100)
            ) AS required_qty
        FROM production_summarys ps
        JOIN product_bom_headers h
          ON h.id = (
              SELECT h2.id
              FROM product_bom_headers h2
              WHERE h2.parent_product_cd = ps.product_cd
                AND h2.status = 'active'
                AND (h2.effective_from IS NULL OR h2.effective_from <= ps.date)
                AND (h2.effective_to IS NULL OR h2.effective_to >= ps.date)
              ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
              LIMIT 1
          )
        JOIN product_bom_lines l
          ON l.header_id = h.id
         AND l.component_product_cd IS NOT NULL
         AND TRIM(l.component_product_cd) <> ''
         AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
        WHERE {" AND ".join(conditions)}
        GROUP BY
            ps.date,
            COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)')
    """
    )

    result = await db.execute(dsql, params)
    rows = result.mappings().fetchall()
    out: Dict[Tuple[str, date], int] = {}
    for r in rows:
        cd = normalize_part_stock_cd(r.get("component_cd"))
        eff_d = calendar_date_only(r.get("eff_date"))
        if eff_d is None:
            continue
        rq = _usage_int(r.get("required_qty"))
        key = (cd, eff_d)
        out[key] = rq
    return out
