"""
APS（先進的計画・スケジューリング）APIエンドポイント
産線管理、稼働カレンダー、工単 CRUD、排産エンジン、スケジューリンググリッド
"""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

from app.modules.aps.models import (
    ProductionLine,
    LineCapacity,
    ProductionSchedule,
    ScheduleDetail,
)
from app.modules.aps.schemas import (
    ProductionLineOut,
    LineCapacityOut,
    LineCapacityBatchBody,
    ScheduleCreateBody,
    ScheduleUpdateBody,
    ScheduleOut,
    ScheduleGridRow,
    LineGridBlock,
    SchedulingGridResponse,
)
from app.modules.aps.engine import run_engine

router = APIRouter()


def _dec(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


# ═══════════════════ Production Lines ═══════════════════

@router.get("/lines", response_model=List[ProductionLineOut])
async def get_lines(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(
        select(ProductionLine)
        .where(ProductionLine.is_active == True)
        .order_by(ProductionLine.line_code)
    )
    return [
        ProductionLineOut(
            id=r.id,
            line_code=r.line_code,
            default_work_hours=_dec(r.default_work_hours),
            is_active=bool(r.is_active),
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
    line = ProductionLine(
        line_code=line_code.strip(),
        default_work_hours=Decimal(str(default_work_hours)),
    )
    db.add(line)
    await db.flush()
    await db.refresh(line)
    return {"success": True, "data": {"id": line.id, "line_code": line.line_code}}


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
    result = await db.execute(q)
    return [_schedule_to_out(r) for r in result.scalars().all()]


@router.post("/schedules", response_model=ScheduleOut)
async def create_schedule(
    body: ScheduleCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = ProductionSchedule(
        line_id=body.line_id,
        order_no=body.order_no,
        order_id=body.order_id,
        item_name=body.item_name,
        material_shortage=body.material_shortage,
        lot_qty=body.lot_qty,
        planned_process_qty=body.planned_process_qty,
        prev_month_carryover=body.prev_month_carryover,
        due_date=body.due_date,
        material_date=body.material_date,
        setup_time=body.setup_time,
        efficiency=Decimal(str(body.efficiency)),
        daily_capacity=body.daily_capacity,
        start_date=body.start_date,
        status="PLANNING",
    )
    db.add(ps)
    await db.flush()
    await db.refresh(ps)

    if body.run_immediately:
        ps = await run_engine(db, ps.id, override_start_date=body.start_date)
        await db.flush()

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
        "line_id", "order_no", "order_id", "item_name", "material_shortage",
        "lot_qty", "planned_process_qty", "prev_month_carryover",
        "due_date", "material_date", "setup_time", "daily_capacity", "start_date",
    ):
        val = getattr(body, field, None)
        if val is not None:
            setattr(ps, field, val)
    if body.efficiency is not None:
        ps.efficiency = Decimal(str(body.efficiency))

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

    # 産線取得
    line_q = select(ProductionLine).where(ProductionLine.is_active == True)
    if lineId is not None:
        line_q = line_q.where(ProductionLine.id == lineId)
    line_q = line_q.order_by(ProductionLine.line_code)
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
                planned_process_qty=int(ps.planned_process_qty),
                prev_month_carryover=int(ps.prev_month_carryover or 0),
                due_date=ps.due_date.isoformat() if ps.due_date else None,
                material_date=ps.material_date.isoformat() if ps.material_date else None,
                setup_time=int(ps.setup_time or 0),
                efficiency=_dec(ps.efficiency),
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
            line_code=line.line_code,
            default_work_hours=_dec(line.default_work_hours),
            calendar=calendar_map,
            rows=rows,
            daily_totals=dict(daily_totals),
            sum_planned_process_qty=sum_planned_process,
            sum_planned_output_qty=sum_planned_output,
            completion_rate=block_rate,
        ))

    return SchedulingGridResponse(dates=dates_list, blocks=blocks)


# ═══════════════════ Run All (全産線再計算) ═══════════════════

@router.post("/run-all")
async def run_all_schedules(
    lineId: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
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


# ═══════════════════ helpers ═══════════════════

def _schedule_to_out(ps: ProductionSchedule) -> ScheduleOut:
    return ScheduleOut(
        id=ps.id,
        line_id=ps.line_id,
        order_no=ps.order_no,
        order_id=ps.order_id,
        item_name=ps.item_name,
        material_shortage=bool(ps.material_shortage),
        lot_qty=int(ps.lot_qty or 0),
        planned_process_qty=int(ps.planned_process_qty),
        prev_month_carryover=int(ps.prev_month_carryover or 0),
        due_date=ps.due_date,
        material_date=ps.material_date,
        setup_time=int(ps.setup_time or 0),
        efficiency=_dec(ps.efficiency),
        daily_capacity=int(ps.daily_capacity),
        planned_output_qty=int(ps.planned_output_qty or 0),
        start_date=ps.start_date,
        end_date=ps.end_date,
        completion_rate=_dec(ps.completion_rate) if ps.completion_rate is not None else None,
        status=ps.status or "PLANNING",
    )
