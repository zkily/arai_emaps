"""生産検討会資料向け：生産性分析と同口径の月次総合能率（本/時）"""
from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any, Callable, Dict, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.production_schedule.api import (
    _finalize_inspection_productivity_bucket,
    _get_inspection_mgmt_columns,
    _get_welding_mgmt_columns,
    _inspection_mgmt_mes_select_fragment,
    _inspection_row_net_production_sec,
    _merge_inspection_productivity_bucket,
    _normalize_inspection_mgmt_row,
    _welding_mgmt_mes_select_fragment,
    _welding_row_net_production_sec,
)
from app.modules.production_schedule.cutting_productivity_api import (
    _cutting_row_work_sec,
    _normalize_cutting_row,
)
from app.modules.production_schedule.forming_productivity_api import (
    _forming_row_work_sec,
    _normalize_forming_row,
)
from app.modules.production_schedule.plating_productivity_api import (
    _normalize_plating_row,
    _plating_row_work_sec,
)

# performance row key -> 生産性分析データソース
_INDICATOR_SOURCES: Dict[str, Tuple[str, Callable[[dict[str, Any]], int], Callable[[dict[str, Any]], dict[str, Any]]]] = {
    "cutting": ("cutting_production_indicator", _cutting_row_work_sec, _normalize_cutting_row),
    "molding": ("forming_production_indicator", _forming_row_work_sec, _normalize_forming_row),
    "plating": ("plating_production_indicator", _plating_row_work_sec, _normalize_plating_row),
}


def _month_range(year: int, month: int) -> Tuple[date, date]:
    last = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


async def _aggregate_indicator_month(
    db: AsyncSession,
    table: str,
    work_sec_fn: Callable[[dict[str, Any]], int],
    normalize_fn: Callable[[dict[str, Any]], dict[str, Any]],
    year: int,
    month: int,
) -> Optional[int]:
    start_d, end_d = _month_range(year, month)
    sql = text(
        f"SELECT * FROM `{table}` "
        "WHERE production_day >= :start_date AND production_day <= :end_date "
        "LIMIT 50000"
    )
    try:
        rows = (await db.execute(sql, {"start_date": start_d, "end_date": end_d})).mappings().all()
    except Exception:
        return None
    bucket: dict[str, Any] = {
        "session_count": 0,
        "completed_session_count": 0,
        "sum_actual_qty": 0,
        "sum_defect_qty": 0,
        "sum_net_production_sec": 0,
    }
    for row in rows:
        item = normalize_fn(dict(row))
        actual_qty = int(item.get("actual_quantity") or 0)
        defect_qty = int(item.get("quantity_variance") or item.get("defect_quantity") or 0)
        net_sec = work_sec_fn(item)
        if actual_qty <= 0 and net_sec <= 0:
            continue
        _merge_inspection_productivity_bucket(
            bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=1,
        )
    finalized = _finalize_inspection_productivity_bucket(bucket)
    eff = finalized.get("efficiency_per_hour")
    return int(eff) if eff is not None else None


async def _aggregate_inspection_month(db: AsyncSession, year: int, month: int) -> Optional[int]:
    im_cols = await _get_inspection_mgmt_columns(db)
    if not im_cols:
        return None
    start_d, end_d = _month_range(year, month)
    mes_frag = _inspection_mgmt_mes_select_fragment(im_cols)
    where_parts = [
        "inspection_management.production_day >= :start_date",
        "inspection_management.production_day <= :end_date",
    ]
    if "production_completed_check" in im_cols:
        where_parts.append("inspection_management.production_completed_check = 1")
    sql = text(
        f"""
        SELECT inspection_management.actual_production_quantity,
               inspection_management.defect_qty,
               {mes_frag}
               inspection_management.production_day
        FROM inspection_management
        WHERE {' AND '.join(where_parts)}
        LIMIT 50000
        """
    )
    try:
        rows = (await db.execute(sql, {"start_date": start_d, "end_date": end_d})).mappings().all()
    except Exception:
        return None
    bucket: dict[str, Any] = {
        "session_count": 0,
        "completed_session_count": 0,
        "sum_actual_qty": 0,
        "sum_defect_qty": 0,
        "sum_net_production_sec": 0,
    }
    for row in rows:
        item = _normalize_inspection_mgmt_row(dict(row))
        actual_qty = int(item.get("actual_production_quantity") or 0)
        defect_qty = int(item.get("defect_qty") or 0)
        net_sec = _inspection_row_net_production_sec(item)
        if actual_qty <= 0 and net_sec <= 0:
            continue
        _merge_inspection_productivity_bucket(
            bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=1,
        )
    finalized = _finalize_inspection_productivity_bucket(bucket)
    eff = finalized.get("efficiency_per_hour")
    return int(eff) if eff is not None else None


async def _aggregate_welding_month(db: AsyncSession, year: int, month: int) -> Optional[int]:
    wm_cols = await _get_welding_mgmt_columns(db)
    if not wm_cols:
        return None
    start_d, end_d = _month_range(year, month)
    mes_frag = _welding_mgmt_mes_select_fragment(wm_cols)
    where_parts = [
        "welding_management.production_day >= :start_date",
        "welding_management.production_day <= :end_date",
    ]
    if "production_completed_check" in wm_cols:
        where_parts.append("welding_management.production_completed_check = 1")
    sql = text(
        f"""
        SELECT welding_management.actual_production_quantity,
               welding_management.defect_qty,
               {mes_frag}
               welding_management.production_day
        FROM welding_management
        WHERE {' AND '.join(where_parts)}
        LIMIT 50000
        """
    )
    try:
        rows = (await db.execute(sql, {"start_date": start_d, "end_date": end_d})).mappings().all()
    except Exception:
        return None
    bucket: dict[str, Any] = {
        "session_count": 0,
        "completed_session_count": 0,
        "sum_actual_qty": 0,
        "sum_defect_qty": 0,
        "sum_net_production_sec": 0,
    }
    for row in rows:
        item = dict(row)
        actual_qty = int(item.get("actual_production_quantity") or 0)
        defect_qty = int(item.get("defect_qty") or 0)
        net_sec = _welding_row_net_production_sec(item)
        if actual_qty <= 0 and net_sec <= 0:
            continue
        _merge_inspection_productivity_bucket(
            bucket,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            net_sec=net_sec,
            completed_count=1,
        )
    finalized = _finalize_inspection_productivity_bucket(bucket)
    eff = finalized.get("efficiency_per_hour")
    return int(eff) if eff is not None else None


async def get_process_monthly_efficiency(
    db: AsyncSession,
    process_key: str,
    year: int,
    month: int,
) -> Optional[int]:
    """指定月の総合能率（個/時 or 本/時）。出荷数は None。"""
    if process_key == "shipping":
        return None
    if process_key in _INDICATOR_SOURCES:
        table, work_fn, norm_fn = _INDICATOR_SOURCES[process_key]
        return await _aggregate_indicator_month(db, table, work_fn, norm_fn, year, month)
    if process_key == "inspection":
        return await _aggregate_inspection_month(db, year, month)
    if process_key == "welding":
        return await _aggregate_welding_month(db, year, month)
    return None


async def get_process_monthly_efficiency_map(
    db: AsyncSession,
    year: int,
    month: int,
) -> Dict[str, Optional[int]]:
    keys = ("cutting", "molding", "plating", "welding", "inspection")
    out: Dict[str, Optional[int]] = {"shipping": None}
    for key in keys:
        out[key] = await get_process_monthly_efficiency(db, key, year, month)
    return out
