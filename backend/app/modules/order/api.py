"""
受注バッチ API
- GET /products: 納入先+年月で製品一覧（order_monthly と LEFT JOIN で forecast_units）
- GET /check-combination-exists: 納入先名・製品名・年月の組み合わせが既存か
- POST /batch-create-monthly: 一括登録（INSERT IGNORE 相当）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import List, Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Product
from app.modules.erp import models as erp_models

router = APIRouter()


# ---------- GET /products ----------
@router.get("/products")
async def get_products_by_destination(
    destination_cd: str = Query(..., description="納入先CD"),
    year: int = Query(..., description="年"),
    month: int = Query(..., ge=1, le=12, description="月"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    納入先+年月で製品一覧を取得。
    products を destination_cd で絞り、order_monthly を LEFT JOIN して該当年月の forecast_units を取得（無い場合は 0）。
    """
    # products と order_monthly を LEFT JOIN（同一 destination_cd, product_cd, year, month）
    om = erp_models.OrderMonthly
    q = (
        select(
            Product.product_cd,
            Product.product_name,
            Product.product_type,
            func.coalesce(om.forecast_units, 0).label("forecast_units"),
        )
        .select_from(Product)
        .outerjoin(
            om,
            and_(
                Product.product_cd == om.product_cd,
                Product.destination_cd == om.destination_cd,
                om.year == year,
                om.month == month,
            ),
        )
        .where(Product.destination_cd == destination_cd)
        .where(Product.status == "active")
        .order_by(Product.product_cd)
    )
    result = await db.execute(q)
    rows = result.all()
    data = [
        {
            "product_cd": r.product_cd,
            "product_name": r.product_name or "",
            "product_type": r.product_type or "量産品",
            "forecast_units": int(r.forecast_units) if r.forecast_units is not None else 0,
        }
        for r in rows
    ]
    return {"success": True, "data": data}


# ---------- GET /check-combination-exists ----------
@router.get("/check-combination-exists")
async def check_combination_exists(
    destination_name: str = Query(..., description="納入先名"),
    product_name: str = Query(..., description="製品名"),
    year: int = Query(..., description="年"),
    month: int = Query(..., ge=1, le=12, description="月"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    order_monthly に同一 destination_name, product_name, year, month が存在するか。
    存在する場合 id, forecast_units を返し、数量更新に利用する。
    返却: { exists: true/false, id?: number, forecast_units?: number }
    """
    om = erp_models.OrderMonthly
    q = (
        select(om.id, om.forecast_units)
        .where(
            and_(
                om.destination_name == destination_name,
                om.product_name == product_name,
                om.year == year,
                om.month == month,
            )
        )
        .limit(1)
    )
    result = await db.execute(q)
    row = result.one_or_none()
    if row is None:
        return {"exists": False}
    return {"exists": True, "id": row.id, "forecast_units": row.forecast_units or 0}


# ---------- POST /batch-create-monthly ----------
class BatchProductItem(BaseModel):
    product_cd: str
    forecast_units: int = 0


class BatchCreateMonthlyBody(BaseModel):
    year: int
    month: int
    destination_cd: str
    destination_name: str
    products: List[BatchProductItem]


@router.post("/batch-create-monthly")
async def batch_create_monthly(
    body: BatchCreateMonthlyBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    月別受注を一括登録。
    order_id = {year}{month2桁}{destination_cd}{product_cd}。
    INSERT 時に重複（同一 order_id）はスキップ。返却: inserted, total, skipped, message。
    """
    if not body.products:
        return {
            "inserted": 0,
            "total": 0,
            "skipped": 0,
            "message": "products が空です",
        }
    year = body.year
    month = body.month
    destination_cd = body.destination_cd
    destination_name = body.destination_name

    # 製品マスタから product_cd に対応する product_name, product_type を取得
    product_cds = [p.product_cd for p in body.products]
    pq = select(Product).where(Product.product_cd.in_(product_cds))
    presult = await db.execute(pq)
    product_map = {r.product_cd: r for r in presult.scalars().all()}

    inserted = 0
    total = len(body.products)
    for item in body.products:
        prod = product_map.get(item.product_cd)
        product_name = prod.product_name if prod else item.product_cd
        product_type = (prod.product_type or "量産品") if prod else "量産品"
        order_id = f"{year}{month:02d}{destination_cd}{item.product_cd}"
        row = erp_models.OrderMonthly(
            order_id=order_id,
            destination_cd=destination_cd,
            destination_name=destination_name,
            year=year,
            month=month,
            product_cd=item.product_cd,
            product_name=product_name,
            product_type=product_type,
            forecast_units=item.forecast_units,
            forecast_total_units=0,
            forecast_diff=0,
        )
        try:
            db.add(row)
            await db.commit()
            inserted += 1
        except IntegrityError:
            await db.rollback()
            # 重複はスキップ（INSERT IGNORE 相当）
            continue
    skipped = total - inserted
    return {
        "inserted": inserted,
        "total": total,
        "skipped": skipped,
        "message": f"{inserted}件登録、{skipped}件スキップ",
    }
