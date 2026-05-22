"""
納入先マスタ API（destinations + destination_holidays）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
from datetime import date

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Destination, DestinationHoliday, DestinationWorkday
from app.modules.master.schemas import DestinationCreate, DestinationUpdate

router = APIRouter()


def _destination_to_dict(row: Destination) -> dict:
    return {
        "id": row.id,
        "destination_cd": row.destination_cd,
        "destination_name": row.destination_name,
        "customer_cd": row.customer_cd,
        "carrier_cd": row.carrier_cd,
        "delivery_lead_time": row.delivery_lead_time or 0,
        "issue_type": row.issue_type or "自動",
        "phone": row.phone,
        "address": row.address,
        "status": 1 if (row.status is None or row.status == 1) else 0,
        "picked_id": row.picked_id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _holiday_to_dict(row: DestinationHoliday) -> dict:
    return {
        "id": row.id,
        "destination_cd": row.destination_cd,
        "holiday_date": row.holiday_date.isoformat() if row.holiday_date else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _workday_to_dict(row: DestinationWorkday) -> dict:
    return {
        "id": row.id,
        "destination_cd": row.destination_cd,
        "work_date": row.work_date.isoformat() if row.work_date else None,
        "reason": row.reason,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


# ========== 納入先 CRUD ==========

@router.get("")
async def get_destination_list(
    keyword: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    issue_type: Optional[str] = Query(None),
    carrier_cd: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先一覧取得"""
    query = select(Destination)
    if keyword:
        query = query.where(
            or_(
                Destination.destination_cd.like(f"%{keyword}%"),
                Destination.destination_name.like(f"%{keyword}%"),
                Destination.customer_cd.like(f"%{keyword}%"),
            )
        )
    if status is not None:
        query = query.where(Destination.status == status)
    if issue_type:
        query = query.where(Destination.issue_type == issue_type)
    if carrier_cd:
        query = query.where(Destination.carrier_cd.like(f"%{carrier_cd}%"))

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0
    query = query.order_by(Destination.destination_cd).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_destination_to_dict(r) for r in rows], "total": total},
        "list": [_destination_to_dict(r) for r in rows],
        "total": total,
    }


@router.get("/options")
async def get_destination_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先オプション（有効のみ）。destinations テーブルから取得。"""
    q = select(Destination).where(Destination.status == 1).order_by(Destination.destination_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [{"cd": r.destination_cd, "name": r.destination_name or r.destination_cd} for r in rows]


@router.get("/options-with-issue-type")
async def get_destination_options_with_issue_type(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先オプション（有効のみ）+ issue_type。destinations テーブルから取得。"""
    q = select(Destination).where(Destination.status == 1).order_by(Destination.destination_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {
            "cd": r.destination_cd,
            "name": r.destination_name or r.destination_cd,
            "issue_type": r.issue_type or "自動",
        }
        for r in rows
    ]


@router.get("/holidays/by-destination/{destination_cd}")
async def get_holidays_by_destination(
    destination_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定納入先の休日一覧"""
    q = (
        select(DestinationHoliday)
        .where(DestinationHoliday.destination_cd == destination_cd)
        .order_by(DestinationHoliday.holiday_date)
    )
    res = await db.execute(q)
    rows = res.scalars().all()
    return [_holiday_to_dict(r) for r in rows]


@router.post("/holidays")
async def add_holiday(
    destination_cd: str = Query(..., alias="destinationCd"),
    holiday_date: date = Query(..., alias="holidayDate"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """休日追加"""
    q = select(DestinationHoliday).where(
        DestinationHoliday.destination_cd == destination_cd,
        DestinationHoliday.holiday_date == holiday_date,
    )
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同じ日付は既に登録されています")
    row = DestinationHoliday(destination_cd=destination_cd, holiday_date=holiday_date)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _holiday_to_dict(row)


@router.delete("/holidays/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """休日削除"""
    q = select(DestinationHoliday).where(DestinationHoliday.id == holiday_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="休日が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


# ========== 臨時出勤日（workdays） ==========

@router.get("/workdays/by-destination/{destination_cd}")
async def get_workdays_by_destination(
    destination_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定納入先の臨時出勤日一覧"""
    q = (
        select(DestinationWorkday)
        .where(DestinationWorkday.destination_cd == destination_cd)
        .order_by(DestinationWorkday.work_date)
    )
    res = await db.execute(q)
    rows = res.scalars().all()
    return [_workday_to_dict(r) for r in rows]


@router.post("/workdays")
async def add_workday(
    destination_cd: str = Query(..., alias="destinationCd"),
    work_date: date = Query(..., alias="workDate"),
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """臨時出勤日追加"""
    q = select(DestinationWorkday).where(
        DestinationWorkday.destination_cd == destination_cd,
        DestinationWorkday.work_date == work_date,
    )
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同じ日付は既に登録されています")
    row = DestinationWorkday(destination_cd=destination_cd, work_date=work_date, reason=reason)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _workday_to_dict(row)


@router.delete("/workdays/{workday_id}")
async def delete_workday(
    workday_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """臨時出勤日削除"""
    q = select(DestinationWorkday).where(DestinationWorkday.id == workday_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="臨時出勤日が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


@router.get("/{destination_id}")
async def get_destination_by_id(
    destination_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先1件取得"""
    q = select(Destination).where(Destination.id == destination_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="納入先が見つかりません")
    return _destination_to_dict(row)


@router.post("")
async def create_destination(
    body: DestinationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先新規登録"""
    q = select(Destination).where(Destination.destination_cd == body.destination_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="納入先CDは既に存在します")
    row = Destination(
        destination_cd=body.destination_cd,
        destination_name=body.destination_name,
        customer_cd=body.customer_cd,
        carrier_cd=body.carrier_cd,
        delivery_lead_time=body.delivery_lead_time,
        issue_type=body.issue_type or "自動",
        phone=body.phone,
        address=body.address,
        status=body.status,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _destination_to_dict(row)


@router.put("/{destination_id}")
async def update_destination(
    destination_id: int,
    body: DestinationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先更新"""
    q = select(Destination).where(Destination.id == destination_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="納入先が見つかりません")
    if body.destination_cd is not None:
        row.destination_cd = body.destination_cd
    if body.destination_name is not None:
        row.destination_name = body.destination_name
    if body.customer_cd is not None:
        row.customer_cd = body.customer_cd
    if body.carrier_cd is not None:
        row.carrier_cd = body.carrier_cd
    if body.delivery_lead_time is not None:
        row.delivery_lead_time = body.delivery_lead_time
    if body.issue_type is not None:
        row.issue_type = body.issue_type
    if body.phone is not None:
        row.phone = body.phone
    if body.address is not None:
        row.address = body.address
    if body.status is not None:
        row.status = body.status
    await db.commit()
    await db.refresh(row)
    return _destination_to_dict(row)


@router.patch("/{destination_id}/status")
async def update_destination_status(
    destination_id: int,
    status: int = Query(..., ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先状態更新"""
    q = select(Destination).where(Destination.id == destination_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="納入先が見つかりません")
    row.status = status
    await db.commit()
    await db.refresh(row)
    return _destination_to_dict(row)


@router.delete("/{destination_id}")
async def delete_destination(
    destination_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先削除"""
    q = select(Destination).where(Destination.id == destination_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="納入先が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


# ========== 納入先休日（ルートは上に定義済み） ==========
