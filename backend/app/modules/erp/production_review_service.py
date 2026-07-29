"""生産検討会資料 集計サービス"""
from __future__ import annotations

import calendar
import json
import re
from calendar import monthrange
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.company_work_calendar import count_scheduled_workdays, load_company_calendar_sets
from app.modules.budget.models import BudgetWorkingDays
from app.modules.database.models import ProductionSummary
from app.modules.erp.models import OrderMonthly
from app.modules.erp.inventory_report_api import _month_scrap_metrics
from app.modules.erp.production_review_models import ProductionReviewCapacity
from app.modules.erp.production_review_productivity import get_process_monthly_efficiency_map
from app.modules.master.models import ProductRouteStep

# 実績一覧に出す工程（PPT 準拠）
_PERFORMANCE_PROCESSES: Tuple[Tuple[str, str, Optional[str], Optional[str]], ...] = (
    ("shipping", "出荷数", None, "warehouse_actual"),
    ("cutting", "切断", "cutting_plan", "cutting_actual"),
    ("molding", "成型", "molding_plan", "molding_actual"),
    ("plating", "メッキ", "plating_plan", "plating_actual"),
    ("welding", "溶接", "welding_plan", "welding_actual"),
    ("inspection", "検査", "inspection_plan", "inspection_actual"),
)

# 在庫表に出す仕掛工程（複数列合算）
# 切断=切断+面取 / 成型=成型 /
# メッキ → 社内メッキ=メッキ+溶接前検査 / 外注メッキ=外注メッキ+外注検査前 /
# 溶接 → 社内溶接=溶接 / 外注溶接=外注溶接+外注支給前
_WIP_LEAF_GROUPS: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("cutting", "切断", ("cutting_inventory", "chamfering_inventory")),
    ("molding", "成型", ("molding_inventory",)),
    (
        "plating_inhouse",
        "社内メッキ",
        ("plating_inventory", "pre_welding_inspection_inventory"),
    ),
    (
        "plating_outsource",
        "外注メッキ",
        ("outsourced_plating_inventory", "pre_outsourcing_inventory"),
    ),
    ("welding_inhouse", "社内溶接", ("welding_inventory",)),
    (
        "welding_outsource",
        "外注溶接",
        ("outsourced_welding_inventory", "pre_inspection_inventory"),
    ),
)

# 親行 key → 子 key 一覧（展開表示用）
_WIP_PARENT_CHILDREN: Dict[str, Tuple[str, ...]] = {
    "plating": ("plating_inhouse", "plating_outsource"),
    "welding": ("welding_inhouse", "welding_outsource"),
}
_WIP_PARENT_NAMES: Dict[str, str] = {
    "plating": "メッキ",
    "welding": "溶接",
}
_WIP_TOP_ORDER: Tuple[str, ...] = (
    "cutting",
    "molding",
    "plating",
    "welding",
)

# 工程別内示（分母）＝出荷内示を product_route_steps で按分。
# None = 全量出荷内示（成型・製品）。複数 KT は製品ユニオン（二重計上しない）。
_LEAF_ROUTE_PROCESS_CDS: Dict[str, Optional[Tuple[str, ...]]] = {
    "cutting": ("KT01", "KT02"),
    "molding": None,
    "plating_inhouse": ("KT05",),
    "plating_outsource": ("KT06",),
    "welding_inhouse": ("KT07",),
    "welding_outsource": ("KT08",),
}

# 製品 = 検査 + 倉庫 + 外注倉庫
_PRODUCT_INVENTORY_COLS: Tuple[str, ...] = (
    "inspection_inventory",
    "warehouse_inventory",
    "outsourced_warehouse_inventory",
)

# 負荷率表に出す工程（PPT 準拠）
_LOAD_PLAN_PROCESS_CDS: Tuple[str, ...] = (
    "cutting",
    "chamfering",
    "molding",
    "plating",
    "inspection",
    "welding",
    "welding_sp",
)

_PLAN_COL_BY_CD: Dict[str, str] = {
    "cutting": "cutting_plan",
    "chamfering": "chamfering_plan",
    "molding": "molding_plan",
    "plating": "plating_plan",
    "inspection": "inspection_plan",
    "welding": "welding_plan",
    "welding_sp": "welding_plan",
}

# 溶接SP：製品名が該当するものの welding_plan を集計（それ以外は通常溶接）
_WELDING_SP_PRODUCT_NAMES: Tuple[str, ...] = ("CH2 RR", "FE-7")


def _parse_month(target_month: str) -> Tuple[int, int]:
    parts = target_month.strip().split("-")
    if len(parts) != 2:
        raise ValueError("target_month は YYYY-MM 形式で指定してください")
    return int(parts[0]), int(parts[1])


def _month_label(year: int, month: int) -> str:
    return f"{year}年{month}月"


def _shift_month(year: int, month: int, delta: int) -> Tuple[int, int]:
    m = year * 12 + (month - 1) + delta
    return m // 12, m % 12 + 1


def _month_range(year: int, month: int) -> Tuple[date, date]:
    last = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def _fiscal_year(d: date) -> int:
    return d.year if d.month >= 4 else d.year - 1


def _thousands(value: float | int | None, digits: int = 1) -> float:
    if value is None:
        return 0.0
    return round(float(value) / 1000.0, digits)


def _delta_fmt(value: float, digits: int = 1) -> str:
    rounded = round(value, digits)
    if rounded > 0:
        return f"{rounded:.{digits}f}"
    if rounded < 0:
        return f"△{abs(rounded):.{digits}f}"
    return f"{rounded:.{digits}f}"


def _productivity_delta_fmt(delta: float) -> str:
    rounded = round(delta)
    if rounded > 0:
        return f"+{rounded}"
    if rounded < 0:
        return f"△{abs(rounded)}"
    return "+0"


async def _sum_column(
    db: AsyncSession,
    col: str,
    start_d: date,
    end_d: date,
) -> int:
    sql = text(
        f"SELECT COALESCE(SUM(`{col}`), 0) AS total "
        "FROM production_summarys WHERE `date` BETWEEN :start AND :end"
    )
    row = (await db.execute(sql, {"start": start_d, "end": end_d})).mappings().first()
    return int(row["total"] or 0) if row else 0


async def _sum_welding_plan_split(
    db: AsyncSession,
    start_d: date,
    end_d: date,
    *,
    for_sp: bool,
) -> int:
    """溶接計画を製品名で分割。

    for_sp=True  → 製品名 IN (CH2 RR, FE-7)
    for_sp=False → 上記以外（TRIM 後の完全一致）
    """
    names = list(_WELDING_SP_PRODUCT_NAMES)
    placeholders = ", ".join(f":n{i}" for i in range(len(names)))
    op = "IN" if for_sp else "NOT IN"
    # NULL / 空文字は通常溶接側に含める
    null_clause = "" if for_sp else " OR TRIM(COALESCE(product_name, '')) = ''"
    sql = text(
        "SELECT COALESCE(SUM(`welding_plan`), 0) AS total "
        "FROM production_summarys "
        "WHERE `date` BETWEEN :start AND :end "
        f"AND (TRIM(COALESCE(product_name, '')) {op} ({placeholders}){null_clause})"
    )
    params: Dict[str, Any] = {"start": start_d, "end": end_d}
    for i, name in enumerate(names):
        params[f"n{i}"] = name
    row = (await db.execute(sql, params)).mappings().first()
    return int(row["total"] or 0) if row else 0


async def _last_day_inventory(
    db: AsyncSession,
    cols: Union[str, Sequence[str]],
    year: int,
    month: int,
) -> int:
    """月末（なければ月内最終日）の在庫本数。複数列指定時は合算。"""
    col_list = [cols] if isinstance(cols, str) else list(cols)
    if not col_list:
        return 0
    for c in col_list:
        if not c.replace("_", "").isalnum():
            raise ValueError(f"invalid inventory column: {c}")
    sum_expr = " + ".join(f"COALESCE(`{c}`, 0)" for c in col_list)
    _, end_d = _month_range(year, month)
    sql = text(
        f"SELECT COALESCE(SUM({sum_expr}), 0) AS total "
        "FROM production_summarys WHERE `date` = :d"
    )
    row = (await db.execute(sql, {"d": end_d})).mappings().first()
    if row and int(row["total"] or 0) > 0:
        return int(row["total"])
    # 月末データが無い場合は月内最終日
    sql2 = text(
        f"SELECT COALESCE(SUM({sum_expr}), 0) AS total "
        "FROM production_summarys WHERE `date` = ("
        "  SELECT MAX(`date`) FROM production_summarys "
        "  WHERE YEAR(`date`) = :y AND MONTH(`date`) = :m"
        ")"
    )
    row2 = (await db.execute(sql2, {"y": year, "m": month})).mappings().first()
    return int(row2["total"] or 0) if row2 else 0


