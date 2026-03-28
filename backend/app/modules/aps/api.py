"""
APS（先進的計画・スケジューリング）APIエンドポイント
産線管理、稼働カレンダー、工単 CRUD、排産エンジン、スケジューリンググリッド
"""
import math
from collections import defaultdict
from datetime import date, timedelta, datetime, time
from decimal import Decimal
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_, delete, text
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

from app.modules.master.models import Machine, EquipmentEfficiency, Process, Product, Material, Supplier
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
    ProgressLotItem,
    ProductionProgressResponse,
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
                    f"ロット数は {min_batches} 以上にしてください。",
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
            details = detail_result.scalars().all()
            daily: dict[str, int] = {}
            for det in details:
                key = det.schedule_date.isoformat()
                daily[key] = daily.get(key, 0) + int(det.planned_qty or 0)
                daily_totals[key] += int(det.planned_qty or 0)

            actual_daily: dict[str, int] = {}
            remaining_daily: dict[str, int] = {}
            for det in details:
                key = det.schedule_date.isoformat()
                actual_daily[key] = actual_daily.get(key, 0) + int(det.actual_qty or 0)
                remaining_daily[key] = remaining_daily.get(key, 0) + int(getattr(det, "remaining_qty", 0) or 0)

            for k, planned_q in daily.items():
                if k not in remaining_daily:
                    remaining_daily[k] = max(0, int(planned_q or 0) - int(actual_daily.get(k, 0) or 0))

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
                actual_daily=actual_daily,
                remaining_daily=remaining_daily,
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
    """
    ライン順で再計算（実績考慮を統合）。
    ステップ 1: anchor から通常の順次排産（ガント生成）
    ステップ 2: stock_transaction_logs → schedule_details.actual_qty 同期
    ステップ 3: 実績のある工単は「最後の actual>0 の翌日」から残数で再排産
    """
    anchor = None
    if anchorStartDate:
        try:
            anchor = date.fromisoformat(anchorStartDate)
        except ValueError:
            raise HTTPException(400, "anchorStartDate は YYYY-MM-DD 形式")

    # ── Step 1: 通常の順次排産 ──
    updated = await replan_line_sequential(db, line_id, anchor)
    await db.flush()

    # ── Step 2: stock_transaction_logs → schedule_details.actual_qty 同期 ──
    for ps in updated:
        await _sync_actual_from_stock_logs(db, ps)
    await db.flush()

    # ── Step 3: 実績がある工単は残数ベースで再排産 ──
    schedules_with_actual: list[ProductionSchedule] = []
    for ps in updated:
        has_actual = await _schedule_has_actual(db, ps.id)
        if has_actual:
            schedules_with_actual.append(ps)

    if schedules_with_actual:
        cursor_date_r = anchor or updated[0].start_date or now_jst().date()
        cursor_time_r = time(0, 0, 0)

        for ps in updated:
            if ps in schedules_with_actual:
                last_actual_date = await _last_actual_date_for_schedule(db, ps.id)
                if last_actual_date is not None:
                    replan_start = last_actual_date + timedelta(days=1)
                    if replan_start > cursor_date_r:
                        cursor_date_r = replan_start

                period_planned = await _sum_planned_qty_in_details(db, ps.id)
                period_actual = await _sum_actual_qty(db, ps.id)
                remaining = max(0, period_planned - period_actual)

                planned_total = int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0)
                actual_done_for_engine = max(0, planned_total - remaining)

                ps = await run_engine(
                    db,
                    ps.id,
                    override_start_date=cursor_date_r,
                    override_start_time=cursor_time_r,
                    actual_done_qty=actual_done_for_engine,
                )
            else:
                ps = await run_engine(
                    db,
                    ps.id,
                    override_start_date=cursor_date_r,
                    override_start_time=cursor_time_r,
                )

            await db.flush()
            last_q = await db.execute(
                select(ScheduleSliceAllocation)
                .where(ScheduleSliceAllocation.schedule_id == ps.id)
                .order_by(
                    ScheduleSliceAllocation.work_date.desc(),
                    ScheduleSliceAllocation.period_end.desc(),
                    ScheduleSliceAllocation.sort_order.desc(),
                )
                .limit(1)
            )
            last = last_q.scalars().first()
            if last is not None:
                cursor_date_r = last.work_date
                cursor_time_r = last.period_end
                if cursor_time_r == time(0, 0, 0) and last.period_start != time(0, 0, 0):
                    cursor_date_r = cursor_date_r + timedelta(days=1)
                    cursor_time_r = time(0, 0, 0)
            else:
                cursor_date_r = ps.end_date or (cursor_date_r + timedelta(days=1))
                cursor_time_r = time(0, 0, 0)

        # Step 2 再执行：重排后再同步一次 actual_qty
        for ps in updated:
            await _sync_actual_from_stock_logs(db, ps)
        await db.flush()

    # instruction_plans 同期
    for ps in updated:
        await _sync_instruction_plans_from_aps_schedule(db, ps)
    await db.flush()

    return {
        "success": True,
        "data": {"count": len(updated)},
        "message": f"{len(updated)}件の工単を再計算しました（実績考慮済み）",
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


# ═══════════════════ Production Progress（生産進捗） ═══════════════════


def _batch_display_planned_qty(batch: ApsBatchPlan) -> int:
    """計画一覧で確定したロット本数。original_planned_quantity があれば優先（成型再排産で planned_quantity が変わっても不変）。"""
    oq = getattr(batch, "original_planned_quantity", None)
    if oq is not None and int(oq) > 0:
        return int(oq)
    return int(batch.planned_quantity or 0)


def _split_actual_across_lots(actual_total: int, shares: dict[str, int]) -> dict[str, int]:
    """
    工単日次 actual_qty をロット間で按分（スライス計画日別比率）。最大剰余法で合計を一致。
    shares に正の値が無い場合は先頭ロットに全量を寄せる。
    """
    if actual_total <= 0:
        return {k: 0 for k in shares}
    keys = list(shares.keys())
    if not keys:
        return {}
    out = {k: 0 for k in keys}
    positive = [(k, shares[k]) for k in sorted(keys) if shares[k] > 0]
    if not positive:
        out[sorted(keys)[0]] = actual_total
        return out
    total_share = sum(v for _, v in positive)
    allocated = 0
    fractions: list[tuple[float, str]] = []
    for k, v in positive:
        exact = actual_total * v / total_share
        q = int(math.floor(exact))
        out[k] = q
        allocated += q
        fractions.append((exact - q, k))
    diff = actual_total - allocated
    fractions.sort(key=lambda x: -x[0])
    for i in range(diff):
        out[fractions[i % len(fractions)][1]] += 1
    return out


def _lot_displayed_consumed_before(
    lot_daily: dict[str, dict[str, int]],
    lk: str,
    before_d: str,
) -> int:
    dm = lot_daily.get(lk) or {}
    return sum(int(dm[d]) for d in sorted(dm.keys()) if d < before_d)


def _allocate_day_total_across_lots(
    lot_keys: List[str],
    target: int,
    weights: dict[str, int],
    rooms: dict[str, int],
) -> dict[str, int]:
    """
    target を weights 比でロットに配分。各ロットは rooms[lk] を上限。端数は最大剰余で target まで埋める。
    """
    out = {lk: 0 for lk in lot_keys}
    if target <= 0 or not lot_keys:
        return out
    W = sum(max(0, int(weights.get(lk, 0) or 0)) for lk in lot_keys)
    rem = target
    fr: list[tuple[float, str]] = []
    if W <= 0:
        idx = 0
        while rem > 0 and idx < len(lot_keys) * (target + 5):
            progressed = False
            for lk in sorted(lot_keys):
                if rem <= 0:
                    break
                if out[lk] < max(0, int(rooms.get(lk, 0) or 0)):
                    out[lk] += 1
                    rem -= 1
                    progressed = True
            if not progressed:
                break
            idx += 1
        return out
    for lk in lot_keys:
        w = max(0, int(weights.get(lk, 0) or 0))
        x = target * w / W if W > 0 else 0.0
        q = int(math.floor(x))
        q = min(q, max(0, int(rooms.get(lk, 0) or 0)))
        out[lk] = q
        fr.append((x - q, lk))
        rem -= q
    fr.sort(key=lambda z: -z[0])
    guard = 0
    while rem > 0 and guard < 100000:
        progressed = False
        for _, lk in fr:
            if rem <= 0:
                break
            cap_r = max(0, int(rooms.get(lk, 0) or 0))
            if out[lk] < cap_r:
                out[lk] += 1
                rem -= 1
                progressed = True
        if not progressed:
            break
        guard += 1
    return out


def _align_progress_planned_to_schedule_day_totals(
    lot_daily: dict[str, dict[str, int]],
    lot_daily_source: dict[str, dict[str, str]],
    planned_by_schedule_date: dict[int, dict[str, int]],
    actual_by_schedule_date: dict[int, dict[str, int]],
    sched_lot_keys: dict[int, list[str]],
    lot_planned_daily: dict[str, dict[str, int]],
    lot_planned_cap: dict[str, int],
) -> None:
    """
    ガント（日別）の schedule_details.planned_qty 日次合計と、生産進捗の「計画」セル合計を一致させる。
    成型実績のない日は工単日計 P に合わせてロット間で再按分（スライス比率・各ロット残枠を考慮）。
    ロット残枠の合計が P 未満のときは合計は min(P, 残枠合計) に留まる（データ上の上限）。
    """
    for sid, lot_keys in sched_lot_keys.items():
        uniq_keys = list(dict.fromkeys(lot_keys))
        all_dates: set[str] = set()
        for lk in uniq_keys:
            all_dates |= set((lot_daily.get(lk) or {}).keys())
        for d_str in sorted(all_dates):
            if int(actual_by_schedule_date.get(sid, {}).get(d_str, 0) or 0) > 0:
                continue
            P = int(planned_by_schedule_date.get(sid, {}).get(d_str, 0) or 0)
            if P <= 0:
                continue
            participating: List[str] = []
            for lk in uniq_keys:
                src = (lot_daily_source.get(lk) or {}).get(d_str)
                if src == "ACTUAL":
                    continue
                cap = int(lot_planned_cap.get(lk, 0) or 0)
                prev = _lot_displayed_consumed_before(lot_daily, lk, d_str)
                room = max(0, cap - prev)
                has_cell = d_str in (lot_daily.get(lk) or {})
                raw_w = int((lot_planned_daily.get(lk) or {}).get(d_str, 0) or 0)
                if has_cell and src in ("PLANNED", "WAIT_UPSTREAM"):
                    participating.append(lk)
                elif not has_cell and room > 0 and raw_w > 0:
                    participating.append(lk)
            if not participating:
                continue
            Q = sum(int((lot_daily.get(lk) or {}).get(d_str, 0) or 0) for lk in participating)
            if Q == P:
                continue
            rooms = {
                lk: max(
                    0,
                    int(lot_planned_cap.get(lk, 0) or 0) - _lot_displayed_consumed_before(lot_daily, lk, d_str),
                )
                for lk in participating
            }
            weights = {lk: max(0, int((lot_planned_daily.get(lk) or {}).get(d_str, 0) or 0)) for lk in participating}
            cap_sum = sum(rooms[lk] for lk in participating)
            target = min(P, cap_sum)
            if target <= 0:
                for lk in participating:
                    if lk in lot_daily and d_str in lot_daily[lk]:
                        del lot_daily[lk][d_str]
                    if lk in lot_daily_source and d_str in lot_daily_source[lk]:
                        del lot_daily_source[lk][d_str]
                continue
            alloc = _allocate_day_total_across_lots(participating, target, weights, rooms)
            for lk in participating:
                nq = int(alloc.get(lk, 0) or 0)
                src_prev = (lot_daily_source.get(lk) or {}).get(d_str, "PLANNED")
                if nq <= 0:
                    if lk in lot_daily and d_str in lot_daily[lk]:
                        del lot_daily[lk][d_str]
                    if lk in lot_daily_source and d_str in lot_daily_source[lk]:
                        del lot_daily_source[lk][d_str]
                else:
                    if lk not in lot_daily:
                        lot_daily[lk] = {}
                    if lk not in lot_daily_source:
                        lot_daily_source[lk] = {}
                    lot_daily[lk][d_str] = nq
                    lot_daily_source[lk][d_str] = src_prev if src_prev in ("PLANNED", "WAIT_UPSTREAM") else "PLANNED"


def _enforce_lot_progress_row_sum_cap(
    lot_daily: dict[str, dict[str, int]],
    lot_daily_source: dict[str, dict[str, str]],
    lot_planned_cap: dict[str, int],
) -> None:
    """
    各ロット行の日別セル合計が planned_quantity を超えないようにする。
    工単日次との整列（_align）と実績按分の組み合わせで、同一ロットの合計が 1956+1400 のように
    計画数を超えることがあるため、最後に矯正する。
    新しい日から PLANNED/WAIT_UPSTREAM を削り、足りなければ ACTUAL 表示も削る。
    """
    for lk, cap in lot_planned_cap.items():
        if cap <= 0:
            continue
        daily = lot_daily.get(lk)
        if not daily:
            continue
        src_map = lot_daily_source.setdefault(lk, {})
        total = sum(int(v) for v in daily.values())
        if total <= cap:
            continue
        excess = total - cap
        for d_str in sorted(daily.keys(), reverse=True):
            if excess <= 0:
                break
            if src_map.get(d_str, "PLANNED") == "ACTUAL":
                continue
            q = int(daily[d_str])
            if q <= 0:
                continue
            cut = min(q, excess)
            excess -= cut
            nq = q - cut
            if nq <= 0:
                del daily[d_str]
                src_map.pop(d_str, None)
            else:
                daily[d_str] = nq
        for d_str in sorted(daily.keys(), reverse=True):
            if excess <= 0:
                break
            q = int(daily[d_str])
            if q <= 0:
                continue
            cut = min(q, excess)
            excess -= cut
            nq = q - cut
            if nq <= 0:
                del daily[d_str]
                src_map.pop(d_str, None)
            else:
                daily[d_str] = nq


def _sort_lot_keys_in_schedule(uniq_keys: List[str]) -> List[str]:
    """同一工単内の lot_key（{schedule_id}_{lot_number}）をロット番号昇順で並べる。"""

    def sort_key(lk: str) -> tuple:
        try:
            _, lot_rest = lk.split("_", 1)
        except ValueError:
            return (1, lk)
        try:
            return (0, int(str(lot_rest).strip()))
        except ValueError:
            return (1, lot_rest)

    return sorted(uniq_keys, key=sort_key)


def _collect_schedule_progress_dates(
    sid: int,
    ordered_lks: List[str],
    lot_planned_daily: dict[str, dict[str, int]],
    actual_by_schedule_date: dict[int, dict[str, int]],
    planned_by_schedule_date: dict[int, dict[str, int]],
) -> List[str]:
    ds: set[str] = set()
    for lk in ordered_lks:
        ds |= set((lot_planned_daily.get(lk) or {}).keys())
    for dk, aq in (actual_by_schedule_date.get(sid) or {}).items():
        if int(aq or 0) > 0:
            ds.add(dk)
    ds |= set((planned_by_schedule_date.get(sid) or {}).keys())
    return sorted(ds)


def _build_lot_daily_sequential_forming_actuals(
    sid: int,
    uniq_keys: List[str],
    lot_planned_daily: dict[str, dict[str, int]],
    lot_planned_cap: dict[str, int],
    lot_progress_status: dict[str, str],
    actual_by_schedule_date: dict[int, dict[str, int]],
    planned_by_schedule_date: dict[int, dict[str, int]],
    material_flag: bool,
    lot_daily: dict[str, dict[str, int]],
    lot_daily_source: dict[str, dict[str, str]],
) -> None:
    """
    日次成型実績はロット番号順にのみ割当て：先頭ロットの残 cap を尽くしてから次ロットへ（同日も同様）。
    スライス比率での横並び按分はしない。残計画は cap 控除後、最終実績日の翌日以降にスライス形状で配分。
    """
    ordered = _sort_lot_keys_in_schedule(list(dict.fromkeys(uniq_keys)))
    if not ordered:
        return
    sorted_dates = _collect_schedule_progress_dates(
        sid, ordered, lot_planned_daily, actual_by_schedule_date, planned_by_schedule_date
    )
    if not sorted_dates:
        return

    rem_cap = {lk: max(0, int(lot_planned_cap.get(lk, 0) or 0)) for lk in ordered}

    for d_str in sorted_dates:
        a_left = int((actual_by_schedule_date.get(sid) or {}).get(d_str, 0) or 0)
        if a_left <= 0:
            continue
        i = 0
        while a_left > 0:
            while i < len(ordered) and rem_cap.get(ordered[i], 0) <= 0:
                i += 1
            if i >= len(ordered):
                break
            lk = ordered[i]
            room = rem_cap[lk]
            x = min(a_left, room)
            if x <= 0:
                i += 1
                continue
            lot_daily.setdefault(lk, {})
            lot_daily[lk][d_str] = int(lot_daily[lk].get(d_str, 0) or 0) + x
            lot_daily_source.setdefault(lk, {})
            lot_daily_source[lk][d_str] = "ACTUAL"
            rem_cap[lk] -= x
            a_left -= x

    for lk in ordered:
        rem = rem_cap.get(lk, 0)
        if rem <= 0:
            continue
        src_map = lot_daily_source.setdefault(lk, {})
        dm = lot_daily.setdefault(lk, {})
        last_actual: Optional[str] = None
        for d_str in sorted(dm.keys()):
            if int(dm.get(d_str) or 0) > 0 and src_map.get(d_str) == "ACTUAL":
                last_actual = d_str

        eligible = [d for d in sorted_dates if last_actual is None or d > last_actual]
        if not eligible:
            eligible = sorted_dates
        weights = {d: max(0, int((lot_planned_daily.get(lk) or {}).get(d, 0) or 0)) for d in eligible}
        wsum = sum(weights.values())
        if wsum <= 0:
            weights = {d: 1 for d in eligible}
        alloc = _split_actual_across_lots(rem, weights)
        st = lot_progress_status.get(lk, "PLANNED")
        src = "WAIT_UPSTREAM" if (material_flag or st == "PLANNED") else "PLANNED"
        for d_str, q in alloc.items():
            qn = int(q or 0)
            if qn <= 0:
                continue
            if src_map.get(d_str) == "ACTUAL":
                continue
            cur = int(dm.get(d_str, 0) or 0)
            dm[d_str] = cur + qn
            src_map[d_str] = src


def _trim_lot_progress_by_lot_cap(
    lot_daily: dict[str, dict[str, int]],
    lot_daily_source: dict[str, dict[str, str]],
    lot_cap: dict[str, int],
) -> None:
    """
    各ロットの計画数（aps_batch_plans.planned_quantity）を上限に、日付昇順で処理する。
    先に出た実績（ACTUAL）で本数を消化し、残りに対してのみ PLANNED / WAIT_UPSTREAM を表示する。
    例: 計画1956、1日目実績1400 → 2日目のスライス按分が1956でも表示は556に縮む。
    """
    for lk, cap in lot_cap.items():
        if cap <= 0:
            continue
        daily = lot_daily.get(lk)
        if not daily:
            continue
        src_map = lot_daily_source.setdefault(lk, {})
        consumed = 0
        for d_str in sorted(daily.keys()):
            q = int(daily.get(d_str) or 0)
            if q <= 0:
                continue
            src = src_map.get(d_str, "PLANNED")
            if src == "ACTUAL":
                consumed += q
                continue
            room = max(0, cap - consumed)
            new_q = min(q, room)
            if new_q <= 0:
                del daily[d_str]
                src_map.pop(d_str, None)
            else:
                daily[d_str] = new_q
                consumed += new_q


@router.get("/production-progress", response_model=ProductionProgressResponse)
async def get_production_progress(
    lineId: int = Query(..., description="対象設備 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定ラインの APS ロットごとに instruction_plans / cutting_management を照合し、
    リアルタイムの生産進捗ステータス＋日別数量を返す。
    全 aps_batch_plans ロットを返し、本工程（成型）の日別計画・実績を欠かさない。
    cutting_management / instruction_plans はステータス・切断(本)列のみに使用し、行の有無では落とさない。
    cutting_management にあれば生産中、instruction_plans のみなら指示済、未同期は PLANNED。
    日別セルは成型ガント連動（schedule_details の planned/actual）。actual_qty は再計算時に在庫ログから
    当該設備・製品へ同期される成型実績であり、切断完工の代替ではない。切断の本数・完了は cutting_* フィールドで返す。
    True のとき成型実績はロット番号順に日次のみ割当（同日も先頭ロットから順に、横並び按分なし）、残計画はスライス再配置。
    False のときは従来のスライス比率実績按分。
    計画数表示は original_planned_quantity を維持。上流待ちは WAIT_UPSTREAM。
    """
    sched_result = await db.execute(
        select(ProductionSchedule)
        .where(ProductionSchedule.line_id == lineId)
        .order_by(ProductionSchedule.order_no, ProductionSchedule.id)
    )
    schedules = sched_result.scalars().all()
    if not schedules:
        return ProductionProgressResponse(lots=[], dates=[], lot_daily={}, lot_daily_source={})

    schedule_map = {s.id: s for s in schedules}
    schedule_ids = list(schedule_map.keys())

    batch_result = await db.execute(
        select(ApsBatchPlan)
        .where(ApsBatchPlan.aps_schedule_id.in_(schedule_ids))
        .order_by(ApsBatchPlan.aps_schedule_id, ApsBatchPlan.lot_number)
    )
    batches = batch_result.scalars().all()
    if not batches:
        return ProductionProgressResponse(lots=[], dates=[], lot_daily={}, lot_daily_source={})

    if _PRODUCTION_PROGRESS_USE_FORMING_ACTUAL:
        for ps in schedules:
            await _sync_actual_from_stock_logs(db, ps)
        await db.flush()

    slice_result = await db.execute(
        select(ScheduleSliceAllocation)
        .where(ScheduleSliceAllocation.schedule_id.in_(schedule_ids))
        .order_by(
            ScheduleSliceAllocation.schedule_id,
            ScheduleSliceAllocation.work_date,
            ScheduleSliceAllocation.period_start,
            ScheduleSliceAllocation.sort_order,
        )
    )
    all_slices = slice_result.scalars().all()
    slices_by_sched: dict[int, list] = defaultdict(list)
    for s in all_slices:
        slices_by_sched[s.schedule_id].append(s)

    det_result = await db.execute(
        select(ScheduleDetail).where(ScheduleDetail.schedule_id.in_(schedule_ids))
    )
    actual_by_schedule_date: dict[int, dict[str, int]] = defaultdict(dict)
    planned_by_schedule_date: dict[int, dict[str, int]] = defaultdict(dict)
    for det in det_result.scalars().all():
        dkey = det.schedule_date.isoformat()
        sid = det.schedule_id
        planned_by_schedule_date[sid][dkey] = planned_by_schedule_date[sid].get(dkey, 0) + int(det.planned_qty or 0)
        if _PRODUCTION_PROGRESS_USE_FORMING_ACTUAL:
            actual_by_schedule_date[sid][dkey] = actual_by_schedule_date[sid].get(dkey, 0) + int(det.actual_qty or 0)

    lot_planned_daily: dict[str, dict[str, int]] = {}
    lot_progress_status: dict[str, str] = {}
    lot_planned_cap: dict[str, int] = {}
    sched_lot_keys: dict[int, list[str]] = defaultdict(list)
    lots: list[ProgressLotItem] = []

    for batch in batches:
        ps = schedule_map.get(batch.aps_schedule_id)
        if not ps:
            continue

        mc = _instruction_management_code(
            production_month=batch.production_month,
            production_line=batch.production_line,
            product_cd=batch.product_cd,
            priority_order=batch.priority_order,
            production_lot_size=batch.production_lot_size,
            lot_number=batch.lot_number,
        )

        progress_status = "PLANNED"
        cut_planned: Optional[int] = None
        cut_actual: Optional[int] = None
        cut_done: Optional[bool] = None
        try:
            cut_res = await db.execute(
                text(
                    "SELECT planned_quantity, actual_production_quantity, "
                    "COALESCE(production_completed_check, 0) AS pcc "
                    "FROM cutting_management WHERE management_code = :mc LIMIT 1"
                ),
                {"mc": mc},
            )
            cut_row = cut_res.mappings().first()
            if cut_row is not None:
                progress_status = "IN_PROGRESS"
                cut_planned = int(cut_row.get("planned_quantity") or 0)
                cut_actual = int(cut_row.get("actual_production_quantity") or 0)
                cut_done = bool(int(cut_row.get("pcc") or 0))
            else:
                ins_q = await db.execute(
                    text(
                        "SELECT id FROM instruction_plans "
                        "WHERE aps_batch_plan_id = :bid OR management_code = :mc "
                        "ORDER BY id DESC LIMIT 1"
                    ),
                    {"bid": batch.id, "mc": mc},
                )
                if ins_q.scalar() is not None:
                    progress_status = "RELEASED"
        except (OperationalError, ProgrammingError):
            pass

        start_iso = batch.start_date.isoformat() if batch.start_date else None
        end_iso = batch.end_date.isoformat() if batch.end_date else None

        lots.append(ProgressLotItem(
            batch_plan_id=batch.id,
            aps_schedule_id=batch.aps_schedule_id,
            product_cd=batch.product_cd,
            product_name=batch.product_name,
            lot_number=batch.lot_number,
            planned_quantity=_batch_display_planned_qty(batch),
            order_no=ps.order_no,
            start_date=start_iso,
            end_date=end_iso,
            predicted_completion=end_iso,
            progress_status=progress_status,
            management_code=mc,
            production_line=batch.production_line or "",
            cutting_planned_qty=cut_planned,
            cutting_actual_qty=cut_actual,
            cutting_completed=cut_done,
        ))

        lot_key = f"{batch.aps_schedule_id}_{batch.lot_number}"
        sched_lot_keys[ps.id].append(lot_key)
        lot_progress_status[lot_key] = progress_status
        lot_planned_cap[lot_key] = max(
            lot_planned_cap.get(lot_key, 0),
            _batch_display_planned_qty(batch),
        )
        daily_map: dict[str, int] = {}

        slices = slices_by_sched.get(ps.id, [])
        if slices and batch.start_date and batch.end_date:
            b_start = batch.start_date
            b_end = batch.end_date
            for sl in slices:
                sl_start = _combine_work_date_and_time(sl.work_date, sl.period_start, end_of_day=False)
                is_eod = sl.period_end == time(0, 0, 0) and sl.period_start != time(0, 0, 0)
                sl_end = _combine_work_date_and_time(sl.work_date, sl.period_end, end_of_day=is_eod)
                if sl_end <= b_start or sl_start >= b_end:
                    continue
                sq = int(sl.planned_qty or 0)
                if sq <= 0:
                    continue
                overlap_start = max(sl_start, b_start)
                overlap_end = min(sl_end, b_end)
                sl_dur = max(1.0, (sl_end - sl_start).total_seconds())
                overlap_dur = max(0.0, (overlap_end - overlap_start).total_seconds())
                portion = int(round(sq * overlap_dur / sl_dur))
                if portion <= 0:
                    continue
                d_key = sl.work_date.isoformat()
                daily_map[d_key] = daily_map.get(d_key, 0) + portion

        lot_planned_daily[lot_key] = daily_map

    lot_daily: dict[str, dict[str, int]] = {}
    lot_daily_source: dict[str, dict[str, str]] = {}

    for sid, lot_keys in sched_lot_keys.items():
        ps = schedule_map.get(sid)
        if ps is None or not lot_keys:
            continue
        uniq_keys = list(dict.fromkeys(lot_keys))
        material_flag = bool(ps.material_shortage)
        if _PRODUCTION_PROGRESS_USE_FORMING_ACTUAL:
            _build_lot_daily_sequential_forming_actuals(
                sid,
                uniq_keys,
                lot_planned_daily,
                lot_planned_cap,
                lot_progress_status,
                actual_by_schedule_date,
                planned_by_schedule_date,
                material_flag,
                lot_daily,
                lot_daily_source,
            )
            continue

        date_keys: set[str] = set()
        for lk in uniq_keys:
            date_keys |= set(lot_planned_daily.get(lk, {}).keys())
        for dk, aq in actual_by_schedule_date.get(sid, {}).items():
            if aq > 0:
                date_keys.add(dk)

        for d_str in sorted(date_keys):
            actual_total = int(actual_by_schedule_date.get(sid, {}).get(d_str, 0) or 0)
            shares = {lk: lot_planned_daily.get(lk, {}).get(d_str, 0) for lk in uniq_keys}

            if actual_total > 0:
                split = _split_actual_across_lots(actual_total, shares)
                for lk in uniq_keys:
                    q = int(split.get(lk, 0) or 0)
                    if q <= 0:
                        continue
                    if lk not in lot_daily:
                        lot_daily[lk] = {}
                    if lk not in lot_daily_source:
                        lot_daily_source[lk] = {}
                    lot_daily[lk][d_str] = q
                    lot_daily_source[lk][d_str] = "ACTUAL"
                continue

            for lk in uniq_keys:
                q = int(shares.get(lk, 0) or 0)
                if q <= 0:
                    continue
                st = lot_progress_status.get(lk, "PLANNED")
                src = "WAIT_UPSTREAM" if (material_flag or st == "PLANNED") else "PLANNED"
                if lk not in lot_daily:
                    lot_daily[lk] = {}
                if lk not in lot_daily_source:
                    lot_daily_source[lk] = {}
                lot_daily[lk][d_str] = q
                lot_daily_source[lk][d_str] = src

    _trim_lot_progress_by_lot_cap(lot_daily, lot_daily_source, lot_planned_cap)
    _align_progress_planned_to_schedule_day_totals(
        lot_daily,
        lot_daily_source,
        planned_by_schedule_date,
        actual_by_schedule_date,
        sched_lot_keys,
        lot_planned_daily,
        lot_planned_cap,
    )
    _enforce_lot_progress_row_sum_cap(lot_daily, lot_daily_source, lot_planned_cap)
    all_dates_set: set[str] = set()
    for dm in lot_daily.values():
        all_dates_set |= set(dm.keys())
    dates = sorted(all_dates_set)
    return ProductionProgressResponse(
        lots=lots,
        dates=dates,
        lot_daily=lot_daily,
        lot_daily_source=lot_daily_source,
    )


# ═══════════════════ helpers ═══════════════════


async def _sum_actual_qty(db: AsyncSession, schedule_id: int) -> int:
    """schedule_details の actual_qty 合計（from-now 下限チェック用）。"""
    from sqlalchemy import func as sa_func
    res = await db.execute(
        select(sa_func.coalesce(sa_func.sum(ScheduleDetail.actual_qty), 0))
        .where(ScheduleDetail.schedule_id == schedule_id)
    )
    return int(res.scalar() or 0)


async def _actual_daily_from_schedule_details(
    db: AsyncSession,
    schedule_id: int,
    start_date: date,
    end_date: date,
) -> dict[str, int]:
    """
    schedule_details から実績を日別集計（YYYY-MM-DD -> qty）。
    """
    q = await db.execute(
        select(ScheduleDetail).where(
            ScheduleDetail.schedule_id == schedule_id,
            ScheduleDetail.schedule_date >= start_date,
            ScheduleDetail.schedule_date <= end_date,
        )
    )
    out: dict[str, int] = {}
    for det in q.scalars().all():
        k = det.schedule_date.isoformat()
        out[k] = out.get(k, 0) + int(det.actual_qty or 0)
    return out


async def _sum_actual_qty_until(
    db: AsyncSession,
    schedule_id: int,
    start_date: date,
    end_date: date,
) -> int:
    if end_date < start_date:
        return 0
    res = await db.execute(
        select(ScheduleDetail).where(
            ScheduleDetail.schedule_id == schedule_id,
            ScheduleDetail.schedule_date >= start_date,
            ScheduleDetail.schedule_date <= end_date,
        )
    )
    return sum(int(r.actual_qty or 0) for r in res.scalars().all())


async def _last_actual_date_for_line(db: AsyncSession, line_id: int) -> Optional[date]:
    rows = await db.execute(
        select(ScheduleDetail.schedule_date)
        .join(ProductionSchedule, ProductionSchedule.id == ScheduleDetail.schedule_id)
        .where(
            ProductionSchedule.line_id == line_id,
            ScheduleDetail.actual_qty > 0,
        )
        .order_by(ScheduleDetail.schedule_date.desc())
        .limit(1)
    )
    return rows.scalar_one_or_none()


async def _sync_actual_from_stock_logs(db: AsyncSession, ps: ProductionSchedule):
    """
    成型実績：stock_transaction_logs（実績・当該設備 machine_cd・製品 target_cd）を
    schedule_details.actual_qty に日付単位で同期。切断完工ではない。
    run_engine 後に schedule_details が再作成されるため、DB トリガーが効かないケースを補完する。
    """
    from sqlalchemy import func as sa_func

    machine = await db.get(Machine, ps.line_id)
    if machine is None:
        return

    details_res = await db.execute(
        select(ScheduleDetail).where(ScheduleDetail.schedule_id == ps.id)
    )
    details = details_res.scalars().all()
    if not details:
        return

    from app.modules.erp.stock_transaction_log_models import StockTransactionLog

    for det in details:
        agg_res = await db.execute(
            select(sa_func.coalesce(sa_func.sum(StockTransactionLog.quantity), 0))
            .where(
                StockTransactionLog.transaction_type == '実績',
                StockTransactionLog.transaction_time.isnot(None),
                sa_func.date(StockTransactionLog.transaction_time) == det.schedule_date,
                StockTransactionLog.machine_cd == machine.machine_cd,
                StockTransactionLog.target_cd == ps.product_cd,
            )
        )
        actual = int(agg_res.scalar() or 0)
        det.actual_qty = actual
        det.remaining_qty = max(0, int(det.planned_qty or 0) - actual)


async def _schedule_has_actual(db: AsyncSession, schedule_id: int) -> bool:
    from sqlalchemy import func as sa_func
    res = await db.execute(
        select(sa_func.coalesce(sa_func.sum(ScheduleDetail.actual_qty), 0))
        .where(ScheduleDetail.schedule_id == schedule_id)
    )
    return int(res.scalar() or 0) > 0


async def _last_actual_date_for_schedule(db: AsyncSession, schedule_id: int) -> Optional[date]:
    rows = await db.execute(
        select(ScheduleDetail.schedule_date)
        .where(
            ScheduleDetail.schedule_id == schedule_id,
            ScheduleDetail.actual_qty > 0,
        )
        .order_by(ScheduleDetail.schedule_date.desc())
        .limit(1)
    )
    return rows.scalar_one_or_none()


async def _sum_planned_qty_in_details(db: AsyncSession, schedule_id: int) -> int:
    from sqlalchemy import func as sa_func
    res = await db.execute(
        select(sa_func.coalesce(sa_func.sum(ScheduleDetail.planned_qty), 0))
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


def _aps_build_batch_qty_rows(total_qty: int, lot_size_snapshot: int) -> tuple[int, List[tuple[int, int]]]:
    """ロット数と [(lot_index, qty), ...]（qty>0 のみ）。"""
    production_lot_size = max(1, int(math.ceil(total_qty / float(lot_size_snapshot))))
    batch_qtys: List[tuple[int, int]] = []
    for i in range(1, production_lot_size + 1):
        if i < production_lot_size:
            batch_qtys.append((i, lot_size_snapshot))
        else:
            remain = total_qty - lot_size_snapshot * (production_lot_size - 1)
            batch_qtys.append((i, max(0, int(remain))))
    batch_qtys = [(i, q) for i, q in batch_qtys if q > 0]
    return production_lot_size, batch_qtys


def _scale_slice_rows_to_instruction_total(
    slices: List[ScheduleSliceAllocation],
    slice_total: int,
    target_total: int,
) -> List[tuple[ScheduleSliceAllocation, int]]:
    """
    成型スライス合計 slice_total を、切断指示用の計画本数 target_total に比例拡大（切断前計画）。
    成型実績でスライスが「残数」のみでも、instruction_plans は計画一覧の合計本数を表す。
    """
    if not slices:
        return []
    if slice_total <= 0 or target_total <= 0:
        return [(s, int(s.planned_qty or 0)) for s in slices]
    if slice_total == target_total:
        return [(s, int(s.planned_qty or 0)) for s in slices]
    out: List[tuple[ScheduleSliceAllocation, int]] = []
    acc = 0
    for idx in range(len(slices) - 1):
        s = slices[idx]
        q = int(s.planned_qty or 0)
        sq = int(math.floor(target_total * q / slice_total))
        out.append((s, sq))
        acc += sq
    last_s = slices[-1]
    out.append((last_s, max(0, target_total - acc)))
    return out


def _walk_slice_pairs_to_batches(
    slice_pairs: List[tuple[ScheduleSliceAllocation, int]],
    batch_qtys: List[tuple[int, int]],
) -> List[Dict[str, Any]]:
    """スライス（数量付き）をロットへ割当、開始・終了時刻を付与。"""
    batches: List[Dict[str, Any]] = []
    if not batch_qtys:
        return batches
    batch_idx = 0
    batch_accum_qty = 0
    batch_start_dt: Optional[datetime] = None
    batch_end_dt: Optional[datetime] = None

    for s, slice_total_qty in slice_pairs:
        if slice_total_qty <= 0:
            continue
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
                batch_idx += 1
                batch_accum_qty = 0
                if batch_idx >= len(batch_qtys):
                    break
                batch_start_dt = None
                batch_end_dt = None
                continue

            portion_qty = min(slice_remaining_qty, batch_need)
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
    return batches


# instruction_plans へ書き込むのは「成型」(KT04) の設備に限る（get_lines の processCd 判定と同一）。aps_batch_plans は全工程で更新する。
_APS_INSTRUCTION_PLANS_SYNC_PROCESS_CD = "KT04"
# 生産進捗：True のとき schedule_details.actual_qty をロット順に割当て、残数を翌日以降に再按分し日別ガントと整列する。
_PRODUCTION_PROGRESS_USE_FORMING_ACTUAL = True


async def _machine_matches_process_cd(
    db: AsyncSession,
    machine: Machine,
    process_cd: str,
) -> bool:
    """設備の machine_type が指定工程の名称または工程CDと一致するか（/lines?processCd= と同じ）。"""
    pc = (process_cd or "").strip()
    if not pc:
        return False
    proc_result = await db.execute(select(Process).where(Process.process_cd == pc))
    proc = proc_result.scalar_one_or_none()
    if proc is None:
        return False
    pn = (proc.process_name or "").strip()
    pcc = (proc.process_cd or "").strip()
    mt = (machine.machine_type or "").strip()
    if not mt:
        return False
    if pn and mt == pn:
        return True
    if pcc and mt == pcc:
        return True
    return False


async def _sync_instruction_plans_from_aps_schedule(db: AsyncSession, ps: ProductionSchedule) -> None:
    """
    APS の工単スケジュールをロット（lot_number）に展開し、instruction_plans へ同期する。

    実装方針:
    - instruction_plans は工程 KT04（成型）設備の計画のみ。aps_batch_plans は設備の工程に関わらず更新する。
    - aps_batch_plans: 排産エンジンのスライス（成型実績を考慮した残数）に基づく。
    - instruction_plans: 切断工程指示前の「計画一覧」＝ planned_process_qty + prev_month_carryover を本数基準とし、
      成型実績で縮んだスライスは時間軸の形を保ったまま比例拡大してロット割当（実績本数は参照しない）。
    - cutting_management に既に存在する management_code のロットは instruction 同期を skip。
    """
    # schedule は APS ロット単位に分解できる前提
    if not ps.product_cd:
        return

    machine = await db.get(Machine, ps.line_id)
    if machine is None:
        return
    sync_instruction_plans = await _machine_matches_process_cd(
        db, machine, _APS_INSTRUCTION_PLANS_SYNC_PROCESS_CD
    )

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

    slice_total = sum(int(s.planned_qty or 0) for s in slices)
    if slice_total <= 0:
        return

    full_plan_total = int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0)
    if full_plan_total <= 0:
        full_plan_total = slice_total

    # 生産月/ライン/製品情報（管理コードと整合させるため機械側情報を優先）
    # instruction_plans の management_code トリガーは RIGHT(production_line,2) を使うため、
    # instruction_plans 側に保存する production_line は「設備名」に揃える
    production_line = (machine.machine_name or '').strip() or (machine.machine_cd or str(machine.id))
    production_name = ps.item_name or ""
    production_product_cd = (ps.product_cd or "").strip()

    # cutting/scrap/material 情報（products -> materials）
    # APS schedule は products/material のキー（product_cd/material_cd）を持つ前提で同期する。
    cutting_length = None
    chamfering_length = None
    developed_length = None
    scrap_length = None
    take_count = None
    material_name = None
    material_manufacturer = None
    standard_specification = None

    prod = None
    if production_product_cd:
        prod_res = await db.execute(select(Product).where(Product.product_cd == production_product_cd))
        prod = prod_res.scalars().first()

    if prod is not None:
        cutting_length = float(prod.cut_length) if prod.cut_length is not None else None
        chamfering_length = float(prod.chamfer_length) if prod.chamfer_length is not None else None
        developed_length = float(prod.developed_length) if prod.developed_length is not None else None
        scrap_length = float(prod.scrap_length) if prod.scrap_length is not None else None
        take_count = int(prod.take_count) if prod.take_count is not None else None

        if prod.material_cd:
            mat_res = await db.execute(select(Material).where(Material.material_cd == prod.material_cd))
            mat = mat_res.scalars().first()
            if mat is not None:
                material_name = mat.material_name
                supplier_cd = (mat.supplier_cd or "").strip() if mat.supplier_cd else ""
                if supplier_cd:
                    sup_res = await db.execute(select(Supplier).where(Supplier.supplier_cd == supplier_cd))
                    sup = sup_res.scalars().first()
                    material_manufacturer = (sup.supplier_name or "").strip() if sup is not None else supplier_cd
                else:
                    material_manufacturer = None
                standard_specification = mat.standard_spec

    # lot_size：スケジュール側のスナップショットが無い場合は products から取得
    lot_size_snapshot = int(getattr(ps, "lot_size_snapshot", 0) or 0)
    if lot_size_snapshot <= 0:
        pr_res = await db.execute(select(Product.lot_size).where(Product.product_cd == production_product_cd))
        lot_size_snapshot = int(pr_res.scalar() or 0)
    if lot_size_snapshot <= 0:
        return

    # aps_batch_plans：エンジンスライス（成型実績反映後の残数）
    production_lot_size_engine, batch_qtys_engine = _aps_build_batch_qty_rows(slice_total, lot_size_snapshot)
    if not batch_qtys_engine:
        return
    slice_pairs_engine = [(s, int(s.planned_qty or 0)) for s in slices]
    batches_engine = _walk_slice_pairs_to_batches(slice_pairs_engine, batch_qtys_engine)
    if not batches_engine:
        return

    # instruction_plans：計画一覧合計（切断前。スライスを full_plan_total へ比例拡大してロット・時刻を算出）
    instruction_planned_qty = full_plan_total
    production_lot_size_ip, batch_qtys_ip = _aps_build_batch_qty_rows(full_plan_total, lot_size_snapshot)
    slice_pairs_ip = _scale_slice_rows_to_instruction_total(slices, slice_total, full_plan_total)
    batches_instruction = (
        _walk_slice_pairs_to_batches(slice_pairs_ip, batch_qtys_ip)
        if sync_instruction_plans and batch_qtys_ip
        else []
    )

    # 生産月はスライスの最初日基準
    min_work_date = min(s.work_date for s in slices)
    production_month = date(min_work_date.year, min_work_date.month, 1)

    # ① aps_batch_plans のみ（成型スライス実値）
    for b in batches_engine:
        lot_number = b["lot_number"]
        batch_planned_qty = int(b["planned_quantity"])
        start_dt = b["start_date"]
        end_dt = b["end_date"]

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
                planned_quantity=batch_planned_qty,
                original_planned_quantity=batch_planned_qty,
                production_lot_size=production_lot_size_engine,
                lot_number=lot_number,
                start_date=start_dt,
                end_date=end_dt,
            )
            db.add(new_row)
            await db.flush()
            await db.refresh(new_row)
        else:
            old_pq = int(existing.planned_quantity or 0)
            new_pq = int(batch_planned_qty or 0)
            oq = getattr(existing, "original_planned_quantity", None)
            if oq is None:
                existing.original_planned_quantity = max(old_pq, new_pq)
            else:
                existing.original_planned_quantity = max(int(oq or 0), new_pq)
            existing.production_month = production_month
            existing.production_line = str(production_line)
            existing.priority_order = ps.order_no
            existing.product_cd = production_product_cd
            existing.product_name = production_name
            existing.planned_quantity = new_pq
            existing.production_lot_size = production_lot_size_engine
            existing.start_date = start_dt
            existing.end_date = end_dt
            await db.flush()

    await db.flush()

    if not sync_instruction_plans or not batches_instruction:
        return

    bp_map_res = await db.execute(
        select(ApsBatchPlan).where(ApsBatchPlan.aps_schedule_id == ps.id)
    )
    plan_id_by_lot: dict[str, int] = {}
    for bp in bp_map_res.scalars().all():
        plan_id_by_lot[str(bp.lot_number)] = int(bp.id)

    # ② instruction_plans（切断工程用。ロットが APS 側に無い場合は aps_batch_plan_id は NULL）
    for b in batches_instruction:
        lot_number = b["lot_number"]
        batch_planned_qty = int(b["planned_quantity"])
        start_dt = b["start_date"]
        end_dt = b["end_date"]
        batch_plan_id = plan_id_by_lot.get(lot_number)

        mc = _instruction_management_code(
            production_month=production_month,
            production_line=str(production_line),
            product_cd=production_product_cd,
            priority_order=ps.order_no,
            production_lot_size=production_lot_size_ip,
            lot_number=lot_number,
        )
        cut_q = await db.execute(text("SELECT id FROM cutting_management WHERE management_code = :mc LIMIT 1"), {"mc": mc})
        if cut_q.scalar() is not None:
            continue

        found = None
        if batch_plan_id is not None:
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
                    "planned_quantity=:instruction_planned_qty, actual_production_quantity=:batch_planned_qty, "
                    "take_count=:take_count, "
                    "cutting_length=:cutting_length, chamfering_length=:chamfering_length, developed_length=:developed_length, scrap_length=:scrap_length, "
                    "material_name=:material_name, material_manufacturer=:material_manufacturer, standard_specification=:standard_specification, "
                    "start_date=:start_date, end_date=:end_date, "
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
                    "instruction_planned_qty": instruction_planned_qty,
                    "batch_planned_qty": batch_planned_qty,
                    "take_count": take_count,
                    "cutting_length": cutting_length,
                    "chamfering_length": chamfering_length,
                    "developed_length": developed_length,
                    "scrap_length": scrap_length,
                    "material_name": material_name,
                    "material_manufacturer": material_manufacturer,
                    "standard_specification": standard_specification,
                    "start_date": start_dt,
                    "end_date": end_dt,
                    "production_lot_size": production_lot_size_ip,
                    "lot_number": lot_number,
                    "aps_batch_plan_id": batch_plan_id,
                },
            )
        else:
            ins_conf = await db.execute(
                text(
                    "SELECT id, aps_batch_plan_id FROM instruction_plans WHERE management_code = :mc LIMIT 1"
                ),
                {"mc": mc},
            )
            conf_row = ins_conf.mappings().first()
            if conf_row and conf_row.get("aps_batch_plan_id"):
                ins_id = conf_row.get("id")
                await db.execute(
                    text(
                        "UPDATE instruction_plans SET "
                        "production_month=:production_month, production_line=:production_line, "
                        "priority_order=:priority_order, product_cd=:product_cd, product_name=:product_name, "
                        "planned_quantity=:instruction_planned_qty, actual_production_quantity=:batch_planned_qty, "
                        "take_count=:take_count, "
                        "cutting_length=:cutting_length, chamfering_length=:chamfering_length, developed_length=:developed_length, scrap_length=:scrap_length, "
                        "material_name=:material_name, material_manufacturer=:material_manufacturer, standard_specification=:standard_specification, "
                        "start_date=:start_date, end_date=:end_date, "
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
                        "instruction_planned_qty": instruction_planned_qty,
                        "batch_planned_qty": batch_planned_qty,
                        "take_count": take_count,
                        "cutting_length": cutting_length,
                        "chamfering_length": chamfering_length,
                        "developed_length": developed_length,
                        "scrap_length": scrap_length,
                        "material_name": material_name,
                        "material_manufacturer": material_manufacturer,
                        "standard_specification": standard_specification,
                        "start_date": start_dt,
                        "end_date": end_dt,
                        "production_lot_size": production_lot_size_ip,
                        "lot_number": lot_number,
                        "aps_batch_plan_id": batch_plan_id,
                    },
                )
                continue
            if conf_row and not conf_row.get("aps_batch_plan_id"):
                continue

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
                      :instruction_planned_qty, :start_date, :end_date, :production_lot_size, :lot_number,
                      0, 0, 0,
                      0, 0,
                      :batch_planned_qty, :take_count,
                      :cutting_length, :chamfering_length, :developed_length, :scrap_length,
                      :material_name, :material_manufacturer, :standard_specification,
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
                    "instruction_planned_qty": instruction_planned_qty,
                    "start_date": start_dt,
                    "end_date": end_dt,
                    "production_lot_size": production_lot_size_ip,
                    "lot_number": lot_number,
                    "batch_planned_qty": batch_planned_qty,
                    "take_count": take_count,
                    "cutting_length": cutting_length,
                    "chamfering_length": chamfering_length,
                    "developed_length": developed_length,
                    "scrap_length": scrap_length,
                    "material_name": material_name,
                    "material_manufacturer": material_manufacturer,
                    "standard_specification": standard_specification,
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
