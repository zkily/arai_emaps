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
    """製品一覧取得（product テーブル優先、無い場合は products テーブルから取得）"""
    try:
        query = select(models.Product).where(models.Product.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()
    except Exception:
        pass
    try:
        from app.modules.master.models import Product as MasterProduct
        query = select(MasterProduct).where(
            (MasterProduct.status == "active") | (MasterProduct.status.is_(None))
        )
        result = await db.execute(query)
        rows = result.scalars().all()
        return [
            schemas.Product(
                id=r.id,
                product_code=r.product_cd or "",
                product_name=r.product_name or "",
                product_name_kana=None,
                category=r.category,
                specification=None,
                unit="個",
                standard_price=r.unit_price,
                cost_price=None,
                remarks=r.note,
                is_active=(r.status or "").lower() == "active",
                created_at=r.created_at or datetime.now(),
                updated_at=r.updated_at or datetime.now(),
            )
            for r in rows
        ]
    except Exception:
        return []


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


# ========== 月別受注 API ==========

@router.get("/orders/monthly", response_model=List[schemas.OrderMonthly])
async def list_order_monthly(
    year: Optional[int] = Query(None, description="年"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月"),
    destination_cd: Optional[str] = Query(None, description="納入先CD"),
    product_cd: Optional[str] = Query(None, description="製品CD"),
    keyword: Optional[str] = Query(None, description="納入先名・製品名検索"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月別受注一覧"""
    query = select(models.OrderMonthly)
    if year is not None:
        query = query.where(models.OrderMonthly.year == year)
    if month is not None:
        query = query.where(models.OrderMonthly.month == month)
    if destination_cd:
        query = query.where(models.OrderMonthly.destination_cd == destination_cd)
    if product_cd:
        query = query.where(models.OrderMonthly.product_cd == product_cd)
    if keyword:
        k = f"%{keyword}%"
        query = query.where(
            or_(
                models.OrderMonthly.destination_name.like(k),
                models.OrderMonthly.product_name.like(k),
                models.OrderMonthly.product_cd.like(k),
            )
        )
    query = query.order_by(models.OrderMonthly.year.desc(), models.OrderMonthly.month.desc())
    result = await db.execute(query)
    return result.scalars().all()


def _order_monthly_type_suffix(product_type: str) -> str:
    """order_id 用の種別サフィックス（DBトリガーと同一）"""
    m = {
        "試作品": "1", "別注品": "2", "補給品": "3", "サンプル品": "4",
        "代替品": "5", "返却品": "6", "その他": "7",
    }
    return m.get(product_type, "0")


@router.post("/orders/monthly", response_model=schemas.OrderMonthly)
async def create_order_monthly(
    body: schemas.OrderMonthlyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月別受注登録。同一（年・月・納入先・製品・種別）が既にあれば更新（重複不可）"""
    product_type = body.product_type or "量産品"
    result = await db.execute(
        select(models.OrderMonthly).where(
            and_(
                models.OrderMonthly.year == body.year,
                models.OrderMonthly.month == body.month,
                models.OrderMonthly.destination_cd == body.destination_cd,
                models.OrderMonthly.product_cd == body.product_cd,
                models.OrderMonthly.product_type == product_type,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.destination_name = body.destination_name
        existing.product_name = body.product_name
        existing.product_alias = body.product_alias
        existing.forecast_units = body.forecast_units or 0
        existing.forecast_total_units = body.forecast_total_units or 0
        existing.forecast_diff = body.forecast_diff or 0
        await db.commit()
        await db.refresh(existing)
        return existing
    # order_id をアプリで生成（DBトリガーが無い環境でも動作するように）
    suffix = _order_monthly_type_suffix(product_type)
    order_id = f"{body.year}{body.month:02d}{body.destination_cd}{body.product_cd}{suffix}"
    row = models.OrderMonthly(
        order_id=order_id,
        destination_cd=body.destination_cd,
        destination_name=body.destination_name,
        year=body.year,
        month=body.month,
        product_cd=body.product_cd,
        product_name=body.product_name,
        product_alias=body.product_alias,
        product_type=product_type,
        forecast_units=body.forecast_units or 0,
        forecast_total_units=body.forecast_total_units or 0,
        forecast_diff=body.forecast_diff or 0,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/orders/monthly/by-order-id/{order_id}", response_model=schemas.OrderMonthly)
async def get_order_monthly_by_order_id(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """order_id で月別受注取得"""
    result = await db.execute(
        select(models.OrderMonthly).where(models.OrderMonthly.order_id == order_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return row


@router.get("/orders/monthly/{id}", response_model=schemas.OrderMonthly)
async def get_order_monthly_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """id で月別受注取得"""
    result = await db.execute(
        select(models.OrderMonthly).where(models.OrderMonthly.id == id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return row


@router.put("/orders/monthly/{id}")
async def update_order_monthly(
    id: int,
    body: schemas.OrderMonthlyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月別受注更新"""
    result = await db.execute(select(models.OrderMonthly).where(models.OrderMonthly.id == id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    data = body.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/orders/monthly/{id}")
async def delete_order_monthly(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月別受注削除"""
    result = await db.execute(select(models.OrderMonthly).where(models.OrderMonthly.id == id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.delete(row)
    await db.commit()
    return {"ok": True}

