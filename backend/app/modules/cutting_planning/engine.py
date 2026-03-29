from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


DEFAULT_EFFICIENCY_RATE = 60.0


def parse_sql_date(value: Any) -> date | None:
    """instruction_plans.start_date / end_date 等を date に正規化"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def subtract_business_days_backward(from_day: date, business_days: int) -> date:
    """from_day から遡って business_days 営業日分（土日除く）移動した日付（database.api の _subtract_business_days と同趣旨）"""
    if business_days <= 0:
        return from_day
    remaining = int(business_days)
    current = from_day
    while remaining > 0:
        current -= timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


def compute_recommended_cutting_start_date(
    forming_start: date | None,
    cuting_process_lt: int | None,
    forming_process_lt: int | None,
) -> date | None:
    """
    成型開始予定日 start_date から、BOM の (切断LT - 成型LT) 営業日を遡った日を
    切断開始の目安とする。forming_start が無い場合は制約なし。
    """
    if forming_start is None:
        return None
    c_lt = as_int(cuting_process_lt, 0)
    f_lt = as_int(forming_process_lt, 0)
    delta = c_lt - f_lt
    if delta <= 0:
        return forming_start
    return subtract_business_days_backward(forming_start, delta)


def bom_int_key_for_product_cd(product_cd: str) -> int | None:
    s = str(product_cd or "").strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        try:
            return int(float(s))
        except ValueError:
            return None


def parse_month(value: str) -> date:
    parts = (value or "").strip().split("-")
    if len(parts) != 2:
        raise ValueError("production_month must be YYYY-MM")
    year = int(parts[0])
    month = int(parts[1])
    return date(year, month, 1)


def month_end(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1) - timedelta(days=1)
    return date(d.year, d.month + 1, 1) - timedelta(days=1)


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def as_time(value: Any, default: time) -> time:
    """DB 驱动可能返回 str / timedelta；datetime.combine 需要 time。"""
    if value is None:
        return default
    if isinstance(value, time):
        return value.replace(microsecond=0)
    if isinstance(value, datetime):
        return value.time().replace(microsecond=0)
    if isinstance(value, timedelta):
        secs = int(value.total_seconds()) % 86400
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        return time(h, m, s)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return default
        for fmt in ("%H:%M:%S.%f", "%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(s, fmt).time().replace(microsecond=0)
            except ValueError:
                continue
        return default
    return default


def combine_dt(work_date: date, work_time: time) -> datetime:
    return datetime.combine(work_date, work_time)


@dataclass
class MachineInfo:
    id: int
    machine_cd: str
    machine_name: str
    default_work_hours: float
    available_from: time
    available_to: time


@dataclass
class TimeSegment:
    machine_id: int
    machine_name: str
    start_at: datetime
    end_at: datetime
    work_date: date

    @property
    def minutes(self) -> float:
        return max((self.end_at - self.start_at).total_seconds() / 60.0, 0.0)


@dataclass
class FixedReservation:
    item_id: int
    machine_id: int
    machine_name: str
    start_at: datetime
    end_at: datetime


@dataclass
class ScheduleSlice:
    work_date: date
    period_start: time
    period_end: time
    planned_qty: int
    sort_order: int


@dataclass
class PlannedItem:
    instruction_plan_id: int | None
    source_management_code: str | None
    product_cd: str
    product_name: str
    material_name: str | None
    production_line: str | None
    planned_quantity: int
    production_lot_size: int | None
    lot_number: str | None
    take_count: int | None
    cutting_length: float | None
    instruction_production_quantity: int = 0
    id: int | None = None
    assigned_machine_id: int | None = None
    assigned_machine: str | None = None
    sequence_no: int = 0
    planned_day: date | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    estimated_minutes: float = 0.0
    efficiency_rate: float | None = None
    setup_time_min: int | None = None
    is_locked: bool = False
    publish_status: str = "PLANNED"
    published_cutting_id: int | None = None
    actual_quantity: int = 0
    completion_status: str = "PLANNED"
    forming_start_date: date | None = None
    forming_end_date: date | None = None
    recommended_cutting_start_date: date | None = None
    priority_order: int = 999999
    slices: list[ScheduleSlice] | None = None


async def fetch_cutting_machines(db: AsyncSession, machine_ids: list[int] | None = None) -> list[MachineInfo]:
    sql = """
        SELECT id, machine_cd, machine_name,
               COALESCE(default_work_hours, 8) AS default_work_hours,
               COALESCE(available_from, '08:00:00') AS available_from,
               COALESCE(available_to, '17:00:00') AS available_to
        FROM machines
        WHERE machine_name LIKE '%切断%'
          AND COALESCE(status, 'active') <> 'inactive'
    """
    params: dict[str, Any] = {}
    if machine_ids:
        placeholders = ", ".join(f":mid_{idx}" for idx, _ in enumerate(machine_ids))
        sql += f" AND id IN ({placeholders})"
        params.update({f"mid_{idx}": mid for idx, mid in enumerate(machine_ids)})
    sql += " ORDER BY machine_cd"
    res = await db.execute(text(sql), params)
    rows = res.mappings().all()
    return [
        MachineInfo(
            id=as_int(r["id"]),
            machine_cd=str(r["machine_cd"] or ""),
            machine_name=str(r["machine_name"] or ""),
            default_work_hours=as_float(r["default_work_hours"], 8.0),
            available_from=as_time(r["available_from"], time(8, 0, 0)),
            available_to=as_time(r["available_to"], time(17, 0, 0)),
        )
        for r in rows
    ]


async def fetch_instruction_plans(db: AsyncSession, production_month: date) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT id, production_month, production_line, priority_order, product_cd, product_name,
               planned_quantity, production_lot_size, lot_number, management_code, actual_production_quantity,
               take_count, cutting_length, material_name, start_date, end_date
        FROM instruction_plans
        WHERE production_month = :production_month
          AND COALESCE(is_cutting_instructed, 0) = 1
        ORDER BY COALESCE(priority_order, 999999), id
        """
    )
    res = await db.execute(sql, {"production_month": production_month})
    return [dict(row) for row in res.mappings().all()]


