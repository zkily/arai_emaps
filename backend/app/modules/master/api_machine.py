"""
設備マスタ API（machines）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from datetime import time as dt_time

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Machine
from app.modules.master.schemas import MachineCreate, MachineUpdate

router = APIRouter()


def _time_to_str(t) -> Optional[str]:
    if t is None:
        return None
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M:%S")
    return str(t)


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


def _machine_to_dict(row: Machine) -> dict:
    eff = row.efficiency
    if eff is not None and hasattr(eff, "__float__"):
        eff = float(eff)
    return {
        "id": row.id,
        "machine_cd": row.machine_cd,
        "machine_name": row.machine_name,
        "machine_type": row.machine_type,
        "status": row.status or "active",
        "available_from": _time_to_str(row.available_from),
        "available_to": _time_to_str(row.available_to),
        "calendar_id": row.calendar_id,
        "efficiency": eff,
        "note": row.note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_machine_list(
    keyword: Optional[str] = Query(None),
    machine_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備一覧取得"""
    query = select(Machine)
    if keyword:
        query = query.where(
            or_(
                Machine.machine_cd.like(f"%{keyword}%"),
                Machine.machine_name.like(f"%{keyword}%"),
            )
        )
    if machine_type:
        query = query.where(Machine.machine_type == machine_type)
    if status:
        query = query.where(Machine.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0
    query = query.order_by(Machine.machine_cd).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_machine_to_dict(r) for r in rows], "total": total},
        "list": [_machine_to_dict(r) for r in rows],
        "total": total,
    }


@router.get("/options")
async def get_machine_options(
    status: Optional[str] = Query("active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備オプション（稼働中など）"""
    q = select(Machine).order_by(Machine.machine_cd)
    if status:
        q = q.where(Machine.status == status)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [{"cd": r.machine_cd, "name": r.machine_name or r.machine_cd} for r in rows]


@router.get("/{machine_id}")
async def get_machine_by_id(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備1件取得"""
    q = select(Machine).where(Machine.id == machine_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備が見つかりません")
    return _machine_to_dict(row)


@router.post("")
async def create_machine(
    body: MachineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備新規登録"""
    q = select(Machine).where(Machine.machine_cd == body.machine_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="設備CDは既に存在します")
    row = Machine(
        machine_cd=body.machine_cd,
        machine_name=body.machine_name,
        machine_type=body.machine_type,
        status=body.status,
        available_from=_parse_time(body.available_from),
        available_to=_parse_time(body.available_to),
        calendar_id=body.calendar_id,
        efficiency=body.efficiency,
        note=body.note,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _machine_to_dict(row)


@router.put("/{machine_id}")
async def update_machine(
    machine_id: int,
    body: MachineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備更新"""
    q = select(Machine).where(Machine.id == machine_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備が見つかりません")
    if body.machine_cd is not None:
        row.machine_cd = body.machine_cd
    if body.machine_name is not None:
        row.machine_name = body.machine_name
    if body.machine_type is not None:
        row.machine_type = body.machine_type
    if body.status is not None:
        row.status = body.status
    if body.available_from is not None:
        row.available_from = _parse_time(body.available_from)
    if body.available_to is not None:
        row.available_to = _parse_time(body.available_to)
    if body.calendar_id is not None:
        row.calendar_id = body.calendar_id
    if body.efficiency is not None:
        row.efficiency = body.efficiency
    if body.note is not None:
        row.note = body.note
    await db.commit()
    await db.refresh(row)
    return _machine_to_dict(row)


@router.delete("/{machine_id}")
async def delete_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備削除"""
    q = select(Machine).where(Machine.id == machine_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}
