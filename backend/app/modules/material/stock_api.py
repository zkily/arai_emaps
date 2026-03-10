"""
材料在庫 API
  material_stock     → /api/material/stock
  material_stock_sub → /api/material/stock/sub
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct
from collections import defaultdict
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.material.models import MaterialStock, MaterialStockSub
from app.modules.material.schemas import (
    MaterialStockCreate,
    MaterialStockUpdate,
    MaterialStockResponse,
    MaterialStockSubCreate,
    MaterialStockSubUpdate,
    MaterialStockSubResponse,
)

router = APIRouter()


# ─────────────────────────────────────────────
# material_stock  メイン在庫
# ─────────────────────────────────────────────

def _stock_to_dict(r: MaterialStock) -> dict:
    return {
        "id": r.id,
        "material_cd": r.material_cd,
        "material_name": r.material_name,
        "date": r.date.isoformat() if r.date else None,
        "initial_stock": r.initial_stock,
        "current_stock": r.current_stock,
        "safety_stock": r.safety_stock,
        "planned_usage": r.planned_usage,
        "adjustment_quantity": r.adjustment_quantity,
        "max_stock": r.max_stock,
        "standard_spec": r.standard_spec,
        "unit": r.unit,
        "unit_price": float(r.unit_price) if r.unit_price is not None else None,
        "pieces_per_bundle": r.pieces_per_bundle,
        "long_weight": float(r.long_weight) if r.long_weight is not None else None,
        "supplier_cd": r.supplier_cd,
        "supplier_name": r.supplier_name,
        "lead_time": r.lead_time,
        "bundle_quantity": r.bundle_quantity,
        "bundle_weight": float(r.bundle_weight) if r.bundle_weight is not None else None,
        "order_quantity": r.order_quantity,
        "order_bundle_quantity": r.order_bundle_quantity,
        "order_amount": float(r.order_amount) if r.order_amount is not None else None,
        "remarks": r.remarks,
        "last_updated": r.last_updated.isoformat() if r.last_updated else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("")
async def list_material_stocks(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=10000),
    keyword: Optional[str] = Query(None),
    material_cd: Optional[str] = Query(None),
    supplier_cd: Optional[str] = Query(None),
    suppliers: Optional[str] = Query(None, description="仕入先名称のカンマ区切り。指定時は supplier_name で IN 検索"),
    target_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料在庫一覧"""
    q = select(MaterialStock)
    if keyword:
        kw = f"%{keyword}%"
        q = q.where(
            or_(
                MaterialStock.material_cd.ilike(kw),
                MaterialStock.material_name.ilike(kw),
                MaterialStock.supplier_name.ilike(kw),
            )
        )
    if material_cd:
        q = q.where(MaterialStock.material_cd == material_cd)
    if supplier_cd:
        q = q.where(MaterialStock.supplier_cd == supplier_cd)
    if suppliers:
        supplier_list = [s.strip() for s in suppliers.split(",") if s.strip()]
        if supplier_list:
            q = q.where(MaterialStock.supplier_name.in_(supplier_list))
    if target_date:
        q = q.where(MaterialStock.date == date.fromisoformat(target_date))

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar() or 0

    q = q.order_by(MaterialStock.material_cd, MaterialStock.date.desc())
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(q)).scalars().all()

    return {"success": True, "data": {"list": [_stock_to_dict(r) for r in rows], "total": total}}


@router.get("/latest")
async def get_latest_stocks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """各材料の最新在庫（material_cd ごとに最新日付）"""
    subq = (
        select(MaterialStock.material_cd, func.max(MaterialStock.date).label("max_date"))
        .group_by(MaterialStock.material_cd)
        .subquery()
    )
    q = select(MaterialStock).join(
        subq,
        (MaterialStock.material_cd == subq.c.material_cd) & (MaterialStock.date == subq.c.max_date),
    )
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": [_stock_to_dict(r) for r in rows]}


