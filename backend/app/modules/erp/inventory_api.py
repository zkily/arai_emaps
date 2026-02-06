"""
在庫管理APIエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import date, datetime
import uuid

from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.erp.inventory_models import (
    Inventory, InventoryTransaction, InventoryAdjustment, StockAlert, Warehouse
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ========== 在庫一覧 ==========

@router.get("")
async def get_inventory_list(
    product_code: Optional[str] = Query(None),
    product_name: Optional[str] = Query(None),
    warehouse_code: Optional[str] = Query(None),
    has_stock: Optional[bool] = Query(None),
    low_stock_only: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """在庫一覧取得"""
    query = select(Inventory).where(Inventory.is_active == True)
    
    if product_code:
        query = query.where(Inventory.product_code.like(f"%{product_code}%"))
    if product_name:
        query = query.where(Inventory.product_name.like(f"%{product_name}%"))
    if warehouse_code:
        query = query.where(Inventory.warehouse_code == warehouse_code)
    if has_stock:
        query = query.where(Inventory.quantity > 0)
    if low_stock_only:
        query = query.where(Inventory.quantity < Inventory.min_stock_level)
    
    # 総件数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [_inventory_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/stats")
async def get_inventory_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """在庫統計取得"""
    # 総在庫数
    total_query = select(
        func.count(Inventory.id).label("total_items"),
        func.sum(Inventory.total_cost).label("total_value")
    ).where(Inventory.is_active == True)
    total_result = await db.execute(total_query)
    total_row = total_result.first()
    
    # 在庫不足
    low_stock_query = select(func.count()).where(
        and_(Inventory.is_active == True, Inventory.quantity < Inventory.min_stock_level)
    )
    low_stock_result = await db.execute(low_stock_query)
    low_stock_count = low_stock_result.scalar()
    
    # 過剰在庫
    overstock_query = select(func.count()).where(
        and_(Inventory.is_active == True, Inventory.quantity > Inventory.max_stock_level, Inventory.max_stock_level > 0)
    )
    overstock_result = await db.execute(overstock_query)
    overstock_count = overstock_result.scalar()
    
    return {
        "total_items": total_row.total_items or 0,
        "total_value": float(total_row.total_value or 0),
        "low_stock_count": low_stock_count or 0,
        "overstock_count": overstock_count or 0,
        "expiring_soon_count": 0
    }


@router.get("/{inventory_id}")
async def get_inventory_by_id(
    inventory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """在庫詳細取得"""
    query = select(Inventory).where(Inventory.id == inventory_id)
    result = await db.execute(query)
    inventory = result.scalar_one_or_none()
    
    if not inventory:
        raise HTTPException(status_code=404, detail="在庫が見つかりません")
    
    return _inventory_to_dict(inventory)


# ========== 入出庫 ==========

@router.get("/transactions")
async def get_inventory_transactions(
    inventory_id: Optional[int] = Query(None),
    product_code: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """在庫トランザクション一覧取得"""
    query = select(InventoryTransaction)
    
    if inventory_id:
        query = query.where(InventoryTransaction.inventory_id == inventory_id)
    if product_code:
        query = query.where(InventoryTransaction.product_code.like(f"%{product_code}%"))
    if transaction_type:
        query = query.where(InventoryTransaction.transaction_type == transaction_type)
    if start_date:
        query = query.where(InventoryTransaction.created_at >= start_date)
    if end_date:
        query = query.where(InventoryTransaction.created_at <= end_date)
    
    # 総件数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    query = query.order_by(InventoryTransaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [_transaction_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/inbound")
async def create_inbound_transaction(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """入庫処理"""
    try:
        # 在庫レコード取得または作成
        query = select(Inventory).where(
            and_(
                Inventory.product_code == data["product_code"],
                Inventory.warehouse_code == data["warehouse_code"]
            )
        )
        result = await db.execute(query)
        inventory = result.scalar_one_or_none()
        
        balance_before = inventory.quantity if inventory else 0
        quantity = data["quantity"]
        unit_cost = data.get("unit_cost", 0)
        
        if inventory:
            inventory.quantity += quantity
            inventory.available_quantity += quantity
            inventory.total_cost = inventory.quantity * float(inventory.unit_cost or unit_cost)
        else:
            inventory = Inventory(
                product_code=data["product_code"],
                warehouse_code=data["warehouse_code"],
                quantity=quantity,
                available_quantity=quantity,
                unit_cost=unit_cost,
                total_cost=quantity * unit_cost
            )
            db.add(inventory)
        
        # トランザクション記録
        transaction = InventoryTransaction(
            transaction_no=f"IN-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
            product_code=data["product_code"],
            warehouse_code=data["warehouse_code"],
            transaction_type="inbound",
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost,
            balance_before=balance_before,
            balance_after=balance_before + quantity,
            reference_no=data.get("reference_no"),
            remarks=data.get("remarks"),
            created_by=current_user.username
        )
        db.add(transaction)
        
        await db.commit()
        
        return {"message": "入庫処理が完了しました", "transaction_no": transaction.transaction_no}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outbound")
async def create_outbound_transaction(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """出庫処理"""
    try:
        query = select(Inventory).where(
            and_(
                Inventory.product_code == data["product_code"],
                Inventory.warehouse_code == data["warehouse_code"]
            )
        )
        result = await db.execute(query)
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="在庫が見つかりません")
        
        quantity = data["quantity"]
        if inventory.available_quantity < quantity:
            raise HTTPException(status_code=400, detail="在庫が不足しています")
        
        balance_before = inventory.quantity
        inventory.quantity -= quantity
        inventory.available_quantity -= quantity
        inventory.total_cost = inventory.quantity * float(inventory.unit_cost or 0)
        
        # トランザクション記録
        transaction = InventoryTransaction(
            transaction_no=f"OUT-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
            inventory_id=inventory.id,
            product_code=data["product_code"],
            warehouse_code=data["warehouse_code"],
            transaction_type="outbound",
            quantity=quantity,
            unit_cost=inventory.unit_cost or 0,
            total_cost=quantity * float(inventory.unit_cost or 0),
            balance_before=balance_before,
            balance_after=inventory.quantity,
            reference_no=data.get("reference_no"),
            remarks=data.get("remarks"),
            created_by=current_user.username
        )
        db.add(transaction)
        
        await db.commit()
        
        return {"message": "出庫処理が完了しました", "transaction_no": transaction.transaction_no}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 在庫アラート ==========

@router.get("/alerts")
async def get_stock_alerts(
    alert_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """在庫アラート一覧取得"""
    query = select(StockAlert)
    
    if alert_type:
        query = query.where(StockAlert.alert_type == alert_type)
    if status:
        query = query.where(StockAlert.status == status)
    
    # 総件数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    query = query.order_by(StockAlert.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [_alert_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ========== ヘルパー関数 ==========

def _inventory_to_dict(inv: Inventory) -> dict:
    return {
        "id": inv.id,
        "product_code": inv.product_code,
        "product_name": inv.product_name,
        "warehouse_code": inv.warehouse_code,
        "warehouse_name": inv.warehouse_name,
        "quantity": inv.quantity,
        "available_quantity": inv.available_quantity,
        "reserved_quantity": inv.reserved_quantity,
        "unit": inv.unit,
        "unit_cost": float(inv.unit_cost or 0),
        "total_cost": float(inv.total_cost or 0),
        "location": inv.location,
        "batch_no": inv.batch_no,
        "min_stock_level": inv.min_stock_level,
        "max_stock_level": inv.max_stock_level,
        "reorder_point": inv.reorder_point,
        "is_active": inv.is_active,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
    }


def _transaction_to_dict(trans: InventoryTransaction) -> dict:
    type_names = {
        "inbound": "入庫",
        "outbound": "出庫",
        "transfer_in": "移動（入）",
        "transfer_out": "移動（出）",
        "adjustment": "調整"
    }
    return {
        "id": trans.id,
        "transaction_no": trans.transaction_no,
        "inventory_id": trans.inventory_id,
        "product_code": trans.product_code,
        "product_name": trans.product_name,
        "warehouse_code": trans.warehouse_code,
        "warehouse_name": trans.warehouse_name,
        "transaction_type": trans.transaction_type,
        "transaction_type_name": type_names.get(trans.transaction_type, trans.transaction_type),
        "quantity": trans.quantity,
        "unit_cost": float(trans.unit_cost or 0),
        "total_cost": float(trans.total_cost or 0),
        "balance_before": trans.balance_before,
        "balance_after": trans.balance_after,
        "reference_no": trans.reference_no,
        "remarks": trans.remarks,
        "created_by": trans.created_by,
        "created_at": trans.created_at.isoformat() if trans.created_at else None
    }


def _alert_to_dict(alert: StockAlert) -> dict:
    type_names = {
        "low_stock": "在庫不足",
        "overstock": "過剰在庫",
        "expiring": "期限切迫",
        "expired": "期限切れ"
    }
    status_names = {
        "active": "未対応",
        "acknowledged": "確認済",
        "resolved": "解決済"
    }
    return {
        "id": alert.id,
        "product_code": alert.product_code,
        "product_name": alert.product_name,
        "warehouse_code": alert.warehouse_code,
        "warehouse_name": alert.warehouse_name,
        "alert_type": alert.alert_type,
        "alert_type_name": type_names.get(alert.alert_type, alert.alert_type),
        "current_quantity": alert.current_quantity,
        "threshold_quantity": alert.threshold_quantity,
        "status": alert.status,
        "status_name": status_names.get(alert.status, alert.status),
        "created_at": alert.created_at.isoformat() if alert.created_at else None
    }