async def fetch_efficiency_map(
    db: AsyncSession,
    product_codes: Iterable[str],
    machine_names: Iterable[str],
) -> dict[tuple[str, str], tuple[float, int]]:
    products = [p for p in {str(x or "").strip() for x in product_codes} if p]
    machines = [m for m in {str(x or "").strip() for x in machine_names} if m]
    if not products or not machines:
        return {}
    prod_placeholders = ", ".join(f":pc_{idx}" for idx, _ in enumerate(products))
    machine_placeholders = ", ".join(f":mn_{idx}" for idx, _ in enumerate(machines))
    params: dict[str, Any] = {
        **{f"pc_{idx}": pc for idx, pc in enumerate(products)},
        **{f"mn_{idx}": mn for idx, mn in enumerate(machines)},
    }
    sql = text(
        f"""
        SELECT product_cd, machines_name, efficiency_rate, step_time
        FROM equipment_efficiency
        WHERE product_cd IN ({prod_placeholders})
          AND machines_name IN ({machine_placeholders})
        """
    )
    res = await db.execute(sql, params)
    out: dict[tuple[str, str], tuple[float, int]] = {}
    for row in res.mappings().all():
        out[(str(row["product_cd"] or ""), str(row["machines_name"] or ""))] = (
            max(as_float(row["efficiency_rate"], DEFAULT_EFFICIENCY_RATE), 1.0),
            max(as_int(row["step_time"], 0), 0),
        )
    return out


async def fetch_process_bom_cutting_forming_lt(
    db: AsyncSession,
    product_codes: Iterable[str],
) -> dict[int, tuple[int | None, int | None]]:
    """product_process_bom.product_cd（整数PK）→ (cuting_process_lt, forming_process_lt)"""
    keys = {bom_int_key_for_product_cd(pc) for pc in product_codes}
    keys.discard(None)
    int_ids = [k for k in keys if k is not None]
    if not int_ids:
        return {}
    ph = ", ".join(f":bom_{idx}" for idx, _ in enumerate(int_ids))
    params = {f"bom_{idx}": i for idx, i in enumerate(int_ids)}
    sql = text(
        f"""
        SELECT product_cd, cuting_process_lt, forming_process_lt
        FROM product_process_bom
        WHERE product_cd IN ({ph})
        """
    )
    res = await db.execute(sql, params)
    out: dict[int, tuple[int | None, int | None]] = {}
    for row in res.mappings().all():
        pid = as_int(row["product_cd"])
        out[pid] = (row.get("cuting_process_lt"), row.get("forming_process_lt"))
    return out


async def fetch_eligible_machine_names_by_product(
    db: AsyncSession,
    product_codes: Iterable[str],
) -> dict[str, set[str]]:
    """equipment_efficiency 上に組み合わせがある製品のみ、その設備名集合（切断機候補）"""
    products = sorted({str(x or "").strip() for x in product_codes if str(x or "").strip()})
    if not products:
        return {}
    ph = ", ".join(f":ep_{idx}" for idx, _ in enumerate(products))
    params = {f"ep_{idx}": pc for idx, pc in enumerate(products)}
    sql = text(
        f"""
        SELECT DISTINCT product_cd, machines_name
        FROM equipment_efficiency
        WHERE product_cd IN ({ph})
          AND machines_name IS NOT NULL
          AND TRIM(machines_name) <> ''
        """
    )
    res = await db.execute(sql, params)
    out: dict[str, set[str]] = defaultdict(set)
    for row in res.mappings().all():
        pc = str(row["product_cd"] or "").strip()
        mn = str(row["machines_name"] or "").strip()
        if pc and mn:
            out[pc].add(mn)
    return dict(out)


async def fetch_time_slots(
    db: AsyncSession,
    machine_ids: Iterable[int],
    start_date: date,
    end_date: date,
) -> dict[tuple[int, date], list[tuple[time, time]]]:
    ids = [int(x) for x in set(machine_ids)]
    if not ids:
        return {}
    placeholders = ", ".join(f":lid_{idx}" for idx, _ in enumerate(ids))
    params = {
        **{f"lid_{idx}": lid for idx, lid in enumerate(ids)},
        "start_date": start_date,
        "end_date": end_date,
    }
    sql = text(
        f"""
        SELECT line_id, work_date, start_time, end_time, sort_order
        FROM line_capacity_time_slots
        WHERE line_id IN ({placeholders})
          AND work_date BETWEEN :start_date AND :end_date
          AND COALESCE(is_rest, 0) = 0
        ORDER BY line_id, work_date, sort_order, start_time
        """
    )
    res = await db.execute(sql, params)
    out: dict[tuple[int, date], list[tuple[time, time]]] = defaultdict(list)
    for row in res.mappings().all():
        out[(as_int(row["line_id"]), row["work_date"])].append(
            (
                as_time(row["start_time"], time(0, 0, 0)),
                as_time(row["end_time"], time(23, 59, 59)),
            )
        )
    return out


