"""検査員別所定稼働時間 API"""
from datetime import date, time
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.inspection_inspector_work_schedule import (
    DEFAULT_INSPECTION_STANDARD_HOURS,
    RULE_KIND_LABELS,
    WEEKDAY_LABELS,
    resolve_scheduled_hours,
    schedule_row_to_dict,
)
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_master_operation
from app.modules.master.models import InspectionInspectorWorkSchedule

router = APIRouter()


class InspectorWorkScheduleCreate(BaseModel):
    inspector_user_id: int = Field(..., ge=1)
    rule_kind: str = Field(..., description="date=指定日期 | time=指定时间（曜日別）")
    schedule_date: Optional[str] = Field(None, description="YYYY-MM-DD（rule_kind=date）")
    weekday: Optional[int] = Field(None, ge=0, le=6, description="0=月..6=日（rule_kind=time）")
    work_start_time: Optional[str] = Field(None, description="HH:MM")
    work_end_time: Optional[str] = Field(None, description="HH:MM")
    scheduled_hours: Optional[float] = Field(None, gt=0, le=24)
    note: Optional[str] = None


class InspectorWorkScheduleBatchCreate(BaseModel):
    inspector_user_ids: List[int] = Field(..., min_length=1, description="検査員 users.id 一覧")
    rule_kind: str = Field(..., description="date=指定日期 | time=指定时间（曜日別）")
    schedule_date: Optional[str] = Field(None, description="YYYY-MM-DD（rule_kind=date）")
    weekday: Optional[int] = Field(None, ge=0, le=6, description="0=月..6=日（rule_kind=time）")
    work_start_time: Optional[str] = Field(None, description="HH:MM")
    work_end_time: Optional[str] = Field(None, description="HH:MM")
    scheduled_hours: Optional[float] = Field(None, gt=0, le=24)
    note: Optional[str] = None


class InspectorWorkScheduleUpdate(BaseModel):
    work_start_time: Optional[str] = Field(None, description="HH:MM")
    work_end_time: Optional[str] = Field(None, description="HH:MM")
    scheduled_hours: Optional[float] = Field(None, gt=0, le=24)
    note: Optional[str] = None


def _parse_ymd(raw: Optional[str]) -> Optional[date]:
    if raw is None or not str(raw).strip():
        return None
    try:
        return date.fromisoformat(str(raw).strip()[:10])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="schedule_date が不正です") from exc


def _parse_hm(raw: Optional[str]) -> Optional[time]:
    if raw is None or not str(raw).strip():
        return None
    text = str(raw).strip()[:5]
    try:
        parts = text.split(":")
        if len(parts) != 2:
            raise ValueError("invalid")
        hour = int(parts[0])
        minute = int(parts[1])
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("invalid")
        return time(hour=hour, minute=minute)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="時刻は HH:MM 形式で指定してください") from exc


def _normalize_rule_kind(rule_kind: str) -> str:
    kind = (rule_kind or "").strip().lower()
    if kind == "weekday":
        return "time"
    if kind in ("date", "time"):
        return kind
    raise HTTPException(status_code=400, detail="rule_kind は date（指定日期）または time（指定时间）です")


def _validate_rule_fields(*, rule_kind: str, schedule_date: Optional[date], weekday: Optional[int]) -> None:
    if rule_kind == "date":
        if schedule_date is None:
            raise HTTPException(status_code=400, detail="指定日期には日付が必要です")
        if weekday is not None:
            raise HTTPException(status_code=400, detail="指定日期では曜日を指定できません")
        return
    if rule_kind == "time":
        if weekday is None:
            raise HTTPException(status_code=400, detail="指定时间には曜日が必要です")
        if schedule_date is not None:
            raise HTTPException(status_code=400, detail="指定时间では日付を指定できません")
        return
    raise HTTPException(status_code=400, detail="rule_kind が不正です")


def _resolve_hours_for_write(
    *,
    work_start_time: Optional[time],
    work_end_time: Optional[time],
    scheduled_hours: Optional[float],
) -> float:
    if work_start_time is None or work_end_time is None:
        raise HTTPException(status_code=400, detail="開始・終了時刻を指定してください")
    hours = resolve_scheduled_hours(
        scheduled_hours=scheduled_hours,
        work_start_time=work_start_time,
        work_end_time=work_end_time,
    )
    if hours <= 0:
        raise HTTPException(status_code=400, detail="所定時間が 0 以下です")
    return hours


