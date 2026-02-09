"""
運送便マスタ API（carriers）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from datetime import time as dt_time

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Carrier
from app.modules.master.schemas import CarrierCreate, CarrierUpdate

router = APIRouter()


def _time_to_str(t: Optional[dt_time]) -> Optional[str]:
    if t is None:
        return None
    return t.strftime("%H:%M:%S")


def _parse_time(s: Optional[str]) -> Optional[dt_time]:
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    parts = s.split(":")
    if len(parts) >= 2:
        try:
            h, m = int(parts[0]), int(parts[1])
            sec = int(parts[2]) if len(parts) > 2 else 0
            return dt_time(h, m, sec)
        except (ValueError, IndexError):
            pass
    return None


def _carrier_to_dict(row: Carrier) -> dict:
    return {
        "id": row.id,
        "carrier_cd": row.carrier_cd,
        "carrier_name": row.carrier_name,
        "contact_person": row.contact_person,
        "phone": row.phone,
        "shipping_time": _time_to_str(row.shipping_time),
        "report_no": row.report_no,
        "note": row.note,
        "status": 1 if (row.status is None or row.status == 1) else 0,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_carrier_list(
    keyword: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """運送便一覧取得"""
    query = select(Carrier)
    if keyword:
        query = query.where(
            or_(
                Carrier.carrier_cd.like(f"%{keyword}%"),
                Carrier.carrier_name.like(f"%{keyword}%"),
                Carrier.contact_person.like(f"%{keyword}%"),
            )
        )
    if status is not None:
        query = query.where(Carrier.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0
    query = query.order_by(Carrier.carrier_cd).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_carrier_to_dict(r) for r in rows], "total": total},
        "list": [_carrier_to_dict(r) for r in rows],
        "total": total,
    }


@router.get("/options")
async def get_carrier_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """運送便オプション（有効のみ）"""
    q = select(Carrier).where(Carrier.status == 1).order_by(Carrier.carrier_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [{"cd": r.carrier_cd, "name": r.carrier_name or r.carrier_cd} for r in rows]


@router.get("/{carrier_id}")
async def get_carrier_by_id(
    carrier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """運送便1件取得"""
    q = select(Carrier).where(Carrier.id == carrier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="運送便が見つかりません")
    return _carrier_to_dict(row)


@router.post("")
async def create_carrier(
    body: CarrierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """運送便新規登録"""
    q = select(Carrier).where(Carrier.carrier_cd == body.carrier_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="運送便CDは既に存在します")
    row = Carrier(
        carrier_cd=body.carrier_cd,
        carrier_name=body.carrier_name,
        contact_person=body.contact_person,
        phone=body.phone,
        shipping_time=_parse_time(body.shipping_time),
        report_no=body.report_no,
        note=body.note,
        status=body.status,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _carrier_to_dict(row)


@router.put("/{carrier_id}")
async def update_carrier(
    carrier_id: int,
    body: CarrierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """運送便更新"""
    q = select(Carrier).where(Carrier.id == carrier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="運送便が見つかりません")
    if body.carrier_cd is not None:
        row.carrier_cd = body.carrier_cd
    if body.carrier_name is not None:
        row.carrier_name = body.carrier_name
    if body.contact_person is not None:
        row.contact_person = body.contact_person
    if body.phone is not None:
        row.phone = body.phone
    if body.shipping_time is not None:
        row.shipping_time = _parse_time(body.shipping_time)
    if body.report_no is not None:
        row.report_no = body.report_no
    if body.note is not None:
        row.note = body.note
    if body.status is not None:
        row.status = body.status
    await db.commit()
    await db.refresh(row)
    return _carrier_to_dict(row)


@router.patch("/{carrier_id}/status")
async def update_carrier_status(
    carrier_id: int,
    status: int = Query(..., ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """運送便状態更新"""
    q = select(Carrier).where(Carrier.id == carrier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="運送便が見つかりません")
    row.status = status
    await db.commit()
    await db.refresh(row)
    return _carrier_to_dict(row)


@router.delete("/{carrier_id}")
async def delete_carrier(
    carrier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """運送便削除"""
    q = select(Carrier).where(Carrier.id == carrier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="運送便が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}
