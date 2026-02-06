"""
購買管理APIエンドポイント
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
from app.modules.erp.purchase_models import (
    PurchaseOrder, PurchaseOrderItem, PurchaseReceipt, Supplier
)

router = APIRouter(prefix="/purchase", tags=["Purchase"])


# ========== 発注一覧 ==========

@router.get("/orders")
async def get_purchase_order_list(
    order_no: Optional[str] = Query(None),
    supplier_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """発注一覧取得"""
    query = select(PurchaseOrder)
    
    if order_no:
        query = query.where(PurchaseOrder.order_no.like(f"%{order_no}%"))
    if supplier_code:
        query = query.where(PurchaseOrder.supplier_code == supplier_code)
    if status:
        query = query.where(PurchaseOrder.status == status)
    if start_date:
        query = query.where(PurchaseOrder.order_date >= start_date)
    if end_date:
        query = query.where(PurchaseOrder.order_date <= end_date)
    
    # 総件数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    query = query.order_by(PurchaseOrder.created_at.desc())
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
async def get_purchase_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """購買統計取得"""
    today = date.today()
    
    # 今月の発注
    month_start = today.replace(day=1)
    monthly_query = select(
        func.count(PurchaseOrder.id).label("count"),
        func.sum(PurchaseOrder.total_amount).label("amount")
    ).where(PurchaseOrder.order_date >= month_start)
    monthly_result = await db.execute(monthly_query)
    monthly = monthly_result.first()
    
    # 承認待ち
    pending_query = select(func.count()).where(PurchaseOrder.status == 'pending')
    pending_result = await db.execute(pending_query)
    pending_count = pending_result.scalar()
    
    # 入荷待ち
    receipt_query = select(func.count()).where(PurchaseOrder.status.in_(['approved', 'partial_received']))
    receipt_result = await db.execute(receipt_query)
    receipt_count = receipt_result.scalar()
    
    # 未払い
    unpaid_query = select(func.sum(PurchaseOrder.total_amount - PurchaseOrder.paid_amount)).where(
        and_(PurchaseOrder.payment_status != 'paid', PurchaseOrder.status != 'cancelled')
    )
    unpaid_result = await db.execute(unpaid_query)
    unpaid_amount = unpaid_result.scalar() or 0
    
    return {
        "monthly_order_count": monthly.count or 0,
        "monthly_order_amount": float(monthly.amount or 0),
        "pending_approval_count": pending_count or 0,
        "pending_receipt_count": receipt_count or 0,
        "unpaid_amount": float(unpaid_amount)
    }


@router.get("/orders/{order_id}")
async def get_purchase_order_by_id(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """発注詳細取得"""
    query = select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    
    # 明細取得
    items_query = select(PurchaseOrderItem).where(PurchaseOrderItem.order_id == order_id)
    items_result = await db.execute(items_query)
    items = items_result.scalars().all()
    
    order_dict = _order_to_dict(order)
    order_dict["items"] = [_order_item_to_dict(item) for item in items]
    
    return order_dict


@router.post("/orders")
async def create_purchase_order(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """発注作成"""
    try:
        # 発注番号生成
        order_no = f"PO-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        
        items_data = data.pop("items", [])
        
        order = PurchaseOrder(
            order_no=order_no,
            supplier_code=data["supplier_code"],
            supplier_name=data.get("supplier_name"),
            order_date=data.get("order_date", date.today()),
            expected_delivery_date=data.get("expected_delivery_date"),
            warehouse_code=data.get("warehouse_code"),
            warehouse_name=data.get("warehouse_name"),
            status="draft",
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
            
            item = PurchaseOrderItem(
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
                remarks=item_data.get("remarks")
            )
            db.add(item)
        
        # 合計更新
        tax_amount = subtotal * float(order.tax_rate or 10) / 100
        order.subtotal = subtotal
        order.tax_amount = tax_amount
        order.total_amount = subtotal + tax_amount
        
        await db.commit()
        
        return {"message": "発注を作成しました", "order_no": order_no, "id": order.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}")
async def update_purchase_order(
    order_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """発注更新"""
    query = select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    
    if order.status not in ['draft']:
        raise HTTPException(status_code=400, detail="この発注は編集できません")
    
    try:
        for key, value in data.items():
            if key != "items" and hasattr(order, key):
                setattr(order, key, value)
        
        await db.commit()
        return {"message": "更新しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/submit")
async def submit_purchase_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """発注提出（承認申請）"""
    query = select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    
    if order.status != 'draft':
        raise HTTPException(status_code=400, detail="ドラフト状態の発注のみ提出できます")
    
    try:
        order.status = 'pending'
        await db.commit()
        return {"message": "承認申請しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/{order_id}/approve")
async def approve_purchase_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """発注承認"""
    query = select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    
    if order.status != 'pending':
        raise HTTPException(status_code=400, detail="承認待ち状態の発注のみ承認できます")
    
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
async def cancel_purchase_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """発注キャンセル"""
    query = select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    
    if order.status in ['completed', 'cancelled']:
        raise HTTPException(status_code=400, detail="この発注はキャンセルできません")
    
    try:
        order.status = 'cancelled'
        await db.commit()
        return {"message": "キャンセルしました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 仕入先 ==========

@router.get("/suppliers")
async def get_supplier_list(
    keyword: Optional[str] = Query(None),
    supplier_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """仕入先一覧取得"""
    query = select(Supplier)
    
    if keyword:
        query = query.where(
            (Supplier.supplier_code.like(f"%{keyword}%")) |
            (Supplier.supplier_name.like(f"%{keyword}%"))
        )
    if supplier_type:
        query = query.where(Supplier.supplier_type == supplier_type)
    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)
    
    # 総件数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [_supplier_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/suppliers/options")
async def get_supplier_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """仕入先オプション取得"""
    query = select(Supplier).where(Supplier.is_active == True)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return [
        {"id": item.id, "code": item.supplier_code, "name": item.supplier_name}
        for item in items
    ]


@router.get("/suppliers/{supplier_id}")
async def get_supplier_by_id(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """仕入先詳細取得"""
    query = select(Supplier).where(Supplier.id == supplier_id)
    result = await db.execute(query)
    supplier = result.scalar_one_or_none()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="仕入先が見つかりません")
    
    return _supplier_to_dict(supplier)


@router.post("/suppliers")
async def create_supplier(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """仕入先作成"""
    try:
        supplier = Supplier(**data)
        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)
        return _supplier_to_dict(supplier)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """仕入先更新"""
    query = select(Supplier).where(Supplier.id == supplier_id)
    result = await db.execute(query)
    supplier = result.scalar_one_or_none()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="仕入先が見つかりません")
    
    try:
        for key, value in data.items():
            if hasattr(supplier, key):
                setattr(supplier, key, value)
        
        await db.commit()
        await db.refresh(supplier)
        return _supplier_to_dict(supplier)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== ヘルパー関数 ==========

def _order_to_dict(order: PurchaseOrder) -> dict:
    status_names = {
        "draft": "下書き",
        "pending": "承認待ち",
        "approved": "承認済",
        "partial_received": "一部入荷",
        "completed": "完了",
        "cancelled": "キャンセル"
    }
    payment_status_names = {
        "unpaid": "未払い",
        "partial_paid": "一部支払",
        "paid": "支払済"
    }
    return {
        "id": order.id,
        "order_no": order.order_no,
        "supplier_code": order.supplier_code,
        "supplier_name": order.supplier_name,
        "order_date": order.order_date.isoformat() if order.order_date else None,
        "expected_delivery_date": order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
        "warehouse_code": order.warehouse_code,
        "warehouse_name": order.warehouse_name,
        "status": order.status,
        "status_name": status_names.get(order.status, order.status),
        "subtotal": float(order.subtotal or 0),
        "tax_rate": float(order.tax_rate or 0),
        "tax_amount": float(order.tax_amount or 0),
        "total_amount": float(order.total_amount or 0),
        "paid_amount": float(order.paid_amount or 0),
        "payment_status": order.payment_status,
        "payment_status_name": payment_status_names.get(order.payment_status, order.payment_status),
        "remarks": order.remarks,
        "created_by": order.created_by,
        "approved_by": order.approved_by,
        "approved_at": order.approved_at.isoformat() if order.approved_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None
    }


def _order_item_to_dict(item: PurchaseOrderItem) -> dict:
    return {
        "id": item.id,
        "line_no": item.line_no,
        "product_code": item.product_code,
        "product_name": item.product_name,
        "specification": item.specification,
        "unit": item.unit,
        "quantity": item.quantity,
        "received_quantity": item.received_quantity or 0,
        "unit_price": float(item.unit_price or 0),
        "tax_rate": float(item.tax_rate or 0),
        "tax_amount": float(item.tax_amount or 0),
        "amount": float(item.amount or 0),
        "remarks": item.remarks
    }


def _supplier_to_dict(sup: Supplier) -> dict:
    type_names = {
        "manufacturer": "メーカー",
        "distributor": "卸売",
        "service": "サービス",
        "other": "その他"
    }
    return {
        "id": sup.id,
        "supplier_code": sup.supplier_code,
        "supplier_name": sup.supplier_name,
        "supplier_name_kana": sup.supplier_name_kana,
        "supplier_type": sup.supplier_type,
        "supplier_type_name": type_names.get(sup.supplier_type, sup.supplier_type),
        "category": sup.category,
        "tax_id": sup.tax_id,
        "postal_code": sup.postal_code,
        "address": sup.address,
        "phone": sup.phone,
        "fax": sup.fax,
        "email": sup.email,
        "website": sup.website,
        "payment_term": sup.payment_term,
        "currency": sup.currency,
        "credit_limit": float(sup.credit_limit or 0),
        "rating": sup.rating,
        "is_active": sup.is_active,
        "remarks": sup.remarks,
        "created_at": sup.created_at.isoformat() if sup.created_at else None
    }