async def fetch_line_capacities(
    db: AsyncSession,
    machine_ids: Iterable[int],
    start_date: date,
    end_date: date,
) -> dict[tuple[int, date], float]:
    """line_capacities: (line_id, work_date) → available_hours（日別カレンダー）"""
    ids = [int(x) for x in set(machine_ids)]
    if not ids:
        return {}
    placeholders = ", ".join(f":lcid_{idx}" for idx, _ in enumerate(ids))
    params = {
        **{f"lcid_{idx}": lid for idx, lid in enumerate(ids)},
        "start_date": start_date,
        "end_date": end_date,
    }
    sql = text(
        f"""
        SELECT line_id, work_date, available_hours
        FROM line_capacities
        WHERE line_id IN ({placeholders})
          AND work_date BETWEEN :start_date AND :end_date
        """
    )
    res = await db.execute(sql, params)
    out: dict[tuple[int, date], float] = {}
    for row in res.mappings().all():
        lid = as_int(row["line_id"])
        wd = row["work_date"]
        if isinstance(wd, datetime):
            wd = wd.date()
        out[(lid, wd)] = as_float(row["available_hours"], 0.0)
    return out


def _virtual_segment_from_available_hours(work_date: date, avail_hours: float) -> tuple[datetime, datetime] | None:
    """APS 成型排产と同様：時間帯行が無い日は 06:00 から available_hours 分を仮想稼働とする。"""
    h = float(avail_hours)
    if h <= 0:
        return None
    span_min = max(0, int(round(h * 60)))
    start_at = combine_dt(work_date, time(6, 0, 0))
    end_at = start_at + timedelta(minutes=span_min)
    if end_at <= start_at:
        return None
    return start_at, end_at


async def get_or_create_run(db: AsyncSession, production_month: date) -> int:
    existing = await db.execute(
        text("SELECT id FROM cutting_plan_runs WHERE production_month = :production_month"),
        {"production_month": production_month},
    )
    run_id = existing.scalar_one_or_none()
    if run_id is not None:
        return as_int(run_id)
    await db.execute(
        text(
            """
            INSERT INTO cutting_plan_runs (production_month, status, generated_at)
            VALUES (:production_month, 'DRAFT', NOW())
            """
        ),
        {"production_month": production_month},
    )
    res = await db.execute(text("SELECT LAST_INSERT_ID()"))
    return as_int(res.scalar_one())


async def fetch_run_items(db: AsyncSession, run_id: int) -> list[PlannedItem]:
    # 生産数は instruction_plans.actual_production_quantity を JOIN で取得（207 カラム未適用でも一覧取得可）
    sql = text(
        """
        SELECT
            cpi.id, cpi.instruction_plan_id, cpi.source_management_code, cpi.product_cd, cpi.product_name, cpi.material_name,
            cpi.production_line, cpi.planned_quantity,
            COALESCE(ip.actual_production_quantity, 0) AS instruction_production_quantity,
            cpi.production_lot_size, cpi.lot_number, cpi.take_count, cpi.cutting_length,
            cpi.assigned_machine_id, cpi.assigned_machine, cpi.sequence_no, cpi.planned_day, cpi.planned_start, cpi.planned_end,
            cpi.estimated_minutes, cpi.efficiency_rate, cpi.setup_time_min, cpi.is_locked, cpi.publish_status, cpi.published_cutting_id,
            cpi.actual_quantity, cpi.completion_status
        FROM cutting_plan_items cpi
        LEFT JOIN instruction_plans ip ON cpi.instruction_plan_id = ip.id
        WHERE cpi.run_id = :run_id
        ORDER BY cpi.assigned_machine_id, cpi.sequence_no, cpi.id
        """
    )
    res = await db.execute(sql, {"run_id": run_id})
    items: list[tuple[int, PlannedItem]] = []
    for row in res.mappings().all():
        items.append((
            as_int(row["id"]),
            PlannedItem(
                id=as_int(row["id"]),
                instruction_plan_id=as_int(row["instruction_plan_id"]) if row["instruction_plan_id"] is not None else None,
                source_management_code=row["source_management_code"],
                product_cd=str(row["product_cd"] or ""),
                product_name=str(row["product_name"] or ""),
                material_name=row["material_name"],
                production_line=row["production_line"],
                planned_quantity=as_int(row["planned_quantity"]),
                production_lot_size=as_int(row["production_lot_size"]) if row["production_lot_size"] is not None else None,
                lot_number=row["lot_number"],
                take_count=as_int(row["take_count"]) if row["take_count"] is not None else None,
                cutting_length=as_float(row["cutting_length"]) if row["cutting_length"] is not None else None,
                instruction_production_quantity=as_int(row["instruction_production_quantity"]),
                assigned_machine_id=as_int(row["assigned_machine_id"]) if row["assigned_machine_id"] is not None else None,
                assigned_machine=row["assigned_machine"],
                sequence_no=as_int(row["sequence_no"]),
                planned_day=row["planned_day"],
                planned_start=row["planned_start"],
                planned_end=row["planned_end"],
                estimated_minutes=as_float(row["estimated_minutes"]),
                efficiency_rate=as_float(row["efficiency_rate"]) if row["efficiency_rate"] is not None else None,
                setup_time_min=as_int(row["setup_time_min"]) if row["setup_time_min"] is not None else None,
                is_locked=bool(row["is_locked"]),
                publish_status=str(row["publish_status"] or "PLANNED"),
                published_cutting_id=as_int(row["published_cutting_id"]) if row["published_cutting_id"] is not None else None,
                actual_quantity=as_int(row["actual_quantity"]),
                completion_status=str(row["completion_status"] or "PLANNED"),
                slices=[],
            )
        ))
    if not items:
        return []
    slice_sql = text(
        """
        SELECT item_id, work_date, period_start, period_end, planned_qty, sort_order
        FROM cutting_plan_slices
        WHERE run_id = :run_id
        ORDER BY item_id, sort_order, work_date, period_start
        """
    )
    slice_res = await db.execute(slice_sql, {"run_id": run_id})
    slice_map: dict[int, list[ScheduleSlice]] = defaultdict(list)
    for row in slice_res.mappings().all():
        slice_map[as_int(row["item_id"])].append(
            ScheduleSlice(
                work_date=row["work_date"],
                period_start=as_time(row["period_start"], time(0, 0, 0)),
                period_end=as_time(row["period_end"], time(23, 59, 59)),
                planned_qty=as_int(row["planned_qty"]),
                sort_order=as_int(row["sort_order"]),
            )
        )
    out: list[PlannedItem] = []
    for item_id, item in items:
        item.slices = slice_map.get(item_id, [])
        out.append(item)
    return out


