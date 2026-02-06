"""
ERP（企業資源計画）APIエンドポイント
販売管理、購買管理、在庫管理、受注管理など
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from typing import List, Optional
from datetime import date, datetime
import json

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.erp import models, schemas

router = APIRouter()


# ========== 既存エンドポイント ==========

@router.get("/sales")
async def get_sales(current_user: User = Depends(verify_token_and_get_user)):
    """販売管理データ取得"""
    return {"message": "販売管理データ", "data": []}


@router.get("/purchase")
async def get_purchase(current_user: User = Depends(verify_token_and_get_user)):
    """購買管理データ取得"""
    return {"message": "購買管理データ", "data": []}


@router.get("/inventory")
async def get_inventory(current_user: User = Depends(verify_token_and_get_user)):
    """在庫管理データ取得"""
    return {"message": "在庫管理データ", "data": []}


@router.get("/accounting")
async def get_accounting(current_user: User = Depends(verify_token_and_get_user)):
    """会計管理データ取得"""
    return {"message": "会計管理データ", "data": []}


# ========== 月別受注管理 API ==========

@router.get("/orders/monthly", response_model=dict)
async def get_monthly_orders(
    year: Optional[int] = Query(None, description="年"),
    month: Optional[int] = Query(None, description="月"),
    customer_code: Optional[str] = Query(None, description="顧客コード"),
    product_code: Optional[str] = Query(None, description="品番"),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(50, ge=1, le=1000, description="ページサイズ"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """月別受注一覧取得"""
    try:
        # フィルタ条件構築
        query = select(models.OrderMonthly).where(models.OrderMonthly.is_active == True)
        
        if year:
            query = query.where(models.OrderMonthly.year == year)
        if month:
            query = query.where(models.OrderMonthly.month == month)
        if customer_code:
            query = query.where(models.OrderMonthly.customer_code == customer_code)
        if product_code:
            query = query.where(models.OrderMonthly.product_code.like(f"%{product_code}%"))
        
        # 総件数取得
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # ページネーション
        query = query.order_by(models.OrderMonthly.year.desc(), models.OrderMonthly.month.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "items": [schemas.OrderMonthly.from_orm(order) for order in orders]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/monthly/summary", response_model=schemas.OrderMonthlySummary)
async def get_monthly_orders_summary(
    year: Optional[int] = Query(None, description="年"),
    month: Optional[int] = Query(None, description="月"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """月別受注集計取得"""
    try:
        query = select(
            func.sum(models.OrderMonthly.forecast_units).label("forecast_units"),
            func.sum(models.OrderMonthly.confirmed_units).label("confirmed_units"),
            func.sum(models.OrderMonthly.forecast_diff).label("forecast_diff"),
        ).where(models.OrderMonthly.is_active == True)
        
        if year:
            query = query.where(models.OrderMonthly.year == year)
        if month:
            query = query.where(models.OrderMonthly.month == month)
        
        result = await db.execute(query)
        row = result.first()
        
        # メッキ・溶接の集計
        plating_query = select(
            func.sum(func.if_(models.OrderMonthly.plating_type == "社内", models.OrderMonthly.plating_count, 0)).label("plating_count"),
            func.sum(func.if_(models.OrderMonthly.plating_type == "外注", models.OrderMonthly.plating_count, 0)).label("external_plating_count"),
            func.sum(func.if_(models.OrderMonthly.welding_type == "社内", models.OrderMonthly.welding_count, 0)).label("internal_welding_count"),
            func.sum(func.if_(models.OrderMonthly.welding_type == "外注", models.OrderMonthly.welding_count, 0)).label("external_welding_count"),
        ).where(models.OrderMonthly.is_active == True)
        
        if year:
            plating_query = plating_query.where(models.OrderMonthly.year == year)
        if month:
            plating_query = plating_query.where(models.OrderMonthly.month == month)
        
        plating_result = await db.execute(plating_query)
        plating_row = plating_result.first()
        
        return {
            "forecast_units": row.forecast_units or 0,
            "confirmed_units": row.confirmed_units or 0,
            "forecast_total_units": row.forecast_units or 0,
            "forecast_diff": row.forecast_diff or 0,
            "plating_count": plating_row.plating_count or 0,
            "external_plating_count": plating_row.external_plating_count or 0,
            "internal_welding_count": plating_row.internal_welding_count or 0,
            "external_welding_count": plating_row.external_welding_count or 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/monthly", response_model=schemas.OrderMonthly)
async def create_monthly_order(
    order: schemas.OrderMonthlyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """月別受注作成"""
    try:
        db_order = models.OrderMonthly(**order.dict(), created_by=current_user.username, updated_by=current_user.username)
        db.add(db_order)
        await db.flush()
        
        # ログ記録
        log = models.OrderLog(
            order_type="monthly",
            order_id=db_order.id,
            action="create",
            new_data=json.dumps(order.dict(), default=str),
            user_id=current_user.id,
            user_name=current_user.username
        )
        db.add(log)
        await db.commit()
        await db.refresh(db_order)
        
        return db_order
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/monthly/{order_id}", response_model=schemas.OrderMonthly)
async def get_monthly_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """月別受注詳細取得"""
    query = select(models.OrderMonthly).where(models.OrderMonthly.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    return order


@router.put("/orders/monthly/{order_id}", response_model=schemas.OrderMonthly)
async def update_monthly_order(
    order_id: int,
    order_update: schemas.OrderMonthlyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """月別受注更新"""
    query = select(models.OrderMonthly).where(models.OrderMonthly.id == order_id)
    result = await db.execute(query)
    db_order = result.scalar_one_or_none()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    try:
        old_data = schemas.OrderMonthly.from_orm(db_order).dict()
        
        # 更新
        update_data = order_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_order, field, value)
        
        db_order.updated_by = current_user.username
        
        await db.flush()
        
        # ログ記録
        log = models.OrderLog(
            order_type="monthly",
            order_id=db_order.id,
            action="update",
            old_data=json.dumps(old_data, default=str),
            new_data=json.dumps(update_data, default=str),
            user_id=current_user.id,
            user_name=current_user.username
        )
        db.add(log)
        await db.commit()
        await db.refresh(db_order)
        
        return db_order
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/monthly/{order_id}")
async def delete_monthly_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """月別受注削除"""
    query = select(models.OrderMonthly).where(models.OrderMonthly.id == order_id)
    result = await db.execute(query)
    db_order = result.scalar_one_or_none()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    try:
        old_data = schemas.OrderMonthly.from_orm(db_order).dict()
        
        # 論理削除
        db_order.is_active = False
        db_order.updated_by = current_user.username
        
        # ログ記録
        log = models.OrderLog(
            order_type="monthly",
            order_id=db_order.id,
            action="delete",
            old_data=json.dumps(old_data, default=str),
            user_id=current_user.id,
            user_name=current_user.username
        )
        db.add(log)
        await db.commit()
        
        return {"message": "削除しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 日別受注管理 API ==========

@router.get("/orders/daily", response_model=dict)
async def get_daily_orders(
    year: Optional[int] = Query(None, description="年"),
    month: Optional[int] = Query(None, description="月"),
    day: Optional[int] = Query(None, description="日"),
    customer_code: Optional[str] = Query(None, description="顧客コード"),
    product_code: Optional[str] = Query(None, description="品番"),
    shipping_status: Optional[str] = Query(None, description="出荷状態"),
    confirmation_status: Optional[str] = Query(None, description="確認状態"),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(50, ge=1, le=1000, description="ページサイズ"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """日別受注一覧取得"""
    try:
        query = select(models.OrderDaily).where(models.OrderDaily.is_active == True)
        
        if year:
            query = query.where(models.OrderDaily.year == year)
        if month:
            query = query.where(models.OrderDaily.month == month)
        if day:
            query = query.where(models.OrderDaily.day == day)
        if customer_code:
            query = query.where(models.OrderDaily.customer_code == customer_code)
        if product_code:
            query = query.where(models.OrderDaily.product_code.like(f"%{product_code}%"))
        if shipping_status:
            query = query.where(models.OrderDaily.shipping_status == shipping_status)
        if confirmation_status:
            query = query.where(models.OrderDaily.confirmation_status == confirmation_status)
        
        # 総件数取得
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # ページネーション
        query = query.order_by(models.OrderDaily.order_date.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "items": [schemas.OrderDaily.from_orm(order) for order in orders]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/daily/summary", response_model=schemas.OrderDailySummary)
async def get_daily_orders_summary(
    year: Optional[int] = Query(None, description="年"),
    month: Optional[int] = Query(None, description="月"),
    day: Optional[int] = Query(None, description="日"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """日別受注集計取得"""
    try:
        query = select(
            func.sum(models.OrderDaily.confirmed_boxes).label("total_confirmed_boxes"),
            func.sum(models.OrderDaily.confirmed_units).label("total_confirmed_units"),
            func.sum(models.OrderDaily.forecast_units).label("total_forecast_units"),
            func.sum(func.if_(models.OrderDaily.is_shipped == True, 1, 0)).label("shipped_orders_count"),
            func.sum(func.if_(models.OrderDaily.is_shipped == False, 1, 0)).label("unshipped_orders_count"),
            func.sum(func.if_(models.OrderDaily.is_confirmed == True, 1, 0)).label("confirmed_orders_count"),
            func.sum(func.if_(models.OrderDaily.is_confirmed == False, 1, 0)).label("unconfirmed_orders_count"),
        ).where(models.OrderDaily.is_active == True)
        
        if year:
            query = query.where(models.OrderDaily.year == year)
        if month:
            query = query.where(models.OrderDaily.month == month)
        if day:
            query = query.where(models.OrderDaily.day == day)
        
        result = await db.execute(query)
        row = result.first()
        
        return {
            "total_confirmed_boxes": row.total_confirmed_boxes or 0,
            "total_confirmed_units": row.total_confirmed_units or 0,
            "total_forecast_units": row.total_forecast_units or 0,
            "shipped_orders_count": row.shipped_orders_count or 0,
            "unshipped_orders_count": row.unshipped_orders_count or 0,
            "confirmed_orders_count": row.confirmed_orders_count or 0,
            "unconfirmed_orders_count": row.unconfirmed_orders_count or 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/daily", response_model=schemas.OrderDaily)
async def create_daily_order(
    order: schemas.OrderDailyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """日別受注作成"""
    try:
        # 出荷・確認フラグ設定
        is_shipped = order.shipping_status == "出荷済"
        is_confirmed = order.confirmation_status == "確認済"
        
        db_order = models.OrderDaily(
            **order.dict(),
            is_shipped=is_shipped,
            is_confirmed=is_confirmed,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        db.add(db_order)
        await db.flush()
        
        # ログ記録
        log = models.OrderLog(
            order_type="daily",
            order_id=db_order.id,
            action="create",
            new_data=json.dumps(order.dict(), default=str),
            user_id=current_user.id,
            user_name=current_user.username
        )
        db.add(log)
        await db.commit()
        await db.refresh(db_order)
        
        return db_order
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/daily/batch", response_model=dict)
async def create_daily_orders_batch(
    orders: List[schemas.OrderDailyCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """日別受注一括作成"""
    try:
        created_orders = []
        for order in orders:
            is_shipped = order.shipping_status == "出荷済"
            is_confirmed = order.confirmation_status == "確認済"
            
            db_order = models.OrderDaily(
                **order.dict(),
                is_shipped=is_shipped,
                is_confirmed=is_confirmed,
                created_by=current_user.username,
                updated_by=current_user.username
            )
            db.add(db_order)
            created_orders.append(db_order)
        
        await db.commit()
        
        return {
            "message": f"{len(created_orders)}件の受注を作成しました",
            "count": len(created_orders)
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/daily/{order_id}", response_model=schemas.OrderDaily)
async def get_daily_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """日別受注詳細取得"""
    query = select(models.OrderDaily).where(models.OrderDaily.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    return order


@router.put("/orders/daily/{order_id}", response_model=schemas.OrderDaily)
async def update_daily_order(
    order_id: int,
    order_update: schemas.OrderDailyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """日別受注更新"""
    query = select(models.OrderDaily).where(models.OrderDaily.id == order_id)
    result = await db.execute(query)
    db_order = result.scalar_one_or_none()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    try:
        old_data = schemas.OrderDaily.from_orm(db_order).dict()
        
        # 更新
        update_data = order_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_order, field, value)
        
        # フラグ更新
        if "shipping_status" in update_data:
            db_order.is_shipped = update_data["shipping_status"] == "出荷済"
        if "confirmation_status" in update_data:
            db_order.is_confirmed = update_data["confirmation_status"] == "確認済"
        
        db_order.updated_by = current_user.username
        
        await db.flush()
        
        # ログ記録
        log = models.OrderLog(
            order_type="daily",
            order_id=db_order.id,
            action="update",
            old_data=json.dumps(old_data, default=str),
            new_data=json.dumps(update_data, default=str),
            user_id=current_user.id,
            user_name=current_user.username
        )
        db.add(log)
        await db.commit()
        await db.refresh(db_order)
        
        return db_order
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/daily/{order_id}")
async def delete_daily_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """日別受注削除"""
    query = select(models.OrderDaily).where(models.OrderDaily.id == order_id)
    result = await db.execute(query)
    db_order = result.scalar_one_or_none()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="受注が見つかりません")
    
    try:
        old_data = schemas.OrderDaily.from_orm(db_order).dict()
        
        # 論理削除
        db_order.is_active = False
        db_order.updated_by = current_user.username
        
        # ログ記録
        log = models.OrderLog(
            order_type="daily",
            order_id=db_order.id,
            action="delete",
            old_data=json.dumps(old_data, default=str),
            user_id=current_user.id,
            user_name=current_user.username
        )
        db.add(log)
        await db.commit()
        
        return {"message": "削除しました"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 顧客マスタ API ==========

@router.get("/customers", response_model=List[schemas.Customer])
async def get_customers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """顧客一覧取得"""
    query = select(models.Customer).where(models.Customer.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/customers", response_model=schemas.Customer)
async def create_customer(
    customer: schemas.CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """顧客作成"""
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    await db.commit()
    await db.refresh(db_customer)
    return db_customer


# ========== 納入先マスタ API ==========

@router.get("/destinations", response_model=List[schemas.Destination])
async def get_destinations(
    customer_code: Optional[str] = Query(None, description="顧客コード"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """納入先一覧取得（テーブル未作成・エラー時は空リストを返す）"""
    try:
        query = select(models.Destination).where(models.Destination.is_active == True)
        if customer_code:
            query = query.where(models.Destination.customer_code == customer_code)
        result = await db.execute(query)
        return result.scalars().all()
    except Exception:
        return []


@router.post("/destinations", response_model=schemas.Destination)
async def create_destination(
    destination: schemas.DestinationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """納入先作成"""
    db_destination = models.Destination(**destination.dict())
    db.add(db_destination)
    await db.commit()
    await db.refresh(db_destination)
    return db_destination


# ========== 製品マスタ API ==========

@router.get("/products", response_model=List[schemas.Product])
async def get_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """製品一覧取得"""
    query = select(models.Product).where(models.Product.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/products", response_model=schemas.Product)
async def create_product(
    product: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """製品作成"""
    db_product = models.Product(**product.dict())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


# ========== ログ API ==========

@router.get("/orders/logs", response_model=List[schemas.OrderLog])
async def get_order_logs(
    order_type: Optional[str] = Query(None, description="受注タイプ"),
    order_id: Optional[int] = Query(None, description="受注ID"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user)
):
    """受注ログ取得"""
    query = select(models.OrderLog).order_by(models.OrderLog.created_at.desc())
    
    if order_type:
        query = query.where(models.OrderLog.order_type == order_type)
    if order_id:
        query = query.where(models.OrderLog.order_id == order_id)
    
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

