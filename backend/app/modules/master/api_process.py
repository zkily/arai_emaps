"""
工程マスタ API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Process
from app.modules.master.schemas import ProcessCreate, ProcessUpdate
from typing import Optional

router = APIRouter()


def _process_to_dict(row: Process) -> dict:
    return {
        "id": row.id,
        "process_cd": row.process_cd,
        "process_name": row.process_name,
        "short_name": row.short_name,
        "category": row.category,
        "is_outsource": bool(row.is_outsource),
        "default_cycle_sec": float(row.default_cycle_sec) if row.default_cycle_sec is not None else 0.0,
        "default_yield": float(row.default_yield) if row.default_yield is not None else 1.0,
        "capacity_unit": row.capacity_unit or "pcs",
        "remark": row.remark,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_process_list(
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_outsource: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程一覧取得"""
    query = select(Process)
    if keyword:
        query = query.where(
            or_(
                Process.process_cd.like(f"%{keyword}%"),
                Process.process_name.like(f"%{keyword}%"),
                Process.short_name.like(f"%{keyword}%"),
            )
        )
    if category:
        query = query.where(Process.category == category)
    if is_outsource is not None:
        query = query.where(Process.is_outsource == (1 if is_outsource else 0))

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0
    query = query.order_by(Process.process_cd).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_process_to_dict(r) for r in rows], "total": total},
        "list": [_process_to_dict(r) for r in rows],
        "total": total,
    }


@router.get("/by-cd/{process_cd}")
async def get_process_by_cd(
    process_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程CDで1件取得（オプション用）"""
    q = select(Process).where(Process.process_cd == process_cd)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="工程が見つかりません")
    return _process_to_dict(row)


@router.get("/{process_id}")
async def get_process_by_id(
    process_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程IDで1件取得"""
    q = select(Process).where(Process.id == process_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="工程が見つかりません")
    return _process_to_dict(row)


@router.post("")
async def create_process(
    body: ProcessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程新規登録"""
    q = select(Process).where(Process.process_cd == body.process_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="工程CDは既に存在します")
    row = Process(
        process_cd=body.process_cd,
        process_name=body.process_name,
        short_name=body.short_name,
        category=body.category,
        is_outsource=1 if body.is_outsource else 0,
        default_cycle_sec=body.default_cycle_sec,
        default_yield=body.default_yield,
        capacity_unit=body.capacity_unit or "pcs",
        remark=body.remark,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _process_to_dict(row)


@router.put("/{process_id}")
async def update_process(
    process_id: int,
    body: ProcessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程更新"""
    q = select(Process).where(Process.id == process_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="工程が見つかりません")
    if body.process_cd is not None:
        row.process_cd = body.process_cd
    if body.process_name is not None:
        row.process_name = body.process_name
    if body.short_name is not None:
        row.short_name = body.short_name
    if body.category is not None:
        row.category = body.category
    if hasattr(body, "is_outsource"):
        row.is_outsource = 1 if body.is_outsource else 0
    if body.default_cycle_sec is not None:
        row.default_cycle_sec = body.default_cycle_sec
    if body.default_yield is not None:
        row.default_yield = body.default_yield
    if body.capacity_unit is not None:
        row.capacity_unit = body.capacity_unit or "pcs"
    if body.remark is not None:
        row.remark = body.remark
    await db.commit()
    await db.refresh(row)
    return _process_to_dict(row)


@router.delete("/{process_id}")
async def delete_process(
    process_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程削除"""
    q = select(Process).where(Process.id == process_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="工程が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}