async def fetch_existing_fixed_items(db: AsyncSession, run_id: int) -> list[PlannedItem]:
    items = await fetch_run_items(db, run_id)
    return [item for item in items if item.is_locked or item.published_cutting_id is not None]


def build_segments(
    machines: list[MachineInfo],
    slot_map: dict[tuple[int, date], list[tuple[time, time]]],
    start_date: date,
    end_date: date,
    capacity_map: dict[tuple[int, date], float] | None = None,
) -> dict[int, list[TimeSegment]]:
    """
    稼働区間：line_capacity_time_slots（非休憩）を優先。
    その日に稼働帯行が無い場合は line_capacities.available_hours（0 なら休み）、
    行も無ければ machines の available_from / available_to。
    """
    out: dict[int, list[TimeSegment]] = defaultdict(list)
    cap = capacity_map or {}
    for machine in machines:
        current = start_date
        while current <= end_date:
            slots = slot_map.get((machine.id, current))
            if slots:
                slot_iter: list[tuple[time, time]] = slots
            else:
                hours = cap.get((machine.id, current))
                if hours is not None:
                    virt = _virtual_segment_from_available_hours(current, hours)
                    if virt is None:
                        current += timedelta(days=1)
                        continue
                    start_at, end_at = virt
                    out[machine.id].append(
                        TimeSegment(
                            machine_id=machine.id,
                            machine_name=machine.machine_name,
                            start_at=start_at,
                            end_at=end_at,
                            work_date=current,
                        )
                    )
                    current += timedelta(days=1)
                    continue
                slot_iter = [(machine.available_from, machine.available_to)]
            for start_time, end_time in slot_iter:
                start_at = combine_dt(current, start_time)
                end_at = combine_dt(current, end_time)
                if end_at <= start_at:
                    end_at += timedelta(days=1)
                if end_at > start_at:
                    out[machine.id].append(
                        TimeSegment(
                            machine_id=machine.id,
                            machine_name=machine.machine_name,
                            start_at=start_at,
                            end_at=end_at,
                            work_date=current,
                        )
                    )
            current += timedelta(days=1)
    return out


def estimate_minutes(planned_quantity: int, efficiency_rate: float, setup_time_min: int) -> float:
    qty_hours = (planned_quantity / max(efficiency_rate, 1.0)) * 60.0
    return max(qty_hours + max(setup_time_min, 0), 1.0)


def instruction_plan_quantity_for_cutting(plan: dict[str, Any]) -> int:
    """
    切断排产・cutting_plan_items.planned_quantity に載せる本数。
    instruction_plans.actual_production_quantity（生産数）を優先し、未設定または 0 のときは planned_quantity。
    """
    act = as_int(plan.get("actual_production_quantity"))
    if act > 0:
        return act
    return as_int(plan.get("planned_quantity"))


def item_from_instruction_plan(plan: dict[str, Any]) -> PlannedItem:
    po = plan.get("priority_order")
    qty = instruction_plan_quantity_for_cutting(plan)
    return PlannedItem(
        id=None,
        instruction_plan_id=as_int(plan["id"]),
        source_management_code=plan.get("management_code"),
        product_cd=str(plan.get("product_cd") or ""),
        product_name=str(plan.get("product_name") or ""),
        material_name=plan.get("material_name"),
        production_line=plan.get("production_line"),
        planned_quantity=qty,
        production_lot_size=as_int(plan["production_lot_size"]) if plan.get("production_lot_size") is not None else None,
        lot_number=plan.get("lot_number"),
        take_count=as_int(plan["take_count"]) if plan.get("take_count") is not None else None,
        cutting_length=as_float(plan["cutting_length"]) if plan.get("cutting_length") is not None else None,
        instruction_production_quantity=as_int(plan.get("actual_production_quantity")),
        publish_status="PLANNED",
        completion_status="PLANNED",
        forming_start_date=parse_sql_date(plan.get("start_date")),
        forming_end_date=parse_sql_date(plan.get("end_date")),
        priority_order=as_int(po, 999999) if po is not None else 999999,
        slices=[],
    )


async def refresh_instruction_hints_for_items(
    db: AsyncSession,
    items: list[PlannedItem],
    bom_by_product_int: dict[int, tuple[int | None, int | None]],
) -> None:
    """DB 上の明細に instruction_plans の start/end と BOM 由来の推奨切断日を付与"""
    ip_ids = sorted({as_int(i.instruction_plan_id) for i in items if i.instruction_plan_id is not None})
    if not ip_ids:
        return
    ph = ", ".join(f":hip_{i}" for i in range(len(ip_ids)))
    params = {f"hip_{i}": ip_ids[i] for i in range(len(ip_ids))}
    res = await db.execute(
        text(f"SELECT id, start_date, end_date FROM instruction_plans WHERE id IN ({ph})"),
        params,
    )
    by_ip: dict[int, Any] = {as_int(r["id"]): r for r in res.mappings().all()}
    for it in items:
        if it.instruction_plan_id is None:
            continue
        row = by_ip.get(as_int(it.instruction_plan_id))
        if not row:
            continue
        it.forming_start_date = parse_sql_date(row.get("start_date"))
        it.forming_end_date = parse_sql_date(row.get("end_date"))
        enrich_planned_item_cutting_hints(it, bom_by_product_int)