async def _inventory_on_date(
    db: AsyncSession,
    cols: Union[str, Sequence[str]],
    as_of: date,
) -> int:
    """指定日の在庫本数。複数列指定時は合算。"""
    col_list = [cols] if isinstance(cols, str) else list(cols)
    if not col_list:
        return 0
    for c in col_list:
        if not c.replace("_", "").isalnum():
            raise ValueError(f"invalid inventory column: {c}")
    sum_expr = " + ".join(f"COALESCE(`{c}`, 0)" for c in col_list)
    sql = text(
        f"SELECT COALESCE(SUM({sum_expr}), 0) AS total "
        "FROM production_summarys WHERE `date` = :d"
    )
    row = (await db.execute(sql, {"d": as_of})).mappings().first()
    return int(row["total"] or 0) if row else 0


async def build_inventory_qty_map_for_date(
    db: AsyncSession,
    as_of: date,
) -> Dict[str, Any]:
    """指定日の工程別在庫（千本）。当月在庫列の基準日切替用。"""
    leaf_qty: Dict[str, int] = {}
    qty_th: Dict[str, float] = {}
    for key, _name, cols in _WIP_LEAF_GROUPS:
        qty = await _inventory_on_date(db, cols, as_of)
        leaf_qty[key] = qty
        qty_th[key] = _thousands(qty)

    for top_key, child_keys in _WIP_PARENT_CHILDREN.items():
        total = sum(leaf_qty.get(ck, 0) for ck in child_keys)
        qty_th[top_key] = _thousands(total)

    wip_total = sum(leaf_qty.values())
    qty_th["wip_total"] = _thousands(wip_total)

    product_qty = await _inventory_on_date(db, _PRODUCT_INVENTORY_COLS, as_of)
    qty_th["product"] = _thousands(product_qty)

    return {
        "date": as_of.isoformat(),
        "date_label": f"{as_of.year}年{as_of.month}月{as_of.day}日",
        "quantities_th": qty_th,
    }


async def _count_scheduled_workdays(
    db: AsyncSession,
    start_d: date,
    end_d: date,
) -> int:
    if start_d > end_d:
        return 0
    scheduled, off = await load_company_calendar_sets(db, start_d, end_d)
    return count_scheduled_workdays(
        start_d,
        end_d,
        company_scheduled=scheduled,
        company_off=off,
        extra_workdays=set(),
        extra_holidays=set(),
    )


async def _daily_actual_totals(
    db: AsyncSession,
    actual_col: str,
    start_d: date,
    end_d: date,
) -> List[Tuple[date, int]]:
    sql = text(
        f"SELECT `date` AS day, COALESCE(SUM(`{actual_col}`), 0) AS total "
        "FROM production_summarys WHERE `date` BETWEEN :start AND :end "
        "GROUP BY `date` ORDER BY `date`"
    )
    rows = (await db.execute(sql, {"start": start_d, "end": end_d})).mappings().all()
    out: List[Tuple[date, int]] = []
    for row in rows:
        d = row["day"]
        if isinstance(d, date):
            day = d
        else:
            day = date.fromisoformat(str(d)[:10])
        out.append((day, int(row["total"] or 0)))
    return out


async def _compute_process_jitsumi(
    db: AsyncSession,
    year: int,
    month: int,
    actual_col: str,
) -> int:
    """
    実見（本）= 当月実績合計 + 残り稼働日数 × 当月実績の日平均。
    日平均 = 実績合計 ÷ 実績が発生した稼働日数（月初～最終実績日）。
    残り稼働日 = 最終実績日の翌日～月末の稼働日数。
    """
    start_d, end_d = _month_range(year, month)
    daily_rows = await _daily_actual_totals(db, actual_col, start_d, end_d)
    actual_total = sum(qty for _, qty in daily_rows)
    if actual_total <= 0:
        return 0

    production_days = [day for day, qty in daily_rows if qty > 0]
    if not production_days:
        return 0

    last_actual_day = max(production_days)
    total_workdays = await _working_days(db, year, month)
    if total_workdays <= 0:
        return actual_total

    # 当月実績の日平均（稼働日ベース）
    avg_daily = actual_total / float(total_workdays)
    elapsed_workdays = await _count_scheduled_workdays(db, start_d, last_actual_day)
    remaining_workdays = max(0, total_workdays - elapsed_workdays)

    return int(round(actual_total + remaining_workdays * avg_daily))


async def _compute_shipping_jitsumi(
    db: AsyncSession,
    year: int,
    month: int,
) -> int:
    """出荷数の実見 = production_summarys.forecast_quantity 月合計。"""
    start_d, end_d = _month_range(year, month)
    return await _sum_column(db, "forecast_quantity", start_d, end_d)


async def _forecast_units(db: AsyncSession, year: int, month: int) -> int:
    q = select(func.coalesce(func.sum(OrderMonthly.forecast_units), 0)).where(
        OrderMonthly.year == year,
        OrderMonthly.month == month,
    )
    return int((await db.execute(q)).scalar() or 0)


async def _working_days(db: AsyncSession, year: int, month: int) -> int:
    q = select(BudgetWorkingDays).where(
        BudgetWorkingDays.year == year,
        BudgetWorkingDays.month == month,
    )
    row = (await db.execute(q)).scalar_one_or_none()
    if row and int(row.working_days or 0) > 0:
        return int(row.working_days)
    start_d, end_d = _month_range(year, month)
    try:
        scheduled, off = await load_company_calendar_sets(db, start_d, end_d)
        return count_scheduled_workdays(
            start_d,
            end_d,
            company_scheduled=scheduled,
            company_off=off,
            extra_workdays=set(),
            extra_holidays=set(),
        )
    except Exception:
        # 土日除外の簡易カウント
        days = 0
        for d in range(1, monthrange(year, month)[1] + 1):
            wd = date(year, month, d).weekday()
            if wd < 5:
                days += 1
        return days


async def _scrap_month_entry(db: AsyncSession, year: int, month: int) -> Dict[str, Any]:
    """在庫報告管理と同一の廃棄率（新・旧）・廃棄本数（不良＋廃棄）。"""
    start_d, end_d = _month_range(year, month)
    metrics = await _month_scrap_metrics(db, start_d, end_d)
    rate_new = metrics.get("quality_loss_rate_percent")
    rate_old = metrics.get("all_process_loss_rate_percent")
    loss_qty = int(metrics.get("sum_defect_and_scrap") or 0)
    rate_new_val = round(float(rate_new), 2) if rate_new is not None else 0.0
    rate_old_val = round(float(rate_old), 2) if rate_old is not None else 0.0
    loss_th = _thousands(loss_qty)
    return {
        "year": year,
        "month": month,
        "rate_new_pct": rate_new_val,
        "rate_old_pct": rate_old_val,
        "loss_qty": loss_qty,
        "loss_th": loss_th,
        # 旧キー互換
        "scrap_th": loss_th,
        "rate_pct": rate_old_val,
    }


_DEFAULT_UTILIZATION_RATE_PCT = 96.0  # 定時H用稼働率(%)のデフォルト


def _normalize_utilization_rate_pct(value: Any) -> float:
    """稼働率(%)を 0〜100 に正規化。未設定時は 96。"""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return float(_DEFAULT_UTILIZATION_RATE_PCT)
    if n <= 0:
        return float(_DEFAULT_UTILIZATION_RATE_PCT)
    if n > 100:
        return 100.0
    return round(n, 2)


async def get_capacity_rows(db: AsyncSession) -> List[Dict[str, Any]]:
    rows = list(
        (
            await db.execute(
                select(ProductionReviewCapacity).order_by(
                    ProductionReviewCapacity.sort_order,
                    ProductionReviewCapacity.id,
                )
            )
        ).scalars().all()
    )
    if rows:
        return [
            {
                "process_cd": r.process_cd,
                "process_name": r.process_name,
                "equipment_label": r.equipment_label or "",
                "standard_rate": int(r.standard_rate or 0),
                "shift_label": r.shift_label or "",
                "working_days": int(getattr(r, "working_days", 0) or 0),
                "utilization_rate_pct": _normalize_utilization_rate_pct(
                    getattr(r, "utilization_rate_pct", None)
                ),
                "daily_regular_hours": int(r.daily_regular_hours or 0),
                "sort_order": int(r.sort_order or 0),
            }
            for r in rows
        ]
    return []


