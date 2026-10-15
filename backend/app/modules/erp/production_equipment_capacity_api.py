"""生産設備能力 API（切断・面取・成型・溶接）"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.erp.models import OrderMonthly
from app.modules.erp.production_equipment_capacity_calc import calc_header, calc_line, calc_totals
from app.modules.erp.production_equipment_capacity_models import (
    ProductionEquipmentCapacity,
    ProductionEquipmentCapacityItem,
)
from app.modules.master.models import EquipmentEfficiency, Machine

router = APIRouter(prefix="/production-equipment-capacity", tags=["生産設備能力"])

PROCESSES: dict[str, str] = {
    "cutting": "切断",
    "chamfering": "面取",
    "forming": "成型",
    "welding": "溶接",
}

# production_summarys の工程列（廃棄率分析と同口径）
_PROCESS_SUMMARY_COLS: dict[str, tuple[str, str, str]] = {
    "cutting": ("cutting_actual", "cutting_defect", "cutting_scrap"),
    "chamfering": ("chamfering_actual", "chamfering_defect", "chamfering_scrap"),
    "forming": ("molding_actual", "molding_defect", "molding_scrap"),
    "welding": ("welding_actual", "welding_defect", "welding_scrap"),
}

_CLASSIFY_ORDER: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("chamfering", ("面取", "chamfer")),
    ("forming", ("成型", "成形", "forming")),
    ("welding", ("溶接", "welding")),
    ("cutting", ("切断", "cutting")),
)

_MARKS = {"", "○", "△", "×", "－", "◎"}


def _process(process: str) -> str:
    code = (process or "").strip().lower()
    if code not in PROCESSES:
        raise HTTPException(status_code=400, detail="工程は切断・面取・成型・溶接のいずれかです")
    return code


def classify_equipment(*parts: str) -> Optional[str]:
    blob = " ".join(p or "" for p in parts)
    if "外注" in blob:
        return None
    low = blob.lower()
    for code, keys in _CLASSIFY_ORDER:
        if any(k.lower() in low for k in keys):
            return code
    return None


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _pct(value: Any, default: float) -> float:
    n = _num(value, default)
    return min(100.0, max(0.0, n))


def _s(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _date_out(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    return text[:10] or None


def _date_in(value: Any) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日付は YYYY-MM-DD で指定してください") from exc


def _mark(value: Any) -> str:
    text = _s(value, 8)
    if text not in _MARKS:
        return ""
    return text


def _normalize_product_cd(cd: str) -> str:
    """製品CDの末尾を '1' にそろえる（例: 90012 → 90011）。"""
    text = (cd or "").strip()
    if not text:
        return ""
    return text[:-1] + "1"


class ItemIn(BaseModel):
    part_no: str = ""
    part_name: str = ""
    monthly_qty: float = 0
    qty_days: float = 0
    rate_per_hour: float = 0
    availability_pct: float = 100
    pass_rate_pct: float = 99
    setup_hours: float = 0
    actual_days: float = 0
    reference_rate: Optional[float] = None
    current_rate: Optional[float] = None
    takt1_date: Optional[str] = None
    takt1_ct: Optional[float] = None
    takt1_inspect: str = ""
    takt1_prep: str = ""
    takt1_overall: str = ""
    takt2_date: Optional[str] = None
    takt2_ct: Optional[float] = None
    takt2_inspect: str = ""
    takt2_prep: str = ""
    takt2_overall: str = ""
    remarks: str = ""


class HeaderIn(BaseModel):
    machine_cd: str = ""
    machine_name: str
    regular_hours: float = 7.6
    shift_count: float = 2
    overtime_hours: float = 0
    working_days: float = 22
    note: str = ""


class SaveBody(HeaderIn):
    items: list[ItemIn] = Field(default_factory=list)


class ImportMachine(BaseModel):
    machine_cd: str
    machine_name: str = ""


class ImportBody(BaseModel):
    machines: list[ImportMachine] = Field(default_factory=list)
    with_products: bool = True


def _header_dict(row: ProductionEquipmentCapacity) -> dict[str, Any]:
    return {
        "id": row.id,
        "process_cd": row.process_cd,
        "process_name": PROCESSES.get(row.process_cd, row.process_cd),
        "machine_cd": row.machine_cd,
        "machine_name": row.machine_name,
        "regular_hours": _num(row.regular_hours, 7.6),
        "shift_count": _num(row.shift_count, 2),
        "overtime_hours": _num(row.overtime_hours, 0),
        "working_days": _num(row.working_days, 22),
        "note": row.note or "",
        "sort_order": row.sort_order or 0,
    }


def _apply_header(row: ProductionEquipmentCapacity, body: HeaderIn, process: str) -> None:
    machine_cd = _s(body.machine_cd, 50)
    machine_name = _s(body.machine_name, 100)
    if not machine_cd:
        raise HTTPException(status_code=400, detail="設備コードを入力してください")
    if not machine_name:
        raise HTTPException(status_code=400, detail="設備名を入力してください")
    if body.regular_hours < 0 or body.regular_hours > 24:
        raise HTTPException(status_code=400, detail="定時間は 0〜24 時間です")
    if body.shift_count < 1 or body.shift_count > 3:
        raise HTTPException(status_code=400, detail="直数は 1〜3 です")
    if body.overtime_hours < 0 or body.overtime_hours > 12:
        raise HTTPException(status_code=400, detail="残業は 0〜12 時間です")
    if body.working_days < 0 or body.working_days > 31:
        raise HTTPException(status_code=400, detail="稼働日数は 0〜31 です")
    row.process_cd = process
    row.machine_cd = machine_cd
    row.machine_name = machine_name
    row.partner_name = None
    row.vehicle_model = None
    row.regular_hours = round(body.regular_hours, 2)
    row.shift_count = round(body.shift_count, 1)
    row.overtime_hours = round(body.overtime_hours, 2)
    row.working_days = round(body.working_days, 1)
    row.note = (body.note or "").strip() or None


def _resolve_rate_per_hour(item: ProductionEquipmentCapacityItem) -> float:
    """能率/H：保存値 → 旧 CT からの換算。"""
    rate = _num(item.reference_rate)
    if rate > 0:
        return rate
    ct = _num(item.ct_sec)
    cavity = _num(item.cavity_count, 1) or 1.0
    if ct > 0:
        return round(3600.0 / ct * cavity, 2)
    return 0.0


def _item_input(item: ProductionEquipmentCapacityItem) -> dict[str, Any]:
    rate = _resolve_rate_per_hour(item)
    return {
        "id": item.id,
        "line_no": item.line_no or 0,
        "part_no": item.part_no or "",
        "part_name": item.part_name or "",
        "monthly_qty": _num(item.monthly_qty),
        "qty_days": _num(item.qty_days),
        "rate_per_hour": rate,
        "availability_pct": round(_num(item.availability_rate, 1.0) * 100, 1),
        "pass_rate_pct": round(_num(item.first_pass_rate, 0.99) * 100, 2),
        "setup_hours": _num(item.setup_hours),
        "actual_days": _num(item.actual_days),
        "reference_rate": rate if rate > 0 else None,
        "current_rate": None if item.current_rate is None else _num(item.current_rate),
        "takt1_date": _date_out(item.takt1_date),
        "takt1_ct": None if item.takt1_ct is None else _num(item.takt1_ct),
        "takt1_inspect": item.takt1_inspect or "",
        "takt1_prep": item.takt1_prep or "",
        "takt1_overall": item.takt1_overall or "",
        "takt2_date": _date_out(item.takt2_date),
        "takt2_ct": None if item.takt2_ct is None else _num(item.takt2_ct),
        "takt2_inspect": item.takt2_inspect or "",
        "takt2_prep": item.takt2_prep or "",
        "takt2_overall": item.takt2_overall or "",
        "remarks": item.remarks or "",
    }


def _fill_item(row: ProductionEquipmentCapacityItem, src: ItemIn, line_no: int) -> None:
    avail = _pct(src.availability_pct, 100) / 100.0
    pass_r = _pct(src.pass_rate_pct, 99) / 100.0
    rate = max(_num(src.rate_per_hour), 0)
    if rate <= 0:
        rate = max(_num(src.reference_rate), 0)
    row.line_no = line_no
    row.part_no = _s(src.part_no, 50) or None
    row.part_name = _s(src.part_name, 100) or None
    row.customer_name = None
    row.survey_target = None
    row.monthly_qty = max(_num(src.monthly_qty), 0)
    row.qty_days = min(31.0, max(_num(src.qty_days), 0))
    row.ct_sec = 0
    row.availability_rate = avail
    row.first_pass_rate = pass_r
    row.cavity_count = 1
    row.setup_hours = max(_num(src.setup_hours), 0)
    row.actual_days = min(31.0, max(_num(src.actual_days), 0))
    row.reference_rate = rate if rate > 0 else None
    row.current_rate = None if src.current_rate is None else max(_num(src.current_rate), 0)
    row.takt1_date = _date_in(src.takt1_date)
    row.takt1_ct = None if src.takt1_ct is None else max(_num(src.takt1_ct), 0)
    row.takt1_inspect = _mark(src.takt1_inspect) or None
    row.takt1_prep = _mark(src.takt1_prep) or None
    row.takt1_overall = _mark(src.takt1_overall) or None
    row.takt2_date = _date_in(src.takt2_date)
    row.takt2_ct = None if src.takt2_ct is None else max(_num(src.takt2_ct), 0)
    row.takt2_inspect = _mark(src.takt2_inspect) or None
    row.takt2_prep = _mark(src.takt2_prep) or None
    row.takt2_overall = _mark(src.takt2_overall) or None
    row.remarks = _s(src.remarks, 255) or None


def _computed_items(
    items: list[dict[str, Any]], header_nums: dict[str, float]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    line_calcs: list[dict[str, Any]] = []
    for src in items:
        calc = calc_line(
            monthly_qty=src["monthly_qty"],
            qty_days=src["qty_days"],
            rate_per_hour=src.get("rate_per_hour") or src.get("reference_rate") or 0,
            availability_rate=_num(src["availability_pct"]) / 100.0,
            pass_rate=_num(src["pass_rate_pct"]) / 100.0,
            setup_hours=src["setup_hours"],
            actual_days=src["actual_days"],
            daily_available=header_nums["daily_available"],
            total_hours=header_nums["total_hours"],
        )
        line_calcs.append(calc)
        enriched.append({**src, **calc})
    return enriched, calc_totals(line_calcs, header_nums)


def _detail_payload(
    header: ProductionEquipmentCapacity,
    items: list[ProductionEquipmentCapacityItem],
    *,
    machine_availability_pct: Optional[float] = None,
) -> dict[str, Any]:
    head = _header_dict(header)
    nums = calc_header(
        head["regular_hours"], head["shift_count"], head["overtime_hours"], head["working_days"]
    )
    inputs = [_item_input(it) for it in items]
    enriched, summary = _computed_items(inputs, nums)
    payload = {**head, **nums, "items": enriched, "summary": summary}
    if machine_availability_pct is not None:
        payload["machine_availability_pct"] = round(float(machine_availability_pct), 1)
    return payload


def _three_month_range(today: Optional[date] = None) -> tuple[date, date]:
    """直近3ヶ月（当月含む）の実績期間。"""
    end = today or date.today()
    y, m = end.year, end.month
    for _ in range(2):
        m -= 1
        if m <= 0:
            m = 12
            y -= 1
    start = date(y, m, 1)
    return start, end


async def _machine_availability_pct(db: AsyncSession, machine_cd: str) -> float:
    row = (
        await db.execute(select(Machine.availability_rate).where(Machine.machine_cd == machine_cd))
    ).scalar()
    if row is None:
        return 100.0
    return round(_num(row, 100.0), 1)


async def _pass_rates_3m(
    db: AsyncSession, process: str, product_cds: list[str]
) -> dict[str, float]:
    """廃棄率分析と同口径：工程の (不良+廃棄)/実績 から合格率%を直近3ヶ月加重平均。"""
    cols = _PROCESS_SUMMARY_COLS.get(process)
    if not cols:
        return {}
    keys = {_normalize_product_cd(cd) for cd in product_cds if _normalize_product_cd(cd)}
    if not keys:
        return {}
    actual_col, defect_col, scrap_col = cols
    start, end = _three_month_range()
    sql = text(
        f"""
        SELECT
          CONCAT(SUBSTRING(TRIM(product_cd), 1, LENGTH(TRIM(product_cd)) - 1), '1') AS product_key,
          SUM(COALESCE(`{actual_col}`, 0)) AS sum_actual,
          SUM(COALESCE(`{defect_col}`, 0) + COALESCE(`{scrap_col}`, 0)) AS sum_bad
        FROM production_summarys
        WHERE `date` >= :start_date
          AND `date` <= :end_date
          AND product_cd IS NOT NULL
          AND TRIM(product_cd) != ''
        GROUP BY product_key
        """
    )
    rows = (await db.execute(sql, {"start_date": start, "end_date": end})).all()
    out: dict[str, float] = {}
    for product_key, sum_actual, sum_bad in rows:
        key = _s(product_key, 50)
        if key not in keys:
            continue
        actual = _num(sum_actual)
        if actual <= 0:
            continue
        bad = min(actual, max(_num(sum_bad), 0))
        out[key] = round((1.0 - bad / actual) * 100.0, 2)
    return out


async def _enrich_items_metrics(
    db: AsyncSession,
    process: str,
    machine_cd: str,
    items: list[ItemIn],
) -> list[ItemIn]:
    """能率・可動率・合格率をマスタ／実績から埋める。"""
    avail = await _machine_availability_pct(db, machine_cd)
    part_nos = [it.part_no for it in items if it.part_no]
    pass_map = await _pass_rates_3m(db, process, part_nos)
    for it in items:
        it.availability_pct = avail
        key = _normalize_product_cd(it.part_no)
        if key in pass_map:
            it.pass_rate_pct = pass_map[key]
        elif it.pass_rate_pct <= 0:
            it.pass_rate_pct = 99
    return items


async def _load_header(
    db: AsyncSession, process: str, capacity_id: int
) -> ProductionEquipmentCapacity:
    row = await db.get(ProductionEquipmentCapacity, capacity_id)
    if row is None or row.process_cd != process:
        raise HTTPException(status_code=404, detail="設備が見つかりません")
    return row


async def _items_of(db: AsyncSession, capacity_id: int) -> list[ProductionEquipmentCapacityItem]:
    result = await db.execute(
        select(ProductionEquipmentCapacityItem)
        .where(ProductionEquipmentCapacityItem.capacity_id == capacity_id)
        .order_by(ProductionEquipmentCapacityItem.line_no, ProductionEquipmentCapacityItem.id)
    )
    return list(result.scalars().all())


async def _replace_items(
    db: AsyncSession, capacity_id: int, items: list[ItemIn]
) -> list[ProductionEquipmentCapacityItem]:
    if len(items) > 300:
        raise HTTPException(status_code=400, detail="品目は 300 行までです")
    existing = await _items_of(db, capacity_id)
    for old in existing:
        await db.delete(old)
    await db.flush()
    created: list[ProductionEquipmentCapacityItem] = []
    for index, src in enumerate(items, start=1):
        row = ProductionEquipmentCapacityItem(capacity_id=capacity_id)
        _fill_item(row, src, index)
        db.add(row)
        created.append(row)
    await db.flush()
    return created


def _rate_to_item(
    eff: EquipmentEfficiency,
    working_days: float,
    *,
    availability_pct: float = 100,
    pass_rate_pct: float = 99,
) -> Optional[ItemIn]:
    std = _num(eff.efficiency_rate)
    cur = _num(eff.current_efficiency_rate)
    rate = cur if cur > 0 else std
    part_no = _s(eff.product_cd, 50)
    part_name = _s(eff.product_name, 100)
    if rate <= 0 or (not part_no and not part_name):
        return None
    return ItemIn(
        part_no=part_no or part_name[:50],
        part_name=part_name,
        monthly_qty=0,
        qty_days=working_days,
        rate_per_hour=rate,
        availability_pct=availability_pct,
        pass_rate_pct=pass_rate_pct,
        setup_hours=round(_num(eff.step_time) / 60.0, 3),
        actual_days=working_days,
        reference_rate=rate,
        current_rate=cur if cur > 0 else None,
    )


async def _efficiency_rows(
    db: AsyncSession, machine_cd: str, machine_name: str
) -> list[EquipmentEfficiency]:
    conds = []
    if machine_cd:
        conds.append(EquipmentEfficiency.machine_cd == machine_cd)
    if machine_name:
        conds.append(EquipmentEfficiency.machines_name == machine_name)
    if not conds:
        return []
    result = await db.execute(
        select(EquipmentEfficiency).where(
            or_(*conds),
            or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status != 0),
        )
    )
    return list(result.scalars().all())


async def _suggestions(db: AsyncSession, process: str, existing: set[str]) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    machines = (
        await db.execute(
            select(
                Machine.machine_cd, Machine.machine_name, Machine.machine_type, Machine.is_active
            )
        )
    ).all()
    for cd, name, machine_type, active in machines:
        if active is False:
            continue
        if classify_equipment(cd or "", name or "", machine_type or "") != process:
            continue
        key = _s(cd, 50)
        if not key or key in existing:
            continue
        found[key] = {
            "machine_cd": key,
            "machine_name": _s(name, 100) or key,
            "source": "machines",
            "product_count": 0,
        }

    grouped = (
        await db.execute(
            select(
                EquipmentEfficiency.machine_cd,
                EquipmentEfficiency.machines_name,
                func.count(EquipmentEfficiency.id),
            )
            .where(or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status != 0))
            .group_by(EquipmentEfficiency.machine_cd, EquipmentEfficiency.machines_name)
        )
    ).all()
    for cd, name, count in grouped:
        if classify_equipment(cd or "", name or "") != process:
            continue
        key = _s(cd, 50) or _s(name, 50)
        if not key or key in existing:
            continue
        product_count = int(count or 0)
        if key in found:
            found[key]["product_count"] = int(found[key]["product_count"]) + product_count
            found[key]["source"] = "both"
            if not found[key]["machine_name"]:
                found[key]["machine_name"] = _s(name, 100) or key
        else:
            found[key] = {
                "machine_cd": key,
                "machine_name": _s(name, 100) or key,
                "source": "efficiency",
                "product_count": product_count,
            }
    return sorted(found.values(), key=lambda row: (row["machine_name"], row["machine_cd"]))


@router.get("/{process}")
async def list_equipment(
    process: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    code = _process(process)
    headers = list(
        (
            await db.execute(
                select(ProductionEquipmentCapacity)
                .where(ProductionEquipmentCapacity.process_cd == code)
                .order_by(ProductionEquipmentCapacity.sort_order, ProductionEquipmentCapacity.id)
            )
        )
        .scalars()
        .all()
    )
    ids = [row.id for row in headers]
    grouped: dict[int, list[ProductionEquipmentCapacityItem]] = defaultdict(list)
    if ids:
        item_rows = (
            (
                await db.execute(
                    select(ProductionEquipmentCapacityItem)
                    .where(ProductionEquipmentCapacityItem.capacity_id.in_(ids))
                    .order_by(
                        ProductionEquipmentCapacityItem.line_no, ProductionEquipmentCapacityItem.id
                    )
                )
            )
            .scalars()
            .all()
        )
        for item in item_rows:
            grouped[item.capacity_id].append(item)

    payload = []
    for header in headers:
        detail = _detail_payload(header, grouped.get(header.id, []))
        payload.append(
            {
                "id": detail["id"],
                "machine_cd": detail["machine_cd"],
                "machine_name": detail["machine_name"],
                "regular_hours": detail["regular_hours"],
                "shift_count": detail["shift_count"],
                "overtime_hours": detail["overtime_hours"],
                "working_days": detail["working_days"],
                "summary": detail["summary"],
            }
        )
    existing = {row.machine_cd for row in headers}
    return {
        "success": True,
        "data": {
            "process_cd": code,
            "process_name": PROCESSES[code],
            "equipments": payload,
            "suggestions": await _suggestions(db, code, existing),
        },
    }


@router.get("/{process}/forecast-monthly")
async def forecast_monthly(
    process: str,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    """月内示を製品CD末尾1にそろえて合算する（設定数/月へ反映用）。"""
    _process(process)
    if year < 2000 or year > 2100:
        raise HTTPException(status_code=400, detail="年が不正です")
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="月は 1〜12 です")
    rows = (
        await db.execute(
            select(
                OrderMonthly.product_cd,
                OrderMonthly.product_name,
                OrderMonthly.forecast_units,
            ).where(OrderMonthly.year == year, OrderMonthly.month == month)
        )
    ).all()
    buckets: dict[str, dict[str, Any]] = {}
    for product_cd, product_name, forecast_units in rows:
        key = _normalize_product_cd(product_cd or "")
        if not key:
            continue
        qty = int(forecast_units or 0)
        bucket = buckets.get(key)
        if bucket is None:
            buckets[key] = {
                "product_cd": key,
                "product_name": _s(product_name, 100),
                "monthly_qty": qty,
            }
            continue
        bucket["monthly_qty"] = int(bucket["monthly_qty"]) + qty
        # 末尾が既に 1 の行の品名を優先
        if (product_cd or "").strip().endswith("1") and product_name:
            bucket["product_name"] = _s(product_name, 100)
        elif not bucket["product_name"] and product_name:
            bucket["product_name"] = _s(product_name, 100)
    items = sorted(
        (b for b in buckets.values() if int(b["monthly_qty"]) > 0),
        key=lambda row: row["product_cd"],
    )
    return {
        "success": True,
        "data": {
            "year": year,
            "month": month,
            "item_count": len(items),
            "total_qty": sum(int(i["monthly_qty"]) for i in items),
            "items": items,
        },
    }


@router.get("/{process}/{capacity_id}")
async def get_equipment(
    process: str,
    capacity_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    code = _process(process)
    header = await _load_header(db, code, capacity_id)
    items = await _items_of(db, header.id)
    avail = await _machine_availability_pct(db, header.machine_cd)
    return {
        "success": True,
        "data": _detail_payload(header, items, machine_availability_pct=avail),
    }


@router.post("/{process}")
async def create_equipment(
    process: str,
    body: HeaderIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    code = _process(process)
    current_max = (
        await db.execute(
            select(func.max(ProductionEquipmentCapacity.sort_order)).where(
                ProductionEquipmentCapacity.process_cd == code
            )
        )
    ).scalar()
    row = ProductionEquipmentCapacity(sort_order=int(current_max or 0) + 1)
    _apply_header(row, body, code)
    db.add(row)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=400, detail="同じ設備コードがこの工程に既にあります"
        ) from exc
    return {"success": True, "data": _detail_payload(row, [])}


@router.put("/{process}/{capacity_id}")
async def save_equipment(
    process: str,
    capacity_id: int,
    body: SaveBody,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    code = _process(process)
    header = await _load_header(db, code, capacity_id)
    _apply_header(header, body, code)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=400, detail="同じ設備コードがこの工程に既にあります"
        ) from exc
    items = await _replace_items(db, header.id, body.items)
    return {"success": True, "data": _detail_payload(header, items)}


@router.delete("/{process}/{capacity_id}")
async def delete_equipment(
    process: str,
    capacity_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    code = _process(process)
    header = await _load_header(db, code, capacity_id)
    items = await _items_of(db, header.id)
    for item in items:
        await db.delete(item)
    await db.delete(header)
    await db.flush()
    return {"success": True}


@router.post("/{process}/import-master")
async def import_master(
    process: str,
    body: ImportBody,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    code = _process(process)
    if not body.machines:
        raise HTTPException(status_code=400, detail="取り込む設備を選択してください")
    if len(body.machines) > 80:
        raise HTTPException(status_code=400, detail="一度に取り込める設備は 80 台までです")
    created_ids: list[int] = []
    skipped: list[str] = []
    current_max = (
        await db.execute(
            select(func.max(ProductionEquipmentCapacity.sort_order)).where(
                ProductionEquipmentCapacity.process_cd == code
            )
        )
    ).scalar()
    sort_order = int(current_max or 0)
    for src in body.machines:
        machine_cd = _s(src.machine_cd, 50)
        machine_name = _s(src.machine_name, 100) or machine_cd
        if not machine_cd:
            continue
        exists = (
            await db.execute(
                select(ProductionEquipmentCapacity.id).where(
                    ProductionEquipmentCapacity.process_cd == code,
                    ProductionEquipmentCapacity.machine_cd == machine_cd,
                )
            )
        ).scalar()
        if exists:
            skipped.append(machine_cd)
            continue
        sort_order += 1
        header = ProductionEquipmentCapacity(sort_order=sort_order)
        _apply_header(
            header,
            HeaderIn(machine_cd=machine_cd, machine_name=machine_name),
            code,
        )
        db.add(header)
        try:
            await db.flush()
        except IntegrityError:
            skipped.append(machine_cd)
            continue
        if body.with_products:
            days = _num(header.working_days, 22)
            avail = await _machine_availability_pct(db, machine_cd)
            products: dict[str, ItemIn] = {}
            for eff in await _efficiency_rows(db, machine_cd, machine_name):
                item = _rate_to_item(eff, days, availability_pct=avail)
                if item is None:
                    continue
                products[item.part_no] = item
            if products:
                enriched = await _enrich_items_metrics(
                    db, code, machine_cd, list(products.values())[:300]
                )
                await _replace_items(db, header.id, enriched)
        created_ids.append(header.id)
    return {"success": True, "data": {"created_ids": created_ids, "skipped": skipped}}


@router.post("/{process}/{capacity_id}/import-rates")
async def import_rates(
    process: str,
    capacity_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    """設備能率（本/H）・設備マスタ可動率・直近3ヶ月合格率を品目へ反映する。"""
    code = _process(process)
    header = await _load_header(db, code, capacity_id)
    days = _num(header.working_days, 22)
    avail = await _machine_availability_pct(db, header.machine_cd)
    current = await _items_of(db, header.id)
    by_part: dict[str, ItemIn] = {}
    order: list[str] = []
    for item in current:
        src = ItemIn(**{k: v for k, v in _item_input(item).items() if k not in {"id", "line_no"}})
        key = src.part_no or f"__row_{item.id}"
        by_part[key] = src
        order.append(key)

    added = 0
    updated = 0
    for eff in await _efficiency_rows(db, header.machine_cd, header.machine_name):
        incoming = _rate_to_item(eff, days, availability_pct=avail)
        if incoming is None:
            continue
        key = incoming.part_no
        if key in by_part:
            kept = by_part[key]
            kept.part_name = incoming.part_name or kept.part_name
            kept.rate_per_hour = incoming.rate_per_hour
            kept.setup_hours = incoming.setup_hours
            kept.reference_rate = incoming.reference_rate
            kept.current_rate = incoming.current_rate
            kept.availability_pct = avail
            updated += 1
        else:
            by_part[key] = incoming
            order.append(key)
            added += 1
    if added == 0 and updated == 0:
        raise HTTPException(status_code=404, detail="この設備の設備能率が見つかりません")
    merged = [by_part[key] for key in order if key in by_part][:300]
    merged = await _enrich_items_metrics(db, code, header.machine_cd, merged)
    items = await _replace_items(db, header.id, merged)
    return {
        "success": True,
        "data": _detail_payload(header, items, machine_availability_pct=avail),
        "meta": {"added": added, "updated": updated},
    }


@router.post("/{process}/{capacity_id}/refresh-metrics")
async def refresh_metrics(
    process: str,
    capacity_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(verify_token_and_get_user),
):
    """既存品目の能率・可動率・合格率だけを再取得して保存する（設定数は維持）。"""
    code = _process(process)
    header = await _load_header(db, code, capacity_id)
    days = _num(header.working_days, 22)
    avail = await _machine_availability_pct(db, header.machine_cd)
    current = await _items_of(db, header.id)
    if not current:
        raise HTTPException(status_code=404, detail="品目がありません")

    rate_by_part: dict[str, tuple[float, Optional[float], float]] = {}
    for eff in await _efficiency_rows(db, header.machine_cd, header.machine_name):
        incoming = _rate_to_item(eff, days, availability_pct=avail)
        if incoming is None:
            continue
        rate_by_part[incoming.part_no] = (
            incoming.rate_per_hour,
            incoming.current_rate,
            incoming.setup_hours,
        )

    items_in: list[ItemIn] = []
    for item in current:
        src = ItemIn(**{k: v for k, v in _item_input(item).items() if k not in {"id", "line_no"}})
        hit = rate_by_part.get(src.part_no) or rate_by_part.get(_normalize_product_cd(src.part_no))
        if hit:
            src.rate_per_hour = hit[0]
            src.reference_rate = hit[0]
            src.current_rate = hit[1]
            if hit[2] > 0:
                src.setup_hours = hit[2]
        src.availability_pct = avail
        items_in.append(src)

    items_in = await _enrich_items_metrics(db, code, header.machine_cd, items_in)
    saved = await _replace_items(db, header.id, items_in)
    return {
        "success": True,
        "data": _detail_payload(header, saved, machine_availability_pct=avail),
        "meta": {
            "availability_pct": avail,
            "period": {
                "start": _three_month_range()[0].isoformat(),
                "end": _three_month_range()[1].isoformat(),
            },
        },
    }