def enrich_planned_item_cutting_hints(
    item: PlannedItem,
    bom_by_product_int: dict[int, tuple[int | None, int | None]],
) -> None:
    ik = bom_int_key_for_product_cd(item.product_cd)
    if ik is not None and ik in bom_by_product_int:
        c_lt, f_lt = bom_by_product_int[ik]
    else:
        c_lt, f_lt = None, None
    item.recommended_cutting_start_date = compute_recommended_cutting_start_date(
        item.forming_start_date, c_lt, f_lt,
    )


def earliest_available_start(
    segments: list[TimeSegment],
    reservations: list[FixedReservation],
    duration_minutes: float,
    min_work_date: date | None = None,
) -> tuple[datetime, datetime, list[ScheduleSlice]] | None:
    if duration_minutes <= 0:
        return None
    reservations = sorted(reservations, key=lambda x: x.start_at)
    for seg in segments:
        if min_work_date is not None and seg.work_date < min_work_date:
            continue
        cursor = seg.start_at
        seg_reservations = [r for r in reservations if not (r.end_at <= seg.start_at or r.start_at >= seg.end_at)]
        for res in seg_reservations:
            if res.start_at > cursor:
                result = consume_from_segments(
                    segments, cursor, duration_minutes, reservations, min_work_date=min_work_date,
                )
                if result is not None:
                    return result
            cursor = max(cursor, res.end_at)
        if cursor < seg.end_at:
            result = consume_from_segments(
                segments, cursor, duration_minutes, reservations, min_work_date=min_work_date,
            )
            if result is not None:
                return result
    return None


def consume_from_segments(
    segments: list[TimeSegment],
    start_cursor: datetime,
    duration_minutes: float,
    reservations: list[FixedReservation],
    min_work_date: date | None = None,
) -> tuple[datetime, datetime, list[ScheduleSlice]] | None:
    remaining = duration_minutes
    started_at: datetime | None = None
    end_at: datetime | None = None
    pieces: list[tuple[datetime, datetime, date]] = []
    current_cursor = start_cursor
    for seg in segments:
        if min_work_date is not None and seg.work_date < min_work_date:
            continue
        if seg.end_at <= current_cursor:
            continue
        segment_cursor = max(seg.start_at, current_cursor)
        seg_reservations = sorted(
            [r for r in reservations if not (r.end_at <= seg.start_at or r.start_at >= seg.end_at)],
            key=lambda x: x.start_at,
        )
        windows: list[tuple[datetime, datetime]] = []
        for res in seg_reservations:
            if res.start_at > segment_cursor:
                windows.append((segment_cursor, min(res.start_at, seg.end_at)))
            segment_cursor = max(segment_cursor, res.end_at)
            if segment_cursor >= seg.end_at:
                break
        if segment_cursor < seg.end_at:
            windows.append((segment_cursor, seg.end_at))
        for win_start, win_end in windows:
            if win_end <= win_start:
                continue
            if started_at is None:
                started_at = win_start
            available = (win_end - win_start).total_seconds() / 60.0
            take = min(remaining, available)
            if take <= 0:
                continue
            piece_end = win_start + timedelta(minutes=take)
            pieces.append((win_start, piece_end, seg.work_date))
            remaining -= take
            end_at = piece_end
            current_cursor = piece_end
            if remaining <= 0:
                slices = distribute_qty_to_slices(pieces, duration_minutes)
                return started_at, end_at, slices
    return None


def distribute_qty_to_slices(
    pieces: list[tuple[datetime, datetime, date]],
    total_minutes: float,
) -> list[ScheduleSlice]:
    durations = [max((end - start).total_seconds() / 60.0, 1.0) for start, end, _ in pieces]
    weights = [d / max(total_minutes, 1.0) for d in durations]
    result: list[ScheduleSlice] = []
    for idx, ((start, end, work_date), weight) in enumerate(zip(pieces, weights), start=1):
        result.append(
            ScheduleSlice(
                work_date=work_date,
                period_start=start.time().replace(microsecond=0),
                period_end=end.time().replace(microsecond=0),
                planned_qty=max(int(round(weight * 1000)), 0),
                sort_order=idx,
            )
        )
    return result


def normalize_slice_quantities(slices: list[ScheduleSlice], planned_quantity: int) -> list[ScheduleSlice]:
    if not slices:
        return slices
    raw_total = sum(s.planned_qty for s in slices)
    if raw_total <= 0:
        even = planned_quantity // len(slices)
        remainder = planned_quantity % len(slices)
        for idx, sl in enumerate(slices):
            sl.planned_qty = even + (1 if idx < remainder else 0)
        return slices
    assigned = 0
    for idx, sl in enumerate(slices):
        if idx == len(slices) - 1:
            sl.planned_qty = planned_quantity - assigned
        else:
            sl.planned_qty = int(round(planned_quantity * (sl.planned_qty / raw_total)))
            assigned += sl.planned_qty
    diff = planned_quantity - sum(s.planned_qty for s in slices)
    if diff != 0:
        slices[-1].planned_qty += diff
    return slices


