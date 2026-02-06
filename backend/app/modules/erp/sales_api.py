"""
販売管理APIエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import date, datetime
import uuid

from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.erp.sales_models import (
    SalesOrder, SalesOrderItem, SalesDelivery, SalesDeliveryItem
)

router = APIRouter(prefix="/sales", tags=["Sales"])


# ========== 受注一覧 ==========

@router.get("/orders")
async def get_sales_order_list(
    order_no: Optional[str] = Query(None),
    customer_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """受注一覧取得"""
    query = select(SalesOrder)
    
    if order_no:
        query = query.where(SalesOrder.order_no.like(f"%{order_no}%"))
    if customer_code:
        query = query.where(SalesOrder.customer_code == customer_code)
    if status:
        query = query.where(SalesOrder.status == status)
    if start_date:
        query = query.where(SalesOrder.order_date >= start_date)
    if end_date:
        query = query.where(SalesOrder.order_date <= end_date)
    
    # 総件数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    query = query.order_by(SalesOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [_order_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/orders/stats")
async def get_sales_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """販売統計取得"""
    today = date.today()
    
    # 今月の受注
    month_start = today.replace(day=1)
    monthly_query = select(
        func.count(SalesOrder.id).label("count"),
        func.sum(SalesOrder.total_amount).label("amount")
    ).where(SalesOrder.order_date >= month_start)
    monthly_result = await db.execute(monthly_query)
    monthly = monthly_result.first()
    
    # 出荷待ち
    pending_delivery_query = select(func.count()).where(
        SalesOrder.status.in_(['approved', 'partial_delivered'])
    )
    pending_delivery_result = await db.execute(pending_delivery_query)
    pending_delivery_count = pending_delivery_result.scalar()
    
    # 未回収
    unpaid_query = select(func.sum(SalesOrder.total_amount - SalesOrder.received_amount)).where(
        and_(SalesOrder.payment_status != 'paid', SalesOrder.status != 'cancelled')
    )
    unpaid_result = await db.execute(unpaid_query)
    unpaid_amount = unpaid_result.scalar() or 0
    
    # 今月完了
    completed_query = select(func.count()).where(
        and_(SalesOrder.status == 'completed', SalesOrder.order_date >= month_start)
    )
    completed_result = await db.execute(completed_query)
    completed_count = completed_result.scalar()
    
    return {
        "monthly_order_count": monthly.count or 0,
        "monthly_order_amount": float(monthly.amount or 0),
        "pending_delivery_count": pending_delivery_count or 0,
        "completed_count": completed_count or 0,
        "unpaid_amount": float(unpaid_amount)
    }


@router.get("/orders/{order_id}")
async def get_sales_order_by_id(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """受注詳細取得"""
    query = select(SalesOrder).where(SalesOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    # 明細取得
    items_query = select(SalesOrderItem).where(SalesOrderItem.order_id == order_id)
    items_result = await db.execute(items_query)
    items = items_result.scalars().all()
    
    order_dict = _order_to_dict(order)
    order_dict["items"] = [_order_item_to_dict(item) for item in items]
    
    return order_dict


@router.post("/orders")
async def create_sales_order(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """受注作成"""
    try:
        # 受注番号生成
        order_no = f"SO-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        
        items_data = data.pop("items", [])
        
        order = SalesOrder(
            order_no=order_no,
            customer_code=data["customer_code"],
            customer_name=data.get("customer_name"),
            order_date=data.get("order_date", date.today()),
            expected_delivery_date=data.get("expected_delivery_date"),
            delivery_address=data.get("delivery_address"),
            status="draft",
            sales_person=data.get("sales_person"),
            remarks=data.get("remarks"),
            created_by=current_user.username
        )
        db.add(order)
        await db.flush()
        
        # 明細追加
        subtotal = 0
        for idx, item_data in enumerate(items_data):
            amount = item_data["quantity"] * item_data["unit_price"]
            tax_amount = amount * item_data.get("tax_rate", 10) / 100
            subtotal += amount
            
            item = SalesOrderItem(
                order_id=order.id,
                line_no=idx + 1,
                product_code=item_data["product_code"],
                product_name=item_data.get("product_name"),
                specification=item_data.get("specification"),
                unit=item_data.get("unit", "個"),
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                tax_rate=item_data.get("tax_rate", 10),
                tax_amount=tax_amount,
                amount=amount,
                warehouse_code=item_data.get("warehouse_code"),
                remarks=item_data.get("remarks")
            )
            db.add(item)
        
        # 合計更新
        tax_amount = subtotal * float(order.tax_rate or 10) / 100
        order.subtotal = subtotal
        order.tax_amount = tax_amount
        order.total_amount = subtotal + tax_amount
        
        await db.commit()
        
        return {"message": "受注を作成しました", "order_no": order_no, "id": order.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}")
async def update_sales_order(
    order_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """受注更新"""
    query = select(SalesOrder).where(SalesOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    if order.status not in ['draft']:
        raise HTTPException(status_code=400, detail="この受注は編集できません")
    
    try:
        for key, value in data.items():
            if key != "items" and hasattr(order, key):
                setattr(order, key, value)
        
        await db.commit()
        return {"message": "更新しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/approve")
async def approve_sales_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """受注承認"""
    query = select(SalesOrder).where(SalesOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    if order.status not in ['draft', 'pending']:
        raise HTTPException(status_code=400, detail="この受注は承認できません")
    
    try:
        order.status = 'approved'
        order.approved_by = current_user.username
        order.approved_at = now_jst()
        await db.commit()
        return {"message": "承認しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/cancel")
async def cancel_sales_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """受注キャンセル"""
    query = select(SalesOrder).where(SalesOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    if order.status in ['completed', 'cancelled']:
        raise HTTPException(status_code=400, detail="この受注はキャンセルできません")
    
    try:
        order.status = 'cancelled'
        await db.commit()
        return {"message": "キャンセルしました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 出荷管理 ==========

@router.get("/deliveries")
async def get_sales_delivery_list(
    delivery_no: Optional[str] = Query(None),
    customer_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """出荷一覧取得"""
    query = select(SalesDelivery)
    
    if delivery_no:
        query = query.where(SalesDelivery.delivery_no.like(f"%{delivery_no}%"))
    if customer_code:
        query = query.where(SalesDelivery.customer_code == customer_code)
    if status:
        query = query.where(SalesDelivery.status == status)
    if start_date:
        query = query.where(SalesDelivery.delivery_date >= start_date)
    if end_date:
        query = query.where(SalesDelivery.delivery_date <= end_date)
    
    # 総件数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    query = query.order_by(SalesDelivery.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [_delivery_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/deliveries")
async def create_sales_delivery(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """出荷作成"""
    try:
        # 出荷番号生成
        delivery_no = f"DEL-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        
        items_data = data.pop("items", [])
        
        delivery = SalesDelivery(
            delivery_no=delivery_no,
            order_id=data.get("order_id"),
            order_no=data.get("order_no"),
            customer_code=data["customer_code"],
            customer_name=data.get("customer_name"),
            warehouse_code=data["warehouse_code"],
            warehouse_name=data.get("warehouse_name"),
            delivery_date=data.get("delivery_date", date.today()),
            delivery_address=data.get("delivery_address"),
            status="draft",
            remarks=data.get("remarks"),
            created_by=current_user.username
        )
        db.add(delivery)
        await db.flush()
        
        # 明細追加
        total_quantity = 0
        for item_data in items_data:
            total_quantity += item_data["delivery_quantity"]
            item = SalesDeliveryItem(
                delivery_id=delivery.id,
                order_item_id=item_data.get("order_item_id"),
                product_code=item_data["product_code"],
                product_name=item_data.get("product_name"),
                unit=item_data.get("unit", "個"),
                ordered_quantity=item_data.get("ordered_quantity", 0),
                delivery_quantity=item_data["delivery_quantity"],
                batch_no=item_data.get("batch_no"),
                remarks=item_data.get("remarks")
            )
            db.add(item)
        
        delivery.total_quantity = total_quantity
        
        await db.commit()
        
        return {"message": "出荷を作成しました", "delivery_no": delivery_no, "id": delivery.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deliveries/{delivery_id}/confirm")
async def confirm_sales_delivery(
    delivery_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """出荷確定"""
    query = select(SalesDelivery).where(SalesDelivery.id == delivery_id)
    result = await db.execute(query)
    delivery = result.scalar_one_or_none()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="出荷が見つかりません")
    
    if delivery.status != 'draft':
        raise HTTPException(status_code=400, detail="下書き状態の出荷のみ確定できます")
    
    try:
        delivery.status = 'confirmed'
        delivery.confirmed_by = current_user.username
        delivery.confirmed_at = now_jst()
        await db.commit()
        return {"message": "確定しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== ヘルパー関数 ==========

def _order_to_dict(order: SalesOrder) -> dict:
    status_names = {
        "draft": "下書き",
        "pending": "承認待ち",
        "approved": "承認済",
        "partial_delivered": "一部出荷",
        "completed": "完了",
        "cancelled": "キャンセル"
    }
    payment_status_names = {
        "unpaid": "未入金",
        "partial_paid": "一部入金",
        "paid": "入金済"
    }
    return {
        "id": order.id,
        "order_no": order.order_no,
        "customer_code": order.customer_code,
        "customer_name": order.customer_name,
        "order_date": order.order_date.isoformat() if order.order_date else None,
        "expected_delivery_date": order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
        "delivery_address": order.delivery_address,
        "status": order.status,
        "status_name": status_names.get(order.status, order.status),
        "subtotal": float(order.subtotal or 0),
        "tax_rate": float(order.tax_rate or 0),
        "tax_amount": float(order.tax_amount or 0),
        "total_amount": float(order.total_amount or 0),
        "received_amount": float(order.received_amount or 0),
        "payment_status": order.payment_status,
        "payment_status_name": payment_status_names.get(order.payment_status, order.payment_status),
        "sales_person": order.sales_person,
        "remarks": order.remarks,
        "created_by": order.created_by,
        "approved_by": order.approved_by,
        "approved_at": order.approved_at.isoformat() if order.approved_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None
    }


def _order_item_to_dict(item: SalesOrderItem) -> dict:
    return {
        "id": item.id,
        "line_no": item.line_no,
        "product_code": item.product_code,
        "product_name": item.product_name,
        "specification": item.specification,
        "unit": item.unit,
        "quantity": item.quantity,
        "delivered_quantity": item.delivered_quantity or 0,
        "unit_price": float(item.unit_price or 0),
        "tax_rate": float(item.tax_rate or 0),
        "tax_amount": float(item.tax_amount or 0),
        "amount": float(item.amount or 0),
        "warehouse_code": item.warehouse_code,
        "remarks": item.remarks
    }


def _delivery_to_dict(delivery: SalesDelivery) -> dict:
    status_names = {
        "draft": "下書き",
        "confirmed": "確定済",
        "shipped": "出荷済",
        "completed": "完了"
    }
    return {
        "id": delivery.id,
        "delivery_no": delivery.delivery_no,
        "order_no": delivery.order_no,
        "customer_code": delivery.customer_code,
        "customer_name": delivery.customer_name,
        "warehouse_code": delivery.warehouse_code,
        "warehouse_name": delivery.warehouse_name,
        "delivery_date": delivery.delivery_date.isoformat() if delivery.delivery_date else None,
        "delivery_address": delivery.delivery_address,
        "status": delivery.status,
        "status_name": status_names.get(delivery.status, delivery.status),
        "tracking_no": delivery.tracking_no,
        "carrier": delivery.carrier,
        "total_quantity": delivery.total_quantity,
        "remarks": delivery.remarks,
        "created_by": delivery.created_by,
        "confirmed_by": delivery.confirmed_by,
        "created_at": delivery.created_at.isoformat() if delivery.created_at else None
    }
