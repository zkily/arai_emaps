"""会社共通稼働カレンダー API"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.company_work_calendar import (
    DAY_TYPE_LABELS,
    VALID_DAY_TYPES,
    calendar_row_to_dict,
    count_scheduled_workdays,
    default_is_scheduled_for_day_type,
    infer_day_type,
    load_company_calendar_sets,
    parse_date_csv,
)
from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import CompanyWorkCalendar

router = APIRouter()


class CompanyWorkCalendarCreate(BaseModel):
    calendar_date: str = Field(..., description="YYYY-MM-DD")
    day_type: Optional[str] = None
    is_scheduled: Optional[bool] = None
    name: Optional[str] = None
    note: Optional[str] = None


class CompanyWorkCalendarUpdate(BaseModel):
    day_type: Optional[str] = None
    is_scheduled: Optional[bool] = None
    name: Optional[str] = None
    note: Optional[str] = None


class CompanyWorkCalendarBatchCreate(BaseModel):
    dates: List[str] = Field(..., min_length=1)
    day_type: str = "company_holiday"
    is_scheduled: Optional[bool] = None
    name: Optional[str] = None
    note: Optional[str] = None


def _parse_ymd(raw: str) -> date:
    try:
        return date.fromisoformat(str(raw).strip()[:10])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="calendar_date が不正です") from exc


@router.get("/day-types")
async def get_day_types(
    current_user: User = Depends(verify_token_and_get_user),
):
    return [{"value": k, "label": v} for k, v in DAY_TYPE_LABELS.items()]


@router.get("")
async def list_company_work_calendar(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    start_d = _parse_ymd(start_date)
    end_d = _parse_ymd(end_date)
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="start_date は end_date 以前である必要があります")

    q = (
        select(CompanyWorkCalendar)
        .where(
            CompanyWorkCalendar.calendar_date >= start_d,
            CompanyWorkCalendar.calendar_date <= end_d,
        )
        .order_by(CompanyWorkCalendar.calendar_date)
    )
    res = await db.execute(q)
    rows = res.scalars().all()
    scheduled, off = await load_company_calendar_sets(db, start_d, end_d)
    scheduled_count = count_scheduled_workdays(
        start_d,
        end_d,
        company_scheduled=scheduled,
        company_off=off,
        extra_workdays=set(),
        extra_holidays=set(),
    )
    total_days = (end_d - start_d).days + 1
    return {
        "success": True,
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "items": [calendar_row_to_dict(r) for r in rows],
            "scheduled_workday_count": scheduled_count,
            "total_days": total_days,
        },
    }


@router.get("/resolve")
async def resolve_workdays(
    start_date: str = Query(...),
    end_date: str = Query(...),
    extra_workdays: Optional[str] = Query(None),
    extra_holidays: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """期間内の通常稼働日セット（分析画面等向け）。"""
    start_d = _parse_ymd(start_date)
    end_d = _parse_ymd(end_date)
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="start_date は end_date 以前である必要があります")
    company_scheduled, company_off = await load_company_calendar_sets(db, start_d, end_d)
    extra_wd = parse_date_csv(extra_workdays)
    extra_hol = parse_date_csv(extra_holidays)
    return {
        "success": True,
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "company_extra_workdays": sorted(company_scheduled),
            "company_holidays": sorted(company_off),
            "scheduled_workday_count": count_scheduled_workdays(
                start_d,
                end_d,
                company_scheduled=company_scheduled,
                company_off=company_off,
                extra_workdays=extra_wd,
                extra_holidays=extra_hol,
            ),
        },
    }


@router.post("")
async def create_company_work_calendar_entry(
    body: CompanyWorkCalendarCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    cal_date = _parse_ymd(body.calendar_date)
    q = select(CompanyWorkCalendar).where(CompanyWorkCalendar.calendar_date == cal_date)
    if (await db.execute(q)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同じ日付は既に登録されています")

    day_type = (body.day_type or "").strip() or infer_day_type(
        cal_date, body.is_scheduled if body.is_scheduled is not None else cal_date.weekday() < 5
    )
    if day_type not in VALID_DAY_TYPES:
        raise HTTPException(status_code=400, detail=f"day_type が不正です: {day_type}")

    is_scheduled = (
        body.is_scheduled
        if body.is_scheduled is not None
        else default_is_scheduled_for_day_type(day_type, cal_date)
    )
    row = CompanyWorkCalendar(
        calendar_date=cal_date,
        day_type=day_type,
        is_scheduled=bool(is_scheduled),
        name=body.name,
        note=body.note,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": calendar_row_to_dict(row)}


@router.post("/batch")
async def batch_create_company_work_calendar(
    body: CompanyWorkCalendarBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    day_type = (body.day_type or "").strip()
    if day_type not in VALID_DAY_TYPES:
        raise HTTPException(status_code=400, detail=f"day_type が不正です: {day_type}")

    created = 0
    skipped = 0
    for raw in body.dates:
        cal_date = _parse_ymd(raw)
        q = select(CompanyWorkCalendar).where(CompanyWorkCalendar.calendar_date == cal_date)
        if (await db.execute(q)).scalar_one_or_none():
            skipped += 1
            continue
        is_scheduled = (
            body.is_scheduled
            if body.is_scheduled is not None
            else default_is_scheduled_for_day_type(day_type, cal_date)
        )
        db.add(
            CompanyWorkCalendar(
                calendar_date=cal_date,
                day_type=day_type,
                is_scheduled=bool(is_scheduled),
                name=body.name,
                note=body.note,
            )
        )
        created += 1
    await db.commit()
    return {"success": True, "created": created, "skipped": skipped}


@router.put("/{entry_id}")
async def update_company_work_calendar_entry(
    entry_id: int,
    body: CompanyWorkCalendarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(CompanyWorkCalendar).where(CompanyWorkCalendar.id == entry_id)
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="エントリが見つかりません")

    if body.day_type is not None:
        if body.day_type not in VALID_DAY_TYPES:
            raise HTTPException(status_code=400, detail=f"day_type が不正です: {body.day_type}")
        row.day_type = body.day_type
    if body.is_scheduled is not None:
        row.is_scheduled = bool(body.is_scheduled)
    elif body.day_type is not None:
        row.is_scheduled = default_is_scheduled_for_day_type(row.day_type, row.calendar_date)
    if body.name is not None:
        row.name = body.name
    if body.note is not None:
        row.note = body.note

    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": calendar_row_to_dict(row)}


@router.delete("/{entry_id}")
async def delete_company_work_calendar_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(CompanyWorkCalendar).where(CompanyWorkCalendar.id == entry_id)
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="エントリが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}