def schedule_items(
    source_items: list[PlannedItem],
    machines: list[MachineInfo],
    segments_by_machine: dict[int, list[TimeSegment]],
    fixed_items: list[PlannedItem],
    efficiency_map: dict[tuple[str, str], tuple[float, int]],
    eligible_machine_names_by_product: dict[str, set[str]] | None = None,
) -> list[PlannedItem]:
    reservations_by_machine: dict[int, list[FixedReservation]] = defaultdict(list)
    planned: list[PlannedItem] = []
    for fixed in fixed_items:
        if fixed.assigned_machine_id and fixed.planned_start and fixed.planned_end:
            reservations_by_machine[fixed.assigned_machine_id].append(
                FixedReservation(
                    item_id=fixed.published_cutting_id or 0,
                    machine_id=fixed.assigned_machine_id,
                    machine_name=fixed.assigned_machine or "",
                    start_at=fixed.planned_start,
                    end_at=fixed.planned_end,
                )
            )
            planned.append(fixed)

    machine_lookup = {m.id: m for m in machines}
    sequence_map: dict[int, int] = defaultdict(int)
    for fixed in fixed_items:
        if fixed.assigned_machine_id:
            sequence_map[fixed.assigned_machine_id] = max(sequence_map[fixed.assigned_machine_id], fixed.sequence_no)

    eligible_map = eligible_machine_names_by_product or {}
    min_date_anchor = date(1970, 1, 1)
    ordered_source = sorted(
        source_items,
        key=lambda it: (
            it.recommended_cutting_start_date or min_date_anchor,
            it.priority_order,
            it.instruction_plan_id or 0,
        ),
    )

    for item in ordered_source:
        best_choice: tuple[MachineInfo, datetime, datetime, list[ScheduleSlice], float, int] | None = None
        names = eligible_map.get(str(item.product_cd or "").strip())
        if names:
            machine_candidates = [m for m in machines if m.machine_name in names]
            if not machine_candidates:
                machine_candidates = list(machines)
        else:
            machine_candidates = list(machines)
        for machine in machine_candidates:
            rate, setup = efficiency_map.get((item.product_cd, machine.machine_name), (DEFAULT_EFFICIENCY_RATE, 0))
            estimate = estimate_minutes(item.planned_quantity, rate, setup)
            result = earliest_available_start(
                segments_by_machine.get(machine.id, []),
                reservations_by_machine[machine.id],
                estimate,
                min_work_date=item.recommended_cutting_start_date,
            )
            if result is None:
                continue
            start_at, end_at, slices = result
            if best_choice is None or end_at < best_choice[2]:
                best_choice = (machine, start_at, end_at, slices, rate, setup)

        if best_choice is None:
            # 没有可用时间段时，落到第一台机并标记未排入
            fallback = machines[0]
            item.assigned_machine_id = fallback.id
            item.assigned_machine = fallback.machine_name
            item.sequence_no = sequence_map[fallback.id] + 1
            sequence_map[fallback.id] = item.sequence_no
            item.efficiency_rate = DEFAULT_EFFICIENCY_RATE
            item.setup_time_min = 0
            item.estimated_minutes = estimate_minutes(item.planned_quantity, DEFAULT_EFFICIENCY_RATE, 0)
            item.completion_status = "UNSCHEDULED"
            item.slices = []
            planned.append(item)
            continue

        machine, start_at, end_at, slices, rate, setup = best_choice
        slices = normalize_slice_quantities(slices, item.planned_quantity)
        item.assigned_machine_id = machine.id
        item.assigned_machine = machine.machine_name
        item.sequence_no = sequence_map[machine.id] + 1
        sequence_map[machine.id] = item.sequence_no
        item.planned_day = start_at.date()
        item.planned_start = start_at
        item.planned_end = end_at
        item.estimated_minutes = estimate_minutes(item.planned_quantity, rate, setup)
        item.efficiency_rate = rate
        item.setup_time_min = setup
        item.completion_status = "PLANNED"
        item.slices = slices
        reservations_by_machine[machine.id].append(
            FixedReservation(
                item_id=0,
                machine_id=machine.id,
                machine_name=machine.machine_name,
                start_at=start_at,
                end_at=end_at,
            )
        )
        planned.append(item)

    planned.sort(
        key=lambda x: (
            x.assigned_machine or "",
            x.sequence_no,
            x.planned_start or datetime.max,
            x.product_cd,
        )
    )
    return planned


def fixed_items_excluding_reschedule_targets(
    all_items: list[PlannedItem],
    to_reschedule_ids: set[int],
) -> list[PlannedItem]:
    """既に時刻が入っている行のうち、今回の再排産対象以外を予約（ブロック）として渡す"""
    out: dict[int, PlannedItem] = {}
    for it in all_items:
        iid = as_int(it.id) if it.id is not None else 0
        if iid <= 0:
            continue
        if not (it.planned_start and it.planned_end):
            continue
        if iid in to_reschedule_ids:
            continue
        out[iid] = it
    return list(out.values())


