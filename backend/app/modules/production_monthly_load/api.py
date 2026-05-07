"""
月度工程別生産負荷サマリ API

対象月（YYYY-MM）について、内示・各工程の月計画数、標準能率、月間定時時間、
生産所要時間、負荷率、日均稼働時間を集計して返す。

集計ポリシー（v1 簡素版）:
- 計画数量: production_summarys の各工程 *_plan を月単位で SUM
- 内示数量: production_summarys.forecast_quantity を月単位で SUM
- 稼働日: production_summarys 上、対象月のうち day_of_week NOT IN ('土','日') の DISTINCT 日数
- 標準能率（本/H）: equipment_efficiency × machines × processes を JOIN し、
  対象月に計画数量がある製品に絞って数量加重平均。データが無ければ null。
- 月間定時時間: workingDays × 既定時間/日 × 直数 × resource_count（工程ごとの定数）
- 生産所要時間: planQty / efficiency（efficiency が無ければ null）
- 負荷率: requiredHours / monthlyRegularHours × 100
- 日均稼働(H/台・人): requiredHours / workingDays / resource_count

注意: 設備台数・人員数の既定値（DEFAULT_RESOURCE_COUNT）と直数（SHIFT_COUNT）は
スクリーンショット仕様に近づけた現場固定値です。後続フェーズで設定テーブル化予定。
"""
from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

router = APIRouter()


# ---------------------------------------------------------------------------
# 工程行定義（表示順・計算ポリシー）
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProcessRowSpec:
    key: str
    label: str
    plan_column: Optional[str]
    process_name: Optional[str]
    resource_unit: str  # "台" or "人"
    shift_count: float
    default_resource_count: float
    hours_per_day: float
    annotation: Optional[str] = None
    manual: bool = False  # True の場合はサマリ計算対象外（DB由来データなし）


# スクリーンショットの 5 月計画に近い既定値。後で設定テーブル化する想定。
PROCESS_ROW_SPECS: tuple[ProcessRowSpec, ...] = (
    ProcessRowSpec(
        key="forecast",
        label="内示",
        plan_column=None,
        process_name=None,
        resource_unit="",
        shift_count=0,
        default_resource_count=0,
        hours_per_day=0,
    ),
    ProcessRowSpec(
        key="cutting",
        label="切断",
        plan_column="cutting_plan",
        process_name="切断",
        resource_unit="台",
        shift_count=3,
        default_resource_count=6,
        hours_per_day=7.6,
    ),
    ProcessRowSpec(
        key="chamfering",
        label="面取",
        plan_column="chamfering_plan",
        process_name="面取",
        resource_unit="台",
        shift_count=2,
        default_resource_count=4.5,
        hours_per_day=7.6,
        annotation="2工程換算",
    ),
    ProcessRowSpec(
        key="molding",
        label="成型",
        plan_column="molding_plan",
        process_name="成型",
        resource_unit="ライン",
        shift_count=2,
        default_resource_count=24,
        hours_per_day=7.6,
    ),
    ProcessRowSpec(
        key="plating",
        label="メッキ",
        plan_column="plating_plan",
        process_name="メッキ",
        resource_unit="台",
        shift_count=3,
        default_resource_count=1,
        hours_per_day=7.5,
    ),
    ProcessRowSpec(
        key="inspection",
        label="検査",
        plan_column="inspection_plan",
        process_name="検査",
        resource_unit="人",
        shift_count=1,
        default_resource_count=11,
        hours_per_day=7.6,
    ),
    ProcessRowSpec(
        key="welding",
        label="溶接",
        plan_column="welding_plan",
        process_name="溶接",
        resource_unit="人",
        shift_count=1,
        default_resource_count=6,
        hours_per_day=7.6,
    ),
    ProcessRowSpec(
        key="welding_sp",
        label="溶接SP",
        plan_column=None,  # 専用列が無いため別途設定が必要
        process_name=None,
        resource_unit="人",
        shift_count=1,
        default_resource_count=2,
        hours_per_day=7.6,
        manual=True,
    ),
)


