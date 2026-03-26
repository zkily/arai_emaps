"""
APS（先進的計画・スケジューリング）APIエンドポイント
産線管理、稼働カレンダー、工単 CRUD、排産エンジン、スケジューリンググリッド
"""
import math
from collections import defaultdict
from datetime import date, timedelta, datetime, time
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_, delete, text
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

from app.modules.master.models import Machine, EquipmentEfficiency, Process, Product
from app.modules.aps.models import (
    LineCapacity,
    LineCapacityTimeSlot,
    ProductionSchedule,
    ApsBatchPlan,
    ScheduleDetail,
    ScheduleSliceAllocation,
    LineProductStandard,
)
from app.modules.aps.schemas import (
    ProductionLineOut,
    EquipmentEfficiencyProductOut,
    LineCapacityOut,
    LineCapacityBatchBody,
    DaySlotsBody,
    DaySlotsBatchBody,
    DaySlotsOut,
    TimeSlotOut,
    LineProductStandardBody,
    LineProductStandardOut,
    ScheduleCreateBody,
    ScheduleUpdateBody,
    ScheduleOut,
    ScheduleGridRow,
    LineGridBlock,
    SchedulingGridResponse,
    SchedulingHourlyGridResponse,
    HourlyGridColumnOut,
    HourlyGridRowOut,
    ApsBatchPlanOut,
)
from app.modules.aps.engine import run_engine, replan_line_sequential

router = APIRouter()