async def upsert_capacity_rows(db: AsyncSession, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for it in items:
        cd = str(it.get("process_cd") or "").strip()
        if not cd:
            continue
        row = (
            await db.execute(
                select(ProductionReviewCapacity).where(ProductionReviewCapacity.process_cd == cd)
            )
        ).scalar_one_or_none()
        util_pct = _normalize_utilization_rate_pct(it.get("utilization_rate_pct"))
        payload = {
            "process_name": str(it.get("process_name") or cd),
            "equipment_label": str(it.get("equipment_label") or ""),
            "standard_rate": int(it.get("standard_rate") or 0),
            "shift_label": str(it.get("shift_label") or ""),
            "working_days": max(0, min(31, int(it.get("working_days") or 0))),
            "utilization_rate_pct": util_pct,
            "daily_regular_hours": int(it.get("daily_regular_hours") or 0),
            "sort_order": int(it.get("sort_order") or 0),
        }
        computed_daily = _calc_daily_regular_hours(
            payload["equipment_label"],
            payload["shift_label"],
            util_pct,
        )
        if computed_daily > 0:
            payload["daily_regular_hours"] = int(round(computed_daily))
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(ProductionReviewCapacity(process_cd=cd, **payload))
    await db.commit()
    return await get_capacity_rows(db)


def _build_performance_row(
    *,
    key: str,
    name: str,
    plan_th: float,
    forecast_th: float,
    actual_th: float,
    prev_productivity: Optional[float],
    curr_productivity: Optional[float],
) -> Dict[str, Any]:
    vs_forecast = forecast_th - plan_th  # 対実見 = 実見 - 工程計画
    vs_plan = actual_th - plan_th  # 対計画 = 実績 - 工程計画
    prod_prev = prev_productivity if prev_productivity is not None else None
    prod_curr = curr_productivity if curr_productivity is not None else None
    prod_delta = None
    if prod_prev is not None and prod_curr is not None:
        prod_delta = prod_curr - prod_prev
    return {
        "key": key,
        "name": name,
        "plan_th": plan_th,
        "forecast_th": forecast_th,
        "actual_th": actual_th,
        "vs_forecast_th": vs_forecast,
        "vs_plan_th": vs_plan,
        "productivity_prev": prod_prev,
        "productivity_curr": prod_curr,
        "productivity_delta": prod_delta,
    }


async def _build_performance_table(
    db: AsyncSession,
    year: int,
    month: int,
) -> Dict[str, Any]:
    start_d, end_d = _month_range(year, month)
    prev_py, prev_pm = _shift_month(year, month, -1)
    prod_prev_map = await get_process_monthly_efficiency_map(db, prev_py, prev_pm)
    prod_curr_map = await get_process_monthly_efficiency_map(db, year, month)
    rows: List[Dict[str, Any]] = []
    for key, name, plan_col, actual_col in _PERFORMANCE_PROCESSES:
        if key == "shipping":
            plan_qty = await _forecast_units(db, year, month)
            actual_qty = await _sum_column(db, actual_col, start_d, end_d)
            forecast_qty = await _compute_shipping_jitsumi(db, year, month)
            prod_prev = None
            prod_curr = None
        else:
            plan_qty = await _sum_column(db, plan_col, start_d, end_d) if plan_col else 0
            actual_qty = await _sum_column(db, actual_col, start_d, end_d) if actual_col else 0
            forecast_qty = await _compute_process_jitsumi(db, year, month, actual_col)
            prod_prev = prod_prev_map.get(key)
            prod_curr = prod_curr_map.get(key)
        rows.append(
            _build_performance_row(
                key=key,
                name=name,
                plan_th=_thousands(plan_qty),
                forecast_th=_thousands(forecast_qty),
                actual_th=_thousands(actual_qty),
                prev_productivity=prod_prev,
                curr_productivity=prod_curr,
            )
        )
    return {
        "month": f"{year:04d}-{month:02d}",
        "month_label": _month_label(year, month),
        "rows": rows,
        "comments": _generate_performance_comments(
            {"month_label": _month_label(year, month), "rows": rows}
        ),
    }


def _fiscal_months_from_april_to(end_year: int, end_month: int) -> List[Tuple[int, int]]:
    """当年度4月から end_year/end_month までの (year, month) 一覧。"""
    fy = _fiscal_year(date(end_year, end_month, 1))
    y, m = fy, 4
    out: List[Tuple[int, int]] = []
    while (y, m) <= (end_year, end_month):
        out.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


async def _build_scrap_section(db: AsyncSession, end_year: int, end_month: int) -> Dict[str, Any]:
    """廃棄率・廃棄本数：当年度4月〜対象月（検討会対象月）までを集計。"""
    fy = _fiscal_year(date(end_year, end_month, 1))
    fiscal_months = _fiscal_months_from_april_to(end_year, end_month)
    monthly: List[Dict[str, Any]] = []
    fy_rates_new: List[float] = []
    fy_rates_old: List[float] = []
    prev_fy_rates_new: List[float] = []
    prev_fy_rates_old: List[float] = []
    fy_losses: List[int] = []
    prev_fy_losses: List[int] = []

    for y, m in fiscal_months:
        entry = await _scrap_month_entry(db, y, m)
        monthly.append(entry)
        fy_rates_new.append(entry["rate_new_pct"])
        fy_rates_old.append(entry["rate_old_pct"])
        fy_losses.append(entry["loss_qty"])
        prev_entry = await _scrap_month_entry(db, y - 1, m)
        prev_fy_rates_new.append(prev_entry["rate_new_pct"])
        prev_fy_rates_old.append(prev_entry["rate_old_pct"])
        prev_fy_losses.append(prev_entry["loss_qty"])

    curr_rate_new = fy_rates_new[-1] if fy_rates_new else 0.0
    curr_rate_old = fy_rates_old[-1] if fy_rates_old else 0.0
    curr_loss = fy_losses[-1] if fy_losses else 0
    avg_rate_new_curr = sum(fy_rates_new) / len(fy_rates_new) if fy_rates_new else 0.0
    avg_rate_old_curr = sum(fy_rates_old) / len(fy_rates_old) if fy_rates_old else 0.0
    avg_rate_new_prev = sum(prev_fy_rates_new) / len(prev_fy_rates_new) if prev_fy_rates_new else 0.0
    avg_rate_old_prev = sum(prev_fy_rates_old) / len(prev_fy_rates_old) if prev_fy_rates_old else 0.0
    avg_loss_curr = sum(fy_losses) / len(fy_losses) if fy_losses else 0
    avg_loss_prev = sum(prev_fy_losses) / len(prev_fy_losses) if prev_fy_losses else 0

    start_m = monthly[0]["month"] if monthly else 4
    end_m = monthly[-1]["month"] if monthly else end_month
    range_label = f"{start_m}月〜{end_m}月" if monthly else ""

    out = {
        "monthly": monthly,
        "fiscal_year": fy,
        "fiscal_year_label": f"{fy}年度",
        "range_label": range_label,
        "current_month_rate_new_pct": round(curr_rate_new, 2),
        "current_month_rate_old_pct": round(curr_rate_old, 2),
        "current_month_loss_qty": curr_loss,
        "current_month_loss_th": _thousands(curr_loss),
        "avg_rate_new_current_fy_pct": round(avg_rate_new_curr, 2),
        "avg_rate_old_current_fy_pct": round(avg_rate_old_curr, 2),
        "avg_rate_new_prev_fy_pct": round(avg_rate_new_prev, 2),
        "avg_rate_old_prev_fy_pct": round(avg_rate_old_prev, 2),
        "avg_loss_current_fy_qty": int(round(avg_loss_curr)),
        "avg_loss_prev_fy_qty": int(round(avg_loss_prev)),
        "avg_loss_current_fy_th": round(_thousands(avg_loss_curr), 1),
        "avg_loss_prev_fy_th": round(_thousands(avg_loss_prev), 1),
        "improvement_rate_new_pt": round(avg_rate_new_prev - avg_rate_new_curr, 2),
        "improvement_rate_old_pt": round(avg_rate_old_prev - avg_rate_old_curr, 2),
        "improvement_loss_qty": int(round(avg_loss_prev - avg_loss_curr)),
        # 旧キー互換
        "current_month_rate_pct": round(curr_rate_old, 2),
        "current_month_scrap_th": _thousands(curr_loss),
        "avg_rate_current_fy_pct": round(avg_rate_old_curr, 2),
        "avg_rate_prev_fy_pct": round(avg_rate_old_prev, 2),
        "avg_scrap_current_fy_th": round(_thousands(avg_loss_curr), 1),
        "avg_scrap_prev_fy_th": round(_thousands(avg_loss_prev), 1),
        "improvement_rate_pt": round(avg_rate_old_prev - avg_rate_old_curr, 2),
        "improvement_scrap_th": round(_thousands(avg_loss_prev - avg_loss_curr), 1),
        "comments": [],
    }
    out["comments"] = _generate_scrap_comments(out)
    return out


# 在庫率補正用の標準稼働日（月）／工程別安全水位（補正率）
_STANDARD_WORKDAYS = 20
_PROCESS_TARGET_RATES: Dict[str, float] = {
    "cutting": 0.15,
    "molding": 0.15,
    "plating": 0.19,
    "plating_inhouse": 0.19,
    "plating_outsource": 0.19,
    "welding": 0.19,
    "welding_inhouse": 0.19,
    "welding_outsource": 0.19,
    "product": 0.36,
}
_PRODUCT_TARGET_RATE = _PROCESS_TARGET_RATES["product"]
_PRODUCT_TARGET_DAYS = round(_PRODUCT_TARGET_RATE * _STANDARD_WORKDAYS, 1)  # 7.2日
_PROCESS_TARGET_DAYS: Dict[str, float] = {
    k: round(v * _STANDARD_WORKDAYS, 1) for k, v in _PROCESS_TARGET_RATES.items()
}


def _adjusted_forecast_units(forecast: int, workdays: int, standard: int = _STANDARD_WORKDAYS) -> float:
    """稼働日補正内示：短月の内示を標準月強度に換算。"""
    if forecast <= 0:
        return 0.0
    if workdays <= 0:
        return float(forecast)
    return float(forecast) * (standard / workdays)


def _inventory_rate_and_days(
    qty: float,
    forecast: float,
    adj_forecast: float,
    workdays: int,
) -> Tuple[float, float, float]:
    """(在庫率, 補正在庫率, 在庫日数) を返す。数量は本単位。"""
    rate = (qty / forecast) if forecast > 0 else 0.0
    rate_adj = (qty / adj_forecast) if adj_forecast > 0 else 0.0
    daily = (forecast / workdays) if workdays > 0 and forecast > 0 else 0.0
    days = (qty / daily) if daily > 0 else 0.0
    return round(rate, 2), round(rate_adj, 2), round(days, 1)


def _inventory_row(
    *,
    key: str,
    name: str,
    prev_qty: int,
    curr_qty: int,
    prev_forecast: float,
    curr_forecast: float,
    prev_adj: float,
    curr_adj: float,
    prev_wd: int,
    curr_wd: int,
) -> Dict[str, Any]:
    prev_rate, prev_rate_adj, prev_days = _inventory_rate_and_days(
        prev_qty, prev_forecast, prev_adj, prev_wd
    )
    curr_rate, curr_rate_adj, curr_days = _inventory_rate_and_days(
        curr_qty, curr_forecast, curr_adj, curr_wd
    )
    return {
        "key": key,
        "name": name,
        "prev_inventory_th": _thousands(prev_qty),
        "prev_rate": prev_rate,
        "prev_rate_adj": prev_rate_adj,
        "prev_days": prev_days,
        "curr_inventory_th": _thousands(curr_qty),
        "curr_rate": curr_rate,
        "curr_rate_adj": curr_rate_adj,
        "curr_days": curr_days,
        "delta_th": _thousands(curr_qty - prev_qty),
        # 行ごとの工程内示（千本）— 率・日数の分母
        "prev_forecast_th": _thousands(prev_forecast),
        "curr_forecast_th": _thousands(curr_forecast),
        "prev_forecast_adj_th": _thousands(prev_adj),
        "curr_forecast_adj_th": _thousands(curr_adj),
    }


def _iter_inventory_rows(rows: List[Dict[str, Any]]):
    for row in rows:
        yield row
        for child in row.get("children") or []:
            yield child


async def _sum_route_allocated_forecast(
    db: AsyncSession,
    year: int,
    month: int,
    process_cds: Optional[Sequence[str]],
) -> int:
    """出荷内示を product_route_steps で工程按分（月受注サマリーと同一ロジック）。

    process_cds=None → 全量（加工品除外）。
    複数 KT → 該当工程のいずれかを持つ製品のユニオン（二重計上なし）。
    """
    om = OrderMonthly
    prs = ProductRouteStep
    # order_process_totals_service.order_monthly_base_where と同一（循環 import 回避のため直書き）
    base = and_(
        (om.product_name.is_(None)) | (~om.product_name.like("%加工%")),
        om.year == year,
        om.month == month,
    )
    q = select(func.coalesce(func.sum(om.forecast_units), 0)).select_from(om).where(base)
    if process_cds:
        subq = select(prs.product_cd).where(prs.process_cd.in_(list(process_cds))).distinct()
        q = q.where(om.product_cd.in_(subq))
    return int((await db.execute(q)).scalar() or 0)


def _route_forecast_pair(
    raw_prev: int,
    raw_curr: int,
    *,
    prev_wd: int,
    curr_wd: int,
) -> Tuple[float, float, float, float]:
    """工程按分内示（本）と稼働日補正内示。"""
    prev_f = float(raw_prev)
    curr_f = float(raw_curr)
    prev_adj = _adjusted_forecast_units(int(prev_f), prev_wd)
    curr_adj = _adjusted_forecast_units(int(curr_f), curr_wd)
    return prev_f, curr_f, prev_adj, curr_adj


def _resync_inventory_parent_row(
    parent: Dict[str, Any],
    *,
    prev_wd: int,
    curr_wd: int,
) -> None:
    children = parent.get("children") or []
    if not children:
        return
    prev_th = sum(float(c.get("prev_inventory_th") or 0) for c in children)
    curr_th = sum(float(c.get("curr_inventory_th") or 0) for c in children)
    prev_f_th = sum(float(c.get("prev_forecast_th") or 0) for c in children)
    curr_f_th = sum(float(c.get("curr_forecast_th") or 0) for c in children)
    prev_adj_th = sum(float(c.get("prev_forecast_adj_th") or 0) for c in children)
    curr_adj_th = sum(float(c.get("curr_forecast_adj_th") or 0) for c in children)
    prev_qty = prev_th * 1000
    curr_qty = curr_th * 1000
    prev_f = prev_f_th * 1000
    curr_f = curr_f_th * 1000
    prev_adj = prev_adj_th * 1000
    curr_adj = curr_adj_th * 1000
    prev_rate, prev_rate_adj, prev_days = _inventory_rate_and_days(
        prev_qty, prev_f, prev_adj, prev_wd
    )
    curr_rate, curr_rate_adj, curr_days = _inventory_rate_and_days(
        curr_qty, curr_f, curr_adj, curr_wd
    )
    parent["prev_inventory_th"] = round(prev_th, 1)
    parent["curr_inventory_th"] = round(curr_th, 1)
    parent["prev_forecast_th"] = round(prev_f_th, 1)
    parent["curr_forecast_th"] = round(curr_f_th, 1)
    parent["prev_forecast_adj_th"] = round(prev_adj_th, 1)
    parent["curr_forecast_adj_th"] = round(curr_adj_th, 1)
    parent["prev_rate"] = prev_rate
    parent["prev_rate_adj"] = prev_rate_adj
    parent["prev_days"] = prev_days
    parent["curr_rate"] = curr_rate
    parent["curr_rate_adj"] = curr_rate_adj
    parent["curr_days"] = curr_days
    parent["delta_th"] = round(curr_th - prev_th, 1)


def _recompute_inventory_row_metrics(
    row: Dict[str, Any],
    *,
    prev_wd: int,
    curr_wd: int,
) -> None:
    prev_th = float(row.get("prev_inventory_th") or 0)
    curr_th = float(row.get("curr_inventory_th") or 0)
    prev_f = float(row.get("prev_forecast_th") or 0) * 1000
    curr_f = float(row.get("curr_forecast_th") or 0) * 1000
    prev_adj = float(row.get("prev_forecast_adj_th") or 0) * 1000
    curr_adj = float(row.get("curr_forecast_adj_th") or 0) * 1000
    prev_rate, prev_rate_adj, prev_days = _inventory_rate_and_days(
        prev_th * 1000, prev_f, prev_adj, prev_wd
    )
    curr_rate, curr_rate_adj, curr_days = _inventory_rate_and_days(
        curr_th * 1000, curr_f, curr_adj, curr_wd
    )
    row["prev_rate"] = prev_rate
    row["prev_rate_adj"] = prev_rate_adj
    row["prev_days"] = prev_days
    row["curr_rate"] = curr_rate
    row["curr_rate_adj"] = curr_rate_adj
    row["curr_days"] = curr_days
    row["delta_th"] = round(curr_th - prev_th, 1)


async def _build_inventory_table(
    db: AsyncSession,
    inv_year: int,
    inv_month: int,
    prev_forecast_year: int,
    prev_forecast_month: int,
    curr_forecast_year: int,
    curr_forecast_month: int,
) -> Dict[str, Any]:
    ship_prev = await _sum_route_allocated_forecast(
        db, prev_forecast_year, prev_forecast_month, None
    )
    ship_curr = await _sum_route_allocated_forecast(
        db, curr_forecast_year, curr_forecast_month, None
    )
    prev_wd = await _working_days(db, prev_forecast_year, prev_forecast_month)
    curr_wd = await _working_days(db, curr_forecast_year, curr_forecast_month)
    ship_prev_adj = _adjusted_forecast_units(ship_prev, prev_wd)
    ship_curr_adj = _adjusted_forecast_units(ship_curr, curr_wd)
    prev_inv_year, prev_inv_month = _shift_month(inv_year, inv_month, -1)

    leaf_by_key: Dict[str, Dict[str, Any]] = {}
    leaf_qty: Dict[str, Tuple[int, int]] = {}
    for key, name, cols in _WIP_LEAF_GROUPS:
        prev_qty = await _last_day_inventory(db, cols, prev_inv_year, prev_inv_month)
        curr_qty = await _last_day_inventory(db, cols, inv_year, inv_month)
        leaf_qty[key] = (prev_qty, curr_qty)
        route_cds = _LEAF_ROUTE_PROCESS_CDS.get(key)
        # molding 等 None は全量出荷内示；キー未定義は空タプル扱い（0）
        if key not in _LEAF_ROUTE_PROCESS_CDS:
            raw_prev, raw_curr = 0, 0
        else:
            raw_prev = await _sum_route_allocated_forecast(
                db, prev_forecast_year, prev_forecast_month, route_cds
            )
            raw_curr = await _sum_route_allocated_forecast(
                db, curr_forecast_year, curr_forecast_month, route_cds
            )
        prev_f, curr_f, prev_adj, curr_adj = _route_forecast_pair(
            raw_prev,
            raw_curr,
            prev_wd=prev_wd,
            curr_wd=curr_wd,
        )
        leaf_by_key[key] = _inventory_row(
            key=key,
            name=name,
            prev_qty=prev_qty,
            curr_qty=curr_qty,
            prev_forecast=prev_f,
            curr_forecast=curr_f,
            prev_adj=prev_adj,
            curr_adj=curr_adj,
            prev_wd=prev_wd,
            curr_wd=curr_wd,
        )

    rows: List[Dict[str, Any]] = []
    wip_total_prev = 0
    wip_total_curr = 0
    for top_key in _WIP_TOP_ORDER:
        child_keys = _WIP_PARENT_CHILDREN.get(top_key)
        if child_keys:
            children = [leaf_by_key[ck] for ck in child_keys if ck in leaf_by_key]
            prev_qty = sum(leaf_qty[ck][0] for ck in child_keys if ck in leaf_qty)
            curr_qty = sum(leaf_qty[ck][1] for ck in child_keys if ck in leaf_qty)
            prev_f = sum(float(c.get("prev_forecast_th") or 0) * 1000 for c in children)
            curr_f = sum(float(c.get("curr_forecast_th") or 0) * 1000 for c in children)
            prev_adj = sum(float(c.get("prev_forecast_adj_th") or 0) * 1000 for c in children)
            curr_adj = sum(float(c.get("curr_forecast_adj_th") or 0) * 1000 for c in children)
            wip_total_prev += prev_qty
            wip_total_curr += curr_qty
            parent = _inventory_row(
                key=top_key,
                name=_WIP_PARENT_NAMES.get(top_key, top_key),
                prev_qty=prev_qty,
                curr_qty=curr_qty,
                prev_forecast=prev_f,
                curr_forecast=curr_f,
                prev_adj=prev_adj,
                curr_adj=curr_adj,
                prev_wd=prev_wd,
                curr_wd=curr_wd,
            )
            parent["children"] = children
            rows.append(parent)
        elif top_key in leaf_by_key:
            prev_qty, curr_qty = leaf_qty[top_key]
            leaf = leaf_by_key[top_key]
            wip_total_prev += prev_qty
            wip_total_curr += curr_qty
            rows.append(leaf)

    product_prev = await _last_day_inventory(
        db, _PRODUCT_INVENTORY_COLS, prev_inv_year, prev_inv_month
    )
    product_curr = await _last_day_inventory(db, _PRODUCT_INVENTORY_COLS, inv_year, inv_month)
    rows.append(
        _inventory_row(
            key="product",
            name="製品",
            prev_qty=product_prev,
            curr_qty=product_curr,
            prev_forecast=float(ship_prev),
            curr_forecast=float(ship_curr),
            prev_adj=ship_prev_adj,
            curr_adj=ship_curr_adj,
            prev_wd=prev_wd,
            curr_wd=curr_wd,
        )
    )
    rows.insert(
        len(_WIP_TOP_ORDER),
        _inventory_row(
            key="wip_total",
            name="仕掛品合計",
            prev_qty=wip_total_prev,
            curr_qty=wip_total_curr,
            # 分母は全量出荷内示（工程按分の合計ではない）
            prev_forecast=float(ship_prev),
            curr_forecast=float(ship_curr),
            prev_adj=ship_prev_adj,
            curr_adj=ship_curr_adj,
            prev_wd=prev_wd,
            curr_wd=curr_wd,
        ),
    )

    product_row = next((r for r in rows if r["key"] == "product"), None)
    product_curr_days = float(product_row["curr_days"]) if product_row else 0.0
    product_curr_rate_adj = float(product_row["curr_rate_adj"]) if product_row else 0.0
    if product_curr_days < _PRODUCT_TARGET_DAYS or product_curr_rate_adj < _PRODUCT_TARGET_RATE:
        product_level = "danger"
    elif product_curr_days > _PRODUCT_TARGET_DAYS * 2:
        product_level = "high"
    else:
        product_level = "ok"

    out = {
        "inventory_month": f"{inv_year:04d}-{inv_month:02d}",
        "inventory_month_label": _month_label(inv_year, inv_month),
        "prev_forecast_th": _thousands(ship_prev),
        "curr_forecast_th": _thousands(ship_curr),
        "prev_forecast_adj_th": _thousands(ship_prev_adj),
        "curr_forecast_adj_th": _thousands(ship_curr_adj),
        "prev_forecast_label": _month_label(prev_forecast_year, prev_forecast_month),
        "curr_forecast_label": _month_label(curr_forecast_year, curr_forecast_month),
        "prev_forecast_year": prev_forecast_year,
        "prev_forecast_month": prev_forecast_month,
        "curr_forecast_year": curr_forecast_year,
        "curr_forecast_month": curr_forecast_month,
        "prev_workdays": prev_wd,
        "curr_workdays": curr_wd,
        "standard_workdays": _STANDARD_WORKDAYS,
        "product_target_rate": _PRODUCT_TARGET_RATE,
        "product_target_days": _PRODUCT_TARGET_DAYS,
        "process_target_rates": dict(_PROCESS_TARGET_RATES),
        "process_target_days": dict(_PROCESS_TARGET_DAYS),
        "product_level": product_level,
        "curr_inventory_as_of": None,
        "rows": rows,
        "comments": [],
    }
    out["comments"] = _generate_inventory_comments(out)
    return out


_HOURS_PER_SHIFT = 7.6
_MAX_HOURS_PER_DAY = 24  # 設備稼働率の分母（暦日×24H）


def _parse_equipment_count(equipment_label: str) -> float:
    """設備・人員ラベル先頭の数値（例: 5.5台 / 11人 / 24ライン）。"""
    m = re.search(r"[\d.]+", (equipment_label or "").strip())
    if not m:
        return 0.0
    try:
        return float(m.group(0))
    except ValueError:
        return 0.0


def _parse_shift_count(shift_label: str) -> int:
    """稼働直ラベルの数値（例: 2直 → 2）。"""
    m = re.search(r"(\d+)", (shift_label or "").strip())
    return int(m.group(1)) if m else 0


def _is_personnel_equipment(equipment_label: str) -> bool:
    return "人" in (equipment_label or "")


def _calc_daily_regular_hours(
    equipment_label: str,
    shift_label: str,
    utilization_rate_pct: Any = None,
) -> float:
    """日当たり定時H = 設備数 × 直数 × 7.6H × 稼働率（人員は 人数 × 7.6H × 稼働率）。"""
    equip = _parse_equipment_count(equipment_label)
    if equip <= 0:
        return 0.0
    shifts = _parse_shift_count(shift_label) or 1
    util = _normalize_utilization_rate_pct(utilization_rate_pct) / 100.0
    if _is_personnel_equipment(equipment_label):
        return round(equip * _HOURS_PER_SHIFT * util, 2)
    return round(equip * shifts * _HOURS_PER_SHIFT * util, 2)


def _calc_equipment_utilization_pct(
    *,
    process_cd: str,
    equipment_label: str,
    required_hours: int,
    calendar_days: int,
) -> Optional[float]:
    """設備稼働率(%) = 所要H ÷ (設備数 × 月の暦日数 × 24H) × 100。

    検査工程は対象外（None）。
    """
    if process_cd == "inspection":
        return None
    equip = _parse_equipment_count(equipment_label)
    days = int(calendar_days or 0)
    denom = equip * days * _MAX_HOURS_PER_DAY
    if denom <= 0 or required_hours <= 0:
        return None
    return round(required_hours / denom * 100, 1)


def _calc_load_row(
    *,
    process_cd: str,
    process_name: str,
    plan_th: float,
    working_days: int,
    calendar_days: int,
    capacity: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ov = overrides or {}
    equipment = str(ov.get("equipment_label") or capacity.get("equipment_label") or "")
    std_rate = int(ov.get("standard_rate") or capacity.get("standard_rate") or 0)
    shift = str(ov.get("shift_label") or capacity.get("shift_label") or "")
    util_pct = _normalize_utilization_rate_pct(
        ov.get("utilization_rate_pct")
        if ov.get("utilization_rate_pct") is not None
        else capacity.get("utilization_rate_pct")
    )
    daily_reg_computed = _calc_daily_regular_hours(equipment, shift, util_pct)
    daily_reg_fallback = int(ov.get("daily_regular_hours") or capacity.get("daily_regular_hours") or 0)
    daily_reg = int(round(daily_reg_computed)) if daily_reg_computed > 0 else daily_reg_fallback
    cap_wd = int(capacity.get("working_days") or 0)
    wd = int(ov.get("working_days") or 0) or cap_wd or int(working_days or 0)
    cal_days = int(calendar_days or 0)
    daily_th = round(plan_th / wd, 1) if wd > 0 else 0.0
    regular_hours = int(round(daily_reg * wd)) if wd > 0 else 0
    plan_units = plan_th * 1000
    required_hours = int(round(plan_units / std_rate)) if std_rate > 0 else 0
    load_rate = int(round(required_hours / regular_hours * 100)) if regular_hours > 0 else 0
    equip_count = _parse_equipment_count(equipment)
    if wd > 0 and required_hours > 0 and equip_count > 0:
        daily_operation = round(required_hours / wd / equip_count, 1)
    else:
        daily_operation = 0.0
    return {
        "process_cd": process_cd,
        "process_name": process_name,
        "plan_th": plan_th,
        "daily_th": daily_th,
        "equipment_label": equipment,
        "standard_rate": std_rate,
        "shift_label": shift,
        "regular_hours": regular_hours,
        "required_hours": required_hours,
        "load_rate_pct": load_rate,
        "daily_operation_hours": daily_operation,
        "working_days": wd,
        "calendar_days": cal_days,
        "utilization_rate_pct": util_pct,
        "equipment_utilization_pct": _calc_equipment_utilization_pct(
            process_cd=process_cd,
            equipment_label=equipment,
            required_hours=required_hours,
            calendar_days=cal_days,
        ),
    }


def _recompute_load_row_dict(row: Dict[str, Any], plan_th: Optional[float] = None) -> Dict[str, Any]:
    """負荷計画行の plan_th 変更後、派生項目を再計算する。"""
    pt = round(float(plan_th if plan_th is not None else row.get("plan_th") or 0), 1)
    wd = int(row.get("working_days") or 0)
    cal_days = int(row.get("calendar_days") or 0)
    if cal_days <= 0:
        # 互換：旧データに暦日が無い場合は稼働日を流用しない（計算不能なら0）
        cal_days = 0
    cap = {
        "equipment_label": row.get("equipment_label") or "",
        "standard_rate": int(row.get("standard_rate") or 0),
        "shift_label": row.get("shift_label") or "",
        "working_days": wd,
        "utilization_rate_pct": row.get("utilization_rate_pct"),
        "daily_regular_hours": 0,
    }
    return _calc_load_row(
        process_cd=str(row.get("process_cd") or ""),
        process_name=str(row.get("process_name") or ""),
        plan_th=pt,
        working_days=wd,
        calendar_days=cal_days,
        capacity=cap,
    )


async def _build_load_plan(
    db: AsyncSession,
    year: int,
    month: int,
    capacities: List[Dict[str, Any]],
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    start_d, end_d = _month_range(year, month)
    month_wd = await _working_days(db, year, month)
    calendar_days = monthrange(year, month)[1]
    forecast = await _forecast_units(db, year, month)
    cap_map = {c["process_cd"]: c for c in capacities}
    ov_all = overrides or {}

    rows: List[Dict[str, Any]] = []
    for cd in _LOAD_PLAN_PROCESS_CDS:
        cap = cap_map.get(cd, {"process_name": cd, "process_cd": cd})
        plan_col = _PLAN_COL_BY_CD.get(cd)
        if cd == "welding_sp":
            plan_qty = await _sum_welding_plan_split(db, start_d, end_d, for_sp=True)
        elif cd == "welding":
            plan_qty = await _sum_welding_plan_split(db, start_d, end_d, for_sp=False)
        elif plan_col:
            plan_qty = await _sum_column(db, plan_col, start_d, end_d)
        else:
            plan_qty = 0
        rows.append(
            _calc_load_row(
                process_cd=cd,
                process_name=str(cap.get("process_name") or cd),
                plan_th=_thousands(plan_qty),
                working_days=month_wd,
                calendar_days=calendar_days,
                capacity=cap,
                overrides=(ov_all.get("processes") or {}).get(cd),
            )
        )

    out = {
        "month": f"{year:04d}-{month:02d}",
        "month_label": _month_label(year, month),
        "working_days": month_wd,
        "calendar_days": calendar_days,
        "forecast_th": _thousands(forecast),
        "daily_forecast_th": round(_thousands(forecast) / month_wd, 1) if month_wd > 0 else 0.0,
        "rows": rows,
        "comments": [],
    }
    out["comments"] = _generate_load_plan_comments(out)
    return out


def _fmt_signed_th(v: float, digits: int = 1) -> str:
    n = round(float(v or 0), digits)
    if n > 0:
        return f"+{n:.{digits}f}"
    if n < 0:
        return f"△{abs(n):.{digits}f}"
    return f"±{0:.{digits}f}"


def _fmt_signed_pt(v: float, digits: int = 2) -> str:
    n = round(float(v or 0), digits)
    if n > 0:
        return f"+{n:.{digits}f}"
    if n < 0:
        return f"△{abs(n):.{digits}f}"
    return f"±{0:.{digits}f}"


def _generate_performance_comments(perf: Dict[str, Any]) -> List[str]:
    """実績一覧から自動コメント（計画差・生産性）。"""
    rows = list(perf.get("rows") or [])
    month_label = str(perf.get("month_label") or "")
    comments: List[str] = []
    if month_label:
        comments.append(f"{month_label}の工程別実績を集計しました。")

    shipping = next((r for r in rows if r.get("key") == "shipping"), None)
    if shipping:
        vs_plan = float(shipping.get("vs_plan_th") or 0)
        vs_fc = float(shipping.get("vs_forecast_th") or 0)
        comments.append(
            f"出荷は計画比 {_fmt_signed_th(vs_plan)} 千本、実見比 {_fmt_signed_th(vs_fc)} 千本"
            f"（実績 {float(shipping.get('actual_th') or 0):.1f} / 計画 {float(shipping.get('plan_th') or 0):.1f} 千本）。"
        )

    shortfalls: List[str] = []
    overruns: List[str] = []
    for r in rows:
        if r.get("key") == "shipping":
            continue
        name = str(r.get("name") or r.get("key") or "")
        vs = float(r.get("vs_plan_th") or 0)
        plan = float(r.get("plan_th") or 0)
        # 5千本以上、または計画の5%以上の乖離を指摘
        thr = max(5.0, abs(plan) * 0.05) if plan else 5.0
        if vs <= -thr:
            shortfalls.append(f"{name} {_fmt_signed_th(vs)} 千本")
        elif vs >= thr:
            overruns.append(f"{name} {_fmt_signed_th(vs)} 千本")
    if shortfalls:
        comments.append("計画未達（主な工程）：" + "、".join(shortfalls[:4]) + "。")
    if overruns:
        comments.append("計画超過（主な工程）：" + "、".join(overruns[:4]) + "。")

    prod_down: List[str] = []
    prod_up: List[str] = []
    for r in rows:
        if r.get("key") == "shipping":
            continue
        delta = r.get("productivity_delta")
        if delta is None:
            continue
        d = float(delta)
        name = str(r.get("name") or "")
        if d <= -3:
            prod_down.append(f"{name} {_fmt_signed_pt(d, 1)}")
        elif d >= 3:
            prod_up.append(f"{name} {_fmt_signed_pt(d, 1)}")
    if prod_down:
        comments.append("生産性低下（前月比）：" + "、".join(prod_down[:4]) + "。")
    if prod_up:
        comments.append("生産性改善（前月比）：" + "、".join(prod_up[:4]) + "。")

    if len(comments) == 1:
        comments.append("各工程とも計画との大きな乖離は見られません。")
    return comments[:5]


def _generate_scrap_comments(scrap: Dict[str, Any]) -> List[str]:
    """廃棄率・廃棄本数から自動コメント（選択期間の集計を主に分析）。"""
    comments: List[str] = []
    fy_label = str(scrap.get("fiscal_year_label") or "")
    monthly = list(scrap.get("monthly") or [])
    range_label = str(scrap.get("range_label") or "")
    if not range_label and monthly:
        range_label = f"{monthly[0].get('month')}月〜{monthly[-1].get('month')}月"
    period = f"{fy_label}{range_label}" if (fy_label or range_label) else "対象期間"

    if monthly:
        rates_new = [float(m.get("rate_new_pct") or m.get("rate_pct") or 0) for m in monthly]
        rates_old = [float(m.get("rate_old_pct") or m.get("rate_pct") or 0) for m in monthly]
        losses = []
        for m in monthly:
            if m.get("loss_qty") is not None:
                losses.append(int(m.get("loss_qty") or 0))
            elif m.get("loss_th") is not None:
                losses.append(int(round(float(m.get("loss_th") or 0) * 1000)))
            elif m.get("scrap_th") is not None:
                losses.append(int(round(float(m.get("scrap_th") or 0) * 1000)))
            else:
                losses.append(0)
        avg_new = sum(rates_new) / len(rates_new)
        avg_old = sum(rates_old) / len(rates_old)
        avg_loss = sum(losses) / len(losses)
        total_loss = sum(losses)
    else:
        avg_new = float(scrap.get("avg_rate_new_current_fy_pct") or 0)
        avg_old = float(scrap.get("avg_rate_old_current_fy_pct") or 0)
        avg_loss = float(scrap.get("avg_loss_current_fy_qty") or 0)
        total_loss = int(round(avg_loss))

    comments.append(
        f"{period}の期間平均廃棄率は新 {avg_new:.2f}% / 旧 {avg_old:.2f}%、"
        f"月平均廃棄本数 {int(round(avg_loss)):,} 本（期間合計 {int(total_loss):,} 本）です。"
    )

    avg_new_prev = float(scrap.get("avg_rate_new_prev_fy_pct") or 0)
    avg_old_prev = float(scrap.get("avg_rate_old_prev_fy_pct") or scrap.get("avg_rate_prev_fy_pct") or 0)
    improv_new = float(scrap.get("improvement_rate_new_pt") or (avg_new_prev - avg_new))
    improv_old = float(scrap.get("improvement_rate_old_pt") or scrap.get("improvement_rate_pt") or (avg_old_prev - avg_old))
    if avg_old_prev or avg_new_prev:
        comments.append(
            f"前年同期平均は新 {avg_new_prev:.2f}% / 旧 {avg_old_prev:.2f}%"
            f"（新 {_fmt_signed_pt(improv_new)}pt / 旧 {_fmt_signed_pt(improv_old)}pt）。"
        )

    improv_loss = int(scrap.get("improvement_loss_qty") or 0)
    if improv_loss != 0:
        direction = "減少" if improv_loss > 0 else "増加"
        comments.append(
            f"廃棄本数の月平均は前年同期比 {abs(improv_loss):,} 本{direction}"
            f"（{_fmt_signed_th(_thousands(improv_loss))} 千本）。"
        )

    if monthly:
        last = monthly[-1]
        last_m = last.get("month")
        last_new = float(last.get("rate_new_pct") or last.get("rate_pct") or 0)
        last_old = float(last.get("rate_old_pct") or last.get("rate_pct") or 0)
        if last.get("loss_qty") is not None:
            last_loss = int(last.get("loss_qty") or 0)
        elif last.get("loss_th") is not None:
            last_loss = int(round(float(last.get("loss_th") or 0) * 1000))
        else:
            last_loss = int(round(float(last.get("scrap_th") or 0) * 1000))
        comments.append(
            f"期間末（{last_m}月）は新 {last_new:.2f}% / 旧 {last_old:.2f}%、"
            f"廃棄本数 {last_loss:,} 本。"
        )

    if len(monthly) >= 2:
        prev_m = monthly[-2]
        curr_m = monthly[-1]
        d_rate = float(curr_m.get("rate_old_pct") or curr_m.get("rate_pct") or 0) - float(
            prev_m.get("rate_old_pct") or prev_m.get("rate_pct") or 0
        )
        curr_loss = int(curr_m.get("loss_qty") or 0)
        prev_loss = int(prev_m.get("loss_qty") or 0)
        if curr_m.get("loss_qty") is None and curr_m.get("loss_th") is not None:
            curr_loss = int(round(float(curr_m.get("loss_th") or 0) * 1000))
        if prev_m.get("loss_qty") is None and prev_m.get("loss_th") is not None:
            prev_loss = int(round(float(prev_m.get("loss_th") or 0) * 1000))
        d_loss = curr_loss - prev_loss
        comments.append(
            f"期間内の前月比（{prev_m.get('month')}月→{curr_m.get('month')}月）："
            f"廃棄率（旧） {_fmt_signed_pt(d_rate)}pt、"
            f"廃棄本数 {_fmt_signed_th(_thousands(d_loss))} 千本。"
        )
        if d_rate > 0.1 or d_loss > 500:
            comments.append("前月より悪化しているため、不良・廃棄発生工程の確認を推奨します。")
        elif d_rate < -0.1 or d_loss < -500:
            comments.append("前月より改善傾向です。継続監視をお願いします。")
    return comments[:5]


def _generate_inventory_comments(inv: Dict[str, Any], *, forecast_mode: bool = False) -> List[str]:
    """月末在庫（または予測在庫）から自動コメント。"""
    comments: List[str] = []
    label = str(inv.get("inventory_month_label") or "")
    title = f"{label}月末在庫" if label and not forecast_mode else (f"{label}在庫予測" if label else "在庫")
    comments.append(f"{title}を工程別に集計しました。")

    rows = list(inv.get("rows") or [])
    by_key = {str(r.get("key")): r for r in rows}

    product = by_key.get("product")
    if product:
        rate = float(product.get("curr_rate_adj") or product.get("curr_rate") or 0)
        days = float(product.get("curr_days") or 0)
        target_r = float(inv.get("product_target_rate") or _PRODUCT_TARGET_RATE)
        target_d = float(inv.get("product_target_days") or _PRODUCT_TARGET_DAYS)
        level = str(inv.get("product_level") or "ok")
        level_jp = {"danger": "不足懸念", "ok": "適正", "high": "過多懸念"}.get(level, level)
        comments.append(
            f"製品在庫は補正率 {rate:.2f}（目標 {target_r:.2f}）、"
            f"在庫日数 {days:.1f}日（目標 {target_d:.1f}日）→ 判定【{level_jp}】。"
        )
        if level == "danger":
            comments.append("製品在庫が目標を下回っています。出荷計画との突合と補充検討が必要です。")
        elif level == "high":
            comments.append("製品在庫が目標の2倍超です。過剰在庫の削減・出荷前倒しを検討してください。")

    wip = by_key.get("wip_total")
    if wip:
        delta = float(wip.get("delta_th") or 0)
        comments.append(
            f"仕掛品合計は {float(wip.get('curr_inventory_th') or 0):.1f} 千本"
            f"（前月比 {_fmt_signed_th(delta)} 千本）。"
        )

    alerts: List[str] = []
    for key, r in by_key.items():
        if key in ("wip_total", "product") or r.get("children"):
            continue
        target = _PROCESS_TARGET_RATES.get(key)
        if target is None:
            continue
        rate = float(r.get("curr_rate_adj") or r.get("curr_rate") or 0)
        name = str(r.get("name") or key)
        if rate < target:
            alerts.append(f"{name} 補正率{rate:.2f}<目標{target:.2f}")
        elif rate > target * 2:
            alerts.append(f"{name} 補正率{rate:.2f}>目標×2({target * 2:.2f})")
    if alerts:
        comments.append("工程別の注意点：" + "、".join(alerts[:4]) + "。")
    elif not product or str(inv.get("product_level") or "ok") == "ok":
        comments.append("主要工程の補正在庫率はおおむね目標範囲内です。")
    return comments[:5]


def _generate_load_plan_comments(load: Dict[str, Any]) -> List[str]:
    """負荷計画から自動コメント。"""
    comments: List[str] = []
    month_label = str(load.get("month_label") or "")
    wd = int(load.get("working_days") or 0)
    fc = float(load.get("forecast_th") or 0)
    daily = float(load.get("daily_forecast_th") or 0)
    if month_label:
        comments.append(
            f"{month_label}は稼働日 {wd} 日、内示 {fc:.1f} 千本（日当たり {daily:.1f} 千本）です。"
        )

    overload: List[str] = []
    tight: List[str] = []
    light: List[str] = []
    for r in load.get("rows") or []:
        name = str(r.get("process_name") or r.get("process_cd") or "")
        rate = float(r.get("load_rate_pct") or 0)
        if rate >= 100:
            overload.append(f"{name} {rate:.0f}%")
        elif rate >= 90:
            tight.append(f"{name} {rate:.0f}%")
        elif 0 < rate <= 60:
            light.append(f"{name} {rate:.0f}%")
    if overload:
        comments.append("負荷率100%超（要対策）：" + "、".join(overload[:5]) + "。")
        comments.append("残業・休出・外注・日程調整のいずれかで負荷平準化を検討してください。")
    if tight:
        comments.append("負荷率90%以上（逼迫）：" + "、".join(tight[:4]) + "。")
    if light and not overload:
        comments.append("余裕のある工程：" + "、".join(light[:4]) + "。人員・設備の振替余地があります。")
    if not overload and not tight:
        comments.append("主要工程の負荷率はおおむね適正範囲です。")
    return comments[:5]


def generate_section_comments(kind: str, section: Dict[str, Any]) -> List[str]:
    """画面の現在値（手改反映後）からコメントを再生成する。"""
    k = (kind or "").strip()
    data = section or {}
    if k == "performance":
        return _generate_performance_comments(data)
    if k == "scrap":
        return _generate_scrap_comments(data)
    if k == "inventory":
        return _generate_inventory_comments(data, forecast_mode=False)
    if k == "inventory_forecast":
        return _generate_inventory_comments(data, forecast_mode=True)
    if k == "load_plan":
        return _generate_load_plan_comments(data)
    raise ValueError(
        "kind は performance / scrap / inventory / inventory_forecast / load_plan のいずれかです"
    )


def _default_comments() -> Dict[str, List[str]]:
    return {
        "performance": [],
        "scrap": [],
        "inventory_actual": [],
        "inventory_forecast": [],
        "load_current": [],
        "load_next": [],
    }


def merge_preserve_editable(
    computed: Dict[str, Any],
    existing: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """再計算時、人工入力のコメント・生産性・負荷オーバーライドを保持"""
    if not existing:
        return computed
    merged = json.loads(json.dumps(computed))
    for section in ("part01", "part02", "part03"):
        if section not in merged or section not in existing:
            continue
        ex = existing[section]
        mg = merged[section]
        for key in ("comments",):
            if ex.get(key):
                mg[key] = ex[key]
        if section == "part01":
            if ex.get("performance", {}).get("rows") and mg.get("performance", {}).get("rows"):
                ex_rows = {r["key"]: r for r in ex["performance"]["rows"]}
                for row in mg["performance"]["rows"]:
                    prev = ex_rows.get(row["key"], {})
                    for fld in ("plan_th", "forecast_th", "actual_th"):
                        if prev.get(fld) is not None:
                            row[fld] = prev[fld]
                    plan_th = float(row.get("plan_th") or 0)
                    forecast_th = float(row.get("forecast_th") or 0)
                    actual_th = float(row.get("actual_th") or 0)
                    row["vs_forecast_th"] = round(forecast_th - plan_th, 1)
                    row["vs_plan_th"] = round(actual_th - plan_th, 1)
                    if row.get("key") == "shipping":
                        row["productivity_prev"] = None
                        row["productivity_curr"] = None
                        row["productivity_delta"] = None
                        continue
                    for fld in ("productivity_prev", "productivity_curr"):
                        if prev.get(fld) is not None:
                            row[fld] = prev[fld]
                    if row.get("productivity_prev") is not None and row.get("productivity_curr") is not None:
                        row["productivity_delta"] = row["productivity_curr"] - row["productivity_prev"]
            if ex.get("performance", {}).get("comments"):
                mg["performance"]["comments"] = ex["performance"]["comments"]
            if ex.get("scrap", {}).get("comments"):
                mg["scrap"]["comments"] = ex["scrap"]["comments"]
            if ex.get("inventory", {}).get("comments"):
                mg["inventory"]["comments"] = ex["inventory"]["comments"]
            if ex.get("inventory", {}).get("curr_inventory_as_of"):
                mg["inventory"]["curr_inventory_as_of"] = ex["inventory"]["curr_inventory_as_of"]
            if ex.get("inventory", {}).get("rows") and mg.get("inventory", {}).get("rows"):
                ex_inv_rows = {
                    r.get("key"): r for r in _iter_inventory_rows(ex["inventory"]["rows"])
                }
                prev_wd = int(mg["inventory"].get("prev_workdays") or 0)
                curr_wd = int(mg["inventory"].get("curr_workdays") or 0)
                target_rate = float(
                    mg["inventory"].get("product_target_rate") or _PRODUCT_TARGET_RATE
                )
                target_days = float(
                    mg["inventory"].get("product_target_days") or _PRODUCT_TARGET_DAYS
                )
                for row in _iter_inventory_rows(mg["inventory"]["rows"]):
                    # 親行は子から再集計するため、手改値は子のみ反映
                    if row.get("children"):
                        continue
                    prev = ex_inv_rows.get(row.get("key"), {})
                    for fld in ("prev_inventory_th", "curr_inventory_th"):
                        if prev.get(fld) is not None:
                            row[fld] = prev[fld]
                    # 工程内示分母は再計算結果を維持
                    _recompute_inventory_row_metrics(row, prev_wd=prev_wd, curr_wd=curr_wd)
                for row in mg["inventory"]["rows"]:
                    if row.get("children"):
                        _resync_inventory_parent_row(row, prev_wd=prev_wd, curr_wd=curr_wd)
                # 仕掛品合計をトップ行から再集計
                wip = next(
                    (r for r in mg["inventory"]["rows"] if r.get("key") == "wip_total"),
                    None,
                )
                if wip:
                    tops = [
                        r
                        for r in mg["inventory"]["rows"]
                        if r.get("key") in _WIP_TOP_ORDER
                    ]
                    wip["prev_inventory_th"] = round(
                        sum(float(r.get("prev_inventory_th") or 0) for r in tops), 1
                    )
                    wip["curr_inventory_th"] = round(
                        sum(float(r.get("curr_inventory_th") or 0) for r in tops), 1
                    )
                    # 分母は全量出荷内示を維持
                    wip["prev_forecast_th"] = float(mg["inventory"].get("prev_forecast_th") or 0)
                    wip["curr_forecast_th"] = float(mg["inventory"].get("curr_forecast_th") or 0)
                    wip["prev_forecast_adj_th"] = float(
                        mg["inventory"].get("prev_forecast_adj_th")
                        or mg["inventory"].get("prev_forecast_th")
                        or 0
                    )
                    wip["curr_forecast_adj_th"] = float(
                        mg["inventory"].get("curr_forecast_adj_th")
                        or mg["inventory"].get("curr_forecast_th")
                        or 0
                    )
                    _recompute_inventory_row_metrics(wip, prev_wd=prev_wd, curr_wd=curr_wd)
                product_row = next(
                    (r for r in mg["inventory"]["rows"] if r.get("key") == "product"),
                    None,
                )
                if product_row:
                    pdays = float(product_row.get("curr_days") or 0)
                    prate = float(product_row.get("curr_rate_adj") or 0)
                    if pdays < target_days or prate < target_rate:
                        mg["inventory"]["product_level"] = "danger"
                    elif pdays > target_days * 2:
                        mg["inventory"]["product_level"] = "high"
                    else:
                        mg["inventory"]["product_level"] = "ok"
            # 手改コメントが無い場合のみ、最新数値で自動コメントを再生成
            if not (ex.get("performance") or {}).get("comments"):
                mg["performance"]["comments"] = _generate_performance_comments(mg["performance"])
            if not (ex.get("scrap") or {}).get("comments"):
                mg["scrap"]["comments"] = _generate_scrap_comments(mg["scrap"])
            if not (ex.get("inventory") or {}).get("comments"):
                mg["inventory"]["comments"] = _generate_inventory_comments(mg["inventory"])
        if section in ("part02", "part03"):
            if ex.get("load_plan", {}).get("comments"):
                mg["load_plan"]["comments"] = ex["load_plan"]["comments"]
            ex_rows = {r.get("process_cd"): r for r in (ex.get("load_plan") or {}).get("rows") or []}
            for row in mg.get("load_plan", {}).get("rows") or []:
                prev = ex_rows.get(row.get("process_cd"), {})
                if prev.get("plan_th") is not None:
                    row.update(_recompute_load_row_dict(row, float(prev["plan_th"])))
            if not (ex.get("load_plan") or {}).get("comments"):
                mg["load_plan"]["comments"] = _generate_load_plan_comments(mg["load_plan"])
            if section == "part02" and ex.get("inventory_forecast"):
                mg["inventory_forecast"] = ex["inventory_forecast"]
            elif section == "part02" and not (ex.get("inventory_forecast") or {}).get("comments"):
                mg["inventory_forecast"]["comments"] = _generate_inventory_comments(
                    mg["inventory_forecast"], forecast_mode=True
                )

    if existing.get("meta"):
        merged.setdefault("meta", {}).update(
            {k: v for k, v in existing["meta"].items() if k in ("meeting_date", "title_note")}
        )
    return merged


async def build_meeting_data(
    db: AsyncSession,
    target_month: str,
    existing: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """対象月の生産検討会資料データを組み立てる。

    例: target_month=2026-08 → 8月度検討会
      PART01 = 7月実績, PART02 = 8月計画, PART03 = 9月計画
    """
    ty, tm = _parse_month(target_month)
    prev_y, prev_m = _shift_month(ty, tm, -1)
    next_y, next_m = _shift_month(ty, tm, 1)

    capacities = await get_capacity_rows(db)

    part01_performance = await _build_performance_table(db, prev_y, prev_m)
    part01_scrap = await _build_scrap_section(db, ty, tm)
    # 月末在庫 M 月 → 内示は当月(M)と翌月(M+1)
    part01_inventory = await _build_inventory_table(
        db,
        inv_year=prev_y,
        inv_month=prev_m,
        prev_forecast_year=prev_y,
        prev_forecast_month=prev_m,
        curr_forecast_year=ty,
        curr_forecast_month=tm,
    )

    part02_load = await _build_load_plan(db, ty, tm, capacities)
    part02_inventory_fc = await _build_inventory_table(
        db,
        inv_year=ty,
        inv_month=tm,
        prev_forecast_year=ty,
        prev_forecast_month=tm,
        curr_forecast_year=next_y,
        curr_forecast_month=next_m,
    )
    part02_inventory_fc["comments"] = _generate_inventory_comments(
        part02_inventory_fc, forecast_mode=True
    )

    part03_load = await _build_load_plan(db, next_y, next_m, capacities)

    data = {
        "target_month": target_month,
        "meta": {
            "meeting_date": date.today().isoformat(),
            "meeting_month_label": _month_label(ty, tm),
            "title": f"{tm}月度 生産検討会",
            "subtitle": "各工程の稼働状況および負荷・在庫分析と今後の生産計画",
            "title_note": "",
        },
        "part01": {
            "title": f"PART 01. {_month_label(prev_y, prev_m)} 実績報告",
            "subtitle": f"{_month_label(prev_y, prev_m)}における各工程の生産実績・廃棄率、および月末在庫高の報告",
            "performance": part01_performance,
            "scrap": part01_scrap,
            "inventory": part01_inventory,
        },
        "part02": {
            "title": f"PART 02. {_month_label(ty, tm)} 生産計画",
            "subtitle": f"稼働日{part02_load['working_days']}日における主要工程の生産負荷予測と稼働体制の最適化",
            "load_plan": part02_load,
            "inventory_forecast": part02_inventory_fc,
        },
        "part03": {
            "title": f"PART 03. {_month_label(next_y, next_m)} 生産計画",
            "subtitle": f"稼働日{part03_load['working_days']}日の生産負荷予測",
            "load_plan": part03_load,
        },
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return merge_preserve_editable(data, existing)


def meeting_to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def meeting_from_json(raw: str) -> Dict[str, Any]:
    return json.loads(raw or "{}")
