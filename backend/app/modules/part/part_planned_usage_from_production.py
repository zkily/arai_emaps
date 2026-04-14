"""
production_summarys × 製品 BOM（部品行）から部品コード・日付ごとの数量を集計する。

- 使用数: 溶接実績（welding_actual + welding_defect）駆動（在庫計算の planned_usage）
- 使用計画: welding_actual_plan 駆動（在庫計算の usage_plan_qty）
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ユーザー入力不可（SQL インジェクション対策のため定数のみ使用）
_WELDING_USE_DRIVER_SQL = "(COALESCE(ps.welding_actual, 0) + COALESCE(ps.welding_defect, 0))"
_WELDING_ACTUAL_PLAN_DRIVER_SQL = "COALESCE(ps.welding_actual_plan, 0)"


def _usage_int(v) -> int:
    if v is None:
        return 0
    if isinstance(v, Decimal):
        return int(round(float(v)))
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return 0


async def fetch_part_daily_usage_from_production_summarys(
    db: AsyncSession,
    d_start: date,
    d_end: date,
) -> Dict[Tuple[str, date], int]:
    """
    戻り: (部品CD, 日付) -> 使用数（整数）
    部品CD は BOM 集計と同じく TRIM 後の component_product_cd（空は '(未設定)'）。
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
        cd = (r.get("component_cd") or "").strip()
        eff = r.get("eff_date")
        if eff is None:
            continue
        if isinstance(eff, datetime):
            eff_d = eff.date()
        elif isinstance(eff, date):
            eff_d = eff
        else:
            eff_d = date.fromisoformat(str(eff)[:10])
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
    production_summarys.welding_actual_plan × BOM（部品行）から部品CD・日付ごとの使用計画数量を集計。
    part_stock.usage_plan_qty の同期ソースとする。
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
                ({_WELDING_ACTUAL_PLAN_DRIVER_SQL})
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
        cd = (r.get("component_cd") or "").strip()
        eff = r.get("eff_date")
        if eff is None:
            continue
        if isinstance(eff, datetime):
            eff_d = eff.date()
        elif isinstance(eff, date):
            eff_d = eff
        else:
            eff_d = date.fromisoformat(str(eff)[:10])
        rq = _usage_int(r.get("required_qty"))
        key = (cd, eff_d)
        out[key] = rq
    return out


def normalize_part_stock_cd(part_cd: str | None) -> str:
    s = (part_cd or "").strip()
    return s if s else "(未設定)"