async def _inspector_name_map(db: AsyncSession, user_ids: List[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    res = await db.execute(select(User.id, User.full_name, User.username).where(User.id.in_(user_ids)))
    out: dict[int, str] = {}
    for uid, full_name, username in res.all():
        label = (full_name or username or f"ID:{uid}").strip()
        out[int(uid)] = label
    return out


def _parse_rule_payload(
    *,
    rule_kind: str,
    schedule_date: Optional[str],
    weekday: Optional[int],
    work_start_time: Optional[str],
    work_end_time: Optional[str],
    scheduled_hours: Optional[float],
) -> tuple[date | None, int | None, time, time, float]:
    kind = _normalize_rule_kind(rule_kind)
    sched_d = _parse_ymd(schedule_date) if kind == "date" else None
    wd = int(weekday) if kind == "time" and weekday is not None else None
    _validate_rule_fields(rule_kind=kind, schedule_date=sched_d, weekday=wd)
    start_t = _parse_hm(work_start_time)
    end_t = _parse_hm(work_end_time)
    hours = _resolve_hours_for_write(
        work_start_time=start_t,
        work_end_time=end_t,
        scheduled_hours=scheduled_hours,
    )
    return sched_d, wd, start_t, end_t, hours


async def _rule_exists_for_inspector(
    db: AsyncSession,
    *,
    inspector_user_id: int,
    schedule_date: Optional[date],
    weekday: Optional[int],
) -> bool:
    q = select(InspectionInspectorWorkSchedule.id).where(
        InspectionInspectorWorkSchedule.inspector_user_id == int(inspector_user_id)
    )
    if schedule_date is not None:
        q = q.where(InspectionInspectorWorkSchedule.schedule_date == schedule_date)
    else:
        q = q.where(
            InspectionInspectorWorkSchedule.schedule_date.is_(None),
            InspectionInspectorWorkSchedule.weekday == int(weekday),
        )
    return (await db.execute(q)).scalar_one_or_none() is not None


@router.get("/weekdays")
async def get_weekday_options(
    current_user: User = Depends(verify_token_and_get_user),
):
    return [{"value": k, "label": v} for k, v in WEEKDAY_LABELS.items()]


@router.get("/rule-kinds")
async def get_rule_kind_options(
    current_user: User = Depends(verify_token_and_get_user),
):
    return [{"value": k, "label": v} for k, v in RULE_KIND_LABELS.items()]


@router.get("/defaults")
async def get_defaults(
    current_user: User = Depends(verify_token_and_get_user),
):
    return {
        "success": True,
        "data": {
            "default_scheduled_hours": DEFAULT_INSPECTION_STANDARD_HOURS,
            "default_work_start_time": "08:00",
            "default_work_end_time": "15:36",
            "priority": ["指定日期", "指定时间", f"未設定時 {DEFAULT_INSPECTION_STANDARD_HOURS}h"],
        },
    }


@router.get("")
async def list_inspector_work_schedules(
    inspector_user_id: Optional[int] = Query(None, ge=1),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD（指定日期ルールの絞込）"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(InspectionInspectorWorkSchedule).order_by(
        InspectionInspectorWorkSchedule.inspector_user_id,
        InspectionInspectorWorkSchedule.schedule_date.is_(None),
        InspectionInspectorWorkSchedule.weekday,
        InspectionInspectorWorkSchedule.schedule_date,
    )
    if inspector_user_id is not None:
        q = q.where(InspectionInspectorWorkSchedule.inspector_user_id == int(inspector_user_id))
    start_d = _parse_ymd(start_date) if start_date else None
    end_d = _parse_ymd(end_date) if end_date else None
    if start_d and end_d and start_d > end_d:
        raise HTTPException(status_code=400, detail="start_date は end_date 以前である必要があります")
    if start_d is not None or end_d is not None:
        if start_d is None or end_d is None:
            raise HTTPException(status_code=400, detail="start_date / end_date を両方指定してください")
        q = q.where(
            (InspectionInspectorWorkSchedule.schedule_date.is_(None))
            | (
                (InspectionInspectorWorkSchedule.schedule_date >= start_d)
                & (InspectionInspectorWorkSchedule.schedule_date <= end_d)
            )
        )

    res = await db.execute(q)
    rows = res.scalars().all()
    name_map = await _inspector_name_map(db, list({int(r.inspector_user_id) for r in rows}))
    items = [
        schedule_row_to_dict(r, inspector_name=name_map.get(int(r.inspector_user_id)))
        for r in rows
    ]
    return {"success": True, "data": {"items": items, "total": len(items)}}


@router.post("/batch")
async def batch_create_inspector_work_schedules(
    body: InspectorWorkScheduleBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("create")),
):
    inspector_ids = list(dict.fromkeys(int(uid) for uid in body.inspector_user_ids if int(uid) > 0))
    if not inspector_ids:
        raise HTTPException(status_code=400, detail="検査員を1名以上指定してください")

    sched_d, weekday, start_t, end_t, hours = _parse_rule_payload(
        rule_kind=body.rule_kind,
        schedule_date=body.schedule_date,
        weekday=body.weekday,
        work_start_time=body.work_start_time,
        work_end_time=body.work_end_time,
        scheduled_hours=body.scheduled_hours,
    )
    note = (body.note or "").strip() or None

    valid_ids_res = await db.execute(select(User.id).where(User.id.in_(inspector_ids)))
    valid_ids = {int(row[0]) for row in valid_ids_res.all()}
    failed = len(inspector_ids) - len(valid_ids)

    created = 0
    skipped = 0
    skipped_user_ids: List[int] = []
    for uid in inspector_ids:
        if uid not in valid_ids:
            continue
        if await _rule_exists_for_inspector(
            db,
            inspector_user_id=uid,
            schedule_date=sched_d,
            weekday=weekday,
        ):
            skipped += 1
            skipped_user_ids.append(uid)
            continue
        db.add(
            InspectionInspectorWorkSchedule(
                inspector_user_id=uid,
                schedule_date=sched_d,
                weekday=weekday,
                scheduled_hours=Decimal(str(round(hours, 2))),
                work_start_time=start_t,
                work_end_time=end_t,
                note=note,
            )
        )
        created += 1

    if created > 0:
        await db.commit()
    else:
        await db.rollback()

    skipped_names: List[str] = []
    if skipped_user_ids:
        name_map = await _inspector_name_map(db, skipped_user_ids)
        skipped_names = [name_map.get(uid, f"ID:{uid}") for uid in skipped_user_ids]

    return {
        "success": True,
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "skipped_inspector_names": skipped_names,
    }


@router.post("")
async def create_inspector_work_schedule(
    body: InspectorWorkScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("create")),
):
    sched_d, weekday, start_t, end_t, hours = _parse_rule_payload(
        rule_kind=body.rule_kind,
        schedule_date=body.schedule_date,
        weekday=body.weekday,
        work_start_time=body.work_start_time,
        work_end_time=body.work_end_time,
        scheduled_hours=body.scheduled_hours,
    )

    user_res = await db.execute(select(User.id).where(User.id == int(body.inspector_user_id)))
    if user_res.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="検査員ユーザーが存在しません")

    if await _rule_exists_for_inspector(
        db,
        inspector_user_id=int(body.inspector_user_id),
        schedule_date=sched_d,
        weekday=weekday,
    ):
        raise HTTPException(status_code=409, detail="同一検査員・同一日/曜日のルールが既に存在します")

    row = InspectionInspectorWorkSchedule(
        inspector_user_id=int(body.inspector_user_id),
        schedule_date=sched_d,
        weekday=weekday,
        scheduled_hours=Decimal(str(round(hours, 2))),
        work_start_time=start_t,
        work_end_time=end_t,
        note=(body.note or "").strip() or None,
    )
    db.add(row)
    try:
        await db.commit()
        await db.refresh(row)
    except Exception as exc:
        await db.rollback()
        msg = str(exc).lower()
        if "duplicate" in msg or "uq_insp" in msg:
            raise HTTPException(status_code=409, detail="同一検査員・同一日/曜日のルールが既に存在します") from exc
        raise HTTPException(status_code=500, detail="登録に失敗しました") from exc

    name_map = await _inspector_name_map(db, [int(row.inspector_user_id)])
    return {
        "success": True,
        "data": schedule_row_to_dict(row, inspector_name=name_map.get(int(row.inspector_user_id))),
    }