async def sync_cutting_plan_items_from_instructions(db: AsyncSession, run_id: int, production_month: date) -> None:
    """
    instruction_plans から cutting_plan_items を同期（INSERT/UPDATE）。
    未下発・指示に無い明細のみ削除。planned_start/end は触らず、sequence_no は指示優先で並び用に更新。
    """
    rows = await fetch_instruction_plans(db, production_month)
    valid_ip_ids = [as_int(r["id"]) for r in rows]
    valid_set = set(valid_ip_ids)

    if valid_ip_ids:
        ph = ", ".join(f":vip_{i}" for i in range(len(valid_ip_ids)))
        vip_params = {f"vip_{i}": valid_ip_ids[i] for i in range(len(valid_ip_ids))}
        del_res = await db.execute(
            text(
                f"""
                SELECT id FROM cutting_plan_items
                WHERE run_id = :run_id
                  AND publish_status = 'PLANNED'
                  AND (published_cutting_id IS NULL OR published_cutting_id = 0)
                  AND instruction_plan_id IS NOT NULL
                  AND instruction_plan_id NOT IN ({ph})
                """
            ),
            {"run_id": run_id, **vip_params},
        )
        for r in del_res.mappings().all():
            oid = as_int(r["id"])
            await db.execute(text("DELETE FROM cutting_plan_slices WHERE item_id = :iid"), {"iid": oid})
            await db.execute(text("DELETE FROM cutting_plan_items WHERE id = :iid"), {"iid": oid})

    res = await db.execute(
        text(
            """
            SELECT id, instruction_plan_id FROM cutting_plan_items
            WHERE run_id = :run_id AND instruction_plan_id IS NOT NULL
            """
        ),
        {"run_id": run_id},
    )
    existing_by_ip: dict[int, int] = {}
    for r in res.mappings().all():
        ip = r["instruction_plan_id"]
        if ip is not None:
            existing_by_ip[as_int(ip)] = as_int(r["id"])

    sorted_rows = sorted(rows, key=lambda x: (as_int(x.get("priority_order"), 999999), as_int(x["id"])))
    for seq_no, plan in enumerate(sorted_rows, start=1):
        ip_id = as_int(plan["id"])
        item = item_from_instruction_plan(plan)
        if ip_id in existing_by_ip:
            iid = existing_by_ip[ip_id]
            await db.execute(
                text(
                    """
                    UPDATE cutting_plan_items SET
                        source_management_code = :source_management_code,
                        product_cd = :product_cd,
                        product_name = :product_name,
                        material_name = :material_name,
                        production_line = :production_line,
                        planned_quantity = :planned_quantity,
                        production_lot_size = :production_lot_size,
                        lot_number = :lot_number,
                        take_count = :take_count,
                        cutting_length = :cutting_length,
                        sequence_no = :sequence_no,
                        updated_at = NOW()
                    WHERE id = :id AND run_id = :run_id
                    """
                ),
                {
                    "id": iid,
                    "run_id": run_id,
                    "source_management_code": item.source_management_code,
                    "product_cd": item.product_cd,
                    "product_name": item.product_name,
                    "material_name": item.material_name,
                    "production_line": item.production_line,
                    "planned_quantity": item.planned_quantity,
                    "production_lot_size": item.production_lot_size,
                    "lot_number": item.lot_number,
                    "take_count": item.take_count,
                    "cutting_length": item.cutting_length,
                    "sequence_no": seq_no,
                },
            )
        else:
            await db.execute(
                text(
                    """
                    INSERT INTO cutting_plan_items (
                        run_id, instruction_plan_id, source_management_code, product_cd, product_name, material_name,
                        production_line, planned_quantity, production_lot_size, lot_number, take_count, cutting_length,
                        assigned_machine_id, assigned_machine, sequence_no, planned_day, planned_start, planned_end,
                        estimated_minutes, efficiency_rate, setup_time_min, is_locked, publish_status, published_cutting_id,
                        actual_quantity, completion_status
                    ) VALUES (
                        :run_id, :instruction_plan_id, :source_management_code, :product_cd, :product_name, :material_name,
                        :production_line, :planned_quantity, :production_lot_size, :lot_number, :take_count, :cutting_length,
                        NULL, NULL, :sequence_no, NULL, NULL, NULL,
                        0, NULL, NULL, 0, 'PLANNED', NULL, 0, 'PLANNED'
                    )
                    """
                ),
                {
                    "run_id": run_id,
                    "instruction_plan_id": item.instruction_plan_id,
                    "source_management_code": item.source_management_code,
                    "product_cd": item.product_cd,
                    "product_name": item.product_name,
                    "material_name": item.material_name,
                    "production_line": item.production_line,
                    "planned_quantity": item.planned_quantity,
                    "production_lot_size": item.production_lot_size,
                    "lot_number": item.lot_number,
                    "take_count": item.take_count,
                    "cutting_length": item.cutting_length,
                    "sequence_no": seq_no,
                },
            )

    await db.execute(
        text("UPDATE cutting_plan_runs SET updated_at = NOW() WHERE id = :run_id"),
        {"run_id": run_id},
    )