def _dec(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


# 設備能率マスタ由来の日産初期値と整合（Planning.vue EE_DAILY_HOURS_STANDARD）
_APS_EE_STANDARD_DAY_HOURS = Decimal("15.3")


async def _load_equipment_efficiency_rows_for_machine(
    db: AsyncSession,
    machine: Machine,
) -> List[EquipmentEfficiency]:
    """選択設備に紐づく equipment_efficiency 行（/equipment-efficiency-products と同趣旨のマッチ）"""
    m_cd = (machine.machine_cd or "").strip()
    m_name = (machine.machine_name or "").strip()
    match_conds = []
    if m_cd:
        match_conds.append(EquipmentEfficiency.machine_cd == m_cd)
        match_conds.append(EquipmentEfficiency.machines_name == m_cd)
    if m_name:
        match_conds.append(EquipmentEfficiency.machines_name == m_name)
    if not match_conds:
        return []
    q = (
        select(EquipmentEfficiency)
        .where(or_(*match_conds))
        .where(or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status == 1))
        .order_by(EquipmentEfficiency.product_name, EquipmentEfficiency.product_cd, EquipmentEfficiency.id)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


def _resolve_efficiency_rate_pieces_per_hour(
    ps: ProductionSchedule,
    ee_rows: List[EquipmentEfficiency],
) -> Optional[float]:
    """
    表示用：equipment_efficiency.efficiency_rate（本/H）。
    製品コード→品名の順でマスタ照合。無ければ日産能力÷標準15.3hで概算。
    """
    pcd = (ps.product_cd or "").strip()
    iname = (ps.item_name or "").strip()
    name_hits: List[float] = []
    for r in ee_rows:
        rcd = (r.product_cd or "").strip()
        rname = (r.product_name or "").strip()
        rate = _dec(r.efficiency_rate)
        if pcd and rcd and pcd == rcd:
            return rate
        if iname and rname and iname == rname:
            name_hits.append(rate)
    if name_hits:
        return name_hits[0]
    dc = int(ps.daily_capacity or 0)
    if dc > 0:
        return round(float(Decimal(dc) / _APS_EE_STANDARD_DAY_HOURS), 2)
    return None


def _aps_machine_selectable_clause():
    """APS 下拉用：is_active が False でない、かつ status が active 系"""
    return and_(
        or_(Machine.is_active == True, Machine.is_active.is_(None)),
        or_(
            Machine.status == "active",
            Machine.status.is_(None),
            Machine.status == "",
        ),
    )


# ═══════════════════ Production Lines（データ源: machines）═══════════════════

@router.get("/lines", response_model=List[ProductionLineOut])
async def get_lines(
    processCd: Optional[str] = Query(
        None,
        description="工程CD（指定時は machines.machine_type が当該工程の名称またはCDと一致する設備のみ）",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(Machine).where(_aps_machine_selectable_clause())
    if processCd and processCd.strip():
        pc = processCd.strip()
        proc_result = await db.execute(select(Process).where(Process.process_cd == pc))
        proc = proc_result.scalar_one_or_none()
        if proc is None:
            return []
        pn = (proc.process_name or "").strip()
        pcc = (proc.process_cd or "").strip()
        type_conds = []
        if pn:
            type_conds.append(Machine.machine_type == pn)
        if pcc:
            type_conds.append(Machine.machine_type == pcc)
        if not type_conds:
            return []
        q = q.where(or_(*type_conds))
    result = await db.execute(
        q.order_by(Machine.machine_cd)
    )
    return [
        ProductionLineOut(
            id=r.id,
            line_code=r.machine_cd,
            line_name=(r.machine_name or "").strip(),
            default_work_hours=_dec(r.default_work_hours),
            is_active=bool(r.is_active) if r.is_active is not None else True,
        )
        for r in result.scalars().all()
    ]


@router.post("/lines")
async def create_line(
    line_code: str,
    default_work_hours: float = 0.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    cd = line_code.strip()
    dup = await db.execute(select(Machine).where(Machine.machine_cd == cd))
    if dup.scalar_one_or_none():
        raise HTTPException(400, "同じ設備コードが既に存在します")
    row = Machine(
        machine_cd=cd,
        machine_name=cd,
        default_work_hours=Decimal(str(default_work_hours)) if default_work_hours else None,
        is_active=True,
        status="active",
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return {"success": True, "data": {"id": row.id, "line_code": row.machine_cd}}


@router.get("/equipment-efficiency-products", response_model=List[EquipmentEfficiencyProductOut])
async def get_equipment_efficiency_products_by_machine(
    machineId: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    選択設備（machines.id）に紐づく equipment_efficiency の製品一覧。
    machine_cd 一致、または machines_name が設備名／設備コードと一致する行を対象。
    """
    machine = await db.get(Machine, machineId)
    if machine is None:
        raise HTTPException(404, "設備が見つかりません")

    m_cd = (machine.machine_cd or "").strip()
    m_name = (machine.machine_name or "").strip()
    match_conds = []
    if m_cd:
        match_conds.append(EquipmentEfficiency.machine_cd == m_cd)
        match_conds.append(EquipmentEfficiency.machines_name == m_cd)
    if m_name:
        match_conds.append(EquipmentEfficiency.machines_name == m_name)
    if not match_conds:
        return []

    q = (
        select(EquipmentEfficiency)
        .where(or_(*match_conds))
        .where(or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status == 1))
        .order_by(EquipmentEfficiency.product_name, EquipmentEfficiency.product_cd, EquipmentEfficiency.id)
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    seen: set[tuple[str, str]] = set()
    candidates: list[EquipmentEfficiency] = []
    for r in rows:
        key = (r.product_cd or "", r.product_name or "")
        if key in seen:
            continue
        seen.add(key)
        candidates.append(r)

    cds_order: list[str] = []
    for r in candidates:
        cd = (r.product_cd or "").strip()
        if cd and cd not in cds_order:
            cds_order.append(cd)

    lot_by_cd: dict[str, int] = {}
    if cds_order:
        pr_res = await db.execute(
            select(Product.product_cd, Product.lot_size).where(Product.product_cd.in_(cds_order))
        )
        for prow in pr_res.mappings().all():
            pcd = (prow.get("product_cd") or "").strip()
            if not pcd:
                continue
            ls = prow.get("lot_size")
            if ls is not None:
                lot_by_cd[pcd] = int(ls)

    out: list[EquipmentEfficiencyProductOut] = []
    for r in candidates:
        cd = (r.product_cd or "").strip()
        out.append(
            EquipmentEfficiencyProductOut(
                id=r.id,
                product_cd=r.product_cd,
                product_name=r.product_name,
                efficiency_rate=_dec(r.efficiency_rate),
                step_time=int(r.step_time) if r.step_time is not None else None,
                lot_size=lot_by_cd.get(cd) if cd else None,
            )
        )
    return out


# ═══════════════════ Line Capacities ═══════════════════

@router.get("/line-capacities", response_model=List[LineCapacityOut])
async def get_line_capacities(
    lineId: int = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    result = await db.execute(
        select(LineCapacity)
        .where(
            LineCapacity.line_id == lineId,
            LineCapacity.work_date >= sd,
            LineCapacity.work_date <= ed,
        )
        .order_by(LineCapacity.work_date)
    )
    return [
        LineCapacityOut(
            id=r.id,
            line_id=r.line_id,
            work_date=r.work_date,
            available_hours=_dec(r.available_hours),
            note=r.note,
        )
        for r in result.scalars().all()
    ]


@router.post("/line-capacities/batch")
async def batch_upsert_line_capacities(
    body: LineCapacityBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    count = 0
    for item in body.items:
        existing = await db.execute(
            select(LineCapacity).where(
                LineCapacity.line_id == item.line_id,
                LineCapacity.work_date == item.work_date,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.available_hours = Decimal(str(item.available_hours))
            row.note = item.note
        else:
            db.add(LineCapacity(
                line_id=item.line_id,
                work_date=item.work_date,
                available_hours=Decimal(str(item.available_hours)),
                note=item.note,
            ))
        count += 1
    await db.flush()
    return {"success": True, "data": {"count": count}}


# ═══════════════════ Line Capacity Time Slots ═══════════════════

def _calc_slot_hours(start_time, end_time) -> float:
    s = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    e = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
    return max(0.0, (e - s) / 3600.0)


@router.get("/line-capacity-slots", response_model=List[DaySlotsOut])
async def get_line_capacity_slots(
    lineId: int = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    slots_result = await db.execute(
        select(LineCapacityTimeSlot)
        .where(
            LineCapacityTimeSlot.line_id == lineId,
            LineCapacityTimeSlot.work_date >= sd,
            LineCapacityTimeSlot.work_date <= ed,
        )
        .order_by(LineCapacityTimeSlot.work_date, LineCapacityTimeSlot.sort_order)
    )
    slots = slots_result.scalars().all()

    cap_result = await db.execute(
        select(LineCapacity).where(
            LineCapacity.line_id == lineId,
            LineCapacity.work_date >= sd,
            LineCapacity.work_date <= ed,
        )
    )
    cap_map = {r.work_date: _dec(r.available_hours) for r in cap_result.scalars().all()}

    grouped: dict[date, list] = defaultdict(list)
    for s in slots:
        grouped[s.work_date].append(TimeSlotOut(
            id=s.id,
            start_time=s.start_time,
            end_time=s.end_time,
            sort_order=s.sort_order,
        ))

    result = []
    d = sd
    while d <= ed:
        slot_list = grouped.get(d, [])
        total = cap_map.get(d, sum(_calc_slot_hours(s.start_time, s.end_time) for s in slot_list))
        result.append(DaySlotsOut(work_date=d, available_hours=total, slots=slot_list))
        d += timedelta(days=1)

    return result


@router.put("/line-capacity-slots/batch")
async def batch_upsert_line_capacity_slots(
    body: DaySlotsBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    line = await db.get(Machine, body.line_id)
    if line is None:
        raise HTTPException(404, "設備が見つかりません")

    updated_days = 0
    for day_body in body.days:
        for slot in day_body.slots:
            if slot.end_time <= slot.start_time:
                raise HTTPException(400, f"{day_body.work_date}: end_time must be > start_time")

        await db.execute(
            delete(LineCapacityTimeSlot).where(
                LineCapacityTimeSlot.line_id == body.line_id,
                LineCapacityTimeSlot.work_date == day_body.work_date,
            )
        )

        total_hours = 0.0
        for idx, slot in enumerate(day_body.slots):
            db.add(LineCapacityTimeSlot(
                line_id=body.line_id,
                work_date=day_body.work_date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                sort_order=slot.sort_order if slot.sort_order else idx,
            ))
            total_hours += _calc_slot_hours(slot.start_time, slot.end_time)

        existing_cap = await db.execute(
            select(LineCapacity).where(
                LineCapacity.line_id == body.line_id,
                LineCapacity.work_date == day_body.work_date,
            )
        )
        cap_row = existing_cap.scalar_one_or_none()
        if cap_row:
            cap_row.available_hours = Decimal(str(round(total_hours, 2)))
            cap_row.note = "時間帯から算出"
        else:
            db.add(LineCapacity(
                line_id=body.line_id,
                work_date=day_body.work_date,
                available_hours=Decimal(str(round(total_hours, 2))),
                note="時間帯から算出",
            ))
        updated_days += 1

    await db.flush()
    return {"success": True, "data": {"updated_days": updated_days}}


# ═══════════════════ Line Product Standard ═══════════════════

@router.get("/line-product-standards", response_model=List[LineProductStandardOut])
async def get_line_product_standards(
    lineId: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(LineProductStandard)
    if lineId is not None:
        q = q.where(LineProductStandard.line_id == lineId)
    q = q.order_by(LineProductStandard.line_id, LineProductStandard.product_cd)
    result = await db.execute(q)
    return [
        LineProductStandardOut(
            id=r.id,
            line_id=r.line_id,
            product_cd=r.product_cd,
            std_qty_per_hour=_dec(r.std_qty_per_hour),
            setup_time_min=int(r.setup_time_min or 0),
            efficiency_pct=_dec(r.efficiency_pct),
        )
        for r in result.scalars().all()
    ]


@router.post("/line-product-standards", response_model=LineProductStandardOut)
async def create_line_product_standard(
    body: LineProductStandardBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = LineProductStandard(
        line_id=body.line_id,
        product_cd=body.product_cd,
        std_qty_per_hour=Decimal(str(body.std_qty_per_hour)),
        setup_time_min=body.setup_time_min,
        efficiency_pct=Decimal(str(body.efficiency_pct)),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return LineProductStandardOut(
        id=row.id,
        line_id=row.line_id,
        product_cd=row.product_cd,
        std_qty_per_hour=_dec(row.std_qty_per_hour),
        setup_time_min=int(row.setup_time_min or 0),
        efficiency_pct=_dec(row.efficiency_pct),
    )


@router.put("/line-product-standards/{standard_id}", response_model=LineProductStandardOut)
async def update_line_product_standard(
    standard_id: int,
    body: LineProductStandardBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(LineProductStandard, standard_id)
    if row is None:
        raise HTTPException(404, "標準情報が見つかりません")
    row.line_id = body.line_id
    row.product_cd = body.product_cd
    row.std_qty_per_hour = Decimal(str(body.std_qty_per_hour))
    row.setup_time_min = body.setup_time_min
    row.efficiency_pct = Decimal(str(body.efficiency_pct))
    await db.flush()
    return LineProductStandardOut(
        id=row.id,
        line_id=row.line_id,
        product_cd=row.product_cd,
        std_qty_per_hour=_dec(row.std_qty_per_hour),
        setup_time_min=int(row.setup_time_min or 0),
        efficiency_pct=_dec(row.efficiency_pct),
    )


@router.delete("/line-product-standards/{standard_id}")
async def delete_line_product_standard(
    standard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(LineProductStandard, standard_id)
    if row is None:
        raise HTTPException(404, "標準情報が見つかりません")
    await db.delete(row)
    await db.flush()
    return {"success": True}


# ═══════════════════ Production Schedules (CRUD) ═══════════════════

@router.get("/schedules", response_model=List[ScheduleOut])
async def list_schedules(
    lineId: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(ProductionSchedule)
    conditions = []
    if lineId is not None:
        conditions.append(ProductionSchedule.line_id == lineId)
    if status:
        conditions.append(ProductionSchedule.status == status)
    if conditions:
        q = q.where(and_(*conditions))
    q = q.order_by(ProductionSchedule.line_id, ProductionSchedule.order_no, ProductionSchedule.id)
    try:
        result = await db.execute(q)
    except (OperationalError, ProgrammingError) as e:
        msg = (
            "計画一覧の取得に失敗しました。DB に production_schedules.product_cd 等が無い可能性があります。"
            " migrations/098_production_schedules_product_cd_if_missing.sql を適用してください。"
        )
        if getattr(e, "orig", None):
            msg = f"{msg} ({e.orig!s})"
        raise HTTPException(status_code=500, detail=msg) from e
    return [_schedule_to_out(r) for r in result.scalars().all()]


@router.post("/schedules", response_model=ScheduleOut)
async def create_schedule(
    body: ScheduleCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    machine = await db.get(Machine, body.line_id)
    if machine is None:
        raise HTTPException(status_code=400, detail="指定された設備IDが存在しません（machines テーブルを確認してください）")

    setup_time = int(body.setup_time or 0)
    efficiency = float(body.efficiency) if body.efficiency is not None else 100.0
    daily_capacity = int(body.daily_capacity or 0)
    prev_carry = int(body.prev_month_carryover or 0)
    lot_q = int(body.lot_qty or 0)

    product_cd = (body.product_cd or "").strip() or None
    item_name = (body.item_name or "").strip()
    if not item_name:
        raise HTTPException(status_code=400, detail="品名（item_name）が空です")

    batch_count = int(body.planned_batch_count or 0)
    lot_snap = int(body.lot_size_snapshot or 0)

    if batch_count > 0:
        if lot_snap <= 0:
            if product_cd:
                pr = await db.execute(
                    select(Product.lot_size).where(Product.product_cd == product_cd)
                )
                row = pr.scalar_one_or_none()
                lot_snap = int(row) if row else 0
            if lot_snap <= 0:
                raise HTTPException(
                    400,
                    "ロットサイズが未設定です。製品マスタの lot_size を先に登録してください。",
                )
        planned_qty = batch_count * lot_snap
    else:
        planned_qty = int(body.planned_process_qty or 0)

    # line_product_standard 未適用（094）だと SELECT 時点で ProgrammingError になり得る → flush 前で未捕捉だと素の 500 になる
    std: LineProductStandard | None = None
    if product_cd:
        try:
            std_result = await db.execute(
                select(LineProductStandard).where(
                    LineProductStandard.line_id == body.line_id,
                    LineProductStandard.product_cd == product_cd,
                )
            )
            std = std_result.scalar_one_or_none()
        except ProgrammingError:
            await db.rollback()
            std = None

    if std:
        line = machine
        default_hours = float(line.default_work_hours or 0) if line else 8.0
        if default_hours <= 0:
            default_hours = 8.0
        if body.setup_time == 0 and std.setup_time_min:
            setup_time = int(std.setup_time_min)
        if body.efficiency == 100.0 and std.efficiency_pct:
            efficiency = float(std.efficiency_pct)
        if body.daily_capacity == 0 or daily_capacity == int(body.daily_capacity):
            derived = int(float(std.std_qty_per_hour) * default_hours)
            if derived > 0:
                daily_capacity = derived

    ps = ProductionSchedule(
        line_id=body.line_id,
        order_no=body.order_no,
        order_id=body.order_id,
        item_name=item_name[:100],
        product_cd=product_cd,
        material_shortage=bool(body.material_shortage),
        lot_qty=lot_q,
        planned_batch_count=batch_count,
        lot_size_snapshot=lot_snap,
        planned_process_qty=planned_qty,
        prev_month_carryover=prev_carry,
        due_date=body.due_date,
        material_date=body.material_date,
        setup_time=setup_time,
        efficiency=Decimal(str(efficiency)),
        daily_capacity=daily_capacity,
        start_date=body.start_date,
        status="PLANNING",
    )
    db.add(ps)
    try:
        await db.flush()
        await db.refresh(ps)
    except IntegrityError as e:
        await db.rollback()
        _suffix = f" ({e.orig!s})" if getattr(e, "orig", None) else f" ({e!s})"
        raise HTTPException(
            status_code=400,
            detail=(
                "計画の保存に失敗しました。line_id が machines.id と一致するか、"
                "マイグレーション 096（APS 外部キー→machines）を適用済みか確認してください。"
                + _suffix
            ),
        ) from e
    except (OperationalError, ProgrammingError) as e:
        await db.rollback()
        msg = (
            "計画の保存に失敗しました。production_schedules に product_cd 列が無い場合は "
            "migrations/098_production_schedules_product_cd_if_missing.sql を適用してください。"
        )
        if getattr(e, "orig", None):
            msg = f"{msg} ({e.orig!s})"
        raise HTTPException(status_code=500, detail=msg) from e
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                "計画の保存中にデータベースエラーが発生しました。"
                "096（FK→machines）・095/098（product_cd 列）の適用状況を確認してください。"
                f" ({getattr(e, 'orig', None) or e!s})"
            ),
        ) from e

    if body.run_immediately:
        try:
            ps = await run_engine(db, ps.id, override_start_date=body.start_date)
            await db.flush()
        except ValueError as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) from e

    return _schedule_to_out(ps)


@router.put("/schedules/{schedule_id}", response_model=ScheduleOut)
async def update_schedule(
    schedule_id: int,
    body: ScheduleUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise HTTPException(404, "工単が見つかりません")

    for field in (
        "line_id", "order_no", "order_id", "item_name", "product_cd",
        "material_shortage", "lot_qty", "planned_process_qty", "prev_month_carryover",
        "due_date", "material_date", "setup_time", "daily_capacity", "start_date",
    ):
        val = getattr(body, field, None)
        if val is not None:
            setattr(ps, field, val)
    if body.efficiency is not None:
        ps.efficiency = Decimal(str(body.efficiency))

    if body.planned_batch_count is not None:
        ps.planned_batch_count = body.planned_batch_count
        if body.lot_size_snapshot is not None and body.lot_size_snapshot > 0:
            ps.lot_size_snapshot = body.lot_size_snapshot
        snap = int(ps.lot_size_snapshot or 0)
        if snap <= 0:
            pcd = (ps.product_cd or "").strip()
            if pcd:
                pr = await db.execute(
                    select(Product.lot_size).where(Product.product_cd == pcd)
                )
                row = pr.scalar_one_or_none()
                snap = int(row) if row else 0
                ps.lot_size_snapshot = snap
        if snap > 0 and body.planned_batch_count > 0:
            new_total = body.planned_batch_count * snap
            already_produced = await _sum_actual_qty(db, ps.id)
            if new_total < already_produced:
                min_batches = math.ceil(already_produced / snap) if snap > 0 else 0
                raise HTTPException(
                    400,
                    f"既に {already_produced} 本の実績があるため、"
                    f"批次数は {min_batches} 以上にしてください。",
                )
            ps.planned_process_qty = new_total

    await db.flush()

    if body.run_immediately:
        ps = await run_engine(db, ps.id, override_start_date=body.start_date or ps.start_date)
        await db.flush()

    return _schedule_to_out(ps)


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise HTTPException(404, "工単が見つかりません")

    # APS を削除する場合、紐づく aps_batch_plans → instruction_plans も削除する
    try:
        batch_q = await db.execute(
            select(ApsBatchPlan.id).where(ApsBatchPlan.aps_schedule_id == schedule_id)
        )
        batch_ids = [int(x[0]) for x in batch_q.all()]
        if batch_ids:
            for bid in batch_ids:
                await db.execute(
                    text("DELETE FROM instruction_plans WHERE aps_batch_plan_id = :bid"),
                    {"bid": bid},
                )
            await db.execute(
                delete(ApsBatchPlan).where(ApsBatchPlan.aps_schedule_id == schedule_id)
            )
    except OperationalError:
        # instruction_plans が存在しない/権限不足の環境では APS の削除だけ行う
        pass

    await db.delete(ps)
    await db.flush()
    return {"success": True, "message": "削除しました"}


@router.post("/schedules/{schedule_id}/run")
async def run_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise HTTPException(404, "工単が見つかりません")
    ps = await run_engine(db, schedule_id, override_start_date=ps.start_date)
    await db.flush()
    return {"success": True, "data": _schedule_to_out(ps).model_dump()}


# ═══════════════════ Scheduling Grid ═══════════════════

@router.get("/scheduling/grid", response_model=SchedulingGridResponse)
async def get_scheduling_grid(
    startDate: str = Query(...),
    endDate: str = Query(...),
    lineId: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    dates_list: list[str] = []
    d = sd
    while d <= ed:
        dates_list.append(d.isoformat())
        d += timedelta(days=1)

    # 設備取得（machines）
    line_q = select(Machine).where(_aps_machine_selectable_clause())
    if lineId is not None:
        line_q = line_q.where(Machine.id == lineId)
    line_q = line_q.order_by(Machine.machine_cd)
    lines_result = await db.execute(line_q)
    lines = lines_result.scalars().all()

    blocks: list[LineGridBlock] = []

    for line in lines:
        # カレンダー
        cal_result = await db.execute(
            select(LineCapacity).where(
                LineCapacity.line_id == line.id,
                LineCapacity.work_date >= sd,
                LineCapacity.work_date <= ed,
            )
        )
        calendar_map = {
            row.work_date.isoformat(): _dec(row.available_hours)
            for row in cal_result.scalars().all()
        }

        # 工単取得
        sched_result = await db.execute(
            select(ProductionSchedule)
            .where(ProductionSchedule.line_id == line.id)
            .order_by(ProductionSchedule.order_no, ProductionSchedule.id)
        )
        schedules = sched_result.scalars().all()
        ee_rows = await _load_equipment_efficiency_rows_for_machine(db, line)

        rows: list[ScheduleGridRow] = []
        daily_totals: dict[str, int] = defaultdict(int)
        sum_planned_process = 0
        sum_planned_output = 0

        for ps in schedules:
            detail_result = await db.execute(
                select(ScheduleDetail).where(
                    ScheduleDetail.schedule_id == ps.id,
                    ScheduleDetail.schedule_date >= sd,
                    ScheduleDetail.schedule_date <= ed,
                )
            )
            daily: dict[str, int] = {}
            for det in detail_result.scalars().all():
                key = det.schedule_date.isoformat()
                daily[key] = int(det.planned_qty)
                daily_totals[key] += int(det.planned_qty)

            rows.append(ScheduleGridRow(
                id=ps.id,
                order_no=ps.order_no,
                item_name=ps.item_name,
                material_shortage=bool(ps.material_shortage),
                lot_qty=int(ps.lot_qty or 0),
                planned_batch_count=int(getattr(ps, "planned_batch_count", 0) or 0),
                lot_size_snapshot=int(getattr(ps, "lot_size_snapshot", 0) or 0),
                planned_process_qty=int(ps.planned_process_qty),
                prev_month_carryover=int(ps.prev_month_carryover or 0),
                due_date=ps.due_date.isoformat() if ps.due_date else None,
                material_date=ps.material_date.isoformat() if ps.material_date else None,
                setup_time=int(ps.setup_time or 0),
                efficiency=_dec(ps.efficiency),
                efficiency_rate=_resolve_efficiency_rate_pieces_per_hour(ps, ee_rows),
                daily_capacity=int(ps.daily_capacity),
                planned_output_qty=int(ps.planned_output_qty or 0),
                start_date=ps.start_date.isoformat() if ps.start_date else None,
                end_date=ps.end_date.isoformat() if ps.end_date else None,
                completion_rate=_dec(ps.completion_rate) if ps.completion_rate is not None else None,
                status=ps.status or "PLANNING",
                daily=daily,
            ))
            sum_planned_process += int(ps.planned_process_qty or 0)
            sum_planned_output += int(ps.planned_output_qty or 0)

        block_rate = None
        if sum_planned_process > 0:
            block_rate = round(sum_planned_output / sum_planned_process * 100, 2)

        blocks.append(LineGridBlock(
            line_id=line.id,
            line_code=line.machine_cd,
            default_work_hours=_dec(line.default_work_hours),
            calendar=calendar_map,
            rows=rows,
            daily_totals=dict(daily_totals),
            sum_planned_process_qty=sum_planned_process,
            sum_planned_output_qty=sum_planned_output,
            completion_rate=block_rate,
        ))

    return SchedulingGridResponse(dates=dates_list, blocks=blocks)


def _hourly_slice_key(work_d: date, st, et) -> str:
    return (
        f"{work_d.isoformat()}|{st.strftime('%H:%M:%S')}|{et.strftime('%H:%M:%S')}"
        if hasattr(st, "strftime")
        else f"{work_d.isoformat()}|{st}|{et}"
    )


@router.get("/scheduling/hourly-grid", response_model=SchedulingHourlyGridResponse)
async def get_scheduling_hourly_grid(
    startDate: str = Query(...),
    endDate: str = Query(...),
    lineId: int = Query(..., description="設備ID（machines.id）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    machine = await db.get(Machine, lineId)
    if machine is None:
        raise HTTPException(404, "設備が見つかりません")

    sched_result = await db.execute(
        select(ProductionSchedule)
        .where(ProductionSchedule.line_id == lineId)
        .order_by(ProductionSchedule.order_no, ProductionSchedule.id)
    )
    schedules = sched_result.scalars().all()
    schedule_ids = [ps.id for ps in schedules]
    ee_rows = await _load_equipment_efficiency_rows_for_machine(db, machine)

    col_keys: set[str] = set()
    per_sched: dict[int, dict[str, int]] = defaultdict(dict)
    if schedule_ids:
        slice_result = await db.execute(
            select(ScheduleSliceAllocation)
            .where(
                ScheduleSliceAllocation.schedule_id.in_(schedule_ids),
                ScheduleSliceAllocation.work_date >= sd,
                ScheduleSliceAllocation.work_date <= ed,
            )
            .order_by(
                ScheduleSliceAllocation.work_date,
                ScheduleSliceAllocation.period_start,
                ScheduleSliceAllocation.sort_order,
                ScheduleSliceAllocation.id,
            )
        )
        for sl in slice_result.scalars().all():
            key = _hourly_slice_key(sl.work_date, sl.period_start, sl.period_end)
            col_keys.add(key)
            bucket = per_sched[sl.schedule_id]
            bucket[key] = bucket.get(key, 0) + int(sl.planned_qty or 0)

    sorted_keys = sorted(col_keys, key=lambda k: tuple(k.split("|")))

    columns: list[HourlyGridColumnOut] = []
    for k in sorted_keys:
        parts = k.split("|", 2)
        wd = parts[0] if len(parts) > 0 else ""
        ps = parts[1] if len(parts) > 1 else ""
        pe = parts[2] if len(parts) > 2 else ""
        columns.append(HourlyGridColumnOut(key=k, work_date=wd, period_start=ps, period_end=pe))

    rows: list[HourlyGridRowOut] = [
        HourlyGridRowOut(
            schedule_id=ps.id,
            order_no=ps.order_no,
            planned_batch_count=int(getattr(ps, "planned_batch_count", 0) or 0),
            lot_size_snapshot=int(getattr(ps, "lot_size_snapshot", 0) or 0),
            planned_process_qty=int(ps.planned_process_qty or 0),
            efficiency_rate=_resolve_efficiency_rate_pieces_per_hour(ps, ee_rows),
            item_name=ps.item_name or "",
            slice_qty=dict(per_sched.get(ps.id, {})),
        )
        for ps in schedules
    ]

    return SchedulingHourlyGridResponse(columns=columns, rows=rows)


# ═══════════════════ APS Batch Plans（lot_number表）═══════════════════
@router.get("/batch-plans", response_model=List[ApsBatchPlanOut])
async def get_aps_batch_plans(
    productionMonth: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    lineId: Optional[int] = Query(None, description="設備ID（machines.id）"),
    productCd: Optional[str] = Query(None, description="製品CD（完全一致）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    conditions = []
    q = select(ApsBatchPlan)

    if productionMonth and productionMonth.strip():
        try:
            y_m = productionMonth.strip().split("-")
            if len(y_m) == 2:
                y = int(y_m[0])
                m = int(y_m[1])
                d0 = date(y, m, 1)
                conditions.append(ApsBatchPlan.production_month == d0)
        except (ValueError, IndexError):
            pass

    if lineId is not None:
        q = q.join(ProductionSchedule, ApsBatchPlan.aps_schedule_id == ProductionSchedule.id)
        conditions.append(ProductionSchedule.line_id == lineId)

    if productCd and productCd.strip():
        conditions.append(ApsBatchPlan.product_cd == productCd.strip())

    if conditions:
        q = q.where(and_(*conditions))

    q = q.order_by(
        ApsBatchPlan.production_month.desc(),
        ApsBatchPlan.production_line.asc(),
        ApsBatchPlan.priority_order.asc(),
        ApsBatchPlan.lot_number.asc(),
    )

    result = await db.execute(q)
    return list(result.scalars().all())


# ═══════════════════ Run All / Sequential ═══════════════════

@router.post("/lines/{line_id}/replan-sequence")
async def replan_sequence(
    line_id: int,
    anchorStartDate: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    anchor = None
    if anchorStartDate:
        try:
            anchor = date.fromisoformat(anchorStartDate)
        except ValueError:
            raise HTTPException(400, "anchorStartDate は YYYY-MM-DD 形式")
    updated = await replan_line_sequential(db, line_id, anchor)
    # APS バッチ（lot_number）を instruction_plans へ同期（選択 B：時間精算は schedule_slice_allocations 起点）
    for ps in updated:
        await _sync_instruction_plans_from_aps_schedule(db, ps)
    await db.flush()
    return {
        "success": True,
        "data": {"count": len(updated)},
        "message": f"{len(updated)}件の工単を順次再計算しました",
    }


@router.post("/run-all")
async def run_all_schedules(
    lineId: Optional[int] = Query(None),
    sequential: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    if sequential and lineId is not None:
        updated = await replan_line_sequential(db, lineId)
        return {"success": True, "data": {"count": len(updated)}, "message": f"{len(updated)}件の工単を順次再計算しました"}

    q = select(ProductionSchedule).where(
        ProductionSchedule.status.in_(["PLANNING", "IN_PROGRESS"])
    )
    if lineId is not None:
        q = q.where(ProductionSchedule.line_id == lineId)
    result = await db.execute(q)
    schedules = result.scalars().all()
    count = 0
    for ps in schedules:
        await run_engine(db, ps.id, override_start_date=ps.start_date)
        count += 1
    await db.flush()
    return {"success": True, "data": {"count": count}, "message": f"{count}件の工単を再計算しました"}


# ═══════════════════ Daily Equipment Report ═══════════════════

@router.get("/daily-equipment-report")
async def get_daily_equipment_report(
    startDate: str = Query(...),
    endDate: str = Query(...),
    lineId: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    sql = text("""
        SELECT
            sd.schedule_date,
            m.id AS line_id,
            m.machine_cd AS line_code,
            ps.order_no,
            ps.item_name,
            ps.product_cd,
            sd.planned_qty,
            sd.actual_qty,
            lc.available_hours
        FROM schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN line_capacities lc ON lc.line_id = m.id AND lc.work_date = sd.schedule_date
        WHERE sd.schedule_date >= :sd AND sd.schedule_date <= :ed
          AND (:line_id IS NULL OR m.id = :line_id)
        ORDER BY sd.schedule_date, m.machine_cd, ps.order_no, ps.id
    """)
    result = await db.execute(sql, {"sd": sd, "ed": ed, "line_id": lineId})
    rows = result.mappings().all()

    report: list[dict] = []
    for r in rows:
        report.append({
            "schedule_date": r["schedule_date"].isoformat() if r["schedule_date"] else None,
            "line_id": r["line_id"],
            "line_code": r["line_code"],
            "order_no": r["order_no"],
            "item_name": r["item_name"],
            "product_cd": r["product_cd"],
            "planned_qty": int(r["planned_qty"] or 0),
            "actual_qty": int(r["actual_qty"] or 0),
            "available_hours": float(r["available_hours"]) if r["available_hours"] else None,
        })

    return {"success": True, "data": report}


# ═══════════════════ helpers ═══════════════════


async def _sum_actual_qty(db: AsyncSession, schedule_id: int) -> int:
    """schedule_details の actual_qty 合計（from-now 下限チェック用）。"""
    from sqlalchemy import func as sa_func
    res = await db.execute(
        select(sa_func.coalesce(sa_func.sum(ScheduleDetail.actual_qty), 0))
        .where(ScheduleDetail.schedule_id == schedule_id)
    )
    return int(res.scalar() or 0)


def _combine_work_date_and_time(work_d: date, t, *, end_of_day: bool = False) -> datetime:
    """work_date + period_start/period_end を datetime に結合（period_end=00:00 の 24:00 相当対応）。"""
    if end_of_day and t.hour == 0 and t.minute == 0 and t.second == 0:
        return datetime(work_d.year, work_d.month, work_d.day) + timedelta(days=1)
    return datetime(work_d.year, work_d.month, work_d.day, t.hour, t.minute, t.second or 0)


def _instruction_management_code(
    production_month: date,
    production_line: str,
    product_cd: str,
    priority_order: Optional[int],
    production_lot_size: int,
    lot_number: str,
) -> str:
    """instruction_plans の management_code トリガーと同等ロジック（照合用）。"""
    yy = str(production_month.year)[-2:]
    mm = f"{production_month.month:02d}"
    line_suffix = (production_line or "")[-2:]  # RIGHT(production_line,2)
    po = int(priority_order or 0)
    po2 = f"{po:02d}"
    pls2 = f"{int(production_lot_size or 0):02d}"
    ln = str(lot_number or "")
    ln2 = ln.zfill(2)[-2:]  # LPAD(COALESCE(lot_number,''),2,'0')
    return f"{yy}{mm}{product_cd}{line_suffix}{po2}-{pls2}-{ln2}"


async def _sync_instruction_plans_from_aps_schedule(db: AsyncSession, ps: ProductionSchedule) -> None:
    """
    APS の工単スケジュールをバッチ（lot_number）に展開し、instruction_plans へ同期する。

    実装方針:
    - 時間範囲は schedule_slice_allocations（時間別ガント）から切替点を精算して作成（選択 B）。
    - instruction_plans:
      - aps_batch_plan_id が紐づく行のみ上書き（手作業は維持）
      - cutting_management に既に存在する management_code のバッチは skip（既に移行済み）
    """
    # schedule は APS バッチ単位に分解できる前提
    if not ps.product_cd:
        return

    # schedule_slice_allocations を取得（時間順）
    slice_result = await db.execute(
        select(ScheduleSliceAllocation)
        .where(ScheduleSliceAllocation.schedule_id == ps.id)
        .order_by(
            ScheduleSliceAllocation.work_date,
            ScheduleSliceAllocation.period_start,
            ScheduleSliceAllocation.sort_order,
            ScheduleSliceAllocation.id,
        )
    )
    slices = slice_result.scalars().all()
    if not slices:
        return

    total_qty = sum(int(s.planned_qty or 0) for s in slices)
    if total_qty <= 0:
        return

    # 生産月/ライン/製品情報（管理コードと整合させるため機械側情報を優先）
    machine = await db.get(Machine, ps.line_id)
    if machine is None:
        return

    # instruction_plans の management_code トリガーは RIGHT(production_line,2) を使うため、
    # instruction_plans 側に保存する production_line は「設備名」に揃える
    production_line = (machine.machine_name or '').strip() or (machine.machine_cd or str(machine.id))
    production_name = ps.item_name or ""
    production_product_cd = (ps.product_cd or "").strip()

    # lot_size：スケジュール側のスナップショットが無い場合は products から取得
    lot_size_snapshot = int(getattr(ps, "lot_size_snapshot", 0) or 0)
    if lot_size_snapshot <= 0:
        pr_res = await db.execute(select(Product.lot_size).where(Product.product_cd == production_product_cd))
        lot_size_snapshot = int(pr_res.scalar() or 0)
    if lot_size_snapshot <= 0:
        return

    production_lot_size = int(math.ceil(total_qty / float(lot_size_snapshot)))
    production_lot_size = max(1, production_lot_size)

    # バッチ planned_quantity（最後のみ不足を許容）
    batch_qtys: List[tuple[int, int]] = []
    for i in range(1, production_lot_size + 1):
        if i < production_lot_size:
            batch_qtys.append((i, lot_size_snapshot))
        else:
            remain = total_qty - lot_size_snapshot * (production_lot_size - 1)
            batch_qtys.append((i, max(0, int(remain))))
    # バッチ数が極端に崩れる場合はガード
    batch_qtys = [(i, q) for i, q in batch_qtys if q > 0]
    if not batch_qtys:
        return

    # 生産月はスライスの最初日基準
    min_work_date = min(s.work_date for s in slices)
    production_month = date(min_work_date.year, min_work_date.month, 1)

    # バッチへ時間を割当（数量の順番に沿って部分スライスも按分）
    # schedule_slice_allocations は同一 schedule 内で時系列順に並んでいる前提
    batches = []
    batch_idx = 0
    batch_lot_number, batch_remaining = batch_qtys[batch_idx]
    batch_start_dt: Optional[datetime] = None
    batch_end_dt: Optional[datetime] = None
    batch_accum_qty = 0

    for s in slices:
        slice_total_qty = int(s.planned_qty or 0)
        if slice_total_qty <= 0:
            continue
        # 現在スライス内で、すでに割り当て済みの数量（用于部分時間）
        slice_allocated_qty_in_current = 0
        is_end_of_day = s.period_end == time(0, 0, 0) and s.period_start != time(0, 0, 0)
        slice_start_dt = _combine_work_date_and_time(s.work_date, s.period_start, end_of_day=False)
        slice_end_dt = _combine_work_date_and_time(s.work_date, s.period_end, end_of_day=is_end_of_day)
        duration_sec = max(0.0, (slice_end_dt - slice_start_dt).total_seconds())

        slice_remaining_qty = slice_total_qty - slice_allocated_qty_in_current
        while slice_remaining_qty > 0 and batch_idx < len(batch_qtys):
            lot_i, qty_i = batch_qtys[batch_idx]
            batch_need = int(qty_i - batch_accum_qty)
            if batch_need <= 0:
                # next batch
                batch_idx += 1
                batch_accum_qty = 0
                if batch_idx >= len(batch_qtys):
                    break
                batch_lot_number, batch_remaining = batch_qtys[batch_idx]
                batch_start_dt = None
                batch_end_dt = None
                continue

            portion_qty = min(slice_remaining_qty, batch_need)
            # portion 的时间按数量比例
            start_frac = slice_allocated_qty_in_current / float(slice_total_qty)
            end_allocated_qty = slice_allocated_qty_in_current + portion_qty
            end_frac = end_allocated_qty / float(slice_total_qty)
            portion_start_dt = slice_start_dt + timedelta(seconds=duration_sec * start_frac)
            portion_end_dt = slice_start_dt + timedelta(seconds=duration_sec * end_frac)

            if batch_start_dt is None:
                batch_start_dt = portion_start_dt
            batch_end_dt = portion_end_dt
            batch_accum_qty += portion_qty
            slice_allocated_qty_in_current += portion_qty
            slice_remaining_qty -= portion_qty

            if batch_accum_qty >= qty_i:
                batches.append(
                    {
                        "lot_number": str(lot_i),
                        "planned_quantity": int(qty_i),
                        "start_date": batch_start_dt,
                        "end_date": batch_end_dt,
                    }
                )
                batch_idx += 1
                batch_accum_qty = 0
                batch_start_dt = None
                batch_end_dt = None
    if not batches:
        return

    # バッチをアップサートして instruction_plans を同期
    for b in batches:
        lot_number = b["lot_number"]
        planned_quantity = int(b["planned_quantity"])
        start_dt = b["start_date"]
        end_dt = b["end_date"]

        # aps_batch_plans upsert（lot_number で一意）
        existing_q = await db.execute(
            select(ApsBatchPlan).where(
                ApsBatchPlan.aps_schedule_id == ps.id,
                ApsBatchPlan.lot_number == lot_number,
            )
        )
        existing = existing_q.scalars().first()
        if existing is None:
            new_row = ApsBatchPlan(
                aps_schedule_id=ps.id,
                production_month=production_month,
                production_line=str(production_line),
                priority_order=ps.order_no,
                product_cd=production_product_cd,
                product_name=production_name,
                planned_quantity=planned_quantity,
                production_lot_size=production_lot_size,
                lot_number=lot_number,
                start_date=start_dt,
                end_date=end_dt,
            )
            db.add(new_row)
            await db.flush()
            await db.refresh(new_row)
            batch_plan_id = new_row.id
        else:
            existing.production_month = production_month
            existing.production_line = str(production_line)
            existing.priority_order = ps.order_no
            existing.product_cd = production_product_cd
            existing.product_name = production_name
            existing.planned_quantity = planned_quantity
            existing.production_lot_size = production_lot_size
            existing.start_date = start_dt
            existing.end_date = end_dt
            await db.flush()
            batch_plan_id = existing.id

        # skip if already moved to cutting_management
        mc = _instruction_management_code(
            production_month=production_month,
            production_line=str(production_line),
            product_cd=production_product_cd,
            priority_order=ps.order_no,
            production_lot_size=production_lot_size,
            lot_number=lot_number,
        )
        cut_q = await db.execute(text("SELECT id FROM cutting_management WHERE management_code = :mc LIMIT 1"), {"mc": mc})
        if cut_q.scalar() is not None:
            continue

        # instruction_plans upsert by aps_batch_plan_id
        ins_find = await db.execute(
            text(
                "SELECT id, aps_batch_plan_id FROM instruction_plans WHERE aps_batch_plan_id = :bid LIMIT 1"
            ),
            {"bid": batch_plan_id},
        )
        found = ins_find.mappings().first()

        if found:
            ins_id = found.get("id")
            await db.execute(
                text(
                    "UPDATE instruction_plans SET "
                    "production_month=:production_month, production_line=:production_line, "
                    "priority_order=:priority_order, product_cd=:product_cd, product_name=:product_name, "
                    "planned_quantity=:planned_quantity, actual_production_quantity=:planned_quantity, start_date=:start_date, end_date=:end_date, "
                    "production_lot_size=:production_lot_size, lot_number=:lot_number, "
                    "aps_batch_plan_id=:aps_batch_plan_id "
                    "WHERE id=:ins_id"
                ),
                {
                    "ins_id": ins_id,
                    "production_month": production_month,
                    "production_line": str(production_line),
                    "priority_order": ps.order_no,
                    "product_cd": production_product_cd,
                    "product_name": production_name,
                    "planned_quantity": planned_quantity,
                    "start_date": start_dt,
                    "end_date": end_dt,
                    "production_lot_size": production_lot_size,
                    "lot_number": lot_number,
                    "aps_batch_plan_id": batch_plan_id,
                },
            )
        else:
            # conflict check: if a row already exists by management_code but is manual, don't overwrite
            ins_conf = await db.execute(
                text(
                    "SELECT id, aps_batch_plan_id FROM instruction_plans WHERE management_code = :mc LIMIT 1"
                ),
                {"mc": mc},
            )
            conf_row = ins_conf.mappings().first()
            if conf_row and conf_row.get("aps_batch_plan_id"):
                # previously generated, but different batch_plan_id -> update it instead
                ins_id = conf_row.get("id")
                await db.execute(
                    text(
                        "UPDATE instruction_plans SET "
                        "production_month=:production_month, production_line=:production_line, "
                        "priority_order=:priority_order, product_cd=:product_cd, product_name=:product_name, "
                        "planned_quantity=:planned_quantity, actual_production_quantity=:planned_quantity, start_date=:start_date, end_date=:end_date, "
                        "production_lot_size=:production_lot_size, lot_number=:lot_number, "
                        "aps_batch_plan_id=:aps_batch_plan_id "
                        "WHERE id=:ins_id"
                    ),
                    {
                        "ins_id": ins_id,
                        "production_month": production_month,
                        "production_line": str(production_line),
                        "priority_order": ps.order_no,
                        "product_cd": production_product_cd,
                        "product_name": production_name,
                        "planned_quantity": planned_quantity,
                        "start_date": start_dt,
                        "end_date": end_dt,
                        "production_lot_size": production_lot_size,
                        "lot_number": lot_number,
                        "aps_batch_plan_id": batch_plan_id,
                    },
                )
                continue
            if conf_row and not conf_row.get("aps_batch_plan_id"):
                # manual row -> preserve
                continue

            # insert new instruction_plans row
            await db.execute(
                text(
                    """
                    INSERT INTO instruction_plans (
                      production_month, production_line, priority_order, product_cd, product_name,
                      planned_quantity, start_date, end_date, production_lot_size, lot_number,
                      is_cutting_instructed, has_chamfering_process, is_chamfering_instructed,
                      has_sw_process, is_sw_instructed,
                      actual_production_quantity, take_count,
                      cutting_length, chamfering_length, developed_length, scrap_length,
                      material_name, material_manufacturer, standard_specification,
                      aps_batch_plan_id
                    ) VALUES (
                      :production_month, :production_line, :priority_order, :product_cd, :product_name,
                      :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
                      0, 0, 0,
                      0, 0,
                      :planned_quantity, NULL,
                      NULL, NULL, NULL, NULL,
                      NULL, NULL, NULL,
                      :aps_batch_plan_id
                    )
                    """
                ),
                {
                    "production_month": production_month,
                    "production_line": str(production_line),
                    "priority_order": ps.order_no,
                    "product_cd": production_product_cd,
                    "product_name": production_name,
                    "planned_quantity": planned_quantity,
                    "start_date": start_dt,
                    "end_date": end_dt,
                    "production_lot_size": production_lot_size,
                    "lot_number": lot_number,
                    "aps_batch_plan_id": batch_plan_id,
                },
            )


def _schedule_to_out(ps: ProductionSchedule) -> ScheduleOut:
    return ScheduleOut(
        id=ps.id,
        line_id=ps.line_id,
        order_no=ps.order_no,
        order_id=ps.order_id,
        item_name=ps.item_name or "",
        product_cd=getattr(ps, "product_cd", None),
        material_shortage=bool(ps.material_shortage),
        lot_qty=int(ps.lot_qty or 0),
        planned_batch_count=int(getattr(ps, "planned_batch_count", 0) or 0),
        lot_size_snapshot=int(getattr(ps, "lot_size_snapshot", 0) or 0),
        planned_process_qty=int(ps.planned_process_qty or 0),
        prev_month_carryover=int(ps.prev_month_carryover or 0),
        due_date=ps.due_date,
        material_date=ps.material_date,
        setup_time=int(ps.setup_time or 0),
        efficiency=_dec(ps.efficiency),
        daily_capacity=int(ps.daily_capacity or 0),
        planned_output_qty=int(ps.planned_output_qty or 0),
        start_date=ps.start_date,
        end_date=ps.end_date,
        completion_rate=_dec(ps.completion_rate) if ps.completion_rate is not None else None,
        status=ps.status or "PLANNING",
    )
