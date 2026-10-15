"""生産設備能力の計算。

総時間 = (定時間 + 残業) × 直 × 稼働日数
日当数 = 設定数 ÷ 稼働日数
生産時間 = 日当数 ÷ (能率/H × 可動率 × 合格率)
稼働時間 = 生産時間 + 段取り（生産時間が 0 のときは 0）
加重平均 = 設定稼働日数 ÷ 実生産日数 × 生産時間 + 段取り
占有時間 = 加重平均 × 実生産日数
占有率 = 占有時間 ÷ 総時間
日当判定 = 加重平均 > (定時間+残業)×直 なら ×
月当判定 = 占有時間合計 > 総時間 なら ×
"""

from __future__ import annotations

from typing import Any, Optional


def _f(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def calc_header(
    regular_hours: Any,
    shift_count: Any,
    overtime_hours: Any,
    working_days: Any,
) -> dict[str, float]:
    regular = max(_f(regular_hours), 0.0)
    shifts = max(_f(shift_count), 0.0)
    overtime = max(_f(overtime_hours), 0.0)
    days = max(_f(working_days), 0.0)
    daily_available = (regular + overtime) * shifts
    total_hours = daily_available * days
    return {
        "regular_hours": regular,
        "shift_count": shifts,
        "overtime_hours": overtime,
        "working_days": days,
        "daily_available": daily_available,
        "total_hours": total_hours,
    }


def calc_line(
    *,
    monthly_qty: Any,
    qty_days: Any,
    rate_per_hour: Any,
    availability_rate: Any,
    pass_rate: Any,
    setup_hours: Any,
    actual_days: Any,
    daily_available: float,
    total_hours: float,
) -> dict[str, Any]:
    """1行分。可動率・合格率は 0〜1。"""
    monthly = max(_f(monthly_qty), 0.0)
    days_b = max(_f(qty_days), 0.0)
    rate = max(_f(rate_per_hour), 0.0)
    avail = _f(availability_rate)
    pass_r = _f(pass_rate)
    setup = max(_f(setup_hours), 0.0)
    actual = max(_f(actual_days), 0.0)

    daily_qty = monthly / days_b if days_b > 0 else 0.0
    denom = rate * avail * pass_r
    if daily_qty > 0 and denom > 0:
        production_hours = daily_qty / denom
    else:
        production_hours = 0.0
    operating_hours = (production_hours + setup) if production_hours > 0 else 0.0
    if operating_hours > 0 and actual > 0:
        weighted_hours = days_b / actual * production_hours + setup
    else:
        weighted_hours = 0.0
    occupied_hours = weighted_hours * actual if actual > 0 else 0.0
    occupancy_pct = (occupied_hours / total_hours * 100.0) if total_hours > 0 else None
    if production_hours <= 0 or daily_available <= 0:
        daily_judgment: Optional[str] = None
    else:
        daily_judgment = "ng" if weighted_hours > daily_available else "ok"
    return {
        "daily_qty": daily_qty,
        "production_hours": production_hours,
        "operating_hours": operating_hours,
        "weighted_hours": weighted_hours,
        "occupied_hours": occupied_hours,
        "rate_per_hour": rate,
        "occupancy_pct": occupancy_pct,
        "daily_judgment": daily_judgment,
    }


def calc_totals(lines: list[dict[str, Any]], header: dict[str, float]) -> dict[str, Any]:
    daily_available = header["daily_available"]
    total_hours = header["total_hours"]
    sum_production = 0.0
    sum_operating = 0.0
    sum_occupied = 0.0
    peak_rate = 0.0
    active = 0
    for line in lines:
        prod = _f(line.get("production_hours"))
        if prod > 0:
            active += 1
        sum_production += prod
        sum_operating += _f(line.get("operating_hours"))
        sum_occupied += _f(line.get("occupied_hours"))
        peak_rate = max(peak_rate, _f(line.get("rate_per_hour")))
    occupancy_pct = (sum_occupied / total_hours * 100.0) if total_hours > 0 else None
    if active <= 0:
        daily_judgment = None
        month_judgment = None
    else:
        daily_judgment = "ng" if sum_operating > daily_available else "ok"
        month_judgment = "ng" if total_hours <= 0 or sum_occupied > total_hours else "ok"
    return {
        "item_count": len(lines),
        "active_count": active,
        "total_hours": total_hours,
        "daily_available": daily_available,
        "production_hours": sum_production,
        "operating_hours": sum_operating,
        "occupied_hours": sum_occupied,
        "occupancy_pct": occupancy_pct,
        "remain_hours": total_hours - sum_occupied,
        "daily_judgment": daily_judgment,
        "month_judgment": month_judgment,
        "peak_hourly": peak_rate,
    }