@router.post("/calculate")
async def calculate_material_stock(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    在庫計算: material_stock の current_stock を再計算する。
    各 material_cd について、initial_stock > 0 の最終日を起点に、
    current_stock = initial_stock + order_quantity + adjustment_quantity - planned_usage + 前日の current_stock
    で日付昇順に計算し、DB を更新する。
    """
    q = select(MaterialStock).order_by(MaterialStock.material_cd, MaterialStock.date.asc())
    rows = (await db.execute(q)).scalars().all()
    if not rows:
        return {"success": True, "data": {"calculated_count": 0, "updated_count": 0}}

    # material_cd ごとにグループ化
    by_material: dict[str, list[MaterialStock]] = defaultdict(list)
    for r in rows:
        by_material[r.material_cd].append(r)

    updates: dict[int, int] = {}  # id -> new current_stock
    calculated_count = 0

    for material_cd, list_rows in by_material.items():
        # initial_stock > 0 のうち最終日を取得（日付昇順なので、last が最新日）
        base_dates = [r for r in list_rows if (r.initial_stock or 0) > 0]
        if not base_dates:
            continue
        base_date = max(r.date for r in base_dates)
        # base_date 以降の行を日付昇順で計算
        to_calc = sorted([r for r in list_rows if r.date >= base_date], key=lambda x: x.date)
        prev_current = 0
        for r in to_calc:
            init = r.initial_stock or 0
            order_qty = r.order_quantity or 0
            adj = r.adjustment_quantity or 0
            usage = r.planned_usage or 0
            new_current = init + order_qty + adj - usage + prev_current
            updates[r.id] = new_current
            prev_current = new_current
        calculated_count += 1

    # 一括更新
    updated_count = 0
    for row in rows:
        if row.id in updates and row.current_stock != updates[row.id]:
            row.current_stock = updates[row.id]
            updated_count += 1
    await db.commit()
    return {
        "success": True,
        "data": {"calculated_count": calculated_count, "updated_count": updated_count},
    }


@router.get("/summary")
async def get_stock_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫サマリー（総材料数・安全在庫以下・合計在庫金額）"""
    total_materials = (await db.execute(select(func.count(distinct(MaterialStock.material_cd))))).scalar() or 0
    below_safety = (
        await db.execute(
            select(func.count()).where(MaterialStock.current_stock <= MaterialStock.safety_stock)
        )
    ).scalar() or 0
    total_value_result = await db.execute(
        select(func.sum(MaterialStock.current_stock * MaterialStock.unit_price))
    )
    total_value = float(total_value_result.scalar() or 0)
    return {
        "success": True,
        "data": {
            "total_materials": total_materials,
            "below_safety": below_safety,
            "total_value": total_value,
        },
    }


@router.post("")
async def create_material_stock(
    body: MaterialStockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料在庫登録"""
    row = MaterialStock(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _stock_to_dict(row)}


@router.put("/{item_id}")
async def update_material_stock(
    item_id: int,
    body: MaterialStockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料在庫更新"""
    result = await db.execute(select(MaterialStock).where(MaterialStock.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _stock_to_dict(row)}


@router.delete("/{item_id}")
async def delete_material_stock(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料在庫削除"""
    result = await db.execute(select(MaterialStock).where(MaterialStock.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}


# ─────────────────────────────────────────────
# material_stock_sub  手動注文サブ在庫
# ─────────────────────────────────────────────

def _sub_to_dict(r: MaterialStockSub) -> dict:
    return {
        "id": r.id,
        "material_cd": r.material_cd,
        "material_name": r.material_name,
        "date": r.date.isoformat() if r.date else None,
        "current_stock": float(r.current_stock) if r.current_stock is not None else None,
        "safety_stock": float(r.safety_stock) if r.safety_stock is not None else None,
        "max_stock": float(r.max_stock) if r.max_stock is not None else None,
        "unit": r.unit,
        "unit_price": float(r.unit_price) if r.unit_price is not None else None,
        "supplier_cd": r.supplier_cd,
        "supplier_name": r.supplier_name,
        "lead_time": r.lead_time,
        "planned_usage": float(r.planned_usage) if r.planned_usage is not None else None,
        "order_quantity": float(r.order_quantity) if r.order_quantity is not None else None,
        "order_bundle_quantity": float(r.order_bundle_quantity) if r.order_bundle_quantity is not None else None,
        "bundle_weight": float(r.bundle_weight) if r.bundle_weight is not None else None,
        "order_amount": float(r.order_amount) if r.order_amount is not None else None,
        "standard_spec": r.standard_spec,
        "pieces_per_bundle": r.pieces_per_bundle,
        "long_weight": float(r.long_weight) if r.long_weight is not None else None,
        "remarks": r.remarks,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "last_updated": r.last_updated.isoformat() if r.last_updated else None,
    }


@router.get("/sub")
async def list_stock_sub(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=500),
    keyword: Optional[str] = Query(None),
    suppliers: Optional[str] = Query(None, description="仕入先名称のカンマ区切り。指定時は supplier_name で IN 検索"),
    target_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サブ在庫一覧"""
    q = select(MaterialStockSub)
    if keyword:
        kw = f"%{keyword}%"
        q = q.where(
            or_(
                MaterialStockSub.material_cd.ilike(kw),
                MaterialStockSub.material_name.ilike(kw),
            )
        )
    if suppliers:
        supplier_list = [s.strip() for s in suppliers.split(",") if s.strip()]
        if supplier_list:
            q = q.where(MaterialStockSub.supplier_name.in_(supplier_list))
    if target_date:
        q = q.where(MaterialStockSub.date == date.fromisoformat(target_date))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    q = q.order_by(MaterialStockSub.date.desc(), MaterialStockSub.material_cd)
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": {"list": [_sub_to_dict(r) for r in rows], "total": total}}


@router.post("/sub")
async def create_stock_sub(
    body: MaterialStockSubCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サブ在庫登録"""
    row = MaterialStockSub(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _sub_to_dict(row)}


@router.put("/sub/{item_id}")
async def update_stock_sub(
    item_id: int,
    body: MaterialStockSubUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サブ在庫更新"""
    result = await db.execute(select(MaterialStockSub).where(MaterialStockSub.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _sub_to_dict(row)}


@router.delete("/sub/{item_id}")
async def delete_stock_sub(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サブ在庫削除"""
    result = await db.execute(select(MaterialStockSub).where(MaterialStockSub.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}
