"""
顧客マスタ API（customers）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Customer
from app.modules.master.schemas import CustomerCreate, CustomerUpdate

router = APIRouter()


def _customer_to_dict(row: Customer) -> dict:
    return {
        "id": row.id,
        "customer_cd": row.customer_cd,
        "customer_name": row.customer_name,
        "phone": row.phone,
        "address": row.address,
        "customer_type": row.customer_type,
        "status": 1 if (row.status is None or row.status == 1) else 0,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_customer_list(
    keyword: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    customer_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """顧客一覧取得"""
    query = select(Customer)
    if keyword:
        query = query.where(
            or_(
                Customer.customer_cd.like(f"%{keyword}%"),
                Customer.customer_name.like(f"%{keyword}%"),
                Customer.phone.like(f"%{keyword}%"),
            )
        )
    if status is not None:
        query = query.where(Customer.status == status)
    if customer_type:
        query = query.where(Customer.customer_type == customer_type)

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0
    query = query.order_by(Customer.customer_cd).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {"list": [_customer_to_dict(r) for r in rows], "total": total},
        "list": [_customer_to_dict(r) for r in rows],
        "total": total,
    }


@router.get("/options")
async def get_customer_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """顧客オプション（有効のみ）"""
    q = select(Customer).where(Customer.status == 1).order_by(Customer.customer_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [{"cd": r.customer_cd, "name": r.customer_name or r.customer_cd} for r in rows]


@router.get("/{customer_id}")
async def get_customer_by_id(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """顧客1件取得"""
    q = select(Customer).where(Customer.id == customer_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    return _customer_to_dict(row)


@router.post("")
async def create_customer(
    body: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """顧客新規登録"""
    q = select(Customer).where(Customer.customer_cd == body.customer_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="顧客CDは既に存在します")
    row = Customer(
        customer_cd=body.customer_cd,
        customer_name=body.customer_name,
        phone=body.phone,
        address=body.address,
        customer_type=body.customer_type,
        status=body.status,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _customer_to_dict(row)


@router.put("/{customer_id}")
async def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """顧客更新"""
    q = select(Customer).where(Customer.id == customer_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    if body.customer_cd is not None:
        row.customer_cd = body.customer_cd
    if body.customer_name is not None:
        row.customer_name = body.customer_name
    if body.phone is not None:
        row.phone = body.phone
    if body.address is not None:
        row.address = body.address
    if body.customer_type is not None:
        row.customer_type = body.customer_type
    if body.status is not None:
        row.status = body.status
    await db.commit()
    await db.refresh(row)
    return _customer_to_dict(row)


@router.patch("/{customer_id}/status")
async def update_customer_status(
    customer_id: int,
    status: int = Query(..., ge=0, le=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """顧客状態更新"""
    q = select(Customer).where(Customer.id == customer_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    row.status = status
    await db.commit()
    await db.refresh(row)
    return _customer_to_dict(row)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """顧客削除"""
    q = select(Customer).where(Customer.id == customer_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}
