"""
仕入先マスタ API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Supplier
from app.modules.master.schemas import SupplierCreate, SupplierUpdate

router = APIRouter()


def _row_to_dict(row: Supplier) -> dict:
    return {
        "id": row.id,
        "supplier_cd": row.supplier_cd,
        "supplier_name": row.supplier_name,
        "supplier_kana": row.supplier_kana,
        "contact_person": row.contact_person,
        "phone": row.phone,
        "fax": row.fax,
        "email": row.email,
        "postal_code": row.postal_code,
        "address1": row.address1,
        "address2": row.address2,
        "payment_terms": row.payment_terms,
        "currency": row.currency,
        "remarks": row.remarks,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_supplier_list(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先一覧取得"""
    query = select(Supplier)
    if keyword:
        query = query.where(
            or_(
                Supplier.supplier_name.like(f"%{keyword}%"),
                Supplier.supplier_cd.like(f"%{keyword}%"),
                Supplier.supplier_kana.like(f"%{keyword}%"),
            )
        )

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "success": True,
        "data": {
            "list": [_row_to_dict(r) for r in rows],
            "total": total,
        },
    }


@router.get("/{supplier_id}")
async def get_supplier_by_id(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先1件取得"""
    q = select(Supplier).where(Supplier.id == supplier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="仕入先が見つかりません")
    return _row_to_dict(row)


@router.post("")
async def create_supplier(
    body: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先新規登録"""
    q = select(Supplier).where(Supplier.supplier_cd == body.supplier_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="仕入先CDは既に存在します")
    row = Supplier(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先更新"""
    q = select(Supplier).where(Supplier.id == supplier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="仕入先が見つかりません")
    for k, v in body.model_dump().items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先削除"""
    q = select(Supplier).where(Supplier.id == supplier_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="仕入先が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}