@router.put("/{entry_id}")
async def update_inspector_work_schedule(
    entry_id: int,
    body: InspectorWorkScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    res = await db.execute(
        select(InspectionInspectorWorkSchedule).where(InspectionInspectorWorkSchedule.id == int(entry_id))
    )
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="ルールが見つかりません")

    start_t = _parse_hm(body.work_start_time) if body.work_start_time is not None else row.work_start_time
    end_t = _parse_hm(body.work_end_time) if body.work_end_time is not None else row.work_end_time
    if body.work_start_time is not None or body.work_end_time is not None:
        hours = _resolve_hours_for_write(
            work_start_time=start_t,
            work_end_time=end_t,
            scheduled_hours=float(body.scheduled_hours) if body.scheduled_hours is not None else float(row.scheduled_hours),
        )
        row.work_start_time = start_t
        row.work_end_time = end_t
        row.scheduled_hours = Decimal(str(round(hours, 2)))
    elif body.scheduled_hours is not None:
        row.scheduled_hours = Decimal(str(round(body.scheduled_hours, 2)))

    if body.note is not None:
        row.note = body.note.strip() or None
    await db.commit()
    await db.refresh(row)
    name_map = await _inspector_name_map(db, [int(row.inspector_user_id)])
    return {
        "success": True,
        "data": schedule_row_to_dict(row, inspector_name=name_map.get(int(row.inspector_user_id))),
    }


@router.delete("/{entry_id}")
async def delete_inspector_work_schedule(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("delete")),
):
    res = await db.execute(
        select(InspectionInspectorWorkSchedule).where(InspectionInspectorWorkSchedule.id == int(entry_id))
    )
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="ルールが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True}