# ---------------------------------------------------------------------------
# 共通ユーティリティ
# ---------------------------------------------------------------------------

def _parse_year_month(s: str) -> tuple[date, date, int, int]:
    s = (s or "").strip()
    if len(s) >= 7 and s[4] == "-":
        try:
            year = int(s[:4])
            month = int(s[5:7])
            month_start = date(year, month, 1)
            last_day = monthrange(year, month)[1]
            month_end = date(year, month, last_day)
            return month_start, month_end, year, month
        except ValueError:
            pass
    raise HTTPException(status_code=400, detail="yearMonth は YYYY-MM 形式で指定してください")


def _safe_float(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _round(val: Optional[float], digits: int) -> Optional[float]:
    if val is None:
        return None
    return round(val, digits)


def _shift_month(d: date, delta_months: int) -> date:
    total = d.year * 12 + (d.month - 1) + delta_months
    y, m = divmod(total, 12)
    return date(y, m + 1, 1)


# ---------------------------------------------------------------------------
# データ取得
# ---------------------------------------------------------------------------

async def _fetch_plan_totals(
    db: AsyncSession,
    month_start: date,
    month_end: date,
) -> dict[str, float]:
    """production_summarys 月集計（内示と各工程 *_plan）"""
    plan_cols = [s.plan_column for s in PROCESS_ROW_SPECS if s.plan_column]
    select_parts = ["COALESCE(SUM(forecast_quantity), 0) AS forecast"]
    select_parts += [f"COALESCE(SUM(`{c}`), 0) AS `{c}`" for c in plan_cols]
    sql = text(
        f"""
        SELECT {', '.join(select_parts)}
        FROM production_summarys
        WHERE `date` BETWEEN :start_date AND :end_date
        """
    )
    res = await db.execute(sql, {"start_date": month_start, "end_date": month_end})
    row = res.mappings().fetchone() or {}
    out: dict[str, float] = {"forecast": _safe_float(row.get("forecast"))}
    for c in plan_cols:
        out[c] = _safe_float(row.get(c))
    return out


async def _fetch_working_days(
    db: AsyncSession,
    month_start: date,
    month_end: date,
) -> int:
    """対象月で平日（土日以外）の稼働日数を production_summarys から取得"""
    sql = text(
        """
        SELECT COUNT(DISTINCT `date`) AS days
        FROM production_summarys
        WHERE `date` BETWEEN :start_date AND :end_date
          AND day_of_week IS NOT NULL
          AND day_of_week NOT IN ('土', '日')
        """
    )
    res = await db.execute(sql, {"start_date": month_start, "end_date": month_end})
    row = res.mappings().fetchone()
    days = int(row["days"]) if row and row.get("days") is not None else 0
    if days > 0:
        return days
    # フォールバック: カレンダー平日（土日除外）
    cur = month_start
    fallback = 0
    while cur <= month_end:
        if cur.weekday() < 5:
            fallback += 1
        cur += timedelta(days=1)
    return fallback


async def _fetch_weighted_efficiency(
    db: AsyncSession,
    month_start: date,
    month_end: date,
) -> dict[str, Optional[float]]:
    """工程別の数量加重平均効率（本/H）を取得"""
    sql = text(
        """
        SELECT pr.process_name AS process_name,
               ee.product_cd AS product_cd,
               AVG(ee.efficiency_rate) AS efficiency_rate
        FROM equipment_efficiency ee
        INNER JOIN machines m ON m.machine_cd = ee.machine_cd
        INNER JOIN processes pr ON pr.process_name IN ('切断','面取','成型','メッキ','検査','溶接')
          AND (TRIM(m.machine_type) = pr.process_name OR TRIM(m.machine_type) = pr.process_cd)
        WHERE COALESCE(ee.efficiency_rate, 0) > 0
          AND COALESCE(ee.product_cd, '') <> ''
        GROUP BY pr.process_name, ee.product_cd
        """
    )
    eff_res = await db.execute(sql)
    eff_map: dict[tuple[str, str], float] = {}
    for r in eff_res.mappings().fetchall():
        proc = (r.get("process_name") or "").strip()
        pcd = (r.get("product_cd") or "").strip()
        rate = _safe_float(r.get("efficiency_rate"))
        if proc and pcd and rate > 0:
            eff_map[(proc, pcd)] = rate

    plan_cols = [(s.process_name, s.plan_column) for s in PROCESS_ROW_SPECS if s.plan_column and s.process_name]
    weighted: dict[str, Optional[float]] = {}
    for proc_name, plan_col in plan_cols:
        sql_plan = text(
            f"""
            SELECT product_cd, COALESCE(SUM(`{plan_col}`), 0) AS qty
            FROM production_summarys
            WHERE `date` BETWEEN :start_date AND :end_date
              AND COALESCE(`{plan_col}`, 0) > 0
              AND COALESCE(product_cd, '') <> ''
            GROUP BY product_cd
            """
        )
        plan_res = await db.execute(sql_plan, {"start_date": month_start, "end_date": month_end})
        total_qty = 0.0
        weighted_sum = 0.0
        for pr_row in plan_res.mappings().fetchall():
            pcd = (pr_row.get("product_cd") or "").strip()
            qty = _safe_float(pr_row.get("qty"))
            if qty <= 0 or not pcd:
                continue
            rate = eff_map.get((proc_name, pcd))
            if rate and rate > 0:
                weighted_sum += qty * rate
                total_qty += qty
        weighted[proc_name] = (weighted_sum / total_qty) if total_qty > 0 else None
    return weighted


async def _fetch_forecast_daily(
    db: AsyncSession,
    target_month_start: date,
    target_month_end: date,
) -> tuple[float, int]:
    """指定月の内示合計と稼働日数を返す（次月／次々月の見込日産用）"""
    sql = text(
        """
        SELECT COALESCE(SUM(forecast_quantity), 0) AS total,
               COUNT(DISTINCT CASE WHEN day_of_week NOT IN ('土', '日') THEN `date` END) AS days
        FROM production_summarys
        WHERE `date` BETWEEN :start_date AND :end_date
        """
    )
    res = await db.execute(sql, {"start_date": target_month_start, "end_date": target_month_end})
    row = res.mappings().fetchone() or {}
    total = _safe_float(row.get("total"))
    days = int(row.get("days") or 0)
    if days <= 0:
        cur = target_month_start
        while cur <= target_month_end:
            if cur.weekday() < 5:
                days += 1
            cur += timedelta(days=1)
    return total, days


# ---------------------------------------------------------------------------
# 計算
# ---------------------------------------------------------------------------

def _build_process_row(
    spec: ProcessRowSpec,
    plan_qty: float,
    working_days: int,
    efficiency: Optional[float],
) -> dict[str, Any]:
    """工程行 1 件のメトリクスを生成"""
    plan_thousand = plan_qty / 1000.0 if plan_qty else 0.0
    plan_thousand_per_day = (plan_thousand / working_days) if working_days > 0 else None

    if spec.key == "forecast":
        return {
            "key": spec.key,
            "label": spec.label,
            "plan_qty": plan_qty,
            "plan_thousand": _round(plan_thousand, 1),
            "plan_thousand_per_day": _round(plan_thousand_per_day, 1),
            "resource_count": None,
            "resource_unit": "",
            "shift_count": None,
            "efficiency": None,
            "monthly_regular_hours": None,
            "required_hours": None,
            "load_pct": None,
            "daily_avg_hours": None,
            "annotation": None,
            "manual": False,
        }

    resource_count = spec.default_resource_count
    monthly_regular_hours: Optional[float] = None
    if working_days > 0 and resource_count > 0 and spec.shift_count > 0 and spec.hours_per_day > 0:
        monthly_regular_hours = (
            working_days * spec.hours_per_day * spec.shift_count * resource_count
        )

    required_hours: Optional[float] = None
    if efficiency and efficiency > 0 and plan_qty > 0:
        required_hours = plan_qty / efficiency

    load_pct: Optional[float] = None
    if required_hours is not None and monthly_regular_hours and monthly_regular_hours > 0:
        load_pct = required_hours / monthly_regular_hours * 100.0

    daily_avg: Optional[float] = None
    if (
        required_hours is not None
        and working_days > 0
        and resource_count > 0
    ):
        daily_avg = required_hours / working_days / resource_count

    if spec.manual:
        plan_qty_out: Optional[float] = None
        plan_thousand_out: Optional[float] = None
        plan_thousand_per_day_out: Optional[float] = None
        required_hours = None
        load_pct = None
        daily_avg = None
    else:
        plan_qty_out = plan_qty
        plan_thousand_out = _round(plan_thousand, 1)
        plan_thousand_per_day_out = _round(plan_thousand_per_day, 1)

    return {
        "key": spec.key,
        "label": spec.label,
        "plan_qty": plan_qty_out,
        "plan_thousand": plan_thousand_out,
        "plan_thousand_per_day": plan_thousand_per_day_out,
        "resource_count": resource_count,
        "resource_unit": spec.resource_unit,
        "shift_count": spec.shift_count,
        "efficiency": _round(efficiency, 0) if efficiency is not None else None,
        "monthly_regular_hours": _round(monthly_regular_hours, 0),
        "required_hours": _round(required_hours, 0),
        "load_pct": _round(load_pct, 1),
        "daily_avg_hours": _round(daily_avg, 1),
        "annotation": spec.annotation,
        "manual": spec.manual,
    }


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/summary")
async def get_monthly_load_summary(
    yearMonth: str = Query(..., description="対象月 YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """対象月の工程別負荷サマリを取得"""
    month_start, month_end, year, month = _parse_year_month(yearMonth)

    plan_totals = await _fetch_plan_totals(db, month_start, month_end)
    working_days = await _fetch_working_days(db, month_start, month_end)
    weighted_eff = await _fetch_weighted_efficiency(db, month_start, month_end)

    # 次月／次々月の日当たり見込（千本/日）
    forecast_next: list[dict[str, Any]] = []
    for offset in (1, 2):
        nxt_start = _shift_month(month_start, offset)
        nxt_end = date(nxt_start.year, nxt_start.month, monthrange(nxt_start.year, nxt_start.month)[1])
        total, days = await _fetch_forecast_daily(db, nxt_start, nxt_end)
        per_day = (total / 1000.0 / days) if days > 0 else None
        forecast_next.append(
            {
                "month_label": f"{nxt_start.month}月",
                "year_month": nxt_start.isoformat()[:7],
                "value_per_day": _round(per_day, 1),
                "working_days": days,
                "forecast_total": total,
            }
        )

    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for spec in PROCESS_ROW_SPECS:
        if spec.key == "forecast":
            plan_qty = plan_totals.get("forecast", 0.0)
            efficiency: Optional[float] = None
        elif spec.plan_column:
            plan_qty = plan_totals.get(spec.plan_column, 0.0)
            efficiency = weighted_eff.get(spec.process_name) if spec.process_name else None
        else:
            plan_qty = 0.0
            efficiency = None
        rows.append(_build_process_row(spec, plan_qty, working_days, efficiency))

    if working_days <= 0:
        warnings.append("対象月の稼働日が 0 日です。production_summarys にデータが無い可能性があります。")
    if all(r.get("efficiency") is None for r in rows if r["key"] not in ("forecast", "welding_sp")):
        warnings.append("equipment_efficiency に該当する製品の能率データがありません。生産所要時間と負荷率は計算できません。")
    if any(r.get("manual") for r in rows):
        warnings.append("溶接SP は専用の計画列が無いため未集計です。後続フェーズで設定テーブル化を予定しています。")

    return {
        "success": True,
        "header": {
            "year_month": f"{year:04d}-{month:02d}",
            "title_month": f"{month}月生産計画",
            "working_days": working_days,
            "forecast_daily_next_months": forecast_next,
        },
        "rows": rows,
        "config_note": (
            "設備台数・人員数・直数は v1 固定設定です。"
            "設備能率は equipment_efficiency × 計画数量の加重平均で算出しています。"
        ),
        "warnings": warnings,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
