"""
販売管理APIエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import date, datetime, timedelta
import calendar
import uuid

from sqlalchemy.types import Numeric

from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.erp.models import OrderDaily
from app.modules.erp.sales_models import (
    SalesOrder, SalesOrderItem, SalesDelivery, SalesDeliveryItem,
    SalesQuotation, SalesQuotationItem,
    SalesInvoice, SalesInvoiceItem,
    SalesCredit, SalesContractPricing, SalesForecast, SalesRecording,
    SalesReturn, SalesReturnItem,
)
from app.modules.master.models import Product

router = APIRouter(prefix="/sales", tags=["Sales"])


def _mysql_errno_from_sqlalchemy(exc: BaseException) -> Optional[int]:
    orig = getattr(exc, "orig", None)
    if orig is None:
        return None
    args = getattr(orig, "args", None)
    if isinstance(args, tuple) and len(args) >= 1:
        try:
            return int(args[0])
        except (TypeError, ValueError):
            return None
    return None


def _is_missing_table(exc: BaseException, table_name: str) -> bool:
    if _mysql_errno_from_sqlalchemy(exc) == 1146:
        return True
    msg = str(exc).lower()
    t = table_name.lower()
    return t in msg and (
        "doesn't exist" in msg
        or "does not exist" in msg
        or "doesnt exist" in msg
        or "unknown table" in msg
        or "不存在" in str(exc)
    )


def _dashboard_order_daily_exclude_name_contains_kakou():
    """ダッシュボード用 order_daily 集計: 表示用製品名に「加工」を含む行を除外。

    `_monthly_order_daily_aggregates` の売上（Σ confirmed_units×単価）と確定本数の双方に同一条件で適用する。
    明細の product_name を優先し、無い場合は products マスタを参照する。
    """
    display_name = func.coalesce(OrderDaily.product_name, Product.product_name, "")
    return ~display_name.like("%加工%")


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

    try:
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(SalesOrder.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return {
            "items": [_order_to_dict(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except SQLAlchemyError as e:
        if _is_missing_table(e, "sales_order"):
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        raise


async def _monthly_order_daily_aggregates(
    db: AsyncSession, month_start: date, month_end: date
) -> tuple[float, int]:
    """当月 order_daily: 売上金額と確定本数を一括集計。

    - 売上: Σ(confirmed_units × unit_price)
    - 本数: Σ(confirmed_units)
    - 表示用製品名に「加工」を含む行は除外（ダッシュボード「今月売上」「今月受注」で一致）
    """
    line_amt = func.coalesce(OrderDaily.confirmed_units, 0) * func.coalesce(
        cast(Product.unit_price, Numeric(18, 4)), 0
    )
    units_expr = func.coalesce(OrderDaily.confirmed_units, 0)
    q = (
        select(
            func.coalesce(func.sum(line_amt), 0).label("amount"),
            func.coalesce(func.sum(units_expr), 0).label("units"),
        )
        .select_from(OrderDaily)
        .outerjoin(Product, Product.product_cd == OrderDaily.product_cd)
        .where(
            and_(
                OrderDaily.date >= month_start,
                OrderDaily.date <= month_end,
                _dashboard_order_daily_exclude_name_contains_kakou(),
            )
        )
    )
    r = await db.execute(q)
    row = r.one()
    amt = float(row.amount or 0)
    u = row.units
    try:
        units = int(float(u)) if u is not None else 0
    except (TypeError, ValueError):
        units = 0
    return amt, units


@router.get("/orders/stats")
async def get_sales_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """販売統計取得"""
    today = date.today()
    month_start = today.replace(day=1)
    last_d = calendar.monthrange(today.year, today.month)[1]
    month_end = date(today.year, today.month, last_d)

    empty_stats = {
        "monthly_order_count": 0,
        "monthly_order_amount": 0.0,
        "monthly_confirmed_units": 0,
        "pending_delivery_count": 0,
        "completed_count": 0,
        "unpaid_amount": 0.0,
    }

    monthly_order_amount = 0.0
    monthly_confirmed_units = 0
    try:
        monthly_order_amount, monthly_confirmed_units = await _monthly_order_daily_aggregates(
            db, month_start, month_end
        )
    except SQLAlchemyError as e:
        if _is_missing_table(e, "order_daily") or _is_missing_table(e, "products"):
            monthly_order_amount = 0.0
            monthly_confirmed_units = 0
        else:
            raise

    try:
        # 今月の受注件数（sales_order）
        monthly_query = select(func.count(SalesOrder.id).label("count")).where(
            SalesOrder.order_date >= month_start
        )
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
            "monthly_order_amount": monthly_order_amount,
            "monthly_confirmed_units": monthly_confirmed_units,
            "pending_delivery_count": pending_delivery_count or 0,
            "completed_count": completed_count or 0,
            "unpaid_amount": float(unpaid_amount),
        }
    except SQLAlchemyError as e:
        # 未执行 ERP 迁移时 sales_order 等表可能不存在（今月売上は order_daily ベースの値を返す）
        if _is_missing_table(e, "sales_order"):
            return {
                **empty_stats,
                "monthly_order_amount": monthly_order_amount,
                "monthly_confirmed_units": monthly_confirmed_units,
            }
        raise


@router.get("/orders/daily-confirmed-series")
async def get_daily_confirmed_series(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
    start_date: Optional[date] = Query(None, description="開始日（省略時 JST 今日の 14 日前）"),
    end_date: Optional[date] = Query(None, description="終了日（省略時 JST 今日の 7 日後）"),
):
    """日別受注確定本数（order_daily.confirmed_units の日付合計）。既定レンジ：過去2週＋今日＋将来1週。

    表示用製品名（明細 product_name、無ければ products）に「加工」を含む行は集計から除外する。
    """
    today = now_jst().date()
    if start_date is None:
        start_date = today - timedelta(days=14)
    if end_date is None:
        end_date = today + timedelta(days=7)
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    rows_map: dict[date, int] = {}
    try:
        units_expr = func.coalesce(OrderDaily.confirmed_units, 0)
        q = (
            select(OrderDaily.date, func.coalesce(func.sum(units_expr), 0).label("units"))
            .select_from(OrderDaily)
            .outerjoin(Product, Product.product_cd == OrderDaily.product_cd)
            .where(
                and_(
                    OrderDaily.date >= start_date,
                    OrderDaily.date <= end_date,
                    _dashboard_order_daily_exclude_name_contains_kakou(),
                )
            )
            .group_by(OrderDaily.date)
            .order_by(OrderDaily.date)
        )
        r = await db.execute(q)
        for row in r.all():
            u = row.units
            try:
                v = int(float(u)) if u is not None else 0
            except (TypeError, ValueError):
                v = 0
            rows_map[row.date] = v
    except SQLAlchemyError as e:
        if _is_missing_table(e, "order_daily"):
            rows_map = {}
        else:
            raise

    items = []
    d = start_date
    while d <= end_date:
        items.append({"date": d.isoformat(), "confirmed_units": rows_map.get(d, 0)})
        d += timedelta(days=1)

    return {
        "as_of_date": today.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "items": items,
    }


@router.get("/orders/{order_id}")
async def get_sales_order_by_id(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """受注詳細取得"""
    try:
        query = select(SalesOrder).where(SalesOrder.id == order_id)
        result = await db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="受注が見つかりません")

        items_query = select(SalesOrderItem).where(SalesOrderItem.order_id == order_id)
        items_result = await db.execute(items_query)
        items = items_result.scalars().all()

        order_dict = _order_to_dict(order)
        order_dict["items"] = [_order_item_to_dict(item) for item in items]

        return order_dict
    except SQLAlchemyError as e:
        if _is_missing_table(e, "sales_order") or _is_missing_table(e, "sales_order_item"):
            raise HTTPException(
                status_code=503,
                detail="sales_order テーブルがありません。マイグレーション backend/database/migrations/248_ensure_sales_core_tables.sql を実行してください。",
            )
        raise


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

    try:
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(SalesDelivery.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return {
            "items": [_delivery_to_dict(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except SQLAlchemyError as e:
        if _is_missing_table(e, "sales_delivery"):
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        raise


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


# ========== 見積管理 (Quotation Management) ==========


def _quotation_to_dict(q: SalesQuotation) -> dict:
    status_names = {
        "draft": "下書き",
        "sent": "送付済",
        "accepted": "受諾",
        "rejected": "却下",
        "expired": "期限切れ",
        "converted": "受注変換済",
    }
    return {
        "id": q.id,
        "quotation_no": q.quotation_no,
        "customer_code": q.customer_code,
        "customer_name": q.customer_name,
        "quotation_date": q.quotation_date.isoformat() if q.quotation_date else None,
        "valid_until": q.valid_until.isoformat() if q.valid_until else None,
        "subject": q.subject,
        "status": q.status,
        "status_name": status_names.get(q.status, q.status),
        "currency": q.currency,
        "subtotal": float(q.subtotal or 0),
        "tax_rate": float(q.tax_rate or 0),
        "tax_amount": float(q.tax_amount or 0),
        "discount_rate": float(q.discount_rate or 0),
        "discount_amount": float(q.discount_amount or 0),
        "total_amount": float(q.total_amount or 0),
        "delivery_terms": q.delivery_terms,
        "payment_terms": q.payment_terms,
        "delivery_address": q.delivery_address,
        "sales_person": q.sales_person,
        "remarks": q.remarks,
        "sent_at": q.sent_at.isoformat() if q.sent_at else None,
        "converted_order_id": q.converted_order_id,
        "created_by": q.created_by,
        "created_at": q.created_at.isoformat() if q.created_at else None,
    }


def _quotation_item_to_dict(item: SalesQuotationItem) -> dict:
    return {
        "id": item.id,
        "line_no": item.line_no,
        "product_code": item.product_code,
        "product_name": item.product_name,
        "specification": item.specification,
        "unit": item.unit,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price or 0),
        "tax_rate": float(item.tax_rate or 0),
        "tax_amount": float(item.tax_amount or 0),
        "amount": float(item.amount or 0),
        "remarks": item.remarks,
    }


@router.get("/quotations")
async def get_quotation_list(
    customer_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """見積一覧取得"""
    query = select(SalesQuotation)

    if customer_code:
        query = query.where(SalesQuotation.customer_code == customer_code)
    if status:
        query = query.where(SalesQuotation.status == status)
    if start_date:
        query = query.where(SalesQuotation.quotation_date >= start_date)
    if end_date:
        query = query.where(SalesQuotation.quotation_date <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(SalesQuotation.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [_quotation_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/quotations/{quotation_id}")
async def get_quotation_by_id(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """見積詳細取得"""
    result = await db.execute(
        select(SalesQuotation).where(SalesQuotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")

    items_result = await db.execute(
        select(SalesQuotationItem).where(SalesQuotationItem.quotation_id == quotation_id)
    )
    items = items_result.scalars().all()

    data = _quotation_to_dict(quotation)
    data["items"] = [_quotation_item_to_dict(i) for i in items]
    return data


@router.post("/quotations")
async def create_quotation(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """見積作成"""
    try:
        quotation_no = f"QT-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        items_data = data.pop("items", [])

        quotation = SalesQuotation(
            quotation_no=quotation_no,
            customer_code=data["customer_code"],
            customer_name=data.get("customer_name"),
            quotation_date=data.get("quotation_date", date.today()),
            valid_until=data.get("valid_until"),
            subject=data.get("subject"),
            status="draft",
            currency=data.get("currency", "JPY"),
            delivery_terms=data.get("delivery_terms"),
            payment_terms=data.get("payment_terms"),
            delivery_address=data.get("delivery_address"),
            sales_person=data.get("sales_person"),
            remarks=data.get("remarks"),
            created_by=current_user.username,
        )
        db.add(quotation)
        await db.flush()

        subtotal = 0
        for idx, item_data in enumerate(items_data):
            amount = item_data["quantity"] * item_data["unit_price"]
            tax_amount = amount * item_data.get("tax_rate", 10) / 100
            subtotal += amount

            item = SalesQuotationItem(
                quotation_id=quotation.id,
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
                remarks=item_data.get("remarks"),
            )
            db.add(item)

        tax_amount = subtotal * float(quotation.tax_rate or 10) / 100
        discount_amount = subtotal * float(data.get("discount_rate", 0)) / 100
        quotation.subtotal = subtotal
        quotation.tax_amount = tax_amount
        quotation.discount_rate = data.get("discount_rate", 0)
        quotation.discount_amount = discount_amount
        quotation.total_amount = subtotal - discount_amount + tax_amount

        await db.commit()
        return {"message": "見積を作成しました", "quotation_no": quotation_no, "id": quotation.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/quotations/{quotation_id}")
async def update_quotation(
    quotation_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """見積更新"""
    result = await db.execute(
        select(SalesQuotation).where(SalesQuotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    if quotation.status not in ["draft"]:
        raise HTTPException(status_code=400, detail="下書き状態の見積のみ編集できます")

    try:
        for key, value in data.items():
            if key != "items" and hasattr(quotation, key):
                setattr(quotation, key, value)
        await db.commit()
        return {"message": "更新しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quotations/{quotation_id}/send")
async def send_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """見積送付"""
    result = await db.execute(
        select(SalesQuotation).where(SalesQuotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    if quotation.status not in ["draft"]:
        raise HTTPException(status_code=400, detail="下書き状態の見積のみ送付できます")

    try:
        quotation.status = "sent"
        quotation.sent_at = now_jst()
        await db.commit()
        return {"message": "見積を送付しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quotations/{quotation_id}/convert-to-order")
async def convert_quotation_to_order(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """見積から受注へ変換"""
    result = await db.execute(
        select(SalesQuotation).where(SalesQuotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    if quotation.status in ["converted", "rejected", "expired"]:
        raise HTTPException(status_code=400, detail="この見積は受注に変換できません")

    try:
        items_result = await db.execute(
            select(SalesQuotationItem).where(SalesQuotationItem.quotation_id == quotation_id)
        )
        q_items = items_result.scalars().all()

        order_no = f"SO-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        order = SalesOrder(
            order_no=order_no,
            customer_code=quotation.customer_code,
            customer_name=quotation.customer_name,
            order_date=date.today(),
            expected_delivery_date=None,
            delivery_address=quotation.delivery_address,
            status="draft",
            currency=quotation.currency,
            subtotal=quotation.subtotal,
            tax_rate=quotation.tax_rate,
            tax_amount=quotation.tax_amount,
            discount_rate=quotation.discount_rate,
            discount_amount=quotation.discount_amount,
            total_amount=quotation.total_amount,
            sales_person=quotation.sales_person,
            payment_term=quotation.payment_terms,
            remarks=f"見積 {quotation.quotation_no} から変換",
            created_by=current_user.username,
        )
        db.add(order)
        await db.flush()

        for qi in q_items:
            oi = SalesOrderItem(
                order_id=order.id,
                line_no=qi.line_no,
                product_code=qi.product_code,
                product_name=qi.product_name,
                specification=qi.specification,
                unit=qi.unit,
                quantity=qi.quantity,
                unit_price=qi.unit_price,
                tax_rate=qi.tax_rate,
                tax_amount=qi.tax_amount,
                amount=qi.amount,
                remarks=qi.remarks,
            )
            db.add(oi)

        quotation.status = "converted"
        quotation.converted_order_id = order.id
        await db.commit()
        return {
            "message": "受注に変換しました",
            "order_no": order_no,
            "order_id": order.id,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/quotations/{quotation_id}")
async def delete_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """見積削除（下書きのみ）"""
    result = await db.execute(
        select(SalesQuotation).where(SalesQuotation.id == quotation_id)
    )
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise HTTPException(status_code=404, detail="見積が見つかりません")
    if quotation.status != "draft":
        raise HTTPException(status_code=400, detail="下書き状態の見積のみ削除できます")

    try:
        await db.delete(quotation)
        await db.commit()
        return {"message": "見積を削除しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 請求書発行 (Invoice Management) ==========


def _invoice_to_dict(inv: SalesInvoice) -> dict:
    status_names = {
        "draft": "下書き",
        "issued": "発行済",
        "paid": "入金済",
        "overdue": "延滞",
        "cancelled": "キャンセル",
    }
    return {
        "id": inv.id,
        "invoice_no": inv.invoice_no,
        "order_id": inv.order_id,
        "order_no": inv.order_no,
        "customer_code": inv.customer_code,
        "customer_name": inv.customer_name,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "status": inv.status,
        "status_name": status_names.get(inv.status, inv.status),
        "currency": inv.currency,
        "subtotal": float(inv.subtotal or 0),
        "tax_rate": float(inv.tax_rate or 0),
        "tax_amount": float(inv.tax_amount or 0),
        "total_amount": float(inv.total_amount or 0),
        "paid_amount": float(inv.paid_amount or 0),
        "payment_method": inv.payment_method,
        "payment_terms": inv.payment_terms,
        "billing_address": inv.billing_address,
        "remarks": inv.remarks,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "issued_by": inv.issued_by,
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        "created_by": inv.created_by,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


def _invoice_item_to_dict(item: SalesInvoiceItem) -> dict:
    return {
        "id": item.id,
        "line_no": item.line_no,
        "product_code": item.product_code,
        "product_name": item.product_name,
        "specification": item.specification,
        "unit": item.unit,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price or 0),
        "tax_rate": float(item.tax_rate or 0),
        "tax_amount": float(item.tax_amount or 0),
        "amount": float(item.amount or 0),
        "remarks": item.remarks,
    }


@router.get("/invoices")
async def get_invoice_list(
    customer_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """請求書一覧取得"""
    query = select(SalesInvoice)

    if customer_code:
        query = query.where(SalesInvoice.customer_code == customer_code)
    if status:
        query = query.where(SalesInvoice.status == status)
    if start_date:
        query = query.where(SalesInvoice.invoice_date >= start_date)
    if end_date:
        query = query.where(SalesInvoice.invoice_date <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(SalesInvoice.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [_invoice_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice_by_id(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """請求書詳細取得"""
    result = await db.execute(
        select(SalesInvoice).where(SalesInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求書が見つかりません")

    items_result = await db.execute(
        select(SalesInvoiceItem).where(SalesInvoiceItem.invoice_id == invoice_id)
    )
    items = items_result.scalars().all()

    data = _invoice_to_dict(invoice)
    data["items"] = [_invoice_item_to_dict(i) for i in items]
    return data


@router.post("/invoices")
async def create_invoice(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """請求書作成"""
    try:
        invoice_no = f"INV-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        items_data = data.pop("items", [])

        invoice = SalesInvoice(
            invoice_no=invoice_no,
            order_id=data.get("order_id"),
            order_no=data.get("order_no"),
            customer_code=data["customer_code"],
            customer_name=data.get("customer_name"),
            invoice_date=data.get("invoice_date", date.today()),
            due_date=data.get("due_date"),
            status="draft",
            currency=data.get("currency", "JPY"),
            payment_method=data.get("payment_method"),
            payment_terms=data.get("payment_terms"),
            billing_address=data.get("billing_address"),
            remarks=data.get("remarks"),
            created_by=current_user.username,
        )
        db.add(invoice)
        await db.flush()

        subtotal = 0
        for idx, item_data in enumerate(items_data):
            amount = item_data["quantity"] * item_data["unit_price"]
            tax_amount = amount * item_data.get("tax_rate", 10) / 100
            subtotal += amount

            item = SalesInvoiceItem(
                invoice_id=invoice.id,
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
                remarks=item_data.get("remarks"),
            )
            db.add(item)

        tax_amount = subtotal * float(invoice.tax_rate or 10) / 100
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = subtotal + tax_amount

        await db.commit()
        return {"message": "請求書を作成しました", "invoice_no": invoice_no, "id": invoice.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoices/{invoice_id}/issue")
async def issue_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """請求書発行"""
    result = await db.execute(
        select(SalesInvoice).where(SalesInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求書が見つかりません")
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="下書き状態の請求書のみ発行できます")

    try:
        invoice.status = "issued"
        invoice.issued_at = now_jst()
        invoice.issued_by = current_user.username
        await db.commit()
        return {"message": "請求書を発行しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: int,
    data: dict = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """請求書入金記録"""
    if data is None:
        data = {}

    result = await db.execute(
        select(SalesInvoice).where(SalesInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求書が見つかりません")
    if invoice.status not in ["issued", "overdue"]:
        raise HTTPException(status_code=400, detail="発行済または延滞の請求書のみ入金記録できます")

    try:
        paid = data.get("paid_amount", float(invoice.total_amount or 0))
        invoice.paid_amount = paid
        invoice.status = "paid"
        invoice.paid_at = now_jst()
        await db.commit()
        return {"message": "入金を記録しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """請求書削除（下書きのみ）"""
    result = await db.execute(
        select(SalesInvoice).where(SalesInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="請求書が見つかりません")
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="下書き状態の請求書のみ削除できます")

    try:
        await db.delete(invoice)
        await db.commit()
        return {"message": "請求書を削除しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 与信管理 (Credit Management) ==========


def _credit_to_dict(c: SalesCredit) -> dict:
    status_names = {
        "active": "有効",
        "suspended": "停止中",
        "blocked": "ブロック",
    }
    return {
        "id": c.id,
        "customer_code": c.customer_code,
        "customer_name": c.customer_name,
        "credit_limit": float(c.credit_limit or 0),
        "used_amount": float(c.used_amount or 0),
        "available_amount": float(c.available_amount or 0),
        "status": c.status,
        "status_name": status_names.get(c.status, c.status),
        "risk_level": c.risk_level,
        "last_review_date": c.last_review_date.isoformat() if c.last_review_date else None,
        "next_review_date": c.next_review_date.isoformat() if c.next_review_date else None,
        "remarks": c.remarks,
        "created_by": c.created_by,
        "updated_by": c.updated_by,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("/credits")
async def get_credit_list(
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """与信一覧取得"""
    query = select(SalesCredit)

    if status:
        query = query.where(SalesCredit.status == status)
    if risk_level:
        query = query.where(SalesCredit.risk_level == risk_level)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(SalesCredit.customer_code)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [_credit_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/credits/check/{customer_code}")
async def check_customer_credit(
    customer_code: str,
    order_amount: float = Query(0, description="確認する注文金額"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """与信チェック（注文可否確認）"""
    result = await db.execute(
        select(SalesCredit).where(SalesCredit.customer_code == customer_code)
    )
    credit = result.scalar_one_or_none()
    if not credit:
        raise HTTPException(status_code=404, detail="与信情報が見つかりません")

    available = float(credit.credit_limit or 0) - float(credit.used_amount or 0)
    can_proceed = credit.status == "active" and available >= order_amount

    return {
        "customer_code": customer_code,
        "credit_limit": float(credit.credit_limit or 0),
        "used_amount": float(credit.used_amount or 0),
        "available_amount": available,
        "order_amount": order_amount,
        "can_proceed": can_proceed,
        "status": credit.status,
        "risk_level": credit.risk_level,
    }


@router.get("/credits/{customer_code}")
async def get_customer_credit(
    customer_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """顧客与信詳細取得"""
    result = await db.execute(
        select(SalesCredit).where(SalesCredit.customer_code == customer_code)
    )
    credit = result.scalar_one_or_none()
    if not credit:
        raise HTTPException(status_code=404, detail="与信情報が見つかりません")
    return _credit_to_dict(credit)


@router.post("/credits")
async def create_or_update_credit(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """与信作成・更新"""
    customer_code = data.get("customer_code")
    if not customer_code:
        raise HTTPException(status_code=400, detail="顧客コードは必須です")

    try:
        result = await db.execute(
            select(SalesCredit).where(SalesCredit.customer_code == customer_code)
        )
        credit = result.scalar_one_or_none()

        if credit:
            for key, value in data.items():
                if hasattr(credit, key):
                    setattr(credit, key, value)
            credit.updated_by = current_user.username
            msg = "与信情報を更新しました"
        else:
            credit = SalesCredit(
                customer_code=customer_code,
                customer_name=data.get("customer_name"),
                credit_limit=data.get("credit_limit", 0),
                used_amount=data.get("used_amount", 0),
                available_amount=data.get("credit_limit", 0) - data.get("used_amount", 0),
                status=data.get("status", "active"),
                risk_level=data.get("risk_level", "normal"),
                last_review_date=data.get("last_review_date"),
                next_review_date=data.get("next_review_date"),
                remarks=data.get("remarks"),
                created_by=current_user.username,
                updated_by=current_user.username,
            )
            db.add(credit)
            msg = "与信情報を作成しました"

        await db.commit()
        return {"message": msg, "customer_code": customer_code}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/credits/{customer_code}")
async def update_credit_limit(
    customer_code: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """与信限度額更新"""
    result = await db.execute(
        select(SalesCredit).where(SalesCredit.customer_code == customer_code)
    )
    credit = result.scalar_one_or_none()
    if not credit:
        raise HTTPException(status_code=404, detail="与信情報が見つかりません")

    try:
        if "credit_limit" in data:
            credit.credit_limit = data["credit_limit"]
            credit.available_amount = data["credit_limit"] - float(credit.used_amount or 0)
        for key in ("status", "risk_level", "remarks", "next_review_date"):
            if key in data:
                setattr(credit, key, data[key])
        credit.last_review_date = date.today()
        credit.updated_by = current_user.username
        await db.commit()
        return {"message": "与信限度額を更新しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 契約単価管理 (Contract Pricing) ==========


def _contract_pricing_to_dict(cp: SalesContractPricing) -> dict:
    status_names = {
        "active": "有効",
        "expired": "期限切れ",
        "cancelled": "キャンセル",
    }
    return {
        "id": cp.id,
        "customer_code": cp.customer_code,
        "customer_name": cp.customer_name,
        "product_code": cp.product_code,
        "product_name": cp.product_name,
        "unit_price": float(cp.unit_price or 0),
        "currency": cp.currency,
        "min_quantity": cp.min_quantity,
        "effective_from": cp.effective_from.isoformat() if cp.effective_from else None,
        "effective_to": cp.effective_to.isoformat() if cp.effective_to else None,
        "status": cp.status,
        "status_name": status_names.get(cp.status, cp.status),
        "remarks": cp.remarks,
        "created_by": cp.created_by,
        "created_at": cp.created_at.isoformat() if cp.created_at else None,
    }


@router.get("/contract-pricing")
async def get_contract_pricing_list(
    customer_code: Optional[str] = Query(None),
    product_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """契約単価一覧取得"""
    query = select(SalesContractPricing)

    if customer_code:
        query = query.where(SalesContractPricing.customer_code == customer_code)
    if product_code:
        query = query.where(SalesContractPricing.product_code == product_code)
    if status:
        query = query.where(SalesContractPricing.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(SalesContractPricing.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [_contract_pricing_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/contract-pricing/lookup")
async def lookup_contract_price(
    customer_code: str = Query(..., description="顧客コード"),
    product_code: str = Query(..., description="品番"),
    quantity: int = Query(1, ge=1, description="数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """契約単価ルックアップ（顧客＋品番で有効な単価を検索）"""
    today = date.today()
    query = (
        select(SalesContractPricing)
        .where(
            and_(
                SalesContractPricing.customer_code == customer_code,
                SalesContractPricing.product_code == product_code,
                SalesContractPricing.status == "active",
                SalesContractPricing.effective_from <= today,
                (SalesContractPricing.effective_to >= today)
                | (SalesContractPricing.effective_to.is_(None)),
                SalesContractPricing.min_quantity <= quantity,
            )
        )
        .order_by(SalesContractPricing.min_quantity.desc())
        .limit(1)
    )
    result = await db.execute(query)
    pricing = result.scalar_one_or_none()

    if not pricing:
        return {
            "found": False,
            "customer_code": customer_code,
            "product_code": product_code,
            "unit_price": None,
            "message": "該当する契約単価が見つかりません",
        }

    return {
        "found": True,
        "customer_code": customer_code,
        "product_code": product_code,
        "unit_price": float(pricing.unit_price or 0),
        "currency": pricing.currency,
        "min_quantity": pricing.min_quantity,
        "effective_from": pricing.effective_from.isoformat() if pricing.effective_from else None,
        "effective_to": pricing.effective_to.isoformat() if pricing.effective_to else None,
        "pricing_id": pricing.id,
    }


@router.post("/contract-pricing")
async def create_contract_pricing(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """契約単価作成"""
    try:
        pricing = SalesContractPricing(
            customer_code=data["customer_code"],
            customer_name=data.get("customer_name"),
            product_code=data["product_code"],
            product_name=data.get("product_name"),
            unit_price=data["unit_price"],
            currency=data.get("currency", "JPY"),
            min_quantity=data.get("min_quantity", 1),
            effective_from=data["effective_from"],
            effective_to=data.get("effective_to"),
            status=data.get("status", "active"),
            remarks=data.get("remarks"),
            created_by=current_user.username,
        )
        db.add(pricing)
        await db.commit()
        return {"message": "契約単価を作成しました", "id": pricing.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/contract-pricing/{pricing_id}")
async def update_contract_pricing(
    pricing_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """契約単価更新"""
    result = await db.execute(
        select(SalesContractPricing).where(SalesContractPricing.id == pricing_id)
    )
    pricing = result.scalar_one_or_none()
    if not pricing:
        raise HTTPException(status_code=404, detail="契約単価が見つかりません")

    try:
        for key, value in data.items():
            if hasattr(pricing, key):
                setattr(pricing, key, value)
        await db.commit()
        return {"message": "契約単価を更新しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/contract-pricing/{pricing_id}")
async def delete_contract_pricing(
    pricing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """契約単価削除"""
    result = await db.execute(
        select(SalesContractPricing).where(SalesContractPricing.id == pricing_id)
    )
    pricing = result.scalar_one_or_none()
    if not pricing:
        raise HTTPException(status_code=404, detail="契約単価が見つかりません")

    try:
        await db.delete(pricing)
        await db.commit()
        return {"message": "契約単価を削除しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 内示・フォーキャスト (Forecast) ==========


def _forecast_to_dict(f: SalesForecast) -> dict:
    status_names = {
        "draft": "下書き",
        "submitted": "提出済",
        "confirmed": "確定",
        "revised": "修正済",
    }
    return {
        "id": f.id,
        "customer_code": f.customer_code,
        "customer_name": f.customer_name,
        "product_code": f.product_code,
        "product_name": f.product_name,
        "forecast_month": f.forecast_month,
        "forecast_quantity": f.forecast_quantity,
        "confirmed_quantity": f.confirmed_quantity,
        "unit_price": float(f.unit_price or 0) if f.unit_price else None,
        "forecast_amount": float(f.forecast_amount or 0),
        "status": f.status,
        "status_name": status_names.get(f.status, f.status),
        "confirmed_at": f.confirmed_at.isoformat() if f.confirmed_at else None,
        "confirmed_by": f.confirmed_by,
        "remarks": f.remarks,
        "created_by": f.created_by,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


@router.get("/forecasts")
async def get_forecast_list(
    customer_code: Optional[str] = Query(None),
    product_code: Optional[str] = Query(None),
    month: Optional[str] = Query(None, description="対象年月 (YYYY-MM)"),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """フォーキャスト一覧取得"""
    query = select(SalesForecast)

    if customer_code:
        query = query.where(SalesForecast.customer_code == customer_code)
    if product_code:
        query = query.where(SalesForecast.product_code == product_code)
    if month:
        query = query.where(SalesForecast.forecast_month == month)
    if status:
        query = query.where(SalesForecast.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(SalesForecast.forecast_month.desc(), SalesForecast.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [_forecast_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/forecasts")
async def create_or_update_forecast(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """フォーキャスト作成・更新"""
    customer_code = data.get("customer_code")
    product_code = data.get("product_code")
    forecast_month = data.get("forecast_month")

    if not all([customer_code, product_code, forecast_month]):
        raise HTTPException(
            status_code=400, detail="顧客コード、品番、対象年月は必須です"
        )

    try:
        result = await db.execute(
            select(SalesForecast).where(
                and_(
                    SalesForecast.customer_code == customer_code,
                    SalesForecast.product_code == product_code,
                    SalesForecast.forecast_month == forecast_month,
                )
            )
        )
        forecast = result.scalar_one_or_none()

        quantity = data.get("forecast_quantity", 0)
        unit_price = data.get("unit_price", 0)
        forecast_amount = quantity * unit_price if unit_price else 0

        if forecast:
            forecast.forecast_quantity = quantity
            forecast.unit_price = unit_price
            forecast.forecast_amount = forecast_amount
            forecast.customer_name = data.get("customer_name", forecast.customer_name)
            forecast.product_name = data.get("product_name", forecast.product_name)
            forecast.remarks = data.get("remarks", forecast.remarks)
            if forecast.status == "confirmed":
                forecast.status = "revised"
            msg = "フォーキャストを更新しました"
        else:
            forecast = SalesForecast(
                customer_code=customer_code,
                customer_name=data.get("customer_name"),
                product_code=product_code,
                product_name=data.get("product_name"),
                forecast_month=forecast_month,
                forecast_quantity=quantity,
                unit_price=unit_price,
                forecast_amount=forecast_amount,
                status="draft",
                remarks=data.get("remarks"),
                created_by=current_user.username,
            )
            db.add(forecast)
            msg = "フォーキャストを作成しました"

        await db.commit()
        return {"message": msg, "id": forecast.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/forecasts/{forecast_id}")
async def update_forecast(
    forecast_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """フォーキャスト更新"""
    result = await db.execute(
        select(SalesForecast).where(SalesForecast.id == forecast_id)
    )
    forecast = result.scalar_one_or_none()
    if not forecast:
        raise HTTPException(status_code=404, detail="フォーキャストが見つかりません")

    try:
        for key, value in data.items():
            if hasattr(forecast, key):
                setattr(forecast, key, value)
        if "forecast_quantity" in data or "unit_price" in data:
            qty = data.get("forecast_quantity", forecast.forecast_quantity)
            price = data.get("unit_price", float(forecast.unit_price or 0))
            forecast.forecast_amount = qty * price if price else 0
        await db.commit()
        return {"message": "フォーキャストを更新しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecasts/{forecast_id}/confirm")
async def confirm_forecast(
    forecast_id: int,
    data: dict = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """フォーキャスト確定"""
    if data is None:
        data = {}

    result = await db.execute(
        select(SalesForecast).where(SalesForecast.id == forecast_id)
    )
    forecast = result.scalar_one_or_none()
    if not forecast:
        raise HTTPException(status_code=404, detail="フォーキャストが見つかりません")
    if forecast.status == "confirmed":
        raise HTTPException(status_code=400, detail="既に確定済みです")

    try:
        forecast.status = "confirmed"
        forecast.confirmed_quantity = data.get(
            "confirmed_quantity", forecast.forecast_quantity
        )
        forecast.confirmed_at = now_jst()
        forecast.confirmed_by = current_user.username
        await db.commit()
        return {"message": "フォーキャストを確定しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/forecasts/{forecast_id}")
async def delete_forecast(
    forecast_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """フォーキャスト削除"""
    result = await db.execute(
        select(SalesForecast).where(SalesForecast.id == forecast_id)
    )
    forecast = result.scalar_one_or_none()
    if not forecast:
        raise HTTPException(status_code=404, detail="フォーキャストが見つかりません")

    try:
        await db.delete(forecast)
        await db.commit()
        return {"message": "フォーキャストを削除しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 売上計上 (Sales Recording) ==========


def _recording_to_dict(r: SalesRecording) -> dict:
    return {
        "id": r.id,
        "recording_no": r.recording_no,
        "recording_month": r.recording_month,
        "recording_date": r.recording_date.isoformat() if r.recording_date else None,
        "customer_code": r.customer_code,
        "customer_name": r.customer_name,
        "delivery_id": r.delivery_id,
        "delivery_no": r.delivery_no,
        "order_no": r.order_no,
        "product_code": r.product_code,
        "product_name": r.product_name,
        "quantity": r.quantity,
        "unit_price": float(r.unit_price or 0),
        "amount": float(r.amount or 0),
        "tax_amount": float(r.tax_amount or 0),
        "total_amount": float(r.total_amount or 0),
        "remarks": r.remarks,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/recordings")
async def get_recording_list(
    customer_code: Optional[str] = Query(None),
    recording_month: Optional[str] = Query(None, description="計上年月 (YYYY-MM)"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """売上計上一覧取得"""
    query = select(SalesRecording)

    if customer_code:
        query = query.where(SalesRecording.customer_code == customer_code)
    if recording_month:
        query = query.where(SalesRecording.recording_month == recording_month)
    if start_date:
        query = query.where(SalesRecording.recording_date >= start_date)
    if end_date:
        query = query.where(SalesRecording.recording_date <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(SalesRecording.recording_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [_recording_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/recordings/calculate")
async def calculate_monthly_recordings(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月次売上計上（確定出荷から自動計上）"""
    target_month = data.get("target_month")
    if not target_month:
        raise HTTPException(status_code=400, detail="対象年月 (target_month) は必須です")

    try:
        year, month = map(int, target_month.split("-"))
        month_start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        month_end = date(year, month, last_day)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="対象年月の形式が不正です (YYYY-MM)")

    try:
        deliveries_q = (
            select(SalesDelivery)
            .where(
                and_(
                    SalesDelivery.delivery_date >= month_start,
                    SalesDelivery.delivery_date <= month_end,
                    SalesDelivery.status.in_(["confirmed", "shipped", "completed"]),
                )
            )
        )
        deliveries_result = await db.execute(deliveries_q)
        deliveries = deliveries_result.scalars().all()

        created_count = 0
        for delivery in deliveries:
            existing = await db.execute(
                select(SalesRecording).where(
                    SalesRecording.delivery_id == delivery.id
                )
            )
            if existing.scalar_one_or_none():
                continue

            items_result = await db.execute(
                select(SalesDeliveryItem).where(
                    SalesDeliveryItem.delivery_id == delivery.id
                )
            )
            d_items = items_result.scalars().all()

            for d_item in d_items:
                recording_no = f"REC-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
                recording = SalesRecording(
                    recording_no=recording_no,
                    recording_month=target_month,
                    recording_date=delivery.delivery_date,
                    customer_code=delivery.customer_code,
                    customer_name=delivery.customer_name,
                    delivery_id=delivery.id,
                    delivery_no=delivery.delivery_no,
                    order_no=delivery.order_no,
                    product_code=d_item.product_code,
                    product_name=d_item.product_name,
                    quantity=d_item.delivery_quantity,
                    remarks=d_item.remarks,
                    created_by=current_user.username,
                )
                db.add(recording)
                created_count += 1

        await db.commit()
        return {
            "message": f"{target_month} の売上計上を実行しました",
            "created_count": created_count,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recordings/summary")
async def get_recording_summary(
    recording_month: Optional[str] = Query(None, description="計上年月 (YYYY-MM)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月次売上サマリー"""
    if not recording_month:
        today = date.today()
        recording_month = today.strftime("%Y-%m")

    total_amount_q = select(
        func.coalesce(func.sum(SalesRecording.total_amount), 0).label("total_amount"),
        func.coalesce(func.sum(SalesRecording.amount), 0).label("amount"),
        func.coalesce(func.sum(SalesRecording.tax_amount), 0).label("tax_amount"),
        func.coalesce(func.sum(SalesRecording.quantity), 0).label("total_quantity"),
        func.count(SalesRecording.id).label("record_count"),
    ).where(SalesRecording.recording_month == recording_month)

    result = await db.execute(total_amount_q)
    row = result.one()

    customer_count_q = select(
        func.count(func.distinct(SalesRecording.customer_code))
    ).where(SalesRecording.recording_month == recording_month)
    customer_result = await db.execute(customer_count_q)
    customer_count = customer_result.scalar() or 0

    return {
        "recording_month": recording_month,
        "total_amount": float(row.total_amount or 0),
        "amount": float(row.amount or 0),
        "tax_amount": float(row.tax_amount or 0),
        "total_quantity": int(row.total_quantity or 0),
        "record_count": row.record_count or 0,
        "customer_count": customer_count,
    }


# ========== 返品管理 RMA (Returns Management) ==========


def _return_to_dict(r: SalesReturn) -> dict:
    status_names = {
        "draft": "下書き",
        "pending": "承認待ち",
        "approved": "承認済",
        "received": "受入済",
        "completed": "完了",
        "rejected": "却下",
    }
    refund_status_names = {
        "pending": "返金待ち",
        "refunded": "返金済",
        "none": "返金なし",
    }
    return {
        "id": r.id,
        "return_no": r.return_no,
        "order_id": r.order_id,
        "order_no": r.order_no,
        "delivery_id": r.delivery_id,
        "delivery_no": r.delivery_no,
        "customer_code": r.customer_code,
        "customer_name": r.customer_name,
        "warehouse_code": r.warehouse_code,
        "warehouse_name": r.warehouse_name,
        "return_date": r.return_date.isoformat() if r.return_date else None,
        "status": r.status,
        "status_name": status_names.get(r.status, r.status),
        "return_reason": r.return_reason,
        "total_quantity": r.total_quantity,
        "total_amount": float(r.total_amount or 0),
        "refund_status": r.refund_status,
        "refund_status_name": refund_status_names.get(r.refund_status, r.refund_status),
        "refund_amount": float(r.refund_amount or 0),
        "remarks": r.remarks,
        "created_by": r.created_by,
        "approved_by": r.approved_by,
        "approved_at": r.approved_at.isoformat() if r.approved_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _return_item_to_dict(item: SalesReturnItem) -> dict:
    return {
        "id": item.id,
        "product_code": item.product_code,
        "product_name": item.product_name,
        "unit": item.unit,
        "return_quantity": item.return_quantity,
        "received_quantity": item.received_quantity or 0,
        "unit_price": float(item.unit_price or 0) if item.unit_price else None,
        "amount": float(item.amount or 0) if item.amount else None,
        "quality_status": item.quality_status,
        "return_reason": item.return_reason,
        "remarks": item.remarks,
    }


@router.get("/returns")
async def get_return_list(
    customer_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """返品一覧取得"""
    query = select(SalesReturn)

    if customer_code:
        query = query.where(SalesReturn.customer_code == customer_code)
    if status:
        query = query.where(SalesReturn.status == status)
    if start_date:
        query = query.where(SalesReturn.return_date >= start_date)
    if end_date:
        query = query.where(SalesReturn.return_date <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(SalesReturn.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [_return_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/returns/{return_id}")
async def get_return_by_id(
    return_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """返品詳細取得"""
    result = await db.execute(
        select(SalesReturn).where(SalesReturn.id == return_id)
    )
    ret = result.scalar_one_or_none()
    if not ret:
        raise HTTPException(status_code=404, detail="返品が見つかりません")

    items_result = await db.execute(
        select(SalesReturnItem).where(SalesReturnItem.return_id == return_id)
    )
    items = items_result.scalars().all()

    data = _return_to_dict(ret)
    data["items"] = [_return_item_to_dict(i) for i in items]
    return data


@router.post("/returns")
async def create_return(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """返品作成"""
    try:
        return_no = f"RMA-{now_jst().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        items_data = data.pop("items", [])

        ret = SalesReturn(
            return_no=return_no,
            order_id=data.get("order_id"),
            order_no=data.get("order_no"),
            delivery_id=data.get("delivery_id"),
            delivery_no=data.get("delivery_no"),
            customer_code=data["customer_code"],
            customer_name=data.get("customer_name"),
            warehouse_code=data["warehouse_code"],
            warehouse_name=data.get("warehouse_name"),
            return_date=data.get("return_date", date.today()),
            status="draft",
            return_reason=data.get("return_reason"),
            remarks=data.get("remarks"),
            created_by=current_user.username,
        )
        db.add(ret)
        await db.flush()

        total_quantity = 0
        total_amount = 0
        for item_data in items_data:
            qty = item_data["return_quantity"]
            price = item_data.get("unit_price")
            amount = qty * price if price else None
            total_quantity += qty
            if amount:
                total_amount += amount

            item = SalesReturnItem(
                return_id=ret.id,
                product_code=item_data["product_code"],
                product_name=item_data.get("product_name"),
                unit=item_data.get("unit", "個"),
                return_quantity=qty,
                unit_price=price,
                amount=amount,
                quality_status=item_data.get("quality_status"),
                return_reason=item_data.get("return_reason"),
                remarks=item_data.get("remarks"),
            )
            db.add(item)

        ret.total_quantity = total_quantity
        ret.total_amount = total_amount

        await db.commit()
        return {"message": "返品を作成しました", "return_no": return_no, "id": ret.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/returns/{return_id}")
async def update_return(
    return_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """返品更新"""
    result = await db.execute(
        select(SalesReturn).where(SalesReturn.id == return_id)
    )
    ret = result.scalar_one_or_none()
    if not ret:
        raise HTTPException(status_code=404, detail="返品が見つかりません")
    if ret.status not in ["draft"]:
        raise HTTPException(status_code=400, detail="下書き状態の返品のみ編集できます")

    try:
        for key, value in data.items():
            if key != "items" and hasattr(ret, key):
                setattr(ret, key, value)
        await db.commit()
        return {"message": "返品を更新しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/returns/{return_id}/approve")
async def approve_return(
    return_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """返品承認"""
    result = await db.execute(
        select(SalesReturn).where(SalesReturn.id == return_id)
    )
    ret = result.scalar_one_or_none()
    if not ret:
        raise HTTPException(status_code=404, detail="返品が見つかりません")
    if ret.status not in ["draft", "pending"]:
        raise HTTPException(status_code=400, detail="この返品は承認できません")

    try:
        ret.status = "approved"
        ret.approved_by = current_user.username
        ret.approved_at = now_jst()
        await db.commit()
        return {"message": "返品を承認しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/returns/{return_id}/receive")
async def receive_return(
    return_id: int,
    data: dict = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """返品受入"""
    if data is None:
        data = {}

    result = await db.execute(
        select(SalesReturn).where(SalesReturn.id == return_id)
    )
    ret = result.scalar_one_or_none()
    if not ret:
        raise HTTPException(status_code=404, detail="返品が見つかりません")
    if ret.status != "approved":
        raise HTTPException(status_code=400, detail="承認済の返品のみ受入できます")

    try:
        received_items = data.get("items", [])
        if received_items:
            for ri in received_items:
                item_result = await db.execute(
                    select(SalesReturnItem).where(SalesReturnItem.id == ri["id"])
                )
                item = item_result.scalar_one_or_none()
                if item:
                    item.received_quantity = ri.get("received_quantity", item.return_quantity)
                    if "quality_status" in ri:
                        item.quality_status = ri["quality_status"]
        else:
            items_result = await db.execute(
                select(SalesReturnItem).where(SalesReturnItem.return_id == return_id)
            )
            for item in items_result.scalars().all():
                item.received_quantity = item.return_quantity

        ret.status = "received"
        ret.refund_amount = data.get("refund_amount", float(ret.total_amount or 0))

        await db.commit()
        return {"message": "返品を受入しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
