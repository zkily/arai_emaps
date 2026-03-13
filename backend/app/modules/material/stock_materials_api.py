"""
在庫材料管理 API（stock_materials）
GET    /api/material/stock-materials             一覧取得
GET    /api/material/stock-materials/{id}        詳細取得
POST   /api/material/stock-materials             新規登録
PUT    /api/material/stock-materials/{id}        更新
DELETE /api/material/stock-materials/{id}        削除
PATCH  /api/material/stock-materials/{id}/toggle 使用/未使用切替
GET    /api/material/stock-materials/summary     サマリー統計
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.material.models import StockMaterial
from app.modules.material.schemas import (
    StockMaterialCreate,
    StockMaterialUpdate,
    StockMaterialResponse,
)

router = APIRouter()


def _to_dict(r: StockMaterial) -> dict:
    return {
        "id": r.id,
        "material_name": r.material_name,
        "manufacture_no": r.manufacture_no,
        "quantity": r.quantity,
        "log_date": r.log_date.isoformat() if r.log_date else None,
        "supplier": r.supplier,
        "material_quality": r.material_quality,
        "is_used": r.is_used,
        "note": r.note,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サマリー統計"""
    total = (await db.execute(select(func.count(StockMaterial.id)))).scalar() or 0
    unused = (await db.execute(select(func.count(StockMaterial.id)).where(StockMaterial.is_used == False))).scalar() or 0
    used = (await db.execute(select(func.count(StockMaterial.id)).where(StockMaterial.is_used == True))).scalar() or 0
    total_qty = (await db.execute(select(func.sum(StockMaterial.quantity)))).scalar() or 0
    return {
        "success": True,
        "data": {
            "total": total,
            "unused": unused,
            "used": used,
            "total_quantity": total_qty,
        },
    }


@router.get("")
async def list_stock_materials(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=2000),
    keyword: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    is_used: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    sortBy: Optional[str] = Query("log_date"),
    sortOrder: Optional[str] = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫材料一覧"""
    q = select(StockMaterial)
    if keyword:
        kw = f"%{keyword}%"
        q = q.where(
            or_(
                StockMaterial.material_name.ilike(kw),
                StockMaterial.manufacture_no.ilike(kw),
                StockMaterial.supplier.ilike(kw),
            )
        )
    if supplier:
        q = q.where(StockMaterial.supplier == supplier)
    if is_used is not None and is_used != "":
        q = q.where(StockMaterial.is_used == (is_used == "true" or is_used == "1"))
    if startDate:
        q = q.where(StockMaterial.log_date >= date.fromisoformat(startDate))
    if endDate:
        q = q.where(StockMaterial.log_date <= date.fromisoformat(endDate))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0

    sort_col = getattr(StockMaterial, sortBy, StockMaterial.log_date)
    q = q.order_by(sort_col.desc() if sortOrder == "desc" else sort_col.asc())
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": {"list": [_to_dict(r) for r in rows], "total": total}}


@router.get("/suppliers")
async def get_suppliers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先一覧"""
    q = select(distinct(StockMaterial.supplier)).where(StockMaterial.supplier.isnot(None)).order_by(StockMaterial.supplier)
    result = await db.execute(q)
    return {"success": True, "data": [row[0] for row in result.all() if row[0]]}


@router.get("/{item_id}")
async def get_stock_material(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫材料詳細"""
    result = await db.execute(select(StockMaterial).where(StockMaterial.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    return {"success": True, "data": _to_dict(row)}


@router.post("")
async def create_stock_material(
    body: StockMaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫材料新規登録"""
    row = StockMaterial(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _to_dict(row)}


@router.put("/{item_id}")
async def update_stock_material(
    item_id: int,
    body: StockMaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫材料更新"""
    result = await db.execute(select(StockMaterial).where(StockMaterial.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _to_dict(row)}


@router.patch("/{item_id}/toggle")
async def toggle_used_status(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """使用/未使用切替"""
    result = await db.execute(select(StockMaterial).where(StockMaterial.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    row.is_used = not row.is_used
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _to_dict(row)}


@router.delete("/{item_id}")
async def delete_stock_material(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫材料削除"""
    result = await db.execute(select(StockMaterial).where(StockMaterial.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}
