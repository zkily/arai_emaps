"""
基礎データ管理APIエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.erp.inventory_models import Warehouse

router = APIRouter(prefix="/master", tags=["Master Data"])


# ========== 倉庫管理 ==========

@router.get("/warehouses")
async def get_warehouse_list(
    keyword: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """倉庫一覧取得"""
    query = select(Warehouse)
    
    if keyword:
        query = query.where(
            (Warehouse.warehouse_code.like(f"%{keyword}%")) |
            (Warehouse.warehouse_name.like(f"%{keyword}%"))
        )
    if is_active is not None:
        query = query.where(Warehouse.is_active == is_active)
    
    # 総件数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [_warehouse_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/warehouses/options")
async def get_warehouse_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """倉庫オプション取得"""
    query = select(Warehouse).where(Warehouse.is_active == True)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return [
        {"id": item.id, "code": item.warehouse_code, "name": item.warehouse_name}
        for item in items
    ]


@router.get("/warehouses/{warehouse_id}")
async def get_warehouse_by_id(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """倉庫詳細取得"""
    query = select(Warehouse).where(Warehouse.id == warehouse_id)
    result = await db.execute(query)
    warehouse = result.scalar_one_or_none()
    
    if not warehouse:
        raise HTTPException(status_code=404, detail="倉庫が見つかりません")
    
    return _warehouse_to_dict(warehouse)


@router.post("/warehouses")
async def create_warehouse(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """倉庫作成"""
    try:
        warehouse = Warehouse(**data)
        db.add(warehouse)
        await db.commit()
        await db.refresh(warehouse)
        return _warehouse_to_dict(warehouse)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/warehouses/{warehouse_id}")
async def update_warehouse(
    warehouse_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """倉庫更新"""
    query = select(Warehouse).where(Warehouse.id == warehouse_id)
    result = await db.execute(query)
    warehouse = result.scalar_one_or_none()
    
    if not warehouse:
        raise HTTPException(status_code=404, detail="倉庫が見つかりません")
    
    try:
        for key, value in data.items():
            if hasattr(warehouse, key):
                setattr(warehouse, key, value)
        
        await db.commit()
        await db.refresh(warehouse)
        return _warehouse_to_dict(warehouse)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/warehouses/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """倉庫削除"""
    query = select(Warehouse).where(Warehouse.id == warehouse_id)
    result = await db.execute(query)
    warehouse = result.scalar_one_or_none()
    
    if not warehouse:
        raise HTTPException(status_code=404, detail="倉庫が見つかりません")
    
    try:
        warehouse.is_active = False
        await db.commit()
        return {"message": "削除しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== ヘルパー関数 ==========

def _warehouse_to_dict(wh: Warehouse) -> dict:
    type_names = {
        "material": "原材料倉庫",
        "product": "製品倉庫",
        "semi_finished": "仕掛品倉庫",
        "defective": "不良品倉庫",
        "transit": "移動中"
    }
    return {
        "id": wh.id,
        "warehouse_code": wh.warehouse_code,
        "warehouse_name": wh.warehouse_name,
        "warehouse_type": wh.warehouse_type,
        "warehouse_type_name": type_names.get(wh.warehouse_type, wh.warehouse_type),
        "address": wh.address,
        "manager": wh.manager,
        "phone": wh.phone,
        "capacity": wh.capacity,
        "is_active": wh.is_active,
        "remarks": wh.remarks,
        "created_at": wh.created_at.isoformat() if wh.created_at else None,
        "updated_at": wh.updated_at.isoformat() if wh.updated_at else None
    }
