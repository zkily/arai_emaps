"""
外注先マスタ API（outsourcing_suppliers）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.outsourcing.models import OutsourcingSupplier
from app.modules.outsourcing.schemas import OutsourcingSupplierCreate, OutsourcingSupplierUpdate

router = APIRouter()


def _row_to_dict(row: OutsourcingSupplier) -> dict:
    return {
        "id": row.id,
        "supplier_cd": row.supplier_cd,
        "supplier_name": row.supplier_name,
        "supplier_type": row.supplier_type,
        "postal_code": row.postal_code,
        "address": row.address,
        "phone": row.phone,
        "fax": row.fax,
        "contact_person": row.contact_person,
        "email": row.email,
        "payment_terms": row.payment_terms,
        "lead_time_days": row.lead_time_days,
        "remarks": row.remarks,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_suppliers(
    type: Optional[str] = Query(None, description="外注種別"),
    isActive: Optional[bool] = Query(None, alias="isActive"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注先一覧取得"""
    query = select(OutsourcingSupplier)
    if type:
        query = query.where(OutsourcingSupplier.supplier_type == type)
    if isActive is not None:
        query = query.where(OutsourcingSupplier.is_active == isActive)
    query = query.order_by(OutsourcingSupplier.supplier_cd)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {"success": True, "data": [_row_to_dict(r) for r in rows]}


@router.get("/{supplier_id}")
async def get_supplier_by_id(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注先1件取得"""
    q = select(OutsourcingSupplier).where(OutsourcingSupplier.id == supplier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="外注先が見つかりません")
    return _row_to_dict(row)


@router.post("")
async def create_supplier(
    body: OutsourcingSupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注先新規登録"""
    q = select(OutsourcingSupplier).where(OutsourcingSupplier.supplier_cd == body.supplier_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"外注先コード「{body.supplier_cd}」は既に登録されています",
        )
    row = OutsourcingSupplier(**body.model_dump())
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return {"success": True, "data": _row_to_dict(row)}


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    body: OutsourcingSupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注先更新"""
    q = select(OutsourcingSupplier).where(OutsourcingSupplier.id == supplier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="外注先が見つかりません")
    data = body.model_dump(exclude_unset=True)
    if "supplier_cd" in data and data["supplier_cd"] != row.supplier_cd:
        ex = await db.execute(select(OutsourcingSupplier).where(OutsourcingSupplier.supplier_cd == data["supplier_cd"]))
        if ex.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="外注先コードは既に使用されています")
    for k, v in data.items():
        setattr(row, k, v)
    await db.flush()
    await db.refresh(row)
    return {"success": True, "data": _row_to_dict(row)}


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注先削除"""
    q = select(OutsourcingSupplier).where(OutsourcingSupplier.id == supplier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="外注先が見つかりません")
    await db.delete(row)
    await db.flush()
    return {"success": True, "message": "削除しました"}