async def persist_partial_scheduled_items(db: AsyncSession, run_id: int, scheduled: list[PlannedItem]) -> None:
    """選択行のみ排産結果を UPDATE（スライス差し替え）。replace_run_items は使わない"""
    scheduled = [x for x in scheduled if x.id is not None and as_int(x.id) > 0]
    if not scheduled:
        return
    ids = [as_int(x.id) for x in scheduled]
    ph = ", ".join(f":psid_{i}" for i in range(len(ids)))
    del_params: dict[str, Any] = {"run_id": run_id, **{f"psid_{i}": ids[i] for i in range(len(ids))}}
    await db.execute(
        text(f"DELETE FROM cutting_plan_slices WHERE run_id = :run_id AND item_id IN ({ph})"),
        del_params,
    )
    for item in scheduled:
        iid = as_int(item.id)
        await db.execute(
            text(
                """
                UPDATE cutting_plan_items SET
                    material_name = :material_name,
                    assigned_machine_id = :assigned_machine_id,
                    assigned_machine = :assigned_machine,
                    sequence_no = :sequence_no,
                    planned_day = :planned_day,
                    planned_start = :planned_start,
                    planned_end = :planned_end,
                    estimated_minutes = :estimated_minutes,
                    efficiency_rate = :efficiency_rate,
                    setup_time_min = :setup_time_min,
                    completion_status = :completion_status,
                    updated_at = NOW()
                WHERE id = :id AND run_id = :run_id
                """
            ),
            {
                "id": iid,
                "run_id": run_id,
                "material_name": item.material_name,
                "assigned_machine_id": item.assigned_machine_id,
                "assigned_machine": item.assigned_machine,
                "sequence_no": item.sequence_no,
                "planned_day": item.planned_day,
                "planned_start": item.planned_start,
                "planned_end": item.planned_end,
                "estimated_minutes": item.estimated_minutes,
                "efficiency_rate": item.efficiency_rate,
                "setup_time_min": item.setup_time_min,
                "completion_status": item.completion_status,
            },
        )
        for slice_item in item.slices or []:
            await db.execute(
                text(
                    """
                    INSERT INTO cutting_plan_slices (
                        run_id, item_id, machine_id, assigned_machine, work_date, period_start, period_end, planned_qty, sort_order
                    ) VALUES (
                        :run_id, :item_id, :machine_id, :assigned_machine, :work_date, :period_start, :period_end, :planned_qty, :sort_order
                    )
                    """
                ),
                {
                    "run_id": run_id,
                    "item_id": iid,
                    "machine_id": item.assigned_machine_id,
                    "assigned_machine": item.assigned_machine,
                    "work_date": slice_item.work_date,
                    "period_start": slice_item.period_start,
                    "period_end": slice_item.period_end,
                    "planned_qty": slice_item.planned_qty,
                    "sort_order": slice_item.sort_order,
                },
            )
    await db.execute(
        text("UPDATE cutting_plan_runs SET generated_at = NOW(), updated_at = NOW() WHERE id = :run_id"),
        {"run_id": run_id},
    )


async def replace_run_items(db: AsyncSession, run_id: int, items: list[PlannedItem], production_month: date) -> None:
    await db.execute(text("DELETE FROM cutting_plan_slices WHERE run_id = :run_id"), {"run_id": run_id})
    await db.execute(text("DELETE FROM cutting_plan_items WHERE run_id = :run_id"), {"run_id": run_id})

    for item in items:
        await db.execute(
            text(
                """
                INSERT INTO cutting_plan_items (
                    run_id, instruction_plan_id, source_management_code, product_cd, product_name, material_name,
                    production_line, planned_quantity, production_lot_size, lot_number, take_count, cutting_length,
                    assigned_machine_id, assigned_machine, sequence_no, planned_day, planned_start, planned_end,
                    estimated_minutes, efficiency_rate, setup_time_min, is_locked, publish_status, published_cutting_id,
                    actual_quantity, completion_status
                ) VALUES (
                    :run_id, :instruction_plan_id, :source_management_code, :product_cd, :product_name, :material_name,
                    :production_line, :planned_quantity, :production_lot_size, :lot_number, :take_count, :cutting_length,
                    :assigned_machine_id, :assigned_machine, :sequence_no, :planned_day, :planned_start, :planned_end,
                    :estimated_minutes, :efficiency_rate, :setup_time_min, :is_locked, :publish_status, :published_cutting_id,
                    :actual_quantity, :completion_status
                )
                """
            ),
            {
                "run_id": run_id,
                "instruction_plan_id": item.instruction_plan_id,
                "source_management_code": item.source_management_code,
                "product_cd": item.product_cd,
                "product_name": item.product_name,
                "material_name": item.material_name,
                "production_line": item.production_line,
                "planned_quantity": item.planned_quantity,
                "production_lot_size": item.production_lot_size,
                "lot_number": item.lot_number,
                "take_count": item.take_count,
                "cutting_length": item.cutting_length,
                "assigned_machine_id": item.assigned_machine_id,
                "assigned_machine": item.assigned_machine,
                "sequence_no": item.sequence_no,
                "planned_day": item.planned_day,
                "planned_start": item.planned_start,
                "planned_end": item.planned_end,
                "estimated_minutes": item.estimated_minutes,
                "efficiency_rate": item.efficiency_rate,
                "setup_time_min": item.setup_time_min,
                "is_locked": 1 if item.is_locked else 0,
                "publish_status": item.publish_status,
                "published_cutting_id": item.published_cutting_id,
                "actual_quantity": item.actual_quantity,
                "completion_status": item.completion_status,
            },
        )
        new_id_result = await db.execute(text("SELECT LAST_INSERT_ID()"))
        item_id = as_int(new_id_result.scalar_one())
        for slice_item in item.slices or []:
            await db.execute(
                text(
                    """
                    INSERT INTO cutting_plan_slices (
                        run_id, item_id, machine_id, assigned_machine, work_date, period_start, period_end, planned_qty, sort_order
                    ) VALUES (
                        :run_id, :item_id, :machine_id, :assigned_machine, :work_date, :period_start, :period_end, :planned_qty, :sort_order
                    )
                    """
                ),
                {
                    "run_id": run_id,
                    "item_id": item_id,
                    "machine_id": item.assigned_machine_id,
                    "assigned_machine": item.assigned_machine,
                    "work_date": slice_item.work_date,
                    "period_start": slice_item.period_start,
                    "period_end": slice_item.period_end,
                    "planned_qty": slice_item.planned_qty,
                    "sort_order": slice_item.sort_order,
                },
            )
    await db.execute(
        text(
            """
            UPDATE cutting_plan_runs
            SET status = 'DRAFT', generated_at = NOW(), updated_at = NOW()
            WHERE id = :run_id AND production_month = :production_month
            """
        ),
        {"run_id": run_id, "production_month": production_month},
    )

